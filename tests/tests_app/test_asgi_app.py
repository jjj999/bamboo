import unittest

from bamboo import ASGIApp, ASGIHTTPEndpoint
from bamboo.request import http

from .. import get_log_name
from ..asgi_util import ASGIServerForm, ASGITestExecutor


app = ASGIApp()
PATH_SERVER_LOG = get_log_name(__file__)


@app.route("hello")
class MockEndpoint(ASGIHTTPEndpoint):

    async def do_GET(self) -> None:
        self.send_body(b"Hello, World!")


@app.route("attributes")
class AttributesEndpoint(ASGIHTTPEndpoint):

    async def do_GET(self) -> None:
        assert self.asgi_version == "3.0"
        assert self.http_version == "1.1"
        assert self.scheme == "http"
        assert self.get_host_addr() == ("localhost", 8000)
        assert self.path == "/attributes"
        assert self.queries == {}
        assert self.method == "GET"

        self.send_only_status()


class TestASGIApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        form = ASGIServerForm("localhost", 8000, app, PATH_SERVER_LOG)
        cls.executor = ASGITestExecutor(form).start_serve()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor.close()

    def test_hello(self):
        with http.get("http://localhost:8000/hello") as res:
            self.assertEqual(res.body, b"Hello, World!")

    def test_attributes(self):
        with http.get("http://localhost:8000/attributes") as res:
            self.assertTrue(res.ok)


if __name__ == "__main__":
    unittest.main()
