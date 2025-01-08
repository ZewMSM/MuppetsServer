import asyncio
import io
import logging
from asyncio import StreamReader, StreamWriter

from ZewSFS.Types import SFSObject
from ZewSFS.Utils import compile_packet
from database.player import Player

logger = logging.getLogger('ZewSFS/SFSServer')


class SFSServerClient:
    """
    Represents a client connected to the `SFSServer`.

    Attributes:
        identifier (str): The identifier for the client.
        address (str): The address of the client.
        reader (StreamReader): Stream reader for client communication.
        writer (StreamWriter): Stream writer for client communication.
        server (SFSServer): The server instance to which this client is connected.
        state (str): The current state of the client (e.g., 'handshake', 'login', 'play').
        args (dict): Arguments associated with the client, such as username and password.
    """

    def __init__(self, identifier: str, address: str, reader: 'StreamReader', writer: 'StreamWriter', server):
        self.identifier = identifier
        self.reader = reader
        self.writer = writer
        self.address = address
        self.server = server
        self.state = 'handshake'
        self.args = {}
        self.player: 'Player' = None

        self.server.add_client(self)
        asyncio.create_task(self.on_created())

    async def read_request(self):
        """
        Reads a request from the client.

        Returns:
            SFSObject: The request object.
        Raises:
            ConnectionError: If the client disconnects unexpectedly.
        """
        packet_type = await self.reader.read(1)
        packet_size = b''

        if not packet_type:
            raise ConnectionError

        if packet_type == b'\x88':
            packet_size_len = 4
        elif packet_type == b'\x80':
            packet_size_len = 2
        else:
            return

        while packet_size_len > 0:
            new = await self.reader.read(packet_size_len)
            packet_size += new
            packet_size_len -= len(new)

        packet_size = int.from_bytes(packet_size, "big")

        request = io.BytesIO()

        rlen = 0
        while rlen < packet_size:
            chunk_size = min(packet_size - rlen, 4096 * 4)
            request.write(await self.reader.read(chunk_size))
            rlen = len(request.getbuffer())

        request.seek(0)
        request = SFSObject.unpack(request, skip_type=True)
        return request

    async def send(self, data: bytes):
        """
        Sends data to the client.

        Args:
            data (bytes): The data to be sent.
        """
        try:
            self.writer.write(data)
            await self.writer.drain()
        except ConnectionError:
            logger.error('Client closed connection, can\'t send!')
            self.server.remove_client(self)
            return

    async def send_handshake(self):
        """
        Sends a handshake response to the client.
        """
        params = SFSObject()
        params.putInt('ct', 1000000)
        params.putInt('ms', 8000000)
        params.putUtfString('tk', '5c4ac8dbfb323e39053dcb3ee261bc93')

        resp = SFSObject()
        resp.putByte('c', 0)
        resp.putShort('a', 0)
        resp.putSFSObject('p', params)

        asyncio.create_task(self.send(compile_packet(resp)))

    async def send_and_wait(self, cmd, params):
        """
        Sends a request to the client and waits for a response.

        Args:
            cmd (str): The command to be sent.
            params (SFSObject): The parameters for the command.
        """
        request = SFSObject()
        request.putUtfString("c", cmd)
        request.putInt("r", -1)
        request.putSFSObject("p", params)

        packet = SFSObject()
        packet.putByte("c", 1)
        packet.putShort("a", 13)
        packet.putSFSObject("p", request)

        pkg = compile_packet(packet)
        await self.send(pkg)

    async def send_extension(self, cmd, params, cache: bool = False):
        """
        Sends an extension request to the client.

        Args:
            cmd (str): The command to be sent.
            params (SFSObject): The parameters for the command.
        """
        request = SFSObject()
        request.putUtfString("c", cmd)
        request.putInt("r", -1)
        request.putSFSObject("p", params)

        packet = SFSObject()
        packet.putByte("c", 1)
        packet.putShort("a", 13)
        packet.putSFSObject("p", request)

        logger.info(f'Sending {cmd} to {self.identifier}')
        logger.debug(params)

        compiled = compile_packet(packet)
        if cache:
            self.server.cached_requests[cmd] = compiled
            logger.info(f'Saved {cmd} to cache')
        asyncio.create_task(self.send(compiled))


    def set_arg(self, key, value):
        """
        Sets an argument for the client.

        Args:
            key (str): The key of the argument.
            value (Any): The value of the argument.
        """
        self.args[key] = value

    def get_arg(self, key, default=None):
        """
        Gets an argument value for the client.

        Args:
            key (str): The key of the argument.
            default (Any, optional): The default value if the key is not found.

        Returns:
            Any: The value associated with the key, or the default value if not found.
        """
        return self.args.get(key, default)

    async def kick(self):
        """
        Kicks the client from the server.
        """
        self.server.remove_client(self)

        self.writer.close()

        await self.on_kick()
        del self

    def __del__(self):
        """
        Destructor for the client instance.
        """
        logger.info(f"Client {self.identifier} deleted")
        del self.reader
        del self.writer
        del self.args

    async def on_created(self):
        """
        Callback executed when the client is created.
        """
        ...

    async def on_kick(self):
        """
        Callback executed when the client is kicked.
        """
        ...
