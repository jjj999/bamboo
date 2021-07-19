from __future__ import annotations
import http.client
import typing as t

from . import _get_http_proxy_env, _parse_proxy_netloc
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
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
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

    if use_proxy:
        _http_proxy_env = _get_http_proxy_env()
        if isinstance(use_proxy, tuple):
            proxy_host, proxy_port = use_proxy
        elif _http_proxy_env:
            proxy_host, proxy_port = _parse_proxy_netloc(_http_proxy_env)
        else:
            raise ConnectionAbortedError(
                "Specified 'use_proxy' as True, but any proxy "
                "settings were not found."
            )

        conn = http.client.HTTPConnection(
            proxy_host,
            port=proxy_port,
            timeout=timeout,
            blocksize=blocksize,
        )
        conn.set_tunnel(form.host, port=form.port, headers=proxy_headers)
    else:
        conn = http.client.HTTPConnection(
            form.host,
            port=form.port,
            timeout=timeout,
            blocksize=blocksize,
        )

    conn.request(form.method, form.path, body=form.body, headers=form.headers)
    _res = conn.getresponse()
    return Response(conn, _res, form.uri, datacls=datacls)


def get(
    uri: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData] = None,
    query: t.Dict[str, t.List[str]] = {},
    timeout: t.Optional[float] = None,
    blocksize: int = 8192,
    datacls: t.Type[ResponseData_t] = BinaryApiData,
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
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
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.

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
        datacls=datacls,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
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
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
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
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.

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
        datacls=datacls,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
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
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
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
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.

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
        datacls=datacls,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
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
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
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
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.

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
        datacls=datacls,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
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
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
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
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.

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
        datacls=datacls,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
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
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
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
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.

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
        datacls=datacls,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
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
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
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
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.

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
        datacls=datacls,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
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
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
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
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.

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
        datacls=datacls,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
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
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
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
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.

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
        datacls=datacls,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
    )
