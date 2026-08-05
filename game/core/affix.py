# -*- coding: utf-8 -*-

from .stats import equip_stats
import random

from ..data import AFFIX_COUNT, AFFIX_FALLBACK, AFFIX_POOL, AFFIX_RATIO


"""《剑与魔法》数据层 - affix.py"""
def _affix_base_value(slot: str, lv: int, stat: str) -> int:
    """词条基准值：优先部位白板属性，无则用保底模板"""
    base = equip_stats(slot, lv, "white")
    if base.get(stat, 0) > 0:
        return base[stat]
    fb = AFFIX_FALLBACK.get(stat, (2, 1.0))
    return int(fb[0] + fb[1] * lv)

def roll_affixes(slot: str, lv: int, quality: str) -> list:
    """按品质生成词条列表 [{'stat': ..., 'value': ...}, ...]"""
    n = AFFIX_COUNT.get(quality, 0)
    if isinstance(n, (tuple, list)):  # json 转换后 tuple 变 list
        n = random.randint(n[0], n[1])
    if not n:
        return []
    ratio = AFFIX_RATIO.get(quality, 0.25)
    chosen = random.sample(AFFIX_POOL, min(n, len(AFFIX_POOL)))
    affixes = []
    for stat in chosen:
        if stat in ("crit", "dodge"):
            v = round(random.uniform(0.01, 0.025), 3)  # 1% ~ 2.5%
        else:
            base = _affix_base_value(slot, lv, stat)
            v = int(base * ratio * random.uniform(0.8, 1.2))
            v = max(1, v)
        affixes.append({"stat": stat, "value": v})
    return affixes

