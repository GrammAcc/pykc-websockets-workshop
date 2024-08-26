"""Helper functions/middleware for api websocket routes."""

import functools
from typing import Any, Awaitable, Callable, ParamSpec, TypeVar

import jwt
from quart import Response, websocket

from pykcworkshop import logs
from pykcworkshop.chat import tokens
from pykcworkshop.chat.api import http

logger = logs.make_logger("websockets")


R = TypeVar("R")
P = ParamSpec("P")
AR = Awaitable[Any]


def auth_required(inject_user_data: bool) -> Callable[[Callable[P, AR]], Callable[P, AR]]:
    """Authentication decorator to be used by any websocket route that needs the user to be
    logged in.

    Args:
        inject_user_data:
            If True, then we call the wrapped websocket function with the payload
            from the validated jwt passed into the keyword argument `user_data`. If False,
            then we call the websocket function with the passed through `*args` and
            `**kwargs` only.
    """

    def _decorator(func: Callable[P, AR]) -> Callable[P, AR]:
        @functools.wraps(func)
        async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> Response | AR:
            subprotocols = [
                i.strip() for i in websocket.headers["sec-websocket-protocol"].split(",")
            ]
            try:
                bearer_token = [i for i in subprotocols if i.lower().startswith("bearer")][0]
            except IndexError as e:
                logs.error(
                    logger,
                    {
                        "msg": "Malformed or missing authorization header",
                        "headers": str(websocket.headers),
                        "url": websocket.url,
                    },
                    err=e,
                )
                return http.helpers.unauthorized()
            try:
                user_token = tokens.parse_bearer(bearer_token)
            except Exception as e:
                logs.error(
                    logger,
                    {
                        "msg": "Malformed authorization header",
                        "headers": str(websocket.headers),
                        "url": websocket.url,
                    },
                    err=e,
                )
                return http.helpers.unauthorized()
            else:
                try:
                    user_data = tokens.validate_token(user_token)
                    if inject_user_data:
                        kwargs["user_data"] = user_data
                    return await func(*args, **kwargs)
                except jwt.InvalidTokenError as e:
                    logs.debug(
                        logger,
                        {
                            "msg": "Invalid jwt when authenticating user",
                            "bearer_token": user_token,
                        },
                        err=e,
                    )
                    return http.helpers.unauthorized()
                except Exception as e:
                    logs.error(
                        logger,
                        {
                            "msg": "Unknown error when authenticating user",
                            "bearer_token": user_token,
                        },
                        err=e,
                    )
                    raise e

        return _wrapper

    return _decorator
