# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - world.py（阶段四重写，2026-08-06）

WORLD_EVENT_POOL：07 章七·世界事件（圣光节/兽潮来袭/商队集市/世界Boss/深渊涌动）
WORLD_BOSS_POOL：04 章外域世界 Boss + 地表世界 Boss（v49 意见#5：每 Boss 指定出现地图）
AUCTION_POOL：保留（拍卖品按等级递进）
"""
WORLD_EVENT_POOL = [
    {"type": "auction",  "name": "神秘拍卖行", "icon": "🏪", "duration": 7200,
     "desc": "一位神秘商人出现在铁港城，带来了三件稀世珍宝！输入『拍卖』查看，『竞拍 <编号> <金币>』出价！"},
    {"type": "boss",     "name": "世界Boss入侵", "icon": "👹", "duration": 10800,
     "desc": "强大的魔物突破封印降临大陆！全服勇士共同讨伐，输入『讨伐』加入战斗！"},
    {"type": "merchant", "name": "商队集市", "icon": "🎁", "duration": 3600,
     "desc": "远方商队进城了！所有商店限时 8 折，快去扫货！(输入『商店』查看)",
     "effects": {"shop_discount": 0.8}},
    {"type": "omen",     "name": "深渊涌动", "icon": "🌋", "duration": 7200,
     "desc": "深渊裂隙异常活跃，魔物蠢蠢欲动！探索战斗经验与金币收益＋50%！",
     "effects": {"exp_mult": 1.5, "gold_mult": 1.5}},
    {"type": "swarm",    "name": "兽潮来袭", "icon": "⚔️", "duration": 7200,
     "desc": "兽潮涌向大陆，怪物经验＋30%，击杀声望双倍！守护这片土地！",
     "effects": {"exp_mult": 1.3, "rep_mult": 2.0}},
    {"type": "festival", "name": "圣光节", "icon": "🎉", "duration": 14400,
     "desc": "教会举行圣光节庆典！『签到』奖励翻倍，战斗金币收益＋50%！",
     "effects": {"gold_mult": 1.5}},


    # ============ v125 世界事件扩容 +8（effects 数据驱动） ============
    {
        "type": "festival",
        "name": "丰收祭",
        "icon": "🌾",
        "duration": 14400,
        "desc": "金穗平原麦浪翻涌，丰收祭启幕！全境战斗金币收益×1.5，共庆丰年！",
        "effects": {
        "gold_mult": 1.5
    }
},
    {
        "type": "festival",
        "name": "仲夏夜祭典",
        "icon": "🏮",
        "duration": 14400,
        "desc": "萤火纷飞、篝火映夜，仲夏夜祭典歌舞不休！战斗经验收益×1.3！",
        "effects": {
        "exp_mult": 1.3
    }
},
    {
        "type": "omen",
        "name": "流星雨之夜",
        "icon": "🌠",
        "duration": 7200,
        "desc": "流星雨划破夜空，星辉洒落大地！向流星许愿，战斗经验收益×1.5！",
        "effects": {
        "exp_mult": 1.5
    }
},
    {
        "type": "omen",
        "name": "极光之夜",
        "icon": "🌌",
        "duration": 7200,
        "desc": "北境极光漫天舞动，元素魔力为之共鸣！战斗经验与金币收益×1.3！",
        "effects": {
        "exp_mult": 1.3,
        "gold_mult": 1.3
    }
},
    {
        "type": "merchant",
        "name": "矮人商队",
        "icon": "⚒️",
        "duration": 3600,
        "desc": "矮人锻造商队进城，锤声叮当！所有商店限时 8.5 折，神兵利器任你挑选！",
        "effects": {
        "shop_discount": 0.85
    }
},
    {
        "type": "merchant",
        "name": "精灵商队",
        "icon": "🧝",
        "duration": 3600,
        "desc": "精灵商队踏月色而至，药香弥漫街巷！所有商店限时 8.5 折，珍稀药剂材料不容错过！",
        "effects": {
        "shop_discount": 0.85
    }
},
    {
        "type": "swarm",
        "name": "鼠潮",
        "icon": "🐀",
        "duration": 7200,
        "desc": "地下鼠群骚动不安，成群涌出地表！讨伐鼠潮，战斗经验收益×1.2！",
        "effects": {
        "exp_mult": 1.2
    }
},
    {
        "type": "swarm",
        "name": "狼群围猎季",
        "icon": "🐺",
        "duration": 7200,
        "desc": "北境狼群进入围猎季，嚎声四起！猎杀群狼，战斗经验收益×1.3！",
        "effects": {
        "exp_mult": 1.3
    }
},]

AUCTION_POOL = [
    {"slot": "weapon", "lv": 15, "quality": "purple", "base": 800,  "buyout": 3000},
    {"slot": "weapon", "lv": 25, "quality": "purple", "base": 2000, "buyout": 8000},
    {"slot": "armor",  "lv": 20, "quality": "purple", "base": 1500, "buyout": 6000},
    {"slot": "weapon", "lv": 35, "quality": "orange", "base": 5000, "buyout": 20000},
    {"slot": "ring",   "lv": 30, "quality": "orange", "base": 4000, "buyout": 15000},
    {"slot": "weapon", "lv": 50, "quality": "orange", "base": 12000, "buyout": 50000},
    {"slot": "necklace", "lv": 45, "quality": "orange", "base": 10000, "buyout": 40000},
    {"slot": "weapon", "lv": 70, "quality": "orange", "base": 30000, "buyout": 120000},
    {"slot": "legs",   "lv": 80, "quality": "orange", "base": 40000, "buyout": 150000},
    {"slot": "weapon", "lv": 95, "quality": "orange", "base": 80000, "buyout": 300000},
]

WORLD_BOSS_POOL = [
    # ---- 地表世界 Boss（04 章 7.x 世界 Boss 段） ----
    {"name": "巨史莱姆王·咕噜咕噜", "icon": "🟢", "lv": 20, "hp": 80000,  "reward": {"gold": 800, "exp": 1200}, "map": "misty_swamp", "map_name": "迷雾沼泽", "mech": "summon"},
    {"name": "百族战魂·奥德里克残影", "icon": "👻", "lv": 40, "hp": 300000,  "reward": {"gold": 3000, "exp": 5000}, "map": "old_king_tomb", "map_name": "旧王陵外", "mech": "summon"},
    {"name": "古龙·奥姆之影", "icon": "🐉", "lv": 100, "hp": 5000000, "reward": {"gold": 30000, "exp": 50000}, "map": "dragon_tomb", "map_name": "龙之墓外", "mech": "enrage"},
    # ---- 外域世界 Boss（04 章十四·外域世界 Boss） ----
    {"name": "海蛇王·深渊之鳞", "icon": "🐍", "lv": 55, "hp": 800000,  "reward": {"gold": 5000, "exp": 8000}, "map": "storm_strait", "map_name": "风暴海峡", "mech": "summon"},
    {"name": "地底恶魔·黑炎", "icon": "😈", "lv": 85, "hp": 2500000, "reward": {"gold": 15000, "exp": 25000}, "map": "molten_abyss", "map_name": "熔火深渊", "mech": "summon"},
    {"name": "风暴龙王·裂空", "icon": "🌩️", "lv": 98, "hp": 8000000, "reward": {"gold": 45000, "exp": 80000}, "map": "storm_plateau", "map_name": "雷暴高原", "mech": "enrage"},
]
