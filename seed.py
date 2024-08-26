"""Seed the application db without running the Quart app."""

if __name__ != "__main__":
    raise ImportError("Standalone script cannot be imported!")

import asyncio
import datetime

from pykcworkshop.chat import db


async def seed_db():
    db.connect("sqlite+aiosqlite:///src/instance/pykcworkshop.db")
    await db.initialize(drop_tables=True)
    async with db.get_session() as session:
        test_user, test_user_token = await db.create_user(session, user_name="TestUser")
        test_room = await db.create_room(session, room_name="Sequencer", creator_id=test_user.id)
        futures = [
            asyncio.create_task(
                db.create_chat_message(
                    session,
                    author_id=test_user.id,
                    room_id=test_room.id,
                    content=str(i),
                    timestamp=datetime.datetime.now(datetime.UTC)
                    - datetime.timedelta(seconds=(i * 2)),
                )
            )
            for i in range(10000)
        ]
        await asyncio.gather(*futures)
        await session.commit()
        print(test_user_token.id)


asyncio.run(seed_db())
