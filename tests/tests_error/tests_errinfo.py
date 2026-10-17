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

from .. import get_log_name, get_unused_ports
from ..asgi_util import ASGIServerForm, ASGITestExecutor


app_asgi = ASGIApp()
app_wsgi = WSGIApp()
PATH_ASGI_SERVER_LOG = get_log_name(__file__, "asgi")
PATH_WSGI_SERVER_LOG = get_log_name(__file__, "wsgi")
PORT_ASGI = PORT_WSGI = 0


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
        global PORT_ASGI, PORT_WSGI
        PORT_ASGI, PORT_WSGI = get_unused_ports(2)
        form_asgi = ASGIServerForm("", PORT_ASGI, app_asgi, PATH_ASGI_SERVER_LOG)
        form_wsgi = WSGIServerForm("", PORT_WSGI, app_wsgi, PATH_WSGI_SERVER_LOG)
        cls.executor_asgi = ASGITestExecutor(form_asgi).start_serve()
        cls.executor_wsgi = WSGITestExecutor(form_wsgi).start_serve()
        cls.uri_asgi = f"http://localhost:{PORT_ASGI}"
        cls.uri_wsgi = f"http://localhost:{PORT_WSGI}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor_asgi.close()
        cls.executor_wsgi.close()

    def test_asgi(self) -> None:
        with http.get(self.uri_asgi) as res:
            self.assertFalse(res.ok)
            self.assertIn("X-Bamboo-AAA", res.headers)
            self.assertIn("X-Bamboo-BBB", res.headers)

    def test_wsgi(self) -> None:
        with http.get(self.uri_wsgi) as res:
            self.assertFalse(res.ok)
            self.assertIn("X-Bamboo-AAA", res.headers)
            self.assertIn("X-Bamboo-BBB", res.headers)


if __name__ == "__main__":
    unittest.main()
