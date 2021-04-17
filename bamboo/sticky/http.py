from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
import inspect
from typing import (
    Any, Dict,
    Optional,
    Set,
    Tuple,
    Type,
)

from bamboo.api import ApiData, ValidationFailedError
from bamboo.base import AuthSchemes
from bamboo.endpoint import ASGIHTTPEndpoint, WSGIEndpoint
from bamboo.error import (
    DEFAULT_BASIC_AUTH_HEADER_NOT_FOUND_ERROR,
    DEFAULT_BEARER_AUTH_HEADER_NOT_FOUND_ERROR,
    DEFAULT_HEADER_NOT_FOUND_ERROR,
    DEFUALT_INCORRECT_DATA_FORMAT_ERROR,
    DEFAULT_NOT_APPLICABLE_IP_ERROR,
    ErrInfo,
)
from bamboo.sticky import (
    Callback_ASGI_t,
    Callback_WSGI_t,
    Callback_t,
    CallbackDecorator_t,
    _get_bamboo_attr,
)
from bamboo.util.convert import decode2binary
from bamboo.util.ip import is_valid_ipv4


__all__ = [
    "AuthSchemeConfig",
    "ClientInfo",
    "DataFormatConfig",
    "DataFormatInfo",
    "HTTPErrorConfig",
    "MultipleAuthSchemeError",
    "RequiredHeaderConfig",
    "RequiredHeaderInfo",
    "RestrictedClientsConfig",
    "basic_auth",
    "bearer_auth",
    "data_format",
    "has_header_of",
    "may_occur",
    "restricts_client",
]


class ConfigBase(metaclass=ABCMeta):

    ATTR: str

    @abstractmethod
    def get(self) -> Any:
        pass

    @abstractmethod
    def set(self, *args, **kwargs) -> Callback_t:
        pass


class HTTPErrorConfig(ConfigBase):

    ATTR = _get_bamboo_attr("errors")

    def __init__(self, callback) -> None:
        if not hasattr(callback, self.ATTR):
            setattr(callback, self.ATTR, set())

        self._callback = callback
        self._registered: Set[ErrInfo] = getattr(callback, self.ATTR)

    def get(self) -> Tuple[Type[ErrInfo], ...]:
        return tuple(self._registered)

    def set(self, *errors: Type[ErrInfo]) -> Callback_t:
        for err in errors:
            self._registered.add(err)
        return self._callback


def may_occur(*errors: Type[ErrInfo]) -> CallbackDecorator_t:
    """Register error classes to callback on `Endpoint`.

    Args:
        *errors: Error classes which may occuur.

    Returns:
        CallbackDecorator_t: Decorator to register
            error classes to callback.

    Examples:
        ```python
        class MockErrInfo(ErrInfo):
            http_status = HTTPStatus.INTERNAL_SERVER_ERROR

            def get_body(self) -> bytes:
                return b"Intrernal server error occured"

        class MockEndpoint(WSGIEndpoint):

            @may_occur(MockErrInfo)
            def do_GET(self) -> None:
                # Do something...

                # It is possible to send error response.
                if is_some_flag():
                    self.send_err(MockErrInfo())

                self.send_only_status()
        ```
    """

    def wrapper(callback: Callback_t) -> Callback_t:
        config = HTTPErrorConfig(callback)
        return config.set(*errors)

    return wrapper


@dataclass(eq=True, frozen=True)
class DataFormatInfo:
    """`dataclass` with information of data format at callbacks on `Endpoint`.

    Attributes:
        input (Optional[Type[ApiData]]): Input data format.
        output (Optional[Type[ApiData]]): Output data format.
        is_validate (bool): If input data is to be validate.
        err_validate (ErrInfo): Error information sent
            when validation failes.
    """
    input: Optional[Type[ApiData]] = None
    output: Optional[Type[ApiData]] = None
    is_validate: bool = True
    err_validate: ErrInfo = DEFUALT_INCORRECT_DATA_FORMAT_ERROR
    err_noheader: ErrInfo = DEFAULT_HEADER_NOT_FOUND_ERROR


