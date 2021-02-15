
from collections import deque
import random
import string
from typing import List, Optional


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
                f"The length of 'begin' {begin} doesn't match {length}.")

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
                f"The length of 'begin' {begin} doesn't match {length}.")

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
        
        def challenge(string: List[CircularChar], 
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
