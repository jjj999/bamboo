from __future__ import annotations
import json
import typing as t

from .base import ApiData, ApiValidationFailedError
from ..http import (
    ContentType,
    DEFAULT_CONTENT_TYPE_JSON,
    MediaTypes,
)
from ..util.deco import cached_property, class_property
from ..util.typing import get_args, get_origin


NoneType = type(None)
TYPES_ARGS = (int, float, str, bool, dict, list, NoneType)
TYPES_ARGS_SET = set(TYPES_ARGS)
TYPES_ORIGIN = (list, t.Union)


def _check_annotation(typ: t.Type) -> None:
    origin = get_origin(typ)
    if origin is None:
        if issubclass(typ, TYPES_ARGS):
            return
        elif issubclass(typ, JsonApiData):
            _has_valid_annotations(typ)
        else:
            raise TypeError(
                f"{typ.__name__} is an unacceptable as a type "
                "of attributes of JsonApiData."
            )
    elif origin == list:
        args = get_args(typ)
        if not len(args):
            raise TypeError(
                "List with no arguments is not acceptable. "
                "Specify an argument of type to list."
            )
        _check_annotation(args[0])
    elif origin == t.Union:
        # Only Optional is admitted.
        args = get_args(typ)
        if not (len(args) == 2 and args[1] == NoneType):
            raise TypeError(
                "Attritbutes with multiple types are not acceptable. "
                "Only 'Optional' can be used as type hints."
            )
        _check_annotation(args[0])
    else:
        raise TypeError(
            f"{typ.__name__} is not acceptable as a type of"
            " attributes of JsonApiData."
            )


def _has_valid_annotations(apiclass: t.Type[JsonApiData]) -> None:
    for typ in t.get_type_hints(apiclass).values():
        _check_annotation(typ)


def _validate_obj(obj: t.Any, objtype: t.Type) -> bool:
    origin = get_origin(objtype)
    if origin is None:
        if objtype in TYPES_ARGS_SET:
            return isinstance(obj, objtype)
        if issubclass(objtype, JsonApiData):
            return isinstance(obj, (dict, objtype))
        return False
    elif origin == list:
        if len(obj):
            item = obj[0]
            inner_type = get_args(objtype)[0]
            return _validate_obj(item, inner_type)
        return True
    elif origin == t.Union:
        is_good = False
        for arg in get_args(objtype):
            is_good = is_good or _validate_obj(obj, arg)
        return is_good
    else:
        return False


def _build_json_api(
    apiclass: t.Type[JsonApiData],
    data: t.Dict[str, t.Any]
) -> JsonApiData:
    instance = apiclass.__new__(apiclass)
    annotations = t.get_type_hints(apiclass)

    # NOTE
    #   Ignore keys of data which is not defined in the apiclass.
    for key_def, type_def in annotations.items():

        # Handle default values.
        if not (key_def in data or hasattr(apiclass, key_def)):
            raise ApiValidationFailedError(
                f"Raw data has no key named '{key_def}'."
            )
        if key_def in data:
            val = data.get(key_def)
        else:
            val = getattr(apiclass, key_def)

        # Validate types of values.
        if not _validate_obj(val, type_def):
            raise ApiValidationFailedError(
                "Invalid type was detected in received json data. "
                f"Expected: {type_def.__name__}; "
                f"Detected: {val.__class__.__name__}."
            )

        # Set values of attributes to an instance of the apiclass.
        # Handle only the case in which the origin is t.Optional.
        origin = get_origin(type_def)
        if origin == t.Union:
            type_def = get_args(type_def)[0]
        _set_non_optional_value(instance, type_def, key_def, val)

    return instance


def _set_non_optional_value(
    instance: JsonApiData,
    type_def: t.Any,
    key_def: str,
    val: t.Any,
) -> None:
    origin = get_origin(type_def)
    if origin is None:
        if issubclass(type_def, JsonApiData) and isinstance(val, dict):
            setattr(instance, key_def, type_def(**val))
        else:
            setattr(instance, key_def, val)
    elif origin == list:
        setattr(instance, key_def, _build_list(type_def, val))
    else:
        raise ApiValidationFailedError(
            "Something was wrong. Contact the maintainer of the framework."
        )


