# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - 装配（索引构建 + 派生表）

执行顺序关键：
1. 先构建派生表（百科/职业毕业套/技能扁平表等）
2. 再 build_index 构建 ID 索引
"""
from .index import _INDEXES  # noqa: F401
from ..core.index import build_index, pinyin_id, resolve, display  # noqa: F401
from .classes import CLASSES  # noqa: F401
from .maps import (
    MAPS, MAP_BY_ID, ENCY_MATERIAL_SOURCE, ENCY_MONSTER_MAP, ENCY_MAP_MONSTERS,
    MAP_CONNECTIONS, HIDDEN_MAP_UNLOCK,
)  # noqa: F401
from .subareas import SUBAREAS  # noqa: F401
from .pois import SUBAREA_POIS, POIS  # noqa: F401
# v115 网状子区域：三个区域文件（地理拆分，并行填充；stub 阶段为空 dict）
from .mesh_rooms_south import (  # noqa: F401
    EXTRA_SUBAREAS as _EXTRA_SOUTH,
    SUBAREA_LINKS as _LINKS_SOUTH,
    MESH_POI_MOUNTS as _POI_SOUTH,
)
from .mesh_rooms_west_north import (  # noqa: F401
    EXTRA_SUBAREAS as _EXTRA_WEST_NORTH,
    SUBAREA_LINKS as _LINKS_WEST_NORTH,
    MESH_POI_MOUNTS as _POI_WEST_NORTH,
)
from .mesh_rooms_east_abyss import (  # noqa: F401
    EXTRA_SUBAREAS as _EXTRA_EAST_ABYSS,
    SUBAREA_LINKS as _LINKS_EAST_ABYSS,
    MESH_POI_MOUNTS as _POI_EAST_ABYSS,
)
# v137 副本地图化：22 个副本房间连通表（只含副本内部房间，不连外部地图）
from .dungeon_links import SUBAREA_LINKS as _LINKS_DUNGEON  # noqa: F401
# v137 副本地图化：副本层 POI 挂载（key="地图id:子区域id"→POI 列表，装配合并进 SUBAREA_POIS）
from .dungeon_pois import DUNGEON_POI_MOUNTS as _POI_DUNGEON  # noqa: F401
from .instances import INSTANCES  # noqa: F401
from .instance_stage_maps import INSTANCE_STAGE_MAPS, INSTANCE_STAGE_NPCS  # noqa: F401
# v140 波2：副本通关后调查点数据（22 副本 × 3-5 个，key=inst_xxx 与 INSTANCES 对齐）
from .instance_investigation import INVESTIGATION_POINTS  # noqa: F401
# v140 波2：野外 Boss 看守宝箱（野王体系）数据表
from .wild_king_data import (  # noqa: F401
    WILD_KINGS, WILD_KING_MAPS, WILD_KING_PERIODS, WILD_KING_CHEST_TIERS,
    WILD_KING_GLOBAL_LIMIT, WILD_KING_LIFETIME_SEC, WILD_KING_LOOT_PRIORITY_SEC,
    WILD_KING_PER_PERIOD_LIMIT, WILD_KING_PER_DAY_LIMIT,
    WILD_KING_PITY_PERIODS, WILD_KING_NO_KILL_EXTRA, WILD_KING_SPAWN_HOURS,
)
from .monsters import MONSTER_SKILLS  # noqa: F401
from .skills import PLAYER_SKILLS, BRANCH_SKILLS, TUTOR_SKILLS  # noqa: F401
from .builds import BUILDS  # noqa: F401
from .equipment import (  # noqa: F401
    EQUIP_SLOTS, QUALITY, QUALITY_ORDER, WEAPON_TYPES, WEAPON_NAME_SUFFIX,
    WEAPON_FLAVOR, EQUIP_NAME_PREFIX, EQUIP_NAME_SUFFIX,
    AFFIX_COUNT, AFFIX_FALLBACK,
    QUALITY_CN, WT_CN,
)
from .items import ITEMS, MATERIALS  # noqa: F401
from .npcs import NPCS  # noqa: F401
from .wild_npcs import HIDDEN_NPCS  # noqa: F401
from .dialogues import DIALOGUES  # noqa: F401
from .quests import MAIN_QUESTS, SIDE_QUESTS, DAILY_QUESTS  # noqa: F401
from .shop import SHOP_WEAPONS  # noqa: F401
from .shop_limit import SHOP_LIMIT  # noqa: F401 v166 商店限购配置
from .factions import FACTIONS, FACTION_ORDER, REPUTATION_TIERS, AREA_FACTION, CHRONICLES  # noqa: F401
from .fishing import FISHING_SPOTS, FISH_POOL  # noqa: F401
from .enhance import ENHANCE_TABLE, MAX_ENHANCE, ENHANCE_FAIL_DROP, ENHANCE_SMITH_MAPS  # noqa: F401
from .upgrade import UPGRADE_STONE, UPGRADE_STAMINA, UPGRADE_MATERIAL_CN  # noqa: F401 v172 装备升级（真等级化，cost 阶梯）
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
from .events import EXPLORE_EVENTS, EVENT_WEIGHT_SUM  # noqa: F401
from .titles import TITLES  # noqa: F401
from .world import WORLD_EVENT_POOL, AUCTION_POOL, WORLD_BOSS_POOL  # noqa: F401
from .honor_shop import HONOR_SHOP  # noqa: F401
from .pets import PET_POOL  # noqa: F401
from .mounts import MOUNT_POOL, MOUNT_BY_KEY, MOUNT_DROP_ELITE, MOUNT_DROP_BOSS  # noqa: F401
from .alchemy import ALCHEMY_RECIPES  # noqa: F401
from .cooking import COOKING_RECIPES  # noqa: F401
from .guild import GUILD_CONFIG  # noqa: F401
from .races import RACES  # noqa: F401
from .tips import TIPS  # noqa: F401

from ..core.maps import _build_ency  # noqa: F401
from ..core.class_sets import _build_class_sets  # noqa: F401

# ---- 0.9 v115 网状子区域装配（须在任何消费 SUBAREAS 的循环/派生表之前）----
# 1) 合并 EXTRA_SUBAREAS 进 SUBAREAS（新房间 id 以 _4 起，不与旧房间冲突）
_EXTRA_ALL = {**_EXTRA_SOUTH, **_EXTRA_WEST_NORTH, **_EXTRA_EAST_ABYSS}
for _mid, _rooms in _EXTRA_ALL.items():
    SUBAREAS.setdefault(_mid, []).extend(_rooms)

# 2) 合并 SUBAREA_LINKS → SUBAREA_LINKS_INDEX（模块级名，供 core/maps 导入）
#    只含显式定义该图的网状连接；未定义图回退旧逻辑（城镇星形/野外线性）
SUBAREA_LINKS_INDEX = {}
for _links in (_LINKS_SOUTH, _LINKS_WEST_NORTH, _LINKS_EAST_ABYSS, _LINKS_DUNGEON):
    for _mid, _graph in _links.items():
        _target = SUBAREA_LINKS_INDEX.setdefault(_mid, {})
        _target.update(_graph)

# 3) 合并 MESH_POI_MOUNTS 进 SUBAREA_POIS（追加挂载，不覆盖既有挂载）
for _mkmounts in (_POI_SOUTH, _POI_WEST_NORTH, _POI_EAST_ABYSS):
    for _k, _v in _mkmounts.items():
        SUBAREA_POIS.setdefault(_k, []).extend(_v)

# 3b) v137 副本 POI 挂载：副本子区域 POI（dict 型内联 POI）合并进 SUBAREA_POIS。
#     SUBAREA_POIS 约定 value = poi id 列表（消费端 subarea_pois 返回 id，_handle_poi 从 POIS 查 dict）。
#     因此：①把每个 POI dict 注册进 POIS（key=带前缀 id，保留 type 供 inst:<type> effect）；②SUBAREA_POIS 只存 id。
for _k, _v in _POI_DUNGEON.items():
    _ids = []
    for _poi in _v:
        if isinstance(_poi, dict) and _poi.get("id"):
            POIS[_poi["id"]] = _poi
            _ids.append(_poi["id"])
        else:
            _ids.append(_poi)
    SUBAREA_POIS.setdefault(_k, []).extend(_ids)

# ---- 1. 派生表 ----
_build_ency()

_build_class_sets()

# ---- 1.5 子区域装配（02 章 13 节）：MAPS 注入 subareas + 索引 ----
SUBAREA_INDEX = {}   # "地图id:子区域id" / "子区域名" → 子区域 dict
SUBAREA_BY_MAP = {}  # 地图id → {子区域id: 子区域dict}
for _m in MAPS:
    _sas = SUBAREAS.get(_m["id"], [])
    if not _sas:
        continue
    _m["subareas"] = _sas
    SUBAREA_BY_MAP[_m["id"]] = {sa["id"]: sa for sa in _sas}
    for _sa in _sas:
        SUBAREA_INDEX[f"{_m['id']}:{_sa['id']}"] = _sa
        SUBAREA_INDEX.setdefault(f"{_m['id']}:{_sa['name']}", _sa)

# 1.6 用 MAPS 重建 MAP_BY_ID（历史手写副本与 MAPS 双源易失步；
#    统一以 MAPS 为唯一数据源，subareas 注入后两处一致）
MAP_BY_ID.clear()
MAP_BY_ID.update({_m["id"]: _m for _m in MAPS})

# ---- 1.7 副本地图装配（29 章十三节，v87.2）：INSTANCE_STAGE_MAPS merge 进 stages ----
# 层增强数据（desc/pois/npcs/secret）与战斗数据（monsters/elite/boss）分离维护，
# 装配时合并；无增强数据的层保持纯战斗层（兼容旧副本）。
for _iid, _stage_maps in INSTANCE_STAGE_MAPS.items():
    _ins = INSTANCES.get(_iid)
    if not _ins:
        continue
    _stages = _ins.get("stages") or []
    for _idx, _emap in _stage_maps.items():
        if 0 <= _idx < len(_stages):
            _stages[_idx].update(_emap)

# 层内 NPC 并入 HIDDEN_NPCS（找 NPC/对话逻辑统一从 HIDDEN_NPCS 查询）
for _nid, _npc in INSTANCE_STAGE_NPCS.items():
    _npc.setdefault("title", "副本中的神秘来客")
HIDDEN_NPCS.update(INSTANCE_STAGE_NPCS)

# ---- 2. 扁平派生表（兼容 v48 前旧结构 {职业:{技能}} 与 v48 新结构 {cls_id:{skills}}）----
_SKILL_FLAT = {}
for _cid, _cinfo in PLAYER_SKILLS.items():
    if isinstance(_cinfo, dict) and "skills" in _cinfo:
        _SKILL_FLAT.update(_cinfo["skills"])
    else:
        _SKILL_FLAT.update(_cinfo)
# v101.20 职业导师专属技能（TUTOR_SKILLS）并入扁平表 → 名字↔ID 索引可解析，
# skill_info 查询链（基础→分支→导师）最后一环才生效；重名职业技能已在 TUTOR 表剔除
for _cid, _cinfo in (TUTOR_SKILLS or {}).items():
    if isinstance(_cinfo, dict):
        _SKILL_FLAT.update(_cinfo)

# ---- 3. ID 索引（v48：key 已是 ID，一律传 name_field="name"）----
build_index("materials", MATERIALS, prefix="mat_", name_field="name")
build_index("skills", _SKILL_FLAT, prefix="sk_", name_field="name")
build_index("recipes", CRAFT_RECIPES, prefix="rec_", name_field="name")
build_index("sets", SETS, prefix="set_", name_field="name")
build_index("items", ITEMS, prefix="it_", name_field="name")  # v48：修复旧版畸形 ID（it_i___t...）
build_index("classes", CLASSES, prefix="cls_", name_field="name")
build_index("runes", RUNES, prefix="rn_", name_field="name")
build_index("monster_skills", MONSTER_SKILLS, prefix="ms_", name_field="name")
build_index("alchemy", ALCHEMY_RECIPES, prefix="al_", name_field="name")
build_index("cooking", COOKING_RECIPES, prefix="cook_", name_field="name")
build_index("races", RACES, name_field="name")  # 阶段九：种族（08 章，key 即 ID，无前缀）

# 品质：颜色档位（白/绿/蓝/紫/橙）→ ID（white/...）；稀有度文字（普通/稀有）单独查 QUALITY[name]
if any(k in QUALITY_CN for k in QUALITY):  # v48：key 已是英文 ID
    _INDEXES["quality"] = {
        "name_to_id": {QUALITY_CN[k]: k for k in QUALITY},
        "id_to_name": dict(QUALITY_CN),
    }
else:  # v48 前：key 是中文档位
    _INDEXES["quality"] = {
        "name_to_id": {v: k for k, v in QUALITY_CN.items()},
        "id_to_name": dict(QUALITY_CN),
    }
# 武器类型：key 已是英文 ID（先 build_index 建骨架，WT_CN 再覆盖中文展示映射）
build_index("weapon_types", WEAPON_TYPES)
_INDEXES["weapon_types"]["id_to_name"] = dict(WT_CN)
_INDEXES["weapon_types"]["name_to_id"] = {v: k for k, v in WT_CN.items()}

# 怪物：v87.6 内容下沉子区域——从 SUBAREAS 的 monsters/elite/boss 收集 怪物名→id（地图级仅兜底）
# v104 M24：INSTANCES stages 副本专属怪（试炼侍从/寒冰守卫/月骑士等 28 个）一并进索引，
#           且同名冲突时实例怪优先（后写覆盖，参照 build_index 的 n2i 覆盖规则）
_MONSTER_INDEX = {}
_MONSTER_ID_NAMES = {}  # v104 M24：全量 id→名（含同名冲突落败方），旧 bestiary 已存 id 仍可 display


def _collect_monster_entries(_slots_source, _slots):
    """收集 (mid, mname) 对；兼容三种槽位形态：
    - 条目列表（monsters 多怪）：[[mid, 名, role, lv, skills, drops], ...]
    - 扁平单条目（elite/boss 6 元组）：[mid, 名, role, lv, skills, drops]
    - str 单怪（理论兼容，直接跳过）
    v104 M24：原实现把扁平单条目当条目列表逐元素迭代，
    导致 elite/boss 的技能列表被误判为怪物条目（索引垃圾键 ms_* 的根源）。
    """
    for _slot in _slots:
        _ent = _slots_source.get(_slot)
        if not _ent:
            continue
        if isinstance(_ent, (tuple, list)) and _ent and isinstance(_ent[0], (tuple, list)):
            _lst = _ent  # 条目列表
        else:
            _lst = [_ent]  # 扁平单条目（或 str）
        for _t in _lst:
            if isinstance(_t, (tuple, list)) and len(_t) >= 2:
                yield _t[0], _t[1]


for _sas in SUBAREAS.values():
    for _sa in _sas:
        for _mid, _mname in _collect_monster_entries(_sa, ("monsters", "elite", "boss")):
            # 同名怪物（多地图）→ 取第一个 id，保证反查稳定
            if _mname not in _MONSTER_INDEX:
                _MONSTER_INDEX[_mname] = _mid
            _MONSTER_ID_NAMES.setdefault(_mid, _mname)
# v104 M24：实例层副本专属怪进索引——同名冲突时实例怪优先（无条件覆盖，
# 与 build_index 的 name_to_id 后写覆盖规则一致；实例内部 elite/boss 槽位排在 monsters 之后，
# 同名时实例专属的 elite/boss 变体自然胜出，不再串到子区域同名怪）
for _ins in INSTANCES.values():
    for _st in (_ins.get("stages") or []):
        if not isinstance(_st, dict):
            continue
        for _mid, _mname in _collect_monster_entries(_st, ("monsters", "elite", "boss")):
            _MONSTER_INDEX[_mname] = _mid
            _MONSTER_ID_NAMES.setdefault(_mid, _mname)
_INDEXES["monsters"] = {"name_to_id": dict(_MONSTER_INDEX),
                        "id_to_name": dict(_MONSTER_ID_NAMES)}

# 鱼：FISH_POOL 是 list，手工建索引
_FISH_INDEX = {}
for _i, _f in enumerate(FISH_POOL):
    _fid = f"fish_{pinyin_id(_f['name'])}"
    _FISH_INDEX[_f["name"]] = _fid
_INDEXES["fish"] = {"name_to_id": _FISH_INDEX,
                    "id_to_name": {v: k for k, v in _FISH_INDEX.items()}}

# NPC：key 已是 npc_xxx id，补 name 映射（含隐藏/层内 NPC）
_NPC_INDEX = {}
for _nk, _nv in list(NPCS.items()) + list(HIDDEN_NPCS.items()):
    _nn = _nv.get("name", _nk) if isinstance(_nv, dict) else _nk
    _NPC_INDEX[_nn] = _nk
_INDEXES["npcs"] = {"name_to_id": _NPC_INDEX,
                    "id_to_name": {v: k for k, v in _NPC_INDEX.items()}}

# 商店武器：SHOP_WEAPONS 值是 (名字, 类型, lv, 品质) 元组，补索引
_SHOP_W_INDEX = {}
for _mk, _mlist in SHOP_WEAPONS.items():
    for _t in _mlist:
        if isinstance(_t, (tuple, list)) and _t:
            _wn = _t[0]
            _SHOP_W_INDEX.setdefault(_wn, f"sw_{pinyin_id(_wn)}")
_INDEXES["shop_weapons"] = {"name_to_id": _SHOP_W_INDEX,
                            "id_to_name": {v: k for k, v in _SHOP_W_INDEX.items()}}
