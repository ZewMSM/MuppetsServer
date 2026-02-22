import time

# localmodules:start
from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject, SFSArray
from database.player import PlayerIsland, PlayerStructure
from database.structure import Structure
# localmodules:end

router = SFSRouter()


def _speedup_cost_diamonds(now_ms: int, end_ms: int) -> int:
    if now_ms >= end_ms:
        return 0
    return round((end_ms - now_ms) / 1_800_000) + 1


@router.on_request("gs_buy_structure")
async def buy_structure(client: SFSServerClient, params: SFSObject):
    structure_id = params.get("structure_id")
    pos_x = params.get("pos_x")
    pos_y = params.get("pos_y")
    flip = params.get("flip")
    scale = params.get("scale")

    active_island: PlayerIsland = client.player.get_active_island
    if active_island is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "No active island")
        )

    structure = await Structure.load_by_id(structure_id)
    if structure is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Invalid structure")
        )

    if structure.structure_type not in ("decoration", "bakery"):
        if active_island.has_structure_type_id(structure_id):
            return (
                SFSObject()
                .putBool("success", False)
                .putUtfString("message", "Error buying stricture")
            )

    if not await client.player.check_prices(
        coins=structure.cost_coins,
        diamonds=structure.cost_diamonds,
        charge_if_can=True,
    ):
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error buying stricture")
        )

    await client.player.add_currency("xp", structure.xp)

    user_structure = await PlayerStructure.create_new_structure(
        active_island.id,
        structure_id,
        pos_x,
        pos_y,
        completed=True,
        flip=int(flip) if flip else 0,
        scale=float(scale) if scale else 1.0,
    )
    active_island.structures.append(user_structure)

    response = SFSObject()
    response.putBool("success", True)
    response.putSFSArray("properties", client.player.get_properties())
    response.putSFSObject("user_structure", await user_structure.to_sfs_object())
    return response


@router.on_request("gs_move_structure")
async def move_structure(client: SFSServerClient, params: "SFSObject"):
    user_structure_id = params.get("user_structure_id")
    pos_x = params.get("pos_x")
    pos_y = params.get("pos_y")
    scale = params.get("scale")

    user_structure = (
        client.player.get_active_island.get_structure(user_structure_id)
        if client.player.get_active_island
        else None
    )
    if user_structure is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error move stricture")
        )

    user_structure.pos_x = pos_x
    user_structure.pos_y = pos_y
    user_structure.scale = scale
    await user_structure.save()

    response = SFSObject()
    response.putBool("success", True)
    response.putLong("user_structure_id", user_structure_id)
    response.putSFSObject("user_structure", await user_structure.to_sfs_object())
    props = client.player.get_properties()
    props.addSFSObject(SFSObject().putInt("pos_x", pos_x))
    props.addSFSObject(SFSObject().putInt("pos_y", pos_y))
    props.addSFSObject(SFSObject().putDouble("scale", float(scale)))
    response.putSFSArray("properties", props)

    await client.send_extension(
        "gs_move_structure", SFSObject().putBool("success", True)
    )
    await client.send_extension("gs_update_structure", response)


@router.on_request("gs_mute_structure")
async def mute_structure(client: SFSServerClient, params: "SFSObject"):
    user_structure_id = params.get("user_structure_id")

    user_structure = (
        client.player.get_active_island.get_structure(user_structure_id)
        if client.player.get_active_island
        else None
    )
    if user_structure is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error mute stricture")
        )

    user_structure.muted = 0 if user_structure.muted else 1
    await user_structure.save()

    props = SFSArray()
    props.addSFSObject(SFSObject().putInt("muted", user_structure.muted))

    update_resp = SFSObject()
    update_resp.putLong("user_structure_id", user_structure_id)
    update_resp.putSFSObject("user_structure", await user_structure.to_sfs_object())
    update_resp.putSFSArray("properties", props)

    await client.send_extension(
        "gs_mute_structure", SFSObject().putBool("success", True)
    )
    await client.send_extension("gs_update_structure", update_resp)


@router.on_request("gs_flip_structure")
async def flip_structure(client: "SFSServerClient", params: "SFSObject"):
    user_structure_id = params.get("user_structure_id")

    user_structure = (
        client.player.get_active_island.get_structure(user_structure_id)
        if client.player.get_active_island
        else None
    )
    if user_structure is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error flip stricture")
        )

    user_structure.flip = 0 if user_structure.flip else 1
    await user_structure.save()

    props = SFSArray()
    props.addSFSObject(SFSObject().putInt("flip", user_structure.flip))

    update_resp = SFSObject()
    update_resp.putLong("user_structure_id", user_structure_id)
    update_resp.putSFSObject("user_structure", await user_structure.to_sfs_object())
    update_resp.putSFSArray("properties", props)

    await client.send_extension(
        "gs_flip_structure", SFSObject().putBool("success", True)
    )
    await client.send_extension("gs_update_structure", update_resp)


