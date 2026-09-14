# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 —— 纯业务逻辑（无IO、不碰DB/QQ）

聚合导出全部计算函数，供 services/commands 层调用。
"""
import random  # noqa: F401

from .constants import (  # noqa: F401
    START_MAP, START_SUBAREA, DEFAULT_GOLD, DEFAULT_ATTR_PTS, DEFAULT_STAMINA,
    # v99.3 概率/阶梯常量
    FLEE_CHANCE, MON_SKILL_CHANCE, MON_SKILL_CRIT,
    # v130.7 意见#28：逃跑率等级差/速度差修正与 clamp
    FLEE_LEVEL_STEP, FLEE_SPD_STEP, FLEE_MIN, FLEE_MAX,
    SHIELD_COUNTER_CHANCE, REFLECT_CHANCE,
    ENCOUNTER_EVENT_CHANCE, SA_BOSS_CHANCE, ENCOUNTER_LOW_CHANCE,
    FISH_RARE_CHANCE, PET_EGG_ORANGE_CHANCE, RARE_MAT_CHANCE, PROF5_BONUS_CHANCE,
    INST_EVENT_CHANCE, MOVE_ENCOUNTER_CHANCE,
    STARFALL_STUN_CHANCE, BOSS_BP_DROP_CHANCE, TRADER_DEAL_CHANCE, CHEST_BP_CHANCE,
    INSTANCE_BP_CHANCE, ELITE_EQ_DROP_CHANCE,
    RECIPE_LV_TIERS,
    # v102.1 地图/子区域类型常量
    MAP_TYPE_TOWN, MAP_TYPE_FIELD, MAP_TYPE_INSTANCE, MAP_TYPE_HIDDEN,
    SUB_TYPE_TOWN, SUB_TYPE_STREET, SUB_TYPE_GATE,
    # v102.2 物品 type 常量
    ITEM_TYPE_PET_EGG, ITEM_TYPE_MOUNT,
    # v126.3 材料大类归并集合（背包『材料』筛选/『使用』材料兜底）
    MATERIAL_KIND_TYPES,
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
    # v138.2 异常体系五律（阈值递增/每场上限+饱和/跨阶段保留/真伤独立结算/饱和收敛）
    DOT_THRESHOLD_MULT, DOT_THRESHOLD_CAP, DOT_MAX_TRIGGER,
    DOT_PRESERVE_PCT, DOT_PRESERVE_THRESHOLD_BONUS, DOT_SATURATE_MULT,
)
from .index import pinyin_id, build_index, resolve, display  # noqa: F401
from .dialogue import (  # noqa: F401
    get_dialogue, dialogue_node, check_need, visible_options, is_end,
    node_text,
)
from .stats import (  # noqa: F401
    monster_stats, equip_stats, equip_value, exp_to_next, monster_exp, monster_gold,
)
# B-RPH：`maps` 薄壳保留（import 期 `_build_monster_locs()` 是活的装配时机）；`_build_ency` 本门从不消费，已随收口删除。
from .drops import (  # noqa: F401
    make_blueprint, roll_blueprint, roll_drop, roll_drop_equip, generate_equip, generate_roster_equip,
    build_monster, build_monster_group,
)
from .factions import faction_reputation_tier  # noqa: F401
# v135 铁匠铺全服共享货架：延迟 import（模块自身 import db → db → store.connection →
# content 循环；数据层装配后再加载，避免 content 初始化期死锁）
from . import smith_stock as _smith_stock  # noqa: F401,E402
from .smith_stock import (  # noqa: F401
    QUALITY_WEIGHTS, STOCK_COUNT, STOCK_WINDOW, RESTOCK_HOURS, SMITH_NPC_NAMES,
    town_level, roll_stock, get_smith_stock, buy_stock_item, smith_stock_price,
)
# v166 商店限购（店内共享库存 + 每日个人限购，数据驱动）：同样延迟 import（db 惰性）
from . import shop_stock as _shop_stock  # noqa: F401,E402
from .shop_stock import (  # noqa: F401
    get_limit, stock_state, check_and_consume, limit_label,
)
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
# v127.5 通用倒计时事件引擎（懒计时：限时NPC / 限时任务 / 限时商店等
# 一切"限时存在"状态，任意玩家指令惰性刷新，见 docs/TIMED_EVENT_PLAN_v1275.md）
from .timed_events import (  # noqa: F401
    register_timed, set_timed, get_timed, remove_timed, list_timed, refresh_timed,
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
# B-RPH 聚合门收口：以下四类薄壳已删；真源直取包内实现（包加载口已由 `constants` 完成）
from content.class_sets import _build_class_sets  # noqa: F401
from content.enchant import enchant_value, enchant_match_material  # noqa: F401
from .runes import rune_value, rune_conflict, rune_item  # noqa: F401
# v136 原石系统核心逻辑（聚合导出，命令层 C.roll_gem / C.gem_combine 等可直接调用）
from .gems import roll_gem, gem_combine, gem_socket_cost, sockets_capacity, roll_gem_drop  # noqa: F401
from content.portals import portal_cost  # noqa: F401
from .events import roll_explore_event, roll_explore_egg  # noqa: F401
from content.pois import subarea_pois, roll_poi, subarea_props, prop_entry  # noqa: F401
from .maps import (  # noqa: F401
    subarea_links, map_exit_subarea, map_entry_subarea,
    # v115 网状子区域：供命令层 C.xxx 调用（world/combat 经 getattr(C, ...) 消费）
    subarea_depth, is_hidden_room, reveal_met, reveal_progress, bump_explore_count,
    # v183 地图形状搬引擎：适配层（map_space 引擎对象 / map_center 枢纽 / map_route 必经路径）
    map_space, map_center, map_route,
)
from .daily_events import today_map_event, today_event_effects  # noqa: F401
from content.pets import (  # noqa: F401  v173.2 封顶50+等级差乘区
    make_pet_egg, pet_exp_need, pet_exp_mult, pet_skill_label, pet_quality_label,
    pet_line, pet_exp_bonus, pct_str, PET_MAX_LEVEL,
)
from .mounts import make_mount_rein, roll_mount_drop, mount_effects  # noqa: F401
from .exploration import (  # noqa: F401
    record_visit as exploration_record_visit,  # v115 协作契约名（G 调用 C.exploration_record_visit）
    record_visit, region_progress, overall_progress,
)
# v140 波2：野外 Boss 看守宝箱（野王体系）核心逻辑（聚合导出，命令层 C.wild_king_* 调用）
from .wild_king import (  # noqa: F401
    wild_king_tick, wild_king_state, explore_king, build_king_monster,
    wild_king_on_kill, open_chest, wild_king_summary,
    personal_meta, list_active_kings, period_key, period_label,
)
# v141 大陆隔离：位置结构体 + 大陆抽象（聚合导出，命令层 C.Position / C.cur_map_obj 等调用）
from content.position import (  # noqa: F401
    Position, cur_map_obj, cur_subareas, player_position, position_to_db,
)
from .worlds import (  # noqa: F401
    get_instance_world, create_instance_world, destroy_instance_world,
    update_instance_world, set_instance_st, get_instance_st,
    list_instance_worlds, cleanup_stale_instances, resolve_map_for,
    instance_worlds,
)

# 原 game/engine.py、game/battle.py 保持原位，由 game/__init__ 聚合
