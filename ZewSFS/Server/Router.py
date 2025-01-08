from typing import Callable, Awaitable, Any

from ZewSFS.Types import SFSObject


class SFSRouter:
    """
        Represents the class which handles requests and routes they to server.
    """

    request_handlers: dict[str, Callable[['SFSServerClient', 'SFSObject'], Awaitable[Any]]] = {}
    cached: bool = None

    def on_request(self, message, cached: bool = None):
        """
        Decorator for setting a request handler for a specific command.
        """

        def decorator(func):
            if cached or self.cached:
                self.cached_requests[message] = None
            self.request_handlers[message] = func
            return func

        return decorator

    def __init__(self, cached: bool = False):
        self.cached_requests = dict()
        self.cached = cached