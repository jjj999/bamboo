import unittest

from bamboo import (
    ASGIApp,
    ASGIHTTPEndpoint,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.request import http
from bamboo.sticky.http import has_query_of
from bamboo.util.string import rand_string

from ... import get_log_name
from ...asgi_util import ASGIServerForm, ASGITestExecutor


app_asgi = ASGIApp()
app_wsgi = WSGIApp()
PATH_ASGI_SERVER_LOG = get_log_name(__file__, "asgi")
PATH_WSGI_SERVER_LOG = get_log_name(__file__, "wsgi")
RANDOM_QUERIES = [(rand_string(10), rand_string(10)) for _ in range(10)]


@app_asgi.route()
class TestASGIHTTPEndpoint(ASGIHTTPEndpoint):

    @has_query_of(RANDOM_QUERIES[0][0])
    @has_query_of(RANDOM_QUERIES[1][0])
    @has_query_of(RANDOM_QUERIES[2][0])
    @has_query_of(RANDOM_QUERIES[3][0])
    @has_query_of(RANDOM_QUERIES[4][0])
    @has_query_of(RANDOM_QUERIES[5][0])
    @has_query_of(RANDOM_QUERIES[6][0])
    @has_query_of(RANDOM_QUERIES[7][0])
    @has_query_of(RANDOM_QUERIES[8][0])
    @has_query_of(RANDOM_QUERIES[9][0])
    async def do_GET(
        self,
        header0: str,
        header1: str,
        header2: str,
        header3: str,
        header4: str,
        header5: str,
        header6: str,
        header7: str,
        header8: str,
        header9: str,
    ) -> None:
        self.send_json({
            "headers": [
                header0,
                header1,
                header2,
                header3,
                header4,
                header5,
                header6,
                header7,
                header8,
                header9,
            ]
        })


@app_wsgi.route()
class TestWSGIEndpoint(WSGIEndpoint):

    @has_query_of(RANDOM_QUERIES[0][0])
    @has_query_of(RANDOM_QUERIES[1][0])
    @has_query_of(RANDOM_QUERIES[2][0])
    @has_query_of(RANDOM_QUERIES[3][0])
    @has_query_of(RANDOM_QUERIES[4][0])
    @has_query_of(RANDOM_QUERIES[5][0])
    @has_query_of(RANDOM_QUERIES[6][0])
    @has_query_of(RANDOM_QUERIES[7][0])
    @has_query_of(RANDOM_QUERIES[8][0])
    @has_query_of(RANDOM_QUERIES[9][0])
    def do_GET(
        self,
        header0: str,
        header1: str,
        header2: str,
        header3: str,
        header4: str,
        header5: str,
        header6: str,
        header7: str,
        header8: str,
        header9: str,
    ) -> None:
        self.send_json({
            "headers": [
                header0,
                header1,
                header2,
                header3,
                header4,
                header5,
                header6,
                header7,
                header8,
                header9,
            ]
        })


class TestStickyHasQueryOf(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        form_asgi = ASGIServerForm("", 8000, app_asgi, PATH_ASGI_SERVER_LOG)
        form_wsgi = WSGIServerForm("", 8001, app_wsgi, PATH_WSGI_SERVER_LOG)
        cls.executor_asgi = ASGITestExecutor(form_asgi).start_serve()
        cls.executor_wsgi = WSGITestExecutor(form_wsgi).start_serve()
        cls.uri_asgi = "http://localhost:8000"
        cls.uri_wsgi = "http://localhost:8001"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor_asgi.close()
        cls.executor_wsgi.close()

    def test_asgi(self) -> None:
        with http.get(
            self.uri_asgi,
            query={name: [value] for name, value in RANDOM_QUERIES},
        ) as res:
            self.assertTrue(res.ok)

    def test_wsgi(self) -> None:
        with http.get(
            self.uri_wsgi,
            query={name: [value] for name, value in RANDOM_QUERIES},
        ) as res:
            self.assertTrue(res.ok)


if __name__ == "__main__":
    unittest.main()
