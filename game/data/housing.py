# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - housing.py

v84 余烬纪元房产（25 章：房产与家园系统）：
- PROPERTIES[prop_id] = {"name", "map"(所在城镇地图), "price", "desc"}——全服唯一，先到先得
- HOUSE_LEVELS[lv] = 房屋等级配置（仓库容量/升级条件/附加功能）
- 一个玩家最多持有一张地契（players.deed 列）+ 房屋等级（players.deed_lv 列）
- 家地图 ID = home_{qq_id}（动态，不在 MAPS 里），展示由命令层定制
"""
PROPERTIES = {
    "prop_oak_01": {
        "name": "橡木小屋",
        "map": "oak_town",
        "price": 5000,
        "desc": "橡木镇边缘的小木屋，推开窗就是绿野的麦田。新手冒险者的第一个家。",
    },
    "prop_white_01": {
        "name": "白鹿公寓",
        "map": "white_deer",
        "price": 20000,
        "desc": "白鹿城商街上的公寓，楼下就是酒馆，消息灵通。中阶过渡的好选择。",
    },
    "prop_harbor_01": {
        "name": "铁港阁楼",
        "map": "ironharbor",
        "price": 60000,
        "desc": "铁港城码头顶层的阁楼，推开窗就是桅杆与海风。跑商的绝佳据点。",
    },
    "prop_dawn_01": {
        "name": "晨曦宅院",
        "map": "dawn_city",
        "price": 150000,
        "desc": "晨曦城圣光区内的雅致宅院，门前种着圣光百合。身份的象征。",
    },
    "prop_moon_01": {
        "name": "月冠别墅",
        "map": "moon_court",
        "price": 300000,
        "desc": "月冠王庭的精灵别墅，月光能透过叶隙洒进屋内。奢华之选。",
    },
    "prop_anvil_01": {
        "name": "铁砧庄园",
        "map": "anvil_fort",
        "price": 500000,
        "desc": "铁砧要塞山壁上的矮人庄园，室内流淌着温热的熔岩渠。顶级置业。",
    },
}

# 房屋等级（25 章三）：1 木屋 → 2 石屋 → 3 庄园 → 4 宅邸
# upgrade_cost = {"gold": 金币, "mats": {材料ID: 数量}}；refund 为卖房返还比例
HOUSE_LEVELS = {
    1: {
        "name": "木屋",
        "storage": 20,
        "upgrade_cost": None,            # 初始
        "heal_pct": 0.5,                 # 回家恢复 50% 血蓝
        "stall_slots": 0,                # 铺面挂机位
        "desc": "温暖的小木屋，够住。",
    },
    2: {
        "name": "石屋",
        "storage": 40,
        "upgrade_cost": {"gold": 5000, "mats": {"mat_shi_cai": 20}},
        "heal_pct": 1.0,                 # 回家恢复 100% 血蓝
        "stall_slots": 1,                # 铺面挂机位 +1
        "desc": "结实的石屋，仓库大了，回家能完全恢复。",
    },
    3: {
        "name": "庄园",
        "storage": 80,
        "upgrade_cost": {"gold": 20000, "mats": {"mat_jing_tie": 10}},
        "heal_pct": 1.0,
        "stall_slots": 2,                # 铺面挂机位 +2
        "desc": "带院子的庄园，铺面挂机位更多，可邀请好友留宿。",
    },
    4: {
        "name": "宅邸",
        "storage": 160,
        "upgrade_cost": {"gold": 80000, "mats": {"mat_mi_yin": 5}},
        "heal_pct": 1.0,
        "stall_slots": 3,                # 铺面挂机位 +3
        "desc": "气派的宅邸，仓库 160 格，解锁专属宅邸传送点。",
    },
}

HOUSE_MAX_LEVEL = max(HOUSE_LEVELS)

# 卖房返还比例（按等级递减，25 章三）
HOUSE_REFUND = {1: 0.50, 2: 0.40, 3: 0.30, 4: 0.20}
