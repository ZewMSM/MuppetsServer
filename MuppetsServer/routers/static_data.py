import time

# localmodules:start
from database.backdrop import Backdrop
from database.breeding import BreedingCombination
from database.island import Island
from database.level import Level
from database.light import Light
from database.monster import Monster
from database.structure import Structure
from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSArray, SFSObject
# localmodules:end

router = SFSRouter(cached=True)


@router.on_request("db_level")
async def send_level_data(client: SFSServerClient, request: SFSObject):
    levels_data = SFSArray()
    for level in await Level.load_all():
        levels_data.addSFSObject(await level.to_sfs_object())
    return (
        SFSObject()
        .putSFSArray("levels_data", levels_data)
        .putLong("server_time", round(time.time() * 1000))
    )


@router.on_request("db_monster")
async def send_monster_data(client: SFSServerClient, request: SFSObject):
    monsters_data = SFSArray()
    for monster in await Monster.load_all():
        monsters_data.addSFSObject(await monster.to_sfs_object())
    return (
        SFSObject()
        .putSFSArray("monsters_data", monsters_data)
        .putLong("server_time", round(time.time() * 1000))
    )


@router.on_request("db_structure")
async def send_structure_data(client: SFSServerClient, request: SFSObject):
    structures_data = SFSArray()
    for structure in await Structure.load_all():
        structures_data.addSFSObject(await structure.to_sfs_object())
    return (
        SFSObject()
        .putSFSArray("structures_data", structures_data)
        .putLong("server_time", round(time.time() * 1000))
    )


@router.on_request("db_island")
async def send_island_data(client: SFSServerClient, request: SFSObject):
    islands_data = SFSArray()
    for island in await Island.load_all():
        islands_data.addSFSObject(await island.to_sfs_object())
    return (
        SFSObject()
        .putSFSArray("islands_data", islands_data)
        .putLong("server_time", round(time.time() * 1000))
    )


@router.on_request("db_backdrop")
@router.on_request("db_backdrops")
async def send_backdrop_data(client: SFSServerClient, request: SFSObject):
    backdrop_data = SFSArray()
    for backdrop in await Backdrop.load_all():
        backdrop_data.addSFSObject(await backdrop.to_sfs_object())
    return (
        SFSObject()
        .putSFSArray("backdrop_data", backdrop_data)
        .putLong("server_time", round(time.time() * 1000))
    )


@router.on_request("db_lighting")
async def send_lighting_data(client: SFSServerClient, request: SFSObject):
    lighting_data = SFSArray()
    for light in await Light.load_all():
        lighting_data.addSFSObject(await light.to_sfs_object())
    return (
        SFSObject()
        .putSFSArray("lighting_data", lighting_data)
        .putLong("server_time", round(time.time() * 1000))
    )


@router.on_request("db_breeding")
async def send_breeding_data(client: SFSServerClient, request: SFSObject):
    breeding_data = SFSArray()
    for combo in await BreedingCombination.load_all():
        breeding_data.addSFSObject(await combo.to_sfs_object())
    return (
        SFSObject()
        .putSFSArray("breedingcombo_data", breeding_data)
        .putLong("server_time", round(time.time() * 1000))
    )


@router.on_request("db_store")
async def send_store_data(client: SFSServerClient, request: SFSObject):
    return (
        SFSObject()
        .putSFSArray("store_item_data", SFSArray())
        .putSFSArray("store_group_data", SFSArray())
        .putSFSArray("store_currency_data", SFSArray())
        .putLong("server_time", round(time.time() * 1000))
    )


@router.on_request("gs_quest")
async def send_quests(client: SFSServerClient, request: SFSObject):
    return (
        SFSObject()
        .putSFSArray("result", SFSArray())
        .putLong("server_time", int(time.time() * 1000))
    )

# Алиас для сборки в один файл (muppets_server использует static_data.router)
static_data = type("_RouterAlias", (), {})()
static_data.router = router
