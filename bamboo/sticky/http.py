from abc import ABCMeta, abstractmethod
import dataclasses
import functools
import inspect
import re
import typing as t

from . import (
    Callback_ASGI_t,
    Callback_WSGI_t,
    Callback_t,
    CallbackDecorator_t,
    DuplicatedInfoError,
    _get_bamboo_attr,
)
from ..api.base import ApiData, ApiValidationFailedError
from ..endpoint import (
    ASGIEndpointBase,
    ASGIHTTPEndpoint,
    HTTPMixIn,
    WSGIEndpoint,
    set_response_method,
)
from ..error import (
    DEFAULT_BASIC_AUTH_HEADER_NOT_FOUND_ERROR,
    DEFAULT_BEARER_AUTH_HEADER_NOT_FOUND_ERROR,
    DEFAULT_HEADER_NOT_FOUND_ERROR,
    DEFAULT_CORS_ERROR,
    DEFUALT_INCORRECT_DATA_FORMAT_ERROR,
    DEFAULT_NOT_APPLICABLE_IP_ERROR,
    ErrInfo,
)
from ..http import AuthSchemes, HTTPStatus
from ..util.convert import decode2binary
from ..util.ip import is_valid_ipv4


__all__ = [
    "SetCookieValue_t",
    "add_preflight",
    "allow_simple_access_control",
    "basic_auth",
    "bearer_auth",
    "data_format",
    "get_asgi_preflight",
    "get_wsgi_preflight",
    "has_header_of",
    "has_query_of",
    "may_occur",
    "restricts_client",
    "set_cache_control",
    "set_cookie",
]


class CallbackConfigBase(metaclass=ABCMeta):

    ATTR: str

    @abstractmethod
    def get(self) -> t.Any:
        pass

    @abstractmethod
    def set(self, *args, **kwargs) -> Callback_t:
        pass


class HTTPEndpointConfigBase(metaclass=ABCMeta):

    ATTR: str


    @abstractmethod
    def get(self) -> t.Any:
        pass

    @abstractmethod
    def set(self, *args, **kwargs) -> HTTPMixIn:
        pass


class HTTPErrorConfig(CallbackConfigBase):

    ATTR = _get_bamboo_attr("errors")

    def __init__(self, callback) -> None:
        if not hasattr(callback, self.ATTR):
            setattr(callback, self.ATTR, set())

        self._callback = callback
        self._registered: t.Set[ErrInfo] = getattr(callback, self.ATTR)

    def get(self) -> t.Tuple[t.Type[ErrInfo], ...]:
        return tuple(self._registered)

    def set(self, *errors: t.Type[ErrInfo]) -> Callback_t:
        for err in errors:
            self._registered.add(err)
        return self._callback


def may_occur(*errors: t.Type[ErrInfo]) -> CallbackDecorator_t:
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


@dataclasses.dataclass(eq=True, frozen=True)
class DataFormatInfo:
    """`dataclass` with information of data format at callbacks on `Endpoint`.

    Attributes:
        input (Optional[Type[ApiData]]): Input data format.
        output (Optional[Type[ApiData]]): Output data format.
        is_validate (bool): If input data is to be validate.
        err_validate (ErrInfo): Error information sent
            when validation failes.
    """
    input: t.Optional[t.Type[ApiData]] = None
    output: t.Optional[t.Type[ApiData]] = None
    is_validate: bool = True
    err_validate: ErrInfo = DEFUALT_INCORRECT_DATA_FORMAT_ERROR
    err_noheader: ErrInfo = DEFAULT_HEADER_NOT_FOUND_ERROR


