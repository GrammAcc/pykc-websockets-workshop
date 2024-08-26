"""Functions for managing db connections and making common queries.

Important:
    The querying functions in this module accept an `async_scoped_session`
    as their first argument and they use this session to make all of their queries, but
    they do not call `.commit()` on the session object unless it is required for the
    internal consistency of the function. This means that when using these
    functions, we have to call `get_session()` to obtain a session reference, and
    call `.commit()` on that session instance at the callsite. These functions are
    structured this way both for performance and for flexibility. We avoid creating
    extraneous connections, and we have explicit control over when we start and end each
    transaction.
"""

import asyncio
import datetime
import hashlib
import os

import jwt
from dotenv import load_dotenv
from sqlalchemy import delete, event, insert, select
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import ConnectionPoolEntry

from pykcworkshop import utils
from pykcworkshop.chat.db import models

load_dotenv()


_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_Session = async_scoped_session(
    async_sessionmaker(bind=_engine, expire_on_commit=False),
    scopefunc=asyncio.current_task,
)


def _enable_sqlite_fks(dbapi_con: DBAPIConnection, connection_record: ConnectionPoolEntry):
    if _engine.dialect.name == "sqlite":  # pragma: no cover
        dbapi_con.cursor().execute("PRAGMA foreign_keys = ON;")


event.listen(_engine.sync_engine, "connect", _enable_sqlite_fks)


async def initialize(drop_tables: bool = False) -> None:
    """Create all tables and required rows such as the system user.

    If `drop_tables` is True, drops the entire db and recreates from scratch.

    This function is safe to call on an existing db if `drop_tables` is False, so
    it should be called on application startup.
    """

    async with _engine.begin() as conn:
        if drop_tables:
            await conn.run_sync(models.BaseModel.metadata.drop_all)
        await conn.run_sync(models.BaseModel.metadata.create_all)
    async with get_session() as session:
        try:
            await get_system_user(session)
        except NoResultFound:
            await create_user(session, user_name="System")  # Create system user.


async def create_user(
    session: AsyncSession,
    *,
    user_name: str,
    token_expiration: datetime.timedelta = datetime.timedelta(days=365),
) -> tuple[models.User, models.HashedToken]:
    """Create and add a new user to the db.

    Returns a 2-tuple containing the newly created user and their token.
    """

    async with get_session() as local_session:
        new_user = models.User(name=user_name)
        local_session.add(new_user)
        await local_session.commit()  # Commit to populate PK.
    session.add(new_user)
    now = utils.now()
    payload = {
        "user_id": new_user.id,
        "user_name": user_name,
        "exp": now + token_expiration,
        "iat": now,
    }
    token = jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")

    token_hash = hashlib.sha512(token.encode()).hexdigest()
    shortened_hash = hashlib.sha1(token_hash.encode()).hexdigest()
    new_hashed_token = models.HashedToken(id=shortened_hash, token=token)
    session.add(new_hashed_token)
    new_user.hashed_token = new_hashed_token

    return new_user, new_hashed_token


async def create_room(session: AsyncSession, *, room_name: str, creator_id: int) -> models.Room:
    """Create and add a new chatroom to the db.

    Returns the newly created room.
    """

    token = jwt.encode(
        {"room_name": room_name, "creator_id": creator_id},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )

    token_hash = hashlib.sha512(token.encode()).hexdigest()
    shortened_hash = hashlib.sha1(token_hash.encode()).hexdigest()

    async with get_session() as local_session:
        new_room = models.Room(id=shortened_hash, name=room_name, owner_id=creator_id)
        local_session.add(new_room)
        await local_session.commit()  # Commit to populate PK.
    session.add(new_room)
    await add_user_to_room(session, user_id=creator_id, room_id=new_room.id)

    return new_room


async def get_user_by_id(session: AsyncSession, user_id: int) -> models.User:
    """Fetch a single user row by PK."""

    stmt = select(models.User).where(models.User.id == user_id)
    return (await session.execute(stmt)).scalar_one()


async def get_user_by_name(session: AsyncSession, user_name: str) -> models.User:
    stmt = select(models.User).where(models.User.name == user_name)
    return (await session.execute(stmt)).scalar_one()


