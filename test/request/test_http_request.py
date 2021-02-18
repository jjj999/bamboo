
import unittest

from bamboo import App, Endpoint, data_format
from bamboo.api import JsonApiData
from bamboo.base import ContentType, MediaTypes
from bamboo.request import http
from bamboo.test import ServerForm, TestExecutor
from bamboo.util.time import get_datetime_rfc822


app = App()


class InfoResponse(JsonApiData):
    
    server_name: str
    current_time: str
    
    
@app.route("mock", "info")
class MockInfoEndpoint(Endpoint):
    
    NAME_SERVER = "Mocker"
    
    @data_format(input=None, output=InfoResponse)
    def do_GET(self) -> None:
        body = {
            "server_name": self.NAME_SERVER,
            "current_time": get_datetime_rfc822()
        }
        self.send_json(body)


@app.route("mock", "image")
class MockImageEndpoint(Endpoint):
    
    PATH_IMAGE = "elephant.jpg"

    def do_GET(self) -> None:
        with open(self.PATH_IMAGE, "rb") as f:
            image = f.read()
            
        self.send_body(image, ContentType(MediaTypes.jpeg))
    

class TestHTTPRequest(unittest.TestCase):
    
    def setUp(self) -> None:
        self.url_info = "http://localhost:8000/mock/info"
        self.url_image = "http://localhost:8000/mock/image"
        self.path_image_ideal = "elephant.jpg"
        
        form = ServerForm("", 8000, app, "test_http_request.log")
        self.executor = TestExecutor(form)
        self.executor.start_serve()
        
    def tearDown(self) -> None:
        self.executor.close()

    def test_get_info(self):
        res = http.request(self.url_info, "GET", datacls=InfoResponse)
        print(res.headers)
        data = res.attach()
        
        self.assertTrue(isinstance(data, InfoResponse))
        self.assertEqual(data.server_name, "Mocker")
        print(f"Response of 'current_time' : {data.current_time}")
        
    def test_get_image(self):
        with open(self.path_image_ideal, "rb") as f:
            image_ideal = f.read()
        
        res = http.request(self.url_image, "GET")
        data = res.body
        self.assertEqual(image_ideal, data)


if __name__ == "__main__":
    unittest.main()
