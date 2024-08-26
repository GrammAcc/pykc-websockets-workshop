from typing import TypedDict


class UserData(TypedDict):
    """Represents user data stored in and parsed out of a JWT."""

    user_id: int
    user_name: str
