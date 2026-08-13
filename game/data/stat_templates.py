# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - stat_templates.py（v102.5：从 core/stats.py 下沉）

怪物角色/装备部位属性模板 + 经验金币基数。公式逻辑留在 core/stats.py，
这里只放"数值表"——调数值不改代码，加角色/部位只加一行。
"""
# ============ 怪物角色属性模板（v56.2 调数值）============
# base = 1 级基础值；growth = 每级成长
MONSTER_ROLE_BASE = {
    # v105 闪避体系：speedster/dps 高闪（精准属性对抗目标），tank 不闪，Boss 低闪（不破坏战斗节奏）
    # v106 穿透体系：dps/caster/elite 带穿透（玩家防御受威胁，双向克制闭环）
    "tank":       {"hp": 60,  "atk": 8,  "def": 7,  "matk": 3,  "mdef": 6,  "spd": 6,  "dodge": 0.0},
    "dps":        {"hp": 45,  "atk": 12, "def": 4,  "matk": 4,  "mdef": 4,  "spd": 10, "dodge": 0.05, "pene_phys": 0.05},
    "caster":     {"hp": 40,  "atk": 5,  "def": 3,  "matk": 14, "mdef": 8,  "spd": 9,  "dodge": 0.03, "pene_magi": 0.05},
    "speedster":  {"hp": 35,  "atk": 9,  "def": 3,  "matk": 5,  "mdef": 4,  "spd": 16, "dodge": 0.08},
    "healer":     {"hp": 38,  "atk": 4,  "def": 3,  "matk": 12, "mdef": 8,  "spd": 8,  "dodge": 0.02},  # v86.2 治疗型（副本小怪）
    "elite":      {"hp": 95,  "atk": 14, "def": 8,  "matk": 10, "mdef": 8,  "spd": 11, "dodge": 0.05, "pene_phys": 0.03, "pene_magi": 0.03},
    "boss":       {"hp": 160, "atk": 16, "def": 10, "matk": 12, "mdef": 10, "spd": 10, "dodge": 0.03},
}
MONSTER_ROLE_GROWTH = {
    "tank":       {"hp": 20,  "atk": 2.5, "def": 1.6, "matk": 0.8, "mdef": 1.4, "spd": 0.3, "dodge": 0.0},
    "dps":        {"hp": 15,  "atk": 3.5, "def": 2.0, "matk": 1.0, "mdef": 1.2, "spd": 1.0, "dodge": 0.0},
    "caster":     {"hp": 11,  "atk": 1.2, "def": 1.0, "matk": 3.5, "mdef": 2.2, "spd": 0.9, "dodge": 0.0},
    "speedster":  {"hp": 10,  "atk": 2.6, "def": 1.0, "matk": 1.0, "mdef": 1.0, "spd": 1.8, "dodge": 0.0},
    "healer":     {"hp": 10,  "atk": 1.0, "def": 1.0, "matk": 3.0, "mdef": 1.8, "spd": 0.8, "dodge": 0.0},
    # v57 精英上调：hp 32→40、atk 5.5→6.5（鱼鱼反馈前期精英太弱，2级全力量战士无脑碾压4级精英）
    "elite":      {"hp": 40,  "atk": 6.5, "def": 2.8, "matk": 5.0, "mdef": 2.8, "spd": 1.5, "dodge": 0.0},
    "boss":       {"hp": 58,  "atk": 7.5, "def": 3.8, "matk": 6.0, "mdef": 3.4, "spd": 1.8, "dodge": 0.0},
}
# 怪物经验/金币基数（v28/v56.2 校准，公式在 core/stats.py）
MONSTER_EXP_BASE = {"tank": 8, "dps": 9, "caster": 10, "speedster": 9, "healer": 10, "elite": 24, "boss": 60}
MONSTER_GOLD_BASE = {"tank": 5, "dps": 6, "caster": 6, "speedster": 6, "healer": 6, "elite": 20, "boss": 60}

# ============ 装备部位属性模板 ============
# base = 0 级基础值；scaling = 每装备等级成长
EQUIP_SLOT_BASE = {
    "weapon":   {"atk": 3,  "matk": 3},
    "helm":     {"def": 2,  "hp": 8},
    "armor":    {"def": 4,  "hp": 15},
    "legs":     {"def": 3,  "hp": 10},
    "boots":    {"def": 1,  "spd": 2},
    "ring":     {"atk": 1,  "matk": 1},
    "necklace": {"mdef": 2, "hp": 6},
}
EQUIP_SLOT_SCALING = {
    "weapon":   {"atk": 1.0, "matk": 1.0},
    "helm":     {"def": 0.5, "hp": 3},
    "armor":    {"def": 0.9, "hp": 6},
    "legs":     {"def": 0.65, "hp": 4},
    "boots":    {"def": 0.4, "spd": 0.5},
    "ring":     {"atk": 0.35, "matk": 0.35},
    "necklace": {"mdef": 0.6, "hp": 2.5},
}
