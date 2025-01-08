from __future__ import annotations

import io
import struct

from .BaseType import BaseType


class FloatArray(BaseType):
    """
    This class represents an array of float values. It extends the BaseType class.

    Attributes:
        name (str): The name of the float array.
        value (list[float]): The list of float.

    Methods:
        pack(): Returns a bytes representation of the float array.
        unpack(buffer, name): Static method that returns a FloatArray instance from a bytes buffer.
    """

    def __init__(self, name: str, value: list[float]):
        """
        Constructs a new FloatArray instance.

        Args:
            name (str): The name of the float array.
            value (list[float]): The list of float.
        """

        super().__init__("float_array", name, value)

    def pack(self) -> bytes:
        """
        Packs the float array into bytes.

        Returns:
            bytes: The bytes representation of the float array.
        """
        result = len(self.get_value()).to_bytes(2, "big")
        for i in self.get_value():
            result += int.from_bytes(struct.pack("f", i), "little", signed=True).to_bytes(4, "big", signed=True)
        return self.pack_name() + bytes([14]) + result

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> FloatArray:
        """
        Unpacks a bytes buffer into a FloatArray instance.

        Args:
            buffer (io.BytesIO): The bytes buffer to unpack.
            name (str | None): The name of the float array. Defaults to None.

        Returns:
            FloatArray: The FloatArray instance.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        length = int.from_bytes(buffer.read(2), 'big')
        array = []
        for _ in range(length):
            array.append(round(struct.unpack('f', buffer.read(4)[::-1])[0], 6))
        return FloatArray(name, array)