class DataFormatConfig(ConfigBase):

    ATTR = _get_bamboo_attr("data_format")

    def __init__(self, callback: Callback_t) -> None:
        super().__init__()

        self._callback = callback

    def get(self) -> Optional[DataFormatInfo]:
        return getattr(self._callback, self.ATTR, None)

    def set(self, dataformat: DataFormatInfo) -> Callback_t:
        setattr(self._callback, self.ATTR, dataformat)
        if not dataformat.is_validate:
            return self._callback

        if inspect.iscoroutinefunction(self._callback):
            if dataformat.input:
                func = self.decorate_asgi
            else:
                func = self.decorate_asgi_no_input
        else:
            if dataformat.input:
                func = self.decorate_wsgi
            else:
                func = self.decorate_wsgi_no_input

        return func(self._callback, dataformat)

    @staticmethod
    def decorate_wsgi(
        callback: Callback_WSGI_t,
        dataformat: DataFormatInfo
    ) -> Callback_WSGI_t:

        @may_occur(dataformat.err_validate.__class__)
        @has_header_of("Content-Type", dataformat.err_noheader)
        def _callback(self: WSGIEndpoint, *args) -> None:
            body = self.body
            try:
                data = dataformat.input(body, self.content_type)
            except ValidationFailedError:
                raise dataformat.err_validate

            callback(self, data, *args)

        _callback.__dict__ = callback.__dict__
        return _callback

    @staticmethod
    def decorate_wsgi_no_input(
        callback: Callback_WSGI_t,
        dataformat: DataFormatInfo
    ) -> Callback_WSGI_t:

        def _callback(self: WSGIEndpoint, *args) -> None:
            setattr(self, "body", b"")
            callback(self, *args)

        _callback.__dict__ = callback.__dict__
        return _callback

    @staticmethod
    def decorate_asgi(
        callback: Callback_ASGI_t,
        dataformat: DataFormatInfo
    ) -> Callback_ASGI_t:

        @may_occur(dataformat.err_validate.__class__)
        @has_header_of("Content-Type", dataformat.err_noheader)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            body = await self.body
            try:
                data = dataformat.input(body, self.content_type)
            except ValidationFailedError:
                raise dataformat.err_validate

            await callback(self, data, *args)

        _callback.__dict__ = callback.__dict__
        return _callback

    @staticmethod
    def decorate_asgi_no_input(
        callback: Callback_ASGI_t,
        dataformat: DataFormatInfo
    ) -> Callback_ASGI_t:

        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            # NOTE
            #   Reference awaitable_cached_property
            body_property = await self.__class__.body
            body_property._obj2val[self] = b""
            await callback(self, *args)

        _callback.__dict__ = callback.__dict__
        return _callback


def data_format(
    input: Optional[Type[ApiData]] = None,
    output: Optional[Type[ApiData]] = None,
    is_validate: bool = True,
    err_validate: ErrInfo = DEFUALT_INCORRECT_DATA_FORMAT_ERROR,
    err_noheader: ErrInfo = DEFAULT_HEADER_NOT_FOUND_ERROR,
) -> CallbackDecorator_t:
    """Set data format of input/output data as API to callback on
    `Endpoint`.

    This decorator can be used to add attributes of data format information
    to a response method, and execute validation if input raw data has
    expected format defined on `input` argument.

    To represent no data inputs/outputs, specify `input`/`output` arguments
    as `None`. If `input` is `None`, then any data received from client will
    not be read. If `is_validate` is `False`, then validation will not be
    executed.

    Args:
        input: Input data format.
        output: Output data format.
        is_validate: If input data is to be validated.
        err_validate: Error information sent when validation failes.

    Returns:
        Decorator to add attributes of data format information to callback.

    Examples:
        ```python
        class UserData(JsonApiData):
            name: str
            email: str
            age: int

        class MockEndpoint(WSGIEndpoint):

            @data_format(input=UserData, output=None)
            def do_GET(self, rec_body: UserData) -> None:
                user_name = rec_body.name
                # Do something...
        ```
    """
    dataformat = DataFormatInfo(
        input,
        output,
        is_validate,
        err_validate,
        err_noheader,
    )

    def wrapper(callback: Callback_t) -> Callback_t:
        config = DataFormatConfig(callback)
        return config.set(dataformat)

    return wrapper


@dataclass(eq=True, frozen=True)
class RequiredHeaderInfo:
    """`dataclass` with information of header which should be included in
    response headers.

    Attributes:
        header: Name of header.
        err: Error information sent when the header is not included.
    """
    header: str
    err: ErrInfo = DEFAULT_HEADER_NOT_FOUND_ERROR


