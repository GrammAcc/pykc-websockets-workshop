import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

import tests
from pykcworkshop import chat, utils


async def test_user_login_basic_usage(fixt_client, fixt_testy, fixt_http_headers_csrf_only):
    """The user login endpoint should return the user name and hash."""

    testy = await fixt_testy()
    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/user/login",
        json={"user_hash": testy.hashed_token.id},
        headers=fixt_http_headers_csrf_only,
    )
    assert res.status_code == 200
    data = await res.get_json()
    assert data["user_name"] == testy.name
    assert data["user_id"] == testy.id
    assert data["user_token"] == testy.hashed_token.token


async def test_user_login_401_when_invalid_jwt(fixt_client, fixt_http_headers_csrf_only):
    """The user login endpoint should return a 401 response if the provided
    jwt is invalid."""

    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/user/login",
        json={"user_hash": "invalid-token"},
        headers=fixt_http_headers_csrf_only,
    )
    assert res.status_code == 401


async def test_user_login_401_when_expired_jwt(fixt_client, fixt_http_headers_csrf_only):
    """The user login endpoint should return a 401 response if the provided
    jwt is expired."""

    async with chat.db.get_session() as session:
        new_user, expired_user_token = await chat.db.create_user(
            session, user_name="New User", token_expiration=datetime.timedelta(0)
        )

    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/user/login",
        json={"user_hash": expired_user_token.id},
        headers=fixt_http_headers_csrf_only,
    )
    assert res.status_code == 401


async def test_user_login_400_when_missing_user_hash(fixt_client, fixt_http_headers_csrf_only):
    """The user login endpoint should return a 400 response if a `user_hash` is not
    provided in the request body."""

    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/user/login", json={}, headers=fixt_http_headers_csrf_only
    )
    assert res.status_code == 400


@pytest.mark.usefixtures("reset_db")
async def test_create_user_basic_usage(fixt_client, fixt_http_headers_csrf_only):
    """The create user endpoint should create a new User record."""

    new_user_name = "New User"
    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/user/create",
        json={"user_name": new_user_name},
        headers=fixt_http_headers_csrf_only,
    )
    assert res.status_code == 201
    async with chat.db.get_session() as session:
        with tests.helpers.does_not_raise(NoResultFound):
            (
                await session.execute(
                    select(chat.db.models.User).where(chat.db.models.User.name == new_user_name)
                )
            ).scalar_one()


async def test_create_user_400_when_user_name_taken(
    fixt_client, fixt_testy, fixt_http_headers_csrf_only
):
    """The create user endpoint should return a 400 response if the provided
    user name is already taken."""

    testy = await fixt_testy()
    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/user/create",
        json={"user_name": testy.name},
        headers=fixt_http_headers_csrf_only,
    )
    assert res.status_code == 400


async def test_create_user_400_when_missing_user_name(fixt_client, fixt_http_headers_csrf_only):
    """The create user endpoint should return a 400 response if a `user_name` is not
    provided in the request body."""

    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/user/create",
        json={},
        headers=fixt_http_headers_csrf_only,
    )
    assert res.status_code == 400


async def test_create_user_400_when_user_name_is_empty_string(
    fixt_client, fixt_http_headers_csrf_only
):
    """The create user endpoint should return a 400 response if the `user_name` is an
    empty string."""

    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/user/create",
        json={"user_name": ""},
        headers=fixt_http_headers_csrf_only,
    )
    assert res.status_code == 400
