class InvalidDataType(Exception):
    """
    Exception raised when an unsupported datatype is encountered.

    Attributes:
        id: str
            The id of the unsupported datatype.
    """
    def __init__(self, id):
        super().__init__(f"Datatype with id: {id} is not supported")


class CompilePacketException(Exception):
    """
    Exception raised when there is an error in compiling a packet.

    Attributes:
        error: str
            The error message.
    """
    def __init__(self, error):
        super().__init__(error)


class SendPacketException(Exception):
    """
    Exception raised when there is an error in sending a packet.

    Attributes:
        error: str
            The error message.
    """
    def __init__(self, error):
        super().__init__(error)