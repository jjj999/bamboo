from __future__ import annotations
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable, Optional, Tuple

from bamboo.util.deco import class_property
from bamboo.util.header import make_header


__all__ = []


class _HTTPMethods:
    """Iterator for HTTP methods.
    """

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"
    TRACE = "TRACE"
    CONNECT = "CONNECT"

    __methods = set((
        GET,
        POST,
        PUT,
        DELETE,
        HEAD,
        OPTIONS,
        PATCH,
        TRACE,
    ))

    __instance = None

    def __new__(cls) -> _HTTPMethods:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __iter__(self) -> Iterable[str]:
        return iter(self.__methods)

    def __contains__(self, item: str) -> bool:
        return item in self.__methods


HTTPMethods = _HTTPMethods()


class _MediaTypes:
    """Iterator for media types of body on communication.
    """

    plain = "text/plain"
    html = "text/html"
    xml = "application/xml"
    css = "text/css"
    javascript = "application/javascript"
    json = "application/json"
    x_www_form_urlencoded = "application/x-www-form-urlencoded"
    rss = "application/rss+xml"
    atom = "application/atom+xml"
    binary = "application/octet-stream"
    zip = "application/zip"
    jpeg = "image/jpeg"
    png = "image/png"
    svg = "image/svg+xml"
    multi_form = "multipart/form-data"
    mp4 = "video/mp4"
    excel = "application/vnd.ms-excel"

    __types = set((
        plain,
        html,
        xml,
        css,
        javascript,
        json,
        rss,
        atom,
        binary,
        zip,
        jpeg,
        png,
        svg,
        multi_form,
        mp4,
        excel,
    ))

    __instance = None

    def __new__(cls) -> _MediaTypes:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __iter__(self) -> Iterable[str]:
        return iter(self.__types)

    def __contains__(self, item: str) -> bool:
        return item in self.__types


MediaTypes = _MediaTypes()


class _AuthSchemes:
    """Iterator for authentication schemes of the Authorization header.
    """

    basic = "Basic"
    bearer = "Bearer"

    __schemes = set((
        basic,
        bearer
    ))

    __instance = None

    def __new__(cls) -> _AuthSchemes:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __iter__(self) -> Iterable[str]:
        return iter(self.__schemes)

    def __contains__(self, item: str) -> bool:
        return item in self.__schemes


AuthSchemes = _AuthSchemes()


@dataclass
class ContentType:
    """`dataclass` for describing value of `Content-Type` header.

    Its object is often used when handling the value of `Content-Type` in
    Bamboo.
    """

    media_type: str
    charset: Optional[str] = None
    boundary: Optional[str] = None

    def to_header(self) -> Tuple[str, str]:
        """Format contents as a Content-Type header.

        Returns:
            Header name and value of the header.
        """
        params = {}
        if self.charset:
            params["charset"] = self.charset
        if self.boundary:
            params["boundary"] = self.boundary
        return make_header("Content-Type", self.media_type, **params)

    @classmethod
    def parse(cls, raw: str) -> ContentType:
        """Parse and make new instance of this class.

        Parameters
        ----------
        raw : str
            Value of `Content-Type` header

        Returns
        -------
        ContentType
            New instance of this class based on the `raw` data
        """
        raw = re.split(";\s*", raw)
        result = cls(raw[0])

        for directive, val in [item.split("=") for item in raw[1:]]:
            if directive == "charset":
                result.charset = val.lower()
            elif directive == "boundary":
                result.boundary = val

        return result


class ContentTypeHolder(metaclass=ABCMeta):
    """Abstract class with properties about `Content-Type`.
    """

    @class_property
    @abstractmethod
    def __content_type__(cls) -> ContentType:
        pass

    @classmethod
    def verify_content_type(cls, content_type: ContentType) -> bool:
        media_type_expected = cls.__content_type__.media_type.lower()
        media_type_verified = content_type.media_type.lower()
        if media_type_expected != media_type_verified:
            return False

        if cls.__content_type__.charset:
            charset_expected = cls.__content_type__.charset.lower()
            charset_verified = content_type.charset.lower()
            if charset_expected != charset_verified:
                return False
        return True


# NOTE
#   Value of the Content-Type header by default. This variables can be
#   used if Content-Type of response is not specified.
DEFAULT_CONTENT_TYPE_PLAIN = ContentType(MediaTypes.plain)
DEFAULT_CONTENT_TYPE_JSON = ContentType(MediaTypes.json, "UTF-8")


class _ASGIHTTPEvents:
    """Iterator for events of ASGI HTTP protocol.
    """

    request = "http.request"
    response_start = "http.response.start"
    response_body = "http.response.body"
    disconnect = "http.disconnect"

    _events = set((
        request,
        response_start,
        response_body,
        disconnect,
    ))
    __instance = None

    def __new__(cls) -> _ASGIHTTPEvents:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __iter__(self) -> Iterable[str]:
        return iter(self._events)

    def __contains__(self, item: str) -> bool:
        return item in self._events


