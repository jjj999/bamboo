import unittest

from bamboo import (
    AnyStringLocation,
    DuplicatedUriRegisteredError,
    Router,
    WSGIEndpoint,
)


class RootEndpoint(WSGIEndpoint):
    pass


class StaticEndpoint(WSGIEndpoint):
    pass


class DynamicEndpoint(WSGIEndpoint):
    pass


class TestRouterValidation(unittest.TestCase):

    def setUp(self) -> None:
        self.router = Router()
        self.router.register((), RootEndpoint)
        self.router.register(("static",), StaticEndpoint)
        self.router.register(
            ("dynamic", AnyStringLocation()),
            DynamicEndpoint,
        )

    def test_static_uri(self):
        self.assertEqual(self.router.validate("/static"), ((), StaticEndpoint))

    def test_dynamic_uri(self):
        self.assertEqual(
            self.router.validate("/dynamic/value"),
            (("value",), DynamicEndpoint),
        )

    def test_root_uri(self):
        self.assertEqual(self.router.validate("/"), ((), RootEndpoint))

    def test_unmatched_uri(self):
        self.assertEqual(self.router.validate("/missing"), ((), None))

    def test_versioned_static_routes(self):
        router = Router()
        router.register(("resource",), StaticEndpoint, version=("v1", "v2"))

        self.assertEqual(
            router.validate("/v1/resource"),
            ((), StaticEndpoint),
        )
        self.assertEqual(
            router.validate("/v2/resource"),
            ((), StaticEndpoint),
        )

    def test_duplicate_static_and_dynamic_routes(self):
        router = Router()
        router.register(("users", AnyStringLocation()), DynamicEndpoint)

        with self.assertRaises(DuplicatedUriRegisteredError):
            router.register(("users", "current"), StaticEndpoint)


if __name__ == "__main__":
    unittest.main()
