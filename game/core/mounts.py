# -*- coding: utf-8 -*-

import random

from ..data import MOUNT_BY_KEY, MOUNT_DROP_BOSS, MOUNT_DROP_ELITE


"""《剑与魔法》数据层 - mounts.py"""
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

