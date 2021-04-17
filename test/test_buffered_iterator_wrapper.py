from os import getrandom
from typing import Generator
import unittest

from bamboo import BufferedIteratorWrapper


def test_generator() -> Generator[bytes, None, None]:
    for i in range(10**2, 10**3):
        yield getrandom(i)


class BufferedIteratorWrapperTest(unittest.TestCase):

    def setUp(self) -> None:
        self.total = sum(range(10**2, 10**3))
        self.bufsize = 8192
        self.iter = BufferedIteratorWrapper(test_generator(), self.bufsize)

    def test_iter(self):
        sum = 0
        for i in self.iter:
            diff = self.total - sum
            if diff < self.bufsize:
                self.assertEqual(len(i), diff)
            else:
                self.assertEqual(len(i), self.bufsize)

            sum += len(i)
        self.assertEqual(sum, self.total)


if __name__ == "__main__":
    unittest.main()
