
from __future__ import annotations
from abc import ABCMeta, abstractmethod
import json
from typing import (
    Any, Dict, Sequence, Type, TypeVar, Union, get_args,
    get_origin, get_type_hints,
)
from urllib.parse import parse_qs

from bamboo.base import MediaTypes, ContentTypeHolder, ContentType
from bamboo.util.deco import class_property


class ApiData(ContentTypeHolder, metaclass=ABCMeta):
    """Base class to describe input/output data format on Endpoints as APIs.
    
    Subclasses of this class can be used an argument of `data_format` 
    decorator for callbacks on Endpoints. If input/output parameters of 
    the `data_format` are specified, the decorator validates if raw data, 
    typically a `bytes` object, has expected data format. 
    
    Subclasses of this class can define their own data formats in `__init__` 
    methods. Developers should implement `__init__` methods of the subclasses 
    such that each objects has data with expected formats by implementors. 
    
    Notes
    -----
    This class is an abstract class. So, don't initilize it and specify it 
    as an argument of the `data_format` decorator.
    
    Subclasses of this class should validate if raw data given to `__init__` 
    methods has expected formats. If the validation failes, the classes MUST 
    raise `ValidataionFailedError` to announce the failure to the 
    `data_format` decorator.
    """

    @abstractmethod
    def __init__(self, raw: bytes, content_type: ContentType) -> None:
        """
        Parameters
        ----------
        raw : bytes
            Raw data to be validated
        content_type : ContentType
            Values of `Content-Type` header
        """
        pass
    
    @class_property
    def _content_type_(cls) -> str:
        return MediaTypes.plain


class ValidationFailedError(Exception):
    """Raised if type validation of data failes."""
    pass


class BinaryApiData(ApiData):
    """API data with no format.
    
    This class can be used to describe raw data with no data format. So, 
    any received data from clients is acceptable on the class.
    
    Attributes
    ----------
    raw : bytes
        Property of raw data
        
    Examples
    --------
    ```
    class MockEndpoint(Endpoint):
    
        @data_format(input=BinaryApiData, output=None)
        def do_GET(self, rec_body: BinaryApiData) -> None:
            # get raw data of request body
            raw_data = rec_body.raw
    ```
    """
    
    def __init__(self, raw: bytes, content_type: ContentType) -> None:
        """
        Parameters
        ----------
        raw : bytes
            Raw data to be validated
        content_type : ContentType
            Values of `Content-Type` header
            
        Notes
        -----
        In objects of this class, `content_type` is not used even if any 
        `content_type` is specified.
        """
        super().__init__(raw, content_type)
        
        if not isinstance(raw, bytes):
            raise ValidationFailedError(
                f"'raw' must be a 'bytes', but was {raw.__class__.__name__}.")
        self._raw = raw
        
    @property
    def raw(self) -> bytes:
        return self._raw

        
class InvalidAnnotationError(Exception):
    """Raised if a type not convertable to JSON is included of type hints."""
    pass


