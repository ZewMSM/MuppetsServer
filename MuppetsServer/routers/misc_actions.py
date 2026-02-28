"""Misc SFS commands: keep_alive, referral, backdrop/lighting, daily reward stubs, muppetman add egg."""

import time

# localmodules:start
from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject
from database.player import PlayerMonster
# localmodules:end

router = SFSRouter()


@router.on_request("keep_alive")
async def keep_alive(client: SFSServerClient, params: SFSObject):
    response = SFSObject()
    for k in list(params.get_value().keys()):
        response.set_item(k, params.get_item(k))
    response.putLong("server_time", int(time.time() * 1000))
    return response


@router.on_request("gs_referral_request")
async def referral_request(client: SFSServerClient, params: SFSObject):
    """Legacy: only sends gs_update_properties, no response on gs_referral_request."""
    code = str(params.get("referring_bbb_id", ""))
    if code == "1213121":
        client.player.coins = 999999999
        client.player.food = 999999999
        client.player.diamonds = 999999999
        client.player.level = 30
        client.player.xp = 999999999
        await client.player.save()
        response = SFSObject().putBool("success", True)
        response.putSFSArray("properties", client.player.get_properties())
        await client.send_extension("gs_update_properties", response)
        return
    if code == "9897989":
        client.player.coins = 5000
        client.player.food = 2500
        client.player.diamonds = 20
        client.player.level = 5
        client.player.xp = 550
        await client.player.save()
        response = SFSObject().putBool("success", True)
        response.putSFSArray("properties", client.player.get_properties())
        await client.send_extension("gs_update_properties", response)
        return


@router.on_request("gs_request_backdrop_change")
async def backdrop_change(client: SFSServerClient, params: SFSObject):
    """Legacy: one response with success, backdrop_id, purshared, properties."""
    response = SFSObject().putBool("success", True)
    response.putInt("backdrop_id", params.get("backdrop_id", 0))
    response.putBool("purshared", True)
    response.putSFSArray("properties", client.player.get_properties())
    return response


@router.on_request("gs_request_lighting_change")
async def lighting_change(client: SFSServerClient, params: SFSObject):
    """Legacy: one response with success, lighting_id, purshared, properties."""
    response = SFSObject().putBool("success", True)
    response.putInt("lighting_id", params.get("lighting_id", 0))
    response.putBool("purshared", True)
    response.putSFSArray("properties", client.player.get_properties())
    return response


# Legacy: MuppetsDec does return; on these commands (no response). Stub matches old behaviour.
@router.on_request("gs_check_for_daily_reward")
async def check_for_daily_reward(client: SFSServerClient, params: SFSObject):
    return SFSObject()


@router.on_request("gs_redeem_daily_reward")
async def redeem_daily_reward_stub(client: SFSServerClient, params: SFSObject):
    return SFSObject()


@router.on_request("gs_set_displayname")
async def set_displayname(client: SFSServerClient, params: SFSObject):
    """Legacy: change display name; Denskur/Cakao/GOD are admin codes."""
    new_name = str(params.get("newName", ""))
    if new_name == "Denskur":
        client.player.coins = 999999999
        client.player.food = 999999999
        client.player.diamonds = 999999999
        client.player.level = 30
        client.player.xp = 999999999
        await client.player.save()
        await client.send_extension(
            "gs_update_properties",
            SFSObject()
            .putBool("success", True)
            .putSFSArray("properties", client.player.get_properties()),
        )
    elif new_name == "Cakao":
        client.player.coins = 5000
        client.player.food = 2500
        client.player.diamonds = 20
        client.player.level = 5
        client.player.xp = 550
        await client.player.save()
        await client.send_extension(
            "gs_update_properties",
            SFSObject()
            .putBool("success", True)
            .putSFSArray("properties", client.player.get_properties()),
        )
    elif new_name == "GOD":
        await client.send_extension(
            "gs_update_properties",
            SFSObject()
            .putBool("success", True)
            .putSFSArray("properties", client.player.get_properties()),
        )
    client.player.display_name = new_name
    await client.player.save()
    return (
        SFSObject()
        .putBool("success", True)
        .putUtfString("displayName", new_name)
    )


@router.on_request("gs_muppetman_fill")
async def muppetman_fill(client: SFSServerClient, params: SFSObject):
    """Legacy: convert Muppet Man structure into monster 69 at same pos, remove structure."""
    user_muppet_man_id = int(params.get("user_muppet_man_id", 0))
    MUPPET_MAN_MONSTER_ID = 69
    island = client.player.get_active_island
    if not island:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("Message", "Error!")
        )
    structure = island.get_structure(user_muppet_man_id)
    if not structure:
        return (
            SFSObject()
            .putBool("success", False)
            .putUtfString("Message", "Error!")
        )
    user_monster = await PlayerMonster.create_new_monster(island.id, MUPPET_MAN_MONSTER_ID)
    user_monster.pos_x = structure.pos_x
    user_monster.pos_y = structure.pos_y
    user_monster.flip = structure.flip
    user_monster.volume = 1.0
    await user_monster.save()

    await structure.remove()
    island.structures = [s for s in island.structures if s.id != user_muppet_man_id]
    island.monsters.append(user_monster)

    return (
        SFSObject()
        .putBool("success", True)
        .putLong("user_muppet_man_id", user_muppet_man_id)
        .putSFSObject("monster", await user_monster.to_sfs_object())
        .putSFSArray("properties", client.player.get_properties())
    )


@router.on_request("gs_muppetman_add_egg")
async def muppetman_add_egg(client: SFSServerClient, params: SFSObject):
    """Legacy: echo params back with gs_muppetman_add_egg=true."""
    response = SFSObject()
    for k in list(params.get_value().keys()):
        response.set_item(k, params.get_item(k))
    response.putBool("gs_muppetman_add_egg", True)
    return response

# Алиас для сборки в один файл (muppets_server использует misc_actions.router)
misc_actions = type("_RouterAlias", (), {})()
misc_actions.router = router
