
from __future__ import annotations
import http.client as client
from typing import Generic, Optional, Type

from bamboo.api import BinaryApiData
from bamboo.base import ContentType
from bamboo.request import ResponseData_t
from bamboo.util.deco import cached_property


class Response(Generic[ResponseData_t]):
    
    def __init__(self, 
                 res: client.HTTPResponse, 
                 datacls: Type[ResponseData_t] = BinaryApiData
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
    
    def attach(self, 
               datacls: Optional[Type[ResponseData_t]] = None
               ) -> ResponseData_t:
        content_type_raw = self.get_header("Content-Type")
        if content_type_raw:
            content_type = ContentType.parse(content_type_raw)
        else:
            content_type = ContentType()

        if datacls is None:
            return self._datacls(self.body, content_type)
        else:
            return datacls(self.body, content_type)
    