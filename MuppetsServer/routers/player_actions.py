import asyncio
import time

# localmodules:start
from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject
# localmodules:end

router = SFSRouter()


async def _delayed_update_properties(client: SFSServerClient):
    await asyncio.sleep(5)
    try:
        await client.send_extension(
            "gs_update_properties",
            SFSObject().putSFSArray("properties", client.player.get_properties()),
        )
    except Exception:
        pass


@router.on_request("gs_player")
async def send_player_data(client: SFSServerClient, request: SFSObject):
    for i in range(20):
        if client is not None:
            if i == 3:
                await client.send_extension(
                    "gs_display_generic_message",
                    SFSObject()
                    .putBool("force_logout", False)
                    .putUtfString("msg", "WAIT_PLEASE_HEAVY_LOAD_ON_SERVER_MESSAGE"),
                )
            elif i == 10:
                await client.send_extension(
                    "gs_display_generic_message",
                    SFSObject()
                    .putBool("force_logout", False)
                    .putUtfString("msg", "EXTREMELY_HEAVY_LOAD_ON_SERVER_MESSAGE"),
                )
            if client.player is None:
                await asyncio.sleep(1)
            else:
                pdata = (
                    SFSObject()
                    .putSFSObject("player_object", await client.player.to_sfs_object())
                    .putLong("server_time", int(time.time() * 1000))
                )
                if await client.player.redeem_daily_reward():
                    asyncio.create_task(_delayed_update_properties(client))
                return pdata
        else:
            return None

    await client.send_extension(
        "gs_display_generic_message",
        SFSObject()
        .putBool("force_logout", False)
        .putUtfString("msg", "SERVER_PIZDA_MESSAGE"),
    )

    await client.kick()
    return "Error"

# Алиас для сборки в один файл (muppets_server использует player_actions.router)
player_actions = type("_RouterAlias", (), {})()
player_actions.router = router
