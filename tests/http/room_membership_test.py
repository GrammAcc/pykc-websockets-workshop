import pytest


async def test_get_joined_rooms_for_user_basic_usage(
    fixt_client, fixt_test_room, fixt_http_headers_testy
):
    """The get joined rooms endpoint should return an array of room names and hashes
    for all rooms that the provided user token has joined."""

    test_room = await fixt_test_room()
    res = await fixt_client.get("/chat/api/v1/user/rooms/joined", headers=fixt_http_headers_testy)
    data = await res.get_json()
    assert len(data) == 1
    assert data[0]["room_name"] == test_room.name
    assert data[0]["room_hash"] == test_room.id


@pytest.mark.usefixtures("reset_db")
async def test_join_room_basic_usage(
    fixt_client, fixt_testiest, fixt_test_room, fixt_http_headers_csrf_only
):
    """The join room endpoint should add a user to the room's list of members."""

    testiest = await fixt_testiest()
    test_room = await fixt_test_room()
    auth_headers = {"Authorization": f"Bearer {testiest.hashed_token.token}"}
    auth_headers.update(fixt_http_headers_csrf_only)
    await fixt_client.put(f"/chat/api/v1/room/{test_room.id}/join", headers=auth_headers)
    joined_rooms = (await fixt_testiest()).joined_rooms
    assert len(joined_rooms) == 1
    assert test_room.id == joined_rooms[0].id


async def test_join_room_400_when_user_already_joined(
    fixt_client, fixt_test_room, fixt_http_headers_testy
):
    """The join room endpoint should return a 400 status if the user is already a member of
    the room."""

    test_room = await fixt_test_room()
    res = await fixt_client.put(
        f"/chat/api/v1/room/{test_room.id}/join", headers=fixt_http_headers_testy
    )
    assert res.status_code == 400


async def test_get_room_members_basic_usage(
    fixt_client, fixt_testy, fixt_testier, fixt_test_room, fixt_http_headers_testy
):
    """The room members endpoint should return the user name and hash for all
    current members of the provided room."""

    test_room = await fixt_test_room()
    testy = await fixt_testy()
    testier = await fixt_testier()
    res = await fixt_client.get(
        f"/chat/api/v1/room/{test_room.id}/members", headers=fixt_http_headers_testy
    )
    assert res.status_code == 200
    data = sorted(await res.get_json(), key=lambda d: d["user_name"])
    assert len(data) == 2
    assert data[0]["user_name"] == testier.name
    assert data[0]["user_id"] == testier.id
    assert data[1]["user_name"] == testy.name
    assert data[1]["user_id"] == testy.id


async def test_get_user_owned_rooms(fixt_client, fixt_test_room, fixt_http_headers_testy):
    """The get owned rooms endpoint should return an array of all the rooms
    the logged in user owns."""

    test_room = await fixt_test_room()
    res = await fixt_client.get("/chat/api/v1/user/rooms/owned", headers=fixt_http_headers_testy)
    data = await res.get_json()
    assert len(data) == 1
    assert data[0]["room_name"] == test_room.name
    assert data[0]["room_hash"] == test_room.id