class _ASGIWebSocketEvents:
    """Iterator for events of ASGI WebSocket protocol.
    """

    connect = "websocket.connect"
    accept = "websocket.accept"
    receive = "websocket.receive"
    send = "websocket.send"
    disconnect = "websocket.disconnect"
    close = "websocket.close"

    _events = set((
        connect,
        accept,
        receive,
        send,
        disconnect,
        close,
    ))
    __instance = None

    def __new__(cls) -> _ASGIWebSocketEvents:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __iter__(self) -> Iterable[str]:
        return iter(self._events)

    def __contains__(self, item: str) -> bool:
        return item in self._events


ASGIHTTPEvents = _ASGIHTTPEvents()
ASGIWebSocketEvents = _ASGIWebSocketEvents()


class HTTPStatus(int, Enum):
    """Enum which describes HTTP status.

    Each class variables of the class have four main attributes:

    - value
    - wsgi
    - asgi
    - description

    `value` means the enum value and describes HTTP status as int.
    `wsgi` is str and used only for WSGI servers.
    Similarly, `asgi` is int and only for ASGI servers.
    'description' describes short message of corresponding HTTP satus.
    """

    def __new__(cls, value: int, wsgi: str, asgi: int, description: str = ""):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.wsgi = wsgi
        obj.asgi = asgi
        obj.description = description
        return obj

    @classmethod
    def get_status(cls, code: int) -> Optional[HTTPStatus]:
        for stat in cls:
            if stat.value == code:
                return stat
        return None

    CONTINUE = (
        100,
        "100 Continue",
        100,
        "Request received, please continue"
    )
    SWITCHING_PROTOCOLS = (
        101,
        "101 Switching Protocols",
        101,
        "Switching to new protocol; obey Upgrade header"
    )
    PROCESSING = (
        102,
        "102 Processing",
        102,
        ""
    )

    # success
    OK  = (
        200,
        "200 OK",
        200,
        "Request fulfilled, document follows"
    )
    CREATED = (
        201,
        "201 Created",
        201,
        "Document created, URL follows"
    )
    ACCEPTED = (
        202,
        "202 Accepted",
        202,
        "Request accepted, processing continues off-line"
    )
    NON_AUTHORITATIVE_INFORMATION = (
        203,
        "203 Non-Authoritative Information",
        203,
        "Request fulfilled from cache"
    )
    NO_CONTENT = (
        204,
        "204 No Content",
        204,
        "Request fulfilled, nothing follows"
    )
    RESET_CONTENT = (
        205,
        "205 Reset Content",
        205,
        "Clear input form for further input"
    )
    PARTIAL_CONTENT = (
        206,
        "206 Partial Content",
        206,
        "Partial content follows"
    )
    MULTI_STATUS = (
        207,
        "207 Multi-Status",
        207,
        ""
    )
    ALREADY_REPORTED = (
        208,
        "208 Already Reported",
        208,
        ""
    )
    IM_USED = (
        226,
        "226 IM Used",
        226,
        ""
    )

    # redirection
    MULTIPLE_CHOICES = (
        300,
        "300 Multiple Choices",
        300,
        "Object has several resources -- see URI list"
    )
    MOVED_PERMANENTLY = (
        301,
        "301 Moved Permanently",
        301,
        "Object moved permanently -- see URI list"
    )
    FOUND = (
        302,
        "302 Found",
        302,
        "Object moved temporarily -- see URI list"
    )
    SEE_OTHER = (
        303,
        "303 See Other",
        303,
        "Object moved -- see Method and URL list"
    )
    NOT_MODIFIED = (
        304,
        "304 Not Modified",
        304,
        "Document has not changed since given time"
    )
    USE_PROXY = (
        305,
        "305 Use Proxy",
        305,
        "You must use proxy specified in Location to access this resource"
    )
    TEMPORARY_REDIRECT = (
        307,
        "307 Temporary Redirect",
        307,
        "Object moved temporarily -- see URI list"
    )
    PERMANENT_REDIRECT = (
        308,
        "308 Permanent Redirect",
        308,
        "Object moved permanently -- see URI list"
    )

    # client error
    BAD_REQUEST = (
        400,
        "400 Bad Request",
        400,
        "Bad request syntax or unsupported method"
    )
    UNAUTHORIZED = (
        401,
        "401 Unauthorized",
        401,
        "No permission -- see authorization schemes"
    )
    PAYMENT_REQUIRED = (
        402,
        "402 Payment Required",
        402,
        "No payment -- see charging schemes"
    )
    FORBIDDEN = (
        403,
        "403 Forbidden",
        403,
        "Request forbidden -- authorization will not help"
    )
    NOT_FOUND = (
        404,
        "404 Not Found",
        404,
        "Nothing matches the given URI"
    )
    METHOD_NOT_ALLOWED = (
        405,
        "405 Method Not Allowed",
        405,
        "Specified method is invalid for this resource"
    )
    NOT_ACCEPTABLE = (
        406,
        "406 Not Acceptable",
        406,
        "URI not available in preferred format"
    )
    PROXY_AUTHENTICATION_REQUIRED = (
        407,
        "407 Proxy Authentication Required",
        407,
        "You must authenticate with this proxy before proceeding"
    )
    REQUEST_TIMEOUT = (
        408,
        "408 Request Timeout",
        408,
        "Request timed out; try again later"
    )
    CONFLICT = (
        409,
        "409 Conflict",
        409,
        "Request conflict"
    )
    GONE = (
        410,
        "410 Gone",
        410,
        "URI no longer exists and has been permanently removed"
    )
    LENGTH_REQUIRED = (
        411,
        "411 Length Required",
        411,
        "Client must specify Content-Length"
    )
    PRECONDITION_FAILED = (
        412,
        "412 Precondition Failed",
        412,
        "Precondition in headers is false"
    )
    REQUEST_ENTITY_TOO_LARGE = (
        413,
        "413 Request Entity Too Large",
        413,
        "Entity is too large"
    )
    REQUEST_URI_TOO_LONG = (
        414,
        "414 Request-URI Too Long",
        414,
        "URI is too long"
    )
    UNSUPPORTED_MEDIA_TYPE = (
        415,
        "415 Unsupported Media Type",
        415,
        "Entity body in unsupported format"
    )
    REQUESTED_RANGE_NOT_SATISFIABLE = (
        416,
        "416 Requested Range Not Satisfiable",
        416,
        "Cannot satisfy request range"
    )
    EXPECTATION_FAILED = (
        417,
        "417 Expectation Failed",
        417,
        "Expect condition could not be satisfied"
    )
    MISDIRECTED_REQUEST = (
        421,
        "421 Misdirected Request",
        421,
        "Server is not able to produce a response"
    )
    UNPROCESSABLE_ENTITY = (
        422,
        "422 Unprocessable Entity",
        422,
        ""
    )
    LOCKED = (
        423,
        "423 Locked",
        423,
        ""
    )
    FAILED_DEPENDENCY = (
        424,
        "424 Failed Dependency",
        424,
        ""
    )
    UPGRADE_REQUIRED = (
        426,
        "426 Upgrade Required",
        426,
        ""
    )
    PRECONDITION_REQUIRED = (
        428,
        "428 Precondition Required",
        428,
        "The origin server requires the request to be conditional"
    )
    TOO_MANY_REQUESTS = (
        429,
        "429 Too Many Requests",
        429,
        "The user has sent too many requests in a given amount of time"
        "('rate limiting')"
    )
    REQUEST_HEADER_FIELDS_TOO_LARGE = (
        431,
        "431 Request Header Fields Too Large",
        431,
        "The server is unwilling to process the request because its "
        "header fields are too large"
    )

    # server errors
    INTERNAL_SERVER_ERROR = (
        500,
        "500 Internal Server Error",
        500,
        "Server got itself in trouble"
    )
    NOT_IMPLEMENTED = (
        501,
        "501 Not Implemented",
        501,
        "Server does not support this operation"
    )
    BAD_GATEWAY = (
        502,
        "502 Bad Gateway",
        502,
        "Invalid responses from another server/proxy"
    )
    SERVICE_UNAVAILABLE = (
        503,
        "503 Service Unavailable",
        503,
        "The server cannot process the request due to a high load"
    )
    GATEWAY_TIMEOUT = (
        504,
        "504 Gateway Timeout",
        504,
        "The gateway server did not receive a timely response"
    )
    HTTP_VERSION_NOT_SUPPORTED = (
        505,
        "505 HTTP Version Not Supported",
        505,
        "Cannot fulfill request"
    )
    VARIANT_ALSO_NEGOTIATES = (
        506,
        "506 Variant Also Negotiates",
        506,
        ""
    )
    INSUFFICIENT_STORAGE = (
        507,
        "507 Insufficient Storage",
        507,
        ""
    )
    LOOP_DETECTED = (
        508,
        "508 Loop Detected",
        508,
        ""
    )
    NOT_EXTENDED = (
        510,
        "510 Not Extended",
        510,
        ""
    )
    NETWORK_AUTHENTICATION_REQUIRED = (
        511,
        "511 Network Authentication Required",
        511,
        "The client needs to authenticate to gain network access"
    )
