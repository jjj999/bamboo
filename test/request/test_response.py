
import http.client as client
import os
import unittest

from bamboo import App, Endpoint, data_format
from bamboo.api import JsonApiData
from bamboo.base import ContentType, MediaTypes
from bamboo.request import Response
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


class TestResponse(unittest.TestCase):
    
    def setUp(self) -> None:
        self.conn = client.HTTPConnection("localhost", 8000)
        self.url_info = "/" + os.path.join("mock", "info")
        self.url_image = "/" + os.path.join("", "mock", "image")
        self.path_image_ideal = "elephant.jpg"
        
        form = ServerForm("", 8000, app, "test_response.log")
        self.executor = TestExecutor(form).start_serve()
    
    def tearDown(self) -> None:
        self.executor.close()

    def test_body(self):
        with open(self.path_image_ideal, "rb") as f:
            image_ideal = f.read()
        
        self.conn.request("GET", self.url_image)
        _res = self.conn.getresponse()
        res = Response(_res)
        self.assertEqual(image_ideal, res.body)
        
    def test_attach_datacls(self):
        self.conn.request("GET", self.url_info)
        _res = self.conn.getresponse()
        res = Response(_res, datacls=InfoResponse)
        data = res.attach()
        
        self.assertTrue(isinstance(data, InfoResponse))
        self.assertEqual(data.server_name, "Mocker")
        print(f"Response of 'current_time' : {data.current_time}")


if __name__ == "__main__":
    unittest.main()
