
from __future__ import annotations

from abc import ABCMeta, abstractmethod
import codecs
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

from bamboo.base import ASGIHTTPEvents, HTTPStatus
from bamboo.endpoint import (
    ASGIHTTPEndpoint,
    EndpointBase,
    WSGIEndpoint,
)
from bamboo.error import DEFAULT_NOT_FOUND_ERROR, ErrInfoBase
from bamboo.io import BufferedConcatIterator
from bamboo.location import Location_t, Uri_t
from bamboo.router import Router, Endpoint_t
from bamboo.sticky import _get_bamboo_attr


__all__ = []


ATTR_VERSION = _get_bamboo_attr("version")
Version_t = Tuple[int]


class VersionConfig:
    """Operator class for version of `Endpoint`.

    This class can be used to get and set version of `Endpoint` safely.
    """

    def __init__(self, endpoint: Type[EndpointBase]) -> None:
        """
        Args:
            endpoint: `Endpoint` whose version is to be manipulated
        """
        self._endpoint_class = endpoint

    def set(
        self,
        app: AppBase,
        version: Union[int, Tuple[int], None] = None,
        force: bool = False
    ) -> None:
        """Set version of `Endpoint`.

        Args:
            app: Application including the internal `Endpoint`.
            version: Version to be set.
            force: If forcing to set the `version`.

        Raises:
            ValueError: Raised if version of the `Endpoint` has already
                been set.
        """
        if not hasattr(self._endpoint_class, ATTR_VERSION):
            setattr(self._endpoint_class, ATTR_VERSION, {})

        registered = getattr(self._endpoint_class, ATTR_VERSION)
        current_version = registered.get(app)
        if current_version and not force:
            raise ValueError(
                f"{self._endpoint_class.__name__} already has own version."
                "If you want to overwirte it, set param 'force' True.")

        # Format to fit the type Version_t
        if version is None:
            version = ()
        if isinstance(version, int):
            version = (version,)

        registered[app] = version

    def get(self, app: AppBase) -> Optional[Version_t]:
        """Retrieve version belonging to specified `app`.

        Args:
            app: Application including the internal `Endpoint`.

        Returns:
            Version set to `Endpoint`, if not set yet, then None.
        """
        if hasattr(self._endpoint_class, ATTR_VERSION):
            registered = getattr(self._endpoint_class, ATTR_VERSION)
            return registered.get(app)
        return None

    def get_all(self) -> List[Tuple[AppBase, Version_t]]:
        """Retrieve versions belonging to all `AppBase` objects.

        Returns:
            List of tuples of `AppBase` objects and their versions.
        """
        if hasattr(self._endpoint_class, ATTR_VERSION):
            registered = getattr(self._endpoint_class, ATTR_VERSION)
            return [(app, version) for app, version in registered.items()]
        return []


ATTR_PARCEL = _get_bamboo_attr("parcel")
Parcel_t = Tuple[Any, ...]


class ParcelConfig:
    """Operator class for parcel of `Endpoint`.

    This class can be used to get and set parcel of `Endpoint` safely.
    """

    def __init__(self, endpoint: Type[EndpointBase]) -> None:
        """
        Args:
            endpoint : `Endpoint` whose parcel is to be manipulated.
        """
        self._endpoint_class = endpoint

    def set(self, app: AppBase, parcel: Parcel_t) -> None:
        """Ser parcel of `Endpoint`.

        Args:
            app: Application including the internal `Endpoint`.
            parcel: Parcel to be set.
        """
        if not hasattr(self._endpoint_class, ATTR_PARCEL):
            setattr(self._endpoint_class, ATTR_PARCEL, {})

        registered = getattr(self._endpoint_class, ATTR_PARCEL)
        registered[app] = parcel

    def get(self, app: AppBase) -> Parcel_t:
        """Retrieve parcel belonging to specified `app`.

        Args:
            app: Application including the internal `Endpoint`

        Returns:
            Parcel set to `Endpoint`, if not set yet, then `None`.
        """
        if hasattr(self._endpoint_class, ATTR_PARCEL):
            registered = getattr(self._endpoint_class, ATTR_PARCEL)
            return registered.get(app)
        return ()

    def get_all(self) -> List[Tuple[AppBase, Parcel_t]]:
        """Retrieve parcels belonging to all `AppBase` objects.

        Returns:
            List of tuples of `AppBase` objects and their parcels.
        """
        if hasattr(self._endpoint_class, ATTR_PARCEL):
            registered = getattr(self._endpoint_class, ATTR_PARCEL)
            return [(app, parcel) for app, parcel in registered.items()]
        return []