class RequiredHeaderConfig(ConfigBase):

    ATTR = _get_bamboo_attr("required_headers")

    def __init__(self, callback: Callback_t) -> None:
        super().__init__()

        if not hasattr(callback, self.ATTR):
            setattr(callback, self.ATTR, set())

        self._callback = callback
        self._registered: Set[RequiredHeaderInfo] = getattr(callback, self.ATTR)

    def get(self) -> Tuple[RequiredHeaderInfo]:
        return tuple(self._registered)

    def set(self, info: RequiredHeaderInfo) -> Callback_t:
        self._registered.add(info)

        if inspect.iscoroutinefunction(self._callback):
            func = self.decorate_asgi
        else:
            func = self.decorate_wsgi

        return func(self._callback, info)

    @staticmethod
    def decorate_wsgi(
        callback: Callback_WSGI_t,
        info: RequiredHeaderInfo
    ) -> Callback_WSGI_t:

        @may_occur(info.err.__class__)
        def _callback(self: WSGIEndpoint, *args) -> None:
            val = self.get_header(info.header)
            if val is None:
                raise info.err

            callback(self, *args)

        _callback.__dict__ = callback.__dict__
        return _callback

    @staticmethod
    def decorate_asgi(
        callback: Callback_ASGI_t,
        info: RequiredHeaderInfo
    ) -> Callback_ASGI_t:

        @may_occur(info.err.__class__)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            val = self.get_header(info.header)
            if val is None:
                raise info.err

            await callback(self, *args)

        _callback.__dict__ = callback.__dict__
        return _callback


def has_header_of(
    header: str,
    err: ErrInfo = DEFAULT_HEADER_NOT_FOUND_ERROR
) -> CallbackDecorator_t:
    """Set callback up to receive given header from clients.

    If request headers don't include specified `header`, then response
    headers and body will be made based on `err` and sent.

    Args:
        header: Name of header.
        err: Error information sent when specified `header` is not found.

    Returns:
        Decorator to make callback to be set up to receive the header.

    Examples:
        ```python
        class BasicAuthHeaderNotFoundErrInfo(ErrInfo):
            http_status = HTTPStatus.UNAUTHORIZED

            def get_headers(self) -> List[Tuple[str, str]]:
                return [("WWW-Authenticate", 'Basic realm="SECRET AREA"')]

        class MockEndpoint(WSGIEndpoint):

            @has_header_of("Authorization", BasicAuthHeaderNotFoundErrInfo())
            def do_GET(self) -> None:
                # It is guaranteed that request headers include the
                # `Authorization` header at this point.
                header_auth = self.get_header("Authorization")

                # Do something...
        ```
    """
    info = RequiredHeaderInfo(header, err)

    def wrapper(callback: Callback_t) -> Callback_t:
        config = RequiredHeaderConfig(callback)
        return config.set(info)

    return wrapper


@dataclass(eq=True, frozen=True)
class ClientInfo:

    ip: str
    port: Optional[int] = None


_RestrictedClient_t = Dict[str, Set[Optional[int]]]


