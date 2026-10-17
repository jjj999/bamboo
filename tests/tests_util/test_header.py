import unittest

from bamboo.util.header import make_header


class TestMakeHeader(unittest.TestCase):

    def test_without_parameters(self):
        self.assertEqual(
            make_header("Content-Type", "text/plain"),
            ("Content-Type", "text/plain"),
        )

    def test_with_parameters(self):
        self.assertEqual(
            make_header(
                "Content-Type",
                "multipart/form-data",
                charset="utf-8",
                boundary="example",
            ),
            (
                "Content-Type",
                "multipart/form-data; charset=utf-8; boundary=example",
            ),
        )


if __name__ == "__main__":
    unittest.main()
