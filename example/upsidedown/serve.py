

from wsgiref.simple_server import make_server

from bamboo import App, Endpoint, data_format
from bamboo.api import JsonApiData


app = App()


class UnpsideDownRequest(JsonApiData):
    
    token: str
    
    
class UpsideDownResponse(JsonApiData):
    
    result: str


@app.route("upsidedown")
class UpsideDownEndpoint(Endpoint):

    @data_format(input=UnpsideDownRequest, output=UpsideDownResponse)
    def do_GET(self, req_body: UnpsideDownRequest) -> None:
        token = req_body.token
        result = token[::-1]

        body = {"result": result}
        self.send_json(body)


if __name__ == "__main__":
    HOST_ADDRESS = ("localhost", 8000)
    server = make_server("", 8000, app)

    try:
        print(f"Hosting on : {HOST_ADDRESS}...")
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print()
