
from dataclasses import dataclass
import json
from typing import Any, Callable, List, Optional, Tuple, Type, TypeVar

from bamboo.api import ApiData
from bamboo.endpoint import Endpoint
from bamboo.error import (
    DEFAULT_HEADER_NOT_FOUND_ERROR, DEFAULT_NOT_APPLICABLE_IP_ERROR,
    DEFUALT_INCORRECT_DATA_FORMAT_ERROR, ErrInfoBase,
)


Callback_t = Callable[[Endpoint, Tuple[Any, ...]], None]


def _get_bamboo_attr(attr: str) -> str:
    return f"__bamboo_{attr}__"


# Data Format   ----------------------------------------------------------------------------------------------------

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
                attach_err: Type[ErrInfoBase] = DEFUALT_INCORRECT_DATA_FORMAT_ERROR) -> Callback_t:
    
    _format = {"input": input, "output": output, "attach_err": attach_err, "is_attach": is_attach}
    
    if is_attach and input:
        def input_decoded(callback: Callable[[Endpoint, ApiData, Tuple[Any, ...]], None]) -> Callback_t:
            
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
                
                callback(self, data, *args)
                
            _callback.__dict__ = callback.__dict__
            setattr(callback, ATTR_DATA_FORMAT, _format)
                
            return _callback
        return input_decoded
    else:
        def input_decoded(callback: Callable[[Endpoint, Tuple[Any, ...]], None]) -> Callback_t:
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
    
# ------------------------------------------------------------------------------------------------------------------

# Required Headers  ------------------------------------------------------------------------------------------------

ATTR_HEADERS_REQUIRED = _get_bamboo_attr("headers_required")


@dataclass
class RequiredHeaderInfo:
    header: str
    err: Type[ErrInfoBase] = DEFAULT_HEADER_NOT_FOUND_ERROR
    
    
def get_required_header_info(callback: Callback_t) -> List[RequiredHeaderInfo]:
    if hasattr(callback, ATTR_HEADERS_REQUIRED):
        arr_info = getattr(callback, ATTR_HEADERS_REQUIRED)
        return [RequiredHeaderInfo(*info) for info in arr_info]
    return []


def has_header_of(key: str, err: Type[ErrInfoBase] = DEFAULT_HEADER_NOT_FOUND_ERROR) -> Callback_t:
    
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

# ------------------------------------------------------------------------------------------------------------------

# IP restriction    ------------------------------------------------------------------------------------------------

ATTR_CLIENT_RESTRICTED = _get_bamboo_attr("client_restricted")


def get_restricted_ip_info(callback: Callback_t) -> List[str]:
    if hasattr(callback, ATTR_CLIENT_RESTRICTED):
        return getattr(callback, ATTR_CLIENT_RESTRICTED)
    return []


def restricts_client(*client_ips: str, err: Type[ErrInfoBase] = DEFAULT_NOT_APPLICABLE_IP_ERROR) -> Callback_t:
    
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

# ------------------------------------------------------------------------------------------------------------------

# Error Information ------------------------------------------------------------------------------------------------

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

# ------------------------------------------------------------------------------------------------------------------