async def get_room_by_id(session: AsyncSession, room_id: str) -> models.Room:
    """Fetch a single room row by PK."""

    stmt = select(models.Room).where(models.Room.id == room_id)
    return (await session.execute(stmt)).scalar_one()


async def get_room_by_name(session: AsyncSession, room_name: str) -> models.Room:
    stmt = select(models.Room).where(models.Room.name == room_name)
    return (await session.execute(stmt)).scalar_one()


async def get_system_user(session: AsyncSession) -> models.User:
    """Fetch the system user from the db."""

    stmt = select(models.User).where(models.User.name == "System")
    return (await session.execute(stmt)).scalar_one()


async def get_jwt_by_hash(session: AsyncSession, token_hash: str) -> str:
    """Fetch the actual jwt token from the db by its hash.

    This also checks that the token hasn't been manually revoked.
    The `.scalar_one` call will raise a `sqlalchemy.exc.NoResultFound` error if
    the token is revoked or the provided hash is invalid.

    Important:
        The returned token string still needs to be validated with the `jwt.decode`
        function.
    """

    stmt = (
        select(models.HashedToken.token)
        .where(models.HashedToken.id == token_hash)
        .where(models.HashedToken.is_revoked == False)
    )
    return (await session.execute(stmt)).scalar_one()


async def add_user_to_room(session: AsyncSession, *, user_id: int, room_id: str) -> None:
    """Adds user with id `user_id` to the list of members in room with id `room_id`."""

    stmt = insert(models.table_room_member).values(room_id=room_id, member_id=user_id)
    await session.execute(stmt)
    system_user = await get_system_user(session)
    joining_user = await get_user_by_id(session, user_id)
    await create_chat_message(
        session,
        author_id=system_user.id,
        room_id=room_id,
        content=f"{joining_user.name} has joined the chat.",
    )


async def remove_user_from_room(session: AsyncSession, *, user_id: int, room_id: str) -> None:
    """Removes user with id `user_id` from the list of members in room with id `room_id`.

    Raises:
        IntegrityError:
            If the user is not a member of the room.
    """

    raise NotImplementedError("Removing a user from a room is not implemented yet.")

    stmt = delete(models.table_room_member).where(
        models.table_room_member.c.room_id == room_id,
        models.table_room_member.c.member_id == user_id,
    )
    await session.execute(stmt)
    system_user = await get_system_user(session)
    leaving_user = await get_user_by_id(session, user_id)
    await create_chat_message(
        session,
        author_id=system_user.id,
        room_id=room_id,
        content=f"{leaving_user.name} has left the chat.",
    )


async def create_chat_message(
    session: AsyncSession,
    *,
    author_id: int,
    room_id: str,
    content: str,
    timestamp: datetime.datetime | None = None,
) -> models.ChatMessage:
    """Create and add a new chat message to the db.

    Returns the newly created `pykcworkshop.chat.db.models.ChatMessage` instance.

    All keyword arguments are required except for `timestamp`.
    If `timestamp` is not provided or `None` is passed explicitly, then
    the current UTC time is used as a default.
    """

    chat_message = models.ChatMessage(
        author_id=author_id,
        room_id=room_id,
        content=content,
        timestamp=timestamp if timestamp is not None else utils.now(),
    )
    session.add(chat_message)
    return chat_message


def connect(db_uri: str, debug: bool = False) -> None:
    """Update the sqlalchemy async engine and scoped session to connect to
    the db at `db_uri`.

    If `debug` is True, then emit generated sql.
    """

    global _engine
    global _Session
    _engine = create_async_engine(db_uri, echo=debug)
    _Session = async_scoped_session(
        async_sessionmaker(bind=_engine, expire_on_commit=False),
        scopefunc=asyncio.current_task,
    )

    event.listen(_engine.sync_engine, "connect", _enable_sqlite_fks)


def get_session() -> AsyncSession:
    """Get a reference to the async scoped session suitable for use in an async context manager.

    This needs to be used anytime we make db queries in the database, and it can be passed
    into any of the querying functions in this module as the first argument.
    """

    return _Session()


def get_session_proxy() -> async_scoped_session:
    """Get a reference to the proxy object of the async scoped session.

    This can be used the same way as `get_session`, but in general, this
    function should not be used unless the proxy object itself is needed.

    For example, when cleaning up reasources in quart's appteardown handler.
    """

    return _Session
