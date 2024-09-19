"""This module provides the version 1 http-based api endpoints of the chat backend."""

from __future__ import annotations

import jwt
from quart import Blueprint, Response, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound

from pykcworkshop import logs
from pykcworkshop.chat import db, tokens
from pykcworkshop.chat.api.http import helpers
from pykcworkshop.chat.types import UserData

bp = Blueprint("v1-http", __name__, url_prefix="/v1")
"""This blueprint contains all version 1 http routes for the chat app."""


@bp.route("/user/login", methods=["POST"])
async def user_login() -> Response:
    """Validate a user token and authenticate the client session.
    Returns the name, id, and full base64 JWT for the authenticated user.

    POST body required fields:
        `user_hash`: `str`

    Note:
        Currently, the raw base64 JWT is returned in the `user_token` field of the
        response body, but this may change at any time, so the frontend should not
        rely on the ability to parse data from the JWT. The only invariant of the
        `user_token` field is that it will be usable as a bearer token in the
        `Authentication` header for subsequent requests from the frontend.
        For example, if the need arises, the `user_token` value may be encrypted without
        changes to the response structure, but any authenticated endpoints will be updated
        to accept the encrypted token value in the Authentication header instead of the
        raw base64 value, so the frontend should only use the `user_token`
        as an opaque session identifier.
    """

    body = await request.get_json()
    bad_req = helpers.validate_required_fields(body, ["user_hash"])
    if bad_req is not None:
        return bad_req
    user_hash: str = body["user_hash"]
    try:
        password, user_id = tokens.parse_login_hash(user_hash)
        async with db.get_session() as session:
            user = await db.get_user_by_id(session, user_id)
        # token column is optional in db. All current users should have a token, but
        # it's possible we could get one without, so we assert to break the try block
        # if we can't validate the login.
        assert user.token is not None
        tokens.pw_hasher().verify(user.token.password_hash, password)
        user_data = tokens.validate_token(user.token.token)
        res = jsonify(
            {
                "user_id": user_data["user_id"],
                "user_name": user_data["user_name"],
                "user_token": user.token.token,
            }
        )
        res.status_code = 200
        return res
    except (jwt.InvalidTokenError, NoResultFound) as e:
        logs.debug(
            helpers.logger,
            {
                "msg": "Invalid jwt when logging in user",
            },
            err=e,
        )
        return helpers.unauthorized()
    except Exception as e:  # pragma: no cover
        logs.error(
            helpers.logger,
            {
                "msg": "Unknown error when logging in user",
            },
            err=e,
        )
        return helpers.unauthorized()


@bp.route("/room/<room_token>", methods=["GET"])
@helpers.auth_required(inject_user_data=False)
async def get_room_data(room_token: str) -> Response:
    """Return the room hash and name for the provided hashed token."""

    try:
        async with db.get_session() as session:
            room = await db.get_room_by_id(session, room_token)
            return jsonify({"room_hash": room.id, "room_name": room.name})
    except NoResultFound as e:
        logs.debug(
            helpers.logger,
            {
                "msg": "Invalid room token when fetching room data.",
                "room_token_hash": room_token,
            },
            err=e,
        )
        return helpers.bad_request("Invalid room token")
    except Exception as e:  # pragma: no cover
        logs.error(
            helpers.logger,
            {
                "msg": "Unknown error in get_room_data http route.",
                "room_token": room_token,
            },
            err=e,
        )
        raise e


@bp.route("/user/create", methods=["POST"])
async def create_new_user_token() -> Response:
    """Create a new user and token and return the hash and user name in the response."""

    body = await request.get_json()
    bad_req = helpers.validate_required_fields(body, ["user_name"])
    if bad_req is not None:
        return bad_req
    user_name = body["user_name"]
    try:
        try:
            async with db.get_session() as session:
                new_user, new_user_password = await db.create_user(session, user_name=user_name)
                await session.commit()
        except IntegrityError as e:
            constraint_violation = db.parse_constraint_error(e)
            if constraint_violation == db.ConstraintViolation.UNIQUE:
                return helpers.bad_request("Username already taken")
            else:  # pragma: no cover
                logs.error(
                    helpers.logger,
                    {
                        "msg": "Unknown error creating new user.",
                        "constraint_violation": constraint_violation.name,
                    },
                    err=e,
                )
                raise e
        else:
            res = jsonify({"user_hash": new_user_password, "user_name": new_user.name})
            res.status_code = 201
            return res
    except Exception as e:  # pragma: no cover
        logs.error(
            helpers.logger,
            {"msg": "Unknown error when creating a new user.", "new_user_name": user_name},
            err=e,
        )
        raise e


