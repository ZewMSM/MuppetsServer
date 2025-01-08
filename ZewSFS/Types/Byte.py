from __future__ import annotations

import io
from .BaseType import BaseType


class Byte(BaseType):
    """
    Byte is a class that represents a byte value. It is a subclass of BaseType.

    Methods:
        __init__(self, name: str, value: int | bytes): Constructs a new Byte object.
        pack(self) -> bytes: Returns the packed name of the object followed by a byte representing the byte value.
        unpack(buffer: io.BytesIO, name: str | None = None) -> Byte: Unpacks a Byte object from the given buffer.
    """

    def __init__(self, name: str, value: int | bytes):
        """
        Constructs a new Byte object.

        Args:
            name (str): The name of the object.
            value (int | bytes): The byte value of the object. If an integer is provided, it is converted to a byte.
        """
        if isinstance(value, int):
            value = value.to_bytes(1, "big", signed=True)
        super().__init__("byte", name, value)

    def pack(self) -> bytes:
        """
        Returns the packed name of the Byte object followed by a byte representing the byte value.

        Returns:
            bytes: The packed name of the object followed by a byte representing the byte value.
        """
        return self.pack_name() + bytes([2]) + self.get_value()

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> Byte:
        """
        Unpacks a Byte object from the given buffer.

        Args:
            buffer (io.BytesIO): The buffer to unpack the Byte object from.
            name (str | None): The name of the Byte object.

        Returns:
            Byte: The unpacked Byte object.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)
        return Byte(name, buffer.read(1))
