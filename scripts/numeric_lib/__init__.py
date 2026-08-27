# -*- coding: utf-8 -*-
"""numeric_lib —— 多维度数值计算工具集（v131 通用化沉淀，2026-08-27）

背景：v131 数值分析发现 scripts/numeric_calibration.py 的玩家模型"残疾"——
漏自由属性点/tier/词条/附魔/药水/真实技能轴，导致副本 Boss 结论 110~315 轮
是假象（真实玩家每轮输出 5~6 倍）。本包把 v2 模型（scripts/_tmp_calib_v2.py，
真实引擎面板+技能轴逐职验证误差≤3.2%）提炼为**可复用、可扩展、带自检**的
通用工具集，供校准/胜率矩阵/方案预演/档位对比统一使用。

设计原则：
  1. 默认 = 真实玩家（全乘区开启），不再出现"残疾模型默认输出"；
  2. 每个乘区都是独立开关（PlayerOptions），关掉即可做归因分析；
  3. 怪物曲线 override 用上下文管理器，预演不污染进程状态；
  4. 所有输出统一走 report（markdown 表格 / JSON），可 diff 对比；
  5. 自带门禁自检 tests/test_numeric_toolkit.py（模型 vs 引擎误差/归因/公式）。
"""
from .env import setup_env
from .constants import (
    CLASSES, TIER_GROWTH, ATTR_PER_LV, DEFAULT_ATTR_PTS,
    POTION_ATK, POTION_MATK, AFFIX_MULT, ENCHANT_CRIT, TEAM_BUFF,
    ROTATIONS, ASSASSIN_COND_WEIGHT, DEF_DOWN_SKILLS,
    BOSS_HP_MULT, TEAM_PER_PLAYER_ADD,
)
from .gear import make_gear, gear_loadout
from .player import PlayerOptions, build_player, per_action_dmg, dmg_budget, panel
from .monster import build, panel as monster_panel, curve_override
from .team import boss_hp, team_rounds, team_net_mult, team_matrix, instance_details
from .battle import win_rate, panel as battle_panel
from .report import md_table, md_lines, to_json, diff_tables

__all__ = [
    "setup_env", "CLASSES", "TIER_GROWTH", "ATTR_PER_LV", "DEFAULT_ATTR_PTS",
    "POTION_ATK", "POTION_MATK", "AFFIX_MULT", "ENCHANT_CRIT", "TEAM_BUFF",
    "ROTATIONS", "ASSASSIN_COND_WEIGHT", "DEF_DOWN_SKILLS",
    "BOSS_HP_MULT", "TEAM_PER_PLAYER_ADD",
    "make_gear", "gear_loadout", "LOADOUTS",
    "PlayerOptions", "build_player", "per_action_dmg", "dmg_budget", "panel",
    "build", "monster_panel", "curve_override",
    "boss_hp", "team_rounds", "team_net_mult", "team_matrix", "instance_details",
    "win_rate", "battle_panel",
    "md_table", "md_lines", "to_json", "diff_tables",
]