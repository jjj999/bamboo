
from __future__ import annotations
import http.client as client
from json import dumps
from typing import Any, Dict, List, Optional, Type
from urllib.parse import parse_qs, urlparse

from bamboo.api import BinaryApiData  
from bamboo.base import HTTPMethods, MediaTypes
from bamboo.request import ResponseData_t, Schemes
from bamboo.request.response import Response
from bamboo.util.convert import unparse_qs


def request(uri: str, 
            method: str, 
            headers: Dict[str, str] = {},
            body: Optional[bytes] = None, 
            json: Optional[Dict[str, Any]] = None,
            query: Dict[str, List[str]] = {},
            timeout: Optional[float] = None, 
            blocksize: int = 8192,
            datacls: Type[ResponseData_t] = BinaryApiData
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
        if "Content-Type" not in headers:
            headers["Content-Type"] = MediaTypes.json
    
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


def get(uri: str, 
        headers: Dict[str, str] = {}, 
        body: Optional[bytes] = None,
        json: Optional[Dict[str, Any]] = None,
        query: Dict[str, List[str]] = {},
        timeout: Optional[float] = None, 
        blocksize: int = 8192,
        datacls: Type[ResponseData_t] = BinaryApiData
        ) -> Response[ResponseData_t]:
    return request(uri, HTTPMethods.GET, headers=headers, body=body,
                   json=json, query=query, timeout=timeout,
                   blocksize=blocksize, datacls=datacls)


def post(uri: str, 
        headers: Dict[str, str] = {},
        body: Optional[bytes] = None,
        json: Optional[Dict[str, Any]] = None,
        query: Dict[str, List[str]] = {},
        timeout: Optional[float] = None, 
        blocksize: int = 8192,
        datacls: Type[ResponseData_t] = BinaryApiData
        ) -> Response[ResponseData_t]:
    return request(uri, HTTPMethods.POST, headers=headers, body=body,
                   json=json, query=query, timeout=timeout,
                   blocksize=blocksize, datacls=datacls)


def put(uri: str, 
        headers: Dict[str, str] = {},
        body: Optional[bytes] = None,
        json: Optional[Dict[str, Any]] = None,
        query: Dict[str, List[str]] = {},
        timeout: Optional[float] = None, 
        blocksize: int = 8192,
        datacls: Type[ResponseData_t] = BinaryApiData
        ) -> Response[ResponseData_t]:
    return request(uri, HTTPMethods.PUT, headers=headers, body=body,
                   json=json, query=query, timeout=timeout,
                   blocksize=blocksize, datacls=datacls)


def delete(uri: str, 
           headers: Dict[str, str] = {},
           body: Optional[bytes] = None,
           json: Optional[Dict[str, Any]] = None,
           query: Dict[str, List[str]] = {},
           timeout: Optional[float] = None, 
           blocksize: int = 8192,
           datacls: Type[ResponseData_t] = BinaryApiData
           ) -> Response[ResponseData_t]:
    return request(uri, HTTPMethods.DELETE, headers=headers, body=body,
                   json=json, query=query, timeout=timeout,
                   blocksize=blocksize, datacls=datacls)


def head(uri: str,
         headers: Dict[str, str] = {},
         body: Optional[bytes] = None,
         json: Optional[Dict[str, Any]] = None,
         query: Dict[str, List[str]] = {},
         timeout: Optional[float] = None, 
         blocksize: int = 8192,
         datacls: Type[ResponseData_t] = BinaryApiData
         ) -> Response[ResponseData_t]:
    return request(uri, HTTPMethods.HEAD, headers=headers, body=body,
                   json=json, query=query, timeout=timeout,
                   blocksize=blocksize, datacls=datacls)


def options(uri: str, 
            headers: Dict[str, str] = {}, 
            body: Optional[bytes] = None,
            json: Optional[Dict[str, Any]] = None, 
            query: Dict[str, List[str]] = {},
            timeout: Optional[float] = None, 
            blocksize: int = 8192,
            datacls: Type[ResponseData_t] = BinaryApiData
            ) -> Response[ResponseData_t]:
    return request(uri, HTTPMethods.OPTIONS, headers=headers, body=body,
                   json=json, query=query, timeout=timeout,
                   blocksize=blocksize, datacls=datacls)
