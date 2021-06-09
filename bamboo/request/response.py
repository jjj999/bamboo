from __future__ import annotations
import http.client
import typing as t

from ..api.base import BinaryApiData
from ..http import ContentType
from ..request import ResponseData_t
from ..util.deco import cached_property


__all__ = []


class ResponseBodyAlreadyReadError(Exception):
    """Response body has already been read and data consistensy would be
    broken.
    """
    pass


class Response(t.Generic[ResponseData_t]):
    """Response returned by request functions of `http` or `https` modules.

    Examples:
        ```python
        from bamboo.request import http

        with http.get("http://localhost:8000/hello") as res:
            headers = res.headers

            if res.ok:
                body = res.body
                print(body)
            else:
                print(f"Error occured. Response status: {res.status}")

            # The session will be automatically closed by leaving the block.
        ```
    """

    def __init__(
        self,
        conn: http.client.HTTPConnection,
        res: http.client.HTTPResponse,
        datacls: t.Type[ResponseData_t] = BinaryApiData,
    ) -> None:
        """
        Args:
            conn: connection object of a session.
            res: HTTPResponse of a request.
            datacls: ApiData class to attach raw response body.
        """
        self._conn = conn
        self._res = res
        self._datacls = datacls
        self._is_read = False

    @property
    def headers(self) -> http.client.HTTPMessage:
        """All response headers.
        """
        return self._res.msg

    def get_header(self, name: str) -> t.Optional[str]:
        """Retrive header value from response headers.

        Args:
            name: Header name.

        Returns:
            Value of header if existing, None otherwise.
        """
        return self._res.getheader(name)

    @property
    def url(self) -> str:
        """Real url of the endpoint.
        """
        return self._res.geturl()

    @property
    def status(self) -> int:
        """Response status.
        """
        return self._res.status

    @property
    def version(self) -> int:
        """HTTP version of the session.
        """
        return self._res.version

    @property
    def ok(self) -> bool:
        """If request succeeded or not.
        """
        status = self.status
        if 200 <= status < 300:
            return True
        return False

    @property
    def is_closed(self) -> bool:
        """If the session is closed or not.
        """
        return self._res.closed

    @property
    def fileno(self) -> int:
        """File number of the socket.
        """
        return self._res.fileno()

    @property
    def content_length(self) -> t.Optional[int]:
        """Content length of the response if existing, None otherwise.
        """
        length = self.get_header("Content-Length")
        if length is not None:
            return int(length)
        return None

    def read(self, amt: t.Optional[int] = None) -> bytes:
        """Reads and returns the response body.

        Args:
            amt: Amount of the binary, all of it if None.

        Returns:
            Results of reading. Its length may be less than `amt`.
        """
        if not self._is_read:
            self._is_read = True
        return self._res.read(amt)

    @cached_property
    def body(self) -> bytes:
        """The raw response body.

        This property returns all reponse body and caches the result.
        If you want to read the response body step-by-step by chunks,
        then you can use the `read` method, but cannot use both the
        property and the `read` method.

        Raises:
            ResponseBodyAlreadyReadError: Raised if the `read` method has
                been already used.
        """
        if self._is_read:
            raise ResponseBodyAlreadyReadError(
                "Response body has been already read by 'read' method. "
                "Data consistensy would be broken."
            )
        return self._res.read(self.content_length)

    def attach(
        self,
        datacls: t.Optional[t.Type[ResponseData_t]] = None,
    ) -> ResponseData_t:
        """Generate new object of specified ApiData from response body.

        Args:
            datacls: ApiData class or its subclass.

        Returns:
            ResponseData_t: Generated object.
        """
        content_type_raw = self.get_header("Content-Type")
        if content_type_raw:
            content_type = ContentType.parse(content_type_raw)

        if datacls is None:
            if content_type_raw is None:
                content_type = self._datacls.__content_type__
            return self._datacls.__validate__(self.body, content_type)
        else:
            if content_type_raw is None:
                content_type = datacls.__content_type__
            return datacls.__validate__(self.body, content_type)

    def close(self) -> None:
        """Close the session.
        """
        self._conn.close()

    def __enter__(self) -> Response[ResponseData_t]:
        return self

    def __exit__(self, type, value, traceback) -> None:
        self.close()
