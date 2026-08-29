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
        # v126 数值下沉：5 件对敌增伤条件（敌方名字关键词）从数据声明，battle 查表消费
        "bonus_5_cond": {"enemy_contains": ["暗", "影", "亡", "鬼", "骨", "骷髅"],
                         "dmg_mult": 1.10, "tag": "✨圣光克暗"},
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
        "bonus_5_cond": {"enemy_contains": ["龙"],
                         "dmg_mult": 1.10, "tag": "🐉龙息追猎"},
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
        "bonus_5_cond": {"enemy_contains": ["深渊"],
                         "dmg_mult": 1.10, "tag": "🕳️深渊共鸣"},
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
        "bonus_5_cond": {"enemy_contains": ["沼泽", "毒", "腐", "瘴"],
                         "dmg_mult": 1.10, "tag": "🌫️迷雾侵染"},
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
        "bonus_5_cond": {"player_hp_below": 0.30,
                         "dmg_mult": 1.20, "tag": "🔥灰烬之怒"},
    },

    # ===== v136 Phase6 合并: CLASS_SET_BONUS (18 条) =====
    '铁皮': {'class': 'cls_zhan_shi', 'icon': '🛡️', 'quality': 'blue', 'bonus_2': {'atk': 0.08, 'def': 0.08}, 'bonus_4_stats': {'def': 0.1}, 'bonus_4': {'effect': 'pierce', 'chance': 0.3, 'desc': '攻击 30% 概率破甲(敌方防御减半 2 回合)'}},
    '精铁': {'class': 'cls_zhan_shi', 'icon': '🛡️', 'quality': 'blue', 'bonus_2': {'atk': 0.08, 'def': 0.08}, 'bonus_4_stats': {'def': 0.1}, 'bonus_4': {'effect': 'pierce', 'chance': 0.3, 'desc': '攻击 30% 概率破甲(敌方防御减半 2 回合)'}},
    '百炼': {'class': 'cls_zhan_shi', 'icon': '⚔️', 'quality': 'purple', 'bonus_2': {'atk': 0.08, 'def': 0.08}, 'bonus_4_stats': {'def': 0.1}, 'bonus_4': {'effect': 'pierce', 'chance': 0.3, 'desc': '攻击 30% 概率破甲(敌方防御减半 2 回合)'}},
    '学徒': {'class': 'cls_fa_shi', 'icon': '🔮', 'quality': 'blue', 'bonus_2': {'matk': 0.08, 'cdr': 0.05}, 'bonus_4_stats': {'matk': 0.1}, 'bonus_4': {'effect': 'thunder', 'chance': 0.25, 'desc': '攻击 25% 概率追加一次雷击(60% 攻击伤害)'}},
    '符文': {'class': 'cls_fa_shi', 'icon': '🔮', 'quality': 'blue', 'bonus_2': {'matk': 0.08, 'cdr': 0.05}, 'bonus_4_stats': {'matk': 0.1}, 'bonus_4': {'effect': 'thunder', 'chance': 0.25, 'desc': '攻击 25% 概率追加一次雷击(60% 攻击伤害)'}},
    '秘法': {'class': 'cls_fa_shi', 'icon': '✨', 'quality': 'purple', 'bonus_2': {'matk': 0.08, 'cdr': 0.05}, 'bonus_4_stats': {'matk': 0.1}, 'bonus_4': {'effect': 'thunder', 'chance': 0.25, 'desc': '攻击 25% 概率追加一次雷击(60% 攻击伤害)'}},
    '布衣': {'class': 'cls_mu_shi', 'icon': '☀️', 'quality': 'blue', 'bonus_2': {'heal_power': 0.08, 'mdef': 0.05}, 'bonus_4_stats': {'mdef': 0.1}, 'bonus_4': {'effect': 'regen', 'chance': 1.0, 'desc': '每回合开始回复 5% 生命'}},
    '祝福': {'class': 'cls_mu_shi', 'icon': '☀️', 'quality': 'blue', 'bonus_2': {'heal_power': 0.08, 'mdef': 0.05}, 'bonus_4_stats': {'mdef': 0.1}, 'bonus_4': {'effect': 'regen', 'chance': 1.0, 'desc': '每回合开始回复 5% 生命'}},
    '圣堂': {'class': 'cls_mu_shi', 'icon': '⛪', 'quality': 'purple', 'bonus_2': {'heal_power': 0.08, 'mdef': 0.05}, 'bonus_4_stats': {'mdef': 0.1}, 'bonus_4': {'effect': 'regen', 'chance': 1.0, 'desc': '每回合开始回复 5% 生命'}},
    '猎手': {'class': 'cls_you_xia', 'icon': '🏹', 'quality': 'blue', 'bonus_2': {'spd': 0.08, 'crit': 0.03}, 'bonus_4_stats': {'spd': 0.08}, 'bonus_4': {'effect': 'dodge_set', 'stats': {'dodge': 0.1}, 'chance': 1.0, 'desc': '闪避率＋10%'}},
    '风行': {'class': 'cls_you_xia', 'icon': '🏹', 'quality': 'blue', 'bonus_2': {'spd': 0.08, 'crit': 0.03}, 'bonus_4_stats': {'spd': 0.08}, 'bonus_4': {'effect': 'dodge_set', 'stats': {'dodge': 0.1}, 'chance': 1.0, 'desc': '闪避率＋10%'}},
    '暗夜': {'class': 'cls_you_xia', 'icon': '🏹', 'quality': 'purple', 'bonus_2': {'spd': 0.08, 'crit': 0.03}, 'bonus_4_stats': {'spd': 0.08}, 'bonus_4': {'effect': 'dodge_set', 'stats': {'dodge': 0.1}, 'chance': 1.0, 'desc': '闪避率＋10%'}},
    '轻影': {'class': 'cls_ci_ke', 'icon': '🗡️', 'quality': 'blue', 'bonus_2': {'crit': 0.05, 'atk': 0.08}, 'bonus_4_stats': {'crit': 0.05}, 'bonus_4': {'effect': 'execute', 'chance': 1.0, 'desc': '对生命低于 30% 的敌人额外造成 25% 伤害'}},
    '夜行': {'class': 'cls_ci_ke', 'icon': '🗡️', 'quality': 'blue', 'bonus_2': {'crit': 0.05, 'atk': 0.08}, 'bonus_4_stats': {'crit': 0.05}, 'bonus_4': {'effect': 'execute', 'chance': 1.0, 'desc': '对生命低于 30% 的敌人额外造成 25% 伤害'}},
    '阴影': {'class': 'cls_ci_ke', 'icon': '🗡️', 'quality': 'purple', 'bonus_2': {'crit': 0.05, 'atk': 0.08}, 'bonus_4_stats': {'crit': 0.05}, 'bonus_4': {'effect': 'execute', 'chance': 1.0, 'desc': '对生命低于 30% 的敌人额外造成 25% 伤害'}},
    '行者': {'class': 'cls_wu_seng', 'icon': '🥋', 'quality': 'blue', 'bonus_2': {'atk': 0.08, 'def': 0.05}, 'bonus_4_stats': {'hp': 0.1}, 'bonus_4': {'effect': 'lifesteal_set', 'chance': 0.3, 'desc': '攻击 30% 概率吸血 15% 伤害'}},
    '石拳': {'class': 'cls_wu_seng', 'icon': '🥋', 'quality': 'blue', 'bonus_2': {'atk': 0.08, 'def': 0.05}, 'bonus_4_stats': {'hp': 0.1}, 'bonus_4': {'effect': 'lifesteal_set', 'chance': 0.3, 'desc': '攻击 30% 概率吸血 15% 伤害'}},
    '壁槌': {'class': 'cls_wu_seng', 'icon': '🥋', 'quality': 'purple', 'bonus_2': {'atk': 0.08, 'def': 0.05}, 'bonus_4_stats': {'hp': 0.1}, 'bonus_4': {'effect': 'lifesteal_set', 'chance': 0.3, 'desc': '攻击 30% 概率吸血 15% 伤害'}},
    # ===== v136 Phase6 区域套（5 资料片通用，无 class 字段=不打职业折扣）=====
    '护林': {'icon': '🌳', 'quality': 'white', 'bonus_2': {'def': 0.05}, 'bonus_4_stats': {'hp': 0.08}, 'bonus_4': {'effect': 'regen', 'desc': '每回合开始回复 3% 生命'}},
    '渡口': {'icon': '⛵', 'quality': 'blue', 'bonus_2': {'spd': 0.05}, 'bonus_4_stats': {'mdef': 0.06}, 'bonus_4': {'effect': 'dodge_set', 'stats': {'dodge': 0.05}, 'chance': 1.0, 'desc': '闪避率＋5%'}},
    '巡林': {'icon': '🌲', 'quality': 'blue', 'bonus_2': {'dodge': 0.05}, 'bonus_4_stats': {'spd': 0.05}, 'bonus_4': {'effect': 'dodge_set', 'stats': {'dodge': 0.06}, 'chance': 1.0, 'desc': '闪避率＋6%'}},
    '霜猎': {'icon': '🐺', 'quality': 'purple', 'bonus_2': {'element_ice': 0.05}, 'bonus_4_stats': {'atk': 0.05}, 'bonus_4': {'effect': 'execute', 'chance': 1.0, 'desc': '对生命低于 30% 的敌人额外造成 20% 伤害'}},
    '龙裔': {'icon': '🐉', 'quality': 'purple', 'bonus_2': {'mdef': 0.05}, 'bonus_4_stats': {'atk': 0.06}, 'bonus_4': {'effect': 'pierce', 'chance': 0.3, 'desc': '攻击 30% 概率破甲(敌方防御减半 2 回合)'}},
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
        # v136 Phase6：职业套装归属（本职业 100% / 非本职业 60% 职业折扣）
        if b.get("class"):
            entry["class"] = b["class"]
        if b.get("bonus_4_stats"):
            entry["bonus_4_stats"] = dict(b["bonus_4_stats"])
        if b.get("bonus_4"):
            entry["bonus_4"] = dict(b["bonus_4"])
        if b.get("bonus_5"):
            entry["bonus_5"] = dict(b["bonus_5"])
        if b.get("bonus_5_cond"):
            # v126 数值下沉：5 件战斗条件（enemy_contains/player_hp_below/dmg_mult/tag）随套装注册
            entry["bonus_5_cond"] = dict(b["bonus_5_cond"])
        SETS[set_id] = entry
