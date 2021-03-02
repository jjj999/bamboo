
import falcon
from wsgiref import simple_server


class Resource:
    
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = "text/plain"
        resp.body = "Hello, World!"

        
app = falcon.API()
app.add_route("/test", Resource())


if __name__ == "__main__":
    httpd = simple_server.make_server("localhost", 8000, app)
    httpd.serve_forever()
