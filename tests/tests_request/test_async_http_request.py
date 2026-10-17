import asyncio
import ssl
import unittest
from unittest.mock import patch

from bamboo.api import BinaryApiData
from bamboo.http import HTTPMethods
from bamboo.request import ahttp, ahttps


HTTP_METHODS = (
    ("get", HTTPMethods.GET),
    ("post", HTTPMethods.POST),
    ("put", HTTPMethods.PUT),
    ("delete", HTTPMethods.DELETE),
    ("head", HTTPMethods.HEAD),
    ("options", HTTPMethods.OPTIONS),
    ("patch", HTTPMethods.PATCH),
    ("trace", HTTPMethods.TRACE),
    ("connect", HTTPMethods.CONNECT),
)


class FakeEventLoop:

    def __init__(self):
        self.calls = []

    def run_in_executor(self, executor, func, *args):
        self.calls.append((executor, func, args))

        async def run():
            return func(*args)

        return run()


class TestAsyncHTTPMethods(unittest.TestCase):

    def test_all_http_methods_forward_default_arguments(self):
        calls = []

        async def fake_request(*args, **kwargs):
            calls.append((args, kwargs))
            return "response"

        with patch.object(ahttp, "request", new=fake_request):
            for name, method in HTTP_METHODS:
                result = asyncio.run(getattr(ahttp, name)("http://example.com"))
                self.assertEqual(result, "response")
                args, kwargs = calls[-1]
                self.assertEqual(args, ("http://example.com", method))
                self.assertIsNone(kwargs["headers"])
                self.assertIsNone(kwargs["query"])
                self.assertIsNone(kwargs["proxy_headers"])
                self.assertIsNone(kwargs["executor"])

    def test_http_method_forwards_all_arguments(self):
        calls = []
        executor = object()
        headers = {"X-Test": "header"}
        query = {"page": ["1"]}
        proxy_headers = {"X-Proxy": "header"}

        async def fake_request(*args, **kwargs):
            calls.append((args, kwargs))
            return "response"

        with patch.object(ahttp, "request", new=fake_request):
            asyncio.run(ahttp.post(
                "http://example.com", headers=headers, body=b"body",
                json=None, query=query, timeout=1.5, blocksize=1024,
                datacls=BinaryApiData, use_proxy=("proxy", 8080),
                proxy_headers=proxy_headers, executor=executor,
            ))

        args, kwargs = calls[0]
        self.assertEqual(args, ("http://example.com", HTTPMethods.POST))
        self.assertEqual(kwargs, {
            "headers": headers, "body": b"body", "json": None,
            "query": query, "timeout": 1.5, "blocksize": 1024,
            "datacls": BinaryApiData, "use_proxy": ("proxy", 8080),
            "proxy_headers": proxy_headers, "executor": executor,
        })

    def test_request_uses_default_and_explicit_executors(self):
        sentinel = object()
        loop = FakeEventLoop()

        with patch.object(ahttp.asyncio, "get_event_loop", return_value=loop):
            with patch.object(ahttp.http, "request", return_value=sentinel) as mocked:
                self.assertIs(asyncio.run(ahttp.request(
                    "http://example.com", HTTPMethods.GET,
                )), sentinel)
                mocked.assert_called_once_with(
                    "http://example.com", HTTPMethods.GET, None, None, None,
                    None, None, 8192, BinaryApiData, False, None,
                )

        executor = object()
        with patch.object(ahttp.asyncio, "get_event_loop", return_value=loop):
            with patch.object(ahttp.http, "request", return_value=sentinel):
                self.assertIs(asyncio.run(ahttp.request(
                    "http://example.com", HTTPMethods.GET,
                    executor=executor,
                )), sentinel)
        self.assertIsNone(loop.calls[0][0])
        self.assertIs(loop.calls[1][0], executor)


class TestAsyncHTTPSMethods(unittest.TestCase):

    def test_all_https_methods_forward_default_arguments(self):
        calls = []

        async def fake_request(*args, **kwargs):
            calls.append((args, kwargs))
            return "response"

        with patch.object(ahttps, "request", new=fake_request):
            for name, method in HTTP_METHODS:
                result = asyncio.run(getattr(ahttps, name)("https://example.com"))
                self.assertEqual(result, "response")
                args, kwargs = calls[-1]
                self.assertEqual(args, ("https://example.com", method))
                self.assertIsNone(kwargs["context"])
                self.assertIsNone(kwargs["executor"])

    def test_https_method_forwards_all_arguments(self):
        calls = []
        executor = object()
        context = ssl.create_default_context()
        headers = {"X-Test": "header"}
        query = {"page": ["1"]}
        proxy_headers = {"X-Proxy": "header"}

        async def fake_request(*args, **kwargs):
            calls.append((args, kwargs))
            return "response"

        with patch.object(ahttps, "request", new=fake_request):
            asyncio.run(ahttps.post(
                "https://example.com", headers=headers, body=b"body",
                json=None, query=query, timeout=1.5, blocksize=1024,
                datacls=BinaryApiData, context=context,
                use_proxy=("proxy", 8080), proxy_headers=proxy_headers,
                executor=executor,
            ))

        args, kwargs = calls[0]
        self.assertEqual(args, ("https://example.com", HTTPMethods.POST))
        self.assertEqual(kwargs, {
            "headers": headers, "body": b"body", "json": None,
            "query": query, "timeout": 1.5, "blocksize": 1024,
            "datacls": BinaryApiData, "context": context,
            "use_proxy": ("proxy", 8080),
            "proxy_headers": proxy_headers, "executor": executor,
        })

    def test_request_uses_default_and_explicit_executors(self):
        sentinel = object()
        loop = FakeEventLoop()

        with patch.object(ahttps.asyncio, "get_event_loop", return_value=loop):
            with patch.object(ahttps.https, "request", return_value=sentinel) as mocked:
                self.assertIs(asyncio.run(ahttps.request(
                    "https://example.com", HTTPMethods.GET,
                )), sentinel)
                mocked.assert_called_once_with(
                    "https://example.com", HTTPMethods.GET, None, None, None,
                    None, None, 8192, BinaryApiData, None, False, None,
                )

        executor = object()
        with patch.object(ahttps.asyncio, "get_event_loop", return_value=loop):
            with patch.object(ahttps.https, "request", return_value=sentinel):
                self.assertIs(asyncio.run(ahttps.request(
                    "https://example.com", HTTPMethods.GET,
                    executor=executor,
                )), sentinel)
        self.assertIsNone(loop.calls[0][0])
        self.assertIs(loop.calls[1][0], executor)


if __name__ == "__main__":
    unittest.main()
