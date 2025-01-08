from __future__ import annotations

import io
import struct

from .BaseType import BaseType


class DoubleArray(BaseType):
    """
    This class represents an array of double values. It extends the BaseType class.

    Attributes:
        name (str): The name of the double array.
        value (list[float]): The list of floats.

    Methods:
        pack(): Returns a bytes representation of the double array.
        unpack(buffer, name): Static method that returns a DoubleArray instance from a bytes buffer.
    """

    def __init__(self, name: str, value: list[float]):
        """
        Constructs a new DoubleArray instance.

        Args:
            name (str): The name of the double array.
            value (list[float]): The list of double.
        """

        super().__init__("double_array", name, value)

    def pack(self) -> bytes:
        """
        Packs the double array into bytes.

        Returns:
            bytes: The bytes representation of the double array.
        """
        result = len(self.get_value()).to_bytes(2, "big")
        for i in self.get_value():
            result += int.from_bytes(struct.pack("d", i), "little", signed=True).to_bytes(8, "big", signed=True)
        return self.pack_name() + bytes([15]) + result

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> DoubleArray:
        """
        Unpacks a bytes buffer into a DoubleArray instance.

        Args:
            buffer (io.BytesIO): The bytes buffer to unpack.
            name (str | None): The name of the double array. Defaults to None.

        Returns:
            DoubleArray: The DoubleArray instance.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        length = int.from_bytes(buffer.read(2), 'big')
        array = []
        for _ in range(length):
            array.append(round(struct.unpack('d', buffer.read(8)[::-1])[0], 12))
        return DoubleArray(name, array)
