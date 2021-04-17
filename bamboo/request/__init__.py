from __future__ import annotations
from typing import TypeVar

from ..api import ApiData


__all__ = [
    "Response",
    "Schemes",
]


ResponseData_t = TypeVar("ResponseData_t", bound=ApiData)


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


from bamboo.request.response import Response
