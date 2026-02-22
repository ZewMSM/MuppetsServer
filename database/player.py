import json
import logging
import time
from typing import List, Optional

from database import PlayerDB, PlayerIslandDB, PlayerMonsterDB, PlayerStructureDB
from database.base_adapter import BaseAdapter
from database.island import Island
from database.level import Level
from database.monster import Monster
from database.structure import Structure
from ZewSFS.Types import Double, Long, SFSArray, SFSObject

logger = logging.getLogger("GameServer/Player")


class Player(BaseAdapter):
    _db_model = PlayerDB
    _game_id_key = "bbb_id"
    _specific_sfs_datatypes = {"active_island": Long, "last_collection": Long}

    display_name: str = "New Player"
    coins: int = 5000
    diamonds: int = 20
    food: int = 2500
    xp: int = 655
    level: int = 5
    daily_reward_level: int = 1
    last_collection: int = 0
    active_island: int = -1
    backdrops: str = "[]"
    lighting: str = "[]"

    islands: List["PlayerIsland"] = []

    async def update_sfs(self, params: SFSObject):
        params.putInt("bbb_id", self.id)
        params.putInt("user_id", self.id)
        params.putLong("last_collection", self.last_collection or 0)
        params.putLong("active_island", self.active_island or -1)
        params.putSFSArray("backdrops", SFSArray.from_json(self.backdrops))
        params.putSFSArray("lighting", SFSArray.from_json(self.lighting))
        params.putSFSArray("hidden_objects", SFSArray())
        islands = SFSArray()
        for island in self.islands:
            islands.addSFSObject(await island.to_sfs_object())
        params.putSFSArray("islands", islands)
        return params

    async def on_load_complete(self):
        self.islands = await PlayerIsland.load_all_by(user_id=self.id)
        if len(self.islands) == 0:
            self.islands.append(await PlayerIsland.create_new_island(self.id, 1))
        if self.get_island(self.active_island) is None:
            self.active_island = self.islands[0].id if self.islands else -1

    async def create_new_player(self):
        logger.info("Creating new player(bbb_id=%s)", self.id)
        player_island = await PlayerIsland.create_new_island(self.id, 1)
        self.islands = [player_island]
        self.active_island = player_island.id

    async def check_prices(
        self,
        coins: int = None,
        diamonds: int = None,
        food: int = None,
        obj: Optional[Island | Monster | Structure] = None,
        check_all: bool = False,
        charge_if_can: bool = True,
    ):
        if obj is not None:
            if coins is None:
                coins = getattr(obj, "cost_coins", 0)
            if diamonds is None:
                diamonds = getattr(obj, "cost_diamonds", 0)
            if food is None:
                food = getattr(obj, "cost_food", 0) if hasattr(obj, "cost_food") else 0
        coins = coins or 0
        diamonds = diamonds or 0
        food = food or 0
        checks = {
            "coins": (self.coins, coins),
            "diamonds": (self.diamonds, diamonds),
            "food": (self.food, food),
        }
        if check_all:
            for curr, (have, need) in checks.items():
                if have < need:
                    return False
            if charge_if_can:
                self.coins -= coins
                self.diamonds -= diamonds
                self.food -= food
                await self.save()
        else:
            for curr, (have, need) in checks.items():
                if need > 0 and have < need:
                    return False
            if charge_if_can and (coins or diamonds or food):
                self.coins -= coins
                self.diamonds -= diamonds
                self.food -= food
                await self.save()
        return True

    @property
    def get_active_island(self) -> Optional["PlayerIsland"]:
        for island in self.islands:
            if island.id == self.active_island:
                return island
        return None

    def get_island(self, user_island_id) -> Optional["PlayerIsland"]:
        for island in self.islands:
            if island.id == user_island_id:
                return island
        return None

    def get_island_by_id(self, island_id: int) -> Optional["PlayerIsland"]:
        for island in self.islands:
            if island.island_id == island_id:
                return island
        return None

    async def add_currency(self, currency: str, amount: int):
        amount = int(amount)
        if currency == "coins":
            self.coins += amount
        elif currency == "diamonds":
            self.diamonds += amount
        elif currency == "food":
            self.food += amount
        elif currency == "xp":
            self.xp += amount
            all_levels = await Level.load_all()
            max_level_data = None
            for lvl in all_levels:
                if self.xp > lvl.xp:
                    if max_level_data is None or lvl.level > max_level_data.level:
                        max_level_data = lvl
            if max_level_data and max_level_data.level > self.level:
                self.diamonds += max_level_data.diamond_reward
                self.level = max_level_data.level
        else:
            raise ValueError("Unknown currency: %s" % currency)
        await self.save()

    def get_properties(self) -> SFSArray:
        props = SFSArray()
        props.addSFSObject(SFSObject().putInt("coins", self.coins))
        props.addSFSObject(SFSObject().putInt("diamonds", self.diamonds))
        props.addSFSObject(SFSObject().putInt("food", self.food))
        props.addSFSObject(SFSObject().putInt("xp", self.xp))
        props.addSFSObject(SFSObject().putInt("level", self.level))
        return props

    async def redeem_daily_reward(self) -> bool:
        """If 24h passed since last_collection, grant daily reward and return True."""
        now_ms = int(time.time() * 1000)
        if now_ms <= (self.last_collection or 0) + 86400000:
            return False
        self.last_collection = now_ms
        await self.save()
        level_data = await Level.load_by_id(self.level)
        if not level_data or not level_data.daily_rewards:
            return True
        try:
            rewards = json.loads(level_data.daily_rewards)
        except (json.JSONDecodeError, TypeError):
            return True
        idx = (self.daily_reward_level or 1) - 1
        if idx < 0 or idx >= len(rewards):
            idx = 0
        r = rewards[idx]
        coins_reward = int(r.get("coins", 0))
        diamonds_reward = int(r.get("diamonds", 0))
        diamonds_reward += len(self.islands)
        await self.add_currency("coins", coins_reward)
        await self.add_currency("diamonds", diamonds_reward)
        self.daily_reward_level = (idx + 2) if (idx + 1) < 5 else 1
        await self.save()
        return True


