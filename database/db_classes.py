from datetime import datetime

from sqlalchemy import *
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship


###################### -------    BASE    ------- ######################


class Base(AsyncAttrs, DeclarativeBase):
    id = Column(BIGINT(), primary_key=True, unique=True, nullable=False)

    last_changed = Column(BIGINT, nullable=True, default=datetime.now().timestamp() * 1000)
    date_created = Column(BIGINT, nullable=False, default=datetime.now().timestamp() * 1000)


@event.listens_for(Base, 'before_update')
def receive_before_update(mapper, connection, target):
    target.changed_at = datetime.now()


###################### -------    STRUCTURES    ------- ######################


class StructureDB(Base):
    __tablename__ = 'structures'

    # Basic Information
    name = Column(String, nullable=False, default="")
    description = Column(String, nullable=True, default="")
    entity_id = Column(Integer, nullable=False, default=0)
    entity_type = Column(String, nullable=False, default="structure")
    structure_type = Column(String, nullable=False, default="")
    level = Column(Integer, nullable=False, default=0)
    upgrades_to = Column(Integer, ForeignKey('structures.id'), nullable=True) # 0 if None
    upgrades_to_structure = relationship('StructureDB', uselist=False)

    # Visual and Sound
    y_offset = Column(Integer, nullable=False, default=0)
    sticker_offset = Column(Integer, nullable=False, default=0)  # Added based on MSM Hacks Muppets
    sound = Column(String, nullable=False, default="")

    # Cost Information
    cost_coins = Column(Integer, nullable=False, default=0)
    cost_diamonds = Column(Integer, nullable=False, default=0)
    premium = Column(Boolean, nullable=False, default=False)

    # Build Information
    build_time = Column(Integer, nullable=False, default=0)

    # Requirements and Restrictions
    movable = Column(Boolean, nullable=False, default=False)  # Converted to Boolean
    view_in_market = Column(Boolean, nullable=False, default=False)  # Converted to Boolean
    min_server_version = Column(String, nullable=False, default="")
    
    # Experience Information
    xp = Column(Integer, nullable=False, default=0)

    # Size Information
    size_x = Column(Integer, nullable=False, default=0)
    size_y = Column(Integer, nullable=False, default=0)

    # Miscellaneous
    extra = Column(String, nullable=False, default="")
    last_changed = Column(BIGINT, nullable=True, default=0)

    # Miscellaneous
    requirements = Column(ARRAY(Integer), nullable=False, default=[])
    graphic = Column(String, nullable=False, default="")
    extra = Column(String, nullable=False, default="")


###################### -------    ISLANDS    ------- ######################
class IslandDB(Base):
    __tablename__ = 'islands'

    # Basic information
    name = Column(String, nullable=False, default="")
    short_name = Column(String, nullable=False, default="")
    description = Column(String, nullable=True, default="")
    first_time_visit_desc = Column(String, nullable=True, default="")
    first_time_visit_menu = Column(String, nullable=True, default="")

    # Costs
    cost_coins = Column(Integer, nullable=False, default=0)
    cost_keys = Column(Integer, nullable=False, default=0)
    cost_relics = Column(Integer, nullable=False, default=0)
    cost_diamonds = Column(Integer, nullable=False, default=0)
    cost_starpower = Column(Integer, nullable=False, default=0)
    cost_medals = Column(Integer, nullable=False, default=0)
    cost_eth_currency = Column(Integer, nullable=False, default=0)

    # Requirements and settings
    min_level = Column(Integer, nullable=False, default=1)
    min_server_version = Column(String, nullable=False, default="1.0")
    enabled = Column(Boolean, nullable=False, default=True)
    island_type = Column(Integer, nullable=False, default=0)
    island_lock = Column(Integer, nullable=None, default=None)
    has_nursery_scratch = Column(Boolean, nullable=False, default=True)
    has_book = Column(Boolean, nullable=False, default=True)

    # Graphics and audio
    graphic = Column(String, nullable=False, default="")
    iconSheet = Column(String, nullable=False, default="island_buttons02.xml")
    iconSprite = Column(String, nullable=False, default="")
    torch_graphic = Column(String, nullable=False, default="tiki_plant01")
    midi = Column(String, nullable=False, default="world01.mid")
    ambient_track = Column(String, nullable=False, default="audio/sfx/world_01_ambience")

    # Structures
    castle_structure_id = Column(Integer, nullable=False, default=0)
    grid = Column(String, nullable=False, default="")


