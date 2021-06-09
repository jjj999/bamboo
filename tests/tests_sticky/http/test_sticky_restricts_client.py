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
from bamboo.sticky.http import ClientInfo, restricts_client

from ... import get_log_name
from ...asgi_util import ASGIServerForm, ASGITestExecutor


app_asgi = ASGIApp()
app_wsgi = WSGIApp()
PATH_ASGI_SERVER_LOG = get_log_name(__file__, "asgi")
PATH_WSGI_SERVER_LOG = get_log_name(__file__, "wsgi")
CLIENT_CORRECT = ClientInfo("127.0.0.1")
CLIENT_INCORRECT = ClientInfo("199.9.9.9")


@app_asgi.route()
class TestASGIHTTPEndpoint(ASGIHTTPEndpoint):

    @restricts_client(CLIENT_CORRECT)
    async def do_GET(self) -> None:
        self.send_only_status()

    @restricts_client(CLIENT_INCORRECT)
    async def do_HEAD(self) -> None:
        self.send_only_status()


@app_wsgi.route()
class TestWSGIEndpoint(WSGIEndpoint):

    @restricts_client(CLIENT_CORRECT)
    def do_GET(self) -> None:
        self.send_only_status()

    @restricts_client(CLIENT_INCORRECT)
    def do_HEAD(self) -> None:
        self.send_only_status()


class TestStickyRestrictsClient(unittest.TestCase):

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

    def test_asgi_correct(self):
        with http.get(self.uri_asgi) as res:
            self.assertTrue(res.ok)

    def test_asgi_incorrect(self):
        with http.head(self.uri_asgi) as res:
            self.assertFalse(res.ok)

    def test_wsgi_correct(self):
        with http.get(self.uri_wsgi) as res:
            self.assertTrue(res.ok)

    def test_wsgi_incorrect(self):
        with http.head(self.uri_wsgi) as res:
            self.assertFalse(res.ok)


if __name__ == "__main__":
    unittest.main()
