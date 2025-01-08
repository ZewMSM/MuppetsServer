from __future__ import annotations

import io
from .BaseType import BaseType


class Long(BaseType):
    """
    Long is a class that represents a long value. It is a subclass of BaseType.

    Methods:
        __init__(self, name: str, value: int | bytes): Constructs a new Long object.
        pack(self) -> bytes: Returns the packed name of the object followed by a byte representing the long value.
        unpack(buffer: io.BytesIO, name: str | None = None) -> Byte: Unpacks a Long object from the given buffer.
    """

    def __init__(self, name: str, value: int):
        """
        Constructs a new Long object.

        Args:
            name (str): The name of the object.
            value (int): The int value of the object.
        """
        super().__init__("long", name, value)

    def pack(self) -> bytes:
        """
        Returns the packed name of the Long object followed by a byte representing the long value.

        Returns:
            bytes: The packed name of the object followed by a byte representing the long value.
        """
        return self.pack_name() + bytes([5]) + self.get_value().to_bytes(8, "big", signed=True)

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> Long:
        """
        Unpacks a Long object from the given buffer.

        Args:
            buffer (io.BytesIO): The buffer to unpack the Long object from.
            name (str | None): The name of the Long object.

        Returns:
            Long: The unpacked Long object.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        return Long(name, int.from_bytes(buffer.read(8), 'big', signed=True))