ListJsonable_t = TypeVar("ListJsonable_t")
    
    
class JsonApiDataBuilder:
    """Builder for `JsonApiData`.
    
    This utility class has some class methods for validating JSON data and 
    building `JsonApiData` objects from raw data.
    
    Attributes
    ----------
    NoneType : type
        The type of None
    TYPES_ARGS : Tuple[type]
        Tuple of types acceptable to `JsonApiData` with no arguments
    TYPES_ARGS_SET : Set[type]
        Set of types acceptable to `JsonApiData` with no arguments
    TYPES_ORIGIN : Tuple[type]
        Tuple of types acceptable to `JsonApiData` with arguments
    """
    
    NoneType = type(None)
    TYPES_ARGS = (int, float, str, bool, NoneType)
    TYPES_ARGS_SET = set(TYPES_ARGS)
    TYPES_ORIGIN = (list, Union)
    
    @classmethod
    def check_annotations(cls, *types: Type) -> None:
        """Check if types are convertable to JSON data.
        
        Parameters
        ----------
        *types : Type
            Classes to be checked
            
        Raises
        ------
        InvalidAnnotationError
            Raised if a type not convertable to JSON data is detected
        """  
        def checker(types: Sequence[Type]) -> None:
            for type_ in types:
                origin = get_origin(type_)
                if origin is None:
                    if issubclass(type_, cls.TYPES_ARGS):
                        continue
                    elif issubclass(type_, JsonApiData):
                        checker(get_type_hints(JsonApiData).values())
                    else:
                        raise InvalidAnnotationError(
                            f"{type_.__name__} is an unacceptable as a type "
                            "of attributes of JsonApiData.")
                else:
                    args = get_args(type_)
                    if origin == list:
                        if not len(args):
                            raise InvalidAnnotationError(
                                "List with no arguments is not acceptable. "
                                "Specify an argument of type to list.")
                        checker([args[0]])
                    elif origin == Union:
                        # Only Optional is admitted.
                        if not (len(args) == 2 and args[1] == cls.NoneType):
                            raise InvalidAnnotationError(
                                "Attritbutes with serveral types are not "
                                "acceptable. Only 'Optional' can be used as "
                                "type hints.")
                        
                        checker([args[0]])
                    else:
                        raise InvalidAnnotationError(
                            f"{type_.__name__} is not acceptable as a type of"
                            " attributes of JsonApiData.")
        checker(types)
        
    @classmethod
    def has_valid_annotations(cls, apiclass: Type[JsonApiData]) -> None:
        """Check if `JsonApiData` has only arguments convertable to JSON.

        Parameters
        ----------
        apiclass : Type[JsonApiData]
            A subclass of the `JsonApiData`
            
        Raises
        ------
        InvalidAnnotationError
            Raised if a type not convertable to JSON data is detected
        """
        cls.check_annotations(*tuple(get_type_hints(apiclass).values()))
    
    @classmethod
    def validate_obj(cls, obj: Any, objtype: Type) -> bool:
        """Validate if given object is acceptable as a value of `JsonApiData`.

        Parameters
        ----------
        obj : Any
            Value to be validated
        objtype : Type
            Type to be validated

        Returns
        -------
        bool
            If the obj and objtype is acceptable to `JsonApiData`
        """
        origin = get_origin(objtype)
        if origin is None:
            if objtype in cls.TYPES_ARGS_SET:
                return isinstance(obj, objtype)
            return issubclass(objtype, JsonApiData) and isinstance(obj, dict)
        
        if origin == list:
            if len(obj):
                item = obj[0]
                inner_type = get_args(objtype)[0]
                return cls.validate_obj(item, inner_type)
            return True
        elif origin == Union:
            is_good = False
            for arg in get_args(objtype):
                is_good = is_good or cls.validate_obj(obj, arg)
            return is_good
        else:
            return False
    
    @classmethod
    def build(cls, apiclass: Type[JsonApiData], 
              data: Dict[str, Any]) -> JsonApiData:
        """Build new `JsonApiData` object from raw data.

        Parameters
        ----------
        apiclass : Type[JsonApiData]
            Class of new object to be generated
        data : Dict[str, Any]
            Raw data converted as a dictionary

        Returns
        -------
        JsonApiData
            New object built

        Raises
        ------
        ValidationFailedError
            Raised if type validation of raw data failes
        """
        instance = apiclass.__new__(apiclass)
        annotations = get_type_hints(apiclass)
        
        # NOTE
        #   Ignore keys of data which is not defined in the apiclass.
        for key_def, type_def in annotations.items():            
            if not (key_def in data or hasattr(apiclass, key_def)):
                raise ValidationFailedError(
                    f"Raw data has no key of '{key_def}'.")
            
            val = data.get(key_def)
            if not cls.validate_obj(val, type_def):
                raise ValidationFailedError(
                    "Invalid type was detected in received json data. "
                    f"Expected: {type_def.__name__}; "
                    f"Detected: {val.__class__.__name__}")
            
            # Set values of attributes to an instance of the apiclass.
            origin = get_origin(type_def)
            if origin is None:       
                if issubclass(type_def, JsonApiData):
                    setattr(instance, key_def, cls.build(type_def, val))
                else:
                    setattr(instance, key_def, val)
            else:
                if origin == list:
                    setattr(instance, key_def, cls._build_list(type_def, val))
                elif origin == Union:
                    possible = get_args(type_def)[0]
                    if possible in cls.TYPES_ARGS_SET:
                        setattr(instance, key_def, val)
                    elif possible == list:
                        setattr(instance, key_def,
                                cls._build_list(possible, val))
                    elif issubclass(possible, JsonApiData):
                        setattr(instance, key_def, cls.build(type_def, val))
                    else:
                        raise ValidationFailedError(
                            f"{possible.__name__} is not acceptable as a type"
                            " of attributes of JsonApiData.")
        return instance
    
    @classmethod
    def _build_list(cls, type_def: ListJsonable_t, val: list
                    ) -> ListJsonable_t:
        """Build list convertable to JSON data.

        Parameters
        ----------
        type_def : ListJsonable_t
            Type of object to be generated, must be list with an argument
        val : list
            Raw data converted as a list

        Returns
        -------
        ListJsonable_t
            Generated object
            
        Raises
        ------
        ValueError
            Raised if `type_def` is not list with an argument
        ValidationFailedError
            Raised if the argument of `type_def` is not acceptable
        """
        if not len(val):
            return val
        if not(get_origin(type_def) == list and len(get_args(type_def))):
            raise ValueError("'type_def' must be list with an argument.")

        # Check type of inner value
        inner_type = get_args(type_def)[0] 
        if inner_type in cls.TYPES_ARGS_SET:
            return val
        elif issubclass(inner_type, JsonApiData):
            return [cls.build(inner_type, item) for item in val]
        elif get_origin(inner_type) == list:
            return [cls._build_list(inner_type, item) for item in val]
        else:
            raise ValidationFailedError(
                f"{inner_type.__name__} is not acceptable as a type of "
                "attributes of JsonApiData.")

    
