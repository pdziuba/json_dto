import enum
from datetime import datetime
from typing import get_type_hints

DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S%z'


def is_generic_list(type_):
    if hasattr(type_, '__extra__'):
        # python 3.5/3.6
        return type_.__extra__ == list
    elif hasattr(type_, '__origin__'):
        # python >=3.7
        return type_.__origin__ == list


def is_generic_dict(type_):
    if hasattr(type_, '__extra__'):
        # python 3.5/3.6
        return type_.__extra__ == dict
    elif hasattr(type_, '__origin__'):
        # python >=3.7
        return type_.__origin__ == dict


class JsonDto:

    @classmethod
    def get_type_hints(cls) -> dict:
        # Cache type hints and handle class inheritance
        hints_field = '_type_hints_' + cls.__name__
        if getattr(cls, hints_field, None) is None:
            setattr(cls, hints_field, get_type_hints(cls))
        return getattr(cls, hints_field)

    @staticmethod
    def serialize_value(value, type_):
        if value is None:
            return None

        def serialize_datetime(value_: datetime):
            return value_.strftime(DEFAULT_DATE_FORMAT)

        def serialize_enum(value_: enum.Enum):
            return value_.name

        def serialize_nested(value_):
            return value_.to_json()

        if type_ in [str, int, bool, float, dict, list]:
            return value
        elif type_ == datetime:
            return serialize_datetime(value)
        elif is_generic_list(type_):
            generic_type = type_.__args__[0]
            return [JsonDto.serialize_value(v, generic_type) for v in value]
        elif is_generic_dict(type_):
            key_type = type_.__args__[0]
            val_type = type_.__args__[1]
            return {
                JsonDto.serialize_value(key, key_type): JsonDto.serialize_value(val, val_type)
                for key, val in value.items()
            }
        elif issubclass(type_, enum.Enum):
            return serialize_enum(value)
        elif issubclass(type_, JsonDto):
            return serialize_nested(value)
        else:
            raise NotImplementedError(f'Serializer for {str(type_)} not implemented yet')

    def to_json(self):
        result = {}

        for name, type_ in self.get_type_hints().items():
            result[name] = self.serialize_value(getattr(self, name), type_)

        return result

    @classmethod
    def from_json(cls, payload: dict, _class=None):

        def deserialize_datetime(value: str):
            if isinstance(value, datetime):
                # nothing to do here
                return value
            try:
                return datetime.strptime(value, DEFAULT_DATE_FORMAT) if value else None
            except ValueError as e:
                # todo: handle it some other way
                print(f'Error while deserializing date {str(e)}')
                return None

        def deserialize_enum(value: str, enum_class: enum.Enum):
            return enum_class[value]

        def deserialize_nested(value: str, nested_class):
            return nested_class.from_json(value)

        def deserialize(type_, value):
            if value is None:
                return None
            if type_ in [str, int, bool, float, dict, list]:
                return type_(value)
            elif type_ == datetime:
                return deserialize_datetime(value)
            elif is_generic_list(type_):
                generic_type = type_.__args__[0]
                return [deserialize(generic_type, v) for v in value]
            elif is_generic_dict(type_):
                key_type = type_.__args__[0]
                val_type = type_.__args__[1]
                return {
                    deserialize(key_type, key): deserialize(val_type, val)
                    for key, val in value.items()
                }
            elif issubclass(type_, enum.Enum):
                return deserialize_enum(value, type_)
            elif issubclass(type_, JsonDto):
                return deserialize_nested(value, type_)
            else:
                raise NotImplementedError(f'Deserializer for {str(type_)} not implemented yet')

        if _class is None:
            _class = cls
        return _class(
            **{
                name: deserialize(type_, payload[name]) for name, type_ in _class.get_type_hints().items()
                if name in payload
            }
        )

    @classmethod
    def get_json_schema(cls):
        def type_hint_to_schema(type_):
            if type_ == int:
                return {
                    "type": ["number", "null"]
                }
            if type_ == str:
                return {
                    "type": ["string", "null"]
                }
            if type_ == datetime:
                return {
                    "type": ["string", "null"]
                }
            if issubclass(type_, enum.Enum):
                return {
                    "type": ["string", "null"]
                }
            if issubclass(type_, JsonDto):
                return {
                    "$ref": type_.__name__
                }
            if issubclass(type_, list):
                return {
                    "type": ["array", "null"]
                }

        return {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": cls.__name__,
            "type": "object",
            "properties": {
                key: type_hint_to_schema(type_) for key, type_ in get_type_hints(cls).items()
            },
            "required": []
        }
