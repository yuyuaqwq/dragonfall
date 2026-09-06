# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 —— 纯静态内容（无逻辑、无IO）

聚合导出全部数据表，保持 `from game.data import *` 或
`import game.data as C` 用法与旧 content 一致。
"""
import random  # noqa: F401  (部分表构造使用)

from .index import _INDEXES  # noqa: F401
from .classes import CLASSES  # noqa: F401
from .maps import (
    MAPS, MAP_BY_ID, ENCY_MATERIAL_SOURCE, ENCY_MONSTER_MAP, ENCY_MAP_MONSTERS,
    MONSTER_LOCS,  # v130.3 意见#3：怪名→子区域/等级/类型 详细分布
    MAP_CONNECTIONS, HIDDEN_MAP_UNLOCK, LEGACY_MAP_ALIAS,
)  # noqa: F401
from .subareas import SUBAREAS  # noqa: F401
from .monsters import MONSTER_SKILLS, ELITE_EQUIP_DROP  # noqa: F401
# v140 波1：野外精英专属紫装表（并入自孤儿文件 drop_add_v140.py，聚合层导出）
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
# v181-P2A：10 章名册套装效果表（自 core/class_sets.py 下沉，纯数据）
from .set_bonus_data import SERIES_SET_BONUS  # noqa: F401
# v180E 阶段4：武器特效参数表（数值权威默认，装备行 we_data 为覆盖层）
from .weapon_effect_data import WEAPON_EFFECT_DATA  # noqa: F401
from .items import ITEMS, MATERIALS, MATERIALS_BY_NAME  # noqa: F401
from .npcs import NPCS  # noqa: F401
from .dialogues import DIALOGUES  # noqa: F401
from .quests import MAIN_QUESTS, SIDE_QUESTS, DAILY_QUESTS  # noqa: F401
# v169.2 周常悬赏（Lv50+ 高频经验源，命令层 commands/weekly.py 消费）
from .weekly_quests import (  # noqa: F401
    WEEKLY_QUESTS, WEEKLY_PICK, WEEKLY_MIN_LV,
)
# v169.2 修炼爬塔（Lv70+ 高频经验源，命令层 commands/tower.py 消费）
from .trial_tower import (  # noqa: F401
    TRIAL_FLOORS, TRIAL_DAILY_LIMIT, TRIAL_MIN_LV, TRIAL_MAX_FLOOR,
)
from .shop import SHOP_WEAPONS, SHOP_SMITH_MATERIALS, SHOP_EQUIP, SHOP_WILD_TRADE, SHOP_SUBAREA_ITEMS, SUBAREA_KIND  # noqa: F401
from .shop_limit import SHOP_LIMIT  # noqa: F401 v166 商店限购配置
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
from .upgrade import (  # noqa: F401 v172 装备升级（真等级化，cost 阶梯）
    UPGRADE_TABLE, UPGRADE_STONE, UPGRADE_STAMINA, UPGRADE_MATERIAL_CN,
)
from .sets import SET_THEMES, SET_CHANCE, SETS, CLASS_SET_STAGES, CLASS_SET_THEMES  # noqa: F401
from .craft import CRAFT_RECIPES, CRAFT_RECIPE_ALIASES  # noqa: F401
from .enchant import (  # noqa: F401
    ENCHANT_SLOTS, ENCHANT_RECIPES, ENCHANT_CRIT_CHANCE, ENCHANT_MAX_VALUE,
)
from .runes import (  # noqa: F401
    RUNES, RUNE_CONFLICTS, RUNE_DROP, RUNE_EFFECT_NAMES, RUNE_LEVEL_ROMAN,
    RUNE_CRAFT, RUNE_CRAFT_SHARDS, RUNE_SHARD_KEY,
)
# v136 原石系统数据表（数据层聚合导出，命令层 C.GEM_TIERS 等可直接访问）
from .gems import (  # noqa: F401
    GEM_TIERS, GEM_TIER_NAMES, GEM_STATS, GEM_SOCKETS, GEM_DRILL,
    GEM_REMOVE_COST, RUNE_REMOVE_COST, GEM_LEGENDARY_EFFECTS,
    GEM_DROP_RATE, GEM_DROP_TIER, GEM_BOSS_FIXED,
    GEM_BASE_NAME, GEM_ITEM_TYPE,
)
# v172 装备重锻（怪猎派生树）：同系列旧→新，继承强化/升级
from .refine import REFINE_RECIPES  # noqa: F401
# v172 路B 重锻专属装备（source=重锻，仅重锻可得；target 为名册 rid，命令层并查两表）
from .refine_exclusive import (  # noqa: F401
    REFINE_EXCLUSIVE_RECIPES, merge_into,
)
# v136 怪异炼成（怪猎曙光怪异化）：稀有素材随机强化，每件限 3 次
from .calamity import (  # noqa: F401
    CALAMITY_MAX, CALAMITY_COST, CALAMITY_STATS,
    CALAMITY_BONUS, CALAMITY_MALUS, CALAMITY_POSITIVE_CHANCE,
)
from .portals import PORTALS  # noqa: F401
from .gather import CAMP_SPOTS, MINE_SPOTS  # noqa: F401
from .events import EXPLORE_EVENTS, EVENT_WEIGHT_SUM, EXPLORE_EGG_CHANCE, EXPLORE_EGG_EVENTS, EXPLORE_EGG_SUM  # noqa: F401
from .pois import POIS, SUBAREA_POIS, NOTE_POOL, RUNE_POOL, SIGHT_POOL  # noqa: F401
from .props import PROPS, SUBAREA_PROPS  # noqa: F401
from .hidden_monsters import HIDDEN_MONSTERS  # noqa: F401
from .titles import TITLES  # noqa: F401
from .world import WORLD_EVENT_POOL, AUCTION_POOL, WORLD_BOSS_POOL  # noqa: F401
from .pets import PET_POOL, PET_EGG_ROLL, PET_SKILL_UNLOCK_LV  # noqa: F401
from .mounts import (  # noqa: F401
    MOUNT_POOL, MOUNT_BY_KEY, MOUNT_DROP_ELITE, MOUNT_DROP_BOSS,
)
from .alchemy import ALCHEMY_RECIPES  # noqa: F401
from .cooking import COOKING_RECIPES  # noqa: F401
from .guild import GUILD_CONFIG  # noqa: F401
from .instances import INSTANCES, INSTANCE_BOSS_EQUIP_DROP  # noqa: F401
# v140 波1：副本 Boss 专属装备掉落表（并入自孤儿文件 drop_add_v140.py，聚合层导出）
# v140 波2：副本通关后调查点数据（聚合层导出，命令层 C.INVESTIGATION_POINTS 直读）
from .instance_investigation import (  # noqa: F401
    INVESTIGATION_POINTS, INVESTIGATE_COLLECT_SAMPLES,
    INVESTIGATE_BP_CHANCE, INVESTIGATE_RUNE_CHANCE, INVESTIGATE_COLLECT_CHANCE,
)
# v140 波2：野外 Boss 看守宝箱（野王体系）数据表（聚合层导出，命令层 C.WILD_KING_* 直读）
from .wild_king_data import (  # noqa: F401
    WILD_KINGS, WILD_KING_MAPS, WILD_KING_PERIODS, WILD_KING_CHEST_TIERS,
    WILD_KING_GLOBAL_LIMIT, WILD_KING_LIFETIME_SEC, WILD_KING_LOOT_PRIORITY_SEC,
    WILD_KING_PER_PERIOD_LIMIT, WILD_KING_PER_DAY_LIMIT,
    WILD_KING_PITY_PERIODS, WILD_KING_NO_KILL_EXTRA, WILD_KING_SPAWN_HOURS,
)
# v140 波3.3：任务奖励/章节礼包/补给箱数据（聚合层导出，命令层 C.CHAPTER_PACK / C.SUPPLY_BOX 直读）
from .quest_add_v140 import (  # noqa: F401
    QUEST_ADD, QUEST_MAT, CHAPTER_PACK, SUPPLY_BOX,
)
# v140 波3.7：今日奇遇地图配置（此前仅被 core/daily_events.py 直连引用，未走聚合导出；
# 事件菜单指令需要 C.DAILY_MAP_EVENTS 全图遍历，补导出）
from .daily_events import DAILY_MAP_EVENTS  # noqa: F401
from .housing import PROPERTIES, HOUSE_LEVELS, HOUSE_MAX_LEVEL, HOUSE_REFUND  # noqa: F401
from .races import RACES  # noqa: F401
from .achievements import ACHIEVEMENTS  # noqa: F401
from .collection_book import COLLECTION_BOOKS  # noqa: F401  (v140 波2：5 套冒险者收藏册数据)
from .wild_npcs import WILD_NPCS, HIDDEN_NPCS  # noqa: F401
from .gather_pools import GATHER_MAP_POOLS  # noqa: F401
from .gather_pools import GATHER_COND_POOLS, MINING_DEEP_POOLS  # noqa: F401 v102.3 限定采集/深矿

# v104 B4：采集/挖掘池引用的材料 id 全量校验——任一缺定义即在启动时报错，
# 前置 _settle_gather 运行期的 C.MATERIALS[mat]["price"] KeyError 风险
for _pool_name, _pool in (("GATHER_MAP_POOLS", GATHER_MAP_POOLS),
                          ("GATHER_COND_POOLS", GATHER_COND_POOLS),
                          ("MINING_DEEP_POOLS", MINING_DEEP_POOLS)):
    for _map_id, _entries in _pool.items():
        for _entry in _entries:
            _mat_id = _entry[0]
            assert _mat_id in MATERIALS, (
                f"[{_pool_name}:{_map_id}] 材料 {_mat_id} 未在 MATERIALS 定义"
            )

# v124 FISH_POOL↔MATERIALS 双处定义防漂移校验：_settle_fishing 入包以 FISH_POOL 的
# type/price 为权威（economy.py 按名 resolve("materials") 取 mat_ key），MATERIALS 必须
# 已登记同名条目且 price/type 一致——任一渔获缺登记/价型不符启动即报错（fail-fast），
# 防止新增垃圾/宝物/鱼王类渔获后运行期 KeyError/中文 key 入包
for _f in FISH_POOL:
    _fmat = MATERIALS_BY_NAME.get(_f["name"])
    assert _fmat is not None, (
        f"[FISH_POOL] 渔获『{_f['name']}』未在 MATERIALS 登记——"
        f"_settle_fishing 按名 resolve 将回退中文 key 入包"
    )
    assert _fmat.get("type") == _f.get("type"), (
        f"[FISH_POOL] 渔获『{_f['name']}』type 不一致："
        f"FISH_POOL={_f.get('type')} vs MATERIALS={_fmat.get('type')}（以 FISH_POOL 为准）"
    )
    assert _fmat.get("price") == _f.get("price"), (
        f"[FISH_POOL] 渔获『{_f['name']}』price 不一致："
        f"FISH_POOL={_f.get('price')} vs MATERIALS={_fmat.get('price')}"
    )

# v126.4 审计 P3：FISH_POOL size_range/weight_range 合法性校验（fail-fast）——
# 防珍珠类 0.0kg 式区间配置错误（区间倒挂/零/负/舍入越界）再犯：
# 带波动区间的渔获必须 [lo, hi] 且 lo>=0、hi>lo；v126.4 后 <0.1kg 保留 3 位小数，
# 校验 min_weight >= 0.005（3 位小数下不会舍入成 0）
for _f in FISH_POOL:
    _sr = _f.get("size_range")
    _wr = _f.get("weight_range")
    assert _sr is None or (isinstance(_sr, (list, tuple)) and len(_sr) >= 2
                           and _sr[0] >= 0 and _sr[1] > _sr[0]), (
        f"[FISH_POOL] 渔获『{_f['name']}』size_range 非法：{_sr}（需 [lo,hi] 且 hi>lo>=0）"
    )
    assert _wr is None or (isinstance(_wr, (list, tuple)) and len(_wr) >= 2
                           and _wr[0] >= 0.005 and _wr[1] > _wr[0]), (
        f"[FISH_POOL] 渔获『{_f['name']}』weight_range 非法：{_wr}（需 [lo,hi] 且 "
        f"0.005<=lo<hi；<0.1kg 品种保留 3 位小数，lo 低于 0.005 会舍入成 0.0）"
    )
# v126.4 审计 P3：FISH_COLLECT 收藏鱼登记校验（与 FISH_POOL 同款防护，
# 防止手工双处同步漂移导致收藏鱼按中文 key 入包）
from .fishing import FISH_COLLECT  # noqa: F401  (此处延迟引入避免顶部循环)
for _cf in FISH_COLLECT:
    assert MATERIALS_BY_NAME.get(_cf["name"]) is not None, (
        f"[FISH_COLLECT] 收藏鱼『{_cf['name']}』未在 MATERIALS 登记"
    )
from .poi_pools import WISH_POOL, CAMPFIRE_FOOD_POOL, HERB_POOL  # noqa: F401
from .honor_shop import HONOR_SHOP  # noqa: F401
from .prof_config import (  # noqa: F401
    PROF_TUTORS, PROF_WAIT_BASE, DAILY_PROF_TASKS, BAG_FILTER_TYPES,
    PROF_STAMINA_COST, PROF_WAIT_DECAY, PROF_WAIT_FLOOR, MINING_KEYWORDS, PAWN_RATES,
    ENCHANT_SLOT_UNLOCK, RUNE_LEVEL_GATE, DAILY_PROF_EXP,  # noqa: F401 v125.2 B3 副业数值下沉
    PRICE_BAND, price_band, RARE_MATERIAL_PRICE,  # noqa: F401
    GATHER_MAP_MIN_LV, gather_map_min_lv,  # noqa: F401 v173 采集地图副业等级分档
)
from .item_tag_display import ITEM_TAG_DISPLAY  # noqa: F401  (v126.4 个体属性 tags 显示注册表)
from .tips import TIPS  # noqa: F401  (v127 指令随机提示库，数据驱动)

# v126.4 ITEM_TAG_DISPLAY 结构校验（fail-fast）：每条配置 line 必须是模板串或模板串列表、
# max_lines 为正整数、omit 是模板串——配置写错启动即暴露，防『物品详情』运行期静默跳过全部 tag
for _tag_type, _tag_cfg in ITEM_TAG_DISPLAY.items():
    _lines = _tag_cfg["line"] if isinstance(_tag_cfg["line"], list) else [_tag_cfg["line"]]
    assert _lines and all(isinstance(_l, str) and "{" in _l for _l in _lines), (
        f"[ITEM_TAG_DISPLAY] type={_tag_type!r} 的 line 必须是含占位符的模板串/列表"
    )
    if "max_lines" in _tag_cfg:
        assert isinstance(_tag_cfg["max_lines"], int) and _tag_cfg["max_lines"] > 0, (
            f"[ITEM_TAG_DISPLAY] type={_tag_type!r} 的 max_lines 必须是正整数"
        )
    if "omit" in _tag_cfg:
        assert isinstance(_tag_cfg["omit"], str) and "{left}" in _tag_cfg["omit"], (
            f"[ITEM_TAG_DISPLAY] type={_tag_type!r} 的 omit 必须是含 {{left}} 的模板串"
        )
from .signin_config import SIGNIN_CONFIG  # noqa: F401  (v125 签到配置数据下沉)
from .econ_config import ECON_CONFIG  # noqa: F401  (v125.1 命令层经济数值下沉)
from .skill_up import SKILL_UP  # noqa: F401  (v102.4 从 engine.py 下沉)
from .core_resources import CORE_RESOURCES  # noqa: F401  (v102.4 从 engine.py 下沉)
from .job_guide import (  # noqa: F401  (v130.2g 『职业』速查 12 职业数据表)
    JOB_GUIDE, BASE_ORDER, HIDDEN_ORDER, HIDDEN_SUCCESSORS,
    JOB_ALIASES, EXTRA_ALIASES, EXTRA_RESOURCES, BRANCH_KEY_DISPLAY, resolve_job,
)
from .stat_templates import (  # noqa: F401  (v102.5 从 core/stats.py 下沉)
    MONSTER_ROLE_BASE, MONSTER_ROLE_GROWTH, MONSTER_EXP_BASE, MONSTER_GOLD_BASE,
    EQUIP_SLOT_BASE, EQUIP_SLOT_SCALING, FIELD_TIER_MULT,  # v131 野外首领/精英难度分档
    NORMAL_HP_STAGE_MULT, BOSS_ATK_STAGE_MULT,  # v156 阶段 6 怪物/Boss 数值修复
    INSTANCE_BOSS_ATK_STAGE_MULT,  # v173.1 副本 Boss atk 段乘区（area=instance 消费）
)
from .formula_skeleton import FORMULA_SKELETON  # noqa: F401  (P2F-1 底层公式骨架参数：F2/F3/F4/F7/F9/F15/F16)

# 依赖顺序：maps 依赖 classes 等 → 在最后装配派生表/索引
from . import _assembly  # noqa: F401,E402  (执行 build_index 等)

# 让 build_index 产生的派生表也可见（_SKILL_FLAT/_MONSTER_INDEX 等）
from ._assembly import (  # noqa: F401
    _SKILL_FLAT, _MONSTER_INDEX, _FISH_INDEX, _NPC_INDEX, _SHOP_W_INDEX,
    SUBAREA_INDEX, SUBAREA_BY_MAP, SUBAREA_LINKS_INDEX,
)

# v125.2 B1：战斗主路径数据表（从 battle.py 伤害段 / engine.py 下沉，纯数据）
from .battle_config import (  # noqa: F401
    MECH_STACK_BONUS, MECH_STACK_WHITELIST, DOT_DEFS,
    DOT_BLEED_DOUBLE_HP_PCT, DOT_ADAPT_DECAY_STEP, DOT_RESIST_CAP,
    ELEMENT_REACTIONS, BOSS_ATTACK_MULTS, CONTROL_MECHS, SKILL_CC_WHITELIST,
    MECH_FULL_HP_CRIT, MECH_FROZEN_MULT, MECH_COMBO_STACKS,
    MECH_PROC_GROUPS, MECH_STAT_PASSIVES,
    # v135 锻造品质随机（19 章实装）：蓝→紫 5%（神锻名家 Lv.10 +2% → 7%）、
    # 紫→橙 5%（+2%）、橙装 2% 精良前缀（属性 ×1.15）；提升消耗 精金锭+深海水晶
    QUALITY_UPGRADE_CHANCE, QUALITY_UPGRADE_MASTER_BONUS, MASTERPIECE_CHANCE,
    QUALITY_UPGRADE_COST,
)
