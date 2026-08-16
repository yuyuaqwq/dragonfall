# -*- coding: utf-8 -*-
"""战斗主路径数据表（v125.2 B1 数据下沉）——纯数据，无逻辑、无 IO。

从 game/battle.py 伤害结算段 / game/engine.py 下沉的数值与白名单。
消费端：
  - game/battle.py：_mech_stack_bonus / _apply_mech_gain / _tick_dots /
    _enemy_stats（Boss 攻乘区）/ _apply_mech_effect（控制白名单）/
    伤害主路径 mech 特判（满血必暴/碎冰/连击/proc 归属/stat 归属）
  - game/engine.py：element_reaction 查 ELEMENT_REACTIONS（对外接口不变）

调数值只改本文件。
"""
# ============================================================
# 叠层型机制每层增伤（_mech_stack_bonus）：倍率 = 1 + 层数 × 值
# ============================================================
MECH_STACK_BONUS = {
    "rage": 0.12,        # 狂暴：每层 +12%（5 层 +60%）
    "shadow": 0.12,      # 影袭：每层 +12%
    "chi": 0.12,         # 气力：每层 +12%
    "spellblade": 0.08,  # 魔剑士·魔能：每层 +8%
}

# 增益类技能可叠层 mech 白名单（_apply_mech_gain；v59 封顶语义，共 14 个）
MECH_STACK_WHITELIST = (
    "rage", "shield", "wind", "shadow", "chi", "bless", "judge",
    "iron", "mark", "burn", "poison", "freeze", "arcane", "spellblade",
)

# ============================================================
# DOT 混合公式（_tick_dots，契约 §2.2）：
#   每层伤害 = (atk×atk + matk×matk + max_hp×hp) × 层数 × mult × (1 - 总抗)
# ============================================================
DOT_DEFS = {
    "poison": {"atk": 0.5, "matk": 0.0, "hp": 0.015},  # 毒：atk×0.5 + max_hp×1.5%
    "burn":   {"atk": 0.0, "matk": 0.4, "hp": 0.01},   # 灼烧：matk×0.4 + max_hp×1%
    "bleed":  {"atk": 0.6, "matk": 0.0, "hp": 0.015},  # 流血：atk×0.6 + max_hp×1.5%
}
DOT_BLEED_DOUBLE_HP_PCT = 0.30  # 放血：目标当前生命 <30% 时流血伤害 ×2（处决线）
DOT_ADAPT_DECAY_STEP = 0.04     # 适应回落：poison/burn 最近 2 回合未再叠层 → 耐受 -4%
DOT_RESIST_CAP = 0.95           # 总抗上限：min(0.95, dot_res + 适应 adapt)

# ============================================================
# 元素反应（v2.0，12 章 3.1，严格按策划案表；从 engine.py 迁移，结构不变）
# 当前系 × 目标印记 → 反应：
#   蒸发 = 火印(目标) + 冰(当前系) → 增伤 30%，清除印记
#   超载 = 雷印(目标) + 火(当前系) → 全体 120% 伤害，清除印记
#   冻结 = 冰印(目标) + 水(当前系) → 冻结 1 回合（法师暂无水系技能，预留）
#   感电 = 雷印(目标) + 雷(当前系) → 连击 +1，印记保留
# ============================================================
ELEMENT_REACTIONS = {
    ("ice", "fire_mark"):        {"name": "蒸发", "mult": 1.30, "clear": True, "extra": ""},
    ("fire", "thunder_mark"):    {"name": "超载", "mult": 1.00, "clear": True, "extra": "aoe"},
    ("water", "ice_mark"):       {"name": "冻结", "mult": 1.00, "clear": True, "extra": "freeze"},
    ("thunder", "thunder_mark"): {"name": "感电", "mult": 1.00, "clear": False, "extra": "chain"},
}

# ============================================================
# Boss 攻强乘区（_enemy_stats）：enrage/phase/low_hp/pv_broken/stacks
# 叠加后 atk/matk 不得超过基础 × cap（v120 总帽）
# ============================================================
BOSS_ATTACK_MULTS = {
    "enraged": 1.35,     # v58 狂暴：血量 <30% 触发后攻击 +35%
    "phase_step": 0.20,  # v83 多阶段：每阶段 +20%
    "low_hp": 1.25,      # v116.1 条件反制·玩家低血追击 +25%
    "pv_broken": 1.30,   # v116.1 条件反制·玩家大招反扑 +30%
    "stack_step": 0.08,  # v83 叠层强化：每层 +8%
    "cap": 3.0,          # v120 总帽：基础 atk/matk ×3.0
}

# ============================================================
# 控制白名单
# ============================================================
# 控制类 mech 白名单（_apply_mech_effect：Boss 控制时长减半 / 打断蓄力）
CONTROL_MECHS = ("stun", "freeze", "silence")
# 技能 cc 字段白名单（v63：独立于 mech 叠层的额外控制效果——眩晕/沉默/净化）
SKILL_CC_WHITELIST = ("stun", "silence", "cleanse")

# ============================================================
# mech 特判收敛（伤害结算主路径查表，v125.2 B1）
# ============================================================
# 满血必暴：mech 命中且目标满血 → 必定暴击（影袭）
MECH_FULL_HP_CRIT = ("shadow",)
# 碎冰增伤：mech 命中且目标冻结中 → 伤害 ×值（冰霜）
MECH_FROZEN_MULT = {"freeze": 1.5}
# 连击追加：mech 命中 → 连击次数 += 该 mech 自身层数（风印）
MECH_COMBO_STACKS = ("wind",)
# proc 型被动 mech 归属：被动组名 → 命中即生效的 mech 集合（毒系/奥术系）
MECH_PROC_GROUPS = {
    "poison_dmg": ("poison", "poison_burst"),
    "arcane_dmg": ("arcane",),
}
# stat 型被动 mech 归属：被动 stat 键 → 对应 mech（命中该 mech 才生效）
MECH_STAT_PASSIVES = {
    "judge": "judge",    # 审判之心
    "shadow": "shadow",  # 暗影之心
}
