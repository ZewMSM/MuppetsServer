"""
SFSServer and SFSServerClient module

This module defines two main classes: `SFSServer` and `SFSServerClient`, which together form the server-client architecture for a simple socket-based server.

Classes:
    - SFSServer: Represents the server, handles client connections and requests.
    - SFSServerClient: Represents an individual client connected to the server.

Exceptions:
    - UnhandledRequest: Raised when a request is received that cannot be handled.

Functions:
    - empty_callback: A placeholder function that returns True. Used as a default callback.
"""

import asyncio
import logging
import secrets
import traceback
from asyncio import StreamWriter, StreamReader
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any

from ZewSFS.Server.Router import SFSRouter
from ZewSFS.Server.ServerClient import SFSServerClient
from ZewSFS.Types import SFSObject

logger = logging.getLogger('ZewSFS/SFSServer')


class UnhandledRequest(Exception):
    """
    Exception raised when a request is received that cannot be handled.

    Attributes:
        cmd (str): The command that was unhandled.
    """

    def __init__(self, cmd):
        self.cmd = cmd
        super().__init__()

    def __repr__(self):
        return f'UnhandledRequest {self.cmd}'

    def __str__(self):
        return f'UnhandledRequest {self.cmd}'


async def empty_callback(*args, **kwargs):
    """
    A placeholder callback function that always returns True.
    """
    return True