class PlayerIsland(BaseAdapter):
    _db_model = PlayerIslandDB
    _game_id_key = "user_island_id"
    _specific_sfs_datatypes = {"user_id": Long}

    user_id: int = None
    island_id: int = 0
    upgrading_until: int = None
    upgrade_started: int = None  # Legacy: island upgrade timer (not structure upgrade)
    likes: int = 0
    level: int = 1
    backdrop_id: int = 0
    lighting_id: int = 0
    beds: str = "[4,0]"

    island: Optional[Island] = None
    structures: List["PlayerStructure"] = []
    monsters: List["PlayerMonster"] = []

    async def on_load_complete(self):
        self.island = await Island.load_by_id(int(self.island_id))
        self.structures = await PlayerStructure.load_all_by(user_island_id=self.id)
        self.monsters = await PlayerMonster.load_all_by(user_island_id=self.id)

    def _eggs(self) -> List["PlayerStructure"]:
        return [
            s
            for s in self.structures
            if s.obj_data is not None and s.obj_end is not None
        ]

    async def update_sfs(self, params: SFSObject):
        params.putLong("user", self.user_id)
        params.putInt("island", self.island_id)
        if self.upgrading_until is not None:
            params.putLong("upgrading_until", self.upgrading_until)
        if self.upgrade_started is not None:
            params.putLong("upgrade_started", self.upgrade_started)
        params.putInt("level", self.level)
        params.putInt("backdrop_id", self.backdrop_id)
        params.putInt("lighting_id", self.lighting_id)
        params.putInt("likes", self.likes)
        structures = SFSArray()
        for s in self.structures:
            structures.addSFSObject(await s.to_sfs_object())
        params.putSFSArray("structures", structures)
        monsters = SFSArray()
        for m in self.monsters:
            monsters.addSFSObject(await m.to_sfs_object())
        params.putSFSArray("monsters", monsters)
        return params

    @staticmethod
    async def create_new_island(user_id: int, island_id: int) -> "PlayerIsland":
        self = PlayerIsland()
        self.user_id = user_id
        self.island_id = island_id
        await self.save()
        await self.on_load_complete()
        logger.info(
            "Created new island(island_id=%s) for player(bbb_id=%s)",
            self.island_id,
            self.user_id,
        )
        from MuppetsServer.tools.player_island_factory import PlayerIslandFactory

        await PlayerIslandFactory.create_initial_structures(self)
        return self

    def get_structure(self, user_structure_id: int) -> Optional["PlayerStructure"]:
        for s in self.structures:
            if s.id == user_structure_id:
                return s
        return None

    def get_structures_by_type(self, structure_type: str):
        for s in self.structures:
            if (
                s.structure
                and s.structure.structure_type.lower() == structure_type.lower()
            ):
                yield s

    def get_egg(self, user_structure_id: int) -> Optional["PlayerStructure"]:
        s = self.get_structure(user_structure_id)
        if s and s.obj_data is not None and s.obj_end is not None:
            return s
        return None

    def get_monster(self, user_monster_id: int) -> Optional["PlayerMonster"]:
        for m in self.monsters:
            if m.id == user_monster_id:
                return m
        return None

    def has_structure_type_id(self, structure_id: int) -> bool:
        """Legacy: check if island already has a structure with this structure_id."""
        return any(s.structure_id == structure_id for s in self.structures)

    def get_structure_by_structure_id(self, structure_id: int) -> Optional["PlayerStructure"]:
        """Legacy: getStructureOnIslandByStructureType — первая структура с данным structure_id."""
        for s in self.structures:
            if s.structure_id == structure_id:
                return s
        return None


