
from datetime import datetime
from email.utils import formatdate, parsedate_to_datetime
from typing import Optional


__all__ = [
    "get_datetime_rfc822",
    "rfc822_to_datetime",
    "rfc822_to_unix",
    "unix_to_rfc822",
]


def get_datetime_rfc822(timeval: Optional[float] = None) -> str:
    return formatdate(timeval=timeval, usegmt=True)


def unix_to_rfc822(unixtime: float) -> str:
    return get_datetime_rfc822(unixtime)


def rfc822_to_datetime(rfc822: str) -> datetime:
    return parsedate_to_datetime(rfc822)


def rfc822_to_unix(rfc822: str) -> float:
    dt = rfc822_to_datetime(rfc822)
    return dt.timestamp()