class IslandStructureDB(Base):
    __tablename__ = 'island_structures'

    island_id = Column(Integer, nullable=False)
    structure = Column(Integer, nullable=False)
    instrument = Column(String, nullable=False, default="")


class IslandMonsterDB(Base):
    __tablename__ = 'island_monsters'

    island_id = Column(Integer, nullable=False)
    monster = Column(Integer, nullable=False)
    bom = Column(Boolean, nullable=False, default=False)
    book_y = Column(Integer, nullable=False, default=0)
    book_x = Column(Integer, nullable=False, default=0)
    instrument = Column(String, nullable=False, default="")
    book_flip = Column(Boolean, nullable=False, default=False)
    book_z = Column(Integer, nullable=False, default=0)


class IslandThemeDataDB(Base):
    __tablename__ = 'island_theme_data'

    # Identification
    name = Column(String, nullable=False, default="")
    theme_id = Column(Integer, nullable=False, default=0)
    island = Column(Integer, nullable=False, default=0)
    storeitem_id = Column(Integer, nullable=False, default=0)

    # Costs
    cost_coins = Column(Integer, nullable=False, default=0)
    cost_keys = Column(Integer, nullable=False, default=0)
    cost_diamonds = Column(Integer, nullable=False, default=0)
    cost_starpower = Column(Integer, nullable=False, default=0)
    cost_eth_currency = Column(Integer, nullable=False, default=0)
    cost_relics = Column(Integer, nullable=False, default=0)

    # Availability
    level = Column(Integer, nullable=False, default=0)
    view_in_market = Column(Integer, nullable=False, default=0)
    unlocked_entities = Column(String, nullable=True, default=None)

    # Descriptions
    description = Column(String, nullable=True, default=None)
    modifier_description = Column(String, nullable=True, default=None)

    # Modifiers
    modifiers = Column(String, nullable=True, default=None)

    # Content
    trees = Column(String, nullable=True, default=None)
    rocks = Column(String, nullable=True, default=None)

    # Placement and Graphics
    placement_id = Column(String, nullable=False, default="")
    graphic = Column(String, nullable=False, default="")

    # Event Information
    season_event_name = Column(String, nullable=True)
    month_string = Column(String, nullable=True)

    # Versioning
    version = Column(String, nullable=False, default="")


###################### -------    MONSTERS    ------- ######################

