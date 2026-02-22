from datetime import datetime

from sqlalchemy import (
    BIGINT,
    JSON,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(AsyncAttrs, DeclarativeBase):
    id = Column(
        BIGINT(), primary_key=True, unique=True, nullable=False, autoincrement=True
    )

    date_created = Column(
        BIGINT, nullable=False, default=lambda: int(datetime.now().timestamp() * 1000)
    )


# --- Static (legacy) ---


class StructureDB(Base):
    __tablename__ = "structures"

    name = Column(String, nullable=False, default="")
    description = Column(String, nullable=True, default="")
    entity_id = Column(Integer, nullable=False, default=0)
    entity_type = Column(String, nullable=False, default="structure")
    structure_type = Column(String, nullable=False, default="")
    level = Column(Integer, nullable=False, default=0)
    upgrades_to = Column(Integer, ForeignKey("structures.id"), nullable=True)
    upgrades_to_structure = relationship(
        "StructureDB", uselist=False, remote_side="StructureDB.id"
    )

    y_offset = Column(Integer, nullable=False, default=0)
    sticker_offset = Column(Integer, nullable=False, default=0)

    cost_coins = Column(Integer, nullable=False, default=0)
    cost_diamonds = Column(Integer, nullable=False, default=0)

    build_time = Column(Integer, nullable=False, default=0)

    movable = Column(Integer, nullable=False, default=0)
    view_in_market = Column(Integer, nullable=False, default=0)
    min_server_version = Column(String, nullable=False, default="")

    xp = Column(Integer, nullable=False, default=0)

    size_x = Column(Integer, nullable=False, default=0)
    size_y = Column(Integer, nullable=False, default=0)

    extra = Column(String, nullable=False, default="")
    requirements = Column(JSON, nullable=False, default=list)
    graphic = Column(String, nullable=False, default="")


class MonsterDB(Base):
    __tablename__ = "monsters"

    beds = Column(Integer, nullable=False, default=0)
    build_time = Column(Integer, nullable=False, default=0)
    cost_coins = Column(Integer, nullable=False, default=0)
    cost_diamonds = Column(Integer, nullable=False, default=0)
    entity_id = Column(Integer, nullable=False, default=0)
    hide_friends = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=0)
    movable = Column(Integer, nullable=False, default=0)
    size_x = Column(Integer, nullable=False, default=0)
    size_y = Column(Integer, nullable=False, default=0)
    sticker_offset = Column(Integer, nullable=False, default=0)
    tier = Column(Integer, nullable=False, default=0)
    view_in_market = Column(Integer, nullable=False, default=0)
    xp = Column(Integer, nullable=False, default=0)
    y_offset = Column(Integer, nullable=False, default=0)

    description = Column(String, nullable=False, default="")
    entity_type = Column(String, nullable=False, default="")
    fb_object_id = Column(String, nullable=False, default="")
    genes = Column(String, nullable=False, default="")
    hatch_sound = Column(String, nullable=False, default="")
    min_server_version = Column(String, nullable=False, default="")
    name = Column(String, nullable=False, default="")

    graphic = Column(String, nullable=False, default="{}")
    happiness = Column(String, nullable=False, default="[]")
    levels = Column(String, nullable=False, default="[]")
    requirements = Column(String, nullable=False, default="[]")


class IslandDB(Base):
    __tablename__ = "islands"

    island_id = Column(Integer, nullable=False, default=0)
    cost_coins = Column(Integer, nullable=False, default=0)
    cost_diamonds = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=0)
    description = Column(String, nullable=False, default="")
    fb_object_id = Column(String, nullable=False, default="")
    genes = Column(String, nullable=False, default="")
    min_server_version = Column(String, nullable=False, default="")
    name = Column(String, nullable=False, default="")
    status = Column(String, nullable=False, default="")
    midi = Column(String, nullable=False, default="")

    graphic = Column(Text, nullable=False, default="{}")
    monsters = Column(Text, nullable=False, default="[]")
    structures = Column(Text, nullable=False, default="[]")
    levels = Column(Text, nullable=False, default="[]")


class LevelDB(Base):
    __tablename__ = "levels"

    level = Column(Integer, nullable=False, default=0)
    xp = Column(Integer, nullable=False, default=0)
    coins_conversion = Column(Integer, nullable=False, default=0)
    diamonds_conversion = Column(Integer, nullable=False, default=0)
    diamond_reward = Column(Integer, nullable=False, default=0)
    max_bakeries = Column(Integer, nullable=False, default=0)
    daily_rewards = Column(Text, nullable=False, default="[]")


