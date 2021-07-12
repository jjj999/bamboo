from __future__ import annotations
import codecs
import typing as t

from .error import ErrInfo
from .http import HTTPStatus
from .io import BufferedConcatIterator


class _ASGIProtocols:
    """Iterable for the ASGI protocols.
    """

    http        = "http"
    websocket   = "websocket"
    lifespan    = "lifespan"

    _events = {
        http,
        websocket,
        lifespan,
    }
    __instance = None

    def __new__(cls) -> _ASGIProtocols:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __iter__(self) -> t.Iterator[str]:
        return iter(self._events)

    def __contains__(self, item: str) -> bool:
        return item in self._events


class _ASGIHTTPEvents:
    """Iterable for events of the ASGI HTTP protocol.
    """

    request         = "http.request"
    response_start  = "http.response.start"
    response_body   = "http.response.body"
    disconnect      = "http.disconnect"

    _events = {
        request,
        response_start,
        response_body,
        disconnect,
    }
    __instance = None

    def __new__(cls) -> _ASGIHTTPEvents:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __iter__(self) -> t.Iterator[str]:
        return iter(self._events)

    def __contains__(self, item: str) -> bool:
        return item in self._events


class _ASGIWebSocketEvents:
    """Iterable for events of the ASGI WebSocket protocol.
    """

    connect     = "websocket.connect"
    accept      = "websocket.accept"
    receive     = "websocket.receive"
    send        = "websocket.send"
    disconnect  = "websocket.disconnect"
    close       = "websocket.close"

    _events = {
        connect,
        accept,
        receive,
        send,
        disconnect,
        close,
    }
    __instance = None

    def __new__(cls) -> _ASGIWebSocketEvents:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __iter__(self) -> t.Iterator[str]:
        return iter(self._events)

    def __contains__(self, item: str) -> bool:
        return item in self._events


class _ASGILifespanEvents:
    """Iterable for events of the ASGI Lifespan protocol.
    """

    startup             = "lifespan.startup"
    startup_complete    = "lifespan.startup.complete"
    startup_failed      = "lifespan.startup.failed"
    shutdown            = "lifespan.shutdown"
    shutdown_complete   = "lifespan.shutdown.complete"
    shutdown_failed     = "lifespan.shutdown.failed"

    _events = {
        startup,
        startup_complete,
        startup_failed,
        shutdown,
        shutdown_complete,
        shutdown_failed,
    }
    __instance = None

    def __new__(cls) -> _ASGILifespanEvents:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __iter__(self) -> t.Iterator[str]:
        return iter(self._events)

    def __contains__(self, item: str) -> bool:
        return item in self._events


ASGIProtocols = _ASGIProtocols()
ASGIHTTPEvents = _ASGIHTTPEvents()
ASGIWebSocketEvents = _ASGIWebSocketEvents()
ASGILifespanEvenets = _ASGILifespanEvents()


def _convert_headers_asgistyle(
    headers: t.Iterable[t.Tuple[str, str]]
) -> t.List[t.Tuple[bytes, bytes]]:
    return [tuple(map(codecs.encode, h)) for h in headers]


ASGIRecv_t = t.Callable[
    [],
    t.Awaitable[t.Dict[str, t.Any]]
]
ASGISend_t = t.Callable[
    [t.Dict[str, t.Any]],
    t.Awaitable[None]
]

HTTPSendStart_t = t.Callable[
    [HTTPStatus, t.Iterable[t.Tuple[str, str]]],
    t.Awaitable[None]
]
HTTPSendBody_t = t.Callable[
    [t.Iterable[bytes]],
    t.Awaitable[None]
]
HTTPSendErrInfo_t = t.Callable[
    [ErrInfo],
    t.Awaitable[None]
]


def format_http_sendstart_msg(
    status: HTTPStatus,
    headers: t.Iterable[str, str],
) -> t.Dict[str, t.Any]:
    return {
        "type": ASGIHTTPEvents.response_start,
        "status": status.asgi,
        "headers": _convert_headers_asgistyle(headers),
    }


def format_http_sendbody_msg(
    chunk: bytes = b"",
    more: bool = False,
) -> t.Dict[str, t.Any]:
    return {
        "type": ASGIHTTPEvents.response_body,
        "body": chunk,
        "more_body": more,
    }


def get_http_sendstart(send: ASGISend_t) -> HTTPSendStart_t:

    async def sendstart(
        status: HTTPStatus,
        headers: t.Iterable[t.Tuple[str, str]],
    ) -> None:
        msg = format_http_sendstart_msg(status, headers)
        await send(msg)

    return sendstart


