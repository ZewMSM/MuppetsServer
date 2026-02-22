import time

# localmodules:start
from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject
# localmodules:end

router = SFSRouter()


@router.on_request("gs_move_monster")
async def move_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get("user_monster_id")
    pos_x = params.get("pos_x")
    pos_y = params.get("pos_y")
    volume = params.get("volume", 1.0)

    island = client.player.get_active_island
    user_monster = island.get_monster(user_monster_id) if island else None
    if user_monster is None:
        return "Invalid monster ID."

    if pos_x is not None:
        user_monster.pos_x = pos_x
    if pos_y is not None:
        user_monster.pos_y = pos_y
    if volume is not None:
        user_monster.volume = float(volume)
    await user_monster.save()

    await client.send_extension("gs_move_monster", SFSObject().putBool("success", True))
    update_resp = (
        SFSObject().putBool("success", True).putLong("user_monster_id", user_monster_id)
    )
    update_resp.putSFSObject("monster", await user_monster.to_sfs_object())
    update_resp.putInt("pos_x", user_monster.pos_x)
    update_resp.putInt("pos_y", user_monster.pos_y)
    update_resp.putDouble("volume", float(user_monster.volume))
    await client.send_extension("gs_update_monster", update_resp)
    return update_resp


@router.on_request("gs_flip_monster")
async def flip_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get("user_monster_id")
    flipped = params.get("flipped")

    island = client.player.get_active_island
    user_monster = island.get_monster(user_monster_id) if island else None
    if user_monster is None:
        return "Invalid monster ID."

    if flipped is not None:
        user_monster.flip = 1 if flipped else 0
    else:
        user_monster.flip = 0 if user_monster.flip else 1
    await user_monster.save()

    await client.send_extension("gs_flip_monster", SFSObject().putBool("success", True))
    update_resp = (
        SFSObject().putBool("success", True).putLong("user_monster_id", user_monster_id)
    )
    update_resp.putSFSObject("monster", await user_monster.to_sfs_object())
    update_resp.putInt("flip", user_monster.flip)
    await client.send_extension("gs_update_monster", update_resp)
    return update_resp


@router.on_request("gs_mute_monster")
async def mute_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get("user_monster_id")
    muted = params.get("muted")

    island = client.player.get_active_island
    user_monster = island.get_monster(user_monster_id) if island else None
    if user_monster is None:
        return "Invalid monster ID."

    if muted is not None:
        user_monster.muted = 1 if muted else 0
    else:
        user_monster.muted = 0 if user_monster.muted else 1
    await user_monster.save()

    await client.send_extension("gs_mute_monster", SFSObject().putBool("success", True))
    update_resp = (
        SFSObject().putBool("success", True).putLong("user_monster_id", user_monster_id)
    )
    update_resp.putSFSObject("monster", await user_monster.to_sfs_object())
    update_resp.putInt("muted", user_monster.muted)
    await client.send_extension("gs_update_monster", update_resp)
    return update_resp


@router.on_request("gs_sell_monster")
async def sell_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get("user_monster_id")

    active_island = client.player.get_active_island
    user_monster = active_island.get_monster(user_monster_id)
    if user_monster is None:
        return "Invalid monster ID."

    # Legacy: full cost_coins refund (not 0.75)
    await client.player.add_currency("coins", user_monster.monster.cost_coins)

    active_island.monsters.remove(user_monster)
    await user_monster.remove()

    return (
        SFSObject()
        .putBool("success", True)
        .putLong("user_monster_id", user_monster_id)
        .putSFSArray("properties", client.player.get_properties())
    )


@router.on_request("gs_feed_monster")
async def feed_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get("user_monster_id")

    island = client.player.get_active_island
    user_monster = island.get_monster(user_monster_id) if island else None
    if user_monster is None:
        return "Invalid monster ID."

    levels_list = user_monster.monster.levels_list
    if user_monster.level > len(levels_list):
        return "This monster is already at max level!"
    mlevel = levels_list[user_monster.level - 1]

    if not await client.player.check_prices(food=mlevel.food, charge_if_can=True):
        return "You don't have enough resources to feed this monster!"

    user_monster.times_fed = (user_monster.times_fed or 0) + 1
    if user_monster.times_fed >= 4:
        user_monster.times_fed = 0
        user_monster.level += 1
    await user_monster.save()

    await client.send_extension("gs_feed_monster", SFSObject().putBool("success", True))
    update_resp = (
        SFSObject().putBool("success", True).putLong("user_monster_id", user_monster_id)
    )
    update_resp.putSFSObject("monster", await user_monster.to_sfs_object())
    update_resp.putInt("times_fed", user_monster.times_fed)
    update_resp.putInt("level", user_monster.level)
    await client.send_extension("gs_update_monster", update_resp)
    await client.send_extension(
        "gs_update_properties",
        SFSObject().putSFSArray("properties", client.player.get_properties()),
    )
    return SFSObject().putBool("success", True)


@router.on_request("gs_collect_monster")
async def collect_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get("user_monster_id")

    island = client.player.get_active_island
    user_monster = island.get_monster(user_monster_id) if island else None
    if user_monster is None:
        return "Invalid monster ID."

    mlevel = user_monster.monster.levels_list[user_monster.level - 1]
    now_ms = int(time.time() * 1000)
    time_delta_ms = now_ms - (user_monster.last_collection or now_ms)
    coins_rate = mlevel.coins
    collected = round(time_delta_ms / 60000 * coins_rate)
    if collected > mlevel.max_coins:
        collected = mlevel.max_coins

    await client.player.add_currency("coins", collected)
    user_monster.last_collection = now_ms
    user_monster.collected_coins = 0
    await user_monster.save()

    collect_response = SFSObject().putBool("success", True)
    collect_response.putLong("user_monster_id", user_monster_id)
    collect_response.putInt("coins", collected)
    await client.send_extension("gs_collect_monster", collect_response)

    update_response = (
        SFSObject().putBool("success", True).putLong("user_monster_id", user_monster_id)
    )
    update_response.putSFSObject("monster", await user_monster.to_sfs_object())
    update_response.putLong("last_collection", user_monster.last_collection)
    await client.send_extension("gs_update_monster", update_response)
    await client.send_extension(
        "gs_update_properties",
        SFSObject().putSFSArray("properties", client.player.get_properties()),
    )
    return collect_response

# Алиас для сборки в один файл (muppets_server использует monster_actions.router)
monster_actions = type("_RouterAlias", (), {})()
monster_actions.router = router
