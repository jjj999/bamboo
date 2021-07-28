import asyncio
import concurrent.futures
import typing as t

from . import http
from ..api.base import BinaryApiData
from ..api.json import JsonApiData
from ..http import HTTPMethods
from ..request import ResponseData_t, Response


async def request(
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
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    eloop = asyncio.get_event_loop()
    return await eloop.run_in_executor(
        executor,
        http.request,
        uri,
        method,
        headers,
        body,
        json,
        query,
        timeout,
        blocksize,
        datacls,
        use_proxy,
        proxy_headers,
    )

async def get(
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
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the GET method on HTTP asynchronously.

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
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        executor,
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


async def post(
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
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the POST method on HTTP asynchronously.

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
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        executor,
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


async def put(
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
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the PUT method on HTTP asynchronously.

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
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        executor,
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


async def delete(
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
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the DELETE method on HTTP asynchronously.

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
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        executor,
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


async def head(
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
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the HEAD method on HTTP asynchronously.

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
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        executor,
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


async def options(
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
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the OPTIONS method on HTTP asynchronously.

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
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        executor,
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


async def patch(
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
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the PATCH method on HTTP asynchronously.

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
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        executor,
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


async def trace(
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
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the TRACE method on HTTP asynchronously.

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
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        executor,
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


async def connect(
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
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the CONNECT method on HTTP asynchronously.

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
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        executor,
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