class MonsterDB(Base):
    __tablename__ = 'monsters'

    # Identifiers
    entity_id = Column(Integer, nullable=False, default=0)
    entity_type = Column(String, nullable=False, default="monster")
    name = Column(String, nullable=False, default="")
    common_name = Column(String, nullable=True, default="")
    class_name = Column(String, nullable=False, default="")
    genes = Column(String, nullable=False, default="")
    description = Column(String, nullable=True, default="")

    # Cost attributes
    cost_diamonds = Column(Integer, nullable=False, default=0)
    cost_coins = Column(Integer, nullable=False, default=0)
    cost_keys = Column(Integer, nullable=False, default=0)
    cost_sale = Column(Integer, nullable=False, default=0)
    cost_starpower = Column(Integer, nullable=False, default=0)
    cost_medals = Column(Integer, nullable=False, default=0)
    cost_relics = Column(Integer, nullable=False, default=0)
    cost_eth_currency = Column(Integer, nullable=False, default=0)

    # View and market attributes
    view_in_market = Column(Boolean, nullable=False, default=True)
    view_in_starmarket = Column(Boolean, nullable=False, default=False)
    premium = Column(Boolean, nullable=False, default=True)
    box_monster = Column(Boolean, nullable=False, default=False)
    movable = Column(Boolean, nullable=False, default=True)

    # Requirements and attributes
    requirements = Column(ARRAY(Integer), nullable=True, default="")
    happiness = Column(ARRAY(Integer), nullable=True, default=None)
    min_level = Column(Integer, nullable=False, default=1)
    levelup_island = Column(String, nullable=False, default="none")

    # Graphics and sounds
    graphic = Column(String, nullable=False, default="")
    portrait_graphic = Column(String, nullable=True, default="")
    spore_graphic = Column(String, nullable=False, default="")
    select_sound = Column(String, nullable=False, default="Q01-Memory")

    # Size and position
    size_x = Column(Integer, nullable=False, default=1)
    size_y = Column(Integer, nullable=False, default=1)
    y_offset = Column(Integer, nullable=False, default=100)

    # Build and time attributes
    build_time = Column(Integer, nullable=False, default=0)
    beds = Column(Integer, nullable=False, default=0)
    xp = Column(Integer, nullable=False, default=0)
    time_to_fill_sec = Column(Integer, nullable=False, default=-1)

    # Miscellaneous
    keywords = Column(String, nullable=True, default="")
    min_server_version = Column(String, nullable=False, default="1.0")


class MonsterLevelDB(Base):
    __tablename__ = 'monster_levels'

    monster_id = Column(Integer, nullable=False)
    level = Column(Integer, nullable=False, default=1)
    coins = Column(Integer, nullable=False, default=0)
    max_coins = Column(Integer, nullable=False, default=0)
    food = Column(Integer, nullable=False, default=0)
    max_ethereal = Column(Integer, nullable=False, default=0)
    ethereal_currency = Column(Integer, nullable=False, default=0)


class MonsterCostumeDB(Base):
    __tablename__ = "costumes"

    min_version = Column(String, nullable=False, default="0.0.0")
    ignore_locks = Column(Boolean, nullable=False, default=False)
    always_visible = Column(Boolean, nullable=False, default=False)
    hidden = Column(Boolean, nullable=False, default=True)
    keywords = Column(String, nullable=False, default="")
    medalCost = Column(Integer, nullable=False, default=0)
    sellCost = Column(Integer, nullable=False, default=0)
    etherealSellCost = Column(Integer, nullable=False, default=0)
    diamondCost = Column(Integer, nullable=False, default=0)
    alt_icon_name = Column(String, nullable=False, default="")
    unlock_teleport = Column(Boolean, nullable=False, default=True)
    breed_chance = Column(Float, nullable=False, default=5.0)
    file = Column(String, nullable=False, default="")
    monster_id = Column(Integer, nullable=False, default=0)
    alt_text = Column(String, nullable=False, default="")
    name = Column(String, nullable=False, default="")
    action = Column(Integer, nullable=False, default=100070)
    alt_icon_sheet = Column(String, nullable=False, default="")
    common_name = Column(String, nullable=False, default="")
    unlock_purchased = Column(Boolean, nullable=False, default=False)


class FlexEggsDB(Base):
    __tablename__ = "flex_eggs"

    cost_coins = Column(Integer, nullable=False, default=0)
    cost_diamonds = Column(Integer, nullable=False, default=0)
    xp = Column(Integer, nullable=False, default=0)
    mastertext_desc = Column(String, nullable=False, default="0.0.0")
    _def = Column(String, nullable=False, default="0.0.0")


class GeneDB(Base):
    __tablename__ = "genes"

    gene_graphic = Column(String, nullable=False, default="")
    gene_string = Column(String, nullable=False, default="")
    gene_letter = Column(String, nullable=False, default="")
    sort_order = Column(Integer, nullable=False, default=0)
    min_server_version = Column(String, nullable=False, default="1.0")


class AttunerGeneDB(Base):
    __tablename__ = "attuner_genes"

    schedule = Column(String, nullable=False, default="")
    critter_graphic = Column(String, nullable=False, default="")
    gene = Column(String, nullable=False, default="")
    attuner_graphic = Column(String, nullable=False, default="")
    instability = Column(Integer, nullable=False, default=0)
    island_id = Column(Integer, nullable=False, default=0)


