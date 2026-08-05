# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - fishing.py"""
FISHING_SPOTS = {
    "vila_gate": "城门外的护城河",
    "emerald_trail": "林间溪流",
    "emerald_heart": "翡翠湖畔",
    "gloom_edge": "沼泽水潭",
    "tundra_field": "冰封湖面",
    "blackrock_street": "死城运河",
}

FISH_POOL = [
    {"name": "银鳞鱼", "type": "鱼", "price": 12, "desc": "常见的淡水鱼，肉质鲜美"},
    {"name": "金鲤", "type": "鱼", "price": 25, "desc": "鳞片泛着金光的鲤鱼，酒楼抢着收"},
    {"name": "帝王鲑", "type": "鱼", "price": 45, "desc": "罕见的大鱼，据说吃了能增强体质"},
    {"name": "神秘鳞片", "type": "材料", "price": 30, "desc": "不知名生物留下的鳞片，铁匠会感兴趣"},
    {"name": "珍珠", "type": "材料", "price": 40, "desc": "贝中孕育的珍宝，商人愿意高价收购"},
    {"name": "陈旧的宝箱", "type": "宝物", "price": 0, "desc": "水底的宝箱！打开看看有什么好东西"},
    {"name": "破旧的靴子", "type": "垃圾", "price": 1, "desc": "不知道谁扔进水里的，毫无用处"},
    {"name": "水草", "type": "垃圾", "price": 1, "desc": "缠成一团的水草，什么也没有"},
]

FISH_WEIGHTS = [35, 25, 15, 10, 6, 4, 3, 2]