def get_http_sendbody(send: ASGISend_t) -> HTTPSendBody_t:

    async def sendbody(body: t.Union[t.Iterable[bytes]]) -> None:
        for chunk in body:
            msg = format_http_sendbody_msg(chunk, more=True)
            await send(msg)
        msg = format_http_sendbody_msg()
        await send(msg)

    return sendbody


def get_http_send_errinfo(send: ASGISend_t) -> HTTPSendErrInfo_t:
    sendstart = get_http_sendstart(send)
    sendbody = get_http_sendbody(send)

    async def send_errinfo(
        errinfo: ErrInfo,
        res_headers: t.Iterable[t.Tuple[str, str]],
    ) -> None:
        status, headers, body = errinfo.get_all_form()

        # Judge whether the response headers should be inheritted.
        for header_name, header_value in res_headers:
            if errinfo.should_inherit_header(header_name):
                headers.append((header_name, header_value))

        await sendstart(status, headers)
        await sendbody(BufferedConcatIterator(body))

    return send_errinfo


class WebSocketError(Exception):
    pass


class WebSocketDisconnectedError(Exception):
    pass


WebSocketAccept_t = t.Callable[
    [t.Iterable[t.Tuple[str, str]], t.Optional[str]],
    t.Awaitable[None]
]
WebSocketRecvMsg_t = t.Callable[
    [],
    t.Awaitable[t.Tuple[t.Optional[str], t.Optional[bytes]]]
]
WebSocketSendMsg_t = t.Callable[
    [t.Optional[str], t.Optional[bytes]],
    t.Awaitable[None]
]
WebSocketClose_t = t.Callable[
    [int],
    t.Awaitable[None]
]


def format_websock_accept_msg(
    headers: t.Iterable[str, str],
    subprotocol: t.Optional[str] = None,
) -> t.Dict[str, t.Any]:
    return {
        "type": ASGIWebSocketEvents.accept,
        "subprotocol": subprotocol,
        "headers": _convert_headers_asgistyle(headers),
    }


def format_websock_send_msg(
    text: t.Optional[str] = None,
    bin: t.Optional[bytes] = None,
) -> t.Dict[str, t.Any]:
    if text is None and bin is None:
        raise ValueError("One of 'text' or 'bin' must be non-None.")

    return {
        "type": ASGIWebSocketEvents.send,
        "bytes": bin,
        "text": text,
    }


def format_websock_close_msg(code: int = 1000) -> t.Dict[str, t.Any]:
    return {
        "type": ASGIWebSocketEvents.close,
        "code": code,
    }


def get_websock_accept(send: ASGISend_t) -> WebSocketAccept_t:

    async def websock_accept(
        headers: t.Iterable[str, str],
        subprotocol: t.Optional[str] = None,
    ) -> None:
        msg = format_websock_accept_msg(headers, subprotocol)
        await send(msg)

    return websock_accept


def get_websock_recvmsg(recv: ASGIRecv_t) -> WebSocketRecvMsg_t:

    async def websock_recvmsg() -> t.Tuple[str, bytes]:
        msg = await recv()
        if msg.get("type") == ASGIWebSocketEvents.disconnect:
            raise WebSocketDisconnectedError()
        return (msg.get("text"), msg.get("bytes"))

    return websock_recvmsg


def get_websock_sendmsg(send: ASGISend_t) -> WebSocketSendMsg_t:

    async def websock_sendmsg(
        text: t.Optional[str] = None,
        bin: t.Optional[str] = None,
    ) -> None:
        msg = format_websock_send_msg(text, bin)
        await send(msg)

    return websock_sendmsg


def get_websock_close(send: ASGISend_t) -> WebSocketClose_t:

    async def websock_close(code: int = 1000) -> None:
        msg = format_websock_close_msg(code)
        await send(msg)

    return websock_close


LifespanHandler_t = t.Callable[
    [t.Dict[str, t.Any], ASGIRecv_t, ASGISend_t],
    t.Awaitable[None]
]


async def default_lifespan_handler(
    scope: t.Dict[str, t.Any],
    recv: t.Callable[[], t.Awaitable[t.Dict[str, t.Any]]],
    send: t.Callable[[t.Dict[str, t.Any]], t.Awaitable[None]],
) -> None:
    while True:
        msg = await recv()
        msg_typ = msg.get("type")
        if msg_typ == ASGILifespanEvenets.startup:
            await send({"type": ASGILifespanEvenets.startup_complete})
        elif msg_typ == ASGILifespanEvenets.shutdown:
            await send({"type": ASGILifespanEvenets.shutdown_complete})
            return
