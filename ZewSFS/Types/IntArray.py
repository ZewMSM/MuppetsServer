from __future__ import annotations

import io
import struct

from .BaseType import BaseType


class IntArray(BaseType):
    """
    This class represents an array of integer values. It extends the BaseType class.

    Attributes:
        name (str): The name of the int array.
        value (list[int]): The list of integers.

    Methods:
        pack(): Returns a bytes representation of the int array.
        unpack(buffer, name): Static method that returns a IntArray instance from a bytes buffer.
    """

    def __init__(self, name: str, value: list[int]):
        """
        Constructs a new IntArray instance.

        Args:
            name (str): The name of the int array.
            value (list[int]): The list of int integers.
        """

        super().__init__("int_array", name, value)

    def pack(self) -> bytes:
        """
        Packs the int array into bytes.

        Returns:
            bytes: The bytes representation of the int array.
        """
        result = len(self.get_value()).to_bytes(2, "big")
        for i in self.get_value():
            result += i.to_bytes(4, "big", signed=True)
        return self.pack_name() + bytes([12]) + result

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> IntArray:
        """
        Unpacks a bytes buffer into a IntArray instance.

        Args:
            buffer (io.BytesIO): The bytes buffer to unpack.
            name (str | None): The name of the int array. Defaults to None.

        Returns:
            IntArray: The IntArray instance.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        length = int.from_bytes(buffer.read(2), 'big')
        array = []
        for _ in range(length):
            array.append(int.from_bytes(buffer.read(4), 'big', signed=True))
        return IntArray(name, array)
