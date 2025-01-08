from __future__ import annotations

import io
import struct

from .BaseType import BaseType


class ByteArray(BaseType):
    """
    This class represents an array of byte values. It extends the BaseType class.

    Attributes:
        name (str): The name of the bytearray.
        value (bytearray): The bytearray.

    Methods:
        pack(): Returns a bytes representation of the bytearray.
        unpack(buffer, name): Static method that returns a ByteArray instance from a bytes buffer.
    """

    def __init__(self, name: str, value: list[int] | bytearray):
        """
        Constructs a new ByteArray instance.

        Args:
            name (str): The name of the bytearray.
            value (list[int] | bytearray): The bytearray or list of integers.
        """
        if isinstance(value, bytearray):
            value = list(value)
        super().__init__("byte_array", name, value)

    def pack(self) -> bytes:
        """
        Packs the bytearray into bytes.

        Returns:
            bytes: The bytes representation of the bytearray.
        """
        result = len(self.get_value()).to_bytes(4, "big")
        for i in self.get_value():
            result += i.to_bytes(1, "big", signed=True)
        return self.pack_name() + bytes([10]) + result

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> ByteArray:
        """
        Unpacks a bytes buffer into a ByteArray instance.

        Args:
            buffer (io.BytesIO): The bytes buffer to unpack.
            name (str | None): The name of the bytearray. Defaults to None.

        Returns:
            ByteArray: The ByteArray instance.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        length = int.from_bytes(buffer.read(4), 'big')
        array = []
        for _ in range(length):
            array.append(int.from_bytes(buffer.read(1), 'big', signed=True))
        return ByteArray(name, array)
