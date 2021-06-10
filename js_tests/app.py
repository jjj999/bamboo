import typing as t

from bamboo import (
    HTTPStatus,
    WSGIApp,
    WSGIEndpoint,
)
from bamboo.api import JsonApiData
from bamboo.sticky.http import (
    SetCookieValue_t,
    add_preflight,
    allow_simple_access_control,
    data_format,
    has_header_of,
    set_cache_control,
    set_cookie,
)
from bamboo.util.deco import class_property
from bamboo.util.string import rand_string


js_tests_app = WSGIApp()


@js_tests_app.route("cookie")
class TestCookieEndpoint(WSGIEndpoint):

    _last_cookie: t.Optional[str] = None

    @class_property
    def last_cookie(cls) -> t.Optional[str]:
        return cls._last_cookie

    @last_cookie.setter
    def last_cookie(cls, cookie: str) -> None:
        cls._last_cookie = cookie

    @allow_simple_access_control(
        "http://localhost:8000",
        allow_credentials=True,
    )
    def pre_GET(self, origin: str) -> None:
        assert origin == "http://localhost:8000"

    @set_cache_control(no_cache=True)
    @set_cookie("bamboo", secure=False)
    @has_header_of("Cookie")
    def do_GET(
        self,
        cookie: t.Optional[str],
        set_cookie_val: SetCookieValue_t,
    ) -> None:
        next_cookie = rand_string(2048)
        set_cookie_val(self, next_cookie)
        self.last_cookie = next_cookie
        self.send_body(b"Hello, Client!")


@js_tests_app.route("cors", "simple-request")
class TestCORSSimpleRequestEndpoint(WSGIEndpoint):

    @set_cache_control(no_cache=True)
    @allow_simple_access_control()
    def do_GET(self, origin: str) -> None:
        assert origin == "http://localhost:8000"
        self.send_body(b"Hello, Client!")


class TestPreFlightRequest(JsonApiData):

    account_id: str
    email_addr: str
    age: int


@js_tests_app.route("cors", "preflight")
@add_preflight(
    allow_methods=["POST"],
    allow_origins=["http://localhost:8000"],
)
class TestCORSPreFlightEndpoint(WSGIEndpoint):


    @set_cache_control(no_cache=True)
    @data_format(input=TestPreFlightRequest, output=None)
    def do_POST(self, req: TestPreFlightRequest, origin: str) -> None:
        assert req.account_id == "hogehoge"
        assert origin == "http://localhost:8000"

        self.send_only_status(HTTPStatus.OK)
