from __future__ import annotations

import io
from .BaseType import BaseType


class Int(BaseType):
    """
    Int is a class that represents a int value. It is a subclass of BaseType.

    Methods:
        __init__(self, name: str, value: int | bytes): Constructs a new Int object.
        pack(self) -> bytes: Returns the packed name of the object followed by a byte representing the int value.
        unpack(buffer: io.BytesIO, name: str | None = None) -> Byte: Unpacks an Int object from the given buffer.
    """

    def __init__(self, name: str, value: int):
        """
        Constructs a new Int object.

        Args:
            name (str): The name of the object.
            value (int): The int value of the object.
        """
        super().__init__("int", name, value)

    def pack(self) -> bytes:
        """
        Returns the packed name of the Int object followed by a byte representing the int value.

        Returns:
            bytes: The packed name of the object followed by a byte representing the int value.
        """
        return self.pack_name() + bytes([4]) + self.get_value().to_bytes(4, "big", signed=True)

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> Int:
        """
        Unpacks an Int object from the given buffer.

        Args:
            buffer (io.BytesIO): The buffer to unpack the Int object from.
            name (str | None): The name of the Int object.

        Returns:
            Int: The unpacked Int object.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        return Int(name, int.from_bytes(buffer.read(4), 'big', signed=True))
