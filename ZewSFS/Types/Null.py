from __future__ import annotations

import io
from .BaseType import BaseType


class Null(BaseType):
    """
    Null is a class that represents a null value. It is a subclass of BaseType.

    Methods:
        __init__(self, name: str, value: None): Constructs a new Null object.
        pack(self) -> bytes: Returns the packed name of the object followed by a null byte.
        unpack(buffer: io.BytesIO, name: str | None = None) -> Null: Unpacks a Null object from the given buffer.
    """

    def __init__(self, name: str, value: None):
        """
        Constructs a new Null object.

        Args:
            name (str): The name of the object.
            value (None): The value of the object, which is always None for Null objects.
        """
        super().__init__("null", name, None)

    def pack(self) -> bytes:
        """
        Returns the packed name of the Null object followed by a null byte.

        Returns:
            bytes: The packed name of the object followed by a null byte.
        """
        return super().pack_name() + bytes([0])

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> Null:
        """
        Unpacks a Null object from the given buffer.

        Args:
            buffer (io.BytesIO): The buffer to unpack the Null object from.
            name (str | None): The name of the Null object.

        Returns:
            Null: The unpacked Null object.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        return Null(name, buffer.read(1))
