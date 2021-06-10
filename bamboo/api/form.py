from __future__ import annotations
import typing as t
import urllib.parse

from .base import ApiData, ApiValidationFailedError
from ..http import ContentType, MediaTypes
from ..util.deco import cached_property, class_property


TYPES_ARGS = (str,)


def _check_annotation(typ: t.Type) -> None:
    if typ not in TYPES_ARGS:
        raise TypeError(
            f"{typ.__name__} is unacceptable as a type "
            "of attributes of FormApiData."
        )


def _has_valid_annotations(apiclass: t.Type[FormApiData]) -> None:
    for typ in t.get_type_hints(apiclass).values():
        _check_annotation(typ)


def _build_dict(
    apiclass: t.Type[FormApiData],
    **data: str,
) -> FormApiData:
    instance = apiclass.__new__(apiclass)
    annotations = t.get_type_hints(apiclass)

    for key in annotations.keys():
        if key not in data:
            raise ApiValidationFailedError(
                f"Raw data has no key of '{key}'."
            )
        if type(data[key]) not in TYPES_ARGS:
            raise ApiValidationFailedError(
                "Invalid type was detected. "
                f"Expected {apiclass.__name__}.{key} was a str."
            )
        setattr(instance, key, data[key])
    return instance


def _build_form_api(
    apiclass: t.Type[FormApiData],
    data: str
) -> FormApiData:
    parsing = {}
    for key, val in urllib.parse.parse_qs(data).items():
        if len(val) > 1:
            raise ApiValidationFailedError(
                f"Duplicated keys '{key}' were detected."
            )
        parsing[key] = val[0]
    return _build_dict(apiclass, **parsing)


class FormApiData(ApiData):
    """API data with `x-www-form-urlencoded`

    This class can be used to describe data with `x-www-form-urlencoded`
    format. This class should be inheritted and its several
    class-attributes should be defined in the subclass. Developer must
    define type hints of the class-attributes, which are used to validate if
    raw data has format the type hints define. In this class, the type hints
    must be only `str`. Otherwise, `TypeError` will be raised.

    Examples:
        - Defining subclass of this class
        ```python
        class UserCredentials(FormApiData):
            user_id: str
            password: str
        ```

        - Validating received data
        ```python
        class MockEndpoint(Endpoint):

            @data_format(input=UserCredentials, output=None)
            def do_GET(self, rec_body: UserCredentials) -> None:
                # Do something...

                # Example
                authenticate(rec_body.user_id, rec_body.password)
        ```
    """

    def __init_subclass__(cls) -> None:
        _has_valid_annotations(cls)

    def __init__(self, **data: str) -> None:
        """
        Args:
            raw: Raw data to be validated.
            content_type: Values of `Content-Type` header.
        """
        mapped = _build_dict(self.__class__, **data)
        self.__dict__.update(mapped.__dict__)

    @classmethod
    def __validate__(
        cls,
        raw: bytes,
        content_type: ContentType,
    ) -> FormApiData:
        """
        Args:
            raw: Raw data to be validated.
            content_type: Values of `Content-Type` header.

        Returns:
            The FormApiData object validated successfully.
        """
        if content_type.charset is None:
            content_type.charset = "UTF-8"

        if not cls.verify_content_type(content_type):
            raise ApiValidationFailedError(
                "Media type of 'Content-Type' header is not "
                f"{MediaTypes.x_www_form_urlencoded}, "
                f"but {content_type.media_type}."
            )

        try:
            raw = raw.decode(encoding=content_type.charset)
        except UnicodeDecodeError as e:
            raise ApiValidationFailedError(
                "Decoding raw data failed. The encoding was expected "
                f"{content_type.charset}, but not corresponded."
            ) from e
        return _build_form_api(cls, raw)

    def __extract__(self) -> bytes:
        encoding = self.__content_type__.charset
        if encoding is None:
            encoding = "utf-8"
        return self.string.encode(encoding=encoding)

    @cached_property
    def dict(self) -> t.Dict[str, t.Any]:
        keys = t.get_type_hints(self.__class__).keys()
        return {key: getattr(self, key) for key in keys}

    @cached_property
    def string(self) -> str:
        return "&".join([f"{key}={val}" for key, val in self.dict.items()])

    @class_property
    def __content_type__(cls) -> ContentType:
        """Content type with `application/x-www-form-urlencoded`.
        """
        return ContentType(MediaTypes.x_www_form_urlencoded)