class JsonApiData(ApiData):
    """API data with JSON format.

    This class can be used to describe data with JSON format. This class 
    should be inheritted and its several class-attributes should be 
    defined in the subclass. Developers must define type hints of the 
    class-attribtues, which are used to validate if raw data has format 
    the type hints define.
    
    Examples
    --------
    - Defining subclass of this class
    
    ```
    class User(JsonApiData):
        name: str
        email: str
        age: int
        
    class MockApiData(JsonApiData):
        users: List[User]
    ```
    
    - Validating received data
    
    ```
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
        JsonApiDataBuilder.has_valid_annotations(cls)
            
    # NOTE
    #   DO NOT override the method. This class should be used only 
    #   by defining attributes and their types.
    def __init__(self, raw: bytes, content_type: ContentType) -> None:
        """
        Parameters
        ----------
        raw : bytes
            Raw data to be validated
        content_type : ContentType
            Values of `Content-Type` header
        """
        super().__init__(raw, content_type)
        
        encoding = content_type.charset
        if encoding is None:
            encoding = "UTF-8"
            
        media_type = content_type.media_type
        if media_type is None:
            raise ValidationFailedError(
                "'Content-Type' header was not specified. Specify "
                f"'{MediaTypes.json}' as media type.")
        if media_type.lower() != MediaTypes.json:
            raise ValidationFailedError(
                "Media type of 'Content-Type' header was not "
                f"{MediaTypes.json}, but {content_type.media_type}.")

        try:
            raw = raw.decode(encoding=encoding)
            data = json.loads(raw)
        except UnicodeDecodeError:
            raise ValidationFailedError(
                "Decoding raw data failed. The encoding was expected "
                f"{encoding}, but not corresponded.")
        except json.decoder.JSONDecodeError:
            raise ValidationFailedError(
                "Decoding raw data failed."
                "The raw data had invalid JSON format.")

        self.__dict__.update(
            JsonApiDataBuilder.build(self.__class__, data).__dict__)
        
    @class_property
    def _content_type_(cls) -> str:
        return MediaTypes.json


class XWWWFormUrlEncodedDataBuilder:
    
    TYPES_ARGS = (str,)
    
    @classmethod
    def check_annotations(cls, *types: Type) -> None:
        """Check if types are acceptable to `XWWWFormUriEncodedData` class.

        Parameters
        ----------
        *types : Type
            Classes to be checked

        Raises
        ------
        InvalidAnnotationError
            Raised if a type not acceptable
        """
        for type_ in types:
            if type_ not in cls.TYPES_ARGS:
                raise InvalidAnnotationError(
                    f"{type_.__name__} is an unacceptable as a type "
                    "of attributes of XWWWFormUrlEncodedData.")
            
    @classmethod
    def has_valid_annotations(cls, apiclass: Type[XWWWFormUrlEncodedData]
                              ) -> None:
        """Check if `XWWWFormUrlEncodedData` has only arguments with 
        acceptable types.

        Parameters
        ----------
        apiclass : Type[XWWWFormUrlEncodedData]
            A subclass of the `XWWWFormUrlEncodedData`
            
        Raises
        ------
        InvalidAnnotationError
            Raised if a type not acceptable
        """
        cls.check_annotations(*tuple(get_type_hints(apiclass).values()))
    
    @classmethod
    def build(cls, apiclass: Type[XWWWFormUrlEncodedData],
              data: str) -> XWWWFormUrlEncodedData:
        """Build new `XWWWFormUrlEncodedData` object from raw data.

        Parameters
        ----------
        apiclass : Type[XWWWFormUrlEncodedData]
            Class of new object to be generated
        data : str
            Raw data already decoded

        Returns
        -------
        XWWWFormUrlEncodedData
            New object built

        Raises
        ------
        ValidationFailedError
            Raised if type validation of raw data failes
        """
        instance = apiclass.__new__(apiclass)
        annotations = get_type_hints(apiclass)        
        data = parse_qs(data)
        
        for key_def in annotations.keys():
            if key_def not in data:
                raise ValidationFailedError(
                    f"Raw data has no key of '{key_def}'.")
                
            if len(data[key_def]) > 1:
                raise ValidationFailedError(
                    f"Duplicated keys '{key_def}' were detected.")
            
            setattr(instance, key_def, data[key_def][0])
        
        return instance
        

class XWWWFormUrlEncodedData(ApiData):
    """API data with `x-www-form-urlencoded`
    
    This class can be used to describe data with `x-www-form-urlencoded` 
    format. This class should be inheritted and its several 
    class-attributes should be defined in the subclass. Developer must 
    define type hints of the class-attributes, which are used to validate if 
    raw data has format the type hints define. In this class, the type hints 
    must be only `str`. Otherwise, `InvalidAnnotationError` will be raised.

    Examples
    --------
    - Defining subclass of this class
    
    ```
    class UserCredentials(XWWWFormUrlEncodedData):
        user_id: str
        password: str
    ```
    
    - Validating received data
    
    ```
    class MockEndpoint(Endpoint):
    
        @data_format(input=UserCredentials, output=None)
        def do_GET(self, rec_body: UserCredentials) -> None:
            # Do something...
            
            # Example
            authenticate(rec_body.user_id, rec_body.password)
    ```
    """
    
    def __init_subclass__(cls) -> None:
        XWWWFormUrlEncodedDataBuilder.has_valid_annotations(cls)
    
    def __init__(self, raw: bytes, content_type: ContentType) -> None:
        """
        Parameters
        ----------
        raw : bytes
            Raw data to be validated
        content_type : ContentType
            Values of `Content-Type` header
        """
        encoding = content_type.charset
        if encoding is None:
            encoding = "UTF-8"
            
        media_type = content_type.media_type
        if media_type is None:
            raise ValidationFailedError(
                "'Content-Type' header was not specified. Specify "
                f"'{MediaTypes.x_www_form_urlencoded}' as media type.")
        if media_type.lower() != MediaTypes.x_www_form_urlencoded:
            raise ValidationFailedError(
                "Media type of 'Content-Type' header is not "
                f"{MediaTypes.x_www_form_urlencoded}, "
                f"but {content_type.media_type}.")
        
        try:
            raw = raw.decode(encoding=encoding)
        except UnicodeDecodeError:
            raise ValidationFailedError(
                "Decoding raw data failed. The encoding was expected "
                f"{encoding}, but not corresponded.")
        
        instance = XWWWFormUrlEncodedDataBuilder.build(self.__class__, raw)
        self.__dict__.update(instance.__dict__)
    
    @class_property
    def _content_type_(cls) -> str:
        return MediaTypes.x_www_form_urlencoded
