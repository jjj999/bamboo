from os import getrandom
import unittest

from bamboo import BufferedBinaryIterator


class TestBufferedBinaryIterator(unittest.TestCase):

    def setUp(self) -> None:
        self.total = 10**5
        self.bufsize = 8192
        self.data = getrandom(self.total)
        self.iter = BufferedBinaryIterator(self.data, self.bufsize)

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

    def test_exact_buffer_boundary(self):
        iterator = BufferedBinaryIterator(b"abcdefgh", bufsize=4)

        self.assertEqual(list(iterator), [b"abcd", b"efgh"])

    def test_empty_bytes(self):
        iterator = BufferedBinaryIterator(b"", bufsize=4)

        self.assertEqual(list(iterator), [])


if __name__ == "__main__":
    unittest.main()