class BackdropDB(Base):
    __tablename__ = "backdrops"

    backdrop_id = Column(Integer, nullable=False, default=0)
    cost_coins = Column(Integer, nullable=False, default=0)
    cost_diamonds = Column(Integer, nullable=False, default=0)
    initial = Column(Integer, nullable=False, default=0)
    island_id = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=0)
    view_in_market = Column(Integer, nullable=False, default=0)
    graphic = Column(Text, nullable=False, default="{}")
    name = Column(String, nullable=False, default="")
    description = Column(String, nullable=False, default="")


class LightDB(Base):
    __tablename__ = "lights"

    lighting_id = Column(Integer, nullable=False, default=0)
    cost_coins = Column(Integer, nullable=False, default=0)
    cost_diamonds = Column(Integer, nullable=False, default=0)
    initial = Column(Integer, nullable=False, default=0)
    island_id = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=0)
    view_in_market = Column(Integer, nullable=False, default=0)
    graphic = Column(Text, nullable=False, default="{}")
    name = Column(String, nullable=False, default="")
    description = Column(String, nullable=False, default="")


class BreedingCombinationDB(Base):
    __tablename__ = "breeding_combinations"

    breeding_combination_id = Column(Integer, nullable=False, default=0)
    monster_1 = Column(Integer, nullable=False, default=0)
    monster_2 = Column(Integer, nullable=False, default=0)
    result = Column(Integer, nullable=False, default=0)
    probability = Column(Integer, nullable=False, default=0)
    modifier = Column(Float, nullable=False, default=1.0)


# --- Player (runtime) ---


class PlayerDB(Base):
    __tablename__ = "players"

    display_name = Column(String, nullable=False, default="New Player")
    coins = Column(BIGINT, nullable=False, default=0)
    diamonds = Column(BIGINT, nullable=False, default=0)
    food = Column(BIGINT, nullable=False, default=0)
    xp = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=1)
    daily_reward_level = Column(Integer, nullable=False, default=0)
    last_collection = Column(BIGINT, nullable=True, default=0)
    active_island = Column(BIGINT, nullable=True, default=None)
    backdrops = Column(Text, nullable=False, default="[]")
    lighting = Column(Text, nullable=False, default="[]")


class PlayerIslandDB(Base):
    __tablename__ = "player_islands"

    user_id = Column(BIGINT, ForeignKey("players.id"), nullable=False)
    island_id = Column(Integer, nullable=False, default=0)
    upgrading_until = Column(BIGINT, nullable=True, default=None)
    upgrade_started = Column(BIGINT, nullable=True, default=None)
    likes = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=1)
    backdrop_id = Column(Integer, nullable=False, default=0)
    lighting_id = Column(Integer, nullable=False, default=0)
    beds = Column(Text, nullable=False, default="[4,0]")


class PlayerStructureDB(Base):
    __tablename__ = "player_structures"

    date_created = Column(BIGINT, nullable=True, default=None)
    user_island_id = Column(BIGINT, ForeignKey("player_islands.id"), nullable=False)
    structure_id = Column(Integer, nullable=False, default=0)
    pos_x = Column(Integer, nullable=False, default=0)
    pos_y = Column(Integer, nullable=False, default=0)
    flip = Column(Integer, nullable=False, default=0)
    muted = Column(Integer, nullable=False, default=0)
    is_complete = Column(Integer, nullable=False, default=0)
    is_upgrading = Column(Integer, nullable=False, default=0)
    scale = Column(Float, nullable=False, default=1.0)
    building_completed = Column(BIGINT, nullable=True, default=None)
    last_collection = Column(BIGINT, nullable=True, default=None)
    obj_data = Column(Integer, nullable=True, default=None)
    obj_end = Column(BIGINT, nullable=True, default=None)


class PlayerMonsterDB(Base):
    __tablename__ = "player_monsters"

    user_island_id = Column(BIGINT, ForeignKey("player_islands.id"), nullable=False)
    monster_id = Column(Integer, nullable=False, default=0)
    pos_x = Column(Integer, nullable=False, default=0)
    pos_y = Column(Integer, nullable=False, default=0)
    flip = Column(Integer, nullable=False, default=0)
    muted = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=1)
    happiness = Column(Integer, nullable=False, default=0)
    collected_coins = Column(Integer, nullable=False, default=0)
    times_fed = Column(Integer, nullable=False, default=0)
    volume = Column(Float, nullable=False, default=1.0)
    last_collection = Column(BIGINT, nullable=True, default=None)
