"""General helper functions."""

import datetime
import os
import unicodedata

from dotenv import load_dotenv

load_dotenv()


def now() -> datetime.datetime:
    """Return the current time in UTC."""

    return datetime.datetime.now(datetime.UTC)


def remove_control_characters(s: str) -> str:
    """Remove any hidden control characters from the input string `s`.

    This is helpful when parsing scraped web pages.
    """

    return "".join([ch for ch in s if unicodedata.category(ch)[0] != "C"])


def hyphen_to_snake(hyphenated: str) -> str:  # pragma: no cover
    """Return `hyphenated` with all hyphen characters replaced by underscores.

    Useful for converting url params to corresponding python identifiers.
    """

    return hyphenated.replace("-", "_")


def snake_to_hyphen(snaked: str) -> str:  # pragma: no cover
    """Return `snaked` with all underscore characters replaced by hyphens.

    Useful for converting python identifiers to url params.
    """

    return snaked.replace("_", "-")


_SITE_ROOT = os.environ["SITE_ROOT"]


def get_domain() -> str:
    """Return the full domain name and scheme identifier for the api without
    a quart application context.
    """

    return _SITE_ROOT
