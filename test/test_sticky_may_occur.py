import unittest

from bamboo import (
    ASGIHTTPEndpoint,
    ErrInfo,
    WSGIEndpoint,
)
from bamboo.sticky.http import HTTPErrorConfig, may_occur


ERRORS = [type(f"TestErr{i}", (ErrInfo,), {}) for i in range(10)]


class TestWSGIEndpoint(WSGIEndpoint):

    @may_occur(*ERRORS)
    def do_GET(self) -> None:
        pass


class TestASGIHTTPEndpoint(ASGIHTTPEndpoint):

    @may_occur(*ERRORS)
    async def do_GET(self) -> None:
        pass


class TestSticyMayOccur(unittest.TestCase):

    def check_registered(self, callback):
        config = HTTPErrorConfig(callback)
        errors_registered = config.get()

        for err in ERRORS:
            self.assertIn(err, errors_registered)

    def test_wsgi(self):
        self.check_registered(TestWSGIEndpoint.do_GET)

    def test_asgi(self):
        self.check_registered(TestASGIHTTPEndpoint.do_GET)


if __name__ == "__main__":
    unittest.main()
