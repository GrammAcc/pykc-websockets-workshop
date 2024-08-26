import pytest

from pykcworkshop import chat, utils

_secure_endpoints = [
    (
        "/room/{room_hash}",
        "GET",
        "room-data",
    ),
    (
        "/room/create",
        "POST",
        "create-room",
    ),
    (
        "/user/rooms/joined",
        "GET",
        "user-joined-rooms",
    ),
    (
        "/user/rooms/owned",
        "GET",
        "user-owned-rooms",
    ),
    (
        "/room/{room_hash}/join",
        "PUT",
        "join-room",
    ),
    (
        "/room/{room_hash}/members",
        "GET",
        "room-members",
    ),
]

_all_endpoints = _secure_endpoints + [
    (
        "/user/login",
        "POST",
        "user-login",
    ),
    (
        "/user/create",
        "POST",
        "create-user",
    ),
]


@pytest.fixture(
    params=[(i[0], i[1]) for i in _secure_endpoints], ids=[i[2] for i in _secure_endpoints]
)
async def fixt_http_secure_endpoints(request, fixt_test_room):
    test_room = await fixt_test_room()
    return (
        utils.get_domain() + "/chat/api/v1" + request.param[0].format(room_hash=test_room.id)
    ), request.param[1]


@pytest.fixture(params=[(i[0], i[1]) for i in _all_endpoints], ids=[i[2] for i in _all_endpoints])
async def fixt_http_all_endpoints(request, fixt_test_room):
    test_room = await fixt_test_room()
    return (
        utils.get_domain() + "/chat/api/v1" + request.param[0].format(room_hash=test_room.id)
    ), request.param[1]


@pytest.fixture
async def fixt_http_headers_testy(fixt_testy):
    return {
        "Authorization": f"Bearer {(await fixt_testy()).hashed_token.token}",
        "X-CSRF-TOKEN": chat.tokens.generate_csrf(),
    }


@pytest.fixture
async def fixt_http_headers_csrf_only(fixt_http_headers_testy):
    return {"X-CSRF-TOKEN": fixt_http_headers_testy["X-CSRF-TOKEN"]}