class AppBase(Generic[Endpoint_t], metaclass=ABCMeta):
    """Base class of all application in Bamboo.

    Bamboo has two core concepts called application and endpoint, and
    this class implements basic behavior of the former, e.g. containing
    multiple endpoints, routing requests from URIs to endpoints and so on.

    Note:
        This class is an abstract class. Consider using its subclasses.

    Attributes:
        TAG_VERSION (str): Tag used when versions of `Endpoint`s are inserted
            in front of paths of URIs. If you want, you can override the
            value and set new favorite tag. By default, the tag is 'v'.
    """

    TAG_VERSION = "v"
    __avalidable_endpoints = (EndpointBase,)

    def __init__(
        self,
        is_version_inserted: bool = True,
        error_404: ErrInfoBase = DEFAULT_NOT_FOUND_ERROR
    ) -> None:
        """
        Args:
            is_version_inserted: If version is inserted at the head of
                paths of URIs.
            error_404: Error sending if a request to not registered URI or
                HTTP method comes.
        """
        self._router: Router[Endpoint_t] = Router()
        self._is_version_isnerted = is_version_inserted
        self._error_404 = error_404

    @abstractmethod
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass

    def seach_uris(self, endpoint: Type[Endpoint_t]) -> List[Uri_t]:
        """Retrieve all URI patterns of `Endpoint`.

        Note:
            This method uses `bamboo.Router.search_uris()` method inner.
            For more information, see the API document.

        Args:
            endpoint: `Endpoint` whose URIs to be searched.

        Returns:
            Result of searching.
        """
        return self._router.search_uris(endpoint)

    def validate(self, uri: str) -> Tuple[Tuple[str, ...], Optional[Type[Endpoint_t]]]:
        """Validate specified `uri` and retrieve corresponding `Endpoint` class.

        Note:
            This method uses `bamboo.Router.validate()` method inner.
            For more information, see the API document.

        Args:
            uri: Path of URI to be validated.

        Returns:
            Pair of values of flexible locations and `Endpoint` class if specified
            `uri` is valid, otherwise, pari of empty tuple and None.
        """
        return self._router.validate(uri)

    def route(
        self,
        *locs: Location_t,
        version: Union[int, Tuple[int], None] = None
    ) -> Callable[[Type[Endpoint_t]], Type[Endpoint_t]]:
        """Register combination of URI and `Endpoint` for routing.

        Args:
            version : Version of the `Endpoint`.

        Returns:
            Decorator to add combination of URI and `Endpoint`.

        Examples:
            ```python
            app = App()

            # Set path of URI as `test/data/image` and the version as 1
            @app.route("test", "data", "image", version=1)
            class MockEndpoint(Endpoint):

                def do_GET(self) -> None:
                    # Do something...
            ```
        """
        def register_endpoint(endpoint: Type[Endpoint_t]) -> Type[Endpoint_t]:
            if not issubclass(endpoint, self.__avalidable_endpoints):
                raise TypeError(
                    f"{endpoint.__name__} is not avalidable in "
                    f"the {self.__class__.__name__}."
                )

            # version setting
            ver_config = VersionConfig(endpoint)
            ver_config.set(self, version)

            # router setting
            _version = ver_config.get(self)
            if self._is_version_isnerted and len(_version):
                _version = ver_config.get(self)
                if len(_version):
                    uri_list = [
                        (f"{self.TAG_VERSION}{ver_num}",) + locs
                        for ver_num in _version
                    ]
                    for uri_version_included in uri_list:
                        self._router.register(uri_version_included, endpoint)
            else:
                self._router.register(locs, endpoint)

            return endpoint
        return register_endpoint

    def set_parcel(self, endpoint: Type[Endpoint_t], *parcel: Any) -> None:
        """Set parcel to an endpoint.

        This method enables to give objects to `Endpoint` objects
        dynamically. A parcel is a set of objects delivered via the method,
        and the `Endpoint` object of its destination receives it at
        `EndpointBase.setup()` method.

        Note:
            For more information about the `bamboo.EndpointBase.setup()`,
            see the API document.

        Args:
            endpoint: `Endpoint` the `parcel` to be set.
            *parcel: Pacel to be given to the `Endpoint`.
        """
        parcel_config = ParcelConfig(endpoint)
        parcel_config.set(self, parcel)


