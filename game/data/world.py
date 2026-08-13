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
     "desc": "远方商队进城了！所有商店限时 8 折，快去扫货！(输入『商店』查看)"},
    {"type": "omen",     "name": "深渊涌动", "icon": "🌋", "duration": 7200,
     "desc": "深渊裂隙异常活跃，魔物蠢蠢欲动！探索战斗经验与金币收益＋50%！"},
    {"type": "swarm",    "name": "兽潮来袭", "icon": "⚔️", "duration": 7200,
     "desc": "兽潮涌向大陆，怪物经验＋30%，击杀声望双倍！守护这片土地！"},
    {"type": "festival", "name": "圣光节", "icon": "🎉", "duration": 14400,
     "desc": "教会举行圣光节庆典！『签到』奖励翻倍，战斗金币收益＋50%！"},
]

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
