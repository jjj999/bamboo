
from wsgiref import simple_server

from bamboo.app import App
from bamboo.endpoint import Endpoint


app = App()

@app.route("test")
class TestEndpoint(Endpoint):
    
    def do_GET(self) -> None:
        self.send_body(b"Hello, World!")
 

if __name__ == "__main__":
    httpd = simple_server.make_server("localhost", 8000, app)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        print()
