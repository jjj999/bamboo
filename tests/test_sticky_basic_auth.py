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
from bamboo.sticky.http import basic_auth
from bamboo.util.convert import encode_base64_string
from bamboo.util.string import rand_string

from . import get_log_name
from .asgi_util import ASGIHTTPServerForm, ASGIHTTPTestExecutor


app_asgi = ASGIHTTPApp()
app_wsgi = WSGIApp()
PATH_ASGI_SERVER_LOG = get_log_name(__file__, "asgi")
PATH_WSGI_SERVER_LOG = get_log_name(__file__, "wsgi")
RANDOM_CREDENTIALS = [(rand_string(10), rand_string(10)) for _ in range(10)]


def make_basic_credential(user_id: str, pw: str) -> str:
    return encode_base64_string(f"{user_id}:{pw}")


@app_asgi.route()
class TestASGIHTTPEndpoint(ASGIHTTPEndpoint):

    @basic_auth()
    async def do_HEAD(self, user_id: str, pw: str) -> None:
        self.send_only_status()


@app_wsgi.route()
class TestWSGIEndpoint(WSGIEndpoint):

    @basic_auth()
    def do_HEAD(self, user_id: str, pw: str) -> None:
        self.send_only_status()


class TestStickyRestrictsClient(unittest.TestCase):

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
        for user_id, pw in RANDOM_CREDENTIALS:
            formatted = make_basic_credential(user_id, pw)
            headers = {"Authorization": "Basic " + formatted}
            with http.head(self.uri_asgi, headers=headers) as res:
                self.assertTrue(res.ok)

    def test_wsgi(self):
        for user_id, pw in RANDOM_CREDENTIALS:
            formatted = make_basic_credential(user_id, pw)
            headers = {"Authorization": "Basic " + formatted}
            with http.head(self.uri_wsgi, headers=headers) as res:
                self.assertTrue(res.ok)


if __name__ == "__main__":
    unittest.main()
