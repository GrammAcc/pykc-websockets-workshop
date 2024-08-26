"""This subpackage contains the versioned API endpoints exposed by the server."""

from quart import Blueprint, Response, request, websocket

from pykcworkshop.chat import tokens

from . import http, websockets

bp = Blueprint("api", __name__, url_prefix="/api")
"""This blueprint contains all routes for all versions of the api."""

bp.register_blueprint(http.bp)
bp.register_blueprint(websockets.bp)


@bp.before_request
async def http_validate_csrf() -> Response | None:
    """Ensure the request has a valid CSRF token for all connections."""

    if "x-csrf-token" not in request.headers:
        return http.helpers.unauthorized()
    elif tokens.is_token_valid(request.headers["x-csrf-token"]):
        return None
    else:
        return http.helpers.unauthorized()


@bp.before_websocket
async def ws_validate_csrf() -> Response | None:
    """Ensure the websocket handshake has a valid CSRF token for all connections."""

    subps = [i.strip() for i in websocket.headers["sec-websocket-protocol"].split(",")]
    try:
        csrf_token = [i.removeprefix("csrf") for i in subps if i.lower().startswith("csrf")][0]
    except IndexError:
        return http.helpers.unauthorized()

    if tokens.is_token_valid(csrf_token):
        return None
    else:
        return http.helpers.unauthorized()
