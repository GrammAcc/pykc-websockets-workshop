import asyncio
import datetime
from pathlib import Path
from typing import Generator

import jwt
import pytest
from sqlalchemy import select

import tests
from pykcworkshop import async_create_app, chat


def pytest_sessionstart(session):
    chat.db.connect("sqlite+aiosqlite:///tmp.db")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Pytest-asyncio uses a function-scope event loop for each test case, but
    this causes problems when using fixtures with session scope, so we have to override
    the `event_loop` fixture provided by pytest-asyncio to make it session scope so that
    everything will run in a single event loop.

    This should be removed once the fixture scoping issues in version 0.23 are resolved
    and the pytest-asyncio dep can be unpinned from version 0.21.
    """

    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def fixt_app():
    """The quart application in dev mode."""

    testing_config = {"DB_URI": "sqlite+aiosqlite:///tmp.db"}

    # We can't call the sync `create_app` function because it uses `asyncio.run`, which
    # breaks pytest-asyncio.
    # See: https://github.com/pytest-dev/pytest-asyncio/issues/658#issuecomment-1818847613
    app = await async_create_app(chat_config=testing_config)

    yield app


@pytest.fixture
async def fixt_client(fixt_app):
    """The client used to make requests to the application under test."""

    return fixt_app.test_client()


@pytest.fixture(scope="session")
async def fixt_prod_app():
    """The quart application in dev mode with production-equivalent data."""

    db_path = Path("tests/chat/prod_data.db").absolute()

    if not db_path.exists():
        raise Exception(
            "Production-equivalent database not found. \
Copy the production database to 'tests/chat/prod_data.db' before running the testsuite."
        )

    testing_config = {"DB_URI": "".join(["sqlite+aiosqlite:///", str(db_path)])}

    # We can't call the sync `create_app` function because it uses `asyncio.run`, which
    # breaks pytest-asyncio.
    # See: https://github.com/pytest-dev/pytest-asyncio/issues/658#issuecomment-1818847613
    app = await async_create_app(chat_config=testing_config)

    yield app


@pytest.fixture
async def fixt_prod_client(fixt_prod_app):
    """The client used to make requests to the application under test using
    production-equivalent data."""

    return fixt_prod_app.test_client()


@pytest.fixture
async def fixt_runner(fixt_app):
    """The CLI test runner for the quart application."""

    return fixt_app.test_cli_runner()


@pytest.fixture(autouse=True, scope="session")
async def init_test_db():
    await tests.helpers.seed_db()
    yield


@pytest.fixture(autouse=False)
async def reset_db():
    await tests.helpers.seed_db()
    yield
    await tests.helpers.seed_db()


@pytest.fixture
async def fixt_testy():
    async def _():
        async with chat.db.get_session() as session:
            return (
                await session.execute(
                    select(chat.db.models.User).where(chat.db.models.User.name == "Testy")
                )
            ).scalar_one()

    return _


@pytest.fixture
async def fixt_testier():
    async def _():
        async with chat.db.get_session() as session:
            return (
                await session.execute(
                    select(chat.db.models.User).where(chat.db.models.User.name == "Testier")
                )
            ).scalar_one()

    return _


@pytest.fixture
async def fixt_testiest():
    async def _():
        async with chat.db.get_session() as session:
            return (
                await session.execute(
                    select(chat.db.models.User).where(chat.db.models.User.name == "Testiest")
                )
            ).scalar_one()

    return _


@pytest.fixture
async def fixt_test_room():
    async def _():
        async with chat.db.get_session() as session:
            return (
                await session.execute(
                    select(chat.db.models.Room).where(chat.db.models.Room.name == "Test Room")
                )
            ).scalar_one()

    return _


@pytest.fixture
async def fixt_test_messages(fixt_test_room):
    async def _():
        test_room = await fixt_test_room()
        async with chat.db.get_session() as session:
            return (
                (
                    await session.execute(
                        select(chat.db.models.ChatMessage).where(
                            chat.db.models.ChatMessage.room_id == test_room.id
                        )
                    )
                )
                .scalars()
                .all()
            )

    return _


@pytest.fixture
async def fixt_forged_csrf_token():
    now = datetime.datetime.now(datetime.UTC)
    return jwt.encode(
        {"exp": now + datetime.timedelta(days=31), "iat": now},
        "bad_signing_secret",
        algorithm="HS256",
    )
