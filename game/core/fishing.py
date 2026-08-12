# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心 - fishing.py（16 章品质垂钓 v2.0）

roll 流程：垂钓等级查五档权重表（中间等级线性插值）→ 过滤钓点禁出档位 → 选档位
→ 档位内按品种权重选（过滤品种限定水域）。
"""
import random

from ..data.fishing import (
    FISHING_SPOTS,
    FISH_POOL,
    FISH_QUALITY_WEIGHTS,
    FISH_COLLECT,
)
from ..data import FISH_QUALITY_ORDER  # v101.25i6 别名：= QUALITY_ORDER


def _quality_weights(prof_lv: int) -> list:
    """垂钓等级 → 五档权重(Lv.1/3/5/7/9 查表，中间等级线性插值)。"""
    lv = max(1, min(9, int(prof_lv)))
    keys = sorted(FISH_QUALITY_WEIGHTS)
    if lv <= keys[0]:
        return list(FISH_QUALITY_WEIGHTS[keys[0]])
    if lv >= keys[-1]:
        return list(FISH_QUALITY_WEIGHTS[keys[-1]])
    for a, b in zip(keys, keys[1:]):
        if a <= lv <= b:
            wa = FISH_QUALITY_WEIGHTS[a]
            wb = FISH_QUALITY_WEIGHTS[b]
            t = (lv - a) / (b - a)
            return [wa[i] + (wb[i] - wa[i]) * t for i in range(len(wa))]
    return list(FISH_QUALITY_WEIGHTS[keys[0]])


def roll_fish(prof_lv: int = 1, spot_id: str | None = None):
    """垂钓结果：返回 FISH_POOL 中的一项。

    prof_lv: 垂钓副业等级（1-9）
    spot_id: 钓点地图 ID（FISHING_SPOTS 的 key）；钓点禁出档位权重清零，
             品种限定水域（spots 字段）不满足时跳过。
    """
    spot = FISHING_SPOTS.get(spot_id) if spot_id else None
    ban = set(spot.get("ban_quality", [])) if spot else set()
    weights = _quality_weights(prof_lv)
    for i, q in enumerate(FISH_QUALITY_ORDER):
        if q in ban:
            weights[i] = 0.0
    quality = random.choices(FISH_QUALITY_ORDER, weights=weights, k=1)[0]

    def _match(f):
        return f["quality"] == quality and (
            not f.get("spots") or (spot_id and spot_id in f["spots"])
        )

    pool = [f for f in FISH_POOL if _match(f)]
    if not pool:
        # 防御性兜底：先去掉 spots 限定重试（如新钓点蓝档无全水域品种），再退全品质池
        pool = [f for f in FISH_POOL if f["quality"] == quality]
    return random.choices(pool, weights=[f.get("weight", 1) for f in pool], k=1)[0]

def roll_collect_fish(spot_id: str | None = None, is_night: bool = False):
    """彩蛋收藏鱼判定（16 章 4.x）：五档之外独立判定。

    概率升序判定（最稀有优先），命中即返回，最多 1 条。
    spot_id: 钓点地图 ID；is_night: 当前是否为夜晚（18 章时间系统）。
    """
    for cf in sorted(FISH_COLLECT, key=lambda x: x["chance"]):
        if cf.get("spots") and (spot_id not in cf["spots"]):
            continue
        if cf.get("time") == "night" and not is_night:
            continue
        if random.random() < cf["chance"]:
            return cf
    return None
