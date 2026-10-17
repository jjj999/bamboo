import os
import typing as t
import unittest

from bamboo import BufferedConcatIterator, BufferedFileIterator

from .. import PATH_IMAGE


def generate_test_data() -> t.Generator[bytes, None, None]:
    for i in range(10**2, 10**3):
        yield os.getrandom(i)


class TestBufferedConcatIterator(unittest.TestCase):

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
            generate_test_data(),
            self.binary,
            generate_test_data(),
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

    def test_accepts_iterable_and_combines_chunks(self):
        iterator = BufferedConcatIterator(
            [b"ab", b"c"],
            b"defgh",
            bufsize=4,
        )

        self.assertEqual(list(iterator), [b"abcd", b"efgh"])

    def test_empty_response(self):
        self.assertEqual(list(BufferedConcatIterator(bufsize=4)), [])


if __name__ == "__main__":
    unittest.main()
