
from __future__ import annotations
from http import client
from typing import Any, Dict, List, Optional, Type

from bamboo.api import BinaryApiData  
from bamboo.base import HTTPMethods
from bamboo.request import ResponseData_t, Schemes
from bamboo.request.request_form import get_http_request_form
from bamboo.request.response import Response


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
    form = get_http_request_form(Schemes.HTTP, uri, method, headers=headers,
                          body=body, json=json, query=query)
    conn = client.HTTPConnection(form.host, port=form.port,
                                 timeout=timeout, blocksize=blocksize)
    conn.request(form.method, form.uri, body=form.body, headers=form.headers)
    _res = conn.getresponse()
    return Response(conn, _res, datacls=datacls)


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
