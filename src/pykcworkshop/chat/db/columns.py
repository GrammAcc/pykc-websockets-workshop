"""Custom sqlalchemy column types."""

import datetime

from sqlalchemy.types import DateTime, TypeDecorator


class UTCDateTime(TypeDecorator):
    """This column coerces all datetime objects to UTC to ensure server time is consistent."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value.replace(tzinfo=datetime.UTC)
        return value
