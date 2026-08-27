# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - stat_templates.py（v102.5：从 core/stats.py 下沉）

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
    # v131 数值重设计（2026-08-27 鱼鱼拍板）：怪 HP×2 / 防御×2~4.5 / 攻击×1.4，
    # 攻防比收敛 r≈1.6~2.0（防御重新有意义），跨5级裸装全胜→必败；boss 血量×2.5（副本长盘化）。
    "tank":       {"hp": 36,  "atk": 3.5, "def": 4.0, "matk": 0.8, "mdef": 2.8, "spd": 0.3, "dodge": 0.0},
    "dps":        {"hp": 30,  "atk": 5.0, "def": 5.0, "matk": 1.0, "mdef": 2.4, "spd": 1.0, "dodge": 0.0},
    "caster":     {"hp": 22,  "atk": 1.8, "def": 3.5, "matk": 5.0, "mdef": 4.0, "spd": 0.9, "dodge": 0.0},
    "speedster":  {"hp": 22,  "atk": 3.5, "def": 4.5, "matk": 1.0, "mdef": 2.0, "spd": 1.8, "dodge": 0.0},
    "healer":     {"hp": 20,  "atk": 1.5, "def": 3.0, "matk": 4.0, "mdef": 3.0, "spd": 0.8, "dodge": 0.0},
    # v57 精英上调：hp 32→40、atk 5.5→6.5（鱼鱼反馈前期精英太弱，2级全力量战士无脑碾压4级精英）
    # v131 精英 hp 40→70、def 2.8→5.5（配合 FIELD_TIER_MULT 分档 → 蓝+5 单刷 20~35 轮）
    "elite":      {"hp": 70,  "atk": 6.5, "def": 5.5, "matk": 5.0, "mdef": 4.5, "spd": 1.5, "dodge": 0.0},
    # v131 boss hp 58→145（副本 Boss 保底大几十轮策略长盘；配合实例 hp_mult 表 → 4人 100~150 轮）
    "boss":       {"hp": 145, "atk": 7.5, "def": 3.8, "matk": 6.0, "mdef": 3.4, "spd": 1.8, "dodge": 0.0},
}
# 怪物经验/金币基数（v28/v56.2 校准，公式在 core/stats.py）
MONSTER_EXP_BASE = {"tank": 8, "dps": 9, "caster": 10, "speedster": 9, "healer": 10, "elite": 24, "boss": 60}

# v131 野外首领/精英难度分档（2026-08-27 鱼鱼拍板，build_monster 消费）：
#   野外战斗无组队血量缩放（组队 DPS≈人数倍）→ 精英/野外 Boss 按团队/高挑战定标；
#   与 MONSTER_MODS 个体 mod（±5%~20%）叠乘生效；副本 Boss 不消费本表（走 instances.hp_mult）。
#   目标：野外精英 蓝+5 单刷 20~35 轮；野外 Boss 4 人组队 60~100 轮（单刷=送死）。
FIELD_TIER_MULT = {
    "elite": ((30, 8.0), (60, 3.0), (999, 1.5)),     # ≤30 ×8 / 31-60 ×3 / 61+ ×1.5
    "boss":  ((30, 15.0), (60, 9.0), (999, 6.2)),    # ≤30 ×15 / 31-60 ×9 / 61+ ×6.2（v131 标定：4人组队 60~100 轮全达标）
}
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
