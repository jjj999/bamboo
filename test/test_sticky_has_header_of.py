import unittest

from bamboo import (
    ASGIHTTPApp,
    ASGIHTTPEndpoint,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.request import http
from bamboo.sticky.http import has_header_of
from bamboo.util.string import rand_string

from . import get_log_name
from .asgi_util import ASGIHTTPServerForm, ASGIHTTPTestExecutor


app_asgi = ASGIHTTPApp()
app_wsgi = WSGIApp()
PATH_ASGI_SERVER_LOG = get_log_name(__file__, "asgi")
PATH_WSGI_SERVER_LOG = get_log_name(__file__, "wsgi")
RANDOM_HEADERS = [(rand_string(10), rand_string(10)) for _ in range(10)]


@app_asgi.route()
class TestASGIHTTPEndpoint(ASGIHTTPEndpoint):

    @has_header_of(RANDOM_HEADERS[0][0])
    @has_header_of(RANDOM_HEADERS[1][0])
    @has_header_of(RANDOM_HEADERS[2][0])
    @has_header_of(RANDOM_HEADERS[3][0])
    @has_header_of(RANDOM_HEADERS[4][0])
    @has_header_of(RANDOM_HEADERS[5][0])
    @has_header_of(RANDOM_HEADERS[6][0])
    @has_header_of(RANDOM_HEADERS[7][0])
    @has_header_of(RANDOM_HEADERS[8][0])
    @has_header_of(RANDOM_HEADERS[9][0])
    async def do_GET(self) -> None:
        self.send_only_status()


@app_wsgi.route()
class TestWSGIEndpoint(WSGIEndpoint):

    @has_header_of(RANDOM_HEADERS[0][0])
    @has_header_of(RANDOM_HEADERS[1][0])
    @has_header_of(RANDOM_HEADERS[2][0])
    @has_header_of(RANDOM_HEADERS[3][0])
    @has_header_of(RANDOM_HEADERS[4][0])
    @has_header_of(RANDOM_HEADERS[5][0])
    @has_header_of(RANDOM_HEADERS[6][0])
    @has_header_of(RANDOM_HEADERS[7][0])
    @has_header_of(RANDOM_HEADERS[8][0])
    @has_header_of(RANDOM_HEADERS[9][0])
    def do_GET(self) -> None:
        self.send_only_status()


class TestStickyHasHeaderOf(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        form_asgi = ASGIHTTPServerForm("", 8000, app_asgi, PATH_ASGI_SERVER_LOG)
        form_wsgi = WSGIServerForm("", 8001, app_wsgi, PATH_WSGI_SERVER_LOG)
        cls.executor_asgi = ASGIHTTPTestExecutor(form_asgi).start_serve()
        cls.executor_wsgi = WSGITestExecutor(form_wsgi).start_serve()
        cls.uri_asgi = "http://localhost:8000"
        cls.uri_wsgi = "http://localhost:8001"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor_asgi.close()
        cls.executor_wsgi.close()

    def test_asgi(self):
        with http.get(self.uri_asgi, headers=dict(RANDOM_HEADERS)) as res:
            self.assertTrue(res.ok)

    def test_wsgi(self):
        with http.get(self.uri_wsgi, headers=dict(RANDOM_HEADERS)) as res:
            self.assertTrue(res.ok)


if __name__ == "__main__":
    unittest.main()
