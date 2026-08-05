# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 —— 纯业务逻辑（无IO、不碰DB/QQ）

聚合导出全部计算函数，供 services/commands 层调用。
"""
import random  # noqa: F401

from .index import pinyin_id, build_index, resolve, display  # noqa: F401
from .stats import (  # noqa: F401
    monster_stats, equip_stats, exp_to_next, monster_exp, monster_gold,
)
from .maps import _build_ency  # noqa: F401
from .monsters import monster_skills_pool  # noqa: F401
from .drops import (  # noqa: F401
    _stage_for_lv, roll_blueprint, roll_drop, generate_equip, build_monster,
)
from .factions import faction_reputation_tier  # noqa: F401
from .fishing import roll_fish  # noqa: F401
from .affix import _affix_base_value, roll_affixes  # noqa: F401
from .craft import (  # noqa: F401
    craft_recipe_make, craft_recipe_search, craft_recipes_by_material,
    craft_recipes_for_level,
)
from .class_sets import _build_class_sets  # noqa: F401
from .enchant import enchant_value, enchant_match_material  # noqa: F401
from .runes import rune_value, rune_conflict, rune_item  # noqa: F401
from .portals import portal_cost  # noqa: F401
from .events import roll_explore_event  # noqa: F401
from .pets import make_pet_egg, pet_exp_need  # noqa: F401
from .mounts import make_mount_rein, roll_mount_drop  # noqa: F401

# 原 game/engine.py、game/battle.py 保持原位，由 game/__init__ 聚合
