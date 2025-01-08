import asyncio
import logging
from os import environ

import uvloop

from GameServer import GameServer
from database import init_database

logging.basicConfig(
    level=logging.DEBUG if environ.get('type', 'release') == 'debug' else logging.INFO,
    format='%(levelname)s/%(name)s:\t%(message)s'
)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

async def main():
    await init_database()
    await GameServer.start()


if __name__ == '__main__':
    asyncio.run(main())
