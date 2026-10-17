from bamboo import WSGIApp, WSGIEndpoint
from bamboo.api import JsonApiData
from bamboo.sticky.http import data_format


app = WSGIApp()


class HelloData(JsonApiData):
    text: str


@app.route("hello")
class HelloEndpoint(WSGIEndpoint):
    @data_format(input=None, output=HelloData)
    def do_GET(self) -> None:
        self.send_api(HelloData(text="Hello, World!"))