class RareMonsterDataDB(Base):
    __tablename__ = "rare_monster_data"

    rare_id = Column(Integer, nullable=False, default=0)


class EpicMonsterDataDB(Base):
    __tablename__ = "epic_monster_data"

    epic_id = Column(Integer, nullable=False, default=0)


class MonsterHomeDB(Base):
    __tablename__ = "monster_home_data"

    source_monster = Column(Integer, nullable=False, default=0)
    dest_monster = Column(Integer, nullable=False, default=0)
    source_island = Column(Integer, nullable=False, default=0)
    dest_island = Column(Integer, nullable=False, default=0)


###################### -------    STUFF    ------- ######################


class LevelDB(Base):
    __tablename__ = "levels"
    xp = Column(Integer, nullable=False, default=0)
    title = Column(String, nullable=True, default=None)
    max_bakeries = Column(Integer, nullable=False, default=0)
    last_changed = Column(BIGINT, nullable=True, default=0)


class ScratchOfferDB(Base):
    __tablename__ = "scratch_offers"
    amount = Column(Integer, nullable=False, default=0)
    sheetName = Column(String, nullable=False, default="")
    probability = Column(Integer, nullable=False, default=0)
    is_top_prize = Column(Boolean, nullable=False, default=False)
    spriteName = Column(String, nullable=False, default="")
    revealSfx = Column(String, nullable=False, default="")
    type = Column(String, nullable=False, default="")
    prize = Column(String, nullable=False, default="")
    min_server_version = Column(String, nullable=False, default="0.0")
    last_changed = Column(BIGINT, nullable=True, default=0)


class FlipBoardDB(Base):
    __tablename__ = "flip_boards"
    name = Column(String, nullable=False, default="")
    definition = Column(String, nullable=False, default="")


class FlipLevelDB(Base):
    __tablename__ = "flip_levels"

    num_dipsters = Column(Integer, nullable=False, default=0)
    num_sigils = Column(Integer, nullable=False, default=0)
    shape = Column(String, nullable=False, default="")
    level = Column(Integer, nullable=False, default=0)
    columns = Column(Integer, nullable=False, default=0)
    rows = Column(Integer, nullable=False, default=0)
    num_epics = Column(Integer, nullable=False, default=0)
    mismatches_allowed = Column(Integer, nullable=False, default=0)
    num_rares = Column(Integer, nullable=False, default=0)
    prize_pool = Column(Integer, nullable=False, default=0)
    last_changed = Column(BIGINT, nullable=False, default=0)


class DailyCumulativeLoginDB(Base):
    __tablename__ = "daily_cumulative_logins"

    name = Column(String, nullable=False, default="")
    layout = Column(String, nullable=False, default="")
    rewards = Column(String, nullable=False, default="")
    min_version = Column(String, nullable=False, default="0.0")
    island = Column(Integer, nullable=False, default=0)


###################### -------    STORE    ------- ######################

class StoreItemDB(Base):
    __tablename__ = "store_items"

    amount = Column(Integer, nullable=False, default=0)
    unlock_level = Column(Integer, nullable=False, default=0)
    item_desc = Column(String, nullable=False, default="")
    max = Column(Integer, nullable=False, default=-1)
    ios_platform_id = Column(String, nullable=False, default="")
    item_name = Column(String, nullable=False, default="")
    enabled = Column(Boolean, nullable=False, default=True)
    most_popular_priority = Column(Integer, nullable=False, default=0)
    contents = Column(String, nullable=True, default=None)
    group_id = Column(Integer, nullable=False, default=0)
    sheet_id = Column(String, nullable=False, default="currency.bin")
    android_platform_id = Column(String, nullable=False, default="")
    price = Column(Integer, nullable=False, default=0)
    consumable = Column(Boolean, nullable=False, default=True)
    best_value_priority = Column(Integer, nullable=False, default=0)
    currency = Column(String, nullable=False, default="")
    exclude = Column(Boolean, nullable=False, default=False)
    item_title = Column(String, nullable=False, default="")
    image_id = Column(String, nullable=False, default="")
    min_server_version = Column(String, nullable=False, default="0.0")
    currency_id = Column(Integer, nullable=False, default=1)


