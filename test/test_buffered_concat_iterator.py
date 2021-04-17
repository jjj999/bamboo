import os
from typing import Generator
import unittest

from bamboo import BufferedConcatIterator, BufferedFileIterator

from . import PATH_IMAGE


def test_generator() -> Generator[bytes, None, None]:
    for i in range(10**2, 10**3):
        yield os.getrandom(i)


class BufferedConcatIteratorTest(unittest.TestCase):

    def setUp(self) -> None:
        self.total = sum((
            10**5,
            sum(range(10**2, 10**3)),
            10**5,
            sum(range(10**2, 10**3)),
            os.path.getsize(PATH_IMAGE))
        )
        self.binary = os.getrandom(10**5)
        self.bufsize = 8192
        self.iter = BufferedConcatIterator(
            self.binary,
            test_generator(),
            self.binary,
            test_generator(),
            BufferedFileIterator(PATH_IMAGE),
            bufsize=self.bufsize
        )

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
