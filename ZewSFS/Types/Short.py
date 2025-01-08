from __future__ import annotations

import io
from .BaseType import BaseType


class Short(BaseType):
    """
    Short is a class that represents a short value. It is a subclass of BaseType.

    Methods:
        __init__(self, name: str, value: int | bytes): Constructs a new Short object.
        pack(self) -> bytes: Returns the packed name of the object followed by a byte representing the short value.
        unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> Byte: Unpacks a Short object from the given buffer.
    """

    def __init__(self, name: str, value: int):
        """
        Constructs a new Short object.

        Args:
            name (str): The name of the object.
            value (int): The int value of the object.
        """
        super().__init__("short", name, value)

    def pack(self) -> bytes:
        """
        Returns the packed name of the Short object followed by a byte representing the short value.

        Returns:
            bytes: The packed name of the object followed by a byte representing the short value.
        """
        return self.pack_name() + bytes([3]) + self.get_value().to_bytes(2, "big", signed=True)

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> Short:
        """
        Unpacks a Short object from the given buffer.

        Args:
            buffer (io.BytesIO): The buffer to unpack the Short object from.
            name (str | None): The name of the Short object.

        Returns:
            Short: The unpacked Short object.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        return Short(name, int.from_bytes(buffer.read(2), 'big', signed=True))
