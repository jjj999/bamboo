from __future__ import annotations
import dataclasses
import json as js
import typing as t
from urllib.parse import parse_qs, urlparse

from ..api.json import JsonApiData
from ..http import HTTPMethods, MediaTypes
from ..util.convert import unparse_qs


__all__ = []


@dataclasses.dataclass
class HTTPRequestForm:

    host: str
    port: t.Optional[int]
    uri: str
    method: str
    headers: t.Dict[str, str]
    body: t.Optional[bytes]


def get_http_request_form(
    scheme: str,
    uri: str,
    method: str,
    headers: t.Dict[str, str] = {},
    body: t.Optional[bytes] = None,
    json: t.Union[t.Dict[str, t.Any], JsonApiData, None] = None,
    query: t.Dict[str, t.List[str]] = {}
) -> HTTPRequestForm:
    # method management
    method = method.upper()
    if method not in HTTPMethods:
        raise ValueError(f"Specified method '{method}' is not available.")

    # body management
    if body and json:
        raise ValueError("Request body is specified both 'body' and 'json'.")
    if body:
        if "Content-Type" not in headers:
            headers["Content-Type"] = MediaTypes.plain
    if json:
        if isinstance(json, JsonApiData):
            json = json.dict
        body = js.dumps(json)
        if "Content-Type" not in headers:
            headers["Content-Type"] = MediaTypes.json

    parsed_uri = urlparse(uri)
    if parsed_uri.scheme != scheme:
        raise ValueError(
            f"Scheme of specified uri '{parsed_uri.scheme}' is "
            "not available. Use HTTP."
        )

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

    return HTTPRequestForm(
        parsed_uri.hostname,
        port,
        path,
        method,
        headers,
        body
    )
