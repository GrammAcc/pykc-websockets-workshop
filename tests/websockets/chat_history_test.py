import asyncio
import datetime
import json

import pytest
import websockets
from sqlalchemy import select

import tests
from pykcworkshop import chat, utils

REFERENCE_TS: int = int(
    datetime.datetime(year=2002, month=6, day=15, tzinfo=datetime.UTC).timestamp() * 1000
)

HISTORY_ROOM_NAME: str = "History Room"


@pytest.fixture
async def fixt_history_room():
    async def _():
        async with chat.db.get_session() as session:
            return (
                await session.execute(
                    select(chat.db.models.Room).where(chat.db.models.Room.name == HISTORY_ROOM_NAME)
                )
            ).scalar_one()

    return _


@pytest.fixture(autouse=True, scope="module")
async def generate_message_history():
    """Populates the db with historical chat message data."""

    await tests.helpers.seed_db()
    async with chat.db.get_session() as session:
        CREATOR_ID = (await chat.db.get_user_by_id(session, 2)).id
        history_room = await chat.db.create_room(
            session, room_name=HISTORY_ROOM_NAME, creator_id=CREATOR_ID
        )
        futures = [
            asyncio.create_task(
                chat.db.create_chat_message(
                    session,
                    author_id=CREATOR_ID,
                    room_id=history_room.id,
                    content=f"Party like it's 1999 plus {i}",
                    timestamp=datetime.datetime(year=1999, month=12, day=31, tzinfo=datetime.UTC)
                    + datetime.timedelta(seconds=(i)),
                )
            )
            for i in range(1000)
        ]
        await asyncio.gather(*futures)
        await session.commit()
    yield


@pytest.fixture
async def fixt_history_url(fixt_history_room):
    """The websocket url for the chat-history endpoint for `test_room`."""

    history_room = await fixt_history_room()
    return f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/room/{history_room.id}/chat-history"


async def test_chunk_size(fixt_ws_headers_testy, fixt_history_url):
    """The chat-history websocket should give an array of chat messages with
    a length matching the `chunk_size` it was provided."""

    conn = await websockets.connect(fixt_history_url, extra_headers=fixt_ws_headers_testy)
    for chunk in range(100):
        sz = chunk + 1
        await conn.send(json.dumps({"timestamp": REFERENCE_TS, "chunk_size": sz}))
        msg = await conn.recv()
        data = json.loads(msg)
        assert len(data) == sz
    await conn.close()


async def test_result_ordering(fixt_ws_headers_testy, fixt_history_url):
    """The chat-history websocket should give an array of chat messages in
    reverse-chronological order."""

    conn = await websockets.connect(fixt_history_url, extra_headers=fixt_ws_headers_testy)
    await conn.send(json.dumps({"timestamp": REFERENCE_TS, "chunk_size": 100}))
    msg = await conn.recv()
    await conn.close()
    data = json.loads(msg)
    prev_timestamp = datetime.datetime.now(datetime.UTC)
    for msg in data:
        ts = datetime.datetime.fromisoformat(msg["timestamp"])
        assert ts < prev_timestamp
        prev_timestamp = ts
