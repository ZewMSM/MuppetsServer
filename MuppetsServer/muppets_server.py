import asyncio
import logging
import random
import time
from os import environ

import aiohttp
from aiohttp.web_routedef import static

from MuppetsServer.routers.player_actions import router as player_actions_router
from MuppetsServer.routers.island_actions import router as island_actions_router
from MuppetsServer.routers.egg_actions import router as egg_actions_router
from MuppetsServer.routers.monster_actions import router as monster_actions_router
from MuppetsServer.routers.structure_actions import router as structure_actions_router
from MuppetsServer.routers.static_data import router as static_data_router
from MuppetsServer.tools.utils import decrypt_token, generate_bind_link
from ZewSFS import SFSServer
from ZewSFS.Server import SFSServerClient, UnhandledRequest
from ZewSFS.Types import SFSObject, SFSArray
from ZewSFS.Utils import compile_packet
from config import GameConfig
from database import RedisSession
from database.player import Player
from database.stuff import GameSettings

from database.flip_board import FlipBoard, FlipLevel
from database.gene import Gene, AttunerGene
from database.island import Island, IslandThemeData
from database.level import Level
from database.monster import Monster, MonsterCostume, FlexEggs, EpicMonsterData, RareMonsterData, MonsterHome
from database.player import Player
from database.scratch_offer import ScratchOffer
from database.store import StoreItem, StoreGroup, StoreCurrency, StoreReplacement
from database.structure import Structure
from database.stuff import NucleusReward, EntityAltCosts, TitanSoulLevel, TimedEvents, GameSettings

logger = logging.getLogger('GameServer/Main')

server_id = random.randint(100000, 9999999)
current_online = 0


class GameServer:
    server: 'SFSServer' = SFSServer()

    # @staticmethod
    # async def update_cached_databases():
    #     await asyncio.gather(
    #         asyncio.create_task(Island.load_all(cached=False)),
    #         asyncio.create_task(IslandThemeData.load_all(cached=False)),
    #         asyncio.create_task(Level.load_all(cached=False)),
    #         asyncio.create_task(Monster.load_all(cached=False)),
    #         asyncio.create_task(MonsterCostume.load_all(cached=False)),
    #         asyncio.create_task(RareMonsterData.load_all(cached=False)),
    #         asyncio.create_task(EpicMonsterData.load_all(cached=False)),
    #         asyncio.create_task(MonsterHome.load_all(cached=False)),
    #         asyncio.create_task(FlexEggs.load_all(cached=False)),
    #         asyncio.create_task(ScratchOffer.load_all(cached=False)),
    #         asyncio.create_task(StoreGroup.load_all(cached=False)),
    #         asyncio.create_task(StoreItem.load_all(cached=False)),
    #         asyncio.create_task(StoreCurrency.load_all(cached=False)),
    #         asyncio.create_task(StoreReplacement.load_all(cached=False)),
    #         asyncio.create_task(Structure.load_all(cached=False)),
    #         asyncio.create_task(NucleusReward.load_all(cached=False)),
    #         asyncio.create_task(EntityAltCosts.load_all(cached=False)),
    #         asyncio.create_task(TimedEvents.load_all(cached=False)),
    #         asyncio.create_task(TitanSoulLevel.load_all(cached=False)),
    #     )
    #
    # @staticmethod
    # async def cache_static_data():
    #     async def cache_task(name):
    #         request = SFSObject()
    #         request.putUtfString("c", name)
    #         request.putInt("r", -1)
    #         request.putSFSObject("p", await static_data_router.request_handlers.get(name)(None, None))
    #
    #         packet = SFSObject()
    #         packet.putByte("c", 1)
    #         packet.putShort("a", 13)
    #         packet.putSFSObject("p", request)
    #
    #         static_data_router.cached_requests[name] = compile_packet(packet)
    #
    #     await asyncio.gather(
    #         *[cache_task(name) for name in static_data_router.cached_requests]
    #     )

    # @staticmethod
    # async def load_player_object(client: SFSServerClient):
    #     bbb_id = client.get_arg('bbb_id')
    #     player = await Player.load_by_id(bbb_id)
    #     if player is None:
    #         player = Player()
    #         player.id = bbb_id
    #         await player.create_new_player()
    #
    #     player.last_login = time.time()
    #     await player.save()
    #     client.set_arg('player', player)
    #     client.player = player

    @staticmethod
    async def update_online_task():
        global current_online
        while 1:
            await RedisSession.set(f"online:{server_id}", str(len(GameServer.server.clients)), ex=10)

            total_online = 0
            cursor = 0
            while True:
                cursor, keys = await RedisSession.scan(cursor=cursor, match="online:*", count=100)
                for key in keys:
                    online_count = await RedisSession.get(key)
                    if online_count:
                        total_online += int(online_count)

                if cursor == 0:
                    break

            current_online = total_online
            await asyncio.sleep(7)

    @staticmethod
    async def error_callback(client: 'SFSServerClient', err: Exception, tb: str):
        if isinstance(err, UnhandledRequest):
            await client.send_extension(err.cmd, SFSObject().putBool('success', False))
        else:
            logger.error(tb)

    @staticmethod
    async def login_callback(client: 'SFSServerClient', username, password, auth_params: SFSObject):
        async with aiohttp.ClientSession() as session:
            async with session.post(environ.get('AUTH_SERVER_URL') + 'authUser.php', params={
                'addr': client.address,
            }) as resp:
                data = await resp.json()
                if (bbb_id := data.get('bbb_id', None)) is None:
                    return False

        client.set_arg('bbb_id', bbb_id)
        client.set_arg('client_version', data.get('client_version', None))
        client.set_arg('player', None)

        # asyncio.create_task(load_player_object())
        await client.send_extension('gs_initialized', SFSObject().putLong('bbb_id', bbb_id))
        return True

    @staticmethod
    async def start():
        asyncio.create_task(GameServer.update_online_task())
        await GameServer.server.serve_forever()
