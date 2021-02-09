

import json
from typing import List, Optional
import unittest

from bamboo.api import JsonApiData


class TestInnerData(JsonApiData):
    
    name: str
    age: int
    email: str
    
    
data_inner = json.dumps({
    "name": "hogehoge", "age": 18, "email": "hoge@hoge.com"
}).encode()


class TestListData(JsonApiData):
    
    accounts: List[TestInnerData]
    datetime: str
    

data_list = json.dumps({
    "accounts": [
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
        {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
    ],
    "datetime": "2000.01.01-00:00:00"
}).encode()

    
class TestNestedData(JsonApiData):
    
    account: TestInnerData
    datetime: str
    
    
data_nested = json.dumps({
    "account": {"name": "hogehoge", "age": 18, "email": "hoge@hoge.com"},
    "datetime": "2000.01.01-00:00:00"
}).encode()


class TestUnionData(JsonApiData):
    
    name: str
    age: Optional[int] = None
    
    
data_union = json.dumps({
    "name": "hogehoge", "age": None,
})
    

class TestJsonApiData(unittest.TestCase):
    
    def test_inner_data(self):
        data = TestInnerData(data_inner)
        self.assertEqual(data.name, "hogehoge")
        self.assertEqual(data.age, 18)
        self.assertEqual(data.email, "hoge@hoge.com")
        
    def test_list_data(self):
        data = TestListData(data_list)
        self.assertTrue(isinstance(data.accounts, list))
        self.assertTrue(isinstance(data.accounts[0], TestInnerData))
        self.assertEqual(data.accounts[0].name, "hogehoge")
        self.assertEqual(data.accounts[0].age, 18)
        self.assertEqual(data.accounts[0].email, "hoge@hoge.com")
        self.assertEqual(data.datetime, "2000.01.01-00:00:00")
    
    def test_nested_data(self):
        data = TestNestedData(data_nested)
        self.assertTrue(isinstance(data.account, TestInnerData))
        self.assertEqual(data.account.name, "hogehoge")
        self.assertEqual(data.account.age, 18)
        self.assertEqual(data.account.email, "hoge@hoge.com")
        self.assertEqual(data.datetime, "2000.01.01-00:00:00")
        
    def test_union_data(self):
        data = TestUnionData(data_union)
        self.assertEqual(data.name, "hogehoge")
        self.assertEqual(data.age, None)


if __name__ == "__main__":
    unittest.main()