@router.on_request("gs_sell_structure")
async def sell_structure(client: SFSServerClient, params: "SFSObject"):
    user_structure_id = params.get("user_structure_id")

    user_structure = (
        client.player.get_active_island.get_structure(user_structure_id)
        if client.player.get_active_island
        else None
    )
    if user_structure is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error sell stricture")
        )

    if user_structure.is_complete != 1:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error sell stricture")
        )

    await client.player.add_currency("coins", user_structure.structure.cost_coins)

    client.player.get_active_island.structures.remove(user_structure)
    await user_structure.remove()

    response = SFSObject()
    response.putBool("success", True)
    response.putLong("user_structure_id", user_structure_id)
    response.putSFSArray("properties", client.player.get_properties())
    return response


@router.on_request("gs_start_upgrade_structure")
async def start_upgrade_structure(client: SFSServerClient, params: "SFSObject"):
    user_structure_id = params.get("user_structure_id")

    user_structure = (
        client.player.get_active_island.get_structure(user_structure_id)
        if client.player.get_active_island
        else None
    )
    if user_structure is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error upgrading stricture")
        )

    if user_structure.is_upgrading:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error upgrading stricture")
        )

    if not user_structure.structure.upgrades_to:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error upgrading stricture")
        )

    new_structure = await Structure.load_by_id(user_structure.structure.upgrades_to)
    if not new_structure:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error upgrading stricture")
        )

    if not await client.player.check_prices(
        coins=new_structure.cost_coins,
        diamonds=new_structure.cost_diamonds,
        charge_if_can=True,
    ):
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error upgrading stricture")
        )

    user_structure.is_upgrading = 1
    user_structure.is_complete = 0
    user_structure.date_created = int(time.time() * 1000)
    user_structure.building_completed = (
        int(time.time() * 1000) + new_structure.build_time * 1000
    )
    await user_structure.save()

    props = client.player.get_properties()
    props.addSFSObject(SFSObject().putInt("is_complete", 0))
    props.addSFSObject(SFSObject().putInt("is_upgrading", 1))
    props.addSFSObject(SFSObject().putLong("date_created", user_structure.date_created))
    props.addSFSObject(
        SFSObject().putLong("building_completed", user_structure.building_completed)
    )

    # Legacy: only send gs_update_structure, no response on gs_start_upgrade_structure
    update_resp = SFSObject()
    update_resp.putBool("success", True)
    update_resp.putLong("user_structure_id", user_structure_id)
    update_resp.putSFSArray("properties", props)
    await client.send_extension("gs_update_structure", update_resp)


@router.on_request("gs_finish_upgrade_structure")
async def finish_upgrade_structure(client: SFSServerClient, params: "SFSObject"):
    user_structure_id = params.get("user_structure_id")

    user_structure = (
        client.player.get_active_island.get_structure(user_structure_id)
        if client.player.get_active_island
        else None
    )
    if user_structure is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error move stricture")
        )

    if not user_structure.is_upgrading:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error move stricture")
        )

    new_structure_id = user_structure.structure.upgrades_to
    new_structure = await Structure.load_by_id(new_structure_id)
    if not new_structure:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error move stricture")
        )

    user_structure.structure_id = new_structure_id
    user_structure.is_upgrading = 0
    user_structure.is_complete = 1
    user_structure.date_created = int(time.time() * 1000)
    user_structure.building_completed = 0
    await user_structure.on_load_complete()
    await user_structure.save()

    await client.player.add_currency("xp", new_structure.xp)

    props = client.player.get_properties()
    props.addSFSObject(SFSObject().putInt("structure", new_structure_id))
    props.addSFSObject(SFSObject().putLong("building_completed", 0))
    props.addSFSObject(SFSObject().putInt("is_complete", 1))
    props.addSFSObject(SFSObject().putInt("is_upgrading", 0))
    props.addSFSObject(SFSObject().putLong("date_created", user_structure.date_created))

    return (
        SFSObject()
        .putBool("success", True)
        .putLong("user_structure_id", user_structure_id)
        .putSFSObject("user_structure", await user_structure.to_sfs_object())
        .putSFSArray("properties", props)
    )


