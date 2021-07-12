import json
import typing as t

from .http import (
    AuthSchemes,
    ContentType,
    ContentTypeHolder,
    DEFAULT_CONTENT_TYPE_PLAIN,
    HTTPStatus, MediaTypes,
)
from .io import BufferedConcatIterator
from .util.deco import class_property


__all__ = []


class ErrInfo(Exception, ContentTypeHolder):
    """Base class of all error handlings.

    This class defines the attributes of all classes for error handling.

    Attributes:
        http_status (HTTPStatus) : HTTP status of the error.
        inheritted_headers (Set[str]) : Header names to be inheritted.
    """
    http_status: HTTPStatus = HTTPStatus.BAD_REQUEST
    inheritted_headers: t.Set[str] = set()

    def __init_subclass__(cls) -> None:
        # Make header names lower to ignore the difference of upper and
        # lower charactors.
        cls.inheritted_headers = set(map(str.lower, cls.inheritted_headers))

    @classmethod
    def should_inherit_header(cls, header_name: str) -> bool:
        return header_name.lower() in cls.inheritted_headers

    @class_property
    def __content_type__(cls) -> ContentType:
        """Content type with `text/plain`.
        """
        return DEFAULT_CONTENT_TYPE_PLAIN

    def get_headers(self) -> t.List[t.Tuple[str, str]]:
        """Publishes additional headers for error response.

        Returns:
            Additional headers.
        """
        return []

    def get_body(self) -> t.Union[bytes, t.Iterable[bytes]]:
        """Publishes response body for error response.

        Returns
            Response body of the error.
        """
        return b""

    def get_all_form(
        self,
    ) -> t.Tuple[
        HTTPStatus,
        t.List[t.Tuple[str, str]],
        t.Union[bytes, t.Iterable[bytes]]
    ]:
        """Get status code, headers and body of repsponse of the error.

        Returns:
            Tuple of status code, headers and body of the error.
        """
        stat = self.http_status
        headers = self.get_headers()
        body = self.get_body()

        # NOTE
        #   Automatically Content-Type header is to be added.
        headers.append(self.__content_type__.to_header())
        return (stat, headers, BufferedConcatIterator(body))

# ----------------------------------------------------------------------------

# Default errors    ----------------------------------------------------------

class DefaultNotFoundErrInfo(ErrInfo):

    http_status = HTTPStatus.NOT_FOUND


class DefaultDataFormatErrInfo(ErrInfo):

    http_status = HTTPStatus.UNSUPPORTED_MEDIA_TYPE


class DefaultHeaderNotFoundErrInfo(ErrInfo):

    http_status = HTTPStatus.BAD_REQUEST


class DefaultQueryParamNotFoundErrInfo(ErrInfo):

    http_status = HTTPStatus.BAD_REQUEST


class DefaultNotApplicableIpErrInfo(ErrInfo):

    http_status = HTTPStatus.FORBIDDEN


class DefualtCORSErrInfo(ErrInfo):

    http_status = HTTPStatus.FORBIDDEN


_WWW_AUTH_HEADER = "WWW-Authentication"


def get_auth_realm(scheme: str, msg: str) -> str:
    return f'{scheme} realm="{msg}"'


DEFAULT_REALM_MESSAGE = "SECRET AREA"


def get_default_auth_realm(scheme: str) -> str:
    return get_auth_realm(scheme, DEFAULT_REALM_MESSAGE)


class DefaultAuthHeaderNotFoundErrInfo(ErrInfo):

    http_status = HTTPStatus.UNAUTHORIZED

    def __init__(self, scheme: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._scheme = scheme

    @property
    def scheme(self) -> str:
        return self._scheme

    def get_headers(self) -> t.List[t.Tuple[str, str]]:
        value = get_default_auth_realm(self._scheme)
        return [(_WWW_AUTH_HEADER, value)]


DEFAULT_NOT_FOUND_ERROR = DefaultNotFoundErrInfo()
DEFUALT_INCORRECT_DATA_FORMAT_ERROR = DefaultDataFormatErrInfo()
DEFAULT_HEADER_NOT_FOUND_ERROR = DefaultHeaderNotFoundErrInfo()
DEFAULT_QUERY_PARAM_NOT_FOUND_ERROR = DefaultQueryParamNotFoundErrInfo()
DEFAULT_NOT_APPLICABLE_IP_ERROR = DefaultNotApplicableIpErrInfo()
DEFAULT_BASIC_AUTH_HEADER_NOT_FOUND_ERROR = DefaultAuthHeaderNotFoundErrInfo(AuthSchemes.basic)
DEFAULT_BEARER_AUTH_HEADER_NOT_FOUND_ERROR = DefaultAuthHeaderNotFoundErrInfo(AuthSchemes.bearer)
DEFAULT_CORS_ERROR = DefualtCORSErrInfo()

# ----------------------------------------------------------------------------

class ApiErrInfo(ErrInfo):
    """ErrInfo to handle API error.

    This ErrInfo has implemented method of 'get_body'. This class
    emits Json data including error information defined by developer
    when the error is sent.

    Attributes:
        http_status (HTTPStatus): HTTP status of the error.
        code (str): Error code for your API.
        dev_message (Optional[str]): Message to explain developers the error.
        user_message (Optional[str]): Message to explain end users the error.
        info (Optional[str]): Information about the error.
        encoding (str): Encoding to encode response body.
    """
    code: str
    dev_message: t.Optional[str] = None
    user_message: t.Optional[str] = None
    info: t.Optional[str] = None
    encoding: str = "UTF-8"

    @class_property
    def __content_type__(cls) -> ContentType:
        """Content type with `application/json` and `charset` specified as
        the value of `encoding`.
        """
        return ContentType(MediaTypes.json, charset=cls.encoding)

    def get_body(self) -> t.Optional[bytes]:
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
