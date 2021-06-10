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
from bamboo.sticky.http import bearer_auth
from bamboo.util.string import rand_string

from ... import get_log_name
from ...asgi_util import ASGIServerForm, ASGITestExecutor


app_asgi = ASGIApp()
app_wsgi = WSGIApp()
PATH_ASGI_SERVER_LOG = get_log_name(__file__, "asgi")
PATH_WSGI_SERVER_LOG = get_log_name(__file__, "wsgi")
RANDOM_TOKEN = [rand_string(10) for _ in range(10)]


@app_asgi.route()
class TestASGIHTTPEndpoint(ASGIHTTPEndpoint):

    @bearer_auth()
    async def do_HEAD(self, token: str) -> None:
        self.send_only_status()


@app_wsgi.route()
class TestWSGIEndpoint(WSGIEndpoint):

    @bearer_auth()
    def do_HEAD(self, token: str) -> None:
        self.send_only_status()


class TestStickyBearerAuth(unittest.TestCase):

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

    def test_asgi(self):
        for token in RANDOM_TOKEN:
            headers = {"Authorization": "Bearer " + token}
            with http.head(self.uri_asgi, headers=headers) as res:
                self.assertTrue(res.ok)

    def test_wsgi(self):
        for token in RANDOM_TOKEN:
            headers = {"Authorization": "Bearer " + token}
            with http.head(self.uri_wsgi, headers=headers) as res:
                self.assertTrue(res.ok)


if __name__ == "__main__":
    unittest.main()
