# -*- coding: utf-8 -*-

import random

from ..data import EVENT_WEIGHT_SUM, EXPLORE_EVENTS, EXPLORE_EGG_CHANCE, EXPLORE_EGG_EVENTS, EXPLORE_EGG_SUM



"""《剑与魔法》数据层 - events.py"""
def roll_explore_event():
    """掷一个随机事件，返回事件 dict"""
    r = random.random() * EVENT_WEIGHT_SUM
    acc = 0
    for e in EXPLORE_EVENTS:
        acc += e["weight"]
        if r <= acc:
            return e
    return EXPLORE_EVENTS[0]

def roll_explore_egg(cur_map_id=None):
    """探索彩蛋判定(02 章 7.5)：常规事件之外独立判定，命中返回蛋事件 dict。

    v97.6 区域彩蛋：事件带 maps（地图 id 列表）时仅对应地图可触发；
    无 maps 字段 = 全局彩蛋。命中后按"当前地图可触发的池子"权重分配。
    """
    if random.random() >= EXPLORE_EGG_CHANCE:
        return None
    pool = [e for e in EXPLORE_EGG_EVENTS
            if not e.get("maps") or (cur_map_id and cur_map_id in e["maps"])]
    if not pool:
        return None
    total = sum(e["weight"] for e in pool)
    r = random.random() * total
    acc = 0
    for e in pool:
        acc += e["weight"]
        if r <= acc:
            return e
    return pool[0]
