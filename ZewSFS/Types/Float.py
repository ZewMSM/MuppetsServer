from __future__ import annotations

import io
import struct

from .BaseType import BaseType


class Float(BaseType):
    """
    Float is a class that represents a float value. It is a subclass of BaseType.

    Methods:
        __init__(self, name: str, value: int | bytes): Constructs a new Float object.
        pack(self) -> bytes: Returns the packed name of the object followed by a byte representing the float value.
        unpack(buffer: io.BytesIO, name: str | None = None) -> Byte: Unpacks a Float object from the given buffer.
    """

    def __init__(self, name: str, value: float):
        """
        Constructs a new Float object.

        Args:
            name (str): The name of the object.
            value (float): The float value of the object.
        """
        super().__init__("float", name, value)

    def pack(self) -> bytes:
        """
        Returns the packed name of the Float object followed by a byte representing the float value.

        Returns:
            bytes: The packed name of the object followed by a byte representing the float value.
        """
        return self.pack_name() + bytes([6]) + bytearray(struct.pack('f', self.get_value()))

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> Float:
        """
        Unpacks a Float object from the given buffer.

        Args:
            buffer (io.BytesIO): The buffer to unpack the Float object from.
            name (str | None): The name of the Float object.

        Returns:
            Float: The unpacked Float object.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        return Float(name, float(struct.unpack('f', buffer.read(4))[0]))
