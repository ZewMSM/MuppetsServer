import json
import logging
from pathlib import Path
from types import SimpleNamespace

from database import MonsterDB
from database.base_adapter import BaseAdapter, _session_ctx, register_adapter
from ZewSFS.Types import Int, SFSArray, SFSObject

logger = logging.getLogger(__name__)

_CONTENT_ROOT = Path(__file__).resolve().parent.parent / "content" / "base_game_data"
_MONSTER_JSON_PATH = _CONTENT_ROOT / "monster_data.json"


@register_adapter(MonsterDB)
class Monster(BaseAdapter):
    _db_model = MonsterDB
    _game_id_key = "monster_id"
    _specific_sfs_datatypes = {"id": Int}

    beds: int = 0
    build_time: int = 0
    cost_coins: int = 0
    cost_diamonds: int = 0
    entity_id: int = 0
    hide_friends: int = 0
    level: int = 0
    movable: int = 0
    size_x: int = 0
    size_y: int = 0
    sticker_offset: int = 0
    tier: int = 0
    view_in_market: int = 0
    xp: int = 0
    y_offset: int = 0

    description: str = ""
    entity_type: str = ""
    fb_object_id: str = ""
    genes: str = ""
    hatch_sound: str = ""
    min_server_version: str = ""
    name: str = ""

    graphic: str = "{}"
    happiness: str = "[]"
    levels: str = "[]"
    requirements: str = "[]"

    @property
    def levels_list(self):
        """Parsed levels for game logic (food, coins, max_coins per level)."""
        try:
            raw = (
                json.loads(self.levels) if isinstance(self.levels, str) else self.levels
            )
            return [SimpleNamespace(**lev) for lev in raw]
        except (json.JSONDecodeError, TypeError):
            return []

    @classmethod
    async def _ensure_loaded(cls):
        async with _session_ctx() as session:
            from sqlalchemy import select

            result = await session.execute(select(MonsterDB).limit(1))
            if result.scalar_one_or_none() is not None:
                return
        await cls.import_from_json(_MONSTER_JSON_PATH)

    @classmethod
    async def load_all(cls, use_cache: bool = False):
        await cls._ensure_loaded()
        return await super().load_all(use_cache=use_cache)

    @classmethod
    async def load_by_id(cls, id: int, use_cache: bool = True):
        await cls._ensure_loaded()
        return await super().load_by_id(id, use_cache=use_cache)

    @classmethod
    async def import_from_json(cls, path: Path):
        if not path.exists():
            logger.warning("Monster JSON not found: %s", path)
            return
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        items = data.get("monsters_data", [])
        db_rows = []
        for record in items:
            monster_id = record.get("monster_id") or record.get("entity_id")
            if monster_id is None:
                continue
            inst = cls()
            inst.id = monster_id
            inst.beds = record.get("beds", 0)
            inst.build_time = record.get("build_time", 0)
            inst.cost_coins = record.get("cost_coins", 0)
            inst.cost_diamonds = record.get("cost_diamonds", 0)
            inst.entity_id = record.get("entity_id", 0)
            inst.hide_friends = record.get("hide_friends", record.get("hide_friend", 0))
            inst.level = record.get("level", 0)
            inst.movable = record.get("movable", 0)
            inst.size_x = record.get("size_x", 0)
            inst.size_y = record.get("size_y", 0)
            inst.sticker_offset = record.get("sticker_offset", 0)
            inst.tier = record.get("tier", 0)
            inst.view_in_market = record.get("view_in_market", 0)
            inst.xp = record.get("xp", 0)
            inst.y_offset = record.get("y_offset", 0)
            inst.description = record.get("description", "") or ""
            inst.entity_type = record.get("entity_type", "") or ""
            inst.fb_object_id = record.get("fb_object_id", "") or ""
            inst.genes = record.get("genes", "") or ""
            inst.hatch_sound = record.get("hatch_sound", "") or ""
            inst.min_server_version = record.get("min_server_version", "") or ""
            inst.name = record.get("name", "") or ""
            inst.graphic = (
                json.dumps(record.get("graphic", {}))
                if isinstance(record.get("graphic"), dict)
                else (record.get("graphic") or "{}")
            )
            inst.happiness = (
                json.dumps(record.get("happiness", []))
                if isinstance(record.get("happiness"), list)
                else (record.get("happiness") or "[]")
            )
            levels_raw = record.get("levels", [])
            if isinstance(levels_raw, list):
                levels_clean = [
                    {k: v for k, v in item.items() if k != "last_changed"}
                    for item in levels_raw
                    if isinstance(item, dict)
                ]
                inst.levels = json.dumps(levels_clean)
            else:
                inst.levels = levels_raw or "[]"
            inst.requirements = (
                json.dumps(record.get("requirements", []))
                if isinstance(record.get("requirements"), list)
                else (record.get("requirements") or "[]")
            )
            db_rows.append(
                MonsterDB(
                    id=inst.id,
                    beds=inst.beds,
                    build_time=inst.build_time,
                    cost_coins=inst.cost_coins,
                    cost_diamonds=inst.cost_diamonds,
                    entity_id=inst.entity_id,
                    hide_friends=inst.hide_friends,
                    level=inst.level,
                    movable=inst.movable,
                    size_x=inst.size_x,
                    size_y=inst.size_y,
                    sticker_offset=inst.sticker_offset,
                    tier=inst.tier,
                    view_in_market=inst.view_in_market,
                    xp=inst.xp,
                    y_offset=inst.y_offset,
                    description=inst.description,
                    entity_type=inst.entity_type,
                    fb_object_id=inst.fb_object_id,
                    genes=inst.genes,
                    hatch_sound=inst.hatch_sound,
                    min_server_version=inst.min_server_version,
                    name=inst.name,
                    graphic=inst.graphic,
                    happiness=inst.happiness,
                    levels=inst.levels,
                    requirements=inst.requirements,
                )
            )
        async with _session_ctx() as session:
            for row in db_rows:
                session.add(row)
            await session.commit()
        logger.info("Loaded %d monsters from %s", len(items), path)

    async def update_sfs(self, params: SFSObject) -> SFSObject:
        params.remove_item("date_created")
        params.putSFSObject("graphic", SFSObject.from_json(self.graphic))
        params.putSFSArray("happiness", SFSArray.from_json(self.happiness))
        params.putSFSArray("levels", SFSArray.from_json(self.levels))
        params.putSFSArray("requirements", SFSArray.from_json(self.requirements))
        params.putLong("last_changed", 0)
        return params
