
from collections import deque
from enum import Enum
import random
import string
from typing import List, Optional


__all__ = [
    "CircularChar",
    "CircularString",
    "ColorCode",
    "SerialString",
    "insert_colorcode",
    "rand_string",
]


class CircularChar:

    # NOTE
    #   This order is compatible with database.
    ROW = string.digits + string.ascii_uppercase + string.ascii_lowercase
    END = len(ROW) - 1

    HEAD = ROW[0]
    TAIL = ROW[-1]

    def __init__(self, begin: str = "0") -> None:
        if len(begin) != 1:
            raise ValueError("'begin' must be one charactor.")
        if begin not in self.ROW:
            raise ValueError("'begin' must be an ASCII charactor or digit.")

        self._index = 0

        for i, char in enumerate(self.ROW):
            if begin == char:
                self._index = i
                break

    @property
    def current(self) -> str:
        return self.ROW[self._index]

    def next(self, up: bool = True) -> str:
        if self._index == self.END:
            index = 0
        else:
            index = self._index + 1

        if up:
            self._index = index

        return self.ROW[index]

    def back(self, down: bool = True) -> str:
        if self._index == 0:
            index = self.END
        else:
            index = self._index - 1

        if down:
            self._index = index

        return self.ROW[index]


class SerialString:

    def __init__(self, length: int, begin: Optional[str] = None) -> None:
        if length < 1:
            raise ValueError("'length' must be bigger than 0.")

        if begin and len(begin) != length:
            raise ValueError(
                f"The length of 'begin' {begin} doesn't match {length}."
            )

        self._is_full = False
        self._is_first = False
        if begin:
            self._string = [CircularChar(b) for b in begin]
        else:
            self._string = [CircularChar() for _ in range(length)]
            self._is_first = True

    @property
    def current(self) -> str:
        return "".join([c.current for c in self._string])

    def next(self, up: bool = True) -> Optional[str]:
        result = deque()

        def challenge(string: List[CircularChar], is_carry_up: bool) -> None:
            next_up = False
            if is_carry_up:
                char = string[-1].next(up=up)
                if char == CircularChar.HEAD:
                    next_up = True
            else:
                char = string[-1].current

            result.appendleft(char)

            if len(string) == 1:
                if next_up:
                    self._is_full = True
                return

            challenge(string[:-1], next_up)

        if self._is_first:
            challenge(self._string, False)
            self._is_first = False
        else:
            challenge(self._string, True)

        if self._is_full:
            return None

        return "".join(result)


class CircularString:

    def __init__(self, length: int, begin: Optional[str] = None) -> None:
        if length < 1:
            raise ValueError("'length' must be bigger than 0.")

        if begin and len(begin) != length:
            raise ValueError(
                f"The length of 'begin' {begin} doesn't match {length}."
            )

        if begin:
            self._string = [CircularChar(b) for b in begin]
        else:
            self._string = [CircularChar() for _ in range(length)]

    @property
    def current(self) -> str:
        return "".join([c.current for c in self._string])

    def next(self, up: bool = True) -> str:
        result = deque()

        def challenge(string: List[CircularChar], is_carry_up: bool) -> None:
            next_up = False
            if is_carry_up:
                char = string[-1].next(up=up)
                if char == CircularChar.HEAD:
                    next_up = True
            else:
                char = string[-1].current

            result.appendleft(char)

            if len(string) == 1:
                return

            challenge(string[:-1], next_up)

        challenge(self._string, True)
        return "".join(result)

    def back(self, down: bool = True) -> str:
        result = deque()

        def challenge(
            string: List[CircularChar],
            is_carry_down: bool
        ) -> None:
            next_down = False
            if is_carry_down:
                char = string[-1].back(down=down)
                if char == CircularChar.TAIL:
                    next_down = True
            else:
                char = string[-1].current

            result.appendleft(char)

            if len(string) == 1:
                return

            challenge(string[:-1], next_down)

        challenge(self._string, True)
        return "".join(result)


_ASCII_LETTERS_DIGITS = string.ascii_letters + string.digits


def rand_string(size: int) -> str:
    return "".join(random.choices(_ASCII_LETTERS_DIGITS, k=size))


class ColorCode(Enum):

    BLACK       = "\033[30m"
    RED         = "\033[31m"
    GREEN       = "\033[32m"
    YELLOW      = "\033[33m"
    BLUE        = "\033[34m"
    MAGENTA     = "\033[35m"
    CYAN        = "\033[36m"
    WHITE       = "\033[37m"
    DEFAULT     = "\033[39m"
    BOLD        = "\033[1m"
    UNDERLINE   = "\033[4m"
    INVISIBLE   = "\033[08m"
    REVERCE     = "\033[07m"

    BG_BLACK    = "\033[40m"
    BG_RED      = "\033[41m"
    BG_GREEN    = "\033[42m"
    BG_YELLOW   = "\033[43m"
    BG_BLUE     = "\033[44m"
    BG_MAGENTA  = "\033[45m"
    BG_CYAN     = "\033[46m"
    BG_WHITE    = "\033[47m"
    BG_DEFAULT  = "\033[49m"

    RESET       = "\033[0m"


def insert_colorcode(text: str, code: ColorCode, reset: bool = True) -> str:
    text = "".join((code.value, text))
    if reset:
        text = "".join((text, ColorCode.RESET.value))

    return text
