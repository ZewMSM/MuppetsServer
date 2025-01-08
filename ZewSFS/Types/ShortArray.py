from __future__ import annotations

import io
import struct

from .BaseType import BaseType


class ShortArray(BaseType):
    """
    This class represents an array of short integer values. It extends the BaseType class.

    Attributes:
        name (str): The name of the short array.
        value (list[int]): The list of short integers.

    Methods:
        pack(): Returns a bytes representation of the short array.
        unpack(buffer, name): Static method that returns a ShortArray instance from a bytes buffer.
    """

    def __init__(self, name: str, value: list[int]):
        """
        Constructs a new ShortArray instance.

        Args:
            name (str): The name of the short array.
            value (list[int]): The list of short integers.
        """

        super().__init__("short_array", name, value)

    def pack(self) -> bytes:
        """
        Packs the short array into bytes.

        Returns:
            bytes: The bytes representation of the short array.
        """
        result = len(self.get_value()).to_bytes(2, "big")
        for i in self.get_value():
            result += i.to_bytes(2, "big", signed=True)
        return self.pack_name() + bytes([11]) + result

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> ShortArray:
        """
        Unpacks a bytes buffer into a ShortArray instance.

        Args:
            buffer (io.BytesIO): The bytes buffer to unpack.
            name (str | None): The name of the short array. Defaults to None.

        Returns:
            ShortArray: The ShortArray instance.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        length = int.from_bytes(buffer.read(2), 'big')
        array = []
        for _ in range(length):
            array.append(int.from_bytes(buffer.read(2), 'big', signed=True))
        return ShortArray(name, array)