def _build_list(
    type_def: t.Type[list],
    val: list
) -> t.List[t.Any]:
    if not len(val):
        return val
    if not (get_origin(type_def) == list and len(get_args(type_def))):
        raise ValueError("'type_def' must be list with an argument.")

    # Check type of inner value
    inner_type = get_args(type_def)[0]
    inner_origin = get_origin(inner_type)
    if inner_origin is None:
        if issubclass(inner_type, JsonApiData):
            return [
                inner_type(**item) if isinstance(item, dict) else item
                for item in val
            ]
        return val
    elif inner_origin == list:
        return [_build_list(inner_type, item) for item in val]
    else:
        raise ApiValidationFailedError(
            f"{inner_type.__name__} is not acceptable as a type of "
            "attributes of JsonApiData."
        )


def _extract_dict(api: JsonApiData) -> t.Dict[str, t.Any]:
    cls = type(api)
    res = {}

    for key, type_def in t.get_type_hints(cls).items():
        if hasattr(api, key):
            val = getattr(api, key)
            if isinstance(val, JsonApiData):
                val = _extract_dict(val)
            elif isinstance(val, list):
                inner_type = get_args(type_def)[0]
                if issubclass(inner_type, JsonApiData):
                    val = [_extract_dict(v) for v in val]
        else:
            val = getattr(cls, key)
        res[key] = val

    return res


class JsonApiData(ApiData):
    """API data with JSON format.

    This class can be used to describe data with JSON format. This class
    should be inheritted and its several class-attributes should be
    defined in the subclass. Developers must define type hints of the
    class-attribtues, which are used to validate if raw data has format
    the type hints define.

    Examples:
        - Defining subclass of this class
        ```python
        class User(JsonApiData):
            name: str
            email: str
            age: int

        class MockApiData(JsonApiData):
            users: List[User]
        ```

        - Validating received data
        ```python
        class MockEndpoint(Endpoint):

            @data_format(input=MockApiData, output=None)
            def do_GET(self, rec_body: MockApiData) -> None:
                # Do something...

                # Example
                for user in rec_body.users:
                    print(f"user name : {user.name}")
        ```
    """

    def __init_subclass__(cls) -> None:
        _has_valid_annotations(cls)

    # NOTE
    #   DO NOT override the method. This class should be used only
    #   by defining attributes and their types.
    def __init__(self, **data: t.Any) -> None:
        mapped = _build_json_api(self.__class__, data)
        self.__dict__.update(mapped.__dict__)

    @classmethod
    def __validate__(
        cls,
        raw: bytes,
        content_type: ContentType
    ) -> JsonApiData:
        """
        Args:
            raw: Raw data to be validated.
            content_type: Values of `Content-Type` header.
        """
        super().__init__(raw, content_type)

        if content_type.charset is None:
            content_type.charset = "UTF-8"

        if not cls.verify_content_type(content_type):
            raise ApiValidationFailedError(
                "Media type of 'Content-Type' header was not "
                f"{MediaTypes.json}, but {content_type.media_type}."
            )

        try:
            raw = raw.decode(encoding=content_type.charset)
            data = json.loads(raw)
        except UnicodeDecodeError:
            raise ApiValidationFailedError(
                "Decoding raw data failed. The encoding was expected "
                f"{content_type.charset}, but not corresponded."
            )
        except json.decoder.JSONDecodeError:
            raise ApiValidationFailedError(
                "Decoding raw data failed."
                "The raw data had invalid JSON format."
            )
        return cls(**data)

    def __extract__(self) -> bytes:
        encoding = self.__content_type__.charset
        if encoding is None:
            encoding = "utf-8"
        return json.dumps(self.dict).encode(encoding=encoding)

    @cached_property
    def dict(self) -> t.Dict[str, t.Any]:
        return _extract_dict(self)

    @class_property
    def __content_type__(cls) -> ContentType:
        """Content type with `application/json; charset=UTF-8`.
        """
        return DEFAULT_CONTENT_TYPE_JSON
