# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - world.py"""
WORLD_EVENT_POOL = [
    {"type": "auction",  "name": "神秘拍卖行", "icon": "🏪", "duration": 7200,
     "desc": "一位神秘商人出现在维拉镇，带来了三件稀世珍宝！输入『拍卖』查看，『竞拍 <编号> <金币>』出价！"},
    {"type": "boss",     "name": "世界Boss入侵", "icon": "👹", "duration": 10800,
     "desc": "强大的魔物突破封印降临大陆！全服勇士共同讨伐，输入『讨伐』加入战斗！"},
    {"type": "merchant", "name": "商队集市", "icon": "🎁", "duration": 3600,
     "desc": "远方商队进城了！所有商店限时 8 折，快去扫货！（输入『商店』查看）"},
    {"type": "omen",     "name": "元素异象", "icon": "🌧️", "duration": 7200,
     "desc": "魔法元素异常活跃，全大陆经验与金币收益 +50%！抓住机会升级！"},
    {"type": "swarm",    "name": "兽潮来袭", "icon": "⚔️", "duration": 7200,
     "desc": "兽潮涌向大陆，怪物经验 +30%，击杀声望双倍！守护这片土地！"},
    {"type": "festival", "name": "节日庆典", "icon": "🎉", "duration": 14400,
     "desc": "大陆迎来庆典！签到奖励翻倍，今日金币掉落增加！"},
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
    # v49 意见#5：每个世界 Boss 指定出现地点（map 字段），玩家必须到达该地图才能讨伐
    # v58：mech 专属机制（enrage 狂暴 / summon 召唤 / heal 自愈）
    {"name": "深渊魔王·阿兹莫丹", "icon": "👹", "lv": 35, "hp": 300000,  "reward": {"gold": 2000, "exp": 3000}, "map": "abyss_plain", "map_name": "深渊荒原", "mech": "enrage"},
    {"name": "混沌领主·巴巴托斯", "icon": "😈", "lv": 55, "hp": 800000,  "reward": {"gold": 5000, "exp": 8000}, "map": "dragon_nest", "map_name": "龙巢之巅", "mech": "summon"},
    {"name": "亡灵天灾·克尔苏加德", "icon": "💀", "lv": 75, "hp": 2000000, "reward": {"gold": 12000, "exp": 20000}, "map": "temple_aisle", "map_name": "忏悔回廊", "mech": "heal"},
    {"name": "灭世之龙·尼德霍格", "icon": "🐉", "lv": 95, "hp": 5000000, "reward": {"gold": 30000, "exp": 50000}, "map": "divine_hall", "map_name": "旧宫回廊", "mech": "enrage"},
    {"name": "混沌之源·原始意志", "icon": "🌀", "lv": 100, "hp": 10000000, "reward": {"gold": 60000, "exp": 100000}, "map": "panth_court", "map_name": "先王庭院", "mech": "summon"},
]

