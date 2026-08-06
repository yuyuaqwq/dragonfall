# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - cooking.py：烹饪副业

副业联动：垂钓（鱼）+ 采集（药材/蘑菇/浆果）→ 烹饪 → 战斗消耗品。
- 食谱按烹饪等级解锁（min_lv）
- 产出都是消耗品（heal/mana/effect），走『使用』指令
"""
COOKING_RECIPES = {
    "cook_fish_soup": {
        "name": "鱼汤",
        "desc": "鲜鱼慢炖的浓汤，暖暖身子",
        "min_lv": 1,
        "cost": {"fish_银鳞鱼": 2, "mat_香草": 1},
        "product": {"it_fish_soup": 1},
    },
    "cook_herb_tea": {
        "name": "香草茶",
        "desc": "采集的香草泡的茶，提神醒脑",
        "min_lv": 1,
        "cost": {"mat_香草": 2},
        "product": {"it_herb_tea": 1},
    },
    "cook_mushroom_stew": {
        "name": "蘑菇炖菜",
        "desc": "林间蘑菇炖的杂烩，饱腹又补血",
        "min_lv": 2,
        "cost": {"mat_蘑菇": 2, "mat_香草": 1},
        "product": {"it_mushroom_stew": 1},
    },
    "cook_royal_salmon": {
        "name": "香煎帝王鲑",
        "desc": "帝王鲑煎得金黄，贵族的享受",
        "min_lv": 3,
        "cost": {"fish_帝王鲑": 1, "mat_香料": 1},
        "product": {"it_royal_salmon": 1},
    },
    "cook_berry_pie": {
        "name": "浆果派",
        "desc": "甜香扑鼻的浆果派，吃了心情大好",
        "min_lv": 4,
        "cost": {"mat_浆果": 3, "mat_蜂蜜": 1},
        "product": {"it_berry_pie": 1},
    },
    "cook_elixir_soup": {
        "name": "秘制灵药汤",
        "desc": "加入珍稀药材熬制，药效非凡",
        "min_lv": 6,
        "cost": {"mat_灵芝": 1, "fish_金鲤": 1, "mat_蜂蜜": 1},
        "product": {"it_elixir_soup": 1},
    },
    "cook_dragon_banquet": {
        "name": "龙脊盛宴",
        "desc": "传说级料理，龙脊山涧的珍品全在此锅",
        "min_lv": 8,
        "cost": {"fish_帝王鲑": 2, "mat_灵芝": 2, "mat_香料": 2, "mat_蜂蜜": 1},
        "product": {"it_dragon_banquet": 1},
    },
}

COOKING_REQUIRED_LV = {
    "fish_soup": 1,
    "herb_tea": 1,
    "mushroom_stew": 2,
    "royal_salmon": 3,
    "berry_pie": 4,
    "elixir_soup": 6,
    "dragon_banquet": 8,
}
