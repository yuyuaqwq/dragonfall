# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - portals.py"""
def portal_cost(target_map: dict) -> int:
    """传送费用：50 + 目标地图等级 * 5（低图便宜，高图贵，防滥用）"""
    return 50 + target_map.get("lv", 1) * 5

