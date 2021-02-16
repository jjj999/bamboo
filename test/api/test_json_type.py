
from typing import List
import unittest

from bamboo.api import (
    JsonApiDataBuilder, JsonApiData, NotJsonableAnnotationError
)


class TestInnerApi(JsonApiData):
    
    name: str
    age: int
    
    
class TestOuterApi(JsonApiData):
    
    accounts: List[TestInnerApi]
    

class TestJsonable(unittest.TestCase):
    
    def test_int(self):
        JsonApiDataBuilder.check_jsonable(int)
    
    def test_float(self):
        JsonApiDataBuilder.check_jsonable(float)
    
    def test_str(self):
        JsonApiDataBuilder.check_jsonable(str)
    
    def test_bool(self):
        JsonApiDataBuilder.check_jsonable(bool)
    
    def test_NoneType(self):
        JsonApiDataBuilder.check_jsonable(type(None))
    
    def test_list(self):
        JsonApiDataBuilder.check_jsonable(List[int])

        with self.assertRaises(NotJsonableAnnotationError) as err:
            JsonApiDataBuilder.check_jsonable(List)
        self.assertIsInstance(err.exception, NotJsonableAnnotationError)
        
        with self.assertRaises(NotJsonableAnnotationError) as err:
            JsonApiDataBuilder.check_jsonable(List[dict])
        self.assertIsInstance(err.exception, NotJsonableAnnotationError)
    
    def test_jsonapi(self):
        JsonApiDataBuilder.is_jsonable_api(TestOuterApi)


if __name__ == "__main__":
    unittest.main()
