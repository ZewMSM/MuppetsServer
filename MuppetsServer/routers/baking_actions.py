import time

from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject

router = SFSRouter()

# Legacy Utils.getFoodData(food_index) returns [foodCost, foodCount, foodTime].
# In Player.java startBaking the variable names are swapped: foodCost=data[1], foodCount=data[0].
# Actual charge = data[1] = foodCount. Reward = data[1] = foodCount.
FOOD_DATA = {
    0: (50, 5, 30),
    1: (250, 25, 300),
    2: (1000, 100, 1800),
    3: (5000, 500, 3600),
    4: (15000, 1500, 10800),
    5: (75000, 7500, 21600),
    6: (500000, 50000, 43200),
    7: (1000000, 100000, 86400),
    8: (5000000, 500000, 172800),
}


def _get_food_data(food_index: int) -> tuple[int, int, int]:
    """Returns (coin_cost_charged, food_count, time_secs).
    Legacy charges foodCount (index[1]) as coin cost, not foodCost (index[0])."""
    data = FOOD_DATA.get(food_index, (0, 0, 0))
    food_count = data[1]
    time_secs = data[2]
    return food_count, food_count, time_secs


def _speedup_cost_diamonds(now_ms: int, end_ms: int) -> int:
    if now_ms >= end_ms:
        return 0
    return round((end_ms - now_ms) / 1_800_000) + 1


@router.on_request("gs_start_baking")
async def start_baking(client: SFSServerClient, params: SFSObject):
    user_structure_id = params.get("user_structure_id")
    food_index = int(params.get("food_index", 0))

    island = client.player.get_active_island
    if not island:
        return "No active island."
    user_structure = island.get_structure(user_structure_id)
    if user_structure is None:
        return "Invalid structure ID."

    coin_cost, food_count, time_secs = _get_food_data(food_index)
    if coin_cost <= 0 and food_count <= 0:
        return "Invalid food index."

    if not await client.player.check_prices(coins=coin_cost, charge_if_can=True):
        return "Not enough coins to start baking."

    now_ms = int(time.time() * 1000)
    obj_end = now_ms + time_secs * 1000
    user_structure.obj_data = food_index
    user_structure.obj_end = obj_end
    await user_structure.save()

    user_baking = SFSObject()
    user_baking.putLong("user_structure_id", user_structure_id)
    user_baking.putInt("obj_data", food_index)
    user_baking.putLong("obj_end", obj_end)
    response = SFSObject().putBool("success", True)
    response.putSFSArray("properties", client.player.get_properties())
    response.putSFSObject("user_baking", user_baking)
    await client.send_extension("gs_start_baking", response)
    return response


@router.on_request("gs_speed_up_baking")
async def speed_up_baking(client: SFSServerClient, params: SFSObject):
    user_structure_id = params.get("user_structure_id")

    island = client.player.get_active_island
    if not island:
        return "No active island."
    user_structure = island.get_structure(user_structure_id)
    if user_structure is None or user_structure.obj_data is None:
        return "Invalid structure or no baking in progress."

    now_ms = int(time.time() * 1000)
    cost = _speedup_cost_diamonds(now_ms, user_structure.obj_end or 0)
    if cost <= 0:
        return "Nothing to speed up."
    if not await client.player.check_prices(diamonds=cost, charge_if_can=True):
        return "Not enough diamonds."

    user_structure.obj_end = now_ms + 1500
    await user_structure.save()

    response = SFSObject().putBool("success", True)
    response.putSFSArray("properties", client.player.get_properties())
    response.putLong("user_structure_id", user_structure_id)
    response.putLong("obj_end", user_structure.obj_end)
    await client.send_extension("gs_speed_up_baking", response)
    return response


@router.on_request("gs_finish_baking")
async def finish_baking(client: SFSServerClient, params: SFSObject):
    user_structure_id = params.get("user_structure_id")

    island = client.player.get_active_island
    if not island:
        return "No active island."
    user_structure = island.get_structure(user_structure_id)
    if user_structure is None or user_structure.obj_data is None:
        return "Invalid structure or no baking in progress."

    now_ms = int(time.time() * 1000)
    if (user_structure.obj_end or 0) > now_ms:
        return "Baking not ready yet."

    _, food_count, _ = _get_food_data(user_structure.obj_data)
    await client.player.add_currency("food", food_count)
    await client.player.add_currency("xp", food_count)
    user_structure.obj_data = None
    user_structure.obj_end = None
    await user_structure.save()

    response = SFSObject().putBool("success", True)
    response.putSFSArray("properties", client.player.get_properties())
    response.putLong("user_structure_id", user_structure_id)
    await client.send_extension("gs_finish_baking", response)
    return response