class DataFormatConfig(CallbackConfigBase):

    ATTR = _get_bamboo_attr("data_format")

    def __init__(self, callback: Callback_t) -> None:
        super().__init__()

        self._callback = callback

    def get(self) -> t.Optional[DataFormatInfo]:
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

        @functools.wraps(callback)
        @may_occur(dataformat.err_validate.__class__)
        @has_header_of("Content-Type", dataformat.err_noheader, add_arg=False)
        def _callback(self: WSGIEndpoint, *args) -> None:
            body = self.body
            try:
                data = dataformat.input.__validate__(body, self.content_type)
            except ApiValidationFailedError:
                raise dataformat.err_validate
            callback(self, data, *args)

        return _callback

    @staticmethod
    def decorate_wsgi_no_input(
        callback: Callback_WSGI_t,
        dataformat: DataFormatInfo
    ) -> Callback_WSGI_t:

        @functools.wraps(callback)
        def _callback(self: WSGIEndpoint, *args) -> None:
            setattr(self, "body", b"")
            callback(self, *args)

        return _callback

    @staticmethod
    def decorate_asgi(
        callback: Callback_ASGI_t,
        dataformat: DataFormatInfo
    ) -> Callback_ASGI_t:

        @functools.wraps(callback)
        @may_occur(dataformat.err_validate.__class__)
        @has_header_of("Content-Type", dataformat.err_noheader, add_arg=False)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            body = await self.body
            try:
                data = dataformat.input.__validate__(body, self.content_type)
            except ApiValidationFailedError:
                raise dataformat.err_validate
            await callback(self, data, *args)

        return _callback

    @staticmethod
    def decorate_asgi_no_input(
        callback: Callback_ASGI_t,
        dataformat: DataFormatInfo
    ) -> Callback_ASGI_t:

        @functools.wraps(callback)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            # NOTE
            #   Reference awaitable_cached_property
            body_property = await self.__class__.body
            body_property._obj2val[self] = b""
            await callback(self, *args)

        return _callback


def data_format(
    input: t.Optional[t.Type[ApiData]] = None,
    output: t.Optional[t.Type[ApiData]] = None,
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


@dataclasses.dataclass(eq=True, frozen=True)
class RequiredHeaderInfo:
    """`dataclass` with information of header which should be included in
    response headers.

    Attributes:
        header: Name of header.
        err: Error information sent when the header is not included.
        add_arg: Whether the header is given as a callback's argument.
    """
    header: str
    err: t.Optional[ErrInfo]
    add_arg: bool


class RequiredHeaderConfig(CallbackConfigBase):

    ATTR = _get_bamboo_attr("required_headers")

    def __init__(self, callback: Callback_t) -> None:
        super().__init__()

        if not hasattr(callback, self.ATTR):
            setattr(callback, self.ATTR, set())

        self._callback = callback
        self._registered: t.Set[RequiredHeaderInfo] = getattr(callback, self.ATTR)

    def get(self) -> t.Tuple[RequiredHeaderInfo]:
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
        info: RequiredHeaderInfo,
    ) -> Callback_WSGI_t:

        @functools.wraps(callback)
        def _callback(self: WSGIEndpoint, *args) -> None:
            val = self.get_header(info.header)
            if val is None and info.err:
                raise info.err

            if info.add_arg:
                callback(self, val, *args)
            else:
                callback(self, *args)

        if info.err:
            _callback = may_occur(info.err.__class__)(_callback)
        return _callback

    @staticmethod
    def decorate_asgi(
        callback: Callback_ASGI_t,
        info: RequiredHeaderInfo,
    ) -> Callback_ASGI_t:

        @functools.wraps(callback)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            val = self.get_header(info.header)
            if val is None and info.err:
                raise info.err

            if info.add_arg:
                await callback(self, val, *args)
            else:
                await callback(self, *args)

        if info.err:
            _callback = may_occur(info.err.__class__)(_callback)
        return _callback


