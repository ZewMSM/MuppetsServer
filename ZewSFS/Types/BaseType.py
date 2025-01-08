import io
import typing

OBJType = typing.TypeVar('OBJType')


class BaseType:
    """
    BaseType is a class that represents a base type.

    Attributes:
        __type (str): The type of the object.
        __name (str): The name of the object.
        __value (OBJType): The value of the object.

    Methods:
        __str__(self) -> str: Returns a string representation of the object.
        get_name(self) -> str: Returns the name of the object.
        set_name(self, new_name: str): Sets the name of the object.
        get_type(self) -> str: Returns the type of the object.
        set_type(self, new_type: OBJType): Sets the type of the object.
        get_value(self) -> OBJType: Returns the value of the object.
        set_value(self, new_value: OBJType): Sets the value of the object.
        pack_name(self) -> bytes: Returns the packed name of the object.
        unpack_name(buffer: io.BytesIO) -> str: Unpacks the name from the buffer.
    """

    __type: str = "undefined"
    __name: str
    __value: OBJType

    def __init__(self, object_type: str, name: str, value: OBJType):
        """
        Constructs a new BaseType object.

        Args:
            object_type (str): The type of the object.
            name (str): The name of the object.
            value (OBJType): The value of the object.
        """

        self.__type = object_type
        self.__name = name if name is not None else ""
        self.__value = value

    def __str__(self) -> str:
        """
        Returns a string representation of the BaseType object.

        Returns:
            str: A string in the format "(type) name: value".
        """
        return f"({self.__type}){' ' + self.__name if len(self.__name) != 0 else ''}: {self.__value}"

    def get_name(self) -> str:
        """
        Returns the name of the BaseType object.

        Returns:
            str: The name of the object.
        """
        if isinstance(self.__name, str):
            return self.__name
        return ''

    def set_name(self, new_name: str):
        """
        Sets the name of the BaseType object.

        Args:
            new_name (str): The new name for the object.
        """
        self.__name = new_name

    def get_type(self) -> str:
        """
        Returns the type of the BaseType object.

        Returns:
            str: The type of the object.
        """
        return self.__type

    def set_type(self, new_type: OBJType):
        """
        Sets the type of the BaseType object.

        Args:
            new_type (OBJType): The new type for the object.
        """
        self.__type = new_type

    def get_value(self) -> OBJType:
        """
        Returns the value of the BaseType object.

        Returns:
            OBJType: The value of the object.
        """
        return self.__value

    def set_value(self, new_value: OBJType):
        """
        Sets the value of the BaseType object.

        Args:
            new_value (OBJType): The new value for the object.
        """
        self.__value = new_value

    def pack_name(self) -> bytes:
        """
        Returns the packed name of the BaseType object.

        Returns:
            bytes: The packed name of the object, or an empty byte string if the name is empty.
        """
        if isinstance(self.__name, str) and len(self.__name) != 0:
            name_length = len(self.__name)
            encoded_name = self.__name.encode('utf-8')
            return name_length.to_bytes(2, 'big') + encoded_name
        else:
            return b''

    @staticmethod
    def unpack_name(buffer: io.BytesIO | bytes) -> str:
        """
        Unpacks the name from the given buffer.

        Args:
            buffer (io.BytesIO): The buffer to unpack the name from.

        Returns:
            str: The unpacked name.
        """
        if isinstance(buffer, bytes):
            buffer = io.BytesIO(buffer)
        name_length = int.from_bytes(buffer.read(2), 'big')
        name = buffer.read(name_length)
        # buffer.read(1)
        return name.decode('utf8')
