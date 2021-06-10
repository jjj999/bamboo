import unittest

from bamboo import ContentType, MediaTypes
from bamboo.api import ApiValidationFailedError, FormApiData


class TestData(FormApiData):

    name: str
    age: str
    email: str


ideal_content_type = ContentType(MediaTypes.x_www_form_urlencoded, "utf-8")
data_raw = b"name=hogehoge&email=hoge@hoge.com&age=18"
data_key_not_included = b"name=hogehoge&age=20"
data_duplicated_key = b"name=hogehoge&name=hogest&age=20&email=hoge@hoge.com"


class TestFormValidation(unittest.TestCase):

    def test_data_raw(self):
        data = TestData.__validate__(data_raw, ideal_content_type)
        self.assertEqual(data.name, "hogehoge")
        self.assertEqual(int(data.age), 18)
        self.assertEqual(data.email, "hoge@hoge.com")

    def test_data_key_not_included(self):
        with self.assertRaises(ApiValidationFailedError) as err:
            data = TestData.__validate__(data_key_not_included, ideal_content_type)
        self.assertIsInstance(err.exception, ApiValidationFailedError)

    def test_data_duplicated_key(self):
        with self.assertRaises(ApiValidationFailedError) as err:
            data = TestData.__validate__(data_duplicated_key, ideal_content_type)
        self.assertIsInstance(err.exception, ApiValidationFailedError)


if __name__ == "__main__":
    unittest.main()
