from bamboo import (
    JsonApiData,
    WSGIApp,
    WSGIEndpoint,
    WSGITestExecutor,
)
from bamboo.sticky.http import data_format


app = WSGIApp()


class UpsideDownRequest(JsonApiData):

    token: str


class UpsideDownResponse(JsonApiData):

    result: str


@app.route("upsidedown")
class UpsideDownEndpoint(WSGIEndpoint):

    @data_format(input=UpsideDownRequest, output=UpsideDownResponse)
    def do_GET(self, req_body: UpsideDownRequest) -> None:
        result = req_body.token[::-1]
        self.send_api(UpsideDownResponse(result=result))


if __name__ == "__main__":
    WSGITestExecutor.debug(app)
