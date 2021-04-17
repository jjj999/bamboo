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
    TYPE_CHECKING,
    TypeVar,
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
from bamboo.io import BufferedConcatIterator, BufferedFileIterator
from bamboo.util.deco import (
    awaitable_property,
    awaitable_cached_property,
    cached_property,
)
from bamboo.util.header import make_header


if TYPE_CHECKING:
    from bamboo.app import (
        AppBase,
        WSGIApp,
        ASGIHTTPApp,
    )

    App_t = TypeVar("App_t", bound=AppBase)


__all__ = []


# Base classes for each interfaces  ------------------------------------------

class EndpointBase(metaclass=ABCMeta):
    """Base class of Endpoint to define logic to requests.

    Endpoint is one of the core concept of Bamboo, and this class defines
    its basic behavior. All endpoints must inherit this class.

    Note:
        This class is an abstract class. Consider using its subclasses.
    """

    def __init__(
        self,
        app: App_t,
        flexible_locs: Tuple[str, ...],
        *parcel: Any
    ) -> None:
        """
        Note:
            DO NOT generate its instance. Its object will be initialized
            by application object.

        Args:
            flexible_locs: Flexible locations requested.
            *parcel: Parcel sent via application object.
        """
        self._app = app
        self._flexible_locs = flexible_locs
        self.setup(*parcel)

    def setup(self, *parcel) -> None:
        """Execute setup of the endpoint object.

        This method will execute at initialization of the object by specifying
        parcel. The parcel is sent with `set_parcel()` method of
        the application object which has included the object as one of
        the its endpoints. This method can be used as a substitute for
        the `__init__` method.

        This method is useful in some cases like below:

        - Making an endpoint class a reusable component
        - Injecting environmental dependencies using something like a
            setting file

        Args:
            *parcel: Parcel sent via application object.

        Examples:
            ```python
            app = WSGIApp()

            @app.route("hello")
            class HelloEndpoint(WSGIEndpoint):

                def setup(self, server_name: str) -> None:
                    self._server_name = server_name

                def do_GET(self) -> None:
                    self.send_body(f"Hello from {self._server_name}".encode())

            if __name__ == "__main__":
                SERVER_NAME = "awesome_server"
                app.set_parcel(HelloEndpoint, SERVER_NAME)

                WSGITestExecutor.debug(app, "", 8000)
            ```
        """
        pass

    @property
    def app(self) -> App_t:
        """Application object handling the endpoint.
        """
        return self._app

    @property
    def flexible_locs(self) -> Tuple[str, ...]:
        """Flexible locations extracted from requested URI.
        """
        return self._flexible_locs

    @property
    @abstractmethod
    def http_version(self) -> str:
        """HTTP Version on communication.
        """
        pass

    @property
    @abstractmethod
    def scheme(self) -> str:
        """Scheme of requested URI.
        """
        pass

    @abstractmethod
    def get_client_addr(self) -> Tuple[Optional[str], Optional[int]]:
        """Retrieve client address, pair of its IP address and port.

        Note:
            IP address and port may be None if retrieving the address from
            server application would fail, so it is recommended to confirm
            your using server application's spec.

        Returns:
            Pair of IP and port of client.
        """
        pass

    @abstractmethod
    def get_server_addr(self) -> Tuple[Optional[str], Optional[int]]:
        """Retrive server address, pair of its IP address and port.

        Note:
            IP address and port may be None if retrieving the address from
            server application would fail, so it is recommended to confirm
            your using server application's spec.

        Returns:
            Pair of IP and port of server.
        """
        pass

    @abstractmethod
    def get_host_addr(self) -> Tuple[Optional[str], Optional[int]]:
        """Retrive host name and port from requested headers.

        Returns:
            Pair of host name and port.
        """
        pass

    @abstractmethod
    def get_header(self, name: str) -> Optional[str]:
        """Retrive header value from requested headers.

        Args:
            name: Header name.

        Returns:
            Value of header if existing, None otherwise.
        """
        pass

    @property
    @abstractmethod
    def path(self) -> str:
        """Path of requested URI.
        """
        pass

    @cached_property
    @abstractmethod
    def queries(self) -> Dict[str, List[str]]:
        """Query parameters specified to requested URI.
        """
        pass

    def get_query(self, name: str) -> List[str]:
        """Get value of query parameter.

        Args:
            name: Key name of the parameter

        Returns:
            Value of the parameter. The value of list may have multiple
            items if client specifies the parameter in several times.
        """
        query = self.queries.get(name)
        if query:
            return query
        return []

    @cached_property
    @abstractmethod
    def content_type(self) -> Optional[ContentType]:
        """Content type of request body.

        Returns:
            Content type if existing, None otherwise.
        """
        pass


