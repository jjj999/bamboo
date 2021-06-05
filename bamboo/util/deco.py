from __future__ import annotations
import typing as t


__all__ = [
    "awaitable_property",
    "awaitable_cached_property",
    "cached_property",
    "class_property",
    "joint_funcs",
    "joint_methods",
]


def joint_funcs(*func: t.Callable[[], None]) -> t.Callable[[], None]:
    def joint():
        for f in func:
            f()
    return joint


def joint_methods(
    *methods: t.Callable[[t.Any], None],
) -> t.Callable[[t.Any], None]:
    def joint(obj: t.Any):
        for m in methods:
            m(obj)
    return joint


Object = t.TypeVar("Object")
ReturnGetter = t.TypeVar("ReturnGetter")


class cached_property(t.Generic[Object, ReturnGetter]):

    def __init__(
        self,
        fget: t.Callable[[Object], ReturnGetter]
    ) -> None:
        self.__doc__ = getattr(fget, "__doc__")
        self._fget = fget
        self._obj2val: t.Dict[Object, ReturnGetter] = {}

    def __get__(
        self,
        obj: t.Union[Object, None],
        clazz: t.Optional[t.Type[Object]] = None
    ) -> t.Union[cached_property, ReturnGetter]:
        if obj is None:
            return self
        if self._fget is not None:
            val = self._obj2val.get(obj)
            if val is None:
                val = self._fget(obj)
                self._obj2val[obj] = val
            return val
        raise AttributeError("'getter' has not been set yet.")

    def getter(
        self,
        fget: t.Callable[[Object], ReturnGetter]
    ) -> cached_property:
        self._fget = fget
        return self


class class_property(t.Generic[Object, ReturnGetter]):

    def __init__(
        self,
        fget: t.Callable[[t.Type[Object]], ReturnGetter],
        fset: t.Callable[[t.Type[Object], ReturnGetter], None] = None,
    ) -> None:
        self.__doc__ = getattr(fget, "__doc__")
        self._fget = fget
        self._fset = fset
        self._owner: t.Optional[t.Type[Object]] = None

    def __get__(
        self,
        instance: t.Union[Object, None],
        owner: t.Optional[t.Type[Object]] = None
    ) -> ReturnGetter:
        if self._fget is not None:
            return self._fget(self._owner)
        raise AttributeError("'getter' has not been set yet.")

    def __set__(
        self,
        instance: Object,
        value: ReturnGetter,
    ) -> None:
        if self._fset is None:
            raise AttributeError("'setter' has not been set yet.")
        self._fset(self._owner, value)

    def __set_name__(self, owner: t.Type[Object], name: str) -> None:
        self._owner = owner

    def getter(
        self,
        fget: t.Callable[[t.Type[Object]], ReturnGetter]
    ) -> class_property:
        self._fget = fget
        return self

    def setter(
        self,
        fset: t.Callable[[t.Type[Object], ReturnGetter], None],
    ) -> class_property:
        self._fset = fset
        return self


class awaitable_property(t.Generic[Object, ReturnGetter]):

    def __init__(
        self,
        fget: t.Callable[[Object], t.Awaitable[ReturnGetter]]
    ) -> None:
        self.__doc__ = getattr(fget, "__doc__")
        self._fget = fget

    async def __get__(
        self,
        obj: t.Union[Object, None],
        clazz: t.Optional[t.Type[Object]] = None
    ) -> t.Union[awaitable_property, ReturnGetter]:
        if obj is None:
            return self
        if self._fget is not None:
            return await self._fget(obj)
        raise AttributeError("'getter' has not been set yet.")

    def getter(
        self,
        fget: t.Callable[[Object], t.Awaitable[ReturnGetter]]
    ) -> awaitable_property:
        self._fget = fget
        return self


class awaitable_cached_property(t.Generic[Object, ReturnGetter]):

    def __init__(
        self,
        fget: t.Callable[[Object], t.Awaitable[ReturnGetter]]
    ) -> None:
        self.__doc__ = getattr(fget, "__doc__")
        self._fget = fget
        self._obj2val: t.Dict[Object, ReturnGetter] = {}

    async def __get__(
        self,
        obj: t.Union[Object, None],
        clazz: t.Optional[t.Type[Object]] = None
    ) -> t.Union[awaitable_property, ReturnGetter]:
        if obj is None:
            return self
        if self._fget is not None:
            val = self._obj2val.get(obj)
            if val is None:
                val = await self._fget(obj)
                self._obj2val[obj] = val
            return val
        raise AttributeError("'getter' has not been set yet.")

    def getter(
        self,
        fget: t.Callable[[Object], t.Awaitable[ReturnGetter]]
    ) -> awaitable_cached_property:
        self._fget = fget
        return self
