
from bamboo import App, Endpoint, data_format, TestExecutor
from bamboo.api import JsonApiData


app = App()


class UpsideDownRequest(JsonApiData):
    
    token: str
    
    
class UpsideDownResponse(JsonApiData):
    
    result: str


@app.route("upsidedown")
class UpsideDownEndpoint(Endpoint):

    @data_format(input=UpsideDownRequest, output=UpsideDownResponse)
    def do_GET(self, req_body: UpsideDownRequest) -> None:
        result = req_body.token[::-1]

        body = {"result": result}
        self.send_json(body)


if __name__ == "__main__":
    TestExecutor.debug(app, "upsidedown.log")