class WSGIEndpointBase(EndpointBase):
    """Base class of endpoints compliant with the WSGI.

    This class implements abstract methods of `EndpointBase` with the WSGI.
    However, this class doesn't implement some methods to structure responses.

    Note:
        DO NOT use this class as the super class of your endpoints. Consider
        to use subclasses of the class like `WSGIEndpoint`.
    """

    def __init__(
        self,
        app: WSGIApp,
        environ: Dict[str, Any],
        flexible_locs: Tuple[str, ...],
        *parcel: Any
    ) -> None:
        """
        Args:
            environ: environ variable received from WSGI server.
            flexible_locs: flexible locations requested.
            *parcel: Parcel sent via application object.
        """
        super().__init__(app, flexible_locs, *parcel)

        self._environ = environ

    @property
    def environ(self) -> Dict[str, Any]:
        """environ variable received from WSGI server.
        """
        return self._environ

    @property
    def wsgi_version(self) -> str:
        """WSGI version number.
        """
        version = self._environ.get("wsgi.version")
        return ".".join(map(str, version))

    @property
    def server_software(self) -> str:
        """Software name of WSGI server.
        """
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
        name = name.upper()
        if name == "CONTENT-TYPE":
            return self.content_type
        if name == "CONTENT-LENGTH":
            return self._environ.get("CONTENT_LENGTH")

        name = "HTTP_" + name.replace("-", "_")
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
        if raw:
            return ContentType.parse(raw)
        return None


class ASGIEndpointBase(EndpointBase):
    """Base class of endpoints compliant with the ASGI.

    This class implements abstract methods of `EndpointBase` with the ASGI.
    However, this class doesn't implement some methods to structure responses.

    Note:
        DO NOT use this class as the super class of your endpoints. Consider
        to use subclasses of the class like `ASGIHTTPEndpoint`.
    """

    def __init__(
        self,
        app: App_t,
        scope: Dict[str, Any],
        flexible_locs: Tuple[str, ...],
        *parcel: Any
    ) -> None:
        """
        Args:
            scope: scope variable received from ASGI server.
            flexible_locs: Flexible locations requested.
            *parcel: Parcel sent via application object.
        """
        super().__init__(app, flexible_locs, *parcel)

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
        """scope variable received from ASGI server.
        """
        return self._scope

    @property
    def scope_type(self) -> str:
        """Scope type on ASGI.
        """
        return self._scope.get("type")

    @property
    def asgi_version(self) -> str:
        """ASGI version.
        """
        return self._scope.get("asgi").get("version")

    @property
    def spec_version(self) -> str:
        """Spec version on ASGI.
        """
        return self._scope.get("asgi").get("spec_version")

    @property
    def raw_path(self) -> bytes:
        """The original HTTP path received from client.
        """
        return self._scope.get("raw_path")

    @property
    def root_path(self) -> str:
        """The root path ASGI application is mounted at.
        """
        return self._scope.get("root_path")

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
    def headers(self) -> Dict[str, str]:
        """Request headers.
        """
        return self._req_headers

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

# ----------------------------------------------------------------------------

# HTTP  ----------------------------------------------------------------------

class StatusCodeAlreadySetError(Exception):
    """Raised if response status code has already been set."""
    pass


class HTTPMixIn(metaclass=ABCMeta):
    """Mixin class for HTTP endpoints.

    This class assumes that endpoint classes inherit this class for HTTP.
    So, this class do not work alone.

    Note:
        DO NOT use this class alone. This class work correctly by inheriting
        it, implementing its abstract methods, and call its `__init__()`
        method in the one of the subclass.
    """

    __PREFIX_RESPONSE = "do_"
    __PREFIX_PRE_RESPONSE = "pre_"

    bufsize = 8192

    @classmethod
    def _get_pre_response_method(
        cls,
        method: str
    ) -> Optional[Callable[[EndpointBase], None]]:
        """Retrieve pre-response method corresponding with given HTTP method.

        Args:
            method: HTTP method

        Returns:
            Pre-response method with given name.
        """
        mname = cls.__PREFIX_PRE_RESPONSE + method
        if hasattr(cls, mname):
            return getattr(cls, mname)
        return None

    @classmethod
    def _get_response_method(
        cls,
        method: str
    ) -> Optional[Callable[[EndpointBase], None]]:
        """Retrieve response methods with given HTTP method.

        Args:
            method: HTTP method

        Returns:
            Callback with given name.
        """
        mname = cls.__PREFIX_RESPONSE + method
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
        """Content length of request body if existing.
        """
        pass

    @property
    @abstractmethod
    def method(self) -> str:
        """HTTP method requested from client.
        """
        pass

    def add_header(
        self,
        name: str,
        value: str,
        **params: str
    ) -> None:
        """Add response header with MIME parameters.

        Args:
            name: Field name of the header.
            value: Value of the field.
            **params: Directives added to the field.
        """
        self._res_headers.append(make_header(name, value, **params))

    def add_headers(self, *headers: Tuple[str, str]) -> None:
        """Add response headers at once.

        Note:
            This method would be used as a shortcut to register multiple
            headers. If it requires adding MIME parameters, developers
            can use the 'add_header' method.

        Args:
            **headers: Header's info whose header is the field name.
        """
        for name, val in headers:
            self.add_header(name, val)

    def add_content_type(self, content_type: ContentType) -> None:
        """Add Content-Type header of response.

        Args:
            content_type: Information of Content-Type header.
        """
        self.add_header(*content_type.to_header())

    def add_content_length(self, length: int) -> None:
        """Add Content-Length header of response.

        Args:
            length: Size of response body.
        """
        self.add_header("Content-Length", str(length))

    def add_content_length_body(self, body: bytes) -> None:
        """Add Content-Length header of response by response body.

        Args:
            body: Response body.
        """
        self.add_header("Content-Length", str(len(body)))

    def _set_status_safely(self, status: HTTPStatus) -> None:
        """Check if response status code already exists.

        Raises:
            StatusCodeAlreadySetError: Raised if response status code has
                already been set.
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

        Args:
            status: HTTP status of the response.
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

        Note:
            If the parameter `content_type` is specified, then
            the `Content-Type` header is to be added.

            `DEFAULT_CONTENT_TYPE_PLAIN` has its MIME type of `text/plain`,
            and the other attributes are `None`. If another value of
            `Content-Type` is needed, then you should generate new
            `ContentType` instance with attributes you want.

        Args:
            body: Binary to be set to the response body.
            content_type: `Content-Type` header to be sent.
            status: HTTP status of the response.

        Raises:
            StatusCodeAlreadySetError: Raised if response status code has
                already been set.
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
            self.add_content_length(length)

    def send_json(
        self,
        body: Dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK,
        encoding: str = "UTF-8"
    ) -> None:
        """Set given json data to the response body.

        Args:
            body: Json data to be set to the response body.
            status: HTTP status of the response.
            encoding: Encoding of the Json data.

        Raises:
            StatusCodeAlreadySetError: Raised if response status code
                has already been set.
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
        """Set file to be sent as response.

        Args:
            path: File path.
            fname: File name to be sent.
            content_type: Content type of the response.
            status: HTTP status of the response.
        """
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

    @abstractmethod
    def _attach_err_headers(self, headers: List[Tuple[str, str]]) -> None:
        """Update response headers for error response.

        Args:
            headers: Response headers of the error response.
        """
        pass