class PlayerStructure(BaseAdapter):
    _db_model = PlayerStructureDB
    _game_id_key = "user_structure_id"
    _specific_sfs_datatypes = {"user_island_id": Long, "obj_end": Long}

    user_island_id: int = None
    structure_id: int = 0
    pos_x: int = 0
    pos_y: int = 0
    flip: int = 0
    muted: int = 0
    is_complete: int = 0   # Legacy: 1 when built/upgraded, 0 while building/upgrading
    is_upgrading: int = 0  # Legacy: structure upgrade state; upgrade_started is on island
    scale: float = 1.0
    building_completed: int = None
    last_collection: int = None
    obj_data: int = None
    obj_end: int = None

    structure: Optional[Structure] = None

    async def on_load_complete(self):
        self.structure = await Structure.load_by_id(int(self.structure_id))

    async def get_island(self) -> "PlayerIsland":
        return await PlayerIsland.load_by_id(int(self.user_island_id))

    def is_egg(self) -> bool:
        return self.obj_data is not None and self.obj_end is not None

    async def update_sfs(self, params: SFSObject):
        params.putLong("user_island_id", self.user_island_id)
        params.putInt("structure", self.structure_id)
        params.putInt("pos_x", self.pos_x)
        params.putInt("pos_y", self.pos_y)
        params.putInt("flip", self.flip)
        params.putInt("muted", self.muted)
        params.putInt("is_complete", self.is_complete)
        params.putInt("is_upgrading", self.is_upgrading)
        params.putFloat("scale", self.scale)
        if self.date_created is not None:
            params.putLong("date_created", self.date_created)
        if self.building_completed is not None:
            params.putLong("building_completed", self.building_completed)
        if self.last_collection is not None:
            params.putLong("last_collection", self.last_collection)
        if self.obj_data is not None:
            params.putInt("obj_data", self.obj_data)
        if self.obj_end is not None:
            params.putLong("obj_end", self.obj_end)
        return params

    @staticmethod
    async def create_new_structure(
        user_island_id: int,
        structure_id: int,
        pos_x: int,
        pos_y: int,
        completed: bool,
        flip: int = 0,
        scale: float = 1.0,
        set_timestamps: bool = True,
    ) -> "PlayerStructure":
        self = PlayerStructure()
        self.user_island_id = user_island_id
        self.structure_id = structure_id
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.flip = flip
        self.scale = scale
        self.is_complete = 1 if completed else 0
        self.is_upgrading = 0
        t = int(time.time() * 1000)
        self.date_created = t  # NOT NULL в БД — всегда заполняем
        if set_timestamps:
            if completed:
                self.building_completed = t
                self.last_collection = t
        else:
            self.building_completed = None
            self.last_collection = None
        await self.save()
        await self.on_load_complete()
        logger.info(
            "Created new structure(structure_id=%s) for island(user_island_id=%s)",
            self.structure_id,
            self.user_island_id,
        )
        return self

    @staticmethod
    async def create_egg(
        user_island_id: int,
        structure_id: int,
        monster_id: int,
        completion_time_ms: int,
    ) -> "PlayerStructure":
        async with PlayerStructure() as self:
            self.user_island_id = user_island_id
            self.structure_id = structure_id
            self.obj_data = monster_id
            self.obj_end = completion_time_ms
            self.is_complete = 0
            self.is_upgrading = 0
            self.pos_x = 0
            self.pos_y = 0
            self.date_created = int(time.time() * 1000)
        await self.on_load_complete()
        await self.save()
        logger.info(
            "Created egg(monster_id=%s) in structure for island(user_island_id=%s)",
            monster_id,
            user_island_id,
        )
        return self