@router.on_request("gs_clear_obstacle")
async def clear_obstacle(client: SFSServerClient, params: "SFSObject"):
    user_structure_id = params.get("user_structure_id")

    user_structure = (
        client.player.get_active_island.get_structure(user_structure_id)
        if client.player.get_active_island
        else None
    )
    if user_structure is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error clear obstacle")
        )

    await client.player.add_currency("xp", user_structure.structure.xp)
    client.player.get_active_island.structures.remove(user_structure)
    await user_structure.remove()

    response = SFSObject()
    response.putBool("success", True)
    response.putLong("user_structure_id", user_structure_id)
    response.putSFSArray("properties", client.player.get_properties())
    return response


@router.on_request("gs_start_obstacle")
async def start_obstacle(client: SFSServerClient, params: SFSObject):
    user_structure_id = params.get("user_structure_id")

    user_structure = (
        client.player.get_active_island.get_structure(user_structure_id)
        if client.player.get_active_island
        else None
    )
    if user_structure is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error start obstacle")
        )

    if not await client.player.check_prices(
        coins=user_structure.structure.cost_coins,
        diamonds=user_structure.structure.cost_diamonds,
        charge_if_can=True,
    ):
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error start obstacle")
        )

    now_ms = int(time.time() * 1000)
    user_structure.date_created = now_ms
    user_structure.building_completed = (
        now_ms + user_structure.structure.build_time * 1000
    )
    user_structure.last_collection = 0
    await user_structure.save()

    props = client.player.get_properties()
    props.addSFSObject(SFSObject().putLong("date_created", user_structure.date_created))
    props.addSFSObject(
        SFSObject().putLong("building_completed", user_structure.building_completed)
    )
    props.addSFSObject(SFSObject().putLong("last_collection", 0))

    response = SFSObject()
    response.putBool("success", True)
    response.putLong("user_structure_id", user_structure_id)
    response.putSFSObject("user_structure", await user_structure.to_sfs_object())
    response.putSFSArray("properties", props)
    return response


@router.on_request("gs_speed_up_structure")
async def speed_up_structure(client: SFSServerClient, params: SFSObject):
    """Ускорение апгрейда структуры за алмазы (только is_upgrading)."""
    user_structure_id = params.get("user_structure_id")

    user_structure = (
        client.player.get_active_island.get_structure(user_structure_id)
        if client.player.get_active_island
        else None
    )
    if user_structure is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Invalid structure ID.")
        )

    if not user_structure.is_upgrading:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Only UPGRADING structures supported.")
        )

    now_ms = int(time.time() * 1000)
    end_ms = user_structure.building_completed or 0
    if now_ms >= end_ms:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Structure does not require speedup.")
        )

    cost = _speedup_cost_diamonds(now_ms, end_ms)
    if not await client.player.check_prices(diamonds=cost, charge_if_can=True):
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Not enough diamonds.")
        )

    user_structure.building_completed = now_ms
    user_structure.date_created = now_ms
    await user_structure.save()

    props = client.player.get_properties()
    props.addSFSObject(SFSObject().putLong("building_completed", user_structure.building_completed))
    props.addSFSObject(SFSObject().putLong("date_created", user_structure.date_created))

    response = SFSObject()
    response.putBool("success", True)
    response.putLong("user_structure_id", user_structure_id)
    response.putSFSArray("properties", props)
    response.putSFSObject("user_structure", await user_structure.to_sfs_object())

    await client.send_extension("gs_speed_up_structure", response)
    await client.send_extension("gs_update_structure", response)


@router.on_request("gs_clear_obstacle_speed_up")
async def clear_obstacle_speed_up(client: SFSServerClient, params: SFSObject):
    user_structure_id = params.get("user_structure_id")

    user_structure = (
        client.player.get_active_island.get_structure(user_structure_id)
        if client.player.get_active_island
        else None
    )
    if user_structure is None:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error start obstacle")
        )

    now_ms = int(time.time() * 1000)
    cost = _speedup_cost_diamonds(now_ms, user_structure.building_completed or 0)
    if cost <= 0:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error start obstacle")
        )

    if not await client.player.check_prices(diamonds=cost, charge_if_can=True):
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("message", "Error start obstacle")
        )

    user_structure.building_completed = now_ms
    user_structure.date_created = now_ms
    await user_structure.save()

    props = client.player.get_properties()
    props.addSFSObject(
        SFSObject().putLong("building_completed", user_structure.building_completed)
    )
    props.addSFSObject(SFSObject().putLong("date_created", user_structure.date_created))

    response = SFSObject()
    response.putBool("success", True)
    response.putLong("user_structure_id", user_structure_id)
    response.putInt("diamonds_used", 1)
    response.putSFSArray("properties", props)

    await client.send_extension("gs_clear_obstacle_speed_up", response)
    await client.send_extension("gs_update_structure", response)

# Алиас для сборки в один файл (muppets_server использует structure_actions.router)
structure_actions = type("_RouterAlias", (), {})()
structure_actions.router = router
