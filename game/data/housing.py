# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - housing.py

v68 地契房产：城镇可购买的地皮。

- PROPERTIES[prop_id] = {"name", "map"(所在城镇地图), "price", "desc"}
- 一个玩家最多持有一张地契（players.deed 列）
- 家地图 ID = home_{qq_id}（动态，不在 MAPS 里），展示由命令层定制
"""
PROPERTIES = {
    "prop_vila_01": {
        "name": "维拉镇·喷泉小屋",
        "map": "vila_square",
        "price": 2000,
        "desc": "广场喷泉旁的小屋，推开窗就能看到公告板。新手冒险者的第一个家。",
    },
    "prop_stonefist_01": {
        "name": "石拳丘陵·矿工小屋",
        "map": "stonefist_camp",
        "price": 3500,
        "desc": "矮人风格的石头小屋，壁炉整年烧着炉火。离矿洞近，采矿的绝佳据点。",
    },
    "prop_shadow_01": {
        "name": "暗影之城·塔楼居所",
        "map": "shadow_square",
        "price": 6000,
        "desc": "暗影街区的旧塔楼，窗户朝向夜幕下的城市。神秘而安静。",
    },
    "prop_holy_01": {
        "name": "远境城·圣光宅邸",
        "map": "holy_city_square",
        "price": 12000,
        "desc": "圣光王国城区内的雅致宅邸，门前种着圣光百合。身份的象征。",
    },
    "prop_elf_01": {
        "name": "银月城·树屋",
        "map": "elf_city_square",
        "price": 15000,
        "desc": "缠绕在生命之树上的精灵树屋，月光能透过叶隙洒进屋内。",
    },
    "prop_dragon_01": {
        "name": "龙喉堡·熔岩居所",
        "map": "dragon_city_square",
        "price": 20000,
        "desc": "依着龙喉堡山壁开凿的居所，室内流淌着温热的熔岩渠。",
    },
}
