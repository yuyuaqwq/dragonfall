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
]

EVENT_WEIGHT_SUM = sum(e["weight"] for e in EXPLORE_EVENTS)
