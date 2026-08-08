# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 —— 纯业务逻辑（无IO、不碰DB/QQ）

聚合导出全部计算函数，供 services/commands 层调用。
"""
import random  # noqa: F401

from .index import pinyin_id, build_index, resolve, display  # noqa: F401
from .dialogue import (  # noqa: F401
    get_dialogue, dialogue_node, check_need, visible_options, is_end,
)
from .stats import (  # noqa: F401
    monster_stats, equip_stats, exp_to_next, monster_exp, monster_gold,
)
from .maps import _build_ency  # noqa: F401
from .monsters import monster_skills_pool  # noqa: F401
from .drops import (  # noqa: F401
    _stage_for_lv, roll_blueprint, roll_drop, generate_equip, generate_roster_equip,
    build_monster,
)
from .factions import faction_reputation_tier  # noqa: F401
from .fishing import roll_fish, roll_collect_fish  # noqa: F401
from .time_weather import (  # noqa: F401
    current_period, current_season, today_weather, time_weather_summary,
    PERIOD_CN, SEASON_CN, WEATHER_CN,
)
from .wild import (  # noqa: F401
    ALL_WILD, npc_map_id, unlock_met, base_conditions_met,
    roll_wild_encounter, wild_npc_findable, met_wild, nearby_hints,
)
from .achievements import (  # noqa: F401
    check_achievements, achievement_titles, achievement_points,
)
from .affix import (  # noqa: F401
    roll_affixes, fixed_affixes, stat_affix_stats, random_req,
    affix_label, equip_affix_lines,
)
from .craft import (  # noqa: F401
    craft_recipe_make, craft_recipe_search, craft_recipes_by_material,
    craft_recipes_for_level,
)
from .class_sets import _build_class_sets  # noqa: F401
from .enchant import enchant_value, enchant_match_material  # noqa: F401
from .runes import rune_value, rune_conflict, rune_item  # noqa: F401
from .portals import portal_cost  # noqa: F401
from .events import roll_explore_event, roll_explore_egg  # noqa: F401
from .pois import subarea_pois, roll_poi, subarea_props  # noqa: F401
from .pets import make_pet_egg, pet_exp_need, pet_skill_label  # noqa: F401
from .mounts import make_mount_rein, roll_mount_drop  # noqa: F401

# 原 game/engine.py、game/battle.py 保持原位，由 game/__init__ 聚合
