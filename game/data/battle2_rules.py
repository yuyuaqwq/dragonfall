# -*- coding: utf-8 -*-
"""游戏层战斗规则配置（battle2 引擎的注入表）——换这套 = 新游戏。

battle2 引擎不认识这些名词，只通过 config 挂载点查表折算。
引擎代码零改动；调数值/加状态/改规则全在这里。

挂载方式（游戏启动时）：
    from game.battle2 import config
    config.load_game_rules(game.data.battle2_rules)
"""
from __future__ import annotations

# ============================================================
# state key → 影响规则（cap/stat_scale/dot/on/threshold）
# ============================================================
STATE_EFFECTS: dict = {
    # ============ 通用叠层/资源（玩家侧，每层持有即生效） ============
    "zhan_yi": {
        "cap": 10,
        "stat_scale": {"atk": 0.04},          # 每层攻击 +4%
        "on_threshold": {10: {"form": "fury"}},  # 满 10 进狂暴（上层消费）
    },
    "lian_duan": {
        "cap": 10,
    },
    "rage": {
        "cap": 10,
        "stat_scale": {"dmg_mult": 0.12},     # 每层伤害 +12%
    },
    "chi": {
        "cap": 10,
    },
    "arcane": {
        "cap": 10,
    },
    "shield": {
        "cap": 10,
        "stat_scale": {"reduce": 0.03},       # 每层减伤
    },
    # ============ 对敌标记（on=target，谁打都吃） ============
    "hunt_mark": {
        "cap": 3,
        "on": "target",
        "debuff_scale": {"dmg_taken": 0.08},  # 每层承伤 +8%
    },
    "soul_mark": {
        "cap": 3,
        "on": "target",
        "debuff_scale": {"dmg_taken": 0.06},  # 每层承伤 +6%
    },
    # ============ 持续伤害 DOT（on=target） ============
    "burn": {
        "cap": 5,
        "on": "target",
        "dot": {"pct_max_hp": 0.03},          # 每层每刻掉 3% 生命
    },
    "bleed": {
        "cap": 10,
        "on": "target",
        "dot": {"type": "flat", "per_layer": 0},
    },
    "poison": {
        "cap": 5,
        "on": "target",
        "dot": {"pct_max_hp": 0.02},
    },
    "corros": {
        "cap": 5,
        "on": "target",
        "dot": {"pct_max_hp": 0.02, "dmg_type": "true"},  # 真伤 DOT
    },
    # ============ 元素印记（on=target） ============
    "fire_mark": {
        "cap": 5,
        "on": "target",
    },
    "ice_mark": {
        "cap": 5,
        "on": "target",
    },
    "thunder_mark": {
        "cap": 5,
        "on": "target",
    },
}

# ============================================================
# 名词效果 → 引擎动词动作序列
# （技能数据/怪物模板里的 effect/mech 名词，经这里翻译成引擎动词）
# ============================================================
EFFECT_ACTIONS: dict = {
    # ---- 控制类（写 target.buffs[tag]=刻数）----
    "stun":      [{"action": "control", "tag": "stun", "turns": 1}],
    "freeze":    [{"action": "control", "tag": "freeze", "turns": 1}],
    "silence":   [{"action": "control", "tag": "silence", "turns": 2}],
    "sleep":     [{"action": "control", "tag": "sleep", "turns": 1}],
    "slow":      [{"action": "control", "tag": "spd_down", "turns": 2}],
    "spd_down":  [{"action": "control", "tag": "spd_down", "turns": 2}],
    # ---- 属性增益（写 caster.buffs[key]=刻数）----
    "atk_up":    [{"action": "buff", "key": "atk_up"}],
    "dodge_buff":  [{"action": "buff", "key": "dodge_up"}],
    "spd_buff":    [{"action": "buff", "key": "spd_up"}],
    "crit_hit_buff": [{"action": "buff", "key": "crit_up"}],
    "cc_immune":    [{"action": "buff", "key": "cc_immune"}],
    # 团队/全员增益 → 自身有效键（旧 team_keys 同语义）
    "atk_all":   [{"action": "buff", "key": "atk_up"}],
    "def_all":   [{"action": "buff", "key": "def_up"}],
    "matk_all":  [{"action": "buff", "key": "matk_up_strong"}],
    "crit_all":  [{"action": "buff", "key": "crit_up"}],
    "spd_all":   [{"action": "buff", "key": "spd_up"}],
    "atk_matk_all": [{"action": "buff", "key": "atk_up"},
                     {"action": "buff", "key": "matk_up"}],
    # ---- 减伤（value 型 buff：mech_val 折算百分比 45→0.45）----
    "reduce":    [{"action": "buff", "key": "reduce", "pct_from_mech_val": True}],
    # ---- 护盾 ----
    "shield_self": [{"action": "shield", "halve": False}],
    "shield":      [{"action": "shield", "halve": True}],
    # ---- 净化 ----
    "cleanse":     [{"action": "cleanse"}],
    "cleanse_all": [{"action": "cleanse_all"}],
}

# 净化应清的控制键（buff 容器里的控制 tag）
CLEANSE_TAGS = ["stun", "silence", "freeze", "spd_down", "reduce"]

# ============================================================
# buff key → 面板属性折算规则（stats 聚合面板时查表折算）
# value 存刻数 → 属性 ×(1+层数×0.10)；spd_down 特殊 ×0.8
# ============================================================
BUFF_STAT_KEYS: dict = {
    "atk_up": "atk",
    "def_up": "def",
    "matk_up": "matk",
    "mdef_up": "mdef",
    "spd_up": "spd",
    "spd_down": "spd",  # ×0.8（SPD_DOWN_MULT）
}
SPD_DOWN_MULT = 0.8
