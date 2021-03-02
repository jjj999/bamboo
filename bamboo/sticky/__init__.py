
from typing import (
    Any,
    Awaitable,
    Callable,
    Tuple,
    Union,
)

from bamboo.endpoint import ASGIHTTPEndpoint, WSGIEndpoint


__all__ = []


# Signature of the callback of response method on sub classes of
# the Endpoint class.
Callback_WSGI_t = Callable[[WSGIEndpoint, Tuple[Any, ...]], None]
Callback_ASGI_t = Callable[[ASGIHTTPEndpoint, Tuple[Any, ...]], Awaitable[None]]
Callback_t = Union[Callback_WSGI_t, Callback_ASGI_t]
CallbackDecorator_t = Callable[[Callback_t], Callback_t]


def _get_bamboo_attr(attr: str) -> str:
    return f"__bamboo_{attr}__"
