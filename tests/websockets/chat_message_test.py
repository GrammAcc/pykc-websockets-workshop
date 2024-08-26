import asyncio
import json

import pytest
import websockets
from sqlalchemy import func, select

from pykcworkshop import chat, utils


async def test_chat_message_timestamp(fixt_ws_headers_testy, fixt_test_room, fixt_testy):
    """The chat message websocket should add a timestamp to every message."""

    test_room = await fixt_test_room()
    testy = await fixt_testy()
    sock_url = (
        f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/room/{test_room.id}/chat-message"
    )
    testy_conn = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_testy)
    await testy_conn.send(json.dumps({"user_name": testy.name, "content": "Test Content"}))
    msg = await testy_conn.recv()
    await testy_conn.close()
    data = json.loads(msg)
    assert "timestamp" in data


async def test_throw_out_empty_messages(fixt_ws_headers_testy, fixt_test_room, fixt_testy):
    """The chat message websocket should silently discard messages with an empty content
    field."""

    test_room = await fixt_test_room()
    testy = await fixt_testy()

    async def _get_msg_count() -> int:
        async with chat.db.get_session() as session:
            _count = (
                await session.execute(
                    select(func.count()).select_from(
                        select(chat.db.models.ChatMessage)
                        .where(chat.db.models.ChatMessage.author_id == testy.id)
                        .subquery()
                    )
                )
            ).scalar_one()
            return _count

    before_count = await _get_msg_count()

    sock_url = (
        f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/room/{test_room.id}/chat-message"
    )
    testy_conn = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_testy)
    await testy_conn.send(json.dumps({"user_name": testy.name, "content": ""}))

    with pytest.raises(asyncio.TimeoutError):
        # There's no way to actually assert that a message wasn't broadcast, so
        # we set a timeout that is longer than it should reasonably take for
        # the server to send a message back and check if it raises.
        async with asyncio.timeout(1):
            await testy_conn.recv()
    await testy_conn.close()
    after_count = await _get_msg_count()
    assert after_count == before_count  # Ensure the message didn't get saved to the db.
