import pytest
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

import tests
from pykcworkshop import chat, utils


async def test_room_data_basic_usage(fixt_client, fixt_test_room, fixt_http_headers_testy):
    """The room data endpoint should return the room name and hash."""

    test_room = await fixt_test_room()
    res = await fixt_client.get(
        f"{utils.get_domain()}/chat/api/v1/room/{test_room.id}", headers=fixt_http_headers_testy
    )
    assert res.status_code == 200
    data = await res.get_json()
    assert data["room_name"] == test_room.name
    assert data["room_hash"] == test_room.id


async def test_room_data_400_when_invalid_jwt(fixt_client, fixt_http_headers_testy):
    """The room data endpoint should return a 400 response if the provided
    jwt is invalid."""

    res = await fixt_client.get(
        f"{utils.get_domain()}/chat/api/v1/room/invalid-token", headers=fixt_http_headers_testy
    )
    assert res.status_code == 400


@pytest.mark.usefixtures("reset_db")
async def test_create_room_basic_usage(fixt_client, fixt_http_headers_testy):
    """The create room endpoint should create a new User record."""

    new_room_name = "New Room"
    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/room/create",
        json={"room_name": new_room_name},
        headers=fixt_http_headers_testy,
    )
    assert res.status_code == 201
    async with chat.db.get_session() as session:
        with tests.helpers.does_not_raise(NoResultFound):
            (
                await session.execute(
                    select(chat.db.models.Room).where(chat.db.models.Room.name == new_room_name)
                )
            ).scalar_one()


async def test_create_room_400_when_missing_room_name(fixt_client, fixt_http_headers_testy):
    """The create room endpoint should return a 400 response if a `room_name` is not
    provided in the request body."""

    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/room/create", json={}, headers=fixt_http_headers_testy
    )
    assert res.status_code == 400


async def test_create_room_400_when_room_name_is_empty_string(fixt_client, fixt_http_headers_testy):
    """The create room endpoint should return a 400 response if the `room_name` is an
    empty string."""

    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/room/create",
        json={"room_name": ""},
        headers=fixt_http_headers_testy,
    )
    assert res.status_code == 400


@pytest.mark.usefixtures("reset_db")
async def test_create_room_400_when_name_already_used_by_user(fixt_client, fixt_http_headers_testy):
    """The create room endpoint should return a 400 status if the user already owns a room
    with the provided name."""

    new_room_name = "New Room"
    res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/room/create",
        json={"room_name": new_room_name},
        headers=fixt_http_headers_testy,
    )
    assert res.status_code == 201
    async with chat.db.get_session() as session:
        with tests.helpers.does_not_raise(NoResultFound):
            (
                await session.execute(
                    select(chat.db.models.Room).where(chat.db.models.Room.name == new_room_name)
                )
            ).scalar_one()

    duplicate_res = await fixt_client.post(
        f"{utils.get_domain()}/chat/api/v1/room/create",
        json={"room_name": new_room_name},
        headers=fixt_http_headers_testy,
    )
    assert duplicate_res.status_code == 400
