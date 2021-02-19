
import bamboo


app = bamboo.App()


class HelloData(bamboo.JsonApiData):
    
    text: str
    
    
@app.route("hello")
class HelloEndpoint(bamboo.Endpoint):
    
    @bamboo.data_format(input=None, output=HelloData)
    def do_GET(self) -> None:
        body = {"text": "Hello, World!"}
        self.send_json(body)
