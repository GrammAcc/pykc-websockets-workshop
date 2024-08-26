"""This module provides the api's websockets-based endpoints for the backend of the chat app."""

from quart import Blueprint

from . import helpers, v1  # noqa: F401

bp = Blueprint("websockets", __name__)
"""This blueprint contains all websockets-based routes for the api."""

bp.register_blueprint(v1.bp)
