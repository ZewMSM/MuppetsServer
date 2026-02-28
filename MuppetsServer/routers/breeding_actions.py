"""Breeding: gs_breed_monsters, gs_speed_up_breeding, gs_finish_breeding."""

import random
import time

# localmodules:start
from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject
from database.breeding import BreedingCombination
from database.monster import Monster
from MuppetsServer.tools.utils import calculate_probability_for_breeding
# localmodules:end

router = SFSRouter()

BREEDING_STRUCTURE_ID = 2
NURSERY_STRUCTURE_ID_PRIMARY = 1
NURSERY_STRUCTURE_ID_FALLBACK = 324


def _speedup_cost_diamonds(now_ms: int, end_ms: int) -> int:
    if now_ms >= end_ms:
        return 0
    return round((end_ms - now_ms) / 1_800_000) + 1


@router.on_request("gs_breed_monsters")
async def breed_monsters(client: SFSServerClient, params: SFSObject):
    user_monster_id_1 = int(params.get("user_monster_id_1", 0))
    user_monster_id_2 = int(params.get("user_monster_id_2", 0))
    island = client.player.get_active_island
    if not island:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    plm1 = island.get_monster(user_monster_id_1)
    plm2 = island.get_monster(user_monster_id_2)
    if not plm1 or not plm2 or plm1.level < 4 or plm2.level < 4:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    breeding_struct = island.get_structure_by_structure_id(BREEDING_STRUCTURE_ID)
    if not breeding_struct or breeding_struct.obj_data is not None or breeding_struct.obj_end is not None:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    combo = await BreedingCombination.get_by_monsters(plm1.monster_id, plm2.monster_id)
    if combo:
        breed_prob = calculate_probability_for_breeding(
            plm1.level, plm2.level, combo.probability, combo.modifier
        )
        result_monster = await Monster.load_by_id(combo.result)
        if (
            random.randint(1, 100) < breed_prob
            or (result_monster and result_monster.level <= client.player.level)
        ):
            result_monster_id = combo.result
        else:
            first_prob = int((plm1.level / (plm1.level + plm2.level)) * 100)
            result_monster_id = (
                plm1.monster_id
                if random.randint(1, 100) < first_prob
                else plm2.monster_id
            )
    else:
        first_prob = int((plm1.level / (plm1.level + plm2.level)) * 100)
        result_monster_id = (
            plm1.monster_id
            if random.randint(1, 100) < first_prob
            else plm2.monster_id
        )

    breed_monster = await Monster.load_by_id(result_monster_id)
    if not breed_monster:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    now_ms = int(time.time() * 1000)
    completion_time_ms = now_ms + breed_monster.build_time * 1000
    breeding_struct.obj_data = result_monster_id
    breeding_struct.obj_end = completion_time_ms
    await breeding_struct.save()

    user_breeding = (
        SFSObject()
        .putInt("obj_data", result_monster_id)
        .putLong("obj_end", completion_time_ms)
    )
    return (
        SFSObject()
        .putSFSObject("user_breeding", user_breeding)
        .putSFSArray("properties", client.player.get_properties())
        .putBool("success", True)
        .putBool("remove_buyback", False)
    )


@router.on_request("gs_speed_up_breeding")
async def speed_up_breeding(client: SFSServerClient, params: SFSObject):
    user_structure_id = int(params.get("user_structure_id", 0))
    island = client.player.get_active_island
    if not island:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    if user_structure_id == 0:
        breeding_struct = island.get_structure_by_structure_id(BREEDING_STRUCTURE_ID)
    else:
        breeding_struct = island.get_structure(user_structure_id)

    if not breeding_struct or breeding_struct.obj_data is None or breeding_struct.obj_end is None:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    now_ms = int(time.time() * 1000)
    cost = _speedup_cost_diamonds(now_ms, breeding_struct.obj_end or 0)
    if cost <= 0:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    if not await client.player.check_prices(diamonds=cost, charge_if_can=True):
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    breeding_struct.obj_end = now_ms + 1500
    await breeding_struct.save()

    response = SFSObject().putBool("success", True)
    response.putSFSObject(
        "user_breeding",
        SFSObject()
        .putLong("obj_end", breeding_struct.obj_end)
        .putInt("obj_data", breeding_struct.obj_data),
    )
    response.putSFSArray("properties", client.player.get_properties())
    return response


@router.on_request("gs_finish_breeding")
async def finish_breeding(client: SFSServerClient, params: SFSObject):
    user_structure_id = int(params.get("user_structure_id", 0))
    island = client.player.get_active_island
    if not island:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    if user_structure_id == 0:
        breeding_struct = island.get_structure_by_structure_id(BREEDING_STRUCTURE_ID)
    else:
        breeding_struct = island.get_structure(user_structure_id)

    if not breeding_struct or breeding_struct.obj_data is None or breeding_struct.obj_end is None:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    now_ms = int(time.time() * 1000)
    if now_ms < (breeding_struct.obj_end or 0):
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    monster_id = breeding_struct.obj_data
    breeding_struct.obj_data = None
    breeding_struct.obj_end = None
    await breeding_struct.save()

    nursery = island.get_structure_by_structure_id(NURSERY_STRUCTURE_ID_PRIMARY)
    if nursery is None:
        nursery = island.get_structure_by_structure_id(NURSERY_STRUCTURE_ID_FALLBACK)
    if nursery is None:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    monster = await Monster.load_by_id(monster_id)
    if not monster:
        return SFSObject().putBool("success", False).putUtfString("message", "Error")

    if nursery.structure_id == NURSERY_STRUCTURE_ID_FALLBACK:
        hatching_time_ms = monster.build_time * 750
    else:
        hatching_time_ms = monster.build_time * 1000
    end_ms = now_ms + hatching_time_ms

    nursery.obj_data = monster_id
    nursery.obj_end = end_ms
    await nursery.save()

    user_egg = SFSObject().putInt("obj_data", monster_id).putLong("obj_end", end_ms)
    return (
        SFSObject()
        .putBool("success", True)
        .putLong("user_structure_id", breeding_struct.id)
        .putSFSObject("user_egg", user_egg)
        .putSFSArray("properties", client.player.get_properties())
    )
