from __future__ import annotations
from abc import ABCMeta, abstractmethod
import typing as t

from ..http import (
    ContentType,
    ContentTypeHolder,
    DEFAULT_CONTENT_TYPE_PLAIN,
)
from ..util.deco import class_property


class ApiValidationFailedError(Exception):
    """Raised if type validation of data failes."""
    pass


class ApiData(ContentTypeHolder, metaclass=ABCMeta):
    """Base class to describe input/output data format on Endpoints as APIs.

    Subclasses of this class can be used an argument of `data_format`
    decorator for callbacks on Endpoints. If input/output parameters of
    the `data_format` are specified, the decorator validates if raw data,
    typically a `bytes` object, has expected data format.

    Subclasses of this class can define their own data formats in `__init__`
    methods. Developers should implement `__init__` methods of the subclasses
    such that each objects has data with expected formats by implementors.

    Note:
        This class is an abstract class. So, don't initilize it and specify it
        as an argument of the `data_format` decorator.

        Subclasses of this class should validate if raw data given to
        `__init__` methods has expected formats. If the validation failes,
        the classes MUST raise `ValidataionFailedError` to announce the
        failure to the `data_format` decorator.
    """

    @classmethod
    @abstractmethod
    def __validate__(cls, raw: bytes, content_type: ContentType) -> ApiData:
        """
        Args:
            raw : Raw data to be validated.
            content_type : Values of `Content-Type` header.
        """
        pass

    @abstractmethod
    def __extract__(self) -> t.Union[bytes, t.Iterable[bytes]]:
        pass


class BinaryApiData(ApiData):
    """API data with no format.

    This class can be used to describe raw data with no data format. So,
    any received data from clients is acceptable on the class.

    Examples:
        ```python
        class MockEndpoint(Endpoint):

            @data_format(input=BinaryApiData, output=None)
            def do_GET(self, rec_body: BinaryApiData) -> None:
                # get raw data of request body
                raw_data = rec_body.raw
        ```
    """

    def __init__(self, data: bytes) -> None:
        """
        Args:
            data: Binary data.
        """
        self._data = data

    @classmethod
    def __validate__(cls, raw: bytes, content_type: ContentType) -> BinaryApiData:
        """
        Args:
            raw: Raw data to be validated.
            content_type: Values of `Content-Type` header.

        Returns:
            The BinaryApiData object validated succcessfully.

        Note:
            In objects of this class, `content_type` is not used even if any
            `content_type` is specified.
        """
        if not isinstance(raw, bytes):
            raise ApiValidationFailedError(f"'raw' must be a 'bytes'.")
        return cls(raw)

    @property
    def raw(self) -> bytes:
        """Raw data of input binary."""
        return self._data

    @class_property
    def __content_type__(cls) -> ContentType:
        """Content type with `text/plain`.
        """
        return DEFAULT_CONTENT_TYPE_PLAIN

    def __extract__(self) -> bytes:
        return self.raw
