import random
import typing as t
import unittest

from bamboo import (
    ASGIApp,
    ASGIHTTPEndpoint,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.api import JsonApiData
from bamboo.request import http
from bamboo.sticky.http import data_format
from bamboo.util.string import rand_string

from ... import get_log_name
from ...asgi_util import ASGIServerForm, ASGITestExecutor


app_asgi = ASGIApp()
app_wsgi = WSGIApp()
PATH_ASGI_SERVER_LOG = get_log_name(__file__, "asgi")
PATH_WSGI_SERVER_LOG = get_log_name(__file__, "wsgi")


class UserJsonApi(JsonApiData):

    user_id: str
    name: str
    email: str
    age: int


class TestJsonApi(JsonApiData):

    users: t.List[UserJsonApi]
    total: int


def make_user_api_data() -> t.Dict[str, t.Any]:
    user_id = rand_string(10)
    name = rand_string(10)
    email = rand_string(20)
    age = random.randint(0, 100)
    return {
        "user_id": user_id,
        "name": name,
        "email": email,
        "age": age,
    }


def make_test_api_data() -> t.Dict[str, t.Any]:
    total = random.randint(0, 100)
    users = [make_user_api_data() for _ in range(total)]
    return {
        "users": users,
        "total": total,
    }


@app_asgi.route()
class TestASGIHTTPEndpoint(ASGIHTTPEndpoint):

    @data_format(input=None, output=TestJsonApi)
    async def do_GET(self) -> None:
        assert await self.body == b""
        self.send_json(make_test_api_data())

    @data_format(input=TestJsonApi, output=None)
    async def do_POST(self, rec_body: TestJsonApi) -> None:
        self.send_only_status()

    @data_format(input=JsonApiData, output=None, is_validate=False)
    async def do_DELETE(self) -> None:
        self.send_only_status()


@app_wsgi.route()
class TestWSGIEndpoint(WSGIEndpoint):

    @data_format(input=None, output=TestJsonApi)
    def do_GET(self) -> None:
        assert self.body == b""
        self.send_json(make_test_api_data())

    @data_format(input=TestJsonApi, output=None)
    def do_POST(self, rec_body: TestJsonApi) -> None:
        self.send_only_status()

    @data_format(input=JsonApiData, output=None, is_validate=False)
    def do_DELETE(self) -> None:
        self.send_only_status()


class TestStickyDataFormat(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        form_asgi = ASGIServerForm("", 8000, app_asgi, PATH_ASGI_SERVER_LOG)
        form_wsgi = WSGIServerForm("", 8001, app_wsgi, PATH_WSGI_SERVER_LOG)
        cls.executor_asgi = ASGITestExecutor(form_asgi).start_serve()
        cls.executor_wsgi = WSGITestExecutor(form_wsgi).start_serve()
        cls.uri_asgi = "http://localhost:8000"
        cls.uri_wsgi = "http://localhost:8001"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor_asgi.close()
        cls.executor_wsgi.close()

    def test_asgi_output(self):
        with http.get(self.uri_asgi) as res:
            self.assertTrue(res.ok)
            api_data = res.attach(TestJsonApi)
            self.assertIsInstance(api_data, TestJsonApi)

    def test_asgi_input_validation(self):
        data = make_test_api_data()
        with http.post(self.uri_asgi, json=data) as res:
            self.assertTrue(res.ok)

    def test_asgi_input_no_validation(self):
        data = make_test_api_data()
        with http.delete(self.uri_asgi, json=data) as res:
            self.assertTrue(res.ok)

    def test_wsgi_output(self):
        with http.get(self.uri_wsgi) as res:
            self.assertTrue(res.ok)
            api_data = res.attach(TestJsonApi)
            self.assertIsInstance(api_data, TestJsonApi)

    def test_wsgi_input_validation(self):
        data = make_test_api_data()
        with http.post(self.uri_wsgi, json=data) as res:
            self.assertTrue(res.ok)

    def test_wsgi_input_no_validation(self):
        data = make_test_api_data()
        with http.delete(self.uri_wsgi, json=data) as res:
            self.assertTrue(res.ok)


if __name__ == "__main__":
    unittest.main()
