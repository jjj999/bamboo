

import unittest

from bamboo import App, Endpoint, data_format
from bamboo.api import JsonApiData
from bamboo.base import ContentType, MediaTypes
from bamboo.request import http
from bamboo.test import  ServerForm, TestExecutor
from bamboo.util.time import get_datetime_rfc822


class InfoResponse(JsonApiData):
    
    server_name: str
    current_time: str


class MockInfoEndpoint(Endpoint):
    
    NAME_SERVER = "Mocker"
    
    @data_format(input=None, output=InfoResponse)
    def do_GET(self) -> None:
        body = {
            "server_name": self.NAME_SERVER,
            "current_time": get_datetime_rfc822()
        }
        self.send_json(body)


class MockImageEndpoint(Endpoint):
    
    PATH_IMAGE = "elephant.jpg"

    def do_GET(self) -> None:
        with open(self.PATH_IMAGE, "rb") as f:
            image = f.read()
            
        self.send_body(image, ContentType(MediaTypes.jpeg))
        
        
class TestHTTPRequest(unittest.TestCase):
    
    def setUp(self) -> None:
        self.urls_info = [f"http://localhost:800{i}/mock/info" for i in range(3)]
        self.urls_image = [f"http://localhost:800{i}/mock/image" for i in range(3)]
        self.path_image_ideal = "elephant.jpg"
        
        app_1 = App()
        app_2 = App()
        app_3 = App()

        for app in (app_1, app_2, app_3):
            app.route("mock", "info")(MockInfoEndpoint)
            app.route("mock", "image")(MockImageEndpoint)
            
        form_1 = ServerForm("", 8000, app_1, "serverlog_1.log")
        form_2 = ServerForm("", 8001, app_2, "serverlog_2.log")
        form_3 = ServerForm("", 8002, app_3, "serverlog_3.log")
        self.executor = TestExecutor(form_1, form_2, form_3).start_serve()

    def tearDown(self) -> None:
        self.executor.close()

    def test_get_info(self):
        for url in self.urls_info:
            res = http.request(url, "GET", datacls=InfoResponse)
            data = res.attach()
            
            self.assertTrue(isinstance(data, InfoResponse))
            self.assertEqual(data.server_name, "Mocker")
            print(f"Response of 'current_time' : {data.current_time}")
        
    def test_get_image(self):
        with open(self.path_image_ideal, "rb") as f:
            image_ideal = f.read()
        
        for url in self.urls_image:
            res = http.request(url, "GET")
            data = res.body
            self.assertEqual(image_ideal, data)


if __name__ == "__main__":
    unittest.main()
