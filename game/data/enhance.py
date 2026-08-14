# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - enhance.py"""
ENHANCE_TABLE = {
    0: {"rate": 1.00, "cost": 50,   "mult": 1.00},
    1: {"rate": 0.95, "cost": 120,  "mult": 1.10},
    2: {"rate": 0.88, "cost": 250,  "mult": 1.22},
    3: {"rate": 0.78, "cost": 450,  "mult": 1.36},
    4: {"rate": 0.65, "cost": 800,  "mult": 1.52},
    5: {"rate": 0.52, "cost": 1300, "mult": 1.70},
    6: {"rate": 0.42, "cost": 2000, "mult": 1.90},
    7: {"rate": 0.32, "cost": 3200, "mult": 2.12},
    8: {"rate": 0.25, "cost": 5000, "mult": 2.36},
    # v104R3 M11 P3-12：+9 已是极限（MAX_ENHANCE=9），强化流程 cur_enh∈[0,8]（economy.py:2033
    # 用 cur_enh 查表，+8→+9 取第 8 行 cost/rate），本行 rate/cost 零消费端；
    # mult 被 engine.py 属性结算与装备详情显示读取，故仅保留 mult
    9: {"mult": 2.62},
}

MAX_ENHANCE = 9

# v113.3：+5/+6 失败掉 1 级（原 v104 +5 掉 2 级、+6~+8 掉 1 级）；+7/+8 失败不掉级（大师工艺保底）
# v113.3 拍板：成功率平缓化 + 高段保底，消除 514 万断崖（期望成本 514 万金 → 设计锚点 13170 金）
ENHANCE_FAIL_DROP = {5: 1, 6: 1}

# v83：改为余烬纪元真实铁匠铺地图（旧版是已删旧世界地图，新世界玩家找不到铁匠铺）
ENHANCE_SMITH_MAPS = ["oak_town", "white_deer", "ironharbor", "ironshield_town", "anvil_fort", "dawn_city"]

