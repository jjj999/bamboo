
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
from bamboo.error import DEFAULT_NOT_FOUND_ERROR
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
        Parameters
        ----------
        endpoint : Type[Endpoint]
            `Endpoint` whose version is to be manipulated
        """
        self._endpoint_class = endpoint

    def set(
        self,
        app: AppBase,
        version: Union[int, Tuple[int], None] = None,
        force: bool = False
    ) -> None:
        """Set version of `Endpoint`.

        Parameters
        ----------
        app : AppBase
            Application including the internal `Endpoint`
        version : Union[int, Tuple[int], None], optional
            Version to be set, by default `None`
        force : bool, optional
            If forcing to set the `version`, by default `False`

        Raises
        ------
        ValueError
            Raised if version of the `Endpoint` has already been set.
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

        Parameters
        ----------
        app : AppBase
            Application including the internal `Endpoint`

        Returns
        -------
        Optional[Version_t]
            Version set to `Endpoint`, if not set yet, then `None`
        """
        if hasattr(self._endpoint_class, ATTR_VERSION):
            registered = getattr(self._endpoint_class, ATTR_VERSION)
            return registered.get(app)
        return None

    def get_all(self) -> List[Tuple[AppBase, Version_t]]:
        """Retrieve versions belonging to all `AppBase` objects.

        Returns
        -------
        List[Tuple[AppBase, Version_t]]
            `list` of `tuple`s of `AppBase` objects and their versions
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
        Parameters
        ----------
        endpoint : Type[Endpoint]
            `Endpoint` whose parcel is to be manipulated
        """
        self._endpoint_class = endpoint

    def set(self, app: AppBase, parcel: Parcel_t) -> None:
        """Ser parcel of `Endpoint`

        Parameters
        ----------
        app : AppBase
            Application including the internal `Endpoint`
        parcel : Parcel_t
            Parcel to be set
        """
        if not hasattr(self._endpoint_class, ATTR_PARCEL):
            setattr(self._endpoint_class, ATTR_PARCEL, {})

        registered = getattr(self._endpoint_class, ATTR_PARCEL)
        registered[app] = parcel

    def get(self, app: AppBase) -> Parcel_t:
        """Retrieve parcel belonging to specified `app`/

        Parameters
        ----------
        app : AppBase
            Application including the internal `Endpoint`

        Returns
        -------
        Parcel_t
            Parcel set to `Endpoint`, if not set yet, then `None`
        """
        if hasattr(self._endpoint_class, ATTR_PARCEL):
            registered = getattr(self._endpoint_class, ATTR_PARCEL)
            return registered.get(app)
        return ()

    def get_all(self) -> List[Tuple[AppBase, Parcel_t]]:
        """Retrieve parcels belonging to all `AppBase` objects.

        Returns
        -------
        List[Tuple[AppBase, Parcel_t]]
            `list` of `tuple`s of `AppBase` objects and their parcels
        """
        if hasattr(self._endpoint_class, ATTR_PARCEL):
            registered = getattr(self._endpoint_class, ATTR_PARCEL)
            return [(app, parcel) for app, parcel in registered.items()]
        return []


class AppBase(Generic[Endpoint_t], metaclass=ABCMeta):

    TAG_VERSION = "v"
    __avalidable_endpoints = (EndpointBase,)

    def __init__(self, is_version_inserted: bool = True) -> None:
        """
        Parameters
        ----------
        is_version_inserted : bool, optional
            If version is inserted at the head of paths of URIs,
            by default `True`
        """
        self._router: Router[Endpoint_t] = Router()
        self._is_version_isnerted = is_version_inserted

    @abstractmethod
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass

    def seach_uris(self, endpoint: Type[Endpoint_t]) -> List[Uri_t]:
        """Retrieve all URI patterns of `Endpoint`.

        Parameters
        ----------
        endpoint : Type[Endpoint]
            `Endpoint` whose URIs to be searched

        Returns
        -------
        List[Uri_t]
            Result of searching
        """
        return self._router.search_uris(endpoint)

    def validate(self, uri: str) -> Tuple[Tuple[str, ...], Optional[Type[Endpoint_t]]]:
        return self._router.validate(uri)

    def route(
        self,
        *locs: Location_t,
        version: Union[int, Tuple[int], None] = None
    ) -> Callable[[Type[Endpoint_t]], Type[Endpoint_t]]:
        """Register combination of URI and `Endpoint` for routing.

        Parameters
        ----------
        version : Union[int, Tuple[int], None], optional
            Version of the `Endpoint`, by default None

        Returns
        -------
        Callable[[Type[Endpoint]], Type[Endpoint]]
            Decorator to add combination of URI and `Endpoint`

        Examples
        --------
        ```
        app = App()

        # set path of URI as `test/data/image` and version as 1
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

        Parameters
        ----------
        endpoint : Type[Endpoint]
            `Endpoint` the `parcel` to be set
        *parcel : Any
            Pacel to be given to the `Endpoint`
        """
        parcel_config = ParcelConfig(endpoint)
        parcel_config.set(self, parcel)


class WSGIApp(AppBase):
    """Application objects compliant with the WSGI.
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

    @staticmethod
    def send_404(start_response: Callable) -> bytes:
        """Send `404` error code, i.e. `Resource Not Found` error.

        Parameters
        ----------
        start_response : Callable
            `start_response` callbale given from the WSGI application

        Returns
        -------
        bytes
            Response body
        """
        status, headers, res_body = DEFAULT_NOT_FOUND_ERROR.get_all_form()
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
        for chunk in body:
            await send({
                "type": ASGIHTTPEvents.response_body,
                "body": chunk,
                "more_body": True
            })
        await send({"type": ASGIHTTPEvents.response_body})

    @classmethod
    async def send_404(
        cls,
        send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        status, headers, res_body = DEFAULT_NOT_FOUND_ERROR.get_all_form()
        headers = [
            tuple(map(codecs.encode, header)) for header in headers
        ]
        await cls.send_start(send, status, headers)
        await cls.send_body(send, BufferedConcatIterator(res_body))

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
