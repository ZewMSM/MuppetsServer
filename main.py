import asyncio
import logging
from os import environ

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from database import init_database
from MuppetsServer import MuppetsServer
from MuppetsServer.auth_app import app as auth_app

logging.basicConfig(
    level=logging.DEBUG if environ.get("type", "release") == "debug" else logging.INFO,
    format="%(levelname)s/%(name)s:\t%(message)s",
)

AUTH_PORT = 6362


async def main():
    await init_database()
    config = uvicorn.Config(auth_app, host="0.0.0.0", port=AUTH_PORT)
    server = uvicorn.Server(config)
    await asyncio.gather(server.serve(), MuppetsServer.start())


if __name__ == "__main__":
    asyncio.run(main())