class StoreGroupDB(Base):
    __tablename__ = "store_groups"

    group_title = Column(String, nullable=False, default="")
    group_name = Column(String, nullable=False, default="")
    ad_name = Column(String, nullable=False, default="")
    currency = Column(Integer, nullable=False, default=1)
    min_server_version = Column(String, nullable=False, default="0.2")
    store_ordering = Column(Integer, nullable=False, default=0)


class StoreCurrencyDB(Base):
    __tablename__ = "store_currencies"

    currency_name = Column(String, nullable=False, default="")


class NucleusRewardDB(Base):
    __tablename__ = "nucleus_rewards"

    types = Column(ARRAY(Integer), nullable=False, default=[])


class EntityAltCostsDB(Base):
    __tablename__ = "entity_alt_costs"

    cost_coins = Column(Integer, nullable=False, default=0)
    cost_keys = Column(Integer, nullable=False, default=0)
    cost_eth_currency = Column(Integer, nullable=False, default=0)
    cost_diamonds = Column(Integer, nullable=False, default=0)
    cost_relics = Column(Integer, nullable=False, default=0)
    cost_starpower = Column(Integer, nullable=False, default=0)
    entity_id = Column(Integer, nullable=False, default=0)
    island = Column(Integer, nullable=False, default=0)


class StoreReplacementDB(Base):
    __tablename__ = "store_replacements"

    numOwnedBeforeReplacement = Column(Integer, nullable=False, default=0)
    entityIdSource = Column(String, nullable=False, default=0)


class TitanSoulLevelDB(Base):
    __tablename__ = "tital_soul_levels"

    min_links = Column(Integer, nullable=False, default=0)
    power = Column(Integer, nullable=False, default=0)
    song_part = Column(Integer, nullable=False, default=0)


class TimedEventsDB(Base):
    __tablename__ = "timed_events"

    start_date = Column(BIGINT, nullable=False, default=0)
    end_date = Column(BIGINT, nullable=False, default=0)
    event_type = Column(String, nullable=False, default="")
    data = Column(String, nullable=False, default="")
    event_id = Column(Integer, nullable=False, default=0)


class GameSettingsDB(Base):
    __tablename__ = "game_settings"

    key = Column(String, nullable=False, default="")
    value = Column(String, nullable=False, default="")


###################### -------    PLAYER    ------- ######################


