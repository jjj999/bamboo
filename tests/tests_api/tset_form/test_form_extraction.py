import unittest

from bamboo import ContentType, MediaTypes
from bamboo.api import FormApiData


class AccountApi(FormApiData):

    name: str
    age: str
    email: str


ideal_content_type = ContentType(MediaTypes.x_www_form_urlencoded, "utf-8")
account_dict = {
    "name": "hogehoge",
    "email": "hoge@hoge.com",
    "age": "18"
}
account_string = b"name=hogehoge&age=18&email=hoge@hoge.com"


class TestFormExtraction(unittest.TestCase):

    def test_dict(self) -> None:
        api = AccountApi(**account_dict)
        self.assertDictEqual(api.dict, account_dict)

    def test_string(self) -> None:
        api = AccountApi.__validate__(account_string, ideal_content_type)
        self.assertListEqual(
            api.string.split("&"),
            account_string.decode().split("&"),
        )


if __name__ == "__main__":
    unittest.main()
