
from __future__ import annotations
import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from urllib.parse import parse_qs

from bamboo.base import HTTPMethods, HTTPStatus
from bamboo.error import ErrInfoBase


class AlreadyBodySetError(Exception):
    """Raised if response body has already been set."""
    pass


class Endpoint:
    
    response_methods: Tuple[str]
    
    @classmethod
    def _find_response_methods(cls) -> Tuple[str]:
        result = []
        for name, _ in inspect.getmembers(cls):
            if len(name) < 3:
                continue
            if name[:3] == "do_" and name[3:] in HTTPMethods:
                result.append(name[3:])
        return tuple(result)
    
    def __init_subclass__(cls) -> None:
        cls.response_methods = cls._find_response_methods()
        
    def __init__(self, environ: Dict[str, Any], *parcel) -> None:
        self._environ = environ
        self._req_body = None
        self._status: Optional[HTTPStatus] = None
        self._headers: List[Tuple[str, str]] = []
        self._res_body: bytes = b""

        self.setup(*parcel)
        
    @classmethod
    def _get_response_method(cls, method: str) -> Optional[Callable[[Endpoint, Tuple[Any, ...]], None]]:
        mname = "do_" + method
        if hasattr(cls, mname):
            return getattr(cls, mname)
        return None
        
    def _recv_body_secure(self) -> bytes:
        body = self._environ.get("wsgi.input").read(self.content_length)
        return body
        
    def setup(self, *parcel) -> None:
        pass
    
    @property
    def client_ip(self) -> str:
        pass
        
    def get_header(self, key: str) -> str:
        key = "HTTP_" + key.replace("-", "_").upper()
        return self._environ.get(key)
    
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
    
    def add_header(self, name: str, value: str, **params: str) -> None:
        params = [f'; {key}="{val}"' for key, val in params.items()]
        params = "".join(params)
        self._headers.append((name, value + params))
    
    def add_headers(self, headers: Dict[str, str]) -> None:
        for key, val in headers.items():
            self._headers.append((key, val))
    
    def _check_already_body_set(self) -> None:
        if self._res_body:
            raise AlreadyBodySetError("Response body has already been set.")
    
    def send_body(self, body: bytes = b"", status: HTTPStatus = HTTPStatus.OK) -> None:
        self._check_already_body_set()

        self._status = status
        self._res_body = body
    
    def send_json(self, body: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK,
                  encoding: str = "utf-8") -> None:
        self._check_already_body_set()
        self._status = status
        self._res_body = json.dumps(body).encode(encoding=encoding)
    
    def send_err(self, err: Type[ErrInfoBase]) -> None:
        self._check_already_body_set()

        self._status = err.http_status
        self._res_body = err.get_body()
