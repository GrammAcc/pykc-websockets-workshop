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

OLDEST_DATETIME: int = datetime.datetime(year=1999, month=12, day=31, tzinfo=datetime.UTC)


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
        CREATOR_ID = (await chat.db.get_user_by_name(session, "Testy")).id
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
                    timestamp=(OLDEST_DATETIME + datetime.timedelta(seconds=(i))),
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
        await conn.send(json.dumps({"timestamp": REFERENCE_TS, "chunk_size": sz, "newer": False}))
        msg = await conn.recv()
        data = json.loads(msg)
        assert len(data) == sz
    await conn.close()


async def test_older_ordering(fixt_ws_headers_testy, fixt_history_url):
    """The chat-history websocket should give an array of chat messages in
    reverse-chronological order when `newer` is False."""

    conn = await websockets.connect(fixt_history_url, extra_headers=fixt_ws_headers_testy)
    await conn.send(json.dumps({"timestamp": REFERENCE_TS, "chunk_size": 100, "newer": False}))
    msg = await conn.recv()
    await conn.close()
    data = json.loads(msg)
    prev_timestamp = datetime.datetime.now(datetime.UTC)
    for msg in data:
        ts = datetime.datetime.fromisoformat(msg["timestamp"])
        assert ts < prev_timestamp
        prev_timestamp = ts


async def test_newer_ordering(fixt_ws_headers_testy, fixt_history_url):
    """The chat-history websocket should give an array of chat messages in
    chronological order when `newer` is True."""

    conn = await websockets.connect(fixt_history_url, extra_headers=fixt_ws_headers_testy)
    await conn.send(
        json.dumps(
            {"timestamp": OLDEST_DATETIME.timestamp() * 1000, "chunk_size": 100, "newer": True}
        )
    )
    msg = await conn.recv()
    await conn.close()
    data = json.loads(msg)
    prev_timestamp = OLDEST_DATETIME
    for msg in data:
        ts = datetime.datetime.fromisoformat(msg["timestamp"])
        assert ts > prev_timestamp
        prev_timestamp = ts


async def test_newer(fixt_ws_headers_testy, fixt_history_url):
    """The chat-history websocket should give messages newer than the reference
    timestamp when the `newer` field is true."""

    conn = await websockets.connect(fixt_history_url, extra_headers=fixt_ws_headers_testy)
    await conn.send(
        json.dumps(
            {"timestamp": OLDEST_DATETIME.timestamp() * 1000, "chunk_size": 100, "newer": True}
        )
    )
    msg = await conn.recv()
    await conn.close()
    data = json.loads(msg)
    first_dt = datetime.datetime.fromisoformat(data[0]["timestamp"])
    assert first_dt > OLDEST_DATETIME
    last_dt = datetime.datetime.fromisoformat(data.pop()["timestamp"])
    assert last_dt == OLDEST_DATETIME + datetime.timedelta(seconds=100)


async def test_result_is_older_than_ref_timestamp(
    fixt_ws_headers_testy, fixt_history_url, fixt_testy, fixt_history_room
):
    """The chat history websocket should only return results that are older than the reference
    timestamp. Since these are in reverse-chronological order, this means that the first
    result in the returned array should be the newest message that is older than the reference
    timestamp."""

    testy = await fixt_testy()
    history_room = await fixt_history_room()
    newer = utils.now()
    older = newer - datetime.timedelta(seconds=1)
    async with chat.db.get_session() as session:
        newer_message = await chat.db.create_chat_message(
            session,
            author_id=testy.id,
            room_id=history_room.id,
            content="Newer message",
            timestamp=newer,
        )
        older_message = await chat.db.create_chat_message(
            session,
            author_id=testy.id,
            room_id=history_room.id,
            content=newer_message.content + "something to ensure these are different.",
            timestamp=older,
        )
        await session.commit()  # populate PKs.

    conn = await websockets.connect(fixt_history_url, extra_headers=fixt_ws_headers_testy)
    await conn.send(
        json.dumps({"timestamp": newer.timestamp() * 1000, "chunk_size": 1, "newer": False})
    )
    msg = await conn.recv()
    await conn.close()
    data = json.loads(msg)
    assert data[0]["content"] == older_message.content
