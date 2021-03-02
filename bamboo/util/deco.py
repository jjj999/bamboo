
from __future__ import annotations

from typing import (
    Any,
    Awaitable,
    Callable, Dict,
    Generic,
    Optional,
    Type,
    TypeVar,
    Union,
)


__all__ = [
    "awaitable_property",
    "awaitable_cached_property",
    "cached_property",
    "class_property",
    "joint_funcs",
    "joint_methods",
]


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

    def __init__(
        self,
        fget: Callable[[Object], ReturnGetter]
    ) -> None:
        self.__doc__ = getattr(fget, "__doc__")
        self._fget = fget
        self._obj2val: Dict[Object, ReturnGetter] = {}

    def __get__(
        self,
        obj: Union[Object, None],
        clazz: Optional[Type[Object]] = None
    ) -> Union[cached_property, ReturnGetter]:
        if obj is None:
            return self
        if self._fget is not None:
            val = self._obj2val.get(obj)
            if val is None:
                val = self._fget(obj)
                self._obj2val[obj] = val
            return val
        raise AttributeError(
            "'getter' has not been set yet."
        )

    def getter(
        self,
        fget: Callable[[Object], ReturnGetter]
    ) -> cached_property:
        self._fget = fget
        return self


class class_property(Generic[Object, ReturnGetter]):

    def __init__(
        self,
        fget: Callable[[Object], ReturnGetter]
    ) -> None:
        self.__doc__ = getattr(fget, "__doc__")
        self._fget = fget

    def __get__(
        self,
        obj: Union[Object, None],
        clazz: Optional[Type[Object]] = None
    ) -> ReturnGetter:
        if clazz is None:
            clazz = type(obj)

        if self._fget is not None:
            return self._fget(clazz)
        raise AttributeError(
            "'getter' has not been set yet."
        )

    def getter(
        self,
        fget: Callable[[Object], ReturnGetter]
    ) -> class_property:
        self._fget = fget
        return self


class awaitable_property(Generic[Object, ReturnGetter]):

    def __init__(
        self,
        fget: Callable[[Object], Awaitable[ReturnGetter]]
    ) -> None:
        self.__doc__ = getattr(fget, "__doc__")
        self._fget = fget

    async def __get__(
        self,
        obj: Union[Object, None],
        clazz: Optional[Type[Object]] = None
    ) -> Union[awaitable_property, ReturnGetter]:
        if obj is None:
            return self
        if self._fget is not None:
            return await self._fget(obj)
        raise AttributeError(
            "'getter' has not been set yet."
        )

    def getter(
        self,
        fget: Callable[[Object], Awaitable[ReturnGetter]]
    ) -> awaitable_property:
        self._fget = fget
        return self


class awaitable_cached_property(Generic[Object, ReturnGetter]):

    def __init__(
        self,
        fget: Callable[[Object], Awaitable[ReturnGetter]]
    ) -> None:
        self.__doc__ = getattr(fget, "__doc__")
        self._fget = fget
        self._obj2val: Dict[Object, ReturnGetter] = {}

    async def __get__(
        self,
        obj: Union[Object, None],
        clazz: Optional[Type[Object]] = None
    ) -> Union[awaitable_property, ReturnGetter]:
        if obj is None:
            return self
        if self._fget is not None:
            val = self._obj2val.get(obj)
            if val is None:
                val = await self._fget(obj)
                self._obj2val[obj] = val
            return val
        raise AttributeError(
            "'getter' has not been set yet."
        )

    def getter(
        self,
        fget: Callable[[Object], Awaitable[ReturnGetter]]
    ) -> awaitable_cached_property:
        self._fget = fget
        return self
