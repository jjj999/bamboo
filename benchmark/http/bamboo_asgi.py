
from bamboo import ASGIApp, ASGIHTTPEndpoint


app = ASGIApp()


@app.route("test")
class TestEndpoint(ASGIHTTPEndpoint):

    async def do_GET(self) -> None:
        self.send_body(b"Hello, World!")
