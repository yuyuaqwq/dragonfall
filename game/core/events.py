# -*- coding: utf-8 -*-

import random

from ..data import EVENT_WEIGHT_SUM, EXPLORE_EVENTS


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

