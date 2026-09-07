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
# 名词效果 → 引擎动词动作序列（第 2 步用，先空壳占位）
# 例： {"眩晕": [{"action": "control", "tag": "stun", "turns": 1}]}
# ============================================================
EFFECT_ACTIONS: dict = {}
