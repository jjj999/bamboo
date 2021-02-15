
from __future__ import annotations
from dataclasses import dataclass
import inspect
import json
from typing import (
    Any, Callable, Dict, List, Optional, Tuple, Type,
)
from urllib.parse import parse_qs
from wsgiref.headers import Headers

from bamboo.api import ApiData
from bamboo.base import HTTPMethods, HTTPStatus
from bamboo.error import (
    DEFAULT_HEADER_NOT_FOUND_ERROR, DEFAULT_NOT_APPLICABLE_IP_ERROR,
    DEFUALT_INCORRECT_DATA_FORMAT_ERROR, ErrInfoBase,
)


class BodyAlreadySetError(Exception):
    """Raised if response body has already been set."""
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
        
    def __init__(self, environ: Dict[str, Any], *parcel) -> None:
        self._environ = environ
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
    
    @property
    def content_type(self) -> str:
        return self._environ.get("CONTENT_TYPE")
    
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
        params = [f'; {key}="{val}"' for key, val in params.items()]
        params = "".join(params)
        self._headers.append((name, value + params))
    
    def add_headers(self, **headers: str) -> None:
        """Add response headers at once.

        Parameters
        ----------
        **headers : str
            Header's info whose key is the field name.
            
        Notes
        -----
        This method would be used shortcut to register multiple 
        headers. If it requires adding MIME parameters, developers
        can use the 'add_header' method.
        """
        for name, val in headers.items():
            self.add_header(name, val)
    
    def _check_body_already_set(self) -> None:
        """Check if response body already exists.

        Raises
        ------
        BodyAlreadySetError
            Raised if response body has already been set.
        """
        if self._res_body:
            raise BodyAlreadySetError("Response body has already been set.")
    
    def send_body(self, body: bytes = b"", 
                  status: HTTPStatus = HTTPStatus.OK) -> None:
        """Set given binary to the response body.

        Parameters
        ----------
        body : bytes, optional
            Binary to be set to the response body, by default b""
        status : HTTPStatus, optional
            HTTP status of the response, by default HTTPStatus.OK
            
        Raises
        ------
        BodyAlreadySetError
            Raised if response body has already been set.
        """
        self._check_body_already_set()

        self._status = status
        self._res_body = body
    
    def send_json(self, body: Dict[str, Any], 
                  status: HTTPStatus = HTTPStatus.OK,
                  encoding: str = "utf-8") -> None:
        """Set given json data to the response body.

        Parameters
        ----------
        body : Dict[str, Any]
            Json data to be set to the response body
        status : HTTPStatus, optional
            HTTP status of the response, by default HTTPStatus.OK
        encoding : str, optional
            Encoding of the Json data, by default "utf-8"
            
        Raises
        ------
        BodyAlreadySetError
            Raised if response body has already been set.
        """
        self._check_body_already_set()
        
        self._status = status
        self._res_body = json.dumps(body).encode(encoding=encoding)
    
    def send_err(self, err: Type[ErrInfoBase]) -> None:
        """Set error to the response body.

        Parameters
        ----------
        err : Type[ErrInfoBase]
            Sub class of the ErrInfoBase error information is defined on
            
        Raises
        ------
        BodyAlreadySetError
            Raised if response body has already been set.
        """
        self._check_body_already_set()

        self._status = err.http_status
        self._res_body = err.get_body()


# Signature of the callback of response method on sub classes of 
# the Endpoint class.
Callback_t = Callable[[Endpoint, Tuple[Any, ...]], None]


def _get_bamboo_attr(attr: str) -> str:
    return f"__bamboo_{attr}__"


# Data Format   --------------------------------------------------------------

ATTR_DATA_FORMAT = _get_bamboo_attr("data_format")


@dataclass
class DataFormatInfo:
    
    input: Optional[Type[ApiData]] = None
    output: Optional[Type[ApiData]] = None
    is_attach: bool = True
    decode_err: Type[ErrInfoBase] = DEFUALT_INCORRECT_DATA_FORMAT_ERROR
    
    
def get_data_format_info(callback: Callback_t) -> Optional[DataFormatInfo]:
    if hasattr(callback, ATTR_DATA_FORMAT):
        info = getattr(callback, ATTR_DATA_FORMAT)
        return DataFormatInfo(**info)
    return None
    