class PlayerMonster(BaseAdapter):
    _db_model = PlayerMonsterDB
    _game_id_key = "user_monster_id"
    _specific_sfs_datatypes = {
        "user_island_id": Long,
        "last_collection": Long,
        "volume": Double,
    }

    user_island_id: int = None
    monster_id: int = 0
    pos_x: int = 0
    pos_y: int = 0
    flip: int = 0
    muted: int = 0
    level: int = 1
    happiness: int = 0
    collected_coins: int = 0
    times_fed: int = 0
    volume: float = 1.0
    last_collection: int = None

    monster: Optional[Monster] = None

    async def on_load_complete(self):
        self.monster = await Monster.load_by_id(int(self.monster_id))

    async def get_island(self) -> "PlayerIsland":
        return await PlayerIsland.load_by_id(int(self.user_island_id))

    async def update_sfs(self, params: SFSObject):
        params.putLong("user_island_id", self.user_island_id)
        params.putInt("monster", self.monster_id)
        params.putInt("pos_x", self.pos_x)
        params.putInt("pos_y", self.pos_y)
        params.putInt("flip", self.flip)
        params.putInt("muted", self.muted)
        params.putInt("level", self.level)
        params.putInt("happiness", self.happiness)
        params.putInt("collected_coins", self.collected_coins)
        params.putInt("times_fed", self.times_fed)
        params.putFloat("volume", self.volume)
        if self.date_created is not None:
            params.putLong("date_created", self.date_created)
        if self.last_collection is not None:
            params.putLong("last_collection", self.last_collection)
        return params

    @staticmethod
    async def create_new_monster(island_id: int, monster_id: int) -> "PlayerMonster":
        self = PlayerMonster()
        self.user_island_id = island_id
        self.monster_id = monster_id
        now_ms = int(time.time() * 1000)
        self.date_created = now_ms
        self.last_collection = now_ms
        await self.on_load_complete()
        await self.save()
        logger.info(
            "Created new monster(monster_id=%s) for island(user_island_id=%s)",
            monster_id,
            island_id,
        )
        return self
