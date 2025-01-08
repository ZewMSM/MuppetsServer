from __future__ import annotations

import io
import json

from . import SFSArray
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


class SFSObject(BaseType):
    """
    The SFSObject class represents a SmartFoxServer (SFS) object. It extends the BaseType class.

    Attributes:
        name (str): The name of the SFS object.
        value (dict): The dictionary of values in the SFS object.

    Methods:
        pack(): Returns a bytes representation of the SFS object.
        unpack(buffer, name): Static method that returns an SFSObject instance from a bytes buffer.
        set_item(key, value): Sets an item in the SFS object.
        get_item(key, default): Gets an item from the SFS object.
        remove_item(key): Removes an item from the SFS object.
        contains(key): Checks if the SFS object contains a key.
        putNull(key, value): Puts a Null value into the SFS object.
        putBool(key, value): Puts a Bool value into the SFS object.
        putByte(key, value): Puts a Byte value into the SFS object.
        putShort(key, value): Puts a Short value into the SFS object.
        putInt(key, value): Puts an Int value into the SFS object.
        putLong(key, value): Puts a Long value into the SFS object.
        putFloat(key, value): Puts a Float value into the SFS object.
        putDouble(key, value): Puts a Double value into the SFS object.
        putUtfString(key, value): Puts a UtfString value into the SFS object.
        putBoolArray(key, value): Puts a BoolArray value into the SFS object.
        putByteArray(key, value): Puts a ByteArray value into the SFS object.
        putShortArray(key, value): Puts a ShortArray value into the SFS object.
        putIntArray(key, value): Puts an IntArray value into the SFS object.
        putLongArray(key, value): Puts a LongArray value into the SFS object.
        putFloatArray(key, value): Puts a FloatArray value into the SFS object.
        putDoubleArray(key, value): Puts a DoubleArray value into the SFS object.
        putUtfStringArray(key, value): Puts a UtfStringArray value into the SFS object.
        putSFSArray(key, value): Puts an SFSArray value into the SFS object.
        putSFSObject(key, value): Puts an SFSObject value into the SFS object.
        putAny(key, value): Puts any value into the SFS object.
        get(key, default): Gets a value from the SFS object.
        from_python_object(python_object): Static method that returns an SFSObject instance from a Python object.
        to_python_object(): Returns a Python object from the SFS object.
        from_json(json_string): Static method that returns an SFSObject instance from a JSON string.
        to_json(): Returns a JSON string from the SFS object.
    """

    __type = "sfs_object"

    def __init__(self, name: str = None, value: dict = None):
        """
        Constructs a new SFSObject instance.

        Args:
            name (str, optional): The name of the SFS object. Defaults to None.
            value (dict, optional): The dictionary of values in the SFS object. Defaults to None.
        """

        if name is None:
            name = ""
        if value is None:
            value = {}
        super().__init__("sfs_object", name, value)

    def __str__(self) -> str:
        """
        Returns a string representation of the SFS object.

        Returns:
            str: A string representation of the SFS object.
        """

        from . import stringify_object
        return f"(sfs_object){' ' + self.get_name() if len(self.get_name()) > 0 else ''}: \n" + stringify_object(1, self, "")

    def __contains__(self, item: str) -> bool:
        """
        Checks if the SFS object contains a key.

        Args:
            item (str): The key to check.

        Returns:
            bool: True if the key is in the SFS object, False otherwise.
        """

        return item in self.get_value().keys()

    def __getitem__(self, item):
        """
        Gets an item from the SFS object.

        Args:
            item (str): The key of the item to get.

        Returns:
            BaseType: The item associated with the key.
        """

        return self.get_item(item)

    def __setitem__(self, key, value) -> SFSObject:
        """
        Gets an item from the SFS object.

        Args:
            item (str): The key of the item to get.

        Returns:
            BaseType: The item associated with the key.
        """

        if isinstance(value, BaseType):
            return self.set_item(key, value)
        return self.putAny(key, value)

    def __delitem__(self, key) -> SFSObject:
        """
        Removes an item from the SFS object.

        Args:
            key (str): The key of the item to remove.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.remove_item(key)

    def __iter__(self):
        """
        Returns an iterator over the values in the SFS object.

        Returns:
            Iterator[BaseType]: An iterator over the values in the SFS object.
        """

        return iter(self.get_value().values())

    def __len__(self) -> int:
        """
        Returns the number of items in the SFS object.

        Returns:
            int: The number of items in the SFS object.
        """

        return len(self.get_value())

    def __add__(self, other) -> SFSObject:
        """
        Adds another SFS object or a dictionary to this SFS object.

        Args:
            other (SFSObject | dict): The other SFS object or dictionary to add.

        Returns:
            SFSObject: A new SFS object that is the result of the addition.
        """

        if isinstance(other, SFSObject):
            return SFSObject(value={**self.get_value(), **other.get_value()})
        elif isinstance(other, dict):
            return SFSObject(value={**self.get_value(), **other})
        else:
            return NotImplemented

    def pack(self) -> bytes:
        """
        Packs the SFS object into bytes.

        Returns:
            bytes: The bytes representation of the SFS object.
        """

        packed = self.pack_name() + bytes([18])
        packed += len(self.get_value().keys()).to_bytes(2, "big")
        for item_name, item_value in self.get_value().items():
            item_value.set_name(item_name)
            packed += item_value.pack()
        return packed

    def tokenize(self) -> dict:
        """
        Packs the SFS object into bytes.

        Returns:
            bytes: The bytes representation of the SFS object.
        """

        tokenized = {}
        for item_name, item_value in self.get_value().items():
            item_type = item_value.get_type()
            if item_type in ("sfs_object", "sfs_array"):
                tokenized[item_name] = item_value.tokenize()
            else:
                tokenized[item_name] = item_type

        return {key: tokenized[key] for key in sorted(tokenized)}


    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None, skip_type: bool = False) -> SFSObject:
        """
        Unpacks a bytes buffer into an SFSObject instance.

        Args:
            buffer (io.BytesIO | bytes): The bytes buffer to unpack.
            name (str | None, optional): The name of the SFS object. Defaults to None.
            skip_type (bool): # TODO: Add description for it

        Returns:
            SFSObject: The unpacked SFSObject instance.
        """

        from . import sfs2x_datatypes
        from .SFSArray import SFSArray

        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)
        if (isinstance(name, bool) and name) or skip_type:
            buffer.read(1)

        result = SFSObject(name)
        length = int.from_bytes(buffer.read(2), "big")
        for _ in range(length):
            key = BaseType.unpack_name(buffer)
            value = None
            type_id = int.from_bytes(buffer.read(1), "big")
            if type_id > 18:
                raise InvalidDataType(type_id)
            if type_id == 18:
                value = SFSObject.unpack(buffer, False)
            elif type_id == 17:
                value = SFSArray.unpack(buffer, False)
                pass
            else:
                value = list(sfs2x_datatypes.values())[type_id].unpack(buffer, False)
            value.set_name(key)
            result.set_item(key, value)

        return result

    def set_item(self, key: str, value: BaseType) -> SFSObject:
        """
        Sets an item in the SFS object.

        Args:
            key (str): The key of the item to set.
            value (BaseType): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        self.get_value()[key] = value
        return self

    def get_item(self, key: str, default: BaseType = Null) -> BaseType:
        """
        Gets an item from the SFS object.

        Args:
            key (str): The key of the item to get.
            default (BaseType, optional): The default value to return if the key is not in the SFS object. Defaults to Null.

        Returns:
            BaseType: The item associated with the key, or the default value if the key is not in the SFS object.
        """

        if key not in self.get_value():
            return default
        return self.get_value()[key]

    def remove_item(self, key: str) -> SFSObject:
        """
        Removes an item from the SFS object.

        Args:
            key (str): The key of the item to remove.

        Returns:
            SFSObject: The SFS object itself.
        """

        if key in self.get_value():
            del self.get_value()[key]
        return self

    def contains(self, key: str) -> bool:
        """
        Checks if the SFS object contains a key.

        Args:
            item (str): The key to check.

        Returns:
            bool: True if the key is in the SFS object, False otherwise.
        """
        return key in self.get_value()

    def putNull(self, key: str, value: None = None) -> SFSObject:
        """
        Puts a Null value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (None, optional): The value to set. Defaults to None.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, Null(key, None))

    def putBool(self, key: str, value: bool) -> SFSObject:
        """
        Puts a Bool value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (bool): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, Bool(key, value))

    def putByte(self, key: str, value: int | bytes) -> SFSObject:
        """
        Puts a Byte value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (int | bytes): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, Byte(key, value))

    def putShort(self, key: str, value: int) -> SFSObject:
        """
        Puts a Short value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (int): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, Short(key, value))

    def putInt(self, key: str, value: int) -> SFSObject:
        """
        Puts an Int value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (int): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, Int(key, value))

    def putLong(self, key: str, value: int) -> SFSObject:
        """
        Puts a Long value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (int): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, Long(key, value))

    def putFloat(self, key: str, value: float) -> SFSObject:
        """
        Puts a Float value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (float): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, Float(key, value))

    def putDouble(self, key: str, value: float) -> SFSObject:
        """
        Puts a Double value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (float): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, Double(key, value))

    def putUtfString(self, key: str, value: str) -> SFSObject:
        """
        Puts a UtfString value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (str): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, UtfString(key, value))

    def putBoolArray(self, key: str, value: list[bool]) -> SFSObject:
        """
        Puts a BoolArray value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (list[bool]): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, BoolArray(key, value))

    def putByteArray(self, key: str, value: list[int] | bytearray) -> SFSObject:
        """
        Puts a ByteArray value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (list[int] | bytearray): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, ByteArray(key, value))

    def putShortArray(self, key: str, value: list[int]) -> SFSObject:
        """
        Puts a ShortArray value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (list[int]): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, ShortArray(key, value))

    def putIntArray(self, key: str, value: list[int]) -> SFSObject:
        """
        Puts an IntArray value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (list[int]): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, IntArray(key, value))

    def putLongArray(self, key: str, value: list[int]) -> SFSObject:
        """
        Puts a LongArray value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (list[int]): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, LongArray(key, value))

    def putFloatArray(self, key: str, value: list[float]) -> SFSObject:
        """
        Puts a FloatArray value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (list[float]): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, FloatArray(key, value))

    def putDoubleArray(self, key: str, value: list[float]) -> SFSObject:
        """
        Puts a DoubleArray value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (list[float]): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, DoubleArray(key, value))

    def putUtfStringArray(self, key: str, value: list[str]) -> SFSObject:
        """
        Puts a UtfStringArray value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (list[str]): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, UtfStringArray(key, value))

    def putSFSArray(self, key: str, value) -> SFSObject:
        """
        Puts an SFSArray value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (SFSArray): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, value)

    def putSFSObject(self, key: str, value: SFSObject) -> SFSObject:
        """
        Puts an SFSObject value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value (SFSObject): The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """

        return self.set_item(key, value)

    def putAny(self, key: str, value) -> SFSObject:
        """
        Puts any value into the SFS object.

        Args:
            key (str): The key of the item to set.
            value: The value to set.

        Returns:
            SFSObject: The SFS object itself.
        """


        if value is None:
            self.putNull(key)
        elif type(value) is int:

            if value > 2147483647:
                self.putLong(key, value)
            else:
                self.putInt(key, value)
        elif type(value) is float:
            self.putDouble(key, value)
        elif type(value) is dict:
            self.putSFSObject(key, SFSObject.from_python_object(value))
        elif type(value) is list:
            if len(value) > 0:
                if type(value[0]) is dict:
                    self.putSFSArray(key, SFSArray.from_python_object(value))
                elif type(value[0]) is float:
                    self.putDoubleArray(key, value)
                elif type(value[0]) is bool:
                    self.putBoolArray(key, value)
                elif type(value[0]) is str:
                    self.putUtfStringArray(key, value)
                elif type(value[0]) is int:
                    if any(x > 2147483647 for x in value):
                        self.putLongArray(key, value)
                    else:
                        self.putIntArray(key, value)
        elif type(value) is str:
            self.putUtfString(key, value)
        elif type(value) is bool:
            self.putBool(key, value)
        elif type(value) is bytearray:
            self.putByteArray(key, value)

        return self

    def get(self, key: str, default=None) -> BaseType | SFSObject:
        """
        Retrieves the value associated with the given key from the SFS object.

        Args:
            key (str): The key of the item to get.
            default (optional): The default value to return if the key is not in the SFS object. Defaults to None.

        Returns:
            BaseType: The value associated with the key, or the default value if the key is not in the SFS object.
        """

        if key not in self:
            return default
        item = self.get_item(key)
        if item.get_type() in ("sfs_object", "sfs_array"):
            return item
        return self.get_item(key).get_value()

    @staticmethod
    def from_python_object(python_object: dict) -> SFSObject:
        """
        Creates an SFSObject from a Python dictionary.

        Args:
            python_object (dict): The Python dictionary to convert.

        Returns:
            SFSObject: The created SFSObject.
        """

        sfsObject = SFSObject()
        for key, value in python_object.items():
            sfsObject.putAny(key, value)

        return sfsObject

    def to_python_object(self, detailed=False) -> dict:
        """
        Converts the SFSObject to a Python dictionary.

        Returns:
            dict: The converted Python dictionary.
        """

        python_object = {}
        for key, value in self.get_value().items():
            if value.get_type() == "sfs_object":
                val = value.to_python_object(detailed)
            elif value.get_type() == "sfs_array":
                val = value.to_python_object(detailed)
            else:
                val = value.get_value()

            if detailed:
                python_object[key] = [value.get_type(), val]
            else:
                python_object[key] = val
        return python_object

    @staticmethod
    def from_json(json_string: str) -> SFSObject:
        """
        Creates an SFSObject from a JSON string.

        Args:
            json_string (str): The JSON string to convert.

        Returns:
            SFSObject: The created SFSObject.
        """

        return SFSObject.from_python_object(json.loads(json_string))

    def to_json(self, indent=None, detailed=False) -> str:
        """
        Converts the SFSObject to a JSON string.

        Args:
            indent (int, optional): The indentation level. Defaults to None.

        Returns:
            str: The converted JSON string.
            :param detailed:
        """

        if indent is not None:
            return json.dumps(self.to_python_object(detailed), ensure_ascii=False, indent=indent)

        return json.dumps(self.to_python_object(detailed), ensure_ascii=False)
