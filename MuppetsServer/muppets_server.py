import logging

from MuppetsServer.routers import (
    baking_actions,
    egg_actions,
    island_actions,
    misc_actions,
    monster_actions,
    player_actions,
    static_data,
    structure_actions,
)
from ZewSFS import SFSServer
from ZewSFS.Server import SFSServerClient
from ZewSFS.Types import SFSObject

logger = logging.getLogger("MuppetsServer/Main")


async def _load_player(client: "SFSServerClient", bbb_id: int):
    from database.player import Player

    player = await Player.load_by_id(bbb_id)
    if player is None:
        player = Player()
        player.id = bbb_id
        player.coins = 5000
        player.diamonds = 20
        player.food = 2500
        player.xp = 655
        player.level = 5
        await player.save()
        await player.on_load_complete()
        await player.save()
    client.player = player


class MuppetsServer:
    server: "SFSServer" = SFSServer(port=9933)

    @staticmethod
    async def error_callback(client: "SFSServerClient", err: Exception, tb: str):
        logger.error(tb)

    @staticmethod
    async def login_callback(
        client: "SFSServerClient", username, password, auth_params: SFSObject
    ):
        bbb_id = 1796072285
        client.set_arg("bbb_id", bbb_id)
        client.set_arg("client_version", auth_params.get("client_version", None))
        client.set_arg("client_os", auth_params.get("client_os", None))
        client.set_arg("client_platform", auth_params.get("client_platform", None))
        client.set_arg("client_device", auth_params.get("client_device", None))

        await _load_player(client, bbb_id)

        await client.send_extension(
            "gs_initialized", SFSObject().putLong("bbb_id", 1796072285)
        )
        return True

    @staticmethod
    async def start():
        MuppetsServer.server.error_callback = MuppetsServer.error_callback
        MuppetsServer.server.login_callback = MuppetsServer.login_callback

        MuppetsServer.server.include_router(static_data.router)
        MuppetsServer.server.include_router(monster_actions.router)
        MuppetsServer.server.include_router(egg_actions.router)
        MuppetsServer.server.include_router(structure_actions.router)
        MuppetsServer.server.include_router(island_actions.router)
        MuppetsServer.server.include_router(baking_actions.router)
        MuppetsServer.server.include_router(misc_actions.router)
        MuppetsServer.server.include_router(player_actions.router)

        await MuppetsServer.server.serve_forever()
