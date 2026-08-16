# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - signin_config.py（签到配置数据下沉）

原 hardcode 在 commands/misc.py signin（v87 每日运势 + 连续签到奖励），
数值下沉后：调整签到数值只改此文件，零代码改动。
"""
SIGNIN_CONFIG = {
    "base_gold": 20,            # 基础金币
    "streak_gold_step": 5,      # 连续签到每 1 天 +5 金币
    "festival_mult": 2,         # 节日庆典签到奖励倍率
    "fortune_bad_th": 0.15,     # 每日运势阈值：roll < 0.15 → 小凶（当日金币 -10%）
    "fortune_good_th": 0.55,    # roll < 0.55 → 平；≥ 0.55 → 大吉（当日经验 +10%）
    "week_quality_weights": [55, 35, 10],  # 每 7 天额外奖励品质权重（green/blue/purple）
}
