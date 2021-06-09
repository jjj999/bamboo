from __future__ import annotations
import http.client
import typing as t

from ..api.base import BinaryApiData
from ..api.json import JsonApiData
from ..http import HTTPMethods
from ..request import ResponseData_t, Schemes
from ..request.request_form import get_http_request_form
from ..request.response import Response


__all__ = [
    "connect",
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "trace",
]


def request(
    uri: str,
    method: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData] = None,
    query: t.Dict[str, t.List[str]] = {},
    timeout: t.Optional[float] = None,
    blocksize: int = 8192,
    datacls: t.Type[ResponseData_t] = BinaryApiData,
) -> Response[ResponseData_t]:
    form = get_http_request_form(
        Schemes.HTTP,
        uri,
        method,
        headers=headers,
        body=body,
        json=json,
        query=query
    )
    conn = http.client.HTTPConnection(
        form.host,
        port=form.port,
        timeout=timeout,
        blocksize=blocksize
    )
    conn.request(form.method, form.uri, body=form.body, headers=form.headers)
    _res = conn.getresponse()
    return Response(conn, _res, datacls=datacls)


def get(
    uri: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData] = None,
    query: t.Dict[str, t.List[str]] = {},
    timeout: t.Optional[float] = None,
    blocksize: int = 8192,
    datacls: t.Type[ResponseData_t] = BinaryApiData,
) -> Response[ResponseData_t]:
    """Request with the GET method on HTTP.

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.

    Returns:
        Response object generated with the response.
    """
    return request(
        uri,
        HTTPMethods.GET,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls
    )


def post(
    uri: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData] = None,
    query: t.Dict[str, t.List[str]] = {},
    timeout: t.Optional[float] = None,
    blocksize: int = 8192,
    datacls: t.Type[ResponseData_t] = BinaryApiData,
) -> Response[ResponseData_t]:
    """Request with the POST method on HTTP.

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.

    Returns:
        Response object generated with the response.
    """
    return request(
        uri,
        HTTPMethods.POST,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls
    )


def put(
    uri: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData] = None,
    query: t.Dict[str, t.List[str]] = {},
    timeout: t.Optional[float] = None,
    blocksize: int = 8192,
    datacls: t.Type[ResponseData_t] = BinaryApiData,
) -> Response[ResponseData_t]:
    """Request with the PUT method on HTTP.

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.

    Returns:
        Response object generated with the response.
    """
    return request(
        uri,
        HTTPMethods.PUT,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls
    )


def delete(
    uri: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData] = None,
    query: t.Dict[str, t.List[str]] = {},
    timeout: t.Optional[float] = None,
    blocksize: int = 8192,
    datacls: t.Type[ResponseData_t] = BinaryApiData,
) -> Response[ResponseData_t]:
    """Request with the DELETE method on HTTP.

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.

    Returns:
        Response object generated with the response.
    """
    return request(
        uri,
        HTTPMethods.DELETE,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls
    )


def head(
    uri: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData] = None,
    query: t.Dict[str, t.List[str]] = {},
    timeout: t.Optional[float] = None,
    blocksize: int = 8192,
    datacls: t.Type[ResponseData_t] = BinaryApiData,
) -> Response[ResponseData_t]:
    """Request with the HEAD method on HTTP.

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.

    Returns:
        Response object generated with the response.
    """
    return request(
        uri,
        HTTPMethods.HEAD,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls
    )


def options(
    uri: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData] = None,
    query: t.Dict[str, t.List[str]] = {},
    timeout: t.Optional[float] = None,
    blocksize: int = 8192,
    datacls: t.Type[ResponseData_t] = BinaryApiData,
) -> Response[ResponseData_t]:
    """Request with the OPTIONS method on HTTP.

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.

    Returns:
        Response object generated with the response.
    """
    return request(
        uri,
        HTTPMethods.OPTIONS,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls
    )


def patch(
    uri: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData] = None,
    query: t.Dict[str, t.List[str]] = {},
    timeout: t.Optional[float] = None,
    blocksize: int = 8192,
    datacls: t.Type[ResponseData_t] = BinaryApiData,
) -> Response[ResponseData_t]:
    """Request with the PATCH method on HTTP.

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.

    Returns:
        Response object generated with the response.
    """
    return request(
        uri,
        HTTPMethods.PATCH,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls
    )


def trace(
    uri: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData] = None,
    query: t.Dict[str, t.List[str]] = {},
    timeout: t.Optional[float] = None,
    blocksize: int = 8192,
    datacls: t.Type[ResponseData_t] = BinaryApiData,
) -> Response[ResponseData_t]:
    """Request with the TRACE method on HTTP.

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.

    Returns:
        Response object generated with the response.
    """
    return request(
        uri,
        HTTPMethods.TRACE,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls
    )


def connect(
    uri: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData] = None,
    query: t.Dict[str, t.List[str]] = {},
    timeout: t.Optional[float] = None,
    blocksize: int = 8192,
    datacls: t.Type[ResponseData_t] = BinaryApiData,
) -> Response[ResponseData_t]:
    """Request with the CONNECT method on HTTP.

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.

    Returns:
        Response object generated with the response.
    """
    return request(
        uri,
        HTTPMethods.CONNECT,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls
    )
