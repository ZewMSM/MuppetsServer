import time

# localmodules:start
from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject
from database.monster import Monster
from database.player import PlayerMonster, PlayerStructure
# localmodules:end

router = SFSRouter()

# Legacy: getStructureOnIslandByStructureType(active_island, 1) then 324 — приоритет 1, иначе 324
NURSERY_STRUCTURE_ID_PRIMARY = 1
NURSERY_STRUCTURE_ID_FALLBACK = 324


def _speedup_cost_diamonds(now_ms: int, end_ms: int) -> int:
    if now_ms >= end_ms:
        return 0
    return round((end_ms - now_ms) / 1_800_000) + 1


@router.on_request("gs_buy_egg")
async def buy_egg(client: SFSServerClient, params: SFSObject):
    monster_id = int(params.get("monster_id", 0))
    island = client.player.get_active_island
    if not island:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    monster = await Monster.load_by_id(monster_id)
    if monster is None:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    # Legacy: st1 = getStructureOnIslandByStructureType(active_island, 1); st2 = 324; st = st1 ?? st2
    nursery = island.get_structure_by_structure_id(NURSERY_STRUCTURE_ID_PRIMARY)
    if nursery is None:
        nursery = island.get_structure_by_structure_id(NURSERY_STRUCTURE_ID_FALLBACK)
    if nursery is None:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    if monster.cost_diamonds == 0:
        coin_cost = monster.cost_coins
        diamond_cost = 0
    else:
        coin_cost = 0
        diamond_cost = monster.cost_diamonds

    if not await client.player.check_prices(
        coins=coin_cost, diamonds=diamond_cost, charge_if_can=True
    ):
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    now_ms = int(time.time() * 1000)
    completion_time_ms = now_ms + monster.build_time * 1000

    nursery.obj_data = monster_id
    nursery.obj_end = completion_time_ms
    await nursery.save()

    user_egg = (
        SFSObject()
        .putLong("obj_end", completion_time_ms)
        .putInt("obj_data", monster_id)
    )
    return (
        SFSObject()
        .putSFSObject("user_egg", user_egg)
        .putBool("success", True)
        .putBool("remove_buyback", False)
        .putSFSArray("properties", client.player.get_properties())
    )


@router.on_request("gs_hatch_egg")
async def hatch_egg(client: SFSServerClient, params: SFSObject):
    user_structure_id = int(params.get("user_structure_id", 0))
    pos_x = int(params.get("pos_x", 0))
    pos_y = int(params.get("pos_y", 0))
    flip = int(bool(params.get("flip", 0)))

    island = client.player.get_active_island
    if not island:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    user_egg = island.get_egg(user_structure_id)
    if user_egg is None:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    monster_id = user_egg.obj_data
    monster = await Monster.load_by_id(monster_id)

    user_egg.obj_data = None
    user_egg.obj_end = None
    await user_egg.save()

    user_monster = await PlayerMonster.create_new_monster(island.id, monster_id)
    user_monster.pos_x = pos_x
    user_monster.pos_y = pos_y
    user_monster.flip = flip
    await user_monster.save()

    island.monsters.append(user_monster)
    island.structures = await PlayerStructure.load_all_by(user_island_id=island.id)

    if monster and monster.xp:
        await client.player.add_currency("xp", monster.xp)

    resp = (
        SFSObject()
        .putBool("success", True)
        .putLong("user_structure_id", user_structure_id)
        .putSFSObject("monster", await user_monster.to_sfs_object())
        .putSFSArray("properties", client.player.get_properties())
    )
    await client.send_extension("gs_hatch_egg", resp)

    full_player = SFSObject().putSFSObject(
        "player_object", await client.player.to_sfs_object()
    )
    full_player.putLong("server_time", int(time.time() * 1000))
    await client.send_extension("gs_player", full_player)

    return resp


@router.on_request("gs_speed_up_hatching")
async def speed_up_hatching(client: SFSServerClient, params: SFSObject):
    user_structure_id = int(params.get("user_structure_id", 0))
    island = client.player.get_active_island
    if not island:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    user_egg = island.get_egg(user_structure_id)
    if user_egg is None or user_egg.obj_data is None:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    now_ms = int(time.time() * 1000)
    cost = _speedup_cost_diamonds(now_ms, user_egg.obj_end or 0)
    if cost <= 0:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    if not await client.player.check_prices(diamonds=cost, charge_if_can=True):
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    user_egg.obj_end = now_ms + 1500
    await user_egg.save()

    response = SFSObject().putBool("success", True)
    response.putSFSObject(
        "user_egg",
        SFSObject()
        .putLong("obj_end", user_egg.obj_end)
        .putInt("obj_data", user_egg.obj_data),
    )
    response.putSFSArray("properties", client.player.get_properties())
    await client.send_extension("gs_speed_up_hatching", response)
    return response


@router.on_request("gs_sell_egg")
async def sell_egg(client: SFSServerClient, params: SFSObject):
    user_structure_id = int(params.get("user_structure_id", 0))
    island = client.player.get_active_island
    if not island:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    user_egg = island.get_egg(user_structure_id)
    if user_egg is None or user_egg.obj_data is None:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    monster = await Monster.load_by_id(user_egg.obj_data)
    # Legacy: (int) Math.round(Monster.getMonsterByID(...).cost_coins * 0.75)
    refund = int(round((monster.cost_coins or 0) * 0.75)) if monster else 0
    await client.player.add_currency("coins", refund)

    user_egg.obj_data = None
    user_egg.obj_end = None
    await user_egg.save()

    response = SFSObject().putBool("success", True)
    response.putSFSArray("properties", client.player.get_properties())
    await client.send_extension("gs_sell_egg", response)
    return response

# Алиас для сборки в один файл (muppets_server использует egg_actions.router)
egg_actions = type("_RouterAlias", (), {})()
egg_actions.router = router
