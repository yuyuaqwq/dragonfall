# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - pois.py（v87 02 章 7.6：探索点 POI 系统）

每个子区域可挂 0-3 个探索点（POI）——玩家『查看』当前子区域时列出，
『探索』有 15% 概率额外触发当前子区域随机 POI（独立判定）。
POI 与 NPC/商店/怪物独立，不占 NPC 位。
"""

POIS = {
    # ---- 城镇 POI（生活气息）----
    "campfire": {
        "name": "篝火", "icon": "🔥",
        "desc": "一堆噼啪作响的篝火，火光照亮周围的空地。",
        "effect": "recover",  # 恢复 30% 生命/魔力 + 随机烹饪食材
    },
    "shrine": {
        "name": "古老神龛", "icon": "🛕",
        "desc": "一座半埋进土里的古老神龛，石像面容模糊。",
        "effect": "buff",  # 随机 buff：攻击/防御/速度 +10% 持续 5 次战斗
    },
    "herb_patch": {
        "name": "草药丛", "icon": "🌿",
        "desc": "一片长势喜人的野生草药，散发着淡淡的药香。",
        "effect": "herb",  # 随机 1-2 份炼金材料
    },
    "loot_pile": {
        "name": "可疑包裹", "icon": "🎁",
        "desc": "路边扔着一个绑着麻绳的包裹，不知道装着什么。",
        "effect": "loot",  # 随机金币 / 低概率装备 / 陷阱（扣血）
    },
    "rune_stone": {
        "name": "符文石", "icon": "🪨",
        "desc": "一块刻满符文的古老石碑，符文中似乎蕴含着知识。",
        "effect": "rune",  # 读符文：随机知识（图鉴补全 / 隐藏成就线索）
    },
    "fishing_spot": {
        "name": "鱼群聚集", "icon": "🐟",
        "desc": "水面泛起细密的涟漪，一大群鱼正聚在水面下。",
        "effect": "fish",  # 立即获得 1 次免费垂钓机会（不耗次数）
    },
    "note": {
        "name": "神秘字条", "icon": "📜",
        "desc": "一张钉在树干上的字条，墨迹已经有些褪色。",
        "effect": "note",  # 收集线索（H6 书页/H7 信标前置）
    },
}

# 子区域 → POI 分配（key = "地图id:子区域id"，value = poi id 列表）
# 子区域 ID 为 map_N 数字格式（map_1=入口/广场，map_3=深处）
SUBAREA_POIS = {
    # ==== 绿野·橡木镇 ====
    "oak_town:oak_town_1": ["shrine", "campfire", "note"],   # 冒险者广场（含西巷字条）
    # ==== 白鹿城 ====
    "white_deer:white_deer_1": ["shrine"],            # 白鹿广场
    "white_deer:white_deer_5": ["herb_patch", "loot_pile"],  # 南市
    # ==== 铁港城 ====
    "ironharbor:ironharbor_1": ["fishing_spot", "loot_pile"],  # 港口广场
    "ironharbor:ironharbor_5": ["fishing_spot", "note"],       # 东码头
    # ==== 晨曦城 ====
    "dawn_city:dawn_city_3": ["shrine", "note"],      # 圣光大教堂
    "dawn_city:dawn_city_1": ["loot_pile"],           # 王都广场（南门遗物）
    # ==== 月冠王庭 ====
    "moon_court:moon_court_1": ["shrine", "rune_stone"],  # 王庭广场
    # ==== 野外·南境 ====
    "oak_meadow:oak_meadow_3": ["campfire", "herb_patch"],
    "oak_forest:oak_forest_3": ["campfire", "note"],
    "emerald_forest:emerald_forest_3": ["rune_stone", "herb_patch"],
    "misty_swamp:misty_swamp_3": ["loot_pile", "note"],
    "hill_mine:hill_mine_3": ["rune_stone", "loot_pile"],
    # ==== 野外·中域 ====
    "gold_plain:gold_plain_2": ["campfire", "herb_patch"],
    "silver_river:silver_river_2": ["fishing_spot", "campfire"],
    "old_battlefield:old_battlefield_3": ["rune_stone", "note"],
    "dawn_cathedral:dawn_cathedral_3": ["rune_stone", "note"],
    # ==== 野外·西境 ====
    "silverwood:silverwood_3": ["shrine", "herb_patch"],
    "starlake:starlake_3": ["fishing_spot", "rune_stone"],
    "ancient_tree:ancient_tree_3": ["rune_stone", "note"],
    # ==== 野外·北境 ====
    "frost_field:frost_field_3": ["campfire", "loot_pile"],
    "cinder_mountain:cinder_mountain_3": ["rune_stone", "note"],
    "black_forest:black_forest_3": ["loot_pile", "note"],
    # ==== 野外·东境 ====
    "dragon_ridge:dragon_ridge_3": ["rune_stone"],
    "ancient_battlefield:ancient_battlefield_3": ["rune_stone", "note"],
    # ==== 外域 ====
    "coral_reef:coral_reef_3": ["fishing_spot", "loot_pile"],
    "storm_sea:storm_sea_3": ["rune_stone", "note"],
    "molten_abyss:molten_abyss_3": ["rune_stone", "loot_pile"],
    "abyss_altar:abyss_altar_3": ["rune_stone", "note"],
}

# 随机线索 POI 文案池（note 效果：线索收集）
NOTE_POOL = [
    "纸条上写着：『三页旧纸，一扇石门——书页不齐，石门不开。』（失落图书馆线索）",
    "纸条上写着：『烬山深处，火光不灭。守墓人知道那扇门在哪。』（灰烬回廊线索）",
    "纸条上写着：『夜晚的城镇，有人高价收材料——只收识货人。』（夜行者商人线索）",
]

# 符文石知识池（rune 效果：图鉴补全/隐藏线索）
RUNE_POOL = [
    "符文在光芒中浮现：『黄金史莱姆只在最普通的草地出没，但极其罕见。』（图鉴线索）",
    "符文在光芒中浮现：『白鹿王只会在月光下的森林现身。』（图鉴线索）",
    "符文在光芒中浮现：『符文魔像守护着失落的图书馆。』（隐藏区域线索）",
    "符文在光芒中浮现：『暗影猎手喜欢在深夜捕猎。』（图鉴线索）",
]
