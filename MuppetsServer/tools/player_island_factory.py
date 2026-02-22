"""
Fill island structures to match legacy MSM-Hacks-Muppets PlayerIsland.fillIsland().
Reference: https://github.com/MSM-Hacks/MSM-Hacks-Muppets/blob/master/src/main/java/ru/msmhacks/muppets/entities/Player/PlayerIsland.java
"""

import random

from database.player import PlayerStructure, PlayerIsland


def _rand_flip() -> int:
    return random.randint(0, 1)


def _pick(obj_ids: list[int]) -> int:
    return random.choice(obj_ids) if obj_ids else 0


# Legacy fillIsland() data: places_3, places_2, places_1 (x,y), objects_3/2/1 (structure ids), nursery [x,y], castle [structure_id, x, y]
ISLAND_1 = {
    "places_3": [(35, 27), (31, 27), (39, 22), (39, 19), (45, 16), (34, 4), (34, 10), (31, 10), (28, 10)],
    "places_2": [(41, 11), (38, 24), (45, 13), (40, 15), (38, 13), (38, 9), (32, 4), (25, 11), (22, 15), (26, 25)],
    "places_1": [(33, 24), (37, 22), (38, 22), (36, 28), (33, 28), (46, 17), (41, 9), (38, 11), (40, 13), (38, 15), (39, 16), (36, 11), (37, 7), (37, 4), (34, 1), (28, 7), (22, 12), (27, 11), (30, 11), (25, 14), (27, 8), (26, 9), (36, 7), (28, 17), (35, 19), (42, 21)],
    "objects_3": [200, 206, 199, 203, 204, 205],
    "objects_2": [202],
    "objects_1": [205, 201],
    "nursery": (10, 20),
    "castle": (208, 33, 34),
}

ISLAND_2 = {
    "places_3": [(45, 17), (32, 5), (27, 2)],
    "places_2": [(46, 20), (36, 6), (25, 8), (30, 2), (41, 24), (43, 13), (32, 2), (40, 9), (30, 9)],
    "places_1": [(36, 12), (41, 22), (44, 23), (49, 19), (48, 17), (46, 23), (45, 13), (38, 18), (39, 24), (30, 5), (38, 6), (26, 4), (25, 3), (26, 5), (27, 8), (42, 9), (42, 11), (44, 16), (24, 9), (39, 7)],
    "objects_3": [198, 255, 197, 252, 253],
    "objects_2": [251],
    "objects_1": [254, 250],
    "nursery": (10, 10),
    "castle": (213, 49, 23),
}

ISLAND_3 = {
    "places_3": [],
    "places_2": [],
    "places_1": [],
    "objects_3": [188, 195, 189, 192, 193, 196],
    "objects_2": [191],
    "objects_1": [194, 190],
    "nursery": (17, 13),
    "castle": (218, 48, 28),
}

ISLAND_4 = {
    "places_3": [],
    "places_2": [],
    "places_1": [],
    "objects_3": [351, 352, 353, 355, 356],
    "objects_2": [354],
    "objects_1": [350],
    "nursery": (25, 7),
    "castle": (259, 23, 26),
}

ISLAND_5 = {
    "places_3": [],
    "places_2": [],
    "places_1": [],
    "objects_3": [359, 360, 362, 363],
    "objects_2": [361],
    "objects_1": [357, 358],
    "nursery": (41, 26),
    "castle": (266, 40, 39),
}

ISLAND_DATA = {1: ISLAND_1, 2: ISLAND_2, 3: ISLAND_3, 4: ISLAND_4, 5: ISLAND_5}


async def _create_obstacle(user_island_id: int, structure_id: int, pos_x: int, pos_y: int) -> PlayerStructure:
    return await PlayerStructure.create_new_structure(
        user_island_id,
        structure_id,
        pos_x,
        pos_y,
        completed=True,
        flip=_rand_flip(),
        scale=1.0,
        set_timestamps=False,
    )


async def create_initial_structures(player_island: PlayerIsland) -> None:
    """
    Fill island with obstacles, nursery and castle as in legacy PlayerIsland.fillIsland().
    Only islands 1–5 are supported (main game islands).
    """
    island_id = getattr(player_island, "island_id", None) or getattr(player_island, "island", None)
    data = ISLAND_DATA.get(island_id) if island_id else None
    if not data:
        return

    uid = player_island.id
    nx, ny = data["nursery"]
    cid, cx, cy = data["castle"]

    for (x, y) in data["places_3"]:
        await _create_obstacle(uid, _pick(data["objects_3"]), x, y)
    for (x, y) in data["places_2"]:
        await _create_obstacle(uid, _pick(data["objects_2"]), x, y)
    for (x, y) in data["places_1"]:
        await _create_obstacle(uid, _pick(data["objects_1"]), x, y)

    await PlayerStructure.create_new_structure(uid, 1, nx, ny, completed=True)
    await PlayerStructure.create_new_structure(uid, cid, cx, cy, completed=True)
    await player_island.on_load_complete()


class PlayerIslandFactory:
    """Legacy-compatible island fill. Delegates to create_initial_structures()."""

    @staticmethod
    async def create_initial_structures(player_island: PlayerIsland) -> None:
        await create_initial_structures(player_island)
