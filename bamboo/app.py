
from __future__ import annotations
from typing import (
    Any, Callable, Dict, List, Optional, Tuple, Type, Union,
)

from bamboo.endpoint import Endpoint, _get_bamboo_attr
from bamboo.error import DEFAULT_NOT_FOUND_ERROR
from bamboo.location import Location_t, Uri_t
from bamboo.router import Router


ATTR_VERSION = _get_bamboo_attr("version")
Version_t = Tuple[int]


class VersionConfig:
    """Operator class for version of `Endpoint`.
    
    This class can be used to get and set version of `Endpoint` safely.
    """
    
    def __init__(self, endpoint: Type[Endpoint]) -> None:
        """
        Parameters
        ----------
        endpoint : Type[Endpoint]
            `Endpoint` whose version is to be manipulated
        """
        self._endpoint_class = endpoint
        
    def set(self, app: App, version: Union[int, Tuple[int], None] = None,
            force: bool = False) -> None:
        """Set version of `Endpoint`.

        Parameters
        ----------
        app : App
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
        
    def get(self, app: App) -> Optional[Version_t]:
        """Retrieve version belonging to specified `app`.

        Parameters
        ----------
        app : App
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
    
    def get_all(self) -> List[Tuple[App, Version_t]]:
        """Retrieve versions belonging to all `App` objects.

        Returns
        -------
        List[Tuple[App, Version_t]]
            `list` of `tuple`s of `App` objects and their versions
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
    
    def __init__(self, endpoint: Type[Endpoint]) -> None:
        """
        Parameters
        ----------
        endpoint : Type[Endpoint]
            `Endpoint` whose parcel is to be manipulated
        """
        self._endpoint_class = endpoint
        
    def set(self, app: App, parcel: Parcel_t) -> None:
        """Ser parcel of `Endpoint`

        Parameters
        ----------
        app : App
            Application including the internal `Endpoint`
        parcel : Parcel_t
            Parcel to be set
        """
        if not hasattr(self._endpoint_class, ATTR_PARCEL):
            setattr(self._endpoint_class, ATTR_PARCEL, {})
        
        registered = getattr(self._endpoint_class, ATTR_PARCEL)
        registered[app] = parcel
        
    def get(self, app: App) -> Optional[Parcel_t]:
        """Retrieve parcel belonging to specified `app`/

        Parameters
        ----------
        app : App
            Application including the internal `Endpoint`

        Returns
        -------
        Optional[Parcel_t]
            Parcel set to `Endpoint`, if not set yet, then `None`
        """
        if hasattr(self._endpoint_class, ATTR_PARCEL):
            registered = getattr(self._endpoint_class, ATTR_PARCEL)
            return registered.get(app)
        return None
        
    def get_all(self) -> List[Tuple[App, Parcel_t]]:
        """Retrieve parcels belonging to all `App` objects.

        Returns
        -------
        List[Tuple[App, Parcel_t]]
            `list` of `tuple`s of `App` objects and their parcels
        """
        if hasattr(self._endpoint_class, ATTR_PARCEL):
            registered = getattr(self._endpoint_class, ATTR_PARCEL)
            return [(app, parcel) for app, parcel in registered.items()]
        return []


class App:
    """Application objects compliant with the WSGI.

    Attributes
    ----------
    TAG_VERSION : str
        Prefix of version
    """
    
    TAG_VERSION = "v"
    
    def __init__(self, is_version_inserted: bool = True) -> None:
        """
        Parameters
        ----------
        is_version_inserted : bool, optional
            If version is inserted at the head of paths of URIs, 
            by default `True`
        """
        self._router = Router()
        self._is_version_isnerted = is_version_inserted
    
    def __call__(self, environ: Dict[str, Any],
                 start_response: Callable) -> List[bytes]:
        method = environ.get("REQUEST_METHOD").upper()
        path = environ.get("PATH_INFO")
        
        flexible_locs, endpoint_class = self._router.validate(path)
        if endpoint_class is None:
            return [self._send_404(start_response)]
        
        parcel_config = ParcelConfig(endpoint_class)
        parcel = parcel_config.get(self)
        
        endpoint = endpoint_class(environ, flexible_locs, *parcel)
        callback = endpoint_class._get_response_method(method)
        if callback is None:
            return [self._send_404(start_response)]
        
        callback(endpoint)
        start_response(endpoint._status.value, endpoint._headers)
        return [endpoint._res_body]
    
    @staticmethod
    def _send_404(start_response: Callable) -> bytes:
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
        stat, headers, res_body = DEFAULT_NOT_FOUND_ERROR.get_all_form()
        start_response(stat.value, headers)
        return res_body
    
    def seach_uris(self, endpoint: Type[Endpoint]) -> List[Uri_t]:
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
    
    def route(self, *locs: Location_t, parcel: Parcel_t = (),
              version: Union[int, Tuple[int], None] = None
              ) -> Callable[[Type[Endpoint]], Type[Endpoint]]:
        """Register combination of URI and `Endpoint` for routing.

        Parameters
        ----------
        parcel : Parcel_t, optional
            Pacel to be given to the `Endpoint`, by default ()
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
        def register_endpoint(endpoint: Type[Endpoint]) -> Type[Endpoint]:
            # parcel setting
            parcel_config = ParcelConfig(endpoint)
            parcel_config.set(self, parcel)
            
            # version setting
            ver_config = VersionConfig(endpoint)
            ver_config.set(self, version)
            
            # router setting
            _version = ver_config.get(self)
            if self._is_version_isnerted and len(_version):
                _version = ver_config.get(self)
                if len(_version):
                    uri_list = [(f"{self.TAG_VERSION}{ver_num}",) + locs 
                                for ver_num in _version]
                    for uri_version_included in uri_list:
                        self._router.register(uri_version_included, endpoint)
            else:
                self._router.register(locs, endpoint)

            return endpoint
        return register_endpoint
