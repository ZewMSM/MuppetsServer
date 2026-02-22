import asyncio
import logging
from os import environ

import uvicorn
from dotenv import load_dotenv

load_dotenv()

# localmodules:start
from config import HTTP_PORT
from database import init_database
from MuppetsServer import MuppetsServer
from MuppetsServer.auth_app import app as auth_app

# localmodules:end

logging.basicConfig(
    level=logging.DEBUG if environ.get("type", "release") == "debug" else logging.INFO,
    format="%(levelname)s/%(name)s:\t%(message)s",
)


async def main():
    await init_database()
    config = uvicorn.Config(auth_app, host="0.0.0.0", port=int(HTTP_PORT))
    server = uvicorn.Server(config)
    await asyncio.gather(server.serve(), MuppetsServer.start())


asyncio.run(main())
