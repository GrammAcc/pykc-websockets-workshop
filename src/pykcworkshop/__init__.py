import asyncio
import os
from enum import IntEnum
from pathlib import Path
from typing import Any

import dotenv
from quart import Quart, Response, jsonify

from . import chat, logs, utils  # noqa: F401

__version__ = "0.0.1"

dotenv.load_dotenv()


class SubApp(IntEnum):
    CHAT = 1


ALL_SUBAPPS: int = 0 | SubApp.CHAT


async def init_chat(app: Quart, custom_config: dict[str, Any] = {}) -> None:
    """Initialize the chat sub-app."""

    # Register routes for chat subapp.
    app.register_blueprint(chat.bp)

    # Setup the chat database.
    chat_db_uri = custom_config.get(
        "DB_URI", f"sqlite+aiosqlite:///{app.instance_path}/pykcworkshop.db"
    )
    chat.db.connect(chat_db_uri, debug=custom_config.get("DEBUG", False))
    await chat.db.initialize(drop_tables=False)

    @app.teardown_appcontext
    async def cleanup_sqlalchemy_session(exception=None):
        await chat.db.get_session_proxy().remove()


async def async_create_app(
    enabled_subapps: int = ALL_SUBAPPS, **subapp_configs: dict[str, Any]
) -> Quart:
    """Quart application factory."""

    app = Quart(__name__, instance_relative_config=True)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config.from_mapping(
        {
            "PREFERRED_URL_SCHEME": "https",
            "DEBUG": False,
            "TESTING": False,
            "SECRET_KEY": os.environ["QUART_SECRET"],
        }
    )

    @app.route("/coffee", methods=["GET"])
    async def coffee() -> Response:
        """Endpoint that returns a status 418 response for compliance
        with the HTCPCP protocol as defined in RFC 2324."""

        res = jsonify(
            {
                "title": "I'm a Teapot",
                "status": 418,
                "detail": f"The {utils.get_domain().removeprefix('https://')} \
coffee pot was replaced with a tea kettle. \
This endpoint is maintained for compliance with the HTCPCP/1.0 standard as defined in RFC 2324.",
                "see_also": "https://www.rfc-editor.org/rfc/rfc2324",
            }
        )
        res.status_code = 418
        res.content_type = "application/problem+json"
        return res

    @app.route("/favicon.ico", methods=["GET"])
    def i_hate_automatic_favicon_requests():
        return Response(status=404)

    @app.route("/robots.txt", methods=["GET"])
    async def robotstxt():
        res = Response("User-agent: *\nDisallow: /", mimetype="text/plain")
        return res

    if SubApp.CHAT & enabled_subapps:
        await init_chat(app, subapp_configs.get("chat_config", {}))

    return app


def create_app(enabled_subapps: int = ALL_SUBAPPS, **subapp_configs: dict[str, Any]) -> Quart:
    return asyncio.run(async_create_app(enabled_subapps, **subapp_configs))


def test_chat_app() -> Quart:
    testing_config = {"DB_URI": "sqlite+aiosqlite:///tmp.db"}
    return create_app(enabled_subapps=SubApp.CHAT, chat_config=testing_config)