class WSGIEndpoint(WSGIEndpointBase, HTTPMixIn):
    """HTTP endpoint class compliant with the WSGI.

    This class is a complete class of endpoints, communicating on HTTP.
    This class has all attributes of `WSGIEndpointBase` and `HTTPMixIn`,
    and you can define its subclass and use them in your response methods.

    Examples:
        ```python
        app = WSGIApp()

        @app.route("hello")
        class HelloEndpoint(WSGIEndpoint):

            # RECOMMEND to use `data_format` decorator
            def do_GET(self) -> None:
                response = {"greeting": "Hello, Client!"}
                self.send_json(response)

            def do_POST(self) -> None:
                req_body = self.body
                print(req_body)
        ```
    """

    def __init__(
        self,
        app: WSGIApp,
        environ: Dict[str, Any],
        flexible_locs: Tuple[str, ...],
        *parcel: Any
    ) -> None:
        """
        Args:
            environ: environ variable received from WSGI server.
            flexible_locs: flexible locations requested.
            *parcel: Parcel sent via application object.
        """
        WSGIEndpointBase.__init__(self, app, environ, flexible_locs, *parcel)
        HTTPMixIn.__init__(self)

    def _recv_body_secure(self) -> bytes:
        """Receive request body securely.

        Returns:
            Request body sent to the endpoint.
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
        """Request body received from client.
        """
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
    """HTTP endpoint class compliant with the ASGI.

    This class is a complete class of endpoints, communicating on HTTP.
    This class has all attributes of `ASGIEndpointBase` and `HTTPMixIn`,
    and you can define its subclass and use them in your response methods.

    Examples:
        ```python
        app = ASGIHTTPApp()

        @app.route("hello")
        class HelloEndpoint(ASGIHTTPEndpoint):

            # RECOMMEND to use `data_format` decorator
            async def do_GET(self) -> None:
                response = {"greeting": "Hello, Client!"}
                self.send_json(response)

            async def do_POST(self) -> None:
                req_body = async self.body
                print(req_body)
        ```
    """

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
        app: ASGIHTTPApp,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        flexible_locs: Tuple[str, ...],
        *parcel
    ) -> None:
        """
        Args:
            scope: scope variable received from ASGI server.
            receive: `receive` method given from ASGI server.
            flexible_locs: Flexible locations requested.
            *parcel: Parcel sent via application object.
        """
        ASGIEndpointBase.__init__(self, app, scope, flexible_locs, *parcel)
        HTTPMixIn.__init__(self)

        self._res_headers: List[Tuple[bytes, bytes]] = []
        self._receive = receive
        self._req_body = b""
        self._is_disconnected = False

    @awaitable_cached_property
    async def body(self) -> bytes:
        """Request body received from client.
        """
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
        """Whether the connection is closed or not.
        """
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
            map(codecs.encode, make_header(name, value, **params))
        )
        self._res_headers.append(header)

    def _attach_err_headers(self, headers: List[Tuple[str, str]]) -> None:
        self._res_headers = [
            tuple(map(codecs.encode, header)) for header in headers
        ]

# ----------------------------------------------------------------------------