def has_header_of(
    header: str,
    err: t.Optional[ErrInfo] = None,
    add_arg: bool = True,
) -> CallbackDecorator_t:
    """Set callback up to receive given header from clients.

    If request headers don't include specified `header`, then response
    headers and body will be made based on `err` and sent.

    Args:
        header: Name of header.
        err: Error information sent when specified `header` is not found.
        add_arg: Whether the header is given as a callback's argument.

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
    info = RequiredHeaderInfo(header, err, add_arg)

    def wrapper(callback: Callback_t) -> Callback_t:
        config = RequiredHeaderConfig(callback)
        return config.set(info)

    return wrapper


@dataclasses.dataclass(eq=True, frozen=True)
class ClientInfo:

    ip: str
    port: t.Optional[int] = None


_RestrictedClient_t = t.Dict[str, t.Set[t.Optional[int]]]


class RestrictedClientsConfig(CallbackConfigBase):

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

        @functools.wraps(callback)
        @may_occur(err.__class__)
        def _callback(self: WSGIEndpoint, *args) -> None:
            client = ClientInfo(*self.get_client_addr())
            ports = acceptables.get(client.ip)
            if ports is None:
                raise err
            if not(None in ports or client.port in ports):
                raise err
            callback(self, *args)

        return _callback

    @classmethod
    def decorate_asgi(
        cls,
        callback: Callback_ASGI_t,
        err: ErrInfo
    ) -> Callback_ASGI_t:
        acceptables = getattr(callback, cls.ATTR, set())

        @functools.wraps(callback)
        @may_occur(err.__class__)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            client = ClientInfo(*self.get_client_addr())
            ports = acceptables.get(client.ip)
            if ports is None:
                raise err
            if not(None in ports or client.port in ports):
                raise err
            await callback(self, *args)

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


class AuthSchemeConfig(CallbackConfigBase):

    ATTR = _get_bamboo_attr("auth_scheme")
    HEADER_AUTHORIZATION = "Authorization"

    def __init__(self, callback: Callback_t) -> None:
        super().__init__()

        self._callback = callback

    def get(self) -> t.Optional[str]:
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
    def _validate_auth_header(value: str, scheme: str) -> t.Optional[str]:
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

        @functools.wraps(callback)
        @may_occur(err.__class__)
        @has_header_of(cls.HEADER_AUTHORIZATION, err, add_arg=False)
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

        return _callback

    @classmethod
    def decorate_asgi_basic(
        cls,
        callback: Callback_ASGI_t,
        err: ErrInfo
    ) -> Callback_ASGI_t:

        @functools.wraps(callback)
        @may_occur(err.__class__)
        @has_header_of(cls.HEADER_AUTHORIZATION, err, add_arg=False)
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

        return _callback

    @classmethod
    def decorate_wsgi_bearer(
        cls,
        callback: Callback_WSGI_t,
        err: ErrInfo,
    ) -> Callback_WSGI_t:

        @functools.wraps(callback)
        @may_occur(err.__class__)
        @has_header_of(cls.HEADER_AUTHORIZATION, err, add_arg=False)
        def _callback(self: WSGIEndpoint, *args) -> None:
            val = self.get_header(cls.HEADER_AUTHORIZATION)
            token = cls._validate_auth_header(val, AuthSchemes.bearer)
            if token is None:
                raise err
            callback(self, token, *args)

        return _callback

    @classmethod
    def decorate_asgi_bearer(
        cls,
        callback: Callback_ASGI_t,
        err: ErrInfo,
    ) -> Callback_ASGI_t:

        @functools.wraps(callback)
        @may_occur(err.__class__)
        @has_header_of(cls.HEADER_AUTHORIZATION, err, add_arg=False)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            val = self.get_header(cls.HEADER_AUTHORIZATION)
            token = cls._validate_auth_header(val, AuthSchemes.bearer)
            if token is None:
                raise err
            await callback(self, token, *args)

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


@dataclasses.dataclass(eq=True, frozen=True)
class RequiredQueryInfo:

    query: str
    err_empty: t.Optional[ErrInfo] = None
    err_not_unique: t.Optional[ErrInfo] = None
    add_arg: bool = True


class RequiredQueryConfig(CallbackConfigBase):

    ATTR = _get_bamboo_attr("required_queries")

    def __init__(self, callback: Callback_t) -> None:
        super().__init__()

        if not hasattr(callback, self.ATTR):
            setattr(callback, self.ATTR, set())

        self._callback = callback
        self._registered: t.Set[RequiredQueryConfig] = getattr(callback, self.ATTR)

    def get(self) -> t.Tuple[RequiredHeaderInfo]:
        return tuple(self._registered)

    def set(self, info: RequiredQueryInfo) -> Callback_t:
        self._registered.add(info)

        if inspect.iscoroutinefunction(self._callback):
            func = self.decorate_asgi
        else:
            func = self.decorate_wsgi
        return func(self._callback, info)

    @staticmethod
    def decorate_wsgi(
        callback: Callback_WSGI_t,
        info: RequiredQueryInfo,
    ) -> Callback_WSGI_t:

        @functools.wraps(callback)
        def _callback(self: WSGIEndpoint, *args) -> None:
            val = self.get_queries(info.query)
            len_val = len(val)

            if len_val == 0:
                if info.err_empty:
                    raise info.err_empty
                else:
                    val = None
            elif len_val == 1:
                val = val[0]
            else:
                if info.err_not_unique:
                    raise info.err_not_unique

            if info.add_arg:
                callback(self, val, *args)
            else:
                callback(self, *args)

        errs = []
        if info.err_empty:
            errs.append(info.err_empty.__class__)
        if info.err_not_unique:
            errs.append(info.err_not_unique.__class__)
        if len(errs):
            _callback = may_occur(*errs)(_callback)

        return _callback

    @staticmethod
    def decorate_asgi(
        callback: Callback_ASGI_t,
        info: RequiredQueryInfo,
    ) -> Callback_ASGI_t:

        @functools.wraps(callback)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            val = self.get_queries(info.query)
            len_val = len(val)

            if len_val == 0:
                if info.err_empty:
                    raise info.err_empty
                else:
                    val = None
            elif len_val == 1:
                val = val[0]
            else:
                if info.err_not_unique:
                    raise info.err_not_unique

            if info.add_arg:
                await callback(self, val, *args)
            else:
                await callback(self, *args)

        errs = []
        if info.err_empty:
            errs.append(info.err_empty.__class__)
        if info.err_not_unique:
            errs.append(info.err_not_unique.__class__)
        if len(errs):
            _callback = may_occur(*errs)(_callback)

        return _callback


def has_query_of(
    query: str,
    err_empty: t.Optional[ErrInfo] = None,
    err_not_unique: t.Optional[ErrInfo] = None,
    add_arg: bool = True,
) -> CallbackDecorator_t:
    """Set callback up to receive given query parameter from clients.
    """
    info = RequiredQueryInfo(query, err_empty, err_not_unique, add_arg)

    def wrapper(callback: Callback_t) -> Callback_t:
        config = RequiredQueryConfig(callback)
        return config.set(info)

    return wrapper


@dataclasses.dataclass(eq=True, frozen=True)
class SimpleAccessControlInfo:

    origins: t.Tuple[str] = ()
    allow_credentials: bool = False
    err_not_allowed: ErrInfo = DEFAULT_CORS_ERROR
    add_arg: bool = True


class SimpleAccessControlConfig(CallbackConfigBase):

    ATTR = _get_bamboo_attr("simple_access_control")

    def __init__(self, callback: Callback_t) -> None:
        super().__init__()

        self._callback = callback

    def get(self) -> t.Optional[SimpleAccessControlInfo]:
        return getattr(self._callback, self.ATTR, None)

    def set(self, info: SimpleAccessControlInfo) -> Callback_t:
        if hasattr(self._callback, self.ATTR):
            raise DuplicatedInfoError(
                "Decorating of multiple times is forbidden."
            )
        setattr(self._callback, self.ATTR, info)

        if inspect.iscoroutinefunction(self._callback):
            func = self.decorate_asgi
        else:
            func = self.decorate_wsgi
        return func(self._callback, info)

    @staticmethod
    def decorate_wsgi(
        callback: Callback_WSGI_t,
        info: SimpleAccessControlInfo,
    ) -> Callback_WSGI_t:
        origins = set(info.origins)

        @functools.wraps(callback)
        def _callback(self: WSGIEndpoint, *args) -> None:
            # Origin
            origin = self.get_header("Origin")
            if origin:
                if not len(origins):
                    self.add_header("Access-Control-Allow-Origin", "*")
                elif origin in origins:
                    self.add_header("Access-Control-Allow-Origin", origin)
                    self.add_header("Vary", "Origin")
                else:
                    raise info.err_not_allowed

            # Credentials
            if info.allow_credentials:
                self.add_header("Access-Control-Allow-Credentials", "true")

            if info.add_arg:
                callback(self, origin, *args)
            else:
                callback(self, *args)

        if info.err_not_allowed:
            _callback = may_occur(info.err_not_allowed.__class__)(_callback)
        return _callback

    @staticmethod
    def decorate_asgi(
        callback: Callback_ASGI_t,
        info: SimpleAccessControlInfo,
    ) -> Callback_ASGI_t:
        origins = set(info.origins)

        @functools.wraps(callback)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            # Origin
            origin = self.get_header("Origin")
            if origin:
                if not len(origins):
                    self.add_header("Access-Control-Allow-Origin", "*")
                elif origin in origins:
                    self.add_header("Access-Control-Allow-Origin", origin)
                    self.add_header("Vary", "Origin")
                else:
                    raise info.err_not_allowed

            # Credentials
            if info.allow_credentials:
                self.add_header("Access-Control-Allow-Credentials", "true")

            if info.add_arg:
                await callback(self, origin, *args)
            else:
                await callback(self, *args)

        if info.err_not_allowed:
            _callback = may_occur(info.err_not_allowed.__class__)(_callback)
        return _callback


def allow_simple_access_control(
    *origins: str,
    allow_credentials: bool = False,
    err_not_allowed: ErrInfo = DEFAULT_CORS_ERROR,
    add_arg: bool = True,
) -> CallbackDecorator_t:
    info = SimpleAccessControlInfo(
        origins,
        allow_credentials,
        err_not_allowed,
        add_arg,
    )

    def wrapper(callback: Callback_t) -> Callback_t:
        config = SimpleAccessControlConfig(callback)
        return config.set(info)

    return wrapper


# NOTE
#   Each values should be lowercases.

_CORS_SAFELISTED_REQUEST_HEADERS = {
    "accept",
    "accept-language",
    "content-language",
    "content-type",
}


def _handle_cors_preflight(
    allow_methods: t.Union[str, t.Iterable[str]],
    allow_origins: t.Iterable[str] = (),
    allow_headers: t.Iterable[str] = (),
    expose_headers: t.Iterable[str] = (),
    max_age: t.Optional[int] = None,
    allow_credentials: bool = False,
    err_not_allowed_origin: ErrInfo = DEFAULT_CORS_ERROR,
    err_not_allowed_method: ErrInfo = DEFAULT_CORS_ERROR,
) -> t.Callable[
    [
        t.Union[ASGIEndpointBase, WSGIEndpoint],
        t.Optional[str],
        t.Optional[str],
        t.Optional[str],
    ],
    None
]:
    if isinstance(allow_methods, str):
        allow_methods = {allow_methods}
    allow_origins = set(allow_origins)
    allow_headers = set([header.lower() for header in allow_headers])
    allow_headers.update(_CORS_SAFELISTED_REQUEST_HEADERS)
    expose_headers = ", ".join(expose_headers)
    if max_age:
        max_age = str(max_age)

    def handle(
        self: t.Union[ASGIHTTPEndpoint, WSGIEndpoint],
        origin: t.Optional[str],
        req_method: t.Optional[str],
        req_headers: t.Optional[str],
    ) -> None:
        if origin is None and req_method is None:
            self.send_only_status(HTTPStatus.BAD_REQUEST)

        # Allow Origin
        if not len(allow_origins):
            self.add_header("Access-Control-Allow-Origin", "*")
        else:
            if origin in allow_origins:
                self.add_header("Access-Control-Allow-Origin", origin)
                self.add_header("Vary", "Origin")
            else:
                raise err_not_allowed_origin

        # Allow Methods
        if req_method is None:
            raise err_not_allowed_method
        if req_method in allow_methods:
            methods = ", ".join(allow_methods)
            self.add_header("Access-Control-Allow-Methods", methods)
        else:
            raise err_not_allowed_method

        # Allow Headers
        if req_headers:
            accepted_headers = ", ".join([
                header for header in re.split(",|, ", req_headers)
                if header in allow_headers
            ])
            if accepted_headers:
                self.add_header("Access-Control-Allow-Headers", accepted_headers)

        # Expose Headers
        if expose_headers:
            self.add_header("Access-Control-Expose-Headers", expose_headers)

        # Max Age
        if max_age:
            self.add_header("Access-Control-Max-Age", max_age)

        # Allow Credentials
        if allow_credentials:
            self.add_header("Access-Control-Allow-Credentials", "true")

        self.send_only_status(HTTPStatus.NO_CONTENT)

    return handle


def get_wsgi_preflight(
    allow_methods: t.Union[str, t.Iterable[str]],
    allow_origins: t.Iterable[str] = (),
    allow_headers: t.Iterable[str] = (),
    expose_headers: t.Iterable[str] = (),
    max_age: t.Optional[int] = None,
    allow_credentials: bool = False,
    err_not_allowed_origin: ErrInfo = DEFAULT_CORS_ERROR,
    err_not_allowed_method: ErrInfo = DEFAULT_CORS_ERROR,
) -> Callback_WSGI_t:
    callback = _handle_cors_preflight(
        allow_methods,
        allow_origins=allow_origins,
        allow_headers=allow_headers,
        expose_headers=expose_headers,
        max_age=max_age,
        allow_credentials=allow_credentials,
        err_not_allowed_origin=err_not_allowed_origin,
        err_not_allowed_method=err_not_allowed_method,
    )

    @has_header_of("Access-Control-Request-Headers")
    @has_header_of("Access-Control-Request-Method")
    @has_header_of("Origin")
    def do_OPTIONS(
        self: WSGIEndpoint,
        origin: t.Optional[str],
        req_method: t.Optional[str],
        req_headers: t.Optional[str],
    ) -> None:
        callback(self, origin, req_method, req_headers)

    return do_OPTIONS


def get_asgi_preflight(
    allow_methods: t.Union[str, t.Iterable[str]],
    allow_origins: t.Iterable[str] = (),
    allow_headers: t.Iterable[str] = (),
    expose_headers: t.Iterable[str] = (),
    max_age: t.Optional[int] = None,
    allow_credentials: bool = False,
    err_not_allowed_origin: ErrInfo = DEFAULT_CORS_ERROR,
    err_not_allowed_method: ErrInfo = DEFAULT_CORS_ERROR,
) -> Callback_ASGI_t:
    callback = _handle_cors_preflight(
        allow_methods,
        allow_origins=allow_origins,
        allow_headers=allow_headers,
        expose_headers=expose_headers,
        max_age=max_age,
        allow_credentials=allow_credentials,
        err_not_allowed_origin=err_not_allowed_origin,
        err_not_allowed_method=err_not_allowed_method,
    )

    @has_header_of("Access-Control-Request-Headers")
    @has_header_of("Access-Control-Request-Method")
    @has_header_of("Origin")
    async def do_OPTIONS(
        self: t.Type[ASGIHTTPEndpoint],
        origin: t.Optional[str],
        req_method: t.Optional[str],
        req_headers: t.Optional[str],
    ) -> None:
        callback(self, origin, req_method, req_headers)

    return do_OPTIONS


@dataclasses.dataclass(eq=True, frozen=True)
class PreFlightInfo:

    allow_methods: t.Tuple[str]
    allow_origins: t.Tuple[str] = ()
    allow_headers: t.Tuple[str] = ()
    expose_headers: t.Tuple[str] = ()
    max_age: t.Optional[int] = None
    allow_credentials: bool = False
    err_not_allowed_origin: ErrInfo = DEFAULT_CORS_ERROR
    err_not_allowed_method: ErrInfo = DEFAULT_CORS_ERROR
    add_arg: bool = True


class PreFlightConfig(HTTPEndpointConfigBase):

    ATTR = _get_bamboo_attr("preflight")

    def __init__(self, endpoint: t.Type[HTTPMixIn]) -> None:
        super().__init__()

        self._endpoint = endpoint

    def get(self) -> t.Optional[PreFlightInfo]:
        return getattr(self._endpoint, self.ATTR, None)

    def set(self, info: PreFlightInfo) -> t.Type[HTTPMixIn]:
        if hasattr(self._endpoint, self.ATTR):
            raise DuplicatedInfoError(
                "Decorating of multiple times is forbidden."
            )
        setattr(self._endpoint, self.ATTR, info)
        args = (
            info.allow_methods,
            info.allow_origins,
            info.allow_headers,
            info.expose_headers,
            info.max_age,
            info.allow_credentials,
            info.err_not_allowed_origin,
            info.err_not_allowed_method,
        )

        # Set other methods
        for name, res_method in self._endpoint._res_methods.copy().items():
            res_method = allow_simple_access_control(
                *info.allow_origins,
                allow_credentials=info.allow_credentials,
                err_not_allowed=info.err_not_allowed_origin,
                add_arg=info.add_arg,
            )(res_method)
            set_response_method(self._endpoint, name, res_method)

        # Set do_OPTIONS
        if issubclass(self._endpoint, WSGIEndpoint):
            res_method = get_wsgi_preflight(*args)
        elif issubclass(self._endpoint, ASGIHTTPEndpoint):
            res_method = get_asgi_preflight(*args)
        else:
            raise ValueError(
                f"Class {self._endpoint.__name__} is not avalidable."
            )
        set_response_method(self._endpoint, "OPTIONS", res_method)

        return self._endpoint


def add_preflight(
    allow_methods: t.Iterable[str],
    allow_origins: t.Iterable[str] = (),
    allow_headers: t.Iterable[str] = (),
    expose_headers: t.Iterable[str] = (),
    max_age: t.Optional[int] = None,
    allow_credentials: bool = False,
    err_not_allowed_origin: ErrInfo = DEFAULT_CORS_ERROR,
    err_not_allowed_method: ErrInfo = DEFAULT_CORS_ERROR,
    add_arg: bool = True,
) -> t.Callable[[HTTPMixIn], HTTPMixIn]:
    info = PreFlightInfo(
        tuple(allow_methods),
        allow_origins=tuple(allow_origins),
        allow_headers=tuple(allow_headers),
        expose_headers=tuple(expose_headers),
        max_age=max_age,
        allow_credentials=allow_credentials,
        err_not_allowed_origin=err_not_allowed_origin,
        err_not_allowed_method=err_not_allowed_method,
        add_arg=add_arg,
    )

    def wrapper(endpoint: HTTPMixIn) -> HTTPMixIn:
        config = PreFlightConfig(endpoint)
        return config.set(info)

    return wrapper


@dataclasses.dataclass(eq=True, frozen=True)
class CacheControlInfo:

    public: bool = False
    private: bool = False
    no_cache: bool = False
    no_store: bool = False
    max_age: t.Optional[int] = None
    s_maxage: t.Optional[int] = None
    max_stale: t.Optional[int] = None
    min_fresh: t.Optional[int] = None
    stale_while_revalidate: t.Optional[int] = None
    stale_if_error: t.Optional[int] = None
    must_revalidate: bool = False
    proxy_revalidate: bool = False
    immutable: bool = False
    no_transform: bool = False
    only_if_cached: bool = False


def _get_cache_control_value(info: CacheControlInfo) -> str:
    vals = []

    if info.public:
        vals.append("public")
    if info.private:
        vals.append("private")
    if info.no_cache:
        vals.append("no-cache")
    if info.no_store:
        vals.append("no-store")
    if info.max_age is not None:
        vals.append(f"max-age={info.max_age}")
    if info.s_maxage is not None:
        vals.append(f"s-maxage={info.s_maxage}")
    if info.max_stale is not None:
        vals.append(f"max-stale={info.max_stale}")
    if info.min_fresh is not None:
        vals.append(f"min-fresh={info.min_fresh}")
    if info.stale_while_revalidate is not None:
        vals.append(f"stale-while-revalidate={info.stale_while_revalidate}")
    if info.stale_if_error is not None:
        vals.append(f"stale-if-error={info.stale_if_error}")
    if info.must_revalidate:
        vals.append("must-revalidate")
    if info.proxy_revalidate:
        vals.append("proxy-revalidate")
    if info.immutable:
        vals.append("immutable")
    if info.no_transform:
        vals.append("no-transform")
    if info.only_if_cached:
        vals.append("only-if-cached")

    return ", ".join(vals)


class CacheControlConfig(CallbackConfigBase):

    ATTR = _get_bamboo_attr("cache_control")

    def __init__(self, callback: Callback_t) -> None:
        super().__init__()

        self._callback = callback

    def get(self) -> t.Optional[CacheControlInfo]:
        return getattr(self._callback, self.ATTR, None)

    def set(self, info: CacheControlInfo) -> Callback_t:
        if hasattr(self._callback, self.ATTR):
            raise DuplicatedInfoError(
                "Decorating of multiple times is forbidden."
            )
        setattr(self._callback, self.ATTR, info)

        if inspect.iscoroutinefunction(self._callback):
            func = self.decorate_asgi
        else:
            func = self.decorate_wsgi
        return func(self._callback, info)

    @staticmethod
    def decorate_wsgi(
        callback: Callback_WSGI_t,
        info: CacheControlInfo,
    ) -> Callback_WSGI_t:
        val = _get_cache_control_value(info)

        @functools.wraps(callback)
        def _callback(self: WSGIEndpoint, *args) -> None:
            self.add_header("Cache-Control", val)
            callback(self, *args)

        return _callback

    @staticmethod
    def decorate_asgi(
        callback: Callback_ASGI_t,
        info: CacheControlInfo,
    ) -> Callback_ASGI_t:
        val = _get_cache_control_value(info)

        @functools.wraps(callback)
        async def _callback(self: ASGIHTTPEndpoint, *args) -> None:
            self.add_header("Cache-Control", val)
            await callback(self, *args)

        return _callback


def set_cache_control(
    public: bool = False,
    private: bool = False,
    no_cache: bool = False,
    no_store: bool = False,
    max_age: t.Optional[int] = None,
    s_maxage: t.Optional[int] = None,
    max_stale: t.Optional[int] = None,
    min_fresh: t.Optional[int] = None,
    stale_while_revalidate: t.Optional[int] = None,
    stale_if_error: t.Optional[int] = None,
    must_revalidate: bool = False,
    proxy_revalidate: bool = False,
    immutable: bool = False,
    no_transform: bool = False,
    only_if_cached: bool = False,
) -> CallbackDecorator_t:
    info = CacheControlInfo(
        public=public,
        private=private,
        no_cache=no_cache,
        no_store=no_store,
        max_age=max_age,
        s_maxage=s_maxage,
        max_stale=max_stale,
        min_fresh=min_fresh,
        stale_while_revalidate=stale_while_revalidate,
        stale_if_error=stale_if_error,
        must_revalidate=must_revalidate,
        proxy_revalidate=proxy_revalidate,
        immutable=immutable,
        no_transform=no_transform,
        only_if_cached=only_if_cached,
    )

    def wrapper(callback: Callback_t) -> Callback_t:
        config = CacheControlConfig(callback)
        return config.set(info)

    return wrapper


SetCookieValue_t = t.Callable[
    [t.Union[ASGIHTTPEndpoint, WSGIEndpoint], str],
    None
]


def _handle_cookie(
    cookie_name: str,
    expires: t.Optional[str] = None,
    max_age: t.Optional[int] = None,
    domain: t.Optional[str] = None,
    path: t.Optional[str] = None,
    secure: bool = True,
    http_only: bool = True,
    samesite: t.Optional[str] = None,
) -> SetCookieValue_t:
    directives = []
    if expires is not None:
        directives.append(f"Expires={expires}")
    if max_age is not None:
        directives.append(f"Max-Age={max_age}")
    if domain is not None:
        directives.append(f"Domain={domain}")
    if path is not None:
        directives.append(f"Path={path}")
    if secure:
        directives.append("Secure")
    if http_only:
        directives.append("HttpOnly")
    if samesite is not None:
        directives.append(f"SameSite={samesite}")

    directives = "; ".join(directives)
    form = "{name}={value}; {others}"

    def set_cookie_value(
        self: t.Union[ASGIHTTPEndpoint, WSGIEndpoint],
        value: str,
    ) -> None:
        header_val = form.format(
            name=cookie_name,
            value=value,
            others=directives,
        )
        self.add_header("Set-Cookie", header_val)

    return set_cookie_value


@dataclasses.dataclass(eq=True, frozen=True)
class CookieInfo:

    cookie_name: str
    expires: t.Optional[str] = None
    max_age: t.Optional[int] = None
    domain: t.Optional[str] = None
    path: t.Optional[str] = None
    secure: bool = True
    http_only: bool = True
    samesite: t.Optional[str] = None


class CookieConfig(CallbackConfigBase):

    ATTR = _get_bamboo_attr("cookie")

    def __init__(self, callback: Callback_t) -> None:
        super().__init__()

        self._callback = callback

    def get(self) -> t.Optional[CookieInfo]:
        return getattr(self._callback, self.ATTR, None)

    def set(self, info: CookieInfo) -> Callback_t:
        if hasattr(self._callback, self.ATTR):
            raise DuplicatedInfoError(
                "Decorating of multiple times is forbidden."
            )
        setattr(self._callback, self.ATTR, info)

        if inspect.iscoroutinefunction(self._callback):
            func = self.decorate_asgi
        else:
            func = self.decorate_wsgi
        return func(self._callback, info)

    def decorate_wsgi(
        self,
        callback: Callback_WSGI_t,
        info: CookieInfo,
    ) -> Callback_WSGI_t:
        set_cookie_callback = _handle_cookie(
            info.cookie_name,
            expires=info.expires,
            max_age=info.max_age,
            domain=info.domain,
            path=info.path,
            secure=info.secure,
            http_only=info.http_only,
            samesite=info.samesite,
        )

        @functools.wraps(callback)
        def _callback(self: WSGIEndpoint, *args) -> None:
            callback(self, set_cookie_callback, *args)

        return _callback

    def decorate_asgi(
        self,
        callback: Callback_ASGI_t,
        info: CookieInfo,
    ) -> Callback_WSGI_t:
        set_cookie_callback = _handle_cookie(
            info.cookie_name,
            expires=info.expires,
            max_age=info.max_age,
            domain=info.domain,
            path=info.path,
            secure=info.secure,
            http_only=info.http_only,
            samesite=info.samesite,
        )

        @functools.wraps(callback)
        async def _callback(self: ASGIEndpointBase, *args) -> None:
            await callback(self, set_cookie_callback, *args)

        return _callback


def set_cookie(
    cookie_name: str,
    expires: t.Optional[str] = None,
    max_age: t.Optional[int] = None,
    domain: t.Optional[str] = None,
    path: t.Optional[str] = None,
    secure: bool = True,
    http_only: bool = True,
    samesite: t.Optional[str] = None,
) -> CallbackDecorator_t:
    info = CookieInfo(
        cookie_name,
        expires=expires,
        max_age=max_age,
        domain=domain,
        path=path,
        secure=secure,
        http_only=http_only,
        samesite=samesite,
    )

    def wrapper(callback: Callback_t) -> Callback_t:
        config = CookieConfig(callback)
        return config.set(info)

    return wrapper
