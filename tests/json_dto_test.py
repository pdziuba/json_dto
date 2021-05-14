from dataclasses import dataclass, field
from unittest import TestCase

from typing import List, Dict

import jsonschema
from jsonschema import ValidationError

from json_dto import JsonDto


class JsonDtoTest(TestCase):

    def test_handle_primitive_types(self):
        # given
        @dataclass
        class PrimitiveDto(JsonDto):
            my_int: int
            my_str: str
            my_float: float
            my_bool: bool
            my_dict: dict

        payload = PrimitiveDto(my_int=123, my_str='foo', my_float=6.66, my_bool=True, my_dict={'a': 'b'})

        # when
        serialized = payload.to_json()
        deserialized = PrimitiveDto.from_json(serialized)

        # then
        self.assertEqual(deserialized, payload)

    def test_handle_generic_list_of_json_dto(self):
        # given
        @dataclass
        class SimpleDto(JsonDto):
            id: int
            name: str

        @dataclass
        class ListDto(JsonDto):
            my_list: List[SimpleDto]

        payload = ListDto(my_list=[SimpleDto(1, 'foo'), SimpleDto(2, 'bar')])

        # when
        serialized = payload.to_json()
        deserialized = ListDto.from_json(serialized)

        # then
        self.assertEqual(deserialized, payload)

    def test_handle_generic_dict_of_json_dto(self):
        # given
        @dataclass
        class SimpleDto(JsonDto):
            id: int
            name: str

        @dataclass
        class DictDto(JsonDto):
            my_dict: Dict[str, SimpleDto]

        payload = DictDto(my_dict={'foo': SimpleDto(1, 'foo'), 'bar': SimpleDto(2, 'bar')})

        # when
        serialized = payload.to_json()
        deserialized = DictDto.from_json(serialized)

        # then
        self.assertEqual(deserialized, payload)

    def test_handle_json_schema(self):
        # given
        @dataclass
        class PrimitiveDto(JsonDto):
            my_int: int
            my_str: str
            my_float: float
            my_bool: bool = None
            my_dict: dict = None

        result = {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "PrimitiveDto",
            "type": "object",
            "properties": {
                'my_bool': {'type': 'boolean'},
                'my_dict': {"type": "object"},
                'my_float': {'type': 'number'},
                'my_int': {'type': 'integer'},
                'my_str': {'type': 'string'}
            },
            "required": ["my_int", "my_str", "my_float"]
        }

        # when
        schema = PrimitiveDto.get_json_schema()

        # then
        self.assertEqual(schema, result)

    def test_nested_list_dto_json_schema(self):
        # given
        @dataclass
        class PrimitiveDto(JsonDto):
            my_int: int
            my_str: str
            my_float: float
            my_bool: bool = None
            my_dict: dict = None

        @dataclass
        class NestedDto(JsonDto):
            my_list: List[PrimitiveDto] = field(default_factory=list)

        result = {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "NestedDto",
            "type": "object",
            "properties": {
                'my_list': {'type': 'array', 'items': {
                    'type': 'object',
                    'properties': {
                        'my_bool': {'type': 'boolean'},
                        'my_dict': {"type": "object"},
                        'my_float': {'type': 'number'},
                        'my_int': {'type': 'integer'},
                        'my_str': {'type': 'string'}
                    }
                }},
            },
            "required": ['my_list']
        }

        # when
        schema = NestedDto.get_json_schema()

        # then
        self.assertEqual(schema, result)

    def test_nested_dict_dto_json_schema(self):
        # given
        @dataclass
        class PrimitiveDto(JsonDto):
            my_int: int
            my_str: str
            my_float: float
            my_bool: bool = None
            my_dict: dict = None

        @dataclass
        class NestedDto(JsonDto):
            my_dict: Dict[str, PrimitiveDto] = field(default_factory=list)

        result = {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "NestedDto",
            "type": "object",
            "properties": {
                'my_dict': {
                    'type': 'object',
                    'additionalProperties': {
                        'type': 'object',
                        'properties': {
                            'my_bool': {'type': 'boolean'},
                            'my_dict': {"type": "object"},
                            'my_float': {'type': 'number'},
                            'my_int': {'type': 'integer'},
                            'my_str': {'type': 'string'}
                        },
                        'required': ['my_int',
                                     'my_str',
                                     'my_float'],
                    }
                },
            },
            "required": ['my_dict']
        }

        # when
        schema = NestedDto.get_json_schema()

        # then
        self.assertEqual(schema, result)

    def test_nested_dict_dto_json_schema_is_consumable(self):
        # given
        @dataclass
        class PrimitiveDto(JsonDto):
            my_int: int
            my_str: str
            my_float: float
            my_bool: bool = None
            my_dict: dict = None

        @dataclass
        class NestedDto(JsonDto):
            my_dict: Dict[str, PrimitiveDto] = field(default_factory=list)

        schema = NestedDto.get_json_schema()

        # when
        payload = NestedDto({'a': PrimitiveDto(1, 'str', 3.11, True, {})}).to_json()

        # then
        self.assertIsNone(jsonschema.validate(payload, schema))

    def test_nested_dict_dto_json_schema_raises_error_on_invalid_payload(self):
        # given
        @dataclass
        class PrimitiveDto(JsonDto):
            my_int: int
            my_str: str
            my_float: float
            my_bool: bool = None
            my_dict: dict = None

        @dataclass
        class InvalidDto(JsonDto):
            kaczka: int

        @dataclass
        class NestedDto(JsonDto):
            my_dict: Dict[str, PrimitiveDto] = field(default_factory=list)

        schema = NestedDto.get_json_schema()

        # when
        payload = NestedDto({'a': InvalidDto(123)}).to_json()

        # then
        with self.assertRaises(ValidationError):
            jsonschema.validate(payload, schema)

