
from __future__ import annotations
from typing import (
    Any, Callable, Dict, List, Optional, Tuple, Type, Union,
)

from bamboo.endpoint import Endpoint, _get_bamboo_attr
from bamboo.error import DEFAULT_NOT_FOUND_ERROR
from bamboo.location import Location, Uri_t
from bamboo.router import Router


ATTR_VERSION = _get_bamboo_attr("version")
Version_t = Tuple[int]


class VersionConfig:
    
    def __init__(self, endpoint: Type[Endpoint]) -> None:
        self._endpoint_class = endpoint
        
    def set(self, app: App, version: Union[int, Tuple[int], None] = None,
            force: bool = False) -> None:
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
        if hasattr(self._endpoint_class, ATTR_VERSION):
            registered = getattr(self._endpoint_class, ATTR_VERSION)
            return registered.get(app)
        return None
    
    def get_all(self) -> List[Tuple[App, Version_t]]:
        if hasattr(self._endpoint_class, ATTR_VERSION):
            registered = getattr(self._endpoint_class, ATTR_VERSION)
            return [(app, version) for app, version in registered.items()]
        return []


ATTR_PARCEL = _get_bamboo_attr("parcel")
Parcel_t = Tuple[Any, ...]


class ParcelConfig:
    
    def __init__(self, endpoint: Type[Endpoint]) -> None:
        self._endpoint_class = endpoint
        
    def set(self, app: App, parcel: Parcel_t) -> None:
        if not hasattr(self._endpoint_class, ATTR_PARCEL):
            setattr(self._endpoint_class, ATTR_PARCEL, {})
        
        registered = getattr(self._endpoint_class, ATTR_PARCEL)
        registered[app] = parcel
        
    def get(self, app: App) -> Optional[Parcel_t]:
        if hasattr(self._endpoint_class, ATTR_PARCEL):
            registered = getattr(self._endpoint_class, ATTR_PARCEL)
            return registered.get(app)
        return None
        
    def get_all(self) -> List[Tuple[App, Parcel_t]]:
        if hasattr(self._endpoint_class, ATTR_PARCEL):
            registered = getattr(self._endpoint_class, ATTR_PARCEL)
            return [(app, parcel) for app, parcel in registered.items()]
        return []


class App:
    
    TAG_VERSION = "v"
    
    def __init__(self, is_version_insert: bool = True) -> None:
        self._router = Router()
        self._is_version_isnert = is_version_insert
    
    def __call__(self, environ: Dict[str, Any],
                 start_response: Callable) -> List[bytes]:
        method = environ.get("REQUEST_METHOD").upper()
        path = environ.get("PATH_INFO")
        
        endpoint_class = self._router.validate(path)
        if endpoint_class is None:
            return [self.send_404(start_response)]
        
        parcel_config = ParcelConfig(endpoint_class)
        parcel = parcel_config.get(self)
        
        endpoint = endpoint_class(environ, *parcel)
        callback = endpoint_class._get_response_method(method)
        if callback is None:
            return [self.send_404(start_response)]
        
        callback(endpoint)
        start_response(endpoint._status.value, endpoint._headers)
        return [endpoint._res_body]
    
    @staticmethod
    def send_404(start_response: Callable) -> bytes:
        stat, headers, res_body = DEFAULT_NOT_FOUND_ERROR._get_all_form()
        start_response(stat.value, headers)
        return res_body
    
    def seach_uris(self, endpoint: Type[Endpoint]) -> List[Uri_t]:
        return self._router.search_endpoint(endpoint)
    
    def route(self, *locs: Location, parcel: Parcel_t = (),
              version: Union[int, Tuple[int], None] = None
              ) -> Callable[[Type[Endpoint]], Type[Endpoint]]:

        def register_endpoint(endpoint: Type[Endpoint]) -> Type[Endpoint]:
            # parcel setting
            parcel_config = ParcelConfig(endpoint)
            parcel_config.set(self, parcel)
            
            # version setting
            ver_config = VersionConfig(endpoint)
            ver_config.set(self, version)
            
            # router setting
            _version = ver_config.get(self)
            if self._is_version_isnert and len(_version):
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
