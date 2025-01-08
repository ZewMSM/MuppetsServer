from __future__ import annotations

import io
import struct

from .BaseType import BaseType


class Double(BaseType):
    """
    Double is a class that represents a double value. It is a subclass of BaseType.

    Methods:
        __init__(self, name: str, value: int | bytes): Constructs a new Double object.
        pack(self) -> bytes: Returns the packed name of the object followed by a byte representing the double value.
        unpack(buffer: io.BytesIO, name: str | None = None) -> Byte: Unpacks a Double object from the given buffer.
    """

    def __init__(self, name: str, value: float):
        """
        Constructs a new Double object.

        Args:
            name (str): The name of the object.
            value (float): The float value of the object.
        """
        super().__init__("double", name, value)

    def pack(self) -> bytes:
        """
        Returns the packed name of the Double object followed by a byte representing the double value.

        Returns:
            bytes: The packed name of the object followed by a byte representing the double value.
        """
        return self.pack_name() + bytes([7]) + bytearray(struct.pack('d', self.get_value()))[::-1]

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> Double:
        """
        Unpacks a Double object from the given buffer.

        Args:
            buffer (io.BytesIO): The buffer to unpack the Double object from.
            name (str | None): The name of the Double object.

        Returns:
            Double: The unpacked Double object.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        return Double(name, float(struct.unpack('d', buffer.read(8)[::-1])[0]))