def data_format(input: Optional[Type[ApiData]] = None, 
                output: Optional[Type[ApiData]] = None,
                is_attach: bool = True,
                attach_err: Type[ErrInfoBase] = 
                DEFUALT_INCORRECT_DATA_FORMAT_ERROR) -> Callback_t:
    
    _format = {"input": input, "output": output, 
               "attach_err": attach_err, "is_attach": is_attach}
    
    if is_attach and input:
        def input_decoded(
            callback: Callable[[Endpoint, ApiData, Tuple[Any, ...]], None]
            ) -> Callback_t:
            
            def _callback(self: Endpoint, *args) -> None:
                body = self.body
                try:
                    data = input(body)
                except TypeError:
                    self.send_err(attach_err)
                    return
                except KeyError:
                    self.send_err(attach_err)
                    return
                except json.decoder.JSONDecodeError:
                    self.send_err(attach_err)
                    return
                except Exception:
                    self.send_err(attach_err)
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
    header: str
    err: Type[ErrInfoBase] = DEFAULT_HEADER_NOT_FOUND_ERROR
    
    
def get_required_header_info(
    callback: Callback_t) -> List[RequiredHeaderInfo]:
    if hasattr(callback, ATTR_HEADERS_REQUIRED):
        arr_info = getattr(callback, ATTR_HEADERS_REQUIRED)
        return [RequiredHeaderInfo(*info) for info in arr_info]
    return []


def has_header_of(key: str, 
                  err: Type[ErrInfoBase] = DEFAULT_HEADER_NOT_FOUND_ERROR
                  ) -> Callback_t:
    
    def header_checker(callback: Callback_t) -> Callback_t:
        
        def _callback(self: Endpoint, *args) -> None:
            val = self.get_header(key)
            if val is None:
                self.send_err(err)
                return
            callback(self, *args)
        
        _callback.__dict__ = callback.__dict__
        if not hasattr(_callback, ATTR_HEADERS_REQUIRED):
            setattr(_callback, ATTR_HEADERS_REQUIRED, set())
        
        headers_required = getattr(_callback, ATTR_HEADERS_REQUIRED)
        headers_required.add((key, err))
        return _callback
    return header_checker

# ----------------------------------------------------------------------------

# IP restriction    ----------------------------------------------------------

ATTR_CLIENT_RESTRICTED = _get_bamboo_attr("client_restricted")


def get_restricted_ip_info(callback: Callback_t) -> List[str]:
    if hasattr(callback, ATTR_CLIENT_RESTRICTED):
        return getattr(callback, ATTR_CLIENT_RESTRICTED)
    return []


def restricts_client(*client_ips: str, 
                     err: Type[ErrInfoBase] = DEFAULT_NOT_APPLICABLE_IP_ERROR
                     ) -> Callback_t:
    
    def register_restrictions(callback: Callback_t) -> Callback_t:
            
        def _callback(self: Endpoint, *args) -> None:
            if self.client_ip not in client_ips:
                self.send_err(err)
                return
            callback(self, *args)
            
        _callback.__dict__ = callback.__dict__
        if not hasattr(callback, ATTR_CLIENT_RESTRICTED):
            setattr(callback, ATTR_CLIENT_RESTRICTED, set())
            
        restrictions = getattr(callback, ATTR_CLIENT_RESTRICTED)
        for ip in client_ips:
            restrictions.add(ip)
            
        return _callback
    return register_restrictions

# ----------------------------------------------------------------------------

# Error Information ----------------------------------------------------------

ATTR_ERRORS = _get_bamboo_attr("errors")


def get_errors_info(callback: Callback_t) -> List[Type[ErrInfoBase]]:
    if hasattr(callback, ATTR_ERRORS):
        return getattr(callback, ATTR_ERRORS)
    return []


def may_occurs(*errors: Type[ErrInfoBase]) -> Callback_t:
    
    def attach_err_info(callback: Callback_t) -> Callback_t:
        if not hasattr(callback, ATTR_ERRORS):
            setattr(callback, ATTR_ERRORS, set())
        
        registered = getattr(callback, ATTR_ERRORS)
        for err in errors:
            registered.add(err)
            
        return callback
    return attach_err_info

# ----------------------------------------------------------------------------
