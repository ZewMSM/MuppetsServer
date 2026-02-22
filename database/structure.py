import json
import logging
from pathlib import Path

# localmodules:start
from database import StructureDB, _CONTENT_ROOT
from database.base_adapter import BaseAdapter, _session_ctx, register_adapter
from ZewSFS.Types import Int, SFSArray, SFSObject
# localmodules:end

logger = logging.getLogger(__name__)

_STRUCTURE_JSON_PATH = _CONTENT_ROOT / "structure_data.json"


@register_adapter(StructureDB)
class Structure(BaseAdapter):
    _db_model = StructureDB
    _game_id_key = "structure_id"
    _specific_sfs_datatypes = {"id": Int}

    build_time: int = 0
    cost_coins: int = 0
    cost_diamonds: int = 0
    description: str = ""
    entity_id: int = 0
    entity_type: str = "structure"
    extra: str = ""
    graphic: str = ""
    level: int = 0
    min_server_version: str = ""
    movable: int = 0
    name: str = ""
    requirements: str = "[]"
    size_x: int = 1
    size_y: int = 1
    sticker_offset: int = 0
    structure_type: str = ""
    upgrades_to: int = 0
    view_in_market: int = 0
    xp: int = 0
    y_offset: int = 100

    extra_params: dict = None

    async def on_load_complete(self):
        try:
            self.extra_params = json.loads(self.extra) if self.extra else {}
        except (json.JSONDecodeError, TypeError):
            self.extra_params = {}

    @classmethod
    async def _ensure_loaded(cls):
        async with _session_ctx() as session:
            from sqlalchemy import select

            result = await session.execute(select(StructureDB).limit(1))
            if result.scalar_one_or_none() is not None:
                return
        await cls.import_from_json(_STRUCTURE_JSON_PATH)

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
            logger.warning("Structure JSON not found: %s", path)
            return
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        items = data.get("structures_data", [])
        db_rows = []
        for record in items:
            structure_id = record.get("structure_id") or record.get("entity_id")
            if structure_id is None:
                continue
            inst = cls()
            inst.id = structure_id
            inst.build_time = record.get("build_time", 0)
            inst.cost_coins = record.get("cost_coins", 0)
            inst.cost_diamonds = record.get("cost_diamonds", 0)
            inst.description = str(record.get("description", "") or "")
            inst.entity_id = record.get("entity_id", 0)
            inst.entity_type = str(
                record.get("entity_type", "structure") or "structure"
            )
            inst.extra = (
                json.dumps(record.get("extra", {}))
                if isinstance(record.get("extra"), dict)
                else (record.get("extra") or "{}")
            )
            inst.graphic = (
                json.dumps(record.get("graphic", {}))
                if isinstance(record.get("graphic"), dict)
                else (record.get("graphic") or "{}")
            )
            inst.level = record.get("level", 0)
            inst.min_server_version = str(record.get("min_server_version", "") or "")
            inst.movable = record.get("movable", 0)
            inst.name = str(record.get("name", "") or "")
            inst.requirements = (
                json.dumps(record.get("requirements", []))
                if isinstance(record.get("requirements"), list)
                else (record.get("requirements") or "[]")
            )
            inst.size_x = record.get("size_x", 0)
            inst.size_y = record.get("size_y", 0)
            inst.sticker_offset = record.get("sticker_offset", 0)
            inst.structure_type = str(record.get("structure_type", "") or "")
            inst.upgrades_to = record.get("upgrades_to", 0) or 0
            inst.view_in_market = record.get("view_in_market", 0)
            inst.xp = record.get("xp", 0)
            inst.y_offset = record.get("y_offset", 0)
            db_rows.append(
                StructureDB(
                    id=inst.id,
                    name=inst.name,
                    description=inst.description,
                    entity_id=inst.entity_id,
                    entity_type=inst.entity_type,
                    structure_type=inst.structure_type,
                    level=inst.level,
                    upgrades_to=inst.upgrades_to if inst.upgrades_to else None,
                    y_offset=inst.y_offset,
                    sticker_offset=inst.sticker_offset,
                    cost_coins=inst.cost_coins,
                    cost_diamonds=inst.cost_diamonds,
                    build_time=inst.build_time,
                    movable=inst.movable,
                    view_in_market=inst.view_in_market,
                    min_server_version=inst.min_server_version,
                    xp=inst.xp,
                    size_x=inst.size_x,
                    size_y=inst.size_y,
                    extra=inst.extra,
                    requirements=json.loads(inst.requirements)
                    if isinstance(inst.requirements, str)
                    else inst.requirements,
                    graphic=inst.graphic,
                )
            )
        async with _session_ctx() as session:
            for row in db_rows:
                session.add(row)
            await session.commit()
        logger.info("Loaded %d structures from %s", len(items), path)

    async def update_sfs(self, params: SFSObject):
        params.remove_item("date_created")
        params.putInt("structure_id", self.id)
        params.putSFSArray(
            "requirements",
            SFSArray.from_json(self.requirements)
            if isinstance(self.requirements, str)
            else SFSArray.from_python_object(self.requirements),
        )
        params.putSFSObject(
            "graphic",
            SFSObject.from_json(self.graphic)
            if isinstance(self.graphic, str)
            else SFSObject.from_python_object(self.graphic),
        )
        params.putSFSObject(
            "extra",
            SFSObject.from_json(self.extra)
            if isinstance(self.extra, str)
            else SFSObject.from_python_object(self.extra),
        )
        params.putLong("last_changed", 0)
        return params
