import os
import unittest

from bamboo import BufferedFileIterator

from . import PATH_IMAGE


class BufferedFileIteratorTest(unittest.TestCase):

    def setUp(self) -> None:
        self.total = os.path.getsize(PATH_IMAGE)
        self.bufsize = 8192
        self.iter = BufferedFileIterator(PATH_IMAGE, self.bufsize)

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
