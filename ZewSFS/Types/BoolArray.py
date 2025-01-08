from __future__ import annotations

import io
import struct

from .BaseType import BaseType


class BoolArray(BaseType):
    """
    This class represents an array of boolean values. It extends the BaseType class.

    Attributes:
        name (str): The name of the boolean array.
        value (list[bool]): The list of boolean values.

    Methods:
        pack(): Returns a bytes representation of the boolean array.
        unpack(buffer, name): Static method that returns a BoolArray instance from a bytes buffer.
    """

    def __init__(self, name: str, value: list[bool]):
        """
        Constructs a new BoolArray instance.

        Args:
            name (str): The name of the boolean array.
            value (list[bool]): The list of boolean values.
        """
        super().__init__("bool_array", name, value)

    def pack(self) -> bytes:
        """
        Packs the boolean array into bytes.

        Returns:
            bytes: The bytes representation of the boolean array.
        """
        result = len(self.get_value()).to_bytes(2, "big")
        for i in self.get_value():
            result += bytes([i])
        return self.pack_name() + bytes([9]) + result

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> BoolArray:
        """
        Unpacks a bytes buffer into a BoolArray instance.

        Args:
            buffer (io.BytesIO): The bytes buffer to unpack.
            name (str | None): The name of the boolean array. Defaults to None.

        Returns:
            BoolArray: The BoolArray instance.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        length = int.from_bytes(buffer.read(2), 'big')
        array = []
        for _ in range(length):
            array.append(bool.from_bytes(buffer.read(1), "big"))
        return BoolArray(name, array)