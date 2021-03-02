
from __future__ import annotations

from dataclasses import dataclass
from json import dumps
from typing import (
    Any,
    Dict,
    List,
    Optional,
)
from urllib.parse import parse_qs, urlparse

from bamboo.base import HTTPMethods, MediaTypes
from bamboo.util.convert import unparse_qs


__all__ = []


@dataclass
class HTTPRequestForm:

    host: str
    port: Optional[int]
    uri: str
    method: str
    headers: Dict[str, str]
    body: Optional[bytes]


def get_http_request_form(
    scheme: str,
    uri: str,
    method: str,
    headers: Dict[str, str] = {},
    body: Optional[bytes] = None,
    json: Optional[Dict[str, Any]] = None,
    query: Dict[str, List[str]] = {}
) -> HTTPRequestForm:
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
