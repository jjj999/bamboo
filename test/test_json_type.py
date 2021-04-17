from typing import List
import unittest

from bamboo.api import (
    InvalidAnnotationError,
    JsonApiData,
    JsonApiDataBuilder,
)


class TestInnerApi(JsonApiData):

    name: str
    age: int


class TestOuterApi(JsonApiData):

    accounts: List[TestInnerApi]


class TestJsonable(unittest.TestCase):

    def test_int(self):
        JsonApiDataBuilder.check_annotations(int)

    def test_float(self):
        JsonApiDataBuilder.check_annotations(float)

    def test_str(self):
        JsonApiDataBuilder.check_annotations(str)

    def test_bool(self):
        JsonApiDataBuilder.check_annotations(bool)

    def test_NoneType(self):
        JsonApiDataBuilder.check_annotations(type(None))

    def test_list(self):
        JsonApiDataBuilder.check_annotations(List[int])

        with self.assertRaises(InvalidAnnotationError) as err:
            JsonApiDataBuilder.check_annotations(List)
        self.assertIsInstance(err.exception, InvalidAnnotationError)

        with self.assertRaises(InvalidAnnotationError) as err:
            JsonApiDataBuilder.check_annotations(List[dict])
        self.assertIsInstance(err.exception, InvalidAnnotationError)

    def test_jsonapi(self):
        JsonApiDataBuilder.has_valid_annotations(TestOuterApi)


if __name__ == "__main__":
    unittest.main()
