
from bamboo.util.version import VersionState as _VersionState
from bamboo.util.version import resolve_version as _resolve_version


__version__ = _resolve_version(0, 2, 0, _VersionState.alpha)

from bamboo.api import (
    ApiData, NotJsonableAnnotationError, JsonApiData,
)

from bamboo.app import (
    App, ParcelConfig, ATTR_PARCEL, VersionConfig, ATTR_VERSION,
)

from bamboo.base import MediaTypes, HTTPMethods, HTTPStatus

from bamboo.endpoint import (
    BodyAlreadySetError, Endpoint, ATTR_DATA_FORMAT, DataFormatInfo,
    get_data_format_info, data_format, ATTR_HEADERS_REQUIRED, 
    RequiredHeaderInfo, get_required_header_info, has_header_of,
    ATTR_CLIENT_RESTRICTED, get_restricted_ip_info, restricts_client,
    ATTR_ERRORS, get_errors_info, may_occurs,
)

from bamboo.error import ErrInfoBase, ApiErrInfo

from bamboo.location import (
    FlexibleLocation, is_flexible_uri, is_duplicated_uri,
    NumLocation, StringLocation,
)

from bamboo.router import DuplicatedUriRegisteredError, Router
