"""This module provides the api's http-based endpoints for the backend of the chat app."""

from quart import Blueprint

from . import helpers, v1  # noqa: F401

bp = Blueprint("http", __name__)
"""This blueprint contains all http-based routes for the api."""

bp.register_blueprint(v1.bp)
