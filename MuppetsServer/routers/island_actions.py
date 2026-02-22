# localmodules:start
from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject, SFSArray
from database.island import Island
from database.player import PlayerIsland
from MuppetsServer.tools.player_island_factory import PlayerIslandFactory
# localmodules:end

router = SFSRouter()


@router.on_request("gs_buy_island")
async def buy_island(client: SFSServerClient, params: SFSObject):
    island_id = int(params.get("island_id"))
    if island_id == 0:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error buying island")
        )

    island = await Island.load_by_id(island_id)
    if island is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error buying island")
        )

    if client.player.get_island_by_id(island_id) is not None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "User already have this island")
        )

    if not await client.player.check_prices(obj=island, charge_if_can=True):
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error buying island")
        )

    player_island = await PlayerIsland.create_new_island(client.player.id, island_id)
    await PlayerIslandFactory.create_initial_structures(player_island)
    client.player.islands.append(player_island)

    return (
        SFSObject()
        .putBool("success", True)
        .putSFSArray("properties", client.player.get_properties())
        .putSFSObject("user_island", await player_island.to_sfs_object())
    )


@router.on_request("gs_change_island")
async def change_island(client: SFSServerClient, params: SFSObject):
    user_island_id = params.get("user_island_id")

    if client.player.get_island(user_island_id) is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "User don't have this island")
        )

    client.player.active_island = user_island_id
    await client.player.save()

    resp = SFSObject()
    resp.putBool("success", True)
    resp.putLong("user_island_id", user_island_id)
    hidden_objects = SFSObject()
    hidden_objects.putSFSArray("objects", SFSArray())
    resp.putSFSObject("hidden_objects", hidden_objects)
    return resp

# Алиас для сборки в один файл (muppets_server использует island_actions.router)
island_actions = type("_RouterAlias", (), {})()
island_actions.router = router
