import unittest

from bamboo import (
    DEFAULT_CONTENT_TYPE_PLAIN,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.request import http

from . import get_log_name


app = WSGIApp()
PATH_SERVER_LOG = get_log_name(__file__)


@app.route("hello")
class MockEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        self.send_body(b"Hello, World!")


@app.route("attributes")
class AttributesEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        assert self.wsgi_version == "1.0"
        assert self.server_software == "WSGIServer/0.2"
        assert self.http_version == "1.1"
        assert self.scheme == "http"
        assert self.get_host_addr() == ("localhost", 8000)
        assert self.path == "/attributes"
        assert self.queries == {}
        assert self.content_type == DEFAULT_CONTENT_TYPE_PLAIN
        assert self.method == "GET"

        self.send_only_status()


@app.route("callback")
class CallbackEndpoint(WSGIEndpoint):

    def pre_GET(self) -> None:
        self.word = "word"

    def do_GET(self) -> None:
        assert self.word == "word"
        self.send_only_status()


class WSGIAppTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        form = WSGIServerForm("", 8000, app, PATH_SERVER_LOG)
        cls.executor = WSGITestExecutor(form).start_serve()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor.close()

    def test_hello(self):
        with http.get("http://localhost:8000/hello") as res:
            self.assertEqual(res.body, b"Hello, World!")

    def test_attributes(self):
        with http.get("http://localhost:8000/attributes") as res:
            self.assertTrue(res.ok)

    def test_callback(self):
        with http.get("http://localhost:8000/callback") as res:
            self.assertTrue(res.ok)


if __name__ == "__main__":
    unittest.main()
