import asyncio
import io
import logging
from asyncio import StreamReader, StreamWriter
from socket import socket
from typing import List

from ZewSFS.Types import SFSObject
from ZewSFS.Utils import decompile_packet, compile_packet

logger = logging.getLogger('ZewSFS/SFSClient')


class DisconnectException(Exception):
    """
    An exception that is raised when the client disconnects from the server.
    """

    def __str__(self):
        return "The client has disconnected from the server"

    def __repr__(self):
        return "DisconnectException"


class SFSClient:
    """
    A client for SmartFoxServer (SFS).

    Attributes:
        connection (socket): The socket connection to the server.
        loop (asyncio.AbstractEventLoop): The event loop in which this client is running.

    """

    # connection = None
    loop = None

    def __init__(self, proxy_host: str = None, proxy_port: int = None, proxy_login: str = None, proxy_password: str = None):
        """
        Initialize a new SFSClient.

        Args:
            proxy_host (str, optional): The host of the proxy server. Defaults to None.
            proxy_port (int, optional): The port of the proxy server. Defaults to None.
            proxy_login (str, optional): The login for the proxy server. Defaults to None.
            proxy_password (str, optional): The password for the proxy server. Defaults to None.
        """

        self.reader: 'StreamReader' = None
        self.writer: 'StreamWriter' = None

        # if proxy_host is None or proxy_port is None:
        #     self.connection = socket(AF_INET, SOCK_STREAM)
        #     self.connection.setblocking(False)
        # else:
        #     # pip install pysocks requests urllib3
        #
        #     import socks
        #
        #     self.connection = socks.socksocket()
        #     self.connection.set_proxy(socks.SOCKS5, proxy_host, proxy_port, username=proxy_login, password=proxy_password)
        # TODO: нахуй прокси

    def __del__(self):
        """
        Clean up the client by closing the connection.
        """

        try:
            self.writer.close()
            self.reader = None
        except:
            ...

    async def disconnect(self):
        """
        Disconnect the client from the server.
        """

        try:
            del self.reader
            self.writer.close()
            await self.writer.wait_closed()
        except:
            ...

    async def connect(self, host: str, port: int = 9933):
        """
        Connect to the server.

        Args:
            host (str): The host of the server.
            port (int, optional): The port of the server. Defaults to 9933.
        """

        logger.info(f'Connecting to {host}:{port}')

        # self.loop = asyncio.get_running_loop()
        # await self.loop.sock_connect(self.connection, (host, port))

        self.reader, self.writer = await asyncio.open_connection(
            host, port)

        return await self.send_handshake_request()

    async def send_raw(self, packet: bytes):
        """
        Send a raw packet to the server.

        Args:
            packet (bytes): The packet to send.
        """

        self.writer.write(packet)
        await self.writer.drain()

    async def send_packet(self, c: int, a: int, params: SFSObject):
        """
        Send a packet to the server.

        Args:
            c (int): The controller id.
            a (int): The action id.
            params (SFSObject): The parameters of the packet.
        """

        packet = SFSObject()
        packet.putByte("c", c)
        packet.putShort("a", a)
        packet.putSFSObject("p", params)
        await self.send_raw(compile_packet(packet))

    async def send_handshake_request(self):
        """
        Send a handshake request to the server.
        """

        session_info = SFSObject()
        session_info.putUtfString("api", "1.0.3")
        session_info.putUtfString("cl", "UnityPlayer::")
        session_info.putBool("bin", True)

        await self.send_packet(0, 0, session_info)

        return await self.read_response()

    async def send_login_request(self, zone: str, username: str, password: str, auth_params: SFSObject):
        """
        Send a login request to the server.

        Args:
            zone (str): The zone to log in to.
            username (str): The username to log in with.
            password (str): The password to log in with.
            auth_params (SFSObject): The authentication parameters.
        """

        auth_info = SFSObject()
        auth_info.putUtfString("zn", zone)
        auth_info.putUtfString("un", username)
        auth_info.putUtfString("pw", password)
        auth_info.putSFSObject("p", auth_params)

        await self.send_packet(0, 1, auth_info)

    async def send_extension_request(self, command: str, params: SFSObject):
        """
        Send an extension request to the server.

        Args:
            command (str): The command of the extension request.
            params (SFSObject): The parameters of the extension request.
        """

        request = SFSObject()
        request.putUtfString("c", command)
        request.putInt("r", -1)
        request.putSFSObject("p", params)

        logger.info(f'Sending {command} to server')

        await self.send_packet(1, 12, request)

    async def raw_read(self, n) -> bytes:
        resp = await self.reader.read(n)
        if not resp:
            raise DisconnectException('The client has disconnected from the server')
        return resp

    async def read_response(self):
        """
        Read a response from the server.
        """

        response = b''
        packet_size = b''

        packet_type = await self.raw_read(1)
        __ = packet_type

        if packet_type == b'\x88':
            packet_size_len = 4
        elif packet_type == b'\x80':
            packet_size_len = 2
        else:
            return SFSObject(), b""

        while packet_size_len > 0:
            new = await self.raw_read(packet_size_len)
            packet_size += new
            packet_size_len -= len(new)

        __ += packet_size

        packet_size = int.from_bytes(packet_size, "big")

        while len(response) < packet_size:
            chunk_size = min(packet_size - len(response), 4096 * 4)
            response += await self.raw_read(chunk_size)

        __ += response

        packet_bytes = io.BytesIO(response)
        logger.debug(f'Got {len(response)} bytes from server')
        response = decompile_packet(packet_bytes)

        logger.debug(response)
        logger.debug(response.to_python_object(True))

        return response

    @staticmethod
    async def timeout_task(timeout):
        """
        A task that raises an exception after a timeout.

        Args:
            timeout (int): The timeout in seconds.
        """

        await asyncio.sleep(timeout)
        raise Exception(f"Timeout after {timeout} seconds")

    async def wait_extension_response(self, command) -> SFSObject:
        """
        Wait for a response to an extension request.

        Args:
            command (str): The command of the extension request.
            timeout (int, optional): The timeout in seconds. Defaults to 99999.

        Returns:
            SFSObject: The response.
        """

        cmd, params = '', ''

        while cmd != command:
            try:
                response = await self.read_response()

                if 'c' in response:
                    cmd, params = response.get("c"), response.get("p")
            except Exception as e:
                print(f"An error occurred: {e}")
                raise e

        return params

    async def wait_requests(self, commands: List[str], timeout=999999) -> (str, SFSObject):
        """
        Wait for a response to any of a list of requests.

        Args:
            commands (List[str]): The commands of the requests.
            timeout (int, optional): The timeout in seconds. Defaults to 999999.

        Returns:
            tuple: The command and parameters of the response.
        """

        cmd, params = '', ''

        while cmd not in commands:
            try:
                response = await self.read_response()

                if 'c' in response:
                    cmd, params = response.get("c"), response.get("p")

            except asyncio.TimeoutError:
                print(f"Timeout Error: No response for commands '{commands}' within {timeout} seconds.")
                raise
            except DisconnectException as e:
                raise e
            except Exception as e:
                print(f"An error occurred: {e}")
                continue

        # timeout_task.cancel()
        return cmd, params

    async def request(self, command: str, params: SFSObject = None) -> SFSObject:
        """
        Send a request and wait for a response.

        Args:
            command (str): The command of the request.
            params (SFSObject): The parameters of the request.

        Returns:
            SFSObject: The response.
        """

        if params is None:
            params = SFSObject()

        await self.send_extension_request(command, params)
        return await self.wait_extension_response(command)
