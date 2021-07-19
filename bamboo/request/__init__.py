from __future__ import annotations
import os
import urllib.parse
import typing as t

from ..api.base import ApiData


__all__ = [
    "Response",
    "Schemes",
]


ResponseData_t = t.TypeVar("ResponseData_t", bound=ApiData)


class _Schemes:

    HTTP = "http"
    HTTPS = "https"

    _schemes = set((HTTP, HTTPS))
    __instance = None

    def __new__(cls) -> _Schemes:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __iter__(self):
        return iter(self._schemes)

    def __contains__(self, item: str):
        return item in self._schemes


Schemes = _Schemes()


def _get_http_proxy_env() -> t.Optional[str]:
    env = os.environ.get("http_proxy")
    if env is None:
        env = os.environ.get("HTTP_PROXY")
    return env


def _get_https_proxy_env() -> t.Optional[str]:
    env = os.environ.get("https_proxy")
    if env is None:
        env = os.environ.get("HTTPS_PROXY")
    return env


def _parse_proxy_netloc(uri: str) -> t.Tuple[str, int]:
    result = urllib.parse.urlparse(uri)
    try:
        domain, port = result.netloc.split(":", 2)
    except ValueError as e:
        domain = result.netloc
        port = 80
    return (domain, int(port))


from bamboo.request.response import Response
