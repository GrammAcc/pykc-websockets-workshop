"""This subpackage contains the chat sub-app."""

from quart import Blueprint, render_template

from . import api, db, tokens  # noqa: F401

bp = Blueprint(
    "chat",
    __name__,
    url_prefix="/chat",
    template_folder="templates",
    static_folder="static",
)
"""This blueprint contains all routes for the chat app."""


@bp.route("/", methods=["GET"])
async def chatroom():
    """The frontend's URL."""

    return await render_template("chat/index.html", csrf_token=tokens.generate_csrf())


bp.register_blueprint(api.bp)
