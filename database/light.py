import json
import logging
from pathlib import Path

# localmodules:start
from ZewSFS.Types import Int, SFSObject
from database import LightDB, _CONTENT_ROOT
from database.base_adapter import BaseAdapter, _session_ctx, register_adapter
# localmodules:end

logger = logging.getLogger(__name__)

_LIGHTING_JSON_PATH = _CONTENT_ROOT / "lighting_data.json"


@register_adapter(LightDB)
class Light(BaseAdapter):
    _db_model = LightDB
    _game_id_key = "lighting_id"
    _specific_sfs_datatypes = {"id": Int}

    lighting_id: int = 0
    cost_coins: int = 0
    cost_diamonds: int = 0
    initial: int = 0
    island_id: int = 0
    level: int = 0
    view_in_market: int = 0
    graphic: str = "{}"
    name: str = ""
    description: str = ""

    @classmethod
    async def _ensure_loaded(cls):
        async with _session_ctx() as session:
            from sqlalchemy import select

            result = await session.execute(select(LightDB).limit(1))
            if result.scalar_one_or_none() is not None:
                return
        await cls.import_from_json(_LIGHTING_JSON_PATH)

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
            logger.warning("Lighting JSON not found: %s", path)
            return
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        items = data.get("lighting_data", [])
        db_rows = []
        for record in items:
            lighting_id = record.get("lighting_id", 0)
            inst = cls()
            inst.id = lighting_id
            inst.lighting_id = lighting_id
            inst.cost_coins = record.get("cost_coins", 0)
            inst.cost_diamonds = record.get("cost_diamonds", 0)
            inst.initial = record.get("initial", 0)
            inst.island_id = record.get("island_id", 0)
            inst.level = record.get("level", 0)
            inst.view_in_market = record.get("view_in_market", 0)
            inst.graphic = (
                json.dumps(record.get("graphic", {}))
                if isinstance(record.get("graphic"), dict)
                else (record.get("graphic") or "{}")
            )
            inst.name = str(record.get("name", "") or "")
            inst.description = str(record.get("description", "") or "")
            db_rows.append(
                LightDB(
                    id=inst.id,
                    lighting_id=inst.lighting_id,
                    cost_coins=inst.cost_coins,
                    cost_diamonds=inst.cost_diamonds,
                    initial=inst.initial,
                    island_id=inst.island_id,
                    level=inst.level,
                    view_in_market=inst.view_in_market,
                    graphic=inst.graphic,
                    name=inst.name,
                    description=inst.description,
                )
            )
        async with _session_ctx() as session:
            for row in db_rows:
                session.add(row)
            await session.commit()
        logger.info("Loaded %d lights from %s", len(items), path)

    async def update_sfs(self, params: SFSObject):
        params.remove_item("date_created")
        params.putInt("lighting_id", self.id)
        params.putSFSObject("graphic", SFSObject.from_json(self.graphic))
        return params
