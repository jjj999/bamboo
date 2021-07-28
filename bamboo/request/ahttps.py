import asyncio
import concurrent.futures
import ssl
import typing as t

from . import https
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
    context: t.Optional[ssl.SSLContext] = None,
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    eloop = asyncio.get_event_loop()
    return await eloop.run_in_executor(
        executor,
        https.request,
        uri,
        method,
        headers,
        body,
        json,
        query,
        timeout,
        blocksize,
        datacls,
        context,
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
    context: t.Optional[ssl.SSLContext] = None,
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the GET method on HTTPS.

    Note:
        Sometimes your specified arguments may cause security problems in
        communications with the function. It is strongly recommended to
        reference Python ssl module security considerations documents.
        Link: https://docs.python.org/3/library/ssl.html#ssl-security

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.
        context: SSLContext of your communication.
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        uri,
        HTTPMethods.GET,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls,
        context=context,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
        executor=executor,
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
    context: t.Optional[ssl.SSLContext] = None,
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the POST method on HTTPS.

    Note:
        Sometimes your specified arguments may cause security problems in
        communications with the function. It is strongly recommended to
        reference Python ssl module security considerations documents.
        Link: https://docs.python.org/3/library/ssl.html#ssl-security

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.
        context: SSLContext of your communication.
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        uri,
        HTTPMethods.POST,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls,
        context=context,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
        executor=executor,
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
    context: t.Optional[ssl.SSLContext] = None,
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the PUT method on HTTPS.

    Note:
        Sometimes your specified arguments may cause security problems in
        communications with the function. It is strongly recommended to
        reference Python ssl module security considerations documents.
        Link: https://docs.python.org/3/library/ssl.html#ssl-security

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.
        context: SSLContext of your communication.
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        uri,
        HTTPMethods.PUT,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls,
        context=context,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
        executor=executor,
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
    context: t.Optional[ssl.SSLContext] = None,
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the DELETE method on HTTPS.

    Note:
        Sometimes your specified arguments may cause security problems in
        communications with the function. It is strongly recommended to
        reference Python ssl module security considerations documents.
        Link: https://docs.python.org/3/library/ssl.html#ssl-security

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.
        context: SSLContext of your communication.
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        uri,
        HTTPMethods.DELETE,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls,
        context=context,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
        executor=executor,
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
    context: t.Optional[ssl.SSLContext] = None,
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the HEAD method on HTTPS.

    Note:
        Sometimes your specified arguments may cause security problems in
        communications with the function. It is strongly recommended to
        reference Python ssl module security considerations documents.
        Link: https://docs.python.org/3/library/ssl.html#ssl-security

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.
        context: SSLContext of your communication.
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        uri,
        HTTPMethods.HEAD,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls,
        context=context,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
        executor=executor,
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
    context: t.Optional[ssl.SSLContext] = None,
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the OPTIONS method on HTTPS.

    Note:
        Sometimes your specified arguments may cause security problems in
        communications with the function. It is strongly recommended to
        reference Python ssl module security considerations documents.
        Link: https://docs.python.org/3/library/ssl.html#ssl-security

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.
        context: SSLContext of your communication.
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        uri,
        HTTPMethods.OPTIONS,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls,
        context=context,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
        executor=executor,
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
    context: t.Optional[ssl.SSLContext] = None,
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the PATCH method on HTTPS.

    Note:
        Sometimes your specified arguments may cause security problems in
        communications with the function. It is strongly recommended to
        reference Python ssl module security considerations documents.
        Link: https://docs.python.org/3/library/ssl.html#ssl-security

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.
        context: SSLContext of your communication.
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        uri,
        HTTPMethods.PATCH,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls,
        context=context,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
        executor=executor,
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
    context: t.Optional[ssl.SSLContext] = None,
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the TRACE method on HTTPS.

    Note:
        Sometimes your specified arguments may cause security problems in
        communications with the function. It is strongly recommended to
        reference Python ssl module security considerations documents.
        Link: https://docs.python.org/3/library/ssl.html#ssl-security

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.
        context: SSLContext of your communication.
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        uri,
        HTTPMethods.TRACE,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls,
        context=context,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
        executor=executor,
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
    context: t.Optional[ssl.SSLContext] = None,
    use_proxy: t.Union[bool, t.Tuple[str, int]] = False,
    proxy_headers: t.Dict[str, str] = {},
    executor: t.Optional[concurrent.futures.Executor] = None,
) -> Response[ResponseData_t]:
    """Request with the CONNECT method on HTTPS.

    Note:
        Sometimes your specified arguments may cause security problems in
        communications with the function. It is strongly recommended to
        reference Python ssl module security considerations documents.
        Link: https://docs.python.org/3/library/ssl.html#ssl-security

    Args:
        uri: URI to be requested.
        headers: Request headers.
        body: Request body of bytes.
        json: Request body of JSON.
        query: Query parameters to be attached to the URI.
        timeout: Seconds waiting for the connection.
        blocksize: Block size of sending data.
        datacls: `ApiData` or its subclass to be attached from the response body.
        context: SSLContext of your communication.
        use_proxy: Address of a proxy server or whether the connection
            uses a proxy based on the environment variables.
        proxy_headers: Headers to be used on the request to the proxy.
        executor: Executor in which the request will be conducted.

    Returns:
        Response object generated with the response.
    """
    return await request(
        uri,
        HTTPMethods.CONNECT,
        headers=headers,
        body=body,
        json=json,
        query=query,
        timeout=timeout,
        blocksize=blocksize,
        datacls=datacls,
        context=context,
        use_proxy=use_proxy,
        proxy_headers=proxy_headers,
        executor=executor,
    )
