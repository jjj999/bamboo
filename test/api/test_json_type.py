
from typing import List, get_type_hints
import unittest

from bamboo.api import is_jsonable, JsonApiData


class TestInnerApi(JsonApiData):
    
    name: str
    age: int
    
    
class TestOuterApi(JsonApiData):
    
    accounts: List[TestInnerApi]
    

class TestJsonable(unittest.TestCase):
    
    def test_int(self):
        self.assertTrue(is_jsonable([int]))
    
    def test_float(self):
        self.assertTrue(is_jsonable([float]))
    
    def test_str(self):
        self.assertTrue(is_jsonable([str]))
    
    def test_bool(self):
        self.assertTrue(is_jsonable([bool]))
    
    def test_NoneType(self):
        self.assertTrue(is_jsonable([type(None)]))
    
    def test_list(self):
        self.assertTrue(is_jsonable([List[int]]))
        self.assertFalse(is_jsonable([List]))
        self.assertFalse(is_jsonable([List[dict]]))
    
    def test_jsonapi(self):
        self.assertTrue(is_jsonable(get_type_hints(TestOuterApi).values()))
    
    
if __name__ == "__main__":
    unittest.main()
