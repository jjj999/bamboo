import sys
import typing as t


if sys.version_info.minor >= 8:
    from typing import get_args, get_origin
else:
    # NOTE
    #   Below is for compatability to Python 3.7.
    #   The implementation is same as the one of Python 3.8.

    import collections

    def get_origin(tp):
        if isinstance(tp, t._GenericAlias):
            return tp.__origin__
        if tp is t.Generic:
            return t.Generic
        return None

    def get_args(tp):
        if isinstance(tp, t._GenericAlias) and not tp._special:
            res = tp.__args__
            if (
                get_origin(tp) is collections.abc.Callable and
                res[0] is not Ellipsis
            ):
                res = (list(res[:-1]), res[-1])
            return res
        return ()
