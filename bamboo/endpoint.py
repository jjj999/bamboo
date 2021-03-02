
from __future__ import annotations

from abc import ABCMeta, abstractmethod
import codecs
import inspect
from io import BytesIO
import json
import os
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)
from urllib.parse import parse_qs

from bamboo.base import (
    ASGIHTTPEvents,
    ContentType,
    DEFAULT_CONTENT_TYPE_PLAIN,
    HTTPMethods,
    HTTPStatus,
    MediaTypes,
)
from bamboo.error import ErrInfoBase
from bamboo.io import BufferedConcatIterator, BufferedFileIterator
from bamboo.util.deco import (
    awaitable_property,
    awaitable_cached_property,
    cached_property,
)


__all__ = []


# Base classes for each interfaces  ------------------------------------------

class EndpointBase(metaclass=ABCMeta):
    """Base class of Endpoint to define logic to requests.
    """

    def __init__(
        self,
        flexible_locs: Tuple[str, ...],
        *parcel: Any
    ) -> None:
        self._flexible_locs = flexible_locs
        self.setup(*parcel)

    def setup(self, *parcel) -> None:
        pass

    @property
    def flexible_locs(self) -> Tuple[str, ...]:
        return self._flexible_locs

    @property
    @abstractmethod
    def http_version(self) -> str:
        pass

    @property
    @abstractmethod
    def scheme(self) -> str:
        pass

    @abstractmethod
    def get_client_addr(self) -> Tuple[Optional[str], Optional[int]]:
        pass

    @abstractmethod
    def get_server_addr(self) -> Tuple[Optional[str], Optional[int]]:
        pass

    @abstractmethod
    def get_host_addr(self) -> Tuple[Optional[str], Optional[int]]:
        pass

    @abstractmethod
    def get_header(self, name: str) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def path(self) -> str:
        pass

    @cached_property
    @abstractmethod
    def queries(self) -> Dict[str, str]:
        pass

    def get_query(self, name: str) -> List[str]:
        return self.queries.get(name)

    @cached_property
    @abstractmethod
    def content_type(self) -> Optional[ContentType]:
        pass


class WSGIEndpointBase(EndpointBase):

    def __init__(
        self,
        environ: Dict[str, Any],
        flexible_locs: Tuple[str, ...],
        *parcel: Any
    ) -> None:
        super().__init__(flexible_locs, *parcel)

        self._environ = environ

    @property
    def environ(self) -> Dict[str, Any]:
        return self._environ

    @property
    def wsgi_version(self) -> str:
        version = self._environ.get("wsgi.version")
        return ".".join(map(str, version))

    @property
    def server_software(self) -> str:
        return self._environ.get("SERVER_SOFTWARE")

    @property
    def http_version(self) -> str:
        version = self._environ.get("SERVER_PROTOCOL")
        return version.split("/")[1]

    @property
    def scheme(self) -> str:
        return self._environ.get("wsgi.url_scheme")

    def get_client_addr(self) -> Tuple[Optional[str], Optional[int]]:
        client = self._environ.get("REMOTE_ADDR")
        port = self._environ.get("REMOTE_PORT")
        if port:
            port = int(port)
        return (client, port)

    def get_server_addr(self) -> Tuple[Optional[str], Optional[int]]:
        """Retrieve requested a pair of host name and port.

        Returns
        -------
        Tuple[str, int]
            A pair of host name and port
        """
        server = self._environ.get("SERVER_NAME")
        port = self._environ.get("SERVER_PORT")
        if port:
            port = int(port)
        return (server, port)

    def get_host_addr(self) -> Tuple[Optional[str], Optional[int]]:
        http_host = self._environ.get("HTTP_HOST")
        if http_host:
            http_host = http_host.split(":")
            if len(http_host) == 1:
                return (http_host[0], None)
            else:
                host, port = http_host
                port = int(port)
                return (host, port)
        return (None, None)

    def get_header(self, name: str) -> Optional[str]:
        """Try to retrieve a HTTP header.

        Parameters
        ----------
        name : str
            Header field to retrieve

        Returns
        -------
        Optional[str]
            Value of the field if exists, else None
        """
        name = "HTTP_" + name.replace("-", "_").upper()
        return self._environ.get(name)

    @property
    def path(self) -> str:
        return self._environ.get("PATH_INFO")

    @cached_property
    def queries(self) -> Dict[str, List[str]]:
        return parse_qs(self._environ.get("QUERY_STRING"))

    @cached_property
    def content_type(self) -> Optional[ContentType]:
        raw = self._environ.get("CONTENT_TYPE")
        print(raw)
        if raw:
            return ContentType.parse(raw)
        return None