class PlayerDB(Base):
    __tablename__ = 'players'

    active_island = Column(Integer, nullable=True, default=None)
    avatar = Column(String, nullable=False, default="")
    moniker_id = Column(Integer, nullable=True)

    battle_level = Column(Integer, nullable=False, default=0)
    battle_loadout = Column(String, nullable=False, default="")
    battle_loadout_versus = Column(String, nullable=False, default="")
    battle_max_training_level = Column(Integer, nullable=False, default=0)
    battle_medals = Column(Integer, nullable=False, default=0)
    battle_xp = Column(Integer, nullable=False, default=0)
    pvp_season0 = Column(String, nullable=False, default="")
    pvp_season1 = Column(String, nullable=False, default="")
    prev_rank = Column(Integer, nullable=False, default=0)
    prev_tier = Column(Integer, nullable=False, default=0)
    prizes = Column(String, nullable=True)

    is_admin = Column(Boolean, nullable=False, default=False)
    player_groups = Column(String, nullable=False, default="")
    premium = Column(Boolean, nullable=False, default=False)
    display_name = Column(String, nullable=False, default="")
    friend_gift = Column(Integer, nullable=False, default=0)
    country = Column(String, nullable=False, default="")

    client_platform = Column(String, nullable=False, default="")
    client_tutorial_setup = Column(String, nullable=False, default="")
    currency_scratch_time = Column(BIGINT, nullable=False, default=0)

    cached_reward_day = Column(Integer, nullable=False, default=0)
    daily_bonus_amount = Column(Integer, nullable=False, default=0)
    daily_bonus_type = Column(String, nullable=False, default="")
    reward_day = Column(Integer, nullable=False, default=0)
    rewards_total = Column(Integer, nullable=False, default=0)
    scaled_daily_reward = Column(String, nullable=False, default="")
    next_daily_login = Column(BIGINT, nullable=False, default=0)

    daily_cumulative_login_calendar_id = Column(Integer, nullable=False, default=0)
    daily_cumulative_login_next_collect = Column(BIGINT, nullable=False, default=0)
    daily_cumulative_login_reward_idx = Column(Integer, nullable=False, default=0)
    daily_cumulative_login_total = Column(Integer, nullable=False, default=0)
    daily_relic_purchase_count = Column(Integer, nullable=False, default=0)

    diamonds = Column(Integer, nullable=False, default=0)
    coins = Column(Integer, nullable=False, default=0)
    diamonds_spent = Column(Integer, nullable=False, default=0)
    egg_wildcards = Column(Integer, nullable=False, default=0)
    keys = Column(Integer, nullable=False, default=0)
    food = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=0)
    relics = Column(Integer, nullable=False, default=0)
    xp = Column(Integer, nullable=False, default=0)
    starpower = Column(Integer, nullable=False, default=0)
    ethereal_currency = Column(Integer, nullable=False, default=0)
    total_starpower_collected = Column(Integer, nullable=False, default=0)

    has_promo = Column(Boolean, nullable=False, default=False)
    has_free_ad_scratch = Column(Boolean, nullable=False, default=False)
    has_scratch_off_m = Column(Boolean, nullable=False, default=False)
    has_scratch_off_s = Column(Boolean, nullable=False, default=False)
    flip_game_time = Column(BIGINT, nullable=False, default=0)
    monster_scratch_time = Column(BIGINT, nullable=False, default=0)

    next_relic_reset = Column(BIGINT, nullable=False, default=0)

    extra_ad_params = Column(String, nullable=False, default="")
    email_invite_reward = Column(Integer, nullable=False, default=0)
    fb_invite_reward = Column(Integer, nullable=False, default=0)
    twitter_invite_reward = Column(Integer, nullable=False, default=0)
    third_party_ads = Column(Boolean, nullable=False, default=False)
    third_party_video_ads = Column(Boolean, nullable=False, default=False)
    last_fb_post_reward = Column(Integer, nullable=False, default=0)

    inventory = Column(String, nullable=False, default="")
    new_mail = Column(Boolean, nullable=False, default=False)
    owned_island_themes = Column(String, nullable=False, default="")

    relic_diamond_cost = Column(Integer, nullable=False, default=0)
    speed_up_credit = Column(Integer, nullable=False, default=0)

    last_collect_all = Column(BIGINT, nullable=False, default=0)
    last_relic_purchase = Column(BIGINT, nullable=False, default=0)
    show_welcomeback = Column(Boolean, nullable=False, default=False)
    referral = Column(Integer, nullable=False, default=0)

    purchases_amount = Column(Integer, nullable=False, default=0)
    purchases_total = Column(Integer, nullable=False, default=0)

    last_login = Column(BIGINT, nullable=False, default=0)
    last_client_version = Column(String, nullable=False, default="")


class PlayerIslandDB(Base):
    __tablename__ = 'player_islands'

    island_id = Column(Integer, nullable=False, default=0)
    user_id = Column(Integer, nullable=False, default=0)
    last_baked = Column(String, nullable=False, default="")
    costumes_owned = Column(String, nullable=False, default="")
    likes = Column(Integer, nullable=False, default=0)
    dislikes = Column(Integer, nullable=False, default=0)
    last_player_level = Column(Integer, nullable=False, default=0)
    light_torch_flag = Column(Boolean, nullable=False, default=False)
    warp_speed = Column(Double, nullable=False, default=1.0)
    monsters_sold = Column(String, nullable=False, default='[]')
    name = Column(String, nullable=True)


