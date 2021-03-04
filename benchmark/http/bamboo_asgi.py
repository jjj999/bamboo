
from bamboo import ASGIHTTPApp, ASGIHTTPEndpoint


app = ASGIHTTPApp()


@app.route("test")
class TestEndpoint(ASGIHTTPEndpoint):
    
    async def do_GET(self) -> None:
        self.send_body(b"Hello, World!")
