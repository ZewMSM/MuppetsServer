import json
import logging
from pathlib import Path

from database import IslandDB
from database.base_adapter import BaseAdapter, _session_ctx, register_adapter
from ZewSFS.Types import Int, SFSArray, SFSObject

logger = logging.getLogger(__name__)

_CONTENT_ROOT = Path(__file__).resolve().parent.parent / "content" / "base_game_data"
_ISLAND_JSON_PATH = _CONTENT_ROOT / "island_data.json"


@register_adapter(IslandDB)
class Island(BaseAdapter):
    _db_model = IslandDB
    _game_id_key = "island_id"
    _specific_sfs_datatypes = {"id": Int}

    island_id: int = 0
    cost_coins: int = 0
    cost_diamonds: int = 0
    level: int = 0
    description: str = ""
    fb_object_id: str = ""
    genes: str = ""
    min_server_version: str = ""
    name: str = ""
    status: str = ""
    midi: str = ""
    graphic: str = "{}"
    monsters: str = "[]"
    structures: str = "[]"
    levels: str = "[]"

    @classmethod
    async def _ensure_loaded(cls):
        async with _session_ctx() as session:
            from sqlalchemy import select

            result = await session.execute(select(IslandDB).limit(1))
            if result.scalar_one_or_none() is not None:
                return
        await cls.import_from_json(_ISLAND_JSON_PATH)

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
            logger.warning("Island JSON not found: %s", path)
            return
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        items = data.get("islands_data", [])
        db_rows = []
        for record in items:
            island_id = record.get("island_id")
            if island_id is None:
                continue
            inst = cls()
            inst.id = island_id
            inst.island_id = island_id
            inst.cost_coins = record.get("cost_coins", 0)
            inst.cost_diamonds = record.get("cost_diamonds", 0)
            inst.level = record.get("level", 0)
            inst.description = str(record.get("description", "") or "")
            inst.fb_object_id = str(record.get("fb_object_id", "") or "")
            inst.genes = str(record.get("genes", "") or "")
            inst.min_server_version = str(record.get("min_server_version", "") or "")
            inst.name = str(record.get("name", "") or "")
            inst.status = str(record.get("status", "") or "")
            inst.midi = str(record.get("midi", "") or "")
            inst.graphic = (
                json.dumps(record.get("graphic", {}))
                if isinstance(record.get("graphic"), dict)
                else (record.get("graphic") or "{}")
            )
            inst.monsters = (
                json.dumps(record.get("monsters", []))
                if isinstance(record.get("monsters"), list)
                else (record.get("monsters") or "[]")
            )
            inst.structures = (
                json.dumps(record.get("structures", []))
                if isinstance(record.get("structures"), list)
                else (record.get("structures") or "[]")
            )
            beds = record.get("beds") or {}
            levels_arr = beds.get("levels", []) if isinstance(beds, dict) else []
            inst.levels = (
                json.dumps(levels_arr) if isinstance(levels_arr, list) else "[]"
            )
            db_rows.append(
                IslandDB(
                    id=inst.id,
                    island_id=inst.island_id,
                    cost_coins=inst.cost_coins,
                    cost_diamonds=inst.cost_diamonds,
                    level=inst.level,
                    description=inst.description,
                    fb_object_id=inst.fb_object_id,
                    genes=inst.genes,
                    min_server_version=inst.min_server_version,
                    name=inst.name,
                    status=inst.status,
                    midi=inst.midi,
                    graphic=inst.graphic,
                    monsters=inst.monsters,
                    structures=inst.structures,
                    levels=inst.levels,
                )
            )
        async with _session_ctx() as session:
            for row in db_rows:
                session.add(row)
            await session.commit()
        logger.info("Loaded %d islands from %s", len(items), path)

    async def update_sfs(self, params: SFSObject):
        params.putInt("island_id", self.id)
        params.putSFSObject("graphic", SFSObject.from_json(self.graphic))
        params.putSFSArray("monsters", SFSArray.from_json(self.monsters))
        params.putSFSArray("structures", SFSArray.from_json(self.structures))
        params.remove_item(
            "levels"
        )  # base adds "levels" string; legacy has only beds.levels
        params.remove_item("date_created")  # legacy static island does not send this
        beds = SFSObject()
        beds.putSFSArray("levels", SFSArray.from_json(self.levels))
        params.putSFSObject("beds", beds)
        params.putLong("last_changed", 0)
        return params

    def load_monsters(self):
        """Yield monster entries from island JSON (e.g. {'monster': 50, 'instrument': '...'})."""
        try:
            arr = (
                json.loads(self.monsters)
                if isinstance(self.monsters, str)
                else self.monsters
            )
            for item in arr or []:
                yield item
        except (json.JSONDecodeError, TypeError):
            pass
