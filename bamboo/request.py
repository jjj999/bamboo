
from __future__ import annotations
import http.client as client
from json import dumps
from typing import Any, Dict, Generic, List, Optional, TypeVar, Type
from urllib.parse import parse_qs, urlparse

from bamboo.api import ApiData  
from bamboo.base import HTTPMethods
from bamboo.util.convert import unparse_qs
from bamboo.util.deco import cached_property


ResponseData_t = TypeVar("ResponseData_t")


class Response(Generic[ResponseData_t]):
    
    def __init__(self, 
                 res: client.HTTPResponse, 
                 datacls: Type[ResponseData_t] = ApiData
                 ) -> None:
        self._res = res
        self._datacls = datacls

    @property
    def headers(self) -> client.HTTPMessage:
        return self._res.msg
    
    def get_header(self, key: str) -> Optional[str]:
        return self._res.getheader(key)
    
    @property
    def url(self) -> str:
        return self._res.geturl()
    
    @property
    def status(self) -> int:
        return self._res.status
    
    @property
    def version(self) -> int:
        return self._res.version
    
    @property
    def ok(self) -> bool:
        status = self.status
        if 200 <= status < 300:
            return True
        return False
    
    @property
    def is_closed(self) -> bool:
        return self._res.closed
    
    @property
    def fileno(self) -> int:
        return self._res.fileno()
    
    @property
    def content_length(self) -> Optional[int]:
        length = self.get_header("Content-Length")
        if length is not None:
            return int(length)
        return None
    
    @cached_property
    def body(self) -> bytes:
        return self._res.read(self.content_length)
    
    def attach(self) -> ResponseData_t:
        return self._datacls(self.body)


class _Schemes:
    
    HTTP = "http"
    HTTPS = "https"
    
    _schemes = set((HTTP, HTTPS))
    __instance = None
    
    def __new__(cls) -> _Schemes:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def __iter__(self):
        return iter(self._schemes)
    
    def __contains__(self, item: str):
        return item in self._schemes


Schemes = _Schemes()


def http_request(uri: str, 
                 method: str, 
                 headers: Dict[str, str] = {},
                 body: Optional[bytes] = None, 
                 json: Optional[Dict[str, Any]] = None,
                 query: Dict[str, List[str]] = {},
                 timeout: Optional[float] = None, 
                 blocksize: int = 8192,
                 datacls: Type[ResponseData_t] = ApiData
                 ) -> Response[ResponseData_t]:
    # method management
    method = method.upper()
    if method not in HTTPMethods:
        raise ValueError(f"Specified method '{method}' is not available.")
    
    # body management
    if body and json:
        raise ValueError("Request body is specified both 'body' and 'json'.")
    if json:
        body = dumps(json)
    
    parsed_uri = urlparse(uri)
    if parsed_uri.scheme != Schemes.HTTP:
        raise ValueError(f"Scheme of specified uri '{parsed_uri.scheme}' "
                         "is not available. Use HTTP.")

    # port management
    port = parsed_uri.port
    if not port:
        port = None
        
    # query management
    query_included = parse_qs(parsed_uri.query)
    query_included.update(query)
    query = unparse_qs(query_included)
    
    # path management
    path = parsed_uri.path
    if len(query):
        path = "?".join((path, query))
    
    conn = client.HTTPConnection(parsed_uri.hostname, port=port,
                                 timeout=timeout, blocksize=blocksize)
    conn.request(method, path, body=body, headers=headers)
    _res = conn.getresponse()
    return Response(_res, datacls=datacls)


def http_get(uri: str, 
             headers: Dict[str, str] = {}, 
             body: Optional[bytes] = None,
             json: Optional[Dict[str, Any]] = None,
             query: Dict[str, List[str]] = {},
             timeout: Optional[float] = None, 
             blocksize: int = 8192,
             datacls: Type[ResponseData_t] = ApiData
             ) -> Response[ResponseData_t]:
    return http_request(uri, HTTPMethods.GET, headers=headers, body=body,
                        json=json, query=query, timeout=timeout,
                        blocksize=blocksize, datacls=datacls)


def http_post(uri: str, 
              headers: Dict[str, str] = {},
              body: Optional[bytes] = None,
              json: Optional[Dict[str, Any]] = None,
              query: Dict[str, List[str]] = {},
              timeout: Optional[float] = None, 
              blocksize: int = 8192,
              datacls: Type[ResponseData_t] = ApiData
              ) -> Response[ResponseData_t]:
    return http_request(uri, HTTPMethods.POST, headers=headers, body=body,
                        json=json, query=query, timeout=timeout,
                        blocksize=blocksize, datacls=datacls)


def http_put(uri: str, 
             headers: Dict[str, str] = {},
             body: Optional[bytes] = None,
             json: Optional[Dict[str, Any]] = None,
             query: Dict[str, List[str]] = {},
             timeout: Optional[float] = None, 
             blocksize: int = 8192,
             datacls: Type[ResponseData_t] = ApiData
             ) -> Response[ResponseData_t]:
    return http_request(uri, HTTPMethods.PUT, headers=headers, body=body,
                        json=json, query=query, timeout=timeout,
                        blocksize=blocksize, datacls=datacls)


def http_delete(uri: str, 
                headers: Dict[str, str] = {},
                body: Optional[bytes] = None,
                json: Optional[Dict[str, Any]] = None,
                query: Dict[str, List[str]] = {},
                timeout: Optional[float] = None, 
                blocksize: int = 8192,
                datacls: Type[ResponseData_t] = ApiData
                ) -> Response[ResponseData_t]:
    return http_request(uri, HTTPMethods.DELETE, headers=headers, body=body,
                        json=json, query=query, timeout=timeout,
                        blocksize=blocksize, datacls=datacls)


def http_head(uri: str,
              headers: Dict[str, str] = {},
              body: Optional[bytes] = None,
              json: Optional[Dict[str, Any]] = None,
              query: Dict[str, List[str]] = {},
              timeout: Optional[float] = None, 
              blocksize: int = 8192,
              datacls: Type[ResponseData_t] = ApiData
              ) -> Response[ResponseData_t]:
    return http_request(uri, HTTPMethods.HEAD, headers=headers, body=body,
                        json=json, query=query, timeout=timeout,
                        blocksize=blocksize, datacls=datacls)


def http_options(uri: str, 
                 headers: Dict[str, str] = {}, 
                 body: Optional[bytes] = None,
                 json: Optional[Dict[str, Any]] = None, 
                 query: Dict[str, List[str]] = {},
                 timeout: Optional[float] = None, 
                 blocksize: int = 8192,
                 datacls: Type[ResponseData_t] = ApiData
                 ) -> Response[ResponseData_t]:
    return http_request(uri, HTTPMethods.OPTIONS, headers=headers, body=body,
                        json=json, query=query, timeout=timeout,
                        blocksize=blocksize, datacls=datacls)


def https_request(uri: str, 
                  method: str, 
                  headers: Dict[str, str] = {},
                  body: Optional[bytes] = None, 
                  query: Dict[str, List[str]] = None
                  ) -> Response:
    pass


def https_get():
    pass


def https_post():
    pass


def https_put():
    pass


def https_delete():
    pass


def https_head():
    pass


def https_options():
    pass
