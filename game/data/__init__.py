# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 —— 纯静态内容（无逻辑、无IO）

聚合导出全部数据表，保持 `from game.data import *` 或
`import game.data as C` 用法与旧 content 一致。
"""
import random  # noqa: F401  (部分表构造使用)

from .index import _INDEXES  # noqa: F401
from .classes import CLASSES  # noqa: F401
from .maps import (
    MAPS, MAP_BY_ID, ENCY_MATERIAL_SOURCE, ENCY_MONSTER_MAP, ENCY_MAP_MONSTERS,
    MAP_AREAS, AREA_ENTRY, MAP_CONNECTIONS, HIDDEN_MAP_UNLOCK, LEGACY_MAP_ALIAS,
)  # noqa: F401
from .subareas import SUBAREAS  # noqa: F401
from .monsters import MONSTER_SKILLS  # noqa: F401
from .monster_mods import MONSTER_MODS  # noqa: F401
from .skills import PLAYER_SKILLS, BRANCH_SKILLS, TUTOR_SKILLS  # noqa: F401
from .builds import BUILDS  # noqa: F401
from .equipment import (  # noqa: F401
    EQUIP_SLOTS, QUALITY, QUALITY_ORDER, WEAPON_TYPES, WEAPON_NAME_SUFFIX,
    WEAPON_FLAVOR, EQUIP_NAME_PREFIX, EQUIP_NAME_SUFFIX, EQUIP_PREFIX_FLAVOR,
    AFFIX_COUNT, AFFIX_FALLBACK,
    QUALITY_CN, WT_CN,
)
# v101.25i6 品质统一：垂钓档位 = 装备 QUALITY_ORDER（加品质全服生效）
FISH_QUALITY_ORDER = QUALITY_ORDER  # noqa: F401
from .affixes import (  # noqa: F401
    AFFIXES, AFFIX_POOL_BY_QUALITY, AFFIX_KIND, AFFIX_AFFINITY_POOLS,
    AFFIX_AFFINITY_CN, LEGENDARY_EFFECTS, SERIES_FIXED_AFFIX,
)
from .equip_roster import (  # noqa: F401
    EQUIP_ROSTER, EQUIP_ROSTER_BY_NAME, SERIES_SETS,
)
from .items import ITEMS, MATERIALS, MATERIALS_BY_NAME  # noqa: F401
from .npcs import NPCS  # noqa: F401
from .dialogues import DIALOGUES  # noqa: F401
from .quests import MAIN_QUESTS, SIDE_QUESTS, DAILY_QUESTS  # noqa: F401
from .shop import SHOP_WEAPONS, SHOP_SMITH_MATERIALS, SHOP_EQUIP, SHOP_WILD_TRADE, SHOP_SUBAREA_ITEMS  # noqa: F401
from .factions import (  # noqa: F401
    FACTIONS, FACTION_ORDER, REPUTATION_TIERS, AREA_FACTION, CHRONICLES,
    FACTION_SHOP,  # v105 M18 P2-7：声望商店数据（聚合层导出，与其余表一致）
)
from .fishing import (  # noqa: F401
    FISHING_SPOTS, FISH_POOL, FISH_QUALITY_WEIGHTS,
    FISH_EXP, FISH_COLLECT,
)
from .enhance import (  # noqa: F401
    ENHANCE_TABLE, MAX_ENHANCE, ENHANCE_FAIL_DROP, ENHANCE_SMITH_MAPS,
)
from .sets import SET_THEMES, SET_CHANCE, SETS, CLASS_SET_STAGES, CLASS_SET_THEMES  # noqa: F401
from .craft import CRAFT_RECIPES, CRAFT_RECIPE_ALIASES  # noqa: F401
from .enchant import (  # noqa: F401
    ENCHANT_SLOTS, ENCHANT_RECIPES, ENCHANT_CRIT_CHANCE, ENCHANT_MAX_VALUE,
)
from .runes import (  # noqa: F401
    RUNES, RUNE_CONFLICTS, RUNE_DROP, RUNE_EFFECT_NAMES, RUNE_LEVEL_ROMAN,
)
from .portals import PORTALS  # noqa: F401
from .gather import CAMP_SPOTS, MINE_SPOTS  # noqa: F401
from .events import EXPLORE_EVENTS, EVENT_WEIGHT_SUM, EXPLORE_EGG_CHANCE, EXPLORE_EGG_EVENTS, EXPLORE_EGG_SUM  # noqa: F401
from .pois import POIS, SUBAREA_POIS, NOTE_POOL, RUNE_POOL, SIGHT_POOL  # noqa: F401
from .props import PROPS, SUBAREA_PROPS  # noqa: F401
from .hidden_monsters import HIDDEN_MONSTERS  # noqa: F401
from .titles import TITLES  # noqa: F401
from .world import WORLD_EVENT_POOL, AUCTION_POOL, WORLD_BOSS_POOL  # noqa: F401
from .pets import PET_POOL, PET_EGG_ROLL  # noqa: F401
from .mounts import (  # noqa: F401
    MOUNT_POOL, MOUNT_BY_KEY, MOUNT_DROP_ELITE, MOUNT_DROP_BOSS,
)
from .alchemy import ALCHEMY_RECIPES  # noqa: F401
from .cooking import COOKING_RECIPES  # noqa: F401
from .guild import GUILD_CONFIG  # noqa: F401
from .instances import INSTANCES  # noqa: F401
from .housing import PROPERTIES, HOUSE_LEVELS, HOUSE_MAX_LEVEL, HOUSE_REFUND  # noqa: F401
from .races import RACES  # noqa: F401
from .achievements import ACHIEVEMENTS  # noqa: F401
from .wild_npcs import WILD_NPCS, HIDDEN_NPCS  # noqa: F401
from .gather_pools import GATHER_MAP_POOLS  # noqa: F401
from .gather_pools import GATHER_COND_POOLS, MINING_DEEP_POOLS  # noqa: F401 v102.3 限定采集/深矿
from .poi_pools import WISH_POOL, CAMPFIRE_FOOD_POOL, HERB_POOL  # noqa: F401
from .honor_shop import HONOR_SHOP  # noqa: F401
from .prof_config import (  # noqa: F401
    PROF_TUTORS, PROF_WAIT_BASE, DAILY_PROF_TASKS, BAG_FILTER_TYPES,
)
from .skill_up import SKILL_UP  # noqa: F401  (v102.4 从 engine.py 下沉)
from .core_resources import CORE_RESOURCES  # noqa: F401  (v102.4 从 engine.py 下沉)
from .stat_templates import (  # noqa: F401  (v102.5 从 core/stats.py 下沉)
    MONSTER_ROLE_BASE, MONSTER_ROLE_GROWTH, MONSTER_EXP_BASE, MONSTER_GOLD_BASE,
    EQUIP_SLOT_BASE, EQUIP_SLOT_SCALING,
)

# 依赖顺序：maps 依赖 classes 等 → 在最后装配派生表/索引
from . import _assembly  # noqa: F401,E402  (执行 build_index 等)

# 让 build_index 产生的派生表也可见（_SKILL_FLAT/_MONSTER_INDEX 等）
from ._assembly import (  # noqa: F401
    _SKILL_FLAT, _MONSTER_INDEX, _FISH_INDEX, _NPC_INDEX, _SHOP_W_INDEX,
    SUBAREA_INDEX, SUBAREA_BY_MAP,
)
