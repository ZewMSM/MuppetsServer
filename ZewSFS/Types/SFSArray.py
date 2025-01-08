from __future__ import annotations

import io
import json

from .BaseType import BaseType
from .Bool import Bool
from .BoolArray import BoolArray
from .Byte import Byte
from .ByteArray import ByteArray
from .Double import Double
from .DoubleArray import DoubleArray
from .Float import Float
from .FloatArray import FloatArray
from .Int import Int
from .IntArray import IntArray
from .Long import Long
from .LongArray import LongArray
from .Null import Null
from .Short import Short
from .ShortArray import ShortArray
from .UtfString import UtfString
from .UtfStringArray import UtfStringArray
from ..Exceptions import InvalidDataType


class SFSArray(BaseType):
    def __init__(self, name: str = None, value: list = None):
        """
        Constructs a new SFSArray instance.

        Args:
            name (str, optional): The name of the SFSArray. Defaults to None.
            value (list, optional): The list of values in the SFSArray. Defaults to None.
        """

        if name is None:
            name = ""
        if value is None:
            value = []
        super().__init__("sfs_array", name, value)

    def __str__(self) -> str:
        """
        Returns a string representation of the SFSArray.

        Returns:
            str: A string representation of the SFSArray.
        """

        from . import stringify_array
        return f"(sfs_array){' ' + self.get_name() if len(self.get_name()) > 0 else ''}: \n" + stringify_array(1, self, "")

    def __len__(self) -> int:
        """
        Returns the length of the SFSArray.

        Returns:
            int: The length of the SFSArray.
        """

        return len(self.get_value())

    def __iter__(self):
        """
        Returns an iterator for the SFSArray.

        Returns:
            iterator: An iterator for the SFSArray.
        """

        return iter(self.get_value())

    def __getitem__(self, index: int) -> BaseType:
        """
        Returns the item at the specified index.

        Args:
            index (int): The index of the item.

        Returns:
            BaseType: The item at the specified index.
        """

        return self.get_item(index).get_value()

    def __delitem__(self, key):
        """
        Removes the item at the specified index.

        Args:
            key (int): The index of the item.
        """

        self.remove_item(key)

    def pack(self) -> bytes:
        """
        Packs the SFSArray into bytes.

        Returns:
            bytes: The bytes representation of the SFSArray.
        """

        packed = self.pack_name() + bytes([17]) + len(self).to_bytes(2, "big")
        for i in self:
            packed += i.pack()

        return packed

    def tokenize(self):
        tokenized = []

        biggest_obj = SFSArray()
        for item in self.get_value():
            item_type = item.get_type()
            if item_type in ("sfs_object", "sfs_array"):
                if len(biggest_obj) < len(item):
                    biggest_obj = item
            else:
                _objs = 0
                tokenized.append(item_type)

        if len(biggest_obj) > 0:
            tokenized.append(biggest_obj.tokenize())

        return sorted(tokenized)

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> SFSArray:
        """
        Unpacks a bytes buffer into an SFSArray instance.

        Args:
            buffer (io.BytesIO | bytes): The bytes buffer to unpack.
            name (str | None, optional): The name of the SFSArray. Defaults to None.

        Returns:
            SFSArray: The unpacked SFSArray instance.
        """

        from . import sfs2x_datatypes
        from .SFSObject import SFSObject

        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)
            buffer.read(1)

        result = SFSArray(name)
        length = int.from_bytes(buffer.read(2), "big")
        for _ in range(length):
            value = None
            type_id = int.from_bytes(buffer.read(1), "big")
            if type_id > 18:
                raise InvalidDataType
            if type_id == 18:
                value = SFSObject.unpack(buffer, False)
            elif type_id == 17:
                value = SFSArray.unpack(buffer, False)
            else:
                value = list(sfs2x_datatypes.values())[type_id].unpack(buffer, False)
            result.add_item(value)

        return result

    def add_item(self, item: BaseType):
        """
        Adds an item to the SFSArray.

        Args:
            item (BaseType): The item to add.
        """

        self.get_value().append(item)
        return self

    def insert_item(self, index: int, item: BaseType):
        """
        Inserts an item into the SFSArray at the specified index.

        Args:
            index (int): The index to insert the item at.
            item (BaseType): The item to insert.
        """

        self.get_value().insert(index, item)
        return self

    def get_item(self, index: int) -> BaseType:
        """
        Returns the item at the specified index.

        Args:
            index (int): The index of the item.

        Returns:
            BaseType: The item at the specified index.
        """

        return self.get_value()[index]

    def remove_item(self, index: int) -> BaseType:
        """
        Removes the item at the specified index.

        Args:
            index (int): The index of the item.

        Returns:
            BaseType: The removed item.
        """

        return self.get_value().pop(index)

    def contains(self, item: BaseType) -> bool:
        """
        Returns whether the SFSArray contains the specified item.

        Args:
            item (BaseType): The item to check.

        Returns:
            bool: Whether the SFSArray contains the specified item.
        """

        return item in self.get_value()

    def addNull(self, value=None, index=None):
        """
        Adds a null value to the SFSArray.

        Args:
            value (None, optional): The value to add. Defaults to None.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(Null("", value))
        else:
            self.insert_item(index, Null("", value))

        return self

    def addBool(self, value: bool, index=None):
        """
        Adds a bool value to the SFSArray.

        Args:
            value (bool): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(Bool("", value))
        else:
            self.insert_item(index, Bool("", value))

        return self

    def addByte(self, value: int, index=None):
        """
        Adds a byte value to the SFSArray.

        Args:
            value (int): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(Byte("", value))
        else:
            self.insert_item(index, Byte("", value))

        return self

    def addShort(self, value: int, index=None):
        """
        Adds a short value to the SFSArray.

        Args:
            value (int): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(Short("", value))
        else:
            self.insert_item(index, Short("", value))

        return self

    def addInt(self, value: int, index=None):
        """
        Adds an int value to the SFSArray.

        Args:
            value (int): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(Int("", value))
        else:
            self.insert_item(index, Int("", value))

        return self

    def addLong(self, value: int, index=None):
        """
        Adds a long value to the SFSArray.

        Args:
            value (int): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(Long("", value))
        else:
            self.insert_item(index, Long("", value))

        return self

    def addFloat(self, value: float, index=None):
        """
        Adds a float value to the SFSArray.

        Args:
            value (float): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(Float("", value))
        else:
            self.insert_item(index, Float("", value))

        return self

    def addDouble(self, value: float, index=None):
        """
        Adds a double value to the SFSArray.

        Args:
            value (float): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(Double("", value))
        else:
            self.insert_item(index, Double("", value))

        return self

    def addUtfString(self, value: str, index=None):
        """
        Adds a utf_string value to the SFSArray.

        Args:
            value (str): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(UtfString("", value))
        else:
            self.insert_item(index, UtfString("", value))

        return self

    def addBoolArray(self, value: list[bool], index=None):
        """
        Adds a bool_array value to the SFSArray.

        Args:
            value (list[bool]): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(BoolArray("", value))
        else:
            self.insert_item(index, BoolArray("", value))

        return self

    def addByteArray(self, value: bytes, index=None):
        """
        Adds a byte_array value to the SFSArray.

        Args:
            value (bytes): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(ByteArray("", value))
        else:
            self.insert_item(index, ByteArray("", value))

        return self

    def addShortArray(self, value: list[int], index=None):
        """
        Adds a short_array value to the SFSArray.

        Args:
            value (list[int]): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(ShortArray("", value))
        else:
            self.insert_item(index, ShortArray("", value))

        return self

    def addIntArray(self, value: list[int], index=None):
        """
        Adds an int_array value to the SFSArray.

        Args:
            value (list[int]): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(IntArray("", value))
        else:
            self.insert_item(index, IntArray("", value))

        return self

    def addLongArray(self, value: list[int], index=None):
        """
        Adds a long_array value to the SFSArray.

        Args:
            value (list[int]): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(LongArray("", value))
        else:
            self.insert_item(index, LongArray("", value))

        return self

    def addFloatArray(self, value: list[float], index=None):
        """
        Adds a float_array value to the SFSArray.

        Args:
            value (list[float]): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(FloatArray("", value))
        else:
            self.insert_item(index, FloatArray("", value))

        return self

    def addDoubleArray(self, value: list[float], index=None):
        """
        Adds a double_array value to the SFSArray.

        Args:
            value (list[float]): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(DoubleArray("", value))
        else:
            self.insert_item(index, DoubleArray("", value))

        return self

    def addUtfStringArray(self, value: list[str], index=None):
        """
        Adds a utf_string_array value to the SFSArray.

        Args:
            value (list[str]): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(UtfStringArray("", value))
        else:
            self.insert_item(index, UtfStringArray("", value))

        return self

    def addSFSArray(self, value: SFSArray, index=None):
        """
        Adds an sfs_array value to the SFSArray.

        Args:
            value (SFSArray): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(value)
        else:
            self.insert_item(index, value)

        return self

    def addSFSObject(self, value, index=None):
        """
        Adds an sfs_object value to the SFSArray.

        Args:
            value (SFSObject): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        if index is None:
            self.add_item(value)
        else:
            self.insert_item(index, value)

        return self

    def addAny(self, value, index=None):
        """
        Adds a value to the SFSArray.

        Args:
            value (any): The value to add.
            index (None, optional): The index to add the value at. Defaults to None.
        """

        from . import SFSObject

        if isinstance(value, bool):
            self.addBool(value, index)
        elif isinstance(value, int):
            self.addInt(value, index)
        elif isinstance(value, float):
            self.addDouble(value, index)
        elif isinstance(value, str):
            self.addUtfString(value, index)
        elif isinstance(value, list):
            self.addSFSArray(SFSArray.from_python_object(value), index)
        elif isinstance(value, dict):
            self.addSFSObject(SFSObject.from_python_object(value), index)

        return self

    def get(self, index: int):
        """
        Returns the item at the specified index.

        Args:
            index (int): The index of the item.

        Returns:
            BaseType: The item at the specified index.
        """

        item = self.get_item(index)
        if item.get_type() in ("sfs_object", "sfs_array"):
            return item
        return self.get_item(index).get_value()

    @staticmethod
    def from_python_object(value: list):
        """
        Creates an SFSArray from a python list.

        Args:
            value (list): The list to create the SFSArray from.

        Returns:
            SFSArray: The created SFSArray.
        """

        result = SFSArray()
        for i in value:
            result.addAny(i)
        return result

    def to_python_object(self, detailed=False):
        """
        Returns the SFSArray as a python list.

        Returns:
            list: The SFSArray as a python list.
        """

        result = []
        for i in self:
            if i.get_type() == "sfs_array":
                val = i.to_python_object(detailed)
            elif i.get_type() == "sfs_object":
                val = i.to_python_object(detailed)
            else:
                val = i.get_value()

            if detailed:
                result.append([i.get_type(), val])
            else:
                result.append(val)

        return result

    def to_json(self, indent=None, detailed=False):
        """
        Returns the SFSArray as a json string.

        Returns:
            str: The SFSArray as a json string.
        """

        if indent is None:
            return json.dumps(self.to_python_object(detailed), ensure_ascii=False)

        return json.dumps(self.to_python_object(detailed), indent=indent, ensure_ascii=False)

    @staticmethod
    def from_json(value: str):
        """
        Creates an SFSArray from a json string.

        Args:
            value (str): The json string to create the SFSArray from.

        Returns:
            SFSArray: The created SFSArray.
        """

        return SFSArray.from_python_object(json.loads(value))