class ASGIEndpointBase(EndpointBase):

    def __init__(
        self,
        scope: Dict[str, Any],
        flexible_locs: Tuple[str, ...],
        *parcel: Any
    ) -> None:
        super().__init__(flexible_locs, *parcel)

        self._scope = scope

        # TODO
        #   Consider not mapping in this method.
        req_headers = scope.get("headers")
        self._req_headers = {}
        if req_headers:
            req_headers = dict([
                map(codecs.decode, header) for header in req_headers
            ])
            self._req_headers.update(req_headers)

    @property
    def scope(self) -> Dict[str, Any]:
        return self._scope

    @property
    def scope_type(self) -> str:
        return self._scope.get("get")

    @property
    def asgi_version(self) -> str:
        return self._scope.get("asgi").get("version")

    @property
    def spec_version(self) -> str:
        return self._scope.get("asgi").get("spec_version")

    @property
    def http_version(self) -> str:
        return self._scope.get("http_version")

    @property
    def scheme(self) -> str:
        return self._scope.get("scheme")

    def get_client_addr(self) -> Tuple[Optional[str], Optional[str]]:
        client = self._scope.get("client")
        if client:
            return tuple(client)
        return (None, None)

    def get_server_addr(self) -> Tuple[Optional[str], Optional[str]]:
        server = self._scope.get("server")
        if server:
            return tuple(server)
        return (None, None)

    def get_host_addr(self) -> Tuple[Optional[str], Optional[int]]:
        http_host = self.get_header("host")
        if http_host:
            http_host = http_host.split(":")
            if len(http_host) == 1:
                return (http_host[0], None)
            else:
                host, port = http_host
                port = int(port)
                return (host, port)
        return (None, None)

    def get_header(self, name: str) -> Optional[str]:
        name = name.lower()
        return self._req_headers.get(name)

    @property
    def path(self) -> str:
        return self._scope.get("path")

    @cached_property
    def queries(self) -> Dict[str, List[str]]:
        return parse_qs(self._scope.get("query_string").decode())

    @cached_property
    def content_type(self) -> Optional[ContentType]:
        raw = self.get_header("Content-Type")
        if raw:
            return ContentType.parse(raw)
        return None

    @property
    def raw_path(self) -> str:
        return self._scope.get("raw_path")

    @property
    def root_path(self) -> str:
        return self._scope.get("root_path")

# ----------------------------------------------------------------------------

# HTTP  ----------------------------------------------------------------------

class StatusCodeAlreadySetError(Exception):
    """Raised if response status code has already been set."""
    pass


class HTTPMixIn(metaclass=ABCMeta):

    bufsize = 8192

    @classmethod
    def _get_response_method(
        cls,
        method: str
    ) -> Optional[Callable[[EndpointBase], None]]:
        """Retrieve response methods with given HTTP method.

        Parameters
        ----------
        method : str
            HTTP method

        Returns
        -------
        Optional[Callable_t]
            Callback with given name
        """
        mname = "do_" + method
        if hasattr(cls, mname):
            return getattr(cls, mname)
        return None

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Check if bufsize is positive
        if not (cls.bufsize > 0 and isinstance(cls.bufsize, int)):
            raise ValueError(
                f"{cls.__name__}.bufsize must be positive integer"
            )

    def __init__(self) -> None:
        self._res_status: Optional[HTTPStatus] = None
        self._res_headers: List[Tuple[str, str]] = []
        self._res_body = BufferedConcatIterator(bufsize=self.bufsize)

    @property
    @abstractmethod
    def content_length(self) -> Optional[int]:
        pass

    @property
    @abstractmethod
    def method(self) -> str:
        pass

    @staticmethod
    def make_header(
        name: str,
        value: str,
        **params: str
    ) -> Tuple[str, str]:
        params = [f'; {header}={val}' for header, val in params.items()]
        params = "".join(params)
        return (name, value + params)

    def add_header(
        self,
        name: str,
        value: str,
        **params: str
    ) -> None:
        """Add response header with MIME parameters.

        Parameters
        ----------
        name : str
            Field name of the header
        value : str
            Value of the field
        **params : str
            MIME parameters added to the field
        """
        self._res_headers.append(self.make_header(name, value, **params))

    def add_headers(self, *headers: Tuple[str, str]) -> None:
        """Add response headers at once.

        Parameters
        ----------
        **headers : str
            Header's info whose header is the field name.

        Notes
        -----
        This method would be used as a shortcut to register multiple
        headers. If it requires adding MIME parameters, developers
        can use the 'add_header' method.
        """
        for name, val in headers:
            self.add_header(name, val)

    def add_content_type(self, content_type: ContentType) -> None:
        params = {}
        if content_type.charset:
            params["charset"] = content_type.charset
        if content_type.boundary:
            params["boundary"] = content_type.boundary
        self.add_header("Content-Type", content_type.media_type, **params)

    def add_content_length(self, length: int) -> None:
        self.add_header("Content-Length", str(length))

    def add_content_length_body(self, body: bytes) -> None:
        self.add_header("Content-Length", str(len(body)))

    def _set_status_safely(self, status: HTTPStatus) -> None:
        """Check if response status code already exists.

        Raises
        ------
        StatusCodeAlreadySetError
            Raised if response status code has already been set.
        """
        if self._res_status:
            raise StatusCodeAlreadySetError(
                "Response status code has already been set."
            )
        self._res_status = status

    def send_only_status(self, status: HTTPStatus = HTTPStatus.OK) -> None:
        """Set specified status code to one of response.

        This method can be used if a callback doesn't need to send response
        body.

        Parameters
        ----------
        status : HTTPStatus, optional
            HTTP status of the response, by default `HTTPStatus.OK`
        """
        self._set_status_safely(status)

    def send_body(
        self,
        body: Union[bytes, Iterable[bytes]],
        /,
        *others: Union[bytes, Iterable[bytes]],
        content_type: Optional[ContentType] = DEFAULT_CONTENT_TYPE_PLAIN,
        status: HTTPStatus = HTTPStatus.OK
    ) -> None:
        """Set given binary to the response body.

        Parameters
        ----------
        body : bytes, optional
            Binary to be set to the response body, by default `b""`
        content_type : ContentType, optional
            `Content-Type` header to be sent,
            by default `DEFAULT_CONTENT_TYPE_PLAIN`
        status : HTTPStatus, optional
            HTTP status of the response, by default `HTTPStatus.OK`

        Notes
        -----
        If the parameter `content_type` is specified, then the `Content-Type`
        header is to be added.

        `DEFAULT_CONTENT_TYPE_PLAIN` has its MIME type of `text/plain`, and the
        other attributes are `None`. If another value of `Content-Type` is
        needed, then you should generate new `ContentType` instance with
        attributes you want.

        Raises
        ------
        StatusCodeAlreadySetError
            Raised if response status code has already been set.
        """
        self._set_status_safely(status)

        bodies = [body]
        bodies.extend(others)

        is_all_bytes = True
        is_empty = False
        for chunk in bodies:
            is_all_bytes &= isinstance(chunk, bytes)
            if is_all_bytes:
                is_empty |= len(chunk) > 0
            self._res_body.append(chunk)

        if content_type:
            self.add_content_type(content_type)

        # Content-Length if avalidable
        if is_all_bytes and not is_empty:
            length = sum(map(len, bodies))
            self.add_content_length("Content-Length", length)

    def send_json(
        self,
        body: Dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK,
        encoding: str = "UTF-8"
    ) -> None:
        """Set given json data to the response body.

        Parameters
        ----------
        body : Dict[str, Any]
            Json data to be set to the response body
        status : HTTPStatus, optional
            HTTP status of the response, by default HTTPStatus.OK
        encoding : str, optional
            Encoding of the Json data, by default "UTF-8"

        Raises
        ------
        StatusCodeAlreadySetError
            Raised if response status code has already been set.
        """
        body = json.dumps(body).encode(encoding=encoding)
        content_type = ContentType(
            media_type=MediaTypes.json,
            charset=encoding
        )
        self.send_body(body, content_type=content_type, status=status)

    def send_file(
        self,
        path: str,
        fname: Optional[str] = None,
        content_type: str = DEFAULT_CONTENT_TYPE_PLAIN,
        status: HTTPStatus = HTTPStatus.OK
    ) -> None:
        file_iter = BufferedFileIterator(path)
        self.send_body(file_iter, content_type=content_type, status=status)

        length = os.path.getsize(path)
        self.add_header("Content-Length", str(length))
        if fname:
            self.add_header(
                "Content-Disposition",
                "attachment",
                filename=fname
            )

    def send_err(self, err: ErrInfoBase) -> None:
        """Set error to the response body.

        Parameters
        ----------
        err : ErrInfoBase
            Error information to be sent

        Raises
        ------
        StatusCodeAlreadySetError
            Raised if response status code has already been set.
        """
        status, headers, body = err.get_all_form()
        self._set_status_safely(status)
        self._attach_err_headers(headers)
        self._res_body.append(body)

        if body:
            content_type = err._content_type_
            self.add_content_type(content_type)
            self.add_content_length_body(body)

    @abstractmethod
    def _attach_err_headers(self, headers: List[Tuple[str, str]]) -> None:
        pass


