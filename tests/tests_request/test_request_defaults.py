import unittest
from unittest.mock import patch

from bamboo.http import HTTPMethods, MediaTypes
from bamboo.request import http, https


class TestRequestDefaults(unittest.TestCase):

    def test_http_does_not_mutate_caller_headers(self):
        headers = {}
        with patch.object(http.http.client, "HTTPConnection") as connection:
            http.request(
                "http://example.com", HTTPMethods.POST,
                headers=headers, body=b"body",
            )

        self.assertEqual(headers, {})
        sent_headers = connection.return_value.request.call_args[1]["headers"]
        self.assertEqual(sent_headers["Content-Type"], MediaTypes.plain)

    def test_https_does_not_mutate_caller_headers(self):
        headers = {}
        with patch.object(https.http.client, "HTTPSConnection") as connection:
            https.request(
                "https://example.com", HTTPMethods.POST,
                headers=headers, json={"ok": True},
            )

        self.assertEqual(headers, {})
        sent_headers = connection.return_value.request.call_args[1]["headers"]
        self.assertEqual(sent_headers["Content-Type"], MediaTypes.json)

    def test_omitted_mutable_arguments_are_fresh(self):
        with patch.object(http.http.client, "HTTPConnection") as connection:
            http.request("http://example.com", HTTPMethods.POST, body=b"body")
            http.request("http://example.com", HTTPMethods.GET)

        first_headers = connection.return_value.request.call_args_list[0][1]["headers"]
        second_headers = connection.return_value.request.call_args_list[1][1]["headers"]
        self.assertIsNot(first_headers, second_headers)
        self.assertNotIn("Content-Type", second_headers)


if __name__ == "__main__":
    unittest.main()
