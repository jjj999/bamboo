from os import getrandom
import typing as t
import unittest

from bamboo import BufferedIteratorWrapper


def generate_test_data() -> t.Generator[bytes, None, None]:
    for i in range(10**2, 10**3):
        yield getrandom(i)


class TestBufferedIteratorWrapper(unittest.TestCase):

    def setUp(self) -> None:
        self.total = sum(range(10**2, 10**3))
        self.bufsize = 8192
        self.iter = BufferedIteratorWrapper(generate_test_data(), self.bufsize)

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

    def test_accepts_reiterable_input(self):
        iterator = BufferedIteratorWrapper([b"ab", b"cdef"], bufsize=4)

        self.assertEqual(list(iterator), [b"abcd", b"ef"])


if __name__ == "__main__":
    unittest.main()
