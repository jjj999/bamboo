

from typing import (
    Any, Callable, Generic, Optional, Type, TypeVar, Union,
)


def joint_funcs(*func: Callable[[], None]) -> Callable[[], None]:
    def joint():
        for f in func:
            f()
    return joint


def joint_methods(*methods: Callable[[Any], None]) -> Callable[[Any], None]:
    def joint(obj: Any):
        for m in methods:
            m(obj)
    return joint


Object = TypeVar("Object")
ReturnGetter = TypeVar("ReturnGetter")


class cached_property(Generic[Object, ReturnGetter]):
    
    def __init__(self, 
                 fget: Callable[[Object], ReturnGetter]) -> None:
        self.__doc__ = getattr(fget, "__doc__")
        self._fget = fget
        
    def __get__(self, obj: Union[Object, None], 
                clazz: Optional[Type[Object]] = None) -> ReturnGetter:
        if obj is None:
            return self
        if self._fget is not None:
            value = self._fget(obj)
            obj.__dict__[self._fget.__name__] = value
            return value
        raise AttributeError(
            "'getter' has not been set yet."
        )
    
    def getter(self, fget: Callable[[Object], ReturnGetter]):
        self._fget = fget
        return self
    
    
class class_property(Generic[Object, ReturnGetter]):
    
    def __init__(self,
                 fget: Callable[[Object], ReturnGetter]) -> None:
        self.__doc__ = getattr(fget, "__doc__")
        self._fget = fget
        
    def __get__(self, obj: Union[Object, None], 
                clazz: Optional[Type[Object]] = None) -> ReturnGetter:
        if clazz is None:
            clazz = type(obj)
            
        if self._fget is not None:
            return self._fget(clazz)
        raise AttributeError(
            "'getter' has not been set yet."
        )
            
    def getter(self, fget: Callable[[Object], ReturnGetter]):
        self._fget = fget
        return self
