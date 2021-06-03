
from bamboo import (
    JsonApiData,
    WSGIApp,
    WSGIEndpoint,
)
from bamboo.sticky.http import data_format


app = WSGIApp()


class HelloData(JsonApiData):

    text: str


@app.route("hello")
class HelloEndpoint(WSGIEndpoint):

    @data_format(input=None, output=HelloData)
    def do_GET(self) -> None:
        body = {"text": "Hello, World!"}
        self.send_json(body)
