
import json
from typing import List, Optional, Tuple

from bamboo.base import HTTPStatus


class ErrInfoBase:
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
    
    @classmethod
    def get_headers(cls) -> List[Tuple[str, str]]:
        """Publishes additional headers for error response.

        Returns
        -------
        List[Tuple[str, str]]
            Additional headers
        """
        return []
    
    # Optional response body emitter when an error occurs.
    # This is a classmethod, so users can use their defined
    # class attributes. This method is always called at error.
    @classmethod
    def get_body(cls) -> bytes:
        """Publishes response body for error response.

        Returns
        -------
        bytes
            Response body
        """
        return b""
    
    @classmethod
    def _get_all_form(cls) -> Tuple[HTTPStatus, List[Tuple[str, str]], bytes]:
        stat = cls.http_status
        headers = cls.get_headers()
        body = cls.get_body()
        return (stat, headers, body)
    
    def __init_subclass__(cls) -> None:
        if cls.message is None:
           cls.message = cls.http_status.description 
           
           
class DefaultNotFoundErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.NOT_FOUND
    
    
DEFAULT_NOT_FOUND_ERROR = DefaultNotFoundErrInfo


class DefaultDataFormatErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.UNSUPPORTED_MEDIA_TYPE


DEFUALT_INCORRECT_DATA_FORMAT_ERROR = DefaultDataFormatErrInfo


class DefaultHeaderNotFoundErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.BAD_REQUEST
    

DEFAULT_HEADER_NOT_FOUND_ERROR = DefaultHeaderNotFoundErrInfo


class DefaultNotApplicableIpErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.FORBIDDEN
    

DEFAULT_NOT_APPLICABLE_IP_ERROR = DefaultNotApplicableIpErrInfo


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
        Short message for announcing error, default None
    code : Optional[int]
        Error code for your API, default None
    dev_message : Optional[str]
        Message to explain developers the error, default None
    user_message : Optional[str]
        Message to explain end users the error, default None
    info : Optional[str]
        Information about the error, default None
    encoding : str
        Encoding to encode response body, default 'utf-8'
    """
    
    code: Optional[int] = None
    dev_message: Optional[str] = None
    user_message: Optional[str] = None
    info: Optional[str] = None
    encoding: str = "utf-8"
    
    @classmethod
    def get_body(cls) -> Optional[bytes]:
        body = {
            "code": cls.code,
            "developerMessage": cls.dev_message,
            "uesrMessage": cls.user_message,
            "info": cls.info
        }
        return json.dumps(body).encode(encoding=cls.encoding)
