from __future__ import annotations

import io
import struct

from .BaseType import BaseType


class UtfString(BaseType):
    """
    UtfString is a class that represents a utf_string value. It is a subclass of BaseType.

    Methods:
        __init__(self, name: str, value: int | bytes): Constructs a new UtfString object.
        pack(self) -> bytes: Returns the packed name of the object followed by a byte representing the utf_string value.
        unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> Byte: Unpacks a UtfString object from the given buffer.
    """

    def __init__(self, name: str, value: str):
        """
        Constructs a new UtfString object.

        Args:
            name (str): The name of the object.
            value (str): The int value of the object.
        """
        super().__init__("utf_string", name, value)

    def pack(self) -> bytes:
        """
        Returns the packed name of the UtfString object followed by a byte representing the utf_string value.

        Returns:
            bytes: The packed name of the object followed by a byte representing the utf_string value.
        """
        length = len(self.get_value()).to_bytes(2, "big")
        return self.pack_name() + bytes([8]) + length + self.get_value().encode('utf8')

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> UtfString:
        """
        Unpacks a UtfString object from the given buffer.

        Args:
            buffer (io.BytesIO): The buffer to unpack the UtfString object from.
            name (str | None): The name of the UtfString object.

        Returns:
            UtfString: The unpacked UtfString object.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        length = int.from_bytes(buffer.read(2), 'big')
        return UtfString(name, buffer.read(length).decode('utf8'))