class PlayerStructureDB(Base):
    __tablename__ = 'player_structures'

    user_island_id = Column(Integer, nullable=False, default=0)
    structure_id = Column(Integer, nullable=False, default=0)
    pos_x = Column(Integer, nullable=False, default=0)
    pos_y = Column(Integer, nullable=False, default=0)
    muted = Column(Boolean, nullable=False, default=False)
    flip = Column(Boolean, nullable=False, default=False)
    scale = Column(Float, nullable=False, default=1.0)
    in_warehouse = Column(Boolean, nullable=False, default=False)
    is_complete = Column(Boolean, nullable=False, default=False)
    is_upgrading = Column(Boolean, nullable=True)
    last_collection = Column(BIGINT, nullable=False, default=0)
    building_completed = Column(BIGINT, nullable=False, default=0)


class PlayerEggDB(Base):
    __tablename__ = "player_eggs"

    user_island_id = Column(Integer, nullable=False, default=0)
    user_structure_id = Column(Integer, nullable=False, default=0)
    monster_id = Column(Integer, nullable=False, default=0)
    laid_on = Column(BIGINT, nullable=False, default=0)
    hatches_on = Column(BIGINT, nullable=False, default=0)
    previous_name = Column(String, nullable=True, default="")
    prev_permamega = Column(String, nullable=True, default="{}")  # JSON SFS
    book_value = Column(Integer, nullable=False, default=0)



class PlayerMonsterDB(Base):
    __tablename__ = "player_monsters"

    user_island_id = Column(Integer, nullable=False, default=0)
    monster_id = Column(Integer, nullable=False, default=0)

    currency_type = Column(String, nullable=False, default="")
    time_to_collect = Column(Integer, nullable=False, default=0)
    underling_happy = Column(Integer, nullable=False, default=0)

    name = Column(String, nullable=False, default="")
    last_feeding = Column(BIGINT, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=0)
    timed_fed = Column(Integer, nullable=False, default=0)
    happy = Column(Integer, nullable=False, default=0)
    volume = Column(Float, nullable=False, default=1.0)

    in_hotel = Column(Boolean, nullable=False, default=False)
    marked_for_deletion = Column(Boolean, nullable=False, default=False)
    box_data = Column(String, nullable=False, default="")
    boxed_eggs = Column(String, nullable=False, default="")
    mega_data = Column(String, nullable=False, default="")

    eggTimerStart = Column(BIGINT, nullable=False, default=0)
    evolutionUnlocked = Column(Boolean, nullable=False, default=False)
    powerupOnlocked = Column(Boolean, nullable=False, default=False)
    evolution_static_data = Column(String, nullable=False, default="")
    evolution_flex_data = Column(String, nullable=False, default="")

    is_training = Column(Boolean, nullable=False, default=False)
    training_start = Column(Integer, nullable=False, default=0)
    training_end = Column(Integer, nullable=False, default=0)

    parent_island_id = Column(Integer, nullable=True)
    parent_monster_id = Column(Integer, nullable=True)
    child_island_id = Column(Integer, nullable=True)
    child_monster_id = Column(Integer, nullable=True)

    pos_x = Column(Integer, nullable=False, default=0)
    pos_y = Column(Integer, nullable=False, default=0)
    muted = Column(Boolean, nullable=False, default=1.0)
    flip = Column(Boolean, nullable=False, default=0)
    last_collection = Column(BIGINT, nullable=False, default=0)
    book_value = Column(Integer, nullable=False, default=0)

    collected_coins = Column(Integer, nullable=True)
    collected_food = Column(Integer, nullable=True)
    collected_diamonds = Column(Integer, nullable=True)
    collected_starpower = Column(Integer, nullable=True)
    collected_ethereal = Column(Integer, nullable=True)
    collected_medals = Column(Integer, nullable=True)
    collected_relics = Column(Float, nullable=True)
    collected_keys = Column(Integer, nullable=True)