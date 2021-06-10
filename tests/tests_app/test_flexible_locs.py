import random
import unittest

from bamboo import (
    AnyStringLocation,
    AsciiDigitLocation,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.api import JsonApiData
from bamboo.request import http
from bamboo.sticky.http import data_format
from bamboo.util.string import rand_string
from bamboo.util.time import get_datetime_rfc822

from .. import get_log_name


app = WSGIApp()
PATH_SERVER_LOG = get_log_name(__file__)


class InfoResponse(JsonApiData):

    name: str
    datetime: str


@app.route(AnyStringLocation(), "info")
class InfoEndpoint(WSGIEndpoint):

    @data_format(input=None, output=InfoResponse)
    def do_GET(self) -> None:
        name, = self.flexible_locs
        body = {"name": name, "datetime": get_datetime_rfc822()}
        self.send_json(body)


class CalculationResult(JsonApiData):

    result: int


@app.route(AsciiDigitLocation(10), AsciiDigitLocation(10), "multiply")
class MultiplyEndpoint(WSGIEndpoint):

    @data_format(input=None, output=CalculationResult)
    def do_GET(self) -> None:
        num_1, num_2 = self.flexible_locs
        body = {"result": int(num_1) * int(num_2)}
        self.send_json(body)


class TestFlexibleLocs(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        form = WSGIServerForm("", 8000, app, PATH_SERVER_LOG)
        cls.executor = WSGITestExecutor(form).start_serve()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor.close()

    def test_info(self):
        names = [rand_string(10) for _ in range(100)]

        for name in names:
            uri = f"http://localhost:8000/{name}/info"
            with http.get(uri, datacls=InfoResponse) as res:
                if res.ok:
                    body = res.attach()
                    self.assertEqual(body.name, name)
                else:
                    print(f"Request failed. Status code: {res.status}")

    def test_multiply(self):
        get_num = lambda: random.randint(10**9, 10**10 - 1)
        num_pairs = [(get_num(), get_num()) for _ in range(100)]

        for num_1, num_2 in num_pairs:
            uri = f"http://localhost:8000/{num_1}/{num_2}/multiply"
            with http.get(uri, datacls=CalculationResult) as res:
                if res.ok:
                    body = res.attach()
                    self.assertEqual(body.result, num_1 * num_2)
                else:
                    print(f"Request failed. Status code: {res.status}")


if __name__ == "__main__":
    unittest.main()