class WSGIApp(AppBase):
    """Application compliant with the WSGI.

    This class is a subclass of `AppBase` calss and implements the callbable
    compliant with the WSGI.

    Note:
        This class can be used only for WSGI server. If you want to use
        any ASGI servers, consider using `ASGIHTTPApp`.

        This class can also route only `WSGIEndpoint`s. If you want to
        another type of endpoint, consider implementation class of its
        corresponding application.
    """

    __avalidable_endpoints = (WSGIEndpoint,)

    def __call__(
        self,
        environ: Dict[str, Any],
        start_response: Callable
    ) -> List[bytes]:
        method = environ.get("REQUEST_METHOD").upper()
        path = environ.get("PATH_INFO")

        flexible_locs, endpoint_class = self.validate(path)
        if endpoint_class is None:
            return [self.send_404(start_response)]

        parcel_config = ParcelConfig(endpoint_class)
        parcel = parcel_config.get(self)

        endpoint = endpoint_class(environ, flexible_locs, *parcel)
        callback = endpoint_class._get_response_method(method)
        if callback is None:
            return [self.send_404(start_response)]

        callback(endpoint)
        start_response(endpoint._res_status.wsgi, endpoint._res_headers)
        return endpoint._res_body

    def send_404(self, start_response: Callable) -> bytes:
        """Send `404` error code, i.e. `Resource Not Found` error.

        Args:
            start_response: `start_response` callable given from
                the WSGI application.

        Returns:
            Response body of the error.
        """
        status, headers, res_body = self._error_404.get_all_form()
        start_response(status.wsgi, headers)
        return res_body

    def seach_uris(self, endpoint: Type[WSGIEndpoint]) -> List[Uri_t]:
        return super().seach_uris(endpoint)

    def validate(
        self,
        uri: str
    ) -> Tuple[Tuple[str, ...], Optional[Type[WSGIEndpoint]]]:
        return super().validate(uri)

    def route(
        self,
        *locs: Location_t,
        version: Union[int, Tuple[int], None] = None
    ) -> Callable[[Type[WSGIEndpoint]], Type[WSGIEndpoint]]:
        return super().route(*locs, version=version)

    def set_parcel(
        self,
        endpoint: Type[WSGIEndpoint],
        *parcel: Any
    ) -> None:
        return super().set_parcel(endpoint, *parcel)


class ASGIHTTPApp(AppBase):
    """Application compliant with the ASGI.

    This class is a subclass of `AppBase` calss and implements the callbable
    compliant with the ASGI.

    Note:
        This class can be used only for ASGI server. If you want to use
        any WSGI servers, consider using `WSGIApp`.

        This class can also route only `ASGIHTTPEndpoint`s. If you want to
        another type of endpoint, consider implementation class of its
        corresponding application.
    """

    __avalidable_endpoints = (ASGIHTTPEndpoint,)

    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        method = scope.get("method")
        path = scope.get("path")

        flexible_locs, endpoint_class = self.validate(path)
        if endpoint_class is None:
            await self.send_404(send)
            return

        parcel_config = ParcelConfig(endpoint_class)
        parcel = parcel_config.get(self)

        endpoint = endpoint_class(scope, receive, flexible_locs, *parcel)
        callback = endpoint_class._get_response_method(method)
        if callback is None:
            await self.send_404(send)
            return

        await callback(endpoint)
        await self.send_start(send, endpoint._res_status, endpoint._res_headers)
        await self.send_body(send, endpoint._res_body)

    @staticmethod
    async def send_start(
        send: Callable[[Dict[str, Any]], Awaitable[None]],
        status: HTTPStatus,
        headers: List[Tuple[bytes, bytes]]
    ) -> None:
        """Start repsonse by sending response status and headers.

        Args:
            send: `send` awaitable given from the ASGI application.
            status: Response status.
            headers: Response headers.
        """
        await send({
            "type": ASGIHTTPEvents.response_start,
            "status": status.asgi,
            "headers": headers
        })

    @staticmethod
    async def send_body(
        send: Callable[[Dict[str, Any], Awaitable[None]]],
        body: BufferedConcatIterator
    ) -> None:
        """Send response body.

        Args:
            send: `send` awaitable given from the ASGI application.
            body: Response body made in an `Endpoint` object.
        """
        for chunk in body:
            await send({
                "type": ASGIHTTPEvents.response_body,
                "body": chunk,
                "more_body": True
            })
        await send({"type": ASGIHTTPEvents.response_body})

    async def send_404(
        self,
        send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Send `404` error code, i.e. `Resource Not Found` error.

        Args:
            send: `send` awaitable given from the ASGI application.
        """
        status, headers, res_body = self._error_404.get_all_form()
        headers = [
            tuple(map(codecs.encode, header)) for header in headers
        ]
        await self.send_start(send, status, headers)
        await self.send_body(send, BufferedConcatIterator(res_body))

    def seach_uris(
        self,
        endpoint: Type[ASGIHTTPEndpoint]
    ) -> List[Uri_t]:
        return super().seach_uris(endpoint)

    def validate(
        self,
        uri: str
    ) -> Tuple[Tuple[str, ...], Optional[Type[ASGIHTTPEndpoint]]]:
        return super().validate(uri)

    def route(
        self,
        *locs: Location_t,
        version: Union[int, Tuple[int], None] = None
    ) -> Callable[[Type[ASGIHTTPEndpoint]], Type[ASGIHTTPEndpoint]]:
        return super().route(*locs, version=version)

    def set_parcel(
        self,
        endpoint: Type[ASGIHTTPEndpoint],
        *parcel: Any
    ) -> None:
        return super().set_parcel(endpoint, *parcel)
