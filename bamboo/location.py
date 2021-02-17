
from abc import ABCMeta, abstractmethod
from typing import Optional, Tuple, Union


class FlexibleLocation(metaclass=ABCMeta):
    """Base class of flexible location.
    
    Location is concept representing each pieces of path of URI, i.e. 
    locations can configures a path of URI by joining them with 
    separator `/`. 
    
    Location has type of `str` or subclasses of this class. If a location 
    is `str`, then the location is called a static location. Otherwise, 
    the location is called a flexible location. Flexible locations means 
    location with some kind of logical rules of strings. The logic of rules 
    can be implemented on `is_valid` method, returning if specified string 
    is valid in the rules. 
    """
    
    @abstractmethod
    def is_valid(self, loc: str) -> bool:
        pass


Location_t = Union[str, FlexibleLocation]
Uri_t = Tuple[Location_t]


def is_flexible_uri(uri: Uri_t) -> bool:
    """Judge if specified `uri` has one or more flexible location.

    Parameters
    ----------
    uri : Uri_t
        URI pattern to be judged

    Returns
    -------
    bool
        If specified `uri` has one or more flexible location.
    """
    for loc in uri:
        if isinstance(loc, FlexibleLocation):
            return True
    return False


def is_duplicated_uri(uri_1: Uri_t, uri_2: Uri_t) -> bool:
    """Judge if a couple of specified URI patterns has same pattern.

    Parameters
    ----------
    uri_1 : Uri_t
        URI pattern to be judged
    uri_2 : Uri_t
        URI pattern to be judged

    Returns
    -------
    bool
        If two URIs has same pattern or not
    """
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


class AsciiDigitLocation(FlexibleLocation):
    """Flexible location representing location of number in ASCII code.
    """
    
    def __init__(self, digits: int) -> None:
        """
        Parameters
        ----------
        digits : int
            Number of digits which the location accepts

        Raises
        ------
        ValueError
            Raised if `digits` is 0 or less
        """
        if digits < 1:
            raise ValueError("'digits' must be bigger than 0.")
        
        self._digits = digits
        
    def is_valid(self, loc: str) -> bool:
        """Judge if specified `loc` is valid location or not.

        Parameters
        ----------
        loc : str
            Location to be judged

        Returns
        -------
        bool
            If specified location is valid or not
        """
        return loc.isascii() and loc.isdigit() and len(loc) == self._digits
        
        
class AnyStringLocation(FlexibleLocation):
    """Flexible location representing string with no rules.
    """
    
    def __init__(self, max: Optional[int] = None) -> None:
        """
        Parameters
        ----------
        max : Optional[int], optional
            Max length of string of location, by default `None`

        Raises
        ------
        ValueError
            Raised if `max` is 0 or less
            
        Notes
        -----
        If the argument `max` is `None`, then any length of string 
        will be accepted.
        """
        if max and max < 1:
            raise ValueError("'max' must be bigger than 0.")

        self._max = max
        
    def is_valid(self, loc: str) -> bool:
        """Judge if specified `loc` is valid location or not.

        Parameters
        ----------
        loc : str
            Location to be judged

        Returns
        -------
        bool
            If specified location is valid or not
        """
        if self._max is None:
            return True
        
        len_loc = len(loc)
        if len_loc > self._max or len_loc == 0:
            return False
        return True
