import typing as t

from ..endpoint import ASGIHTTPEndpoint, WSGIEndpoint


__all__ = []


# Signature of the callback of response method on sub classes of
# the Endpoint class.
Callback_WSGI_t = t.Callable[[WSGIEndpoint, t.Tuple[t.Any, ...]], None]
Callback_ASGI_t = t.Callable[[ASGIHTTPEndpoint, t.Tuple[t.Any, ...]], t.Awaitable[None]]
Callback_t = t.Union[Callback_WSGI_t, Callback_ASGI_t]
CallbackDecorator_t = t.Callable[[Callback_t], Callback_t]


def _get_bamboo_attr(attr: str) -> str:
    return f"__bamboo_{attr}__"


class DuplicatedInfoError(Exception):
    """Raised if same type of infomation is duplicated."""
    pass