@bp.route("/room/create", methods=["POST"])
@helpers.auth_required(inject_user_data=True)
async def create_new_room_token(user_data: UserData) -> Response:
    """Create a new room token and return the hash and name in the response."""

    body = await request.get_json()
    bad_req = helpers.validate_required_fields(body, ["room_name"])
    if bad_req is not None:
        return bad_req
    room_name = body["room_name"]
    try:
        try:
            async with db.get_session() as session:
                new_room = await db.create_room(
                    session, room_name=room_name, creator_id=user_data["user_id"]
                )
                await session.commit()
        except IntegrityError as e:
            constraint_violation = db.parse_constraint_error(e)
            if constraint_violation == db.ConstraintViolation.UNIQUE:
                return helpers.bad_request("User already owns room with this name")
            else:  # pragma: no cover
                logs.error(
                    helpers.logger,
                    {
                        "msg": "Unknown error creating room.",
                        "constraint_violation": constraint_violation.name,
                    },
                    err=e,
                )
                raise e
        else:
            res = jsonify({"room_hash": new_room.id, "room_name": new_room.name})
            res.status_code = 201
            return res
    except Exception as e:  # pragma: no cover
        logs.error(
            helpers.logger,
            {
                "msg": "Unknown error when creating a new chatroom.",
                "new_room_name": room_name,
                "user_id": user_data["user_id"],
            },
            err=e,
        )
        raise e


@bp.route("/user/rooms/joined", methods=["GET"])
@helpers.auth_required(inject_user_data=True)
async def get_all_joined_rooms(user_data: UserData) -> Response:
    """Return a list of all chatrooms that the authenticated user has joined."""

    async with db.get_session() as session:
        stmt = select(db.models.Room)
        stmt = stmt.where(db.models.Room.members.any(db.models.User.id == user_data["user_id"]))
        rooms = (await session.execute(stmt)).scalars().all()
        results = [{"room_hash": room.id, "room_name": room.name} for room in rooms]
        return jsonify(results)


@bp.route("/user/rooms/owned", methods=["GET"])
@helpers.auth_required(inject_user_data=True)
async def get_all_owned_rooms(user_data: UserData) -> Response:
    """Return a list of all chatrooms that the authenticated user owns."""

    async with db.get_session() as session:
        stmt = select(db.models.Room)
        stmt = stmt.where(db.models.Room.owner_id == user_data["user_id"])
        rooms = (await session.execute(stmt)).scalars().all()
        results = [{"room_hash": room.id, "room_name": room.name} for room in rooms]
        return jsonify(results)


@bp.route("/room/<room_token>/join", methods=["PUT"])
@helpers.auth_required(inject_user_data=True)
async def join_room(room_token: str, user_data: UserData) -> Response:
    """Adds the logged in user to a chatroom's list of members.

    Gives 400 response if the user is already a member of this room.
    """

    try:
        try:
            async with db.get_session() as session:
                await db.add_user_to_room(session, user_id=user_data["user_id"], room_id=room_token)
                await session.commit()
        except IntegrityError as e:
            constraint_violation = db.parse_constraint_error(e)
            if constraint_violation == db.ConstraintViolation.UNIQUE:
                return helpers.bad_request("User is already a member of this room")
            else:  # pragma: no cover
                logs.error(
                    helpers.logger,
                    {
                        "msg": "Unknown error adding user to room.",
                        "constraint_violation": constraint_violation.name,
                    },
                    err=e,
                )
                raise e
        else:
            async with db.get_session() as session:
                room = await db.get_room_by_id(session, room_token)
                await session.commit()
                res = jsonify({"room_token": room.id, "room_name": room.name})
                res.status_code = 200
                return res
    except Exception as e:  # pragma: no cover
        logs.error(
            helpers.logger,
            {"msg": "Error when adding member to chatroom.", "room_token": room_token},
            err=e,
        )
        raise e


@bp.route("/room/<room_token>/members", methods=["GET"])
@helpers.auth_required(inject_user_data=False)
async def get_all_room_members(room_token: str) -> Response:
    """Return user names and ids for all users that have joined this chatroom."""

    async with db.get_session() as session:
        room = await db.get_room_by_id(session, room_token)
        members = room.members
        results = [{"user_name": member.name, "user_id": member.id} for member in members]
        return jsonify(results)
