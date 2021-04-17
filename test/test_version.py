import unittest

from bamboo import (
    WSGIApp,
    WSGIEndpoint,
    VersionConfig,
)


app = WSGIApp()


@app.route("test", "hoge", version=1)
class TestEndpointSingle(WSGIEndpoint):
    ideal_uris = [
        ("v1", "test", "hoge"),
    ]


@app.route("test", "hogehoge", version=(1, 2, 3))
class TestEndpointMultiple(WSGIEndpoint):
    ideal_uris = [
        ("v1", "test", "hogehoge"),
        ("v2", "test", "hogehoge"),
        ("v3", "test", "hogehoge"),
    ]


@app.route("test", "hogest", version=None)
class TestEndpointAny(WSGIEndpoint):
    ideal_uris = [
        ("test", "hogest")
    ]


class TestEndpointNothing(WSGIEndpoint):
    pass


class TestVersion(unittest.TestCase):

    def test_version_single(self):
        config = VersionConfig(TestEndpointSingle)
        self.assertEqual(config.get(app), (1,))

        uris = app.search_uris(TestEndpointSingle)
        for uri, ideal in zip(uris, TestEndpointSingle.ideal_uris):
            self.assertEqual(uri, ideal)

    def test_version_multiple(self):
        config = VersionConfig(TestEndpointMultiple)
        self.assertEqual(config.get(app), (1, 2, 3))

        uris = app.search_uris(TestEndpointMultiple)
        for uri, ideal in zip(uris, TestEndpointMultiple.ideal_uris):
            self.assertEqual(uri, ideal)

    def test_version_any(self):
        config = VersionConfig(TestEndpointAny)
        self.assertEqual(config.get(app), ())

        uris = app.search_uris(TestEndpointAny)
        for uri, ideal in zip(uris, TestEndpointAny.ideal_uris):
            self.assertEqual(uri, ideal)

    def test_version_nothing(self):
        config = VersionConfig(TestEndpointNothing)
        self.assertEqual(config.get(app), None)


if __name__ == "__main__":
    unittest.main()
