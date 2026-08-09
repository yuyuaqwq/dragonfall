# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - cooking.py：烹饪副业（13 章 2.3 烹饪表 v2.0，2026-08-06 重写）

副业联动：垂钓（鱼）+ 采集（药材）→ 烹饪 → 战斗外恢复/持续 buff。
- 成本 key 一律 mat_ ID（v48 ID 规范，禁止 fish_ 中文动态 key）
- 持续 buff 型料理（银鳞鱼汤/狼肉煲/龙息炖锅/精灵果酱）随 19 章食物 buff 系统落地，
  本表只收当前可即时生效的配方（战斗外回复）
"""
COOKING_RECIPES = {
    "cook_slime_jelly": {
        "name": "史莱姆果冻",
        "desc": "史莱姆黏液熬成的果冻，滑嫩爽口",
        "min_lv": 1,
        "cost": {"mat_shi_lai_mu_nian_ye": 3},
        "product": {"it_slime_jelly": 1},
    },
    "cook_skewer": {
        "name": "烤肉串（自制）",
        "desc": "新鲜兽肉串烤，滋滋冒油",
        "min_lv": 1,
        "cost": {"mat_shou_rou": 2},
        "product": {"it_cook_skewer": 1},
    },
    "cook_gold_feast": {
        "name": "金鲤盛宴",
        "desc": "金鲤红烧一锅端，富贵人家才吃得起",
        "min_lv": 2,
        "cost": {"mat_jin_li": 2},
        "product": {"it_gold_feast": 1},
    },
}

COOKING_REQUIRED_LV = {
    "cook_slime_jelly": 1,
    "cook_skewer": 1,
    "cook_gold_feast": 2,
}
