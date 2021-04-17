import unittest

from bamboo import (
    ContentType,
    MediaTypes,
    XWWWFormUrlEncodedData,
    ValidationFailedError,
)


ideal_content_type = ContentType(MediaTypes.x_www_form_urlencoded, "utf-8")


class TestData(XWWWFormUrlEncodedData):

    name: str
    age: str
    email: str


data_raw = b"name=hogehoge&email=hoge@hoge.com&age=18"
data_key_not_included = b"name=hogehoge&age=20"
data_duplicated_key = b"name=hogehoge&name=hogest&age=20&email=hoge@hoge.com"


class TestXWWWFromUrlEncodedData(unittest.TestCase):

    def test_data_raw(self):
        data = TestData(data_raw, ideal_content_type)
        self.assertEqual(data.name, "hogehoge")
        self.assertEqual(int(data.age), 18)
        self.assertEqual(data.email, "hoge@hoge.com")

    def test_data_key_not_included(self):
        with self.assertRaises(ValidationFailedError) as err:
            data = TestData(data_key_not_included, ideal_content_type)
        self.assertIsInstance(err.exception, ValidationFailedError)

    def test_data_duplicated_key(self):
        with self.assertRaises(ValidationFailedError) as err:
            data = TestData(data_duplicated_key, ideal_content_type)
        self.assertIsInstance(err.exception, ValidationFailedError)


if __name__ == "__main__":
    unittest.main()
