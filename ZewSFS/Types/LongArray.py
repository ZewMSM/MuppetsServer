from __future__ import annotations

import io
import struct

from .BaseType import BaseType


class LongArray(BaseType):
    """
    This class represents an array of long integer values. It extends the BaseType class.
;
    Attributes:
        name (str): The name of the long array.
        value (list[int]): The list of long integers.

    Methods:
        pack(): Returns a bytes representation of the long array.
        unpack(buffer, name): Static method that returns a LongArray instance from a bytes buffer.
    """

    def __init__(self, name: str, value: list[int]):
        """
        Constructs a new LongArray instance.

        Args:
            name (str): The name of the long array.
            value (list[int]): The list of long integers.
        """

        super().__init__("long_array", name, value)

    def pack(self) -> bytes:
        """
        Packs the long array into bytes.

        Returns:
            bytes: The bytes representation of the long array.
        """
        result = len(self.get_value()).to_bytes(2, "big")
        for i in self.get_value():
            result += i.to_bytes(8, "big", signed=True)
        return self.pack_name() + bytes([13]) + result

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> LongArray:
        """
        Unpacks a bytes buffer into a LongArray instance.

        Args:
            buffer (io.BytesIO): The bytes buffer to unpack.
            name (str | None): The name of the long array. Defaults to None.

        Returns:
            LongArray: The LongArray instance.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        length = int.from_bytes(buffer.read(2), 'big')
        array = []
        for _ in range(length):
            array.append(int.from_bytes(buffer.read(8), 'big', signed=True))
        return LongArray(name, array)
