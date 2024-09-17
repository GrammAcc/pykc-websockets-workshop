import websockets

from pykcworkshop import chat


async def test_secured_websockets_require_auth(fixt_client, fixt_ws_secured_endpoints):
    """All secured websocket endpoints should return a 401 response if accessed
    without a valid user token."""

    headers = {"Sec-WebSocket-Protocol": f"Bearerbad_token, csrf{chat.tokens.generate_csrf()}"}

    try:
        await websockets.connect(fixt_ws_secured_endpoints, extra_headers=headers)
    except websockets.exceptions.InvalidStatusCode as e:
        assert e.status_code == 401
    else:
        assert False, "Did not raise"


async def test_all_websockets_require_csrf(
    fixt_client, fixt_ws_all_endpoints, fixt_ws_headers_testy, fixt_forged_csrf_token
):
    """All websocket endpoints should return a 401 response if accessed
    with a forged csrf token."""

    subprotocol_string = ",".join(
        [
            fixt_ws_headers_testy["Sec-WebSocket-Protocol"].split(",")[1],
            f"csrf{fixt_forged_csrf_token}",
        ]
    )
    headers = {"Sec-WebSocket-Protocol": subprotocol_string}

    try:
        await websockets.connect(fixt_ws_all_endpoints, extra_headers=headers)
    except websockets.exceptions.InvalidStatusCode as e:
        assert e.status_code == 401
    else:
        assert False, "Did not raise"
