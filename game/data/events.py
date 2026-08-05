# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - events.py"""
EXPLORE_EVENTS = [
    {"id": "treasure", "weight": 18, "name": "闪闪发光的宝箱", "desc": "草丛里藏着一个宝箱！"},
    {"id": "merchant", "weight": 1, "name": "流浪商人", "desc": "一个行色匆匆的商人想低价卖你点东西。"},
    {"id": "spring",   "weight": 14, "name": "神秘泉水", "desc": "一汪冒着微光的泉水，饮下后感觉浑身舒畅。"},
    {"id": "trap",     "weight": 10, "name": "隐蔽的陷阱", "desc": "脚下突然一空，你掉进了猎人的陷阱！"},
    {"id": "omen",     "weight": 8,  "name": "古老的遗迹", "desc": "废墟中刻着古老的符文，似乎隐藏着什么秘密。"},
    {"id": "herb",     "weight": 12, "name": "草药丛", "desc": "一片野生草药，可以采集一些。"},
    {"id": "windfall", "weight": 10, "name": "意外之财", "desc": "地上散落着几枚金币，像是某位粗心商人掉的。"},
    {"id": "wandering", "weight": 8, "name": "迷路的旅人", "desc": "一位迷路的旅人向你求助，想用物品换取指引。"},
]

EVENT_WEIGHT_SUM = sum(e["weight"] for e in EXPLORE_EVENTS)

