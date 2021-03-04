
from wsgiref import simple_server

from bamboo.app import WSGIApp
from bamboo.endpoint import WSGIEndpoint


app = WSGIApp()

@app.route("test")
class TestEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        self.send_body(b"Hello, World!")
