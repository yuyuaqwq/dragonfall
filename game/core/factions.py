# -*- coding: utf-8 -*-

from ..data import REPUTATION_TIERS


"""《剑与魔法》数据层 - factions.py"""
def faction_reputation_tier(points: int) -> str:
    """声望点数 → 等级名"""
    name = "陌生"
    for th, n in REPUTATION_TIERS:
        if points >= th:
            name = n
    return name

