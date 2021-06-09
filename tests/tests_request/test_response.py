import http.client as client
import os
import unittest

from bamboo import (
    ContentType,
    JsonApiData,
    MediaTypes,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.request import Response
from bamboo.sticky.http import data_format
from bamboo.util.time import get_datetime_rfc822

from . import PATH_IMAGE, get_log_name


app = WSGIApp()
NAME_SERVER = "Mocker"
PATH_SERVER_LOG = get_log_name(__file__)


class InfoResponse(JsonApiData):

    server_name: str
    current_time: str


@app.route("mock", "info")
class MockInfoEndpoint(WSGIEndpoint):

    @data_format(input=None, output=InfoResponse)
    def do_GET(self) -> None:
        body = {
            "server_name": NAME_SERVER,
            "current_time": get_datetime_rfc822()
        }
        self.send_json(body)


@app.route("mock", "image")
class MockImageEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        with open(PATH_IMAGE, "rb") as f:
            image = f.read()

        self.send_body(image, content_type=ContentType(MediaTypes.jpeg))


class TestResponse(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.conn = client.HTTPConnection("localhost", 8000)
        form = WSGIServerForm("", 8000, app, PATH_SERVER_LOG)
        cls.executor = WSGITestExecutor(form).start_serve()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor.close()

    def test_body(self):
        with open(PATH_IMAGE, "rb") as f:
            image_ideal = f.read()

        uri = "/" + os.path.join("mock", "image")
        self.conn.request("GET", uri)
        _res = self.conn.getresponse()
        with Response(self.conn, _res) as res:
            self.assertEqual(image_ideal, res.body)

    def test_attach_datacls(self):
        uri = "/" + os.path.join("mock", "info")
        self.conn.request("GET", uri)
        _res = self.conn.getresponse()
        with Response(self.conn, _res, datacls=InfoResponse) as res:
            data = res.attach()

        self.assertTrue(isinstance(data, InfoResponse))
        self.assertEqual(data.server_name, NAME_SERVER)


if __name__ == "__main__":
    unittest.main()
