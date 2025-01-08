from __future__ import annotations

import io
import struct

from .BaseType import BaseType


class UtfStringArray(BaseType):
    """
    This class represents an array of utf_string values. It extends the BaseType class.

    Attributes:
        name (str): The name of the utf_string array.
        value (list[utf_string]): The list of strings.

    Methods:
        pack(): Returns a bytes representation of the utf_string array.
        unpack(buffer, name): Static method that returns a UtfStringArray instance from a bytes buffer.
    """

    def __init__(self, name: str, value: list[str]):
        """
        Constructs a new UtfStringArray instance.

        Args:
            name (str): The name of the utf_string array.
            value (list[utf_string]): The list of utf_string.
        """

        super().__init__("utf_string_array", name, value)

    def pack(self) -> bytes:
        """
        Packs the utf_string array into bytes.

        Returns:
            bytes: The bytes representation of the utf_string array.
        """
        result = len(self.get_value()).to_bytes(2, "big")
        for i in self.get_value():
            result += len(i).to_bytes(2, "big") + i.encode("utf-8")
        return self.pack_name() + bytes([16]) + result

    @staticmethod
    def unpack(buffer: io.BytesIO | bytes, name: str | None = None) -> UtfStringArray:
        """
        Unpacks a bytes buffer into a UtfStringArray instance.

        Args:
            buffer (io.BytesIO): The bytes buffer to unpack.
            name (str | None): The name of the utf_string array. Defaults to None.

        Returns:
            UtfStringArray: The UtfStringArray instance.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        if isinstance(name, bool) and name:
            name = BaseType.unpack_name(buffer)

        length = int.from_bytes(buffer.read(2), 'big')
        array = []
        for _ in range(length):
            string_length = int.from_bytes(buffer.read(2), 'big')
            array.append(buffer.read(string_length).decode("utf-8"))
        return UtfStringArray(name, array)
