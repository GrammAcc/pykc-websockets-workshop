"""This module contains helper functions for working with JWTs."""

import datetime
import os
import random

import jwt

from pykcworkshop import utils


def generate_csrf() -> str:
    """Generate a csrf token for a page render."""

    now = utils.now()
    token_lifetime = datetime.timedelta(days=31)
    payload = {
        "r": str(random.randbytes(4)),
        "exp": now + token_lifetime,
        "iat": now,
    }
    token = jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")
    return token


def is_token_valid(token: str) -> bool:
    """Validate a JWT and return a bool indicating if it is valid or not."""

    try:
        validate_token(token)
        return True
    except jwt.InvalidTokenError:
        return False


def validate_token(token: str) -> dict:
    """Validate a JWT token and return the stored payload."""

    return jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])


def parse_bearer(bearer_token: str) -> str:
    """Parse a bearer token for user auth in http and websocket contexts.

    Because the browser WebSocket API doesn't allow spaces in the
    Sec-WebSocket-Protocol header values, and it doesn't allow setting
    any other headers, we have to specify the bearer token as `Bearer<token>`
    for the websocket connection, but we still want to use the W3C
    norms for `Authorization: <Scheme> <Credentials>` for regular
    HTTP requests, so instead of splitting on a space, we remove the
    first 6 characters from the auth value in order to remove `Bearer`
    case-insensitively, then we strip any whitespace, so that the result
    is the same for both HTTP and websocket bearer tokens.

    This method of parsing the token should never raise any exceptions as
    long as the `bearer_token` is a str. `str.strip()` returns the input
    if there is no whitespace to strip, and slicing outside of the bounds
    of an array just returns either the entire array or an empty array depending
    on which direction you are slicing. For example,
    `"short".strip()[6:].strip()` returns `""`, and `"short".strip()[:6].strip()` returns
    `"short"`, both without raising any exceptions.
    """

    return bearer_token.strip()[6:].strip()
