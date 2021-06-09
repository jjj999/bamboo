import typing as t
import unittest

from bamboo.api import JsonApiData


class NarrowData(JsonApiData):

    name: str
    age: int
    email: str


class NestedData(JsonApiData):

    account: NarrowData
    datetime: str


class ListData(JsonApiData):

    accounts: t.List[NarrowData]
    datetime: str


data_narrow = {
    "age": 18, "email": "hoge@hoge.com", "name": "hogehoge",
}
data_nested_dict = {
    "account": {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
    "datetime": "2000.01.01-00:00:00"
}
data_nested_api = {
    "account": NarrowData(name="hogehoge", age=18, email="hoge@hoge.com"),
    "datetime": "2000.01.01-00:00:00"
}
data_list_dict = {
    "accounts": [
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
    ],
    "datetime": "2000.01.01-00:00:00",
}
data_list_api = {
    "accounts": [
        NarrowData(name="hogehoge", age=18, email="hoge@hoge.com"),
        NarrowData(name="hogehoge", age=18, email="hoge@hoge.com"),
        NarrowData(name="hogehoge", age=18, email="hoge@hoge.com"),
        NarrowData(name="hogehoge", age=18, email="hoge@hoge.com"),
        NarrowData(name="hogehoge", age=18, email="hoge@hoge.com"),
        NarrowData(name="hogehoge", age=18, email="hoge@hoge.com"),
        NarrowData(name="hogehoge", age=18, email="hoge@hoge.com"),
    ],
    "datetime": "2000.01.01-00:00:00",
}


class TestJsonExtraction(unittest.TestCase):

    def test_narrow(self) -> None:
        api = NarrowData(**data_narrow)
        extracted = api.dict
        self.assertDictEqual(extracted, data_narrow)

    def test_nested_dict(self) -> None:
        api = NestedData(**data_nested_dict)
        extracted = api.dict
        self.assertDictEqual(extracted, data_nested_dict)

    def test_nested_api(self) -> None:
        api = NestedData(**data_nested_api)
        extracted = api.dict
        self.assertDictEqual(extracted, data_nested_dict)

    def test_list_dict(self) -> None:
        api = ListData(**data_list_dict)
        extracted = api.dict
        self.assertDictEqual(extracted, data_list_dict)

    def test_list_api(self) -> None:
        api = ListData(**data_list_api)
        extracted = api.dict
        self.assertDictEqual(extracted, data_list_dict)


if __name__ == "__main__":
    unittest.main()
