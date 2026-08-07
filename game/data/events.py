# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - events.py（阶段四重写，2026-08-06）

探索随机事件（遇怪之前判定）。id 必须与 combat.py `_handle_explore_event` 分支一致：
treasure/merchant/spring/trap/omen/herb/windfall/wandering——只改文案，不动 id。
"""
EXPLORE_EVENTS = [
    {"id": "treasure", "weight": 18, "name": "闪闪发光的宝箱", "desc": "树丛里藏着一个落了灰的宝箱，锁扣上刻着冒险者行会的旧徽记！"},
    {"id": "merchant", "weight": 1, "name": "流浪商人", "desc": "一个行色匆匆的商队掉队者拦住你，想低价出手几件压箱底的好货。"},
    {"id": "spring",   "weight": 14, "name": "神秘泉水", "desc": "一汪冒着微光的泉水，喝下后感觉浑身的疲惫都被涤荡干净了。"},
    {"id": "trap",     "weight": 10, "name": "隐蔽的陷阱", "desc": "脚下突然一空，你踩进了猎人的捕兽坑！"},
    {"id": "omen",     "weight": 8,  "name": "古老的遗迹", "desc": "废墟的残垣上刻着陌生的符文，像是某位守护者留下的警示。"},
    {"id": "herb",     "weight": 12, "name": "草药丛", "desc": "一片长势喜人的野生草药，炼金师会为它们出个好价钱。"},
    {"id": "windfall", "weight": 10, "name": "意外之财", "desc": "地上散落着几枚金币，像是某位粗心商人翻车时掉的。"},
    {"id": "wandering", "weight": 8, "name": "迷路的旅人", "desc": "一位迷路的旅人向你求助，想用随身物品换取指路。"},
    # v87 02 章 7.6：常规事件扩容 8 → 12
    {"id": "lost_camp", "weight": 9, "name": "废弃营地", "desc": "一处被遗弃的营地，篝火余烬尚温，帐篷里似乎还有前人留下的物资。"},
    {"id": "meteor",    "weight": 5, "name": "陨石坑", "desc": "地面凹陷着一个冒着热气的陨石坑，坑底嵌着一块奇异的金属。"},
    {"id": "animal",    "weight": 9, "name": "迷路的小动物", "desc": "一只小动物从灌木丛探出头来，好奇地打量着你。"},
    {"id": "rain",      "weight": 7, "name": "突如其来的雨", "desc": "天空骤然阴沉，豆大的雨点砸了下来。"},
]

# v83 02 章 7.5：探索彩蛋事件（独立于常规权重，总概率 EXPLORE_EGG_CHANCE）
# 命中后按权重分配：流星 60 / 宝匣 30 / 访客 10 → 实际 0.30%/0.15%/0.05%
EXPLORE_EGG_CHANCE = 0.005
EXPLORE_EGG_EVENTS = [
    {"id": "shooting_star", "weight": 60, "name": "流星许愿",
     "desc": "一道流星划过夜空！"},
    {"id": "mystery_chest", "weight": 30, "name": "神秘宝匣",
     "desc": "埋藏千年的宝匣。"},
    {"id": "night_visitor", "weight": 10, "name": "神秘访客",
     "desc": "雾中出现的神秘身影。"},
    # v87 02 章 7.5：彩蛋扩充（权重相应调低老彩蛋）
    {"id": "old_map", "weight": 12, "name": "泛黄藏宝图",
     "desc": "一张泛黄的藏宝图。"},
    {"id": "gold_slime", "weight": 8, "name": "金色史莱姆",
     "desc": "一只通体金黄的史莱姆！"},
]
EXPLORE_EGG_SUM = sum(e["weight"] for e in EXPLORE_EGG_EVENTS)


EVENT_WEIGHT_SUM = sum(e["weight"] for e in EXPLORE_EVENTS)
