import pytest

from pykcworkshop import chat, utils


@pytest.fixture
async def fixt_ws_headers_csrf_only():
    return {"Sec-WebSocket-Protocol": f"wamp, csrf{chat.tokens.generate_csrf()}"}


@pytest.fixture
async def fixt_ws_headers_testy(fixt_testy):
    return {
        "Sec-WebSocket-Protocol": f"wamp, Bearer{(await fixt_testy()).token.token}, csrf{chat.tokens.generate_csrf()}"
    }


@pytest.fixture
async def fixt_ws_headers_testier(fixt_testier):
    return {
        "Sec-WebSocket-Protocol": f"wamp, Bearer{(await fixt_testier()).token.token}, csrf{chat.tokens.generate_csrf()}"
    }


@pytest.fixture
async def fixt_ws_headers_testiest(fixt_testiest):
    return {
        "Sec-WebSocket-Protocol": f"wamp, Bearer{(await fixt_testiest()).token.token}, csrf{chat.tokens.generate_csrf()}"
    }


@pytest.fixture(
    params=[
        "/room/{room_hash}/chat-message",
        "/room/{room_hash}/member-status",
        "/room/{room_hash}/client-sync",
        "/room/{room_hash}/chat-history",
        "/{user_id}/direct-message",
    ],
    ids=["chat-message", "member-status", "client-sync", "chat-history", "direct-message"],
)
async def fixt_ws_secured_endpoints(request, fixt_test_room, fixt_testy):
    test_room = await fixt_test_room()
    testy = await fixt_testy()
    return (
        utils.get_domain().replace("http", "ws")
        + "/chat/api/v1"
        + request.param.format(room_hash=test_room.id, user_id=testy.id)
    )


@pytest.fixture(
    params=[
        "/room/{room_hash}/chat-message",
        "/room/{room_hash}/member-status",
        "/room/{room_hash}/client-sync",
    ],
    ids=["chat-message", "member-status", "client-sync"],
)
async def fixt_ws_m2m_endpoints(request, fixt_test_room):
    test_room = await fixt_test_room()
    return (
        utils.get_domain().replace("http", "ws")
        + "/chat/api/v1"
        + request.param.format(room_hash=test_room.id)
    )


@pytest.fixture(params=["/{user_id}/direct-message"], ids=["direct-message"])
async def fixt_ws_p2p_endpoints(request, fixt_testy):
    testy = await fixt_testy()
    return (
        utils.get_domain().replace("http", "ws")
        + "/chat/api/v1"
        + request.param.format(user_id=testy.id)
    )


@pytest.fixture(
    params=[
        "/room/{room_hash}/chat-history",
        "/form-validation",
    ],
    ids=["chat-history", "form-validation"],
)
async def fixt_ws_121_endpoints(request, fixt_test_room):
    test_room = await fixt_test_room()
    return (
        utils.get_domain().replace("http", "ws")
        + "/chat/api/v1"
        + request.param.format(room_hash=test_room.id)
    )


@pytest.fixture(
    params=[
        "/room/{room_hash}/chat-message",
        "/room/{room_hash}/member-status",
        "/room/{room_hash}/client-sync",
        "/room/{room_hash}/chat-history",
        "/{user_id}/direct-message",
        "/form-validation",
    ],
    ids=[
        "chat-message",
        "member-status",
        "client-sync",
        "chat-history",
        "direct-message",
        "form-validation",
    ],
)
async def fixt_ws_all_endpoints(request, fixt_test_room, fixt_testy):
    test_room = await fixt_test_room()
    testy = await fixt_testy()
    return (
        utils.get_domain().replace("http", "ws")
        + "/chat/api/v1"
        + request.param.format(room_hash=test_room.id, user_id=testy.id)
    )
