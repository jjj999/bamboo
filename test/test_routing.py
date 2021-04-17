import random
import string
from typing import List
import unittest

from bamboo import (
    AnyStringLocation,
    AsciiDigitLocation,
    DuplicatedUriRegisteredError,
    Router,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.request import http

from . import get_log_name


IDEAL_RESNPONSE = "Hello, World".encode()
PATH_SERVER_LOG = get_log_name(__file__)


def rand_string(k: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=k))


def rand_strings(num: int) -> List[str]:
    return [rand_string(random.randint(10, 20)) for _ in range(num)]


# Template endpoints
class MockEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        self.send_body(IDEAL_RESNPONSE)


class TestRouting(unittest.TestCase):

    def test_routing(self):
        # Make different uris
        paths = list(set(rand_strings(30)))

        def client():
            for i, path in enumerate(paths):
                uri = f"http://localhost:{8000 + i}/{path}"
                with http.get(uri) as res:
                    self.assertEqual(res.body, IDEAL_RESNPONSE)

        forms = []
        for i, path in enumerate(paths):
            app = WSGIApp()
            app.route(path)(MockEndpoint)
            forms.append(WSGIServerForm("", 8000 + i, app, PATH_SERVER_LOG))

        WSGITestExecutor(*forms).exec(client)

    def assertDuplicatedUris(self, patterns):
        router = Router()

        with self.assertRaises(DuplicatedUriRegisteredError) as err:
            for uri in patterns:
                router.register(uri, MockEndpoint)

        self.assertIsInstance(err.exception, DuplicatedUriRegisteredError)

    def test_duplicated_uris(self):
        pattern_1 = [
            ("test", "hoge", AnyStringLocation()),
            ("test", "hoge", "image")
        ]
        pattern_2 = [
            (AnyStringLocation(), AsciiDigitLocation(4)),
            ("hoge", "hoge")
        ]
        pattern_3 = [
            (AnyStringLocation(), "test", AnyStringLocation()),
            ("hoge", AnyStringLocation(), "image")
        ]

        self.assertDuplicatedUris(pattern_1)
        self.assertDuplicatedUris(pattern_2)
        self.assertDuplicatedUris(pattern_3)


if __name__ == "__main__":
    unittest.main()
