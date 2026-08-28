# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - upgrade.py（v135 装备升级机制）

定位：强化=赌（运气掉级）、升级=养（稳定保底）、附魔=快（一次成型）。
升级 = 装备等级 lv → lv+N，属性随 equip_stats 线性增长，成功率 100%，
让一套装备用久一点、强化/附魔投资不再随换装沉没（v135 鱼鱼拍板）。
"""
UPGRADE_TABLE = {
    0: {"cost": 200, "mult": 1.00},
    1: {"cost": 300, "mult": 1.035},
    2: {"cost": 450, "mult": 1.07},
    3: {"cost": 675, "mult": 1.105},
    4: {"cost": 1012, "mult": 1.14},
    5: {"cost": 1518, "mult": 1.175},
    6: {"cost": 2277, "mult": 1.21},
    7: {"cost": 3415, "mult": 1.245},
    8: {"cost": 5122, "mult": 1.28},
    9: {"cost": 7683, "mult": 1.315},
    10: {"cost": 11524, "mult": 1.35},
}
MAX_UPGRADE = 10
UPGRADE_STONE = "i_stone_refine"     # 每级 1 个精炼强化石
UPGRADE_STAMINA = 10
UPGRADE_MATERIAL_CN = "精炼强化石"
