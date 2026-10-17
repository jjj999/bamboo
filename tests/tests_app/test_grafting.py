import unittest

from bamboo import (
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.request import http

from .. import get_log_name, get_unused_port


PATH_SERVER_LOG = get_log_name(__file__)
PORT = 0
sub_app1 = WSGIApp()
sub_app2 = WSGIApp()
app = WSGIApp()


@sub_app1.route("client", version=(1, 2, 3))
class ClientEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        self.send_body(b"Hello, Client!")


@sub_app2.route("hoge")
class HogeEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        self.send_body(b"hoge")


@app.route("world")
class WorldEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        self.send_body(b"Hello, World!")


app.graft(sub_app1)
app.graft(sub_app2, onto=("hoge",))


class TestGrafting(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        global PORT
        PORT = get_unused_port()
        form = WSGIServerForm("", PORT, app, PATH_SERVER_LOG)
        cls.executor = WSGITestExecutor(form).start_serve()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor.close()

    def test_world(self) -> None:
        with http.get(f"http://localhost:{PORT}/world") as res:
            self.assertTrue(res.ok)

    def test_client(self) -> None:
        for i in range(1, 4):
            with http.get(f"http://localhost:{PORT}/v{i}/client") as res:
                self.assertTrue(res.ok)

    def test_hoge(self) -> None:
        with http.get(f"http://localhost:{PORT}/hoge/hoge") as res:
            self.assertTrue(res.ok)


if __name__ == "__main__":
    unittest.main()
