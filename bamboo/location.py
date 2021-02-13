

from abc import ABCMeta, abstractmethod
from typing import Optional, Tuple, Union


class FlexibleLocation(metaclass=ABCMeta):
    
    @abstractmethod
    def is_valid(self, loc: str) -> bool:
        pass


Location = Union[str, FlexibleLocation]
Uri_t = Tuple[Location]


def is_flexible_uri(uri: Uri_t) -> bool:
    for loc in uri:
        if isinstance(loc, FlexibleLocation):
            return True
    return False


def is_duplicated_uri(uri_1: Uri_t, uri_2: Uri_t) -> bool:
    if len(uri_1) == len(uri_2):
        for loc_1, loc_2 in zip(uri_1, uri_2):
            if isinstance(loc_1, FlexibleLocation):
                continue
            if isinstance(loc_2, FlexibleLocation):
                continue
            
            if loc_1 != loc_2:
                break
        else:
            return True
    return False


class NumLocation(FlexibleLocation):
    
    def __init__(self, digit: int) -> None:
        if digit < 1:
            raise ValueError("'digit' must be bigger than 0.")
        
        self._digit = digit
        
    def is_valid(self, loc: str) -> bool:
        try:
            _ = int(loc)
            
            if len(loc) != self._digit:
                return False
            return True
        except ValueError:
            return False
        
        
class StringLocation(FlexibleLocation):
    
    def __init__(self, max: Optional[int] = None) -> None:
        if max and max < 1:
            raise ValueError("'max' must be bigger than 0.")

        self._max = max
        
    def is_valid(self, loc: str) -> bool:
        if self._max is None:
            return True
        
        len_loc = len(loc)
        if len_loc > self._max or len_loc == 0:
            return False
        return True
