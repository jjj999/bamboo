import unittest

from bamboo import HTTPStatus
from bamboo.asgi import (
    ASGIHTTPEvents,
    ASGIWebSocketEvents,
    format_http_sendstart_msg,
    format_websock_accept_msg,
    format_websock_send_msg,
)


class TestASGIHelpers(unittest.TestCase):

    def test_http_start_headers_are_encoded(self):
        self.assertEqual(
            format_http_sendstart_msg(
                HTTPStatus.OK,
                [("content-type", "text/plain")],
            ),
            {
                "type": ASGIHTTPEvents.response_start,
                "status": 200,
                "headers": [(b"content-type", b"text/plain")],
            },
        )

    def test_websocket_accept_headers_are_encoded(self):
        self.assertEqual(
            format_websock_accept_msg(
                [("set-cookie", "session=example")],
                "chat",
            ),
            {
                "type": ASGIWebSocketEvents.accept,
                "subprotocol": "chat",
                "headers": [(b"set-cookie", b"session=example")],
            },
        )

    def test_websocket_binary_message(self):
        self.assertEqual(
            format_websock_send_msg(bin=b"payload"),
            {
                "type": ASGIWebSocketEvents.send,
                "bytes": b"payload",
                "text": None,
            },
        )


if __name__ == "__main__":
    unittest.main()
