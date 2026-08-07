# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - housing.py

v68 地契房产：城镇可购买的地皮。

- PROPERTIES[prop_id] = {"name", "map"(所在城镇地图), "price", "desc"}
- 一个玩家最多持有一张地契（players.deed 列）
- 家地图 ID = home_{qq_id}（动态，不在 MAPS 里），展示由命令层定制
"""
PROPERTIES = {
    "prop_vila_01": {
        "name": "橡木镇·喷泉小屋",
        "map": "oak_town",
        "price": 2000,
        "desc": "广场喷泉旁的小屋，推开窗就能看到公告板。新手冒险者的第一个家。",
    },
    "prop_stonefist_01": {
        "name": "铁港城·港务小屋",
        "map": "ironharbor",
        "price": 3500,
        "desc": "铁港城码头边的石头小屋，推开窗就是桅杆与海风。离贸易码头近，跑商的绝佳据点。",
    },
    "prop_shadow_01": {
        "name": "铁盾镇·塔楼居所",
        "map": "ironshield_town",
        "price": 6000,
        "desc": "铁盾镇城墙边的旧塔楼，窗户朝向铁匠铺的炉火。安静而踏实。",
    },
    "prop_holy_01": {
        "name": "晨曦城·圣光宅邸",
        "map": "dawn_city",
        "price": 12000,
        "desc": "圣光王国城区内的雅致宅邸，门前种着圣光百合。身份的象征。",
    },
    "prop_elf_01": {
        "name": "月冠王庭·树屋",
        "map": "moon_court",
        "price": 15000,
        "desc": "缠绕在生命之树上的精灵树屋，月光能透过叶隙洒进屋内。",
    },
    "prop_dragon_01": {
        "name": "龙裔聚落·熔岩居所",
        "map": "dragon_kin",
        "price": 20000,
        "desc": "依着龙裔聚落山壁开凿的居所，室内流淌着温热的熔岩渠。",
    },
}
