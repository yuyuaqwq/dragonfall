# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - fishing.py"""
FISHING_SPOTS = {
    "vila_gate": {"name": "城门外的护城河", "min_lv": 1, "desc": "新手也能轻松上钩"},
    "emerald_trail": {"name": "林间溪流", "min_lv": 1, "desc": "清澈见底，银鳞鱼最爱"},
    "emerald_heart": {"name": "翡翠湖畔", "min_lv": 3, "desc": "深水大鱼，考验耐心"},
    "gloom_edge": {"name": "沼泽水潭", "min_lv": 4, "desc": "浑浊水面下藏着宝物"},
    "tundra_field": {"name": "冰封湖面", "min_lv": 6, "desc": "凿开冰层，稀有的冷水鱼"},
    "blackrock_street": {"name": "死城运河", "min_lv": 8, "desc": "古老的运河，传说鱼王栖息于此"},
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
    {"name": "鱼王·翡翠巨龙", "type": "鱼王", "price": 500, "desc": "传说沉眠在深水中的鱼王！全服为之震动"},
]

FISH_WEIGHTS = [35, 25, 15, 10, 6, 4, 3, 2, 0.5]

# 副业等级 → 稀有权重倍率（作用于金鲤/帝王鲑/珍珠/宝物/鱼王）
FISH_RARE_BONUS = {3: 1.5, 5: 2.0, 7: 3.0, 9: 5.0}

