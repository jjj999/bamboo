import unittest

from bamboo import (
    ContentType,
    MediaTypes,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.api import JsonApiData
from bamboo.request import http
from bamboo.sticky.http import data_format
from bamboo.util.time import get_datetime_rfc822

from .. import PATH_IMAGE, get_log_name, get_unused_ports


NAME_SERVER = "Mocker"
PATH_SERVER_LOG_1 = get_log_name(__file__, "1")
PATH_SERVER_LOG_2 = get_log_name(__file__, "2")
PATH_SERVER_LOG_3 = get_log_name(__file__, "3")


class InfoResponse(JsonApiData):

    server_name: str
    current_time: str


class MockInfoEndpoint(WSGIEndpoint):

    @data_format(input=None, output=InfoResponse)
    def do_GET(self) -> None:
        body = {
            "server_name": NAME_SERVER,
            "current_time": get_datetime_rfc822()
        }
        self.send_json(body)


class MockImageEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        with open(PATH_IMAGE, "rb") as f:
            image = f.read()

        self.send_body(image, content_type=ContentType(MediaTypes.jpeg))


class TestTestExecutor(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        ports = get_unused_ports(3)
        cls.urls_info = [f"http://localhost:{port}/mock/info" for port in ports]
        cls.urls_image = [f"http://localhost:{port}/mock/image" for port in ports]

        app_1 = WSGIApp()
        app_2 = WSGIApp()
        app_3 = WSGIApp()

        for app in (app_1, app_2, app_3):
            app.route("mock", "info")(MockInfoEndpoint)
            app.route("mock", "image")(MockImageEndpoint)

        form_1 = WSGIServerForm("", ports[0], app_1, PATH_SERVER_LOG_1)
        form_2 = WSGIServerForm("", ports[1], app_2, PATH_SERVER_LOG_2)
        form_3 = WSGIServerForm("", ports[2], app_3, PATH_SERVER_LOG_3)
        cls.executor = WSGITestExecutor(form_1, form_2, form_3).start_serve()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor.close()

    def test_get_info(self):
        for url in self.urls_info:
            res = http.get(url, datacls=InfoResponse)
            data = res.attach()

            self.assertTrue(isinstance(data, InfoResponse))
            self.assertEqual(data.server_name, "Mocker")

    def test_get_image(self):
        with open(PATH_IMAGE, "rb") as f:
            image_ideal = f.read()

        for url in self.urls_image:
            res = http.get(url)
            data = res.body
            self.assertEqual(image_ideal, data)


if __name__ == "__main__":
    unittest.main()
