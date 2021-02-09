
from __future__ import annotations
from abc import ABCMeta, abstractmethod
import json
from typing import (
    Any, Dict, Sequence, Union, get_args, get_origin, get_type_hints,
)


class ApiData(metaclass=ABCMeta):
    
    def __init__(self, body) -> None:
        pass
    
    @abstractmethod
    def _attach(self, data) -> None:
        pass
    
    
class BinaryApiData(ApiData):
    
    raw: bytes
    
    def __init__(self, body: bytes) -> None:
        super().__init__(body)
        
        self._attach(body)
    
    def _attach(self, body: bytes) -> BinaryApiData:
        setattr(self, "raw", body)


_NoneType = type(None)
    
json_value_types_args = (
    int, float, str, bool, _NoneType,
)

json_value_types_origin = (
    list, Union,
)


def is_jsonable(types: Sequence) -> bool:
    
    def checker(types: Sequence):
        for type_ in types:
            origin = get_origin(type_)
            if origin is None:
                if issubclass(type_, json_value_types_args):
                    continue
                elif issubclass(type_, JsonApiData):
                    checker(get_type_hints(JsonApiData).values())
                else:
                    raise ValueError()
            else:
                if origin not in json_value_types_origin:
                    raise ValueError()
        
                args = get_args(type_)
                if origin == list:
                    if not len(args):
                        raise ValueError()
                    checker([args[0]])
                elif origin == Union:
                    # Only Optional is admitted.
                    if len(args) != 2:
                        raise ValueError()
                    if args[1] != _NoneType:
                        raise ValueError()
                    
                    checker([args[0]])
                else:
                    raise ValueError()
                
    try:
        checker(types)
        return True
    except ValueError:
        return False
    
    
def _validate_jsonable(val, valtype) -> bool:
    origin = get_origin(valtype)
    if origin is None:
        if valtype in json_value_types_args:
            return isinstance(val, valtype)
        else:
            return issubclass(valtype, JsonApiData) and isinstance(val, dict)
    
    if origin == list:
        if len(val):
            item = val[0]
            inner_type = get_args(valtype)[0]
            return _validate_jsonable(item, inner_type)
        return True
    elif origin == Union:
        is_good = False
        for arg in get_args(valtype):
            is_good = is_good or _validate_jsonable(val, arg)
        return is_good
    else:
        return False

        
class NotJsonableAnnotationError(Exception):
    """Raised if not 'jsonable' type is included of type hints."""
    pass


def _attach_jsonable_list(val: list, val_type) -> list:
    if len(val):
        # Check type of inner value
        inner_val_type = get_args(val_type)[0]
        
        if inner_val_type in json_value_types_args:
            return val
        elif issubclass(inner_val_type, JsonApiData):
            return [inner_val_type(item) for item in val]
        else:
            return [_attach_jsonable_list(item, inner_val_type) for item in val]
    else:
        return val 

    
class JsonApiData(ApiData):
    
    def __init_subclass__(cls) -> None:
        if not is_jsonable(get_type_hints(cls).values()):
            raise NotJsonableAnnotationError(
                "Not 'jsonable' type was included of type hints.")
            
    def __init__(self, body: Union[bytes, str, dict]) -> None:
        super().__init__(body)

        data = body        
        if isinstance(body, (bytes, str)):
            data = json.loads(body)
        self._attach(data)

    def _attach(self, data: Dict[str, Any]) -> None:
        annotations = get_type_hints(self.__class__)
        
        for key_def, key_rec in zip(annotations.keys(), data.keys()):
            if key_def != key_rec:
                raise KeyError(f"Undefined key {key_rec} was detected.")
            
            val = data[key_rec]
            val_type_def = annotations[key_def]
            if not _validate_jsonable(val, val_type_def):
                raise TypeError("Invalid type was detected in received json data.")
            
            origin = get_origin(val_type_def)
            if origin is None:       
                if issubclass(val_type_def, JsonApiData):
                    setattr(self, key_def, val_type_def(val))
                else:
                    setattr(self, key_def, val)
            else:
                if origin == list:
                    setattr(self, key_def, _attach_jsonable_list(val, val_type_def))
                elif origin == Union:
                    possible = get_args(val_type_def)[0]
                    if isinstance(val, json_value_types_args):
                        setattr(self, key_def, val)
                    elif isinstance(val, list):
                        setattr(self, key_def, _attach_jsonable_list(val, possible))
                    else:
                        setattr(self, key_def, possible(val))
