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

def roll_explore_egg():
    """探索彩蛋判定(02 章 7.5)：常规事件之外独立判定，命中返回蛋事件 dict。"""
    if random.random() >= EXPLORE_EGG_CHANCE:
        return None
    r = random.random() * EXPLORE_EGG_SUM
    acc = 0
    for e in EXPLORE_EGG_EVENTS:
        acc += e["weight"]
        if r <= acc:
            return e
    return EXPLORE_EGG_EVENTS[0]
