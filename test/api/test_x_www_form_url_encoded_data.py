
from typing import List
import unittest

from bamboo.api import (
    XWWWFormUrlEncodedData, ValidationFailedError,
)
from bamboo.base import ContentType, MediaTypes


ideal_content_type = ContentType(MediaTypes.x_www_form_urlencoded, "utf-8")


class TestData(XWWWFormUrlEncodedData):
    
    name: str
    age: str
    email: str
    
    
data_raw = "name=hogehoge&email=hoge@hoge.com&age=18".encode()

data_key_not_included = "name=hogehoge&age=20".encode()

data_duplicated_key = "name=hogehoge&name=hogest&age=20&email=hoge@hoge.com"
data_duplicated_key = data_duplicated_key.encode()


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
