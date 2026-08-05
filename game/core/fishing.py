# -*- coding: utf-8 -*-

import random

from ..data.fishing import FISH_POOL, FISH_WEIGHTS, FISH_RARE_BONUS


"""《剑与魔法》核心 - fishing.py"""
def roll_fish(prof_lv: int = 1):
    """钓鱼结果：返回 FISH_POOL 中的一项。

    副业等级越高，稀有鱼（金鲤/帝王鲑/珍珠/宝物）权重适度提升，
    鱼王权重单独按等级大幅提升（Lv.9+ 概率约为新手 5 倍）。
    """
    weights = list(FISH_WEIGHTS)
    if prof_lv > 1:
        bonus = 1.0
        for lv_th, mult in sorted(FISH_RARE_BONUS.items()):
            if prof_lv >= lv_th:
                bonus = mult
        # 稀有鱼（金鲤/帝王鲑/珍珠/宝物）权重乘 1 + (bonus-1)*0.3，避免总权重被撑爆
        rare_mult = 1.0 + (bonus - 1.0) * 0.3
        for idx in (1, 2, 4, 5):
            weights[idx] = FISH_WEIGHTS[idx] * rare_mult
        # 鱼王权重单独放大：直接乘 bonus
        weights[8] = FISH_WEIGHTS[8] * bonus
    return random.choices(FISH_POOL, weights=weights, k=1)[0]
