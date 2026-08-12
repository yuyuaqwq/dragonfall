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
    # ---- v101.28i 词条料理接入烹饪（13 件，2026-08-11）：材料成本≈卖价40~90%，
    #      烬火辣椒/蘑菇汤/冰霜浆果/树蜜糖 因材料倒挂保留商店渠道 ----
    "cook_snake_soup": {
        "name": "蛇羹",
        "desc": "蛇皮慢火熬成的鲜羹，沼泽风味",
        "min_lv": 1,
        "cost": {"mat_she_pi": 3},
        "product": {"i_snake_soup": 1},
    },
    "cook_wolf_jerky": {
        "name": "狼肉干",
        "desc": "狼皮风干熏制的野外干粮，耐放顶饿",
        "min_lv": 1,
        "cost": {"mat_lang_pi": 2},
        "product": {"i_wolf_jerky": 1},
    },
    "cook_eagle_egg": {
        "name": "鹰蛋",
        "desc": "悬崖巢穴里捡来的蛋，煎烤皆宜",
        "min_lv": 1,
        "cost": {"mat_hai_ou_yu_mao": 1, "mat_jiang_guo": 1},
        "product": {"i_eagle_egg": 1},
    },
    "cook_ash_pancake": {
        "name": "灰烬烤饼",
        "desc": "炭火烤制的粗粮饼，带着烟火气",
        "min_lv": 1,
        "cost": {"mat_mian_fen": 2, "mat_jiang_guo": 2},
        "product": {"i_ash_pancake": 1},
    },
    "cook_sacred_bread": {
        "name": "圣餐面包",
        "desc": "以圣水揉面烤成的素面包，圣堂赐福",
        "min_lv": 2,
        "cost": {"mat_mian_fen": 2, "mat_sheng_shui": 1},
        "product": {"i_sacred_bread": 1},
    },
    "cook_deer_cheese": {
        "name": "鹿奶干酪",
        "desc": "溪鹿乳发酵压制的干酪，奶香浓郁",
        "min_lv": 2,
        "cost": {"mat_xi_lu_pi": 1, "mat_jiang_guo": 1},
        "product": {"i_deer_cheese": 1},
    },
    "cook_pirate_stew": {
        "name": "海盗炖鱼",
        "desc": "整条银鳞鱼下锅炖煮，无名港私房菜",
        "min_lv": 2,
        "cost": {"mat_yin_lin_yu": 2},
        "product": {"i_pirate_stew": 1},
    },
    "cook_moon_cake": {
        "name": "月光饼",
        "desc": "月鹿角磨粉入馅的甜饼，月色下的点心",
        "min_lv": 3,
        "cost": {"mat_yue_lu_jiao": 1, "mat_jiang_guo": 1},
        "product": {"i_moon_cake": 1},
    },
    "cook_seafood_chowder": {
        "name": "海鲜浓汤",
        "desc": "蟹肉鱼鲜一锅烩，码头工人的最爱",
        "min_lv": 3,
        "cost": {"mat_xie_ke": 1, "mat_yin_lin_yu": 1},
        "product": {"i_seafood_chowder": 1},
    },
    "cook_snowwolf_steak": {
        "name": "雪狼肉排",
        "desc": "雪狼里脊厚切煎排，霜原猎手的骄傲",
        "min_lv": 4,
        "cost": {"mat_xue_lang_pi": 1},
        "product": {"i_snowwolf_steak": 1},
    },
    "cook_royal_roast": {
        "name": "皇家烤肉",
        "desc": "精选兽肉配麦酒腌制，王都御膳风味",
        "min_lv": 4,
        "cost": {"mat_shou_rou": 2, "mat_mai_jiu": 1},
        "product": {"i_royal_roast": 1},
    },
    "cook_royal_soup": {
        "name": "御膳汤",
        "desc": "鹿角兽肉小火慢煨，王都名厨的看家汤",
        "min_lv": 5,
        "cost": {"mat_shou_rou": 1, "mat_yue_lu_jiao": 1, "mat_jiang_guo": 1},
        "product": {"i_royal_soup": 1},
    },
    "cook_dragon_egg_pancake": {
        "name": "龙蛋煎饼",
        "desc": "幼龙鳞入面糊的珍馐，龙脊盛宴压轴",
        "min_lv": 7,
        "cost": {"mat_you_long_lin": 1, "mat_mian_fen": 2, "mat_jiang_guo": 1},
        "product": {"i_dragon_egg_pancake": 1},
    },
}

COOKING_REQUIRED_LV = {
    "cook_slime_jelly": 1,
    "cook_skewer": 1,
    "cook_gold_feast": 2,
}
