# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 —— 纯业务逻辑（无IO、不碰DB/QQ）

聚合导出全部计算函数，供 services/commands 层调用。
"""
import random  # noqa: F401

from .constants import (  # noqa: F401
    START_MAP, START_SUBAREA, DEFAULT_GOLD, DEFAULT_ATTR_PTS, DEFAULT_STAMINA,
    # v99.3 概率/阶梯常量
    FLEE_CHANCE, MON_SKILL_CHANCE, MON_SKILL_CRIT,
    SHIELD_COUNTER_CHANCE, REFLECT_CHANCE,
    ENCOUNTER_EVENT_CHANCE, SA_BOSS_CHANCE, ENCOUNTER_LOW_CHANCE,
    FISH_RARE_CHANCE, PET_EGG_ORANGE_CHANCE, RARE_MAT_CHANCE, PROF5_BONUS_CHANCE,
    INST_EVENT_CHANCE, MOVE_ENCOUNTER_CHANCE,
    STARFALL_STUN_CHANCE, BOSS_BP_DROP_CHANCE, TRADER_DEAL_CHANCE, CHEST_BP_CHANCE,
    RECIPE_LV_TIERS,
    # v102.1 地图/子区域类型常量
    MAP_TYPE_TOWN, MAP_TYPE_FIELD, MAP_TYPE_INSTANCE, MAP_TYPE_HIDDEN,
    SUB_TYPE_TOWN, SUB_TYPE_STREET, SUB_TYPE_GATE,
    # v102.2 物品 type 常量
    ITEM_TYPE_PET_EGG, ITEM_TYPE_MOUNT,
    # v102.3 职业 ID 常量
    CLASS_NOVICE,
    # v102.6 属性集合常量
    PCT_STATS,
    # v106 穿透/韧性/幸运：百分比上限表 + 乘算穿透集合
    PCT_CAPS, PENE_PCT_STATS,
    # v106.4 特殊属性：面板 0 时不显示
    OPTIONAL_STATS,
    # v103.3 B3 整数魔法数字
    EVOLVE_LEVELS, EVOLVE_FEES, RESET_SKILL_COST,
    DEFAULT_MAX_MP, PVP_TIMEOUT_SEC, GUILD_EXP_BASE, PROF_EXP_BASE, prof_exp_need,
    # vF3 体验与战斗数值调整常量
    STAMINA_RECOVER_INTERVAL, SKILL_PMULT_CAP,
)
from .index import pinyin_id, build_index, resolve, display  # noqa: F401
from .dialogue import (  # noqa: F401
    get_dialogue, dialogue_node, check_need, visible_options, is_end,
    node_text,
)
from .stats import (  # noqa: F401
    monster_stats, equip_stats, equip_value, exp_to_next, monster_exp, monster_gold,
)
from .maps import _build_ency  # noqa: F401
from .drops import (  # noqa: F401
    make_blueprint, roll_blueprint, roll_drop, generate_equip, generate_roster_equip,
    build_monster, build_monster_group,
)
from .factions import faction_reputation_tier  # noqa: F401
from .fishing import roll_fish, roll_collect_fish, roll_fish_size_weight  # noqa: F401
from .time_weather import (  # noqa: F401
    current_period, current_season, today_weather, time_weather_summary,
    PERIOD_CN, SEASON_CN, WEATHER_CN,
)
from .wild import (  # noqa: F401
    ALL_WILD, npc_map_id, unlock_met, base_conditions_met,
    roll_wild_encounter, wild_npc_findable, met_wild, nearby_hints,
    town_npc_day_sa, town_npc_visible, town_npc_dialogue,
)
from .achievements import (  # noqa: F401
    check_achievements, achievement_titles, achievement_points,
    claim_achievement_rewards,
)
from .affix import (  # noqa: F401
    roll_affixes, fixed_affixes, stat_affix_stats, random_req,
    affix_label,
)
from .craft import (  # noqa: F401
    craft_recipe_make, craft_recipe_search, craft_recipes_by_material,
)
from .event_templates import EventContext, execute_event_template  # noqa: F401
from .class_sets import _build_class_sets  # noqa: F401
from .enchant import enchant_value, enchant_match_material  # noqa: F401
from .runes import rune_value, rune_conflict, rune_item  # noqa: F401
from .portals import portal_cost  # noqa: F401
from .events import roll_explore_event, roll_explore_egg  # noqa: F401
from .pois import subarea_pois, roll_poi, subarea_props, prop_entry  # noqa: F401
from .maps import (  # noqa: F401
    subarea_links, map_exit_subarea, map_entry_subarea,
    # v115 网状子区域：供命令层 C.xxx 调用（world/combat 经 getattr(C, ...) 消费）
    subarea_depth, is_hidden_room, reveal_met, reveal_progress, bump_explore_count,
)
from .daily_events import today_map_event, today_event_effects  # noqa: F401
from .pets import make_pet_egg, pet_exp_need, pet_skill_label, pet_quality_label, pet_line  # noqa: F401
from .mounts import make_mount_rein, roll_mount_drop, mount_effects  # noqa: F401
from .exploration import (  # noqa: F401
    record_visit as exploration_record_visit,  # v115 协作契约名（G 调用 C.exploration_record_visit）
    record_visit, region_progress, overall_progress,
)

# 原 game/engine.py、game/battle.py 保持原位，由 game/__init__ 聚合
