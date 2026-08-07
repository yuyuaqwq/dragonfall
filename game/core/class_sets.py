# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - class_sets.py（阶段八重写，2026-08-06）

10 章五节名册套装注册：9 系列 5 件套（头盔/胸甲/护腿/鞋子/项链）。
- bonus_2：2 件属性百分比（引擎 set_bonus_2 消费）
- bonus_4_stats：4 件属性百分比（engine.set_bonus_2 叠加，>=4 件生效）
- bonus_4.effect：4 件特效（战斗触发型，保留旧结构兼容）
- bonus_5：5 件效果（数据先行；元素/抗性系统完善后战斗落地）
- 治疗加成（圣光套 2 件）由 battle 治疗段消费（bonus_2.heal 字段）

⚠️ 旧世界毕业套（CLASS_SET_THEMES 6 职业×5 阶段）已废弃：不再动态合并进 CRAFT_RECIPES，
锻造配方 = 10 章名册（craft.py）。旧 SETS 注册由 _assembly 调本函数重建。
"""

from ..data import CRAFT_RECIPES, SERIES_SETS, SETS, WT_CN
from ..core.index import pinyin_id

# 10 章五节套装效果表（5 件特效暂存数据，战斗落地待元素系统）
_SERIES_SET_BONUS = {
    "橡木": {
        "icon": "🌳", "quality": "white",
        "bonus_2": {"atk": 0.05},
        "bonus_4_stats": {"hp": 0.10},
        "bonus_5": {"crit": 0.05, "desc": "暴击 +5%"},
    },
    "铁港": {
        "icon": "⚓", "quality": "blue",
        "bonus_2": {"spd": 0.10},
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"dodge": 0.05, "desc": "闪避 +5%"},
    },
    "圣光": {
        "icon": "✨", "quality": "blue",
        "bonus_2": {"heal": 0.10},   # 治疗 +10%（battle 治疗段消费）
        "bonus_4_stats": {"def": 0.08},
        "bonus_5": {"desc": "圣光增伤 +10%（待元素系统）"},
    },
    "月语": {
        "icon": "🌙", "quality": "purple",
        "bonus_2": {"crit": 0.08},
        "bonus_4_stats": {"spd": 0.10},   # 敏捷 +10% ≈ 速度 +10%
        "bonus_5": {"desc": "月系增伤 +10%（待元素系统）"},
    },
    "霜狼": {
        "icon": "🐺", "quality": "purple",
        "bonus_2": {"def": 0.10},
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"desc": "抗寒：免疫减速（待元素系统）"},
    },
    "龙脊": {
        "icon": "🐉", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 魔抗 +10%
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"desc": "龙息增伤 +10%（待元素系统）"},
    },
    "海神": {
        "icon": "🌊", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 水抗 +10% ≈ 魔抗 +10%
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"desc": "海系增伤 +10%（待元素系统）"},
    },
    "地底": {
        "icon": "🕳️", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 暗抗 +10% ≈ 魔抗 +10%
        "bonus_4_stats": {"def": 0.08},
        "bonus_5": {"desc": "深渊增伤 +10%（待元素系统）"},
    },
    "苍穹": {
        "icon": "☁️", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 风抗 +10% ≈ 魔抗 +10%
        "bonus_4_stats": {"crit": 0.08},
        "bonus_5": {"desc": "雷系增伤 +10%（待元素系统）"},
    },
    # v87 隐藏线（10 章 10.1/10.2）
    "星尘": {
        "icon": "✨", "quality": "purple",
        "bonus_2": {"atk": 0.05, "matk": 0.05, "def": 0.05, "spd": 0.05},
        "bonus_4_stats": {"matk": 0.08},
        "bonus_5": {"desc": "星尘祝福：夜间每回合回蓝 5%（battle 消费）"},
    },
    "灰烬守卫": {
        "icon": "🔥", "quality": "orange",
        "bonus_2": {"mdef": 0.10},
        "bonus_4_stats": {"def": 0.08},
        "bonus_5": {"desc": "灰烬祝福：生命低于 30% 攻击 +20%（battle 消费）"},
    },
}


def _build_class_sets():
    """注册 10 章名册套装到 SETS（幂等：key 唯一，重复运行覆盖同名）。"""
    for series, set_name in SERIES_SETS.items():
        b = _SERIES_SET_BONUS[series]
        set_id = f"set_{pinyin_id(set_name)}"
        entry = {
            "quality": b["quality"],
            "icon": b["icon"],
            "bonus_2": dict(b["bonus_2"]),
            "name": set_name,
        }
        if b.get("bonus_4_stats"):
            entry["bonus_4_stats"] = dict(b["bonus_4_stats"])
        if b.get("bonus_5"):
            entry["bonus_5"] = dict(b["bonus_5"])
        SETS[set_id] = entry
