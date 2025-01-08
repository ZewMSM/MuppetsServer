from __future__ import annotations

import io
from .BaseType import BaseType


class Bool(BaseType):
    """
    Bool is a class that represents a boolean value. It is a subclass of BaseType.

    Methods:
        __init__(self, name: str, value: bool): Constructs a new Bool object.
        pack(self) -> bytes: Returns the packed name of the object followed by a byte representing the boolean value.
        unpack(buffer: io.BytesIO, name: str | None = None) -> Bool: Unpacks a Bool object from the given buffer.
    """

    def __init__(self, name: str, value: bool):
        """
        Constructs a new Bool object.

        Args:
            name (str): The name of the object.
            value (bool): The boolean value of the object.
        """
        super().__init__("bool", name, value)

    def pack(self) -> bytes:
        """
        Returns the packed name of the Bool object followed by a byte representing the boolean value.

        Returns:
            bytes: The packed name of the object followed by a byte representing the boolean value.
        """
        return self.pack_name() + bytes([1]) + self.get_value().to_bytes(1, "big")

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None | bool = None) -> Bool:
        """
        Unpacks a Bool object from the given buffer.

        Args:
            buffer (io.BytesIO): The buffer to unpack the Bool object from.
            name (str | None): The name of the Bool object.

        Returns:
            Bool: The unpacked Bool object.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)
        return Bool(name, bool.from_bytes(buffer.read(1), 'big'))
