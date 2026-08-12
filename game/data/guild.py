# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - guild.py"""
GUILD_CONFIG = {
    "create_cost": 1000,       # 创建公会金币（策划 11 章 3.1：1000 金币）
    "create_level": 30,        # 创建公会等级要求（策划 11 章 3.1：Lv.30）
    "sign_exp": 20,            # 公会签到：公会经验
    "sign_contribute": 10,     # 公会签到：个人贡献
    "sign_gold": 50,           # 公会签到：个人金币
    "task_exp": 40,            # 公会任务：公会经验
    "task_contribute": 20,     # 公会任务：个人贡献
    "task_gold": 100,          # 公会任务：个人金币
    "kill_task": 5,            # 公会任务击杀数
    "donate_items": 3,         # 公会捐献：上交材料份数（策划 11 章 4 种任务：讨伐/捐献/金币/副本 → 简化落地：讨伐＋捐献）
    "exp_bonus_per_level": 0.01,  # 每级公会经验加成
    "max_bonus": 0.20,         # 公会经验加成上限
}

