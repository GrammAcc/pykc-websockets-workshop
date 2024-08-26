import asyncio
import json

import pytest
import websockets

from pykcworkshop import utils


async def test_direct_message_timestamp(fixt_ws_headers_testy, fixt_testy, fixt_testier):
    """The direct message websocket should add a timestamp to every message."""

    testy = await fixt_testy()
    testier = await fixt_testier()
    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/{testier.id}/direct-message"
    testy_conn = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_testy)
    await testy_conn.send(json.dumps({"user_name": testy.name, "content": "Test Content"}))
    msg = await testy_conn.recv()
    await testy_conn.close()
    data = json.loads(msg)
    assert "timestamp" in data


async def test_throw_out_empty_messages(fixt_ws_headers_testy, fixt_testy, fixt_testier):
    """The direct-message websocket should silently discard messages with an empty content
    field."""

    testy = await fixt_testy()
    testier = await fixt_testier()

    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/{testier.id}/direct-message"
    testy_conn = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_testy)
    await testy_conn.send(json.dumps({"user_name": testy.name, "content": ""}))

    with pytest.raises(asyncio.TimeoutError):
        # There's no way to actually assert that a message wasn't broadcast, so
        # we set a timeout that is longer than it should reasonably take for
        # the server to send a message back and check if it raises.
        async with asyncio.timeout(1):
            await testy_conn.recv()
    await testy_conn.close()
