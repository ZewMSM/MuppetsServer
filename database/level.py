import json
import logging
from pathlib import Path

# localmodules:start
from ZewSFS.Types import Int, SFSObject, SFSArray
from database import LevelDB, _CONTENT_ROOT
from database.base_adapter import BaseAdapter, _session_ctx, register_adapter
# localmodules:end

logger = logging.getLogger(__name__)

_LEVEL_JSON_PATH = _CONTENT_ROOT / "level_data.json"


@register_adapter(LevelDB)
class Level(BaseAdapter):
    _db_model = LevelDB
    _game_id_key = "level"
    _specific_sfs_datatypes = {"id": Int}

    level: int = 0
    xp: int = 0
    coins_conversion: int = 0
    diamonds_conversion: int = 0
    diamond_reward: int = 0
    max_bakeries: int = 0
    daily_rewards: str = "[]"

    @classmethod
    async def _ensure_loaded(cls):
        async with _session_ctx() as session:
            from sqlalchemy import select

            result = await session.execute(select(LevelDB).limit(1))
            if result.scalar_one_or_none() is not None:
                return
        await cls.import_from_json(_LEVEL_JSON_PATH)

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
            logger.warning("Level JSON not found: %s", path)
            return
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        items = data.get("level_data", [])
        db_rows = []
        for record in items:
            level_num = record.get("level")
            if level_num is None:
                continue
            inst = cls()
            inst.id = level_num
            inst.level = level_num
            inst.xp = record.get("xp", 0)
            cc = record.get("currency_conversion") or {}
            if isinstance(cc, dict):
                inst.coins_conversion = cc.get("coins", 0)
                inst.diamonds_conversion = cc.get("diamonds", 0)
            else:
                inst.coins_conversion = 0
                inst.diamonds_conversion = 0
            inst.diamond_reward = record.get("diamond_reward", 0)
            inst.max_bakeries = record.get("max_bakeries", 0)
            inst.daily_rewards = (
                json.dumps(record.get("daily_rewards", []))
                if isinstance(record.get("daily_rewards"), list)
                else (record.get("daily_rewards") or "[]")
            )
            db_rows.append(
                LevelDB(
                    id=inst.id,
                    level=inst.level,
                    xp=inst.xp,
                    coins_conversion=inst.coins_conversion,
                    diamonds_conversion=inst.diamonds_conversion,
                    diamond_reward=inst.diamond_reward,
                    max_bakeries=inst.max_bakeries,
                    daily_rewards=inst.daily_rewards,
                )
            )
        async with _session_ctx() as session:
            for row in db_rows:
                session.add(row)
            await session.commit()
        logger.info("Loaded %d levels from %s", len(items), path)

    async def update_sfs(self, params: SFSObject):
        params.remove_item("date_created")
        params.remove_item("coins_conversion")
        params.remove_item("diamonds_conversion")
        currency_conversion = SFSObject()
        currency_conversion.putInt("coins", self.coins_conversion)
        currency_conversion.putInt("diamonds", self.diamonds_conversion)
        params.putSFSObject("currency_conversion", currency_conversion)
        params.putSFSArray("daily_rewards", SFSArray.from_json(self.daily_rewards))
        return params
