import json
import logging
from pathlib import Path
from typing import Optional

# localmodules:start
from ZewSFS.Types import Int
from database import BreedingCombinationDB, _CONTENT_ROOT
from database.base_adapter import BaseAdapter, _session_ctx, register_adapter
# localmodules:end

logger = logging.getLogger(__name__)

_BREEDING_JSON_PATH = _CONTENT_ROOT / "breeding_data.json"


@register_adapter(BreedingCombinationDB)
class BreedingCombination(BaseAdapter):
    _db_model = BreedingCombinationDB
    _game_id_key = "breeding_combination_id"
    _specific_sfs_datatypes = {"id": Int}

    breeding_combination_id: int = 0
    monster_1: int = 0
    monster_2: int = 0
    result: int = 0
    probability: int = 0
    modifier: float = 1.0

    @classmethod
    async def _ensure_loaded(cls):
        async with _session_ctx() as session:
            from sqlalchemy import select

            result = await session.execute(select(BreedingCombinationDB).limit(1))
            if result.scalar_one_or_none() is not None:
                return
        await cls.import_from_json(_BREEDING_JSON_PATH)

    @classmethod
    async def load_all(cls, use_cache: bool = False):
        await cls._ensure_loaded()
        return await super().load_all(use_cache=use_cache)

    @classmethod
    async def load_by_id(cls, id: int, use_cache: bool = True):
        await cls._ensure_loaded()
        return await super().load_by_id(id, use_cache=use_cache)

    @classmethod
    async def get_by_monsters(
        cls, monster_1: int, monster_2: int
    ) -> Optional["BreedingCombination"]:
        """Find combo by (monster_1, monster_2) or (monster_2, monster_1)."""
        await cls._ensure_loaded()
        all_combos = await cls.load_all(use_cache=True)
        for combo in all_combos:
            if (combo.monster_1 == monster_1 and combo.monster_2 == monster_2) or (
                combo.monster_1 == monster_2 and combo.monster_2 == monster_1
            ):
                return combo
        return None

    @classmethod
    async def import_from_json(cls, path: Path):
        if not path.exists():
            logger.warning("Breeding JSON not found: %s", path)
            return
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        items = data.get("breedingcombo_data", [])
        db_rows = []
        for record in items:
            combo_id = record.get("breeding_combination_id")
            if combo_id is None:
                continue
            inst = cls()
            inst.id = combo_id
            inst.breeding_combination_id = combo_id
            inst.monster_1 = record.get("monster_1", 0)
            inst.monster_2 = record.get("monster_2", 0)
            inst.result = record.get("result", 0)
            inst.probability = record.get("probability", 0)
            inst.modifier = float(record.get("modifier", 1.0))
            db_rows.append(
                BreedingCombinationDB(
                    id=inst.id,
                    breeding_combination_id=inst.breeding_combination_id,
                    monster_1=inst.monster_1,
                    monster_2=inst.monster_2,
                    result=inst.result,
                    probability=inst.probability,
                    modifier=inst.modifier,
                )
            )
        async with _session_ctx() as session:
            for row in db_rows:
                session.add(row)
            await session.commit()
        logger.info("Loaded %d breeding combinations from %s", len(items), path)

    async def update_sfs(self, params):
        params.remove_item("date_created")
        params.remove_item("modifier")
        return params
