
import json
from typing import List, Optional, Tuple

from bamboo.base import (
    ContentType, HTTPStatus, ContentTypeHolder,
    DEFAULT_CONTENT_TYPE_PLAIN, DEFAULT_CONTENT_TYPE_JSON,
)
from bamboo.util.deco import class_property


class ErrInfoBase(ContentTypeHolder):
    """Base class of all error handlings.
    
    This class defines the attributes of all classes for error handling.
    
    Attributes
    ----------
    http_status : HTTPStatus
        HTTP status of the error
    message : Optional[str]
        short message for announcing error, default None
    """
    http_status: HTTPStatus = HTTPStatus.BAD_REQUEST
    
    # Optional short message for announcing error.
    # If None, will be set as default message.
    message: Optional[str] = None
    
    def __init_subclass__(cls) -> None:
        if cls.message is None:
           cls.message = cls.http_status.description
    
    def __init__(self, *args, **kwargs) -> None:
        pass
    
    @class_property
    def _content_type_(cls) -> ContentType:
        return DEFAULT_CONTENT_TYPE_PLAIN
    
    def get_headers(self) -> List[Tuple[str, str]]:
        """Publishes additional headers for error response.

        Returns
        -------
        List[Tuple[str, str]]
            Additional headers
        """
        return []
    
    def get_body(self) -> bytes:
        """Publishes response body for error response.

        Returns
        -------
        bytes
            Response body
        """
        return b""
    
    def get_all_form(self) -> Tuple[HTTPStatus, List[Tuple[str, str]], bytes]:
        stat = self.http_status
        headers = self.get_headers()
        body = self.get_body()
        return (stat, headers, body)
           
           
class DefaultNotFoundErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.NOT_FOUND
    
    
DEFAULT_NOT_FOUND_ERROR = DefaultNotFoundErrInfo()


class DefaultDataFormatErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.UNSUPPORTED_MEDIA_TYPE


DEFUALT_INCORRECT_DATA_FORMAT_ERROR = DefaultDataFormatErrInfo()


class DefaultHeaderNotFoundErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.BAD_REQUEST
    

DEFAULT_HEADER_NOT_FOUND_ERROR = DefaultHeaderNotFoundErrInfo()


class DefaultNotApplicableIpErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.FORBIDDEN
    

DEFAULT_NOT_APPLICABLE_IP_ERROR = DefaultNotApplicableIpErrInfo()


class ApiErrInfo(ErrInfoBase):
    """ErrInfo to handle API error.
    
    This ErrInfo has implemented method of 'get_body'. This class 
    emits Json data including error information defined by developer 
    when the error is sent.
    
    Attributes
    ----------
    http_status : HTTPStatus
        HTTP status of the error
    message : Optional[str]
        Short message for announcing error, by default None
    code : Optional[int]
        Error code for your API, by default None
    dev_message : Optional[str]
        Message to explain developers the error, by default None
    user_message : Optional[str]
        Message to explain end users the error, by default None
    info : Optional[str]
        Information about the error, by default None
    encoding : str
        Encoding to encode response body, by default 'UTF-8'
    """    
    code: Optional[int] = None
    dev_message: Optional[str] = None
    user_message: Optional[str] = None
    info: Optional[str] = None
    encoding: str = "UTF-8"
    
    @class_property
    def _content_type_(cls) -> ContentType:
        return DEFAULT_CONTENT_TYPE_JSON
    
    def get_body(self) -> Optional[bytes]:
        """Publishes response body for error response.

        Returns
        -------
        bytes
            Response body
        """
        body = {
            "code": self.code,
            "developerMessage": self.dev_message,
            "uesrMessage": self.user_message,
            "info": self.info
        }
        return json.dumps(body).encode(encoding=self.encoding)
