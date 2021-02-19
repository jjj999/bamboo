
from __future__ import annotations
from dataclasses import dataclass
import inspect
import json
from typing import (
    Any, Callable, Dict, List, Optional, Tuple, Type,
)
from urllib.parse import parse_qs

from bamboo.api import ApiData, ValidationFailedError
from bamboo.base import (
    HTTPMethods, HTTPStatus, MediaTypes, ContentType,
    DEFAULT_CONTENT_TYPE_PLAIN,
)
from bamboo.error import (
    DEFAULT_HEADER_NOT_FOUND_ERROR, DEFAULT_NOT_APPLICABLE_IP_ERROR,
    DEFUALT_INCORRECT_DATA_FORMAT_ERROR, ErrInfoBase,
)
from bamboo.util.deco import cached_property
from bamboo.util.ip import is_valid_ipv4


class StatusCodeAlreadySetError(Exception):
    """Raised if response status code has already been set."""
    pass


class Endpoint:
    """Base class of Endpoint to define logic to requests.
    
    Attributes
    ----------
    response_methods : Tuple[str]
        Callbacks defined the class
    """
    
    response_methods: Tuple[str]
    
    @classmethod
    def _get_response_method_names(cls) -> Tuple[str]:
        """Retrieve names of response methods defined on the class.

        Returns
        -------
        Tuple[str]
            Names of response methods.
        """
        result = []
        for name, _ in inspect.getmembers(cls):
            if len(name) < 3:
                continue
            if name[:3] == "do_" and name[3:] in HTTPMethods:
                result.append(name[3:])
        return tuple(result)
    
    def __init_subclass__(cls) -> None:
        cls.response_methods = cls._get_response_method_names()
        
    def __init__(self, 
                 environ: Dict[str, Any], 
                 flexible_locs: Tuple[str, ...],
                 *parcel
                 ) -> None:
        self._environ = environ
        self._flexible_locs = flexible_locs
        self._req_body = None
        self._status: Optional[HTTPStatus] = None
        self._headers: List[Tuple[str, str]] = []
        self._res_body: bytes = b""

        self.setup(*parcel)
        
    @classmethod
    def _get_response_method(cls, method: str) -> Optional[Callback_t]:
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
        
    def _recv_body_secure(self) -> bytes:
        """Receive request body securely.

        Returns
        -------
        bytes
            Request body
        """
        # TODO
        #   Take measures against DoS attack.
        body = self._environ.get("wsgi.input").read(self.content_length)
        return body
        
    def setup(self, *parcel) -> None:
        pass
    
    @property
    def flexible_locs(self) -> Tuple[str, ...]:
        return self._flexible_locs
    
    @property
    def client_ip(self) -> str:
        return self._environ.get("REMOTE_ADDR")
        
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
    
    @cached_property
    def content_type(self) -> ContentType:
        raw = self._environ.get("CONTENT_TYPE")
        return ContentType.parse(raw)
    
    @property
    def content_length(self) -> int:
        length = self._environ.get("CONTENT_LENGTH")
        if length:
            return int(length)
        return 0
    
    @property
    def path(self) -> str:
        return self._environ.get("PATH_INFO")

    @property
    def request_method(self) -> str:
        return self._environ.get("REQUEST_METHOD").upper()
    
    @property
    def query(self) -> Dict[str, str]:
        return parse_qs(self._environ.get("QUERY_STRING"))
    
    @property
    def body(self) -> bytes:
        if self._req_body is None:
            self._req_body = self._recv_body_secure()
        return self._req_body
    
    def add_header(self, name: str, value: str, 
                   **params: Optional[str]) -> None:
        """Add response header with MIME parameters.

        Parameters
        ----------
        name : str
            Field name of the header
        value : str
            Value of the field
        **params : Optional[str]
            MIME parameters added to the field
        """
        params = [f'; {header}={val}' for header, val in params.items()]
        params = "".join(params)
        self._headers.append((name, value + params))
    
    def add_headers(self, **headers: str) -> None:
        """Add response headers at once.

        Parameters
        ----------
        **headers : str
            Header's info whose header is the field name.
            
        Notes
        -----
        This method would be used shortcut to register multiple 
        headers. If it requires adding MIME parameters, developers
        can use the 'add_header' method.
        """
        for name, val in headers.items():
            self.add_header(name, val)
    
    def _check_status_already_set(self) -> None:
        """Check if response status code already exists.

        Raises
        ------
        StatusCodeAlreadySetError
            Raised if response status code has already been set.
        """
        if self._res_body:
            raise StatusCodeAlreadySetError(
                "Response status code has already been set.")
        
    def send_only_status(self, status: HTTPStatus = HTTPStatus.OK) -> None:
        """Set specified status code to one of response.
        
        This method can be used if a callback doesn't need to send response 
        body. 

        Parameters
        ----------
        status : HTTPStatus, optional
            HTTP status of the response, by default `HTTPStatus.OK`
        """
        self._check_status_already_set()
        
        self._status = status
    
    def send_body(self, body: bytes, 
                  content_type: ContentType = DEFAULT_CONTENT_TYPE_PLAIN,
                  status: HTTPStatus = HTTPStatus.OK) -> None:
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
            
        Raisess
        ------
        StatusCodeAlreadySetError
            Raised if response status code has already been set.
        """
        self._check_status_already_set()

        self._status = status
        self._res_body = body
        
        # Content-Type's parameters
        params = {}
        if content_type.charset:
            params["charset"] = content_type.charset
        if content_type.boundary:
            params["boundary"] = content_type.boundary    
    
        self.add_header("Content-Type", content_type.media_type, **params)
    
    def send_json(self, body: Dict[str, Any], 
                  status: HTTPStatus = HTTPStatus.OK,
                  encoding: str = "UTF-8") -> None:
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
        self._check_status_already_set()
        
        body = json.dumps(body).encode(encoding=encoding)
        content_type = ContentType(media_type=MediaTypes.json, charset=encoding)
        self.send_body(body, content_type=content_type, status=status)
    
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
        self._check_status_already_set()

        self._status = err.http_status
        self._res_body = err.get_body()
        
        for name, val in err.get_headers():
            self.add_header(name, val)
        
        if len(self._res_body):
            self.add_header("Content-Type", err._content_type_,
                            **err._content_type_args_)


# Signature of the callback of response method on sub classes of 
# the Endpoint class.
Callback_t = Callable[[Endpoint, Tuple[Any, ...]], None]
CallbackDecorator_t = Callable[[Callback_t], Callback_t]

def _get_bamboo_attr(attr: str) -> str:
    return f"__bamboo_{attr}__"


# Error Information ----------------------------------------------------------

ATTR_ERRORS = _get_bamboo_attr("errors")


def get_errors_info(callback: Callback_t) -> List[Type[ErrInfoBase]]:
    """Retrieve errors may occur at specified `callback`.

    Parameters
    ----------
    callback : Callback_t
        Response method implemented on `Endpoint`

    Returns
    -------
    List[Type[ErrInfoBase]]
        `list` of error classes may occur
    """
    if hasattr(callback, ATTR_ERRORS):
        return getattr(callback, ATTR_ERRORS)
    return []


def may_occur(*errors: Type[ErrInfoBase]) -> CallbackDecorator_t:
    """Register error classes to callback on `Endpoint`.
    
    Parameters
    ----------
    *errors : Type[ErrInfoBase]
        Error classes which may occuur

    Returns
    -------
    CallbackDecorator_t
        Decorator to register error classes to callback
        
    Examples
    --------
    ```
    class MockErrInfo(ErrInfo):
        http_status = HTTPStatus.INTERNAL_SERVER_ERROR
        
        @classmethod
        def get_body(cls) -> bytes:
            return b"Intrernal server error occured"
            
    class MockEndpoint(Endpoint):
        
        @may_occur(MockErrInfo)
        def do_GET(self) -> None:
            # Do something...
            
            # It is possible to send error response.
            if is_some_flag():
                self.send_err(MockErrInfo)

            self.send_body(status=HTTPStatus.OK)
    ```
    """
    def attach_err_info(callback: Callback_t) -> Callback_t:
        if not hasattr(callback, ATTR_ERRORS):
            setattr(callback, ATTR_ERRORS, set())
        
        registered = getattr(callback, ATTR_ERRORS)
        for err in errors:
            registered.add(err)
            
        return callback
    return attach_err_info

# ----------------------------------------------------------------------------

# Data Format   --------------------------------------------------------------

ATTR_DATA_FORMAT = _get_bamboo_attr("data_format")


@dataclass
class DataFormatInfo:
    """`dataclass` with information of data format at callbacks on `Endpoint`.
    
    Attributes
    ----------
    input : Optional[Type[ApiData]]
        Input data format, by default `None`
    output : Optional[Type[ApiData]]
        Output data format, by default `None`
    is_validate : bool
        If input data is to be validate, by default `True`
    err_validate : ErrInfoBase
        Error information sent when validation failes, 
        by default `DEFUALT_INCORRECT_DATA_FORMAT_ERROR`
    """
    input: Optional[Type[ApiData]] = None
    output: Optional[Type[ApiData]] = None
    is_validate: bool = True
    err_validate: ErrInfoBase = DEFUALT_INCORRECT_DATA_FORMAT_ERROR
    
    
def get_data_format_info(callback: Callback_t) -> Optional[DataFormatInfo]:
    """Retrieve information of data format at `callback` on `Endpoint`.

    Parameters
    ----------
    callback : Callback_t
        Response method implemented on `Endpoint`

    Returns
    -------
    Optional[DataFormatInfo]
        Information of data format at the `callback`. If the `callback` is 
        not decorated by `data_format` decorator, then returns `None`.
    """
    if hasattr(callback, ATTR_DATA_FORMAT):
        info = getattr(callback, ATTR_DATA_FORMAT)
        return DataFormatInfo(**info)
    return None
    

def data_format(input: Optional[Type[ApiData]] = None, 
                output: Optional[Type[ApiData]] = None,
                is_validate: bool = True,
                err_validate: ErrInfoBase = 
                DEFUALT_INCORRECT_DATA_FORMAT_ERROR) -> CallbackDecorator_t:
    """Set data format of input/output data as API to `callback` on 
    `Endpoint`.
    
    This decorator can be used to add attributes of data format information 
    to a `callback`, and execute validation if input raw data has expected 
    format defined on `input` argument. 
    
    To represent no data inputs/outputs, specify `input`/`output` arguments 
    as `None`s. If `input` is `None`, then any data received from client will 
    not be read. If `is_validate` is `False`, then validation will not be 
    executed.
    
    To retrieve data format information, use `get_data_format_info` function.

    Parameters
    ----------
    input : Optional[Type[ApiData]]
        Input data format, by default `None`
    output : Optional[Type[ApiData]]
        Output data format, by default `None`
    is_validate : bool, optional
        If input data is to be validated, by default `True`
    err_validate : ErrInfoBase
        Error information sent when validation failes, 
        by default `DEFUALT_INCORRECT_DATA_FORMAT_ERROR`

    Returns
    -------
    CallbackDecorator_t
        Decorator to add attributes of data format information to callback
        
    Examples
    --------
    ```
    class UserData(JsonApiData):
        name: str
        email: str
        age: int
    
    class MockEndpoint(Endpoint):
    
        @data_format(input=UserData, output=None)
        def do_GET(self, rec_body: UserData) -> None:
            user_name = rec_body.name
            # Do something...
    ```
    """
    _format = {"input": input, "output": output, 
               "err_validate": err_validate, "is_validate": is_validate}
    
    if is_validate and input:
        def input_decoded(
            callback: Callable[[Endpoint, ApiData, Tuple[Any, ...]], None]
            ) -> Callback_t:
            
            @may_occur(err_validate.__class__)
            def _callback(self: Endpoint, *args) -> None:
                body = self.body
                try:
                    data = input(body, self.content_type)
                except ValidationFailedError:
                    self.send_err(err_validate)
                    return
                
                callback(self, data, *args)
                
            _callback.__dict__ = callback.__dict__
            setattr(callback, ATTR_DATA_FORMAT, _format)
                
            return _callback
        return input_decoded
    else:
        def input_decoded(
            callback: Callable[[Endpoint, Tuple[Any, ...]], None]
            ) -> Callback_t:
            setattr(callback, ATTR_DATA_FORMAT, _format)
            
            # NOTE
            #   If input is None, then any response body would be received.
            if input is None:
                def _callback(self: Endpoint, *args) -> None:
                    self._req_body = b""
                    callback(self, *args)
                _callback.__dict__ = callback.__dict__
                return _callback
            
            return callback
        return input_decoded
    
# ----------------------------------------------------------------------------

# Required Headers  ----------------------------------------------------------

ATTR_HEADERS_REQUIRED = _get_bamboo_attr("headers_required")


@dataclass
class RequiredHeaderInfo:
    """`dataclass` with information of header which should be included in 
    response headers.
    
    Attributes
    ----------
    header : str
        Name of header
    err : ErrInfoBase
        Error information sent when the header is not included,
        by default `DEFAULT_HEADER_NOT_FOUND_ERROR`
    """
    header: str
    err: ErrInfoBase = DEFAULT_HEADER_NOT_FOUND_ERROR
    
    
def get_required_header_info(callback: Callback_t
                             ) -> List[RequiredHeaderInfo]:
    """Retrieve information of headers which should be included in 
    response headers.

    Parameters
    ----------
    callback : Callback_t
        Response method implemented on `Endpoint`

    Returns
    -------
    List[RequiredHeaderInfo]
        `list` of information of required headers
    """
    if hasattr(callback, ATTR_HEADERS_REQUIRED):
        arr_info = getattr(callback, ATTR_HEADERS_REQUIRED)
        return [RequiredHeaderInfo(*info) for info in arr_info]
    return []


def has_header_of(header: str, 
                  err: ErrInfoBase = DEFAULT_HEADER_NOT_FOUND_ERROR
                  ) -> CallbackDecorator_t:
    """Set callback up to receive given header from clients.

    If request headers don't include specified `header`, then response 
    headers and body will be made based on `err` and sent.

    Parameters
    ----------
    header : str
        Name of header
    err : ErrInfoBase, optional
        Error information sent when specified `header` is not found of request 
        headers, by default `DEFAULT_HEADER_NOT_FOUND_ERROR`

    Returns
    -------
    CallbackDecorator_t
        Decorator to make callback to be set up to receive the header
        
    Examples
    --------
    ```
    class BasicAuthHeaderNotFoundErrInfo(ErrInfoBase):
        http_status = HTTPStatus.UNAUTHORIZED
        
        @classmethod
        def get_headers(cls) -> List[Tuple[str, str]]:
            return [("WWW-Authenticate", 'Basic realm="SECRET AREA"')]
            
    class MockEndpoint(Endpoint):
    
        @has_header_of("Authorization", BasicAuthHeaderNotFoundErrInfo)
        def do_GET(self) -> None:
            # It is guaranteed that request headers include the 
            # `Authorization` header at this point.
            header_auth = self.get_header("Authorization")
            
            # Do something...
    ```
    """
    def header_checker(callback: Callback_t) -> Callback_t:
        
        @may_occur(err.__class__)
        def _callback(self: Endpoint, *args) -> None:
            val = self.get_header(header)
            if val is None:
                self.send_err(err)
                return
            callback(self, *args)
        
        _callback.__dict__ = callback.__dict__
        if not hasattr(_callback, ATTR_HEADERS_REQUIRED):
            setattr(_callback, ATTR_HEADERS_REQUIRED, set())
        
        headers_required = getattr(_callback, ATTR_HEADERS_REQUIRED)
        headers_required.add((header, err))
        return _callback
    return header_checker

# ----------------------------------------------------------------------------

# IP restriction    ----------------------------------------------------------

ATTR_CLIENT_RESTRICTED = _get_bamboo_attr("client_restricted")


def get_restricted_ip_info(callback: Callback_t) -> List[str]:
    """Retrieve IP addresses restricted at specified `callback`.

    Parameters
    ----------
    callback : Callback_t
        Response method implemented on `Endpoint`

    Returns
    -------
    List[str]
        `list` of restricted IP addresses
    """
    if hasattr(callback, ATTR_CLIENT_RESTRICTED):
        return getattr(callback, ATTR_CLIENT_RESTRICTED)
    return []


def restricts_client(*client_ips: str, 
                     err: ErrInfoBase = DEFAULT_NOT_APPLICABLE_IP_ERROR
                     ) -> CallbackDecorator_t:
    """Restrict IP addresses at callback.

    Parameters
    ----------
    *client_ips : str
        IP addresses to be allowed to request
    err : ErrInfoBase, optional
        Error information sent when request from IP not included specified IPs
         comes, by default `DEFAULT_NOT_APPLICABLE_IP_ERROR`

    Returns
    -------
    CallbackDecorator_t
        Decorator to make callback to be set up to restrict IP addresses
        
    Raises
    ------
    ValueError
        Raised if invalid IP address is detected
        
    Examples
    --------
    ```
    class MockEndpoint(Endpoint):
        
        # Restrict to allow only localhost to request 
        # to this callback
        @restricts_client("localhost")
        def do_GET(self) -> None:
            # Only localhost can access to the callback.
        
            # Do something...
    ```
    """
    for ip in client_ips:
        if not is_valid_ipv4(ip):
            raise ValueError(f"{ip} is invalid IP address.")
    
    allowed_ips = set(client_ips)
    # Convert localhost to the address
    if "localhost" in allowed_ips:
        allowed_ips.remove("localhost")
        allowed_ips.add("127.0.0.1")
    
    def register_restrictions(callback: Callback_t) -> Callback_t:
            
        @may_occur(err.__class__)
        def _callback(self: Endpoint, *args) -> None:
            if self.client_ip not in allowed_ips:
                self.send_err(err)
                return
            callback(self, *args)
            
        _callback.__dict__ = callback.__dict__
        if not hasattr(callback, ATTR_CLIENT_RESTRICTED):
            setattr(callback, ATTR_CLIENT_RESTRICTED, set())
            
        restrictions = getattr(callback, ATTR_CLIENT_RESTRICTED)
        restrictions.update(*allowed_ips)
            
        return _callback
    return register_restrictions

# ----------------------------------------------------------------------------
