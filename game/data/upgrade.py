# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - upgrade.py（v135 装备升级机制 → v172 真等级化）

定位：强化=赌（运气掉级）、升级=养（稳定保底）、附魔=快（一次成型）。
v172 真等级化（鱼鱼拍板）：每次升级装备 lv +1，属性随 equip_stats 公式重算，
upgrade_lv 倍率层作废（存量装备 upgrade_lv 在存档加载时迁移为 lv 补差）。
UPGRADE_TABLE 仅保留 cost 阶梯（每升 1 级消耗目标级金币），mult 字段不再消费。

旧倍率表（v135，存档参考）：1→10 级 ×1.035→×1.35（现仅用于 cost）。
"""
UPGRADE_TABLE = {
    1: {"cost": 300},
    2: {"cost": 450},
    3: {"cost": 675},
    4: {"cost": 1012},
    5: {"cost": 1518},
    6: {"cost": 2277},
    7: {"cost": 3415},
    8: {"cost": 5122},
    9: {"cost": 7683},
    10: {"cost": 11524},
}
# v172：cost 按目标级阶梯取（0→1 级花 1 级档 cost 300 起）。
# 旧 0 级行 cost 200 原为 upgrade_lv 0→1 的档位费，真等级化后并入 1 级档。
MAX_UPGRADE = 10  # 保留存量导入兼容（真等级化后不再消费，防旧引用 ImportError）
UPGRADE_STONE = "i_stone_refine"     # 每级 1 个精炼强化石
UPGRADE_STAMINA = 10
UPGRADE_MATERIAL_CN = "精炼强化石"
