"""Utility functions for working with HTTP routes and responses."""

import functools
from typing import Any, Awaitable, Callable, ParamSpec, TypeVar

import jwt
from quart import Response, jsonify, request

from pykcworkshop import logs
from pykcworkshop.chat import tokens

logger = logs.make_logger("http")


def bad_request(details: str, **kwargs) -> Response:
    """Helper function to construct a status 400 error response with a structured JSON body.

    Intended to be compliant with problem details as defined in
    [RFC7807](https://www.rfc-editor.org/rfc/rfc7807)

    Args:
        details:
            Specific error information. MUST NOT include any sensitive information that can't be
            exposed to the browser console.
        kwargs:
            Any additional key-value pairs to be included in the error response object.
            The values must be json-serializable. Also MUST NOT include any sensitive info.
    """

    err_dict = {
        "title": "Validation error",
        "status": 400,
        "detail": details,
    }
    err_dict.update(kwargs)
    res = jsonify(err_dict)
    res.status_code = 400
    res.content_type = "application/problem+json"
    return res


def unauthorized() -> Response:
    """Helper function to construct a status 401 error response with no debugging details.

    For security reasons, this function should be used instead of constructing
    responses with arbitrary data at the error site.
    """

    return Response("401 UNAUTHORIZED", status=401)


def validate_required_fields(data: dict | None, required_fields: list[str]) -> Response | None:
    """Checks that the `data` dictionary contains the `required_fields` and returns
    a 400 response with appropriate error information if not.

    Args:
        data: Generally, the dict returned by `quart.request.get_json()`.
            This can be None if no body was provided. If None, then the
            argument will be treated as an empty dict.

    Returns:
        `None` if validation succeded. If validations fails, then this function constructs
        a Quart `Response` with a 400 BAD REQUEST status and problem details. This is to
        give consistency in error details without duplicating the same code at every call site.

    Example:

        >>> async def some_route_function():
        ...    bad_req = validate_required_fields((await request.get_json()), ["user_name"])
        ...    if bad_req is not None:
        ...        return bad_req
        ...    # Route/view logic continued...
    """

    if data is None:
        data = {}  # pragma: no cover
    missing_fields = [key for key in required_fields if key not in data or data[key] == ""]
    if missing_fields:
        return bad_request("Missing required fields", missing=missing_fields)
    else:
        return None


R = TypeVar("R")
P = ParamSpec("P")
AR = Awaitable[Any]


def auth_required(
    inject_user_data: bool,
) -> Callable[[Callable[P, Awaitable[Any]]], Callable[P, Awaitable[Any]]]:
    """Authentication decorator to be used by any http route that needs the user to be
    logged in.

    Args:
        inject_user_data:
            If True, then we call the wrapped route function with the payload
            from the validated jwt passed into the keyword argument `user_data`. If False,
            then we call the route function with the passed through `*args` and
            `**kwargs` only.
    """

    def _decorator(func: Callable[P, Awaitable[Any]]) -> Callable[P, Awaitable[Any]]:
        @functools.wraps(func)
        async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> Response | Awaitable[Any]:
            if "authorization" not in request.headers:
                return unauthorized()
            user_token = tokens.parse_bearer(request.headers["authorization"])
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
                return unauthorized()
            except Exception as e:  # pragma: no cover
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
