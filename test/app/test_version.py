

import unittest

from bamboo import App, Endpoint, VersionConfig


app = App()


@app.route("test", "hoge", version=1)
class TestEndpointSingle(Endpoint):
    ideal_uris = [
        ("v1", "test", "hoge"),
    ]


@app.route("test", "hogehoge", version=(1, 2, 3))
class TestEndpointMultiple(Endpoint):
    ideal_uris = [
        ("v1", "test", "hogehoge"),
        ("v2", "test", "hogehoge"),
        ("v3", "test", "hogehoge"),
    ]


@app.route("test", "hogest", version=None)
class TestEndpointAny(Endpoint):
    ideal_uris = [
        ("test", "hogest")
    ]


class TestEndpointNothing(Endpoint):
    pass


class TestVersion(unittest.TestCase):
    
    def test_version_single(self):
        config = VersionConfig(TestEndpointSingle)
        self.assertEqual(config.get(app), (1,))
        
        uris = app.seach_uris(TestEndpointSingle)
        for uri, ideal in zip(uris, TestEndpointSingle.ideal_uris):
            self.assertEqual(uri, ideal)
        
    def test_version_multiple(self):
        config = VersionConfig(TestEndpointMultiple)
        self.assertEqual(config.get(app), (1, 2, 3))
        
        uris = app.seach_uris(TestEndpointMultiple)
        for uri, ideal in zip(uris, TestEndpointMultiple.ideal_uris):
            self.assertEqual(uri, ideal)
        
    def test_version_any(self):
        config = VersionConfig(TestEndpointAny)
        self.assertEqual(config.get(app), ())
        
        uris = app.seach_uris(TestEndpointAny)
        for uri, ideal in zip(uris, TestEndpointAny.ideal_uris):
            self.assertEqual(uri, ideal)
        
    def test_version_nothing(self):
        config = VersionConfig(TestEndpointNothing)
        self.assertEqual(config.get(app), None)
        
        
if __name__ == "__main__":
    unittest.main()
