import json

from ZewSFS.Types import Int, SFSObject, SFSArray
from database import StructureDB
from database.base_adapter import BaseAdapter


class Structure(BaseAdapter):
    _db_model = StructureDB
    _game_id_key = 'structure_id'
    _specific_sfs_datatypes = {'id': Int}

    allowed_on_island: str = ''
    battle_level: int = 0
    build_time: int = 0
    cost_coins: int = 0
    cost_diamonds: int = 0
    cost_eth_currency: int = 0
    cost_keys: int = 0
    cost_medals: int = 0
    cost_relics: int = 0
    cost_sale: int = 0
    cost_starpower: int = 0
    description: str = ''
    entity_id: int = 0
    entity_type: str = 'structure'
    extra: str = ''
    graphic: str = ''
    last_changed: int = 0
    level: int = 0
    min_server_version: str = ''
    movable: bool = True
    name: str = ''
    platforms: str = ''
    premium: bool = False
    requirements: str = ''
    sellable: bool = True
    show_in_levelup: bool = True
    size_x: int = 1
    size_y: int = 1
    sound: str = ''
    structure_type: str = ''
    upgrades_to: int = 0
    view_in_market: bool = True
    view_in_starmarket: bool = False
    xp: int = 0
    y_offset: int = 100

    extra_params: dict = None

    async def on_sfs_load_complete(self):
        self.requirements = []  # int(h.get('entity')) for h in json.loads(self.requirements) # TODO: Fix

    async def on_load_complete(self):
        try:
            self.extra_params = json.loads(self.extra)
        except:
            self.extra_params = {}

    async def update_sfs(self, params: SFSObject):
        params.putSFSArray('requirements', SFSArray())  # TODO: Fix
        params.putSFSObject('graphic', SFSObject.from_json(self.graphic))
        params.putSFSObject('extra', SFSObject.from_json(self.extra))
        return params
