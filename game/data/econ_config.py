# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - econ_config.py（命令层经济数值下沉）

v125.1 审计 P2/命令层：命令层 20+ 处裸魔法数字下沉——
住宿费 / 传送费 / 商店装备价 / 装备回收半价 / 锻造图纸价 / 市场定价上限等。
数值集中后：调整经济数值只改此文件，零代码改动。
"""
ECON_CONFIG = {
    # ---- 住宿（world.py rest，v101.25i4 住宿费公式）----
    "inn_cost_lv_cap": 15,       # Lv.≤15 走新手公式（新手友好不动）
    "inn_cost_min_low": 30,      # 新手档最低：max(30, lv×5)
    "inn_cost_per_lv": 5,        # 每级 5 金
    "inn_cost_min_high": 100,    # Lv.16+ 档最低：max(100, ...)
    "inn_cost_round": 100,       # Lv.16+ 向下取整到百（Lv.100=1000 金）
    "inn_cost_high_mult": 2.0,   # v131 高档系数：lv×5×2 = 每级 10 金（Lv.100=1000）
                                 #   —— 解耦 hp_stage_mult（怪物曲线放缓后住宿跟随掉到 900，
                                 #      违反鱼鱼拍板凑整 1000 金；费用按等级不按百分比）
    # ---- 传送（world.py portal_view/portal_travel，v39 坐骑折扣后保底）----
    "portal_min_cost": 1,        # 传送费折扣后最低 1 金
    # ---- 市场/摆摊定价（social.py market_sell/stall，v104R3 P2）----
    "market_min_price": 1,       # 上架/摆摊最低价（价格至少 1 金币）
    "market_price_cap": 999999,  # 上架/摆摊最高价（防 999999999 恶意占坑/诱导高价）
    # ---- 商店装备价格（economy.py _shop_equip_price，v101.25e）----
    "shop_equip_price_base": 3,  # 基础价系数：equip_value × (3 + lv×0.5)
    "shop_equip_price_lv": 0.5,  # 每级价格系数
    # ---- 装备回收半价（economy.py _sell_one 掉落回收上限 / buy 商店购入价半价，v21/v101.27）----
    "equip_resale_rate": 0.5,    # 装备卖店 = 推导价×0.5（防刷钱）
    # ---- 神秘锻造图纸（economy.py shop/buy，v94 图纸经济）----
    "bp_price_base": 20,         # 图纸价 = (lv×3 + 20) × 3
    "bp_price_per_lv": 3,
    "bp_smith_mult": 3,
    # ---- 购买数量上限（economy.py buy，v95.25『购买 <名称> <数量>』）----
    "buy_qty_max": 999,
}
