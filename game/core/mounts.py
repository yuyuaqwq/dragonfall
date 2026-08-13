# -*- coding: utf-8 -*-

import random

from ..data import MOUNT_BY_KEY, MOUNT_DROP_BOSS, MOUNT_DROP_ELITE


"""《剑与魔法》核心层 - mounts.py"""
def make_mount_rein(mount_key):
    m = MOUNT_BY_KEY[mount_key]
    return {"name": f"{m['name']}缰绳", "type": "坐骑", "mount_key": mount_key, "stackable": True,
            "price": 300, "desc": f"使用后可获得坐骑『{m['name']}』"}

def roll_mount_drop(role: str) -> str | None:
    """战斗胜利按怪物角色掷坐骑缰绳掉落，返回 mount_key 或 None"""
    tbl = MOUNT_DROP_BOSS if role == "boss" else (MOUNT_DROP_ELITE if role == "elite" else None)
    if not tbl:
        return None
    for mk, prob in tbl.items():
        if random.random() < prob:
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
