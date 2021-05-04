from dataclasses import dataclass
from unittest import TestCase

from typing import List, Dict

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