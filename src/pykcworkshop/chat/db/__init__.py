"""This is the persistence layer for the REST api.

Important:
    The querying functions in this module accept an `async_scoped_session`
    as their first argument and they use this session to make all of their queries, but
    they do not call `.commit()` on the session object unless it is required for the
    internal consistency of the function. This means that when using these
    functions, we have to call `get_session()` to obtain a session reference, and
    call `.commit()` on that session instance at the callsite. These functions are
    structured this way both for performance and for flexibility. We avoid creating
    extraneous connections, and we have explicit control over when we start and end each
    transaction.
"""

import enum

from sqlalchemy.exc import IntegrityError

from . import columns, models  # noqa: F401
from .sessions import (  # noqa: F401
    add_user_to_room,
    connect,
    create_chat_message,
    create_room,
    create_user,
    get_room_by_id,
    get_room_by_name,
    get_session,
    get_session_proxy,
    get_system_user,
    get_user_by_id,
    get_user_by_name,
    initialize,
)


class ConstraintViolation(enum.Enum):
    UNIQUE = enum.auto()
    FOREIGN_KEY = enum.auto()
    PRIMARY_KEY = enum.auto()
    CHECK = enum.auto()
    UNKNOWN = enum.auto()


def parse_constraint_error(err: IntegrityError) -> ConstraintViolation:
    """Parse a SQLAlchemy IntegrityError to identify
    the actual db constraint that was violated.

    This works for sqlite, and it should work in postgres as well, but
    different db engines use different error messages, and not all of them
    include the name of the constraint in the message. Because who needs to actually
    know why a query failed, right?
    """

    if "unique" in str(err).lower():
        return ConstraintViolation.UNIQUE
    elif "check" in str(err).lower():
        return ConstraintViolation.CHECK
    elif "foreign" in str(err).lower():
        return ConstraintViolation.FOREIGN_KEY
    elif "primary" in str(err).lower():
        return ConstraintViolation.PRIMARY_KEY
    else:
        return ConstraintViolation.UNKNOWN