class RestrictedClientsConfig(ConfigBase):

    ATTR = _get_bamboo_attr("restricted_clients")

    def __init__(self, callback: Callback_t) -> None:
        super().__init__()

        if not hasattr(callback, self.ATTR):
            setattr(callback, self.ATTR, {})

        self._callback = callback
        self._registered: _RestrictedClient_t = getattr(callback, self.ATTR)

    def get(self) -> _RestrictedClient_t:
        return self._registered.copy()

    def set(
        self,
        *clients: ClientInfo,
        err: ErrInfo = DEFAULT_NOT_APPLICABLE_IP_ERROR
    ) -> Callback_t:
        for client in clients:
            if not is_valid_ipv4(client.ip):
                raise ValueError(f"{client.ip} is an invalid IP address.")
            if client.ip == "localhost":
                client = ClientInfo("127.0.0.1", client.port)

            ports = self._registered.get(client.ip)
            if ports is None:
                self._registered[client.ip] = set()
            self._registered[client.ip].add(client.port)

        if inspect.iscoroutinefunction(self._callback):
            func = self.decorate_asgi
        else:
            func = self.decorate_wsgi

        return func(self._callback, err)

    @classmethod
    def decorate_wsgi(
        cls,
        callback: Callback_WSGI_t,
        err: ErrInfo
    ) -> Callback_WSGI_t:
        acceptables = getattr(callback, cls.ATTR, {})

        @may_occur(err.__class__)
        def _callback(self: WSGIEndpoint, *args) -> None:
            client = ClientInfo(*self.get_client_addr())
            ports = acceptables.get(client.ip)
            if ports is None:
                raise err
            if not(None in ports or client.port in ports):
                raise err

            callback(self, *args)

        _callback.__dict__ = callback.__dict__
        return _callback

    @classmethod
    def decorate_asgi(
        cls,
        callback: Callback_ASGI_t,
        err: ErrInfo
    ) -> Callback_ASGI_t:
        acceptables = getattr(callback, cls.ATTR, set())

        @may_occur(err.__class__)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            client = ClientInfo(*self.get_client_addr())
            ports = acceptables.get(client.ip)
            if ports is None:
                raise err
            if not(None in ports or client.port in ports):
                raise err

            await callback(self, *args)

        _callback.__dict__ = callback.__dict__
        return _callback


def restricts_client(
    *clients: ClientInfo,
    err: ErrInfo = DEFAULT_NOT_APPLICABLE_IP_ERROR
) -> CallbackDecorator_t:
    """Restrict IP addresses at callback.

    Args:
        *client_ips: IP addresses to be allowed to request
        err: Error information sent when request from IP not included
            specified IPs comes.

    Returns:
        Decorator to make callback to be set up to restrict IP addresses.

    Raises:
        ValueError: Raised if invalid IP address is detected

    Examples:
        ```python
        class MockEndpoint(WSGIEndpoint):

            # Restrict to allow only localhost to request
            # to this callback
            @restricts_client(ClientInfo("localhost"))
            def do_GET(self) -> None:
                # Only localhost can access to the callback.

                # Do something...
        ```
    """
    def wrapper(callback: Callback_t) -> Callback_t:
        config = RestrictedClientsConfig(callback)
        return config.set(*clients, err=err)

    return wrapper


class MultipleAuthSchemeError(Exception):
    """Raised if several authentication schemes of the 'Authorization'
    header are detected.
    """
    pass


