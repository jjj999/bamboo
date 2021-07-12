import unittest

from bamboo import (
    ASGIApp,
    ASGIHTTPEndpoint,
    ErrInfo,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.request import http

from .. import get_log_name
from ..asgi_util import ASGIServerForm, ASGITestExecutor


app_asgi = ASGIApp()
app_wsgi = WSGIApp()
PATH_ASGI_SERVER_LOG = get_log_name(__file__, "asgi")
PATH_WSGI_SERVER_LOG = get_log_name(__file__, "wsgi")


class MockErrInfo(ErrInfo):

    inheritted_headers = {
        "X-Bamboo-AAA",
        "X-Bamboo-BBB",
    }


@app_asgi.route()
class TestASGIHTTPEndpoint(ASGIHTTPEndpoint):

    async def do_GET(self) -> None:
        self.add_header("X-Bamboo-AAA", "AAA")
        self.add_header("x-bamboo-bbb", "BBB")
        raise MockErrInfo()


@app_wsgi.route()
class TestWSGIHTTPEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        self.add_header("X-Bamboo-AAA", "AAA")
        self.add_header("x-bamboo-bbb", "BBB")
        raise MockErrInfo()


class TestErrInfo(unittest.TestCase):

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
        with http.get(self.uri_asgi) as res:
            self.assertFalse(res.ok)
            print(res.headers)
            self.assertIn("X-Bamboo-AAA", res.headers)
            self.assertIn("X-Bamboo-BBB", res.headers)

    def test_wsgi(self) -> None:
        with http.get(self.uri_wsgi) as res:
            self.assertFalse(res.ok)
            print(res.headers)
            self.assertIn("X-Bamboo-AAA", res.headers)
            self.assertIn("X-Bamboo-BBB", res.headers)


if __name__ == "__main__":
    unittest.main()
