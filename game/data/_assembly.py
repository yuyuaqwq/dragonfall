# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - 装配（索引构建 + 派生表）

执行顺序关键：
1. 先构建派生表（百科/职业毕业套/技能扁平表等）
2. 再 build_index 构建 ID 索引
"""
from .index import _INDEXES  # noqa: F401
from ..core.index import build_index, pinyin_id, resolve, display  # noqa: F401
from .classes import CLASSES  # noqa: F401
from .maps import (
    MAPS, MAP_BY_ID, ENCY_MATERIAL_SOURCE, ENCY_MONSTER_MAP, ENCY_MAP_MONSTERS,
    MAP_AREAS, AREA_ENTRY, MAP_CONNECTIONS, HIDDEN_MAP_UNLOCK,
)  # noqa: F401
from .subareas import SUBAREAS  # noqa: F401
from .instances import INSTANCES  # noqa: F401
from .instance_stage_maps import INSTANCE_STAGE_MAPS, INSTANCE_STAGE_NPCS  # noqa: F401
from .monsters import MONSTER_SKILLS  # noqa: F401
from .skills import PLAYER_SKILLS, BRANCH_SKILLS  # noqa: F401
from .builds import BUILDS  # noqa: F401
from .equipment import (  # noqa: F401
    EQUIP_SLOTS, QUALITY, QUALITY_ORDER, WEAPON_TYPES, WEAPON_NAME_SUFFIX,
    WEAPON_FLAVOR, EQUIP_NAME_PREFIX, EQUIP_NAME_SUFFIX,
    AFFIX_COUNT, AFFIX_RATIO, AFFIX_POOL, AFFIX_FALLBACK,
    QUALITY_CN, WT_CN,
)
from .items import ITEMS, MATERIALS  # noqa: F401
from .npcs import NPCS  # noqa: F401
from .wild_npcs import HIDDEN_NPCS  # noqa: F401
from .dialogues import DIALOGUES  # noqa: F401
from .quests import MAIN_QUESTS, SIDE_QUESTS, DAILY_QUESTS  # noqa: F401
from .shop import SHOP_ITEMS, SHOP_WEAPONS  # noqa: F401
from .factions import FACTIONS, FACTION_ORDER, REPUTATION_TIERS, AREA_FACTION, CHRONICLES  # noqa: F401
from .fishing import FISHING_SPOTS, FISH_POOL  # noqa: F401
from .enhance import ENHANCE_TABLE, MAX_ENHANCE, ENHANCE_FAIL_DROP, ENHANCE_SMITH_MAPS  # noqa: F401
from .sets import SET_THEMES, SET_CHANCE, SETS, CLASS_SET_STAGES, CLASS_SET_THEMES  # noqa: F401
from .craft import CRAFT_RECIPES, CRAFT_RECIPE_ALIASES  # noqa: F401
from .enchant import (  # noqa: F401
    ENCHANT_SLOTS, ENCHANT_RECIPES, ENCHANT_CRIT_CHANCE, ENCHANT_MAX_VALUE,
    ENCHANT_STONES, ENCHANT_EFFECT_NAMES,
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

from ..core.maps import _build_ency  # noqa: F401
from ..core.class_sets import _build_class_sets  # noqa: F401

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
# 武器类型：key 已是英文 ID
build_index("weapon_types", WEAPON_TYPES)
_INDEXES["weapon_types"]["id_to_name"] = dict(WT_CN)
_INDEXES["weapon_types"]["name_to_id"] = {v: k for k, v in WT_CN.items()}

# 怪物：v87.6 内容下沉子区域——从 SUBAREAS 的 monsters/elite/boss 收集 怪物名→id（地图级仅兜底）
_MONSTER_INDEX = {}


def _collect_monster_entries(_slots_source, _slots):
    """收集 (mid, mname) 对；兼容 str(单怪)与 list(多怪)。"""
    for _slot in _slots:
        _ent = _slots_source.get(_slot)
        if not _ent:
            continue
        _lst = _ent if isinstance(_ent, list) else [_ent]
        for _t in _lst:
            if isinstance(_t, (tuple, list)) and len(_t) >= 2:
                yield _t[0], _t[1]


for _sas in SUBAREAS.values():
    for _sa in _sas:
        for _mid, _mname in _collect_monster_entries(_sa, ("monsters", "elite", "boss")):
            # 同名怪物（多地图）→ 取第一个 id，保证反查稳定
            if _mname not in _MONSTER_INDEX:
                _MONSTER_INDEX[_mname] = _mid
# 兜底：无子区域的地图级内容（当前全图都有子区域，此处为空）
for _m in MAPS:
    for _mid, _mname in _collect_monster_entries(_m, ("monsters", "elite", "boss")):
        if _mname not in _MONSTER_INDEX:
            _MONSTER_INDEX[_mname] = _mid
_INDEXES["monsters"] = {"name_to_id": dict(_MONSTER_INDEX),
                        "id_to_name": {v: k for k, v in _MONSTER_INDEX.items()}}

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