class AuthSchemeConfig(ConfigBase):

    ATTR = _get_bamboo_attr("auth_scheme")
    HEADER_AUTHORIZATION = "Authorization"

    def __init__(self, callback: Callback_t) -> None:
        super().__init__()

        self._callback = callback

    def get(self) -> Optional[str]:
        return getattr(self._callback, self.ATTR, None)

    def set(self, scheme: str, err: ErrInfo) -> Callback_t:
        if hasattr(self._callback, self.ATTR):
            _scheme_registered = getattr(self._callback, self.ATTR)
            raise MultipleAuthSchemeError(
                "Authentication scheme has already been specified as "
                f"'{_scheme_registered}'. Do not specify multiple schemes."
            )

        if scheme not in AuthSchemes:
            raise ValueError(f"Specified scheme '{scheme}' is not supported.")

        setattr(self._callback, self.ATTR, scheme)

        if scheme == AuthSchemes.basic:
            if inspect.iscoroutinefunction(self._callback):
                func = self.decorate_asgi_basic
            else:
                func = self.decorate_wsgi_basic
        elif scheme == AuthSchemes.bearer:
            if inspect.iscoroutinefunction(self._callback):
                func = self.decorate_asgi_bearer
            else:
                func = self.decorate_wsgi_bearer

        return func(self._callback, err)

    @staticmethod
    def _validate_auth_header(value: str, scheme: str) -> Optional[str]:
        value = value.split(" ")
        if len(value) != 2:
            return None

        _scheme, credentials = value
        if _scheme != scheme:
            return None

        return credentials

    @classmethod
    def decorate_wsgi_basic(
        cls,
        callback: Callback_WSGI_t,
        err: ErrInfo
    ) -> Callback_WSGI_t:

        @may_occur(err.__class__)
        @has_header_of(cls.HEADER_AUTHORIZATION, err)
        def _callback(self: WSGIEndpoint, *args) -> None:
            val = self.get_header(cls.HEADER_AUTHORIZATION)
            credentials = cls._validate_auth_header(val, AuthSchemes.basic)
            if credentials is None:
                raise err

            credentials = decode2binary(credentials).decode().split(":")
            if len(credentials) != 2:
                raise err

            user_id, pw = credentials
            callback(self, user_id, pw, *args)

        _callback.__dict__ = callback.__dict__
        return _callback

    @classmethod
    def decorate_asgi_basic(
        cls,
        callback: Callback_ASGI_t,
        err: ErrInfo
    ) -> Callback_ASGI_t:

        @may_occur(err.__class__)
        @has_header_of(cls.HEADER_AUTHORIZATION, err)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            val = self.get_header(cls.HEADER_AUTHORIZATION)
            credentials = cls._validate_auth_header(val, AuthSchemes.basic)
            if credentials is None:
                raise err

            credentials = decode2binary(credentials).decode().split(":")
            if len(credentials) != 2:
                raise err

            user_id, pw = credentials
            await callback(self, user_id, pw, *args)

        _callback.__dict__ = callback.__dict__
        return _callback

    @classmethod
    def decorate_wsgi_bearer(
        cls,
        callback: Callback_WSGI_t,
        err: ErrInfo,
    ) -> Callback_WSGI_t:

        @may_occur(err.__class__)
        @has_header_of(cls.HEADER_AUTHORIZATION, err)
        def _callback(self: WSGIEndpoint, *args) -> None:
            val = self.get_header(cls.HEADER_AUTHORIZATION)
            token = cls._validate_auth_header(val, AuthSchemes.bearer)
            if token is None:
                raise err

            callback(self, token, *args)

        _callback.__dict__ = callback.__dict__
        return _callback

    @classmethod
    def decorate_asgi_bearer(
        cls,
        callback: Callback_ASGI_t,
        err: ErrInfo,
    ) -> Callback_ASGI_t:

        @may_occur(err.__class__)
        @has_header_of(cls.HEADER_AUTHORIZATION, err)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            val = self.get_header(cls.HEADER_AUTHORIZATION)
            token = cls._validate_auth_header(val, AuthSchemes.bearer)
            if token is None:
                raise err

            await callback(self, token, *args)

        _callback.__dict__ = callback.__dict__
        return _callback


def basic_auth(
    err: ErrInfo = DEFAULT_BASIC_AUTH_HEADER_NOT_FOUND_ERROR,
) -> CallbackDecorator_t:
    """Set callback up to require `Authorization` header in Basic
    authentication.

    Args:
        err: Error sent when `Authorization` header is not found, received
            scheme doesn't match, or extracting user ID and password from
            credentials failes.

    Returns:
        Decorator to make callback to be set  up to require
        the `Authorization` header.

    Examples:
        ```python
        class MockEndpoint(WSGIEndpoint):

            @basic_auth()
            def do_GET(self, user_id: str, password: str) -> None:
                # It is guaranteed that request headers include the
                # `Authorization` header at this point, and user_id and
                # password are the ones extracted from the header.

                # Authenticate with any function working on your system.
                authenticate(user_id, password)

                # Do something...
        ```
    """
    def wrapper(callback: Callback_t) -> Callback_t:
        config = AuthSchemeConfig(callback)
        return config.set(AuthSchemes.basic, err)

    return wrapper


def bearer_auth(
    err: ErrInfo = DEFAULT_BEARER_AUTH_HEADER_NOT_FOUND_ERROR,
) -> CallbackDecorator_t:
    """Set callback up to require `Authorization` header in token
    authentication for OAuth 2.0.

    Args:
        err : Error sent when `Authorization` header is not found, or
            when received scheme doesn't match.

    Returns:
        Decorator to make callback to be set  up to require
        the `Authorization` header.

    Examples:
        ```python
        class MockEndpoint(WSGIEndpoint):

            @bearer_auth()
            def do_GET(self, token: str) -> None:
                # It is guaranteed that request headers include the
                # `Authorization` header at this point, and token is
                # the one extracted from the header.

                # Authenticate with any function working on your system.
                authenticate(token)

                # Do something...
        ```
    """
    def wrapper(callback: Callback_t) -> Callback_t:
        config = AuthSchemeConfig(callback)
        return config.set(AuthSchemes.bearer, err)

    return wrapper
