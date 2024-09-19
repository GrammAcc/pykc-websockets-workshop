import asyncio
from contextlib import contextmanager

import pytest

from pykcworkshop.chat import db


@contextmanager
def does_not_raise(exception):
    """The opposite of `pytest.raises`."""

    try:
        yield
    except exception:
        raise pytest.fail("Raised {0}".format(exception))


_TESTY_PASSWORD: str = ""
_TESTIER_PASSWORD: str = ""
_TESTIEST_PASSWORD: str = ""


def testy_password() -> str:
    """Return the plaintext password of the user `testy`."""

    return _TESTY_PASSWORD


def testier_password() -> str:
    """Return the plaintext password of the user `testier`."""

    return _TESTIER_PASSWORD


def testiest_password() -> str:
    """Return the plaintext password of the user `testiest`."""

    return _TESTIEST_PASSWORD


async def seed_db() -> None:
    """Seed the database."""

    await db.initialize(drop_tables=True)
    print("Seeding the database...")
    async with db.get_session() as session:
        global _TESTY_PASSWORD
        global _TESTIER_PASSWORD
        global _TESTIEST_PASSWORD
        testy, _TESTY_PASSWORD = await db.create_user(session, user_name="Testy")
        testier, _TESTIER_PASSWORD = await db.create_user(session, user_name="Testier")
        testiest, _TESTIEST_PASSWORD = await db.create_user(session, user_name="Testiest")
        CREATOR_ID = testy.id
        test_room = await db.create_room(session, room_name="Test Room", creator_id=CREATOR_ID)
        await db.add_user_to_room(session, user_id=testier.id, room_id=test_room.id)
        futures = [
            asyncio.create_task(
                db.create_chat_message(
                    session, author_id=CREATOR_ID, room_id=test_room.id, content=str(i)
                )
            )
            for i in range(11)
        ]
        await asyncio.gather(*futures)
        await session.commit()
    print("Db seed complete!")