class WSGIEndpoint(WSGIEndpointBase, HTTPMixIn):

    def __init__(
        self,
        environ: Dict[str, Any],
        flexible_locs: Tuple[str, ...],
        *parcel: Any
    ) -> None:
        WSGIEndpointBase.__init__(self, environ, flexible_locs, *parcel)
        HTTPMixIn.__init__(self)

    def _recv_body_secure(self) -> bytes:
        """Receive request body securely.

        Returns
        -------
        bytes
            Request body
        """
        # TODO
        #   Take measures against DoS attack.
        content_length = self.content_length
        if content_length is None:
            content_length = -1

        body = self._environ.get("wsgi.input").read(content_length)
        return body

    @cached_property
    def body(self) -> bytes:
        return self._recv_body_secure()

    @property
    def content_length(self) -> Optional[int]:
        length = self._environ.get("CONTENT_LENGTH")
        if length:
            return int(length)
        return None

    @property
    def method(self) -> str:
        return self._environ.get("REQUEST_METHOD")

    def _attach_err_headers(self, headers: List[Tuple[str, str]]) -> None:
        self._res_headers = headers


class ASGIHTTPEndpoint(ASGIEndpointBase, HTTPMixIn):

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # NOTE
        #   All response methods of its subclass must be awaitables.
        for method in HTTPMethods:
            callback = cls._get_response_method(method)
            if callback and not inspect.iscoroutinefunction(callback):
                raise TypeError(
                    f"{cls.__name__}.{callback.__name__} must be an awaitable"
                    ", not a callable."
                )

    def __init__(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        flexible_locs: Tuple[str, ...],
        *parcel
    ) -> None:
        ASGIEndpointBase.__init__(self, scope, flexible_locs, *parcel)
        HTTPMixIn.__init__(self)

        self._res_headers: List[Tuple[bytes, bytes]] = []
        self._receive = receive
        self._req_body = b""
        self._is_disconnected = False

    @awaitable_cached_property
    async def body(self) -> bytes:
        buffer = BytesIO()
        more_body = True

        while more_body:
            chunk = await self._receive()
            type = chunk.get("type")
            if type == ASGIHTTPEvents.disconnect:
                self._is_disconnected = True
                break

            buffer.write(chunk.get("body", b""))
            more_body = chunk.get("more_body", False)

        buffer.flush()
        data = buffer.getvalue()
        buffer.close()
        return data

    @awaitable_property
    async def is_disconnected(self) -> bool:
        await self.body
        return self._is_disconnected

    @property
    def content_length(self) -> Optional[int]:
        length = self.get_header("Content-Length")
        if length:
            return int(length)
        return None

    @property
    def method(self) -> str:
        return self._scope.get("method")

    def add_header(
        self,
        name: str,
        value: str,
        **params: str
    ) -> None:
        header = tuple(
            map(codecs.encode, self.make_header(name, value, **params))
        )
        self._res_headers.append(header)

    def _attach_err_headers(self, headers: List[Tuple[str, str]]) -> None:
        self._res_headers = [
            tuple(map(codecs.encode, header)) for header in headers
        ]

# ----------------------------------------------------------------------------
