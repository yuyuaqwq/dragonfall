# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - class_sets.py（阶段八重写，2026-08-06）

10 章五节名册套装注册：9 系列 5 件套（头盔/胸甲/护腿/鞋子/项链）。
- bonus_2：2 件属性百分比（引擎 set_bonus_2 消费）
- bonus_4_stats：4 件属性百分比（engine.set_bonus_2 叠加，>=4 件生效）
- bonus_4.effect：4 件特效（战斗触发型，保留旧结构兼容）
- bonus_5：5 件效果（v104 起战斗落地：battle 对敌增伤/元素增伤、battle_mech 抗寒）
- 治疗加成（圣光套 2 件）由 battle 治疗段消费（bonus_2.heal 字段）

⚠️ 旧世界毕业套（CLASS_SET_THEMES 6 职业×5 阶段）已废弃：不再动态合并进 CRAFT_RECIPES，
锻造配方 = 10 章名册（craft.py）。旧 SETS 42 条仍残留在 data/sets.py（兼容旧档 set 字段，
待确认后清理）；名册套装由 _assembly 调 _build_class_sets 注册/覆盖同名 key，不删除旧数据。
"""

from ..data import CRAFT_RECIPES, SERIES_SETS, SETS, WT_CN
from ..core.index import pinyin_id

# 10 章五节套装效果表（5 件特效 v104 起战斗落地：battle.py 对敌/元素增伤、battle_mech.py 抗寒）
_SERIES_SET_BONUS = {
    "橡木": {
        "icon": "🌳", "quality": "white",
        "bonus_2": {"atk": 0.05},
        "bonus_4_stats": {"hp": 0.10},
        "bonus_5": {"crit": 0.05, "desc": "暴击＋5%"},
    },
    "铁港": {
        "icon": "⚓", "quality": "blue",
        "bonus_2": {"spd": 0.10},
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"dodge": 0.05, "desc": "闪避＋5%"},
    },
    "圣光": {
        "icon": "✨", "quality": "blue",
        # v110 审计修复：bonus_2 键原为 "heal"（heal ∉ STAT_NAMES）→ engine 属性结算
        # KeyError 崩溃（穿 2 件圣光套必现）。heal_power ∈ PCT_STATS（cap 0.5）且
        # battle.py 治疗段消费（×（1+heal_power））——"治疗+10%"设计经属性体系达成，
        # 与旧 CLASS_SET 圣徽圣愈/晨光圣愈（sets.py 均用 heal_power）同构。
        "bonus_2": {"heal_power": 0.10},
        "bonus_4_stats": {"def": 0.08},
        "bonus_5": {"desc": "圣光增伤＋10%（对暗影/亡灵系敌人）"},
    },
    "月语": {
        "icon": "🌙", "quality": "purple",
        "bonus_2": {"crit": 0.08},
        "bonus_4_stats": {"spd": 0.10},   # 敏捷 +10% ≈ 速度 +10%
        "bonus_5": {"desc": "冰系增伤＋10%（月语/海神套，冰系技能）"},
    },
    "霜狼": {
        "icon": "🐺", "quality": "purple",
        "bonus_2": {"def": 0.10},
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"desc": "抗寒：免疫减速"},
    },
    "龙脊": {
        "icon": "🐉", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 魔抗 +10%
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"desc": "龙息增伤＋10%（对龙系敌人）"},
    },
    "海神": {
        "icon": "🌊", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 水抗 +10% ≈ 魔抗 +10%
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"desc": "冰系增伤＋10%（月语/海神套，冰系技能）"},
    },
    "地底": {
        "icon": "🕳️", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 暗抗 +10% ≈ 魔抗 +10%
        "bonus_4_stats": {"def": 0.08},
        "bonus_5": {"desc": "深渊增伤＋10%（对深渊系敌人）"},
    },
    "苍穹": {
        "icon": "☁️", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 风抗 +10% ≈ 魔抗 +10%
        "bonus_4_stats": {"crit": 0.08},
        "bonus_5": {"desc": "雷系增伤＋10%（雷系技能）"},
    },
    # v93 商店装：白鹿绿装套（敏捷/闪避风格）
    "白鹿": {
        "icon": "🦌", "quality": "green",
        "bonus_2": {"dodge": 0.05},
        "bonus_4_stats": {"spd": 0.08},
        "bonus_5": {"crit": 0.03, "desc": "暴击＋3%"},
    },
    # v101.25e 商店断层补档：银铃/翡翠/迷雾蓝装套（敏捷/闪避风格）
    "银铃": {
        "icon": "🔔", "quality": "blue",
        "bonus_2": {"spd": 0.10},
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"dodge": 0.05, "desc": "闪避＋5%"},
    },
    "翡翠": {
        "icon": "💎", "quality": "blue",
        "bonus_2": {"dodge": 0.08},
        "bonus_4_stats": {"spd": 0.10},
        "bonus_5": {"crit": 0.05, "desc": "暴击＋5%"},
    },
    "迷雾": {
        "icon": "🌫️", "quality": "blue",
        "bonus_2": {"dodge": 0.08},
        "bonus_4_stats": {"mdef": 0.08},
        "bonus_5": {"desc": "迷雾增伤＋10%（对沼泽/毒腐系敌人）"},
    },
    # v87 隐藏线（10 章 10.1/10.2）
    "星尘": {
        "icon": "✨", "quality": "purple",
        "bonus_2": {"atk": 0.05, "matk": 0.05, "def": 0.05, "spd": 0.05},
        "bonus_4_stats": {"matk": 0.08},
        "bonus_5": {"desc": "星尘祝福：夜间(19:00-06:00)每回合回蓝 5%"},
    },
    "灰烬守卫": {
        "icon": "🔥", "quality": "orange",
        "bonus_2": {"mdef": 0.10},
        "bonus_4_stats": {"def": 0.08},
        "bonus_5": {"desc": "灰烬祝福：生命低于 30% 时攻击＋20%"},
    },
}


def _build_class_sets():
    """注册 10 章名册套装到 SETS(幂等：key 唯一，重复运行覆盖同名)。"""
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
