# -*- coding: utf-8 -*-

import random

from ..data import MOUNT_BY_KEY, MOUNT_DROP_BOSS, MOUNT_DROP_ELITE


"""奥兰迪亚·余烬纪年核心层 - mounts.py"""
def make_mount_rein(mount_key):
    m = MOUNT_BY_KEY[mount_key]
    return {"name": f"{m['name']}缰绳", "type": "坐骑", "mount_key": mount_key, "stackable": True,
            "price": 300, "desc": f"使用后可获得坐骑『{m['name']}』"}

def roll_mount_drop(role: str) -> str | None:
    """战斗胜利按怪物角色掷坐骑缰绳掉落，返回 mount_key 或 None。
    q7-3：单次分档随机（cumulative 区间法）替代链式独立伯努利——原 for 循环若前项命中
    即 return，后项名义概率被前项截流（如狮鹫名义 1% → 有效 ≈0.84%）。现一次 random.random()
    按权重归一化取一根，保持各坐骑名义概率 = 实际概率。"""
    tbl = MOUNT_DROP_BOSS if role == "boss" else (MOUNT_DROP_ELITE if role == "elite" else None)
    if not tbl:
        return None
    total = sum(p for p in tbl.values())
    # 一次 uniform 抽签：r ∈ [0, total) 命中（掉落总概率=total）；≥total 则不掉落。
    # 命中分支按累计区间分摊，各坐骑实际概率 = 名义概率，且不改变总掉落率（非必中）。
    r = random.random()
    if r >= total:
        return None
    acc = 0.0
    for mk, prob in tbl.items():
        acc += prob
        if r < acc:
            return mk
    return None

# 坐骑效果字段（v101.11 新增效果统一入口；加效果 = 数据层加字段 + 本函数加 key + 消费点调用）
_MOUNT_EFFECT_KEYS = ("discount", "elite_bonus", "stamina_reduce", "sell_bonus",
                      "collect_bonus", "fish_bonus", "exp_mult")

def mount_effects(player: dict) -> dict:
    """活跃坐骑效果汇总：{discount, elite_bonus, stamina_reduce, sell_bonus,
    collect_bonus, fish_bonus, exp_mult}。未骑乘/未知坐骑返回空 dict。"""
    mounts = (player or {}).get("mounts") or {}
    active_mk = mounts.get("active")
    if not active_mk or active_mk not in MOUNT_BY_KEY:
        return {}
    m = MOUNT_BY_KEY[active_mk]
    return {k: m.get(k, 0) for k in _MOUNT_EFFECT_KEYS}
