# -*- coding: utf-8 -*-

from ..data import REPUTATION_TIERS


"""奥兰迪亚·余烬纪年核心逻辑层 - factions 声望 tier"""
def faction_reputation_tier(points: int) -> str:
    """声望点数 → 等级名"""
    name = "陌生"
    for th, n in REPUTATION_TIERS:
        if points >= th:
            name = n
    return name