class SFSServer(SFSRouter):
    """
    Represents the main server which manages client connections and handles requests.

    Attributes:
        clients (list): A list of connected clients.
        connection_callback (Callable): The callback for handling new connections.
        handshake_callback (Callable): The callback for handling handshake requests.
        login_callback (Callable): The callback for handling login requests.
        error_callback (Callable): The callback for handling errors.
        request_handlers (dict): A dictionary of request handlers for specific commands.
    """
    clients: list['SFSServerClient'] = []
    cached_requests = dict()

    connection_callback: Callable[['SFSServerClient'], Coroutine[Any, Any, bool]] = empty_callback
    handshake_callback: Callable[['SFSServerClient', 'SFSObject'], Awaitable[None]] = empty_callback
    login_callback: Callable[['SFSServerClient', str, str, 'SFSObject'], Awaitable[None]] = empty_callback
    error_callback: Callable[['SFSServerClient', Exception, str], Awaitable[None]] = empty_callback

    def __init__(self, host: str = '0.0.0.0', port: int = 9933, zone_name: str | None = None):
        self.host = host
        self.port = port
        self.zone_name = zone_name

    def get_client_by_address(self, address: str):
        """
        Gets a list of clients by their address.

        Args:
            address (str): The address of the clients.

        Returns:
            list: A list of clients with the specified address.
        """
        return [client for client in self.clients if client.address == address]

    def get_client_by_identifier(self, identifier: str):
        """
        Gets a list of clients by their identifier.

        Args:
            identifier (str): The identifier of the clients.

        Returns:
            list: A list of clients with the specified identifier.
        """
        return [client for client in self.clients if client.identifier == identifier]

    def is_client_exists(self, identifier: str):
        """
        Checks if a client exists by their identifier.

        Args:
            identifier (str): The identifier to check.

        Returns:
            bool: True if the client exists, otherwise False.
        """
        return len(self.get_client_by_identifier(identifier)) > 0

    def add_client(self, client: 'SFSServerClient'):
        """
        Adds a client to the server.

        Args:
            client (SFSServerClient): The client to add.
        """
        self.clients.append(client)

    def remove_client(self, client: 'SFSServerClient'):
        """
        Removes a client from the server.

        Args:
            client (SFSServerClient): The client to remove.
        """
        try:
            self.clients.remove(client)
        except:
            ...

    async def _process_request(self, client: 'SFSServerClient', request: 'SFSObject'):
        """
        Processes a request from a client.

        Args:
            client (SFSServerClient): The client sending the request.
            request (SFSObject): The request data.
        """
        if client.state == 'handshake':
            if request.get('c') == b'\x00' and request.get('a') == 0:
                identifier = secrets.token_urlsafe(32)
                client.identifier = identifier
                logger.info(f'HandshakeRequest from {client.identifier}')
                logger.debug(request)
                client.state = 'login'

                asyncio.create_task(client.send_handshake())
                if not await self.handshake_callback(client, request):
                    return await client.kick()

            return

        if client.state == 'login':
            if request.get('c') == b'\x00' and request.get('a') == 1:
                logger.info(f'LoginRequest from {client.identifier}')
                logger.debug(request)
                params: SFSObject = request.get('p')
                zone_name = params.get('zn')
                username = params.get('un')
                password = params.get('pw')
                auth_params: SFSObject = params.get('p')

                client.state = 'play'

                if zone_name != self.zone_name and self.zone_name is not None:
                    return client.kick()

                if not await self.login_callback(client, username, password, auth_params):
                    await asyncio.sleep(1)
                    return await client.kick()

                client.set_arg('username', username)
                client.set_arg('password', password)
            return

        if client.state == 'play':
            if request.get('c') == b'\x01' and request.get('a') in (12, 13):
                try:
                    cmd: str = request.get("p").get("c")
                    params: 'SFSObject' = request.get("p").get("p")

                    logger.info(f'ExtensionRequest from {client.identifier}: {cmd}')
                    logger.debug(params)

                    if (cached_response := self.cached_requests.get(cmd, None)) is not None:
                        logger.info(f'Loaded {cmd} from cache')
                        await client.send(cached_response)
                        return

                    handler = self.request_handlers.get(cmd)
                    if handler is not None:
                        resp = await handler(client, params)
                        if type(resp) is str:
                            await client.send_extension(cmd, SFSObject(resp).putBool('success', False).putUtfString(
                                'message', resp))
                        elif type(resp) is SFSObject:
                            await client.send_extension(cmd, resp, cache=cmd in self.cached_requests)
                    else:
                        logger.warning(f'Unhandled request from {client.identifier}: {cmd}')
                        raise UnhandledRequest(cmd)

                except (ConnectionError, asyncio.IncompleteReadError) as e:
                    asyncio.create_task(self.error_callback(client, e, traceback.format_exc()))
                    raise e
                except Exception as e:
                    asyncio.create_task(self.error_callback(client, e, traceback.format_exc()))
            else:
                logger.info(f'Invalid message from {client.identifier}: {request}')

    async def _handle_connection(self, reader: 'StreamReader', writer: 'StreamWriter'):
        """
        Handles a new client connection.

        Args:
            reader (StreamReader): Stream reader for communication.
            writer (StreamWriter): Stream writer for communication.
        """
        addr = writer.get_extra_info("peername")[0]
        logger.info(f'New connection from {addr}')

        client = SFSServerClient(None, addr, reader, writer, self)
        if not await self.connection_callback(client):
            return await client.kick()

        try:
            while True:
                await self._process_request(client, await client.read_request())
        except ConnectionError:
            ...
        except asyncio.IncompleteReadError:
            ...
        except Exception as e:
            logging.exception(traceback.format_exc())

        self.remove_client(client)
        logger.info(f'Disconnected from {addr}')
        asyncio.create_task(client.kick())

    async def serve_forever(self):
        """
        Starts the server and listens for incoming connections.
        """
        server = await asyncio.start_server(self._handle_connection, self.host, self.port)
        async with server:
            logger.info(f'Serving on {self.host}:{self.port}')
            while 1:
                try:
                    await server.serve_forever()
                except Exception as e:
                    await asyncio.sleep(5)
                    logging.exception(traceback.format_exc())

    def include_router(self, router: 'SFSRouter'):
        self.request_handlers |= router.request_handlers
        self.cached_requests |= router.cached_requests

    def on_connect(self):
        """
        Decorator for setting the connection callback.
        """

        def decorator(func):
            self.connection_callback = func
            return func

        return decorator

    def on_handshake(self):
        """
        Decorator for setting the handshake callback.
        """

        def decorator(func):
            self.handshake_callback = func
            return func

        return decorator

    def on_error(self):
        """
        Decorator for setting the error callback.
        """

        def decorator(func):
            self.error_callback = func
            return func

        return decorator

    def on_login(self):
        """
        Decorator for setting the login callback.
        """

        def decorator(func):
            self.login_callback = func
            return func

        return decorator
