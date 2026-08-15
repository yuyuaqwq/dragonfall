# -*- coding: utf-8 -*-

import random

from ..data import EVENT_WEIGHT_SUM, EXPLORE_EVENTS, EXPLORE_EGG_CHANCE, EXPLORE_EGG_EVENTS, EXPLORE_EGG_SUM

# v116 季节渗透：探索事件随季节变化（借鉴垂钓，见 core/fishing.py）
# - 事件 season 硬限定：非当季不触发；season_boost 偏好：当季权重 ×1.5
# - 季节码与 time_weather.current_season 对齐（spring/summer/autumn/winter）
from .time_weather import current_season

# v116 季节感前缀：命中限定/偏好事件时附加给返回事件（浅拷贝，不污染数据池）
_SEASON_PREFIX = {"spring": "🌸", "summer": "☀️", "autumn": "🍂", "winter": "❄️"}


"""奥兰迪亚·余烬纪年数据层 - events.py"""
def roll_explore_event(exclude=()):
    """掷一个随机事件，返回事件 dict

    v101.30d #O22/O42：支持排除列表——同一玩家最近触发的常规事件不重复
    （短间隔去重，策划案 02 章 7.6）。排除后按剩余事件权重重掷。
    v116 季节渗透：season 硬限定（非当季剔除）、season_boost（当季权重 ×1.5）；
    若当前季节把池子过滤空则放宽季节限制重试，避免探索无事件。
    """
    # v116 当前季节
    season = current_season()

    def _season_ok(e):
        # 硬限定事件仅当季节匹配才触发；无 season 字段 = 全年可触发
        return not e.get("season") or e["season"] == season

    # 第一步：排除列表 + 季节硬限定 双重过滤
    if exclude:
        pool = [e for e in EXPLORE_EVENTS if e["id"] not in exclude and _season_ok(e)]
    else:
        pool = [e for e in EXPLORE_EVENTS if _season_ok(e)]
    if not pool:
        # 兜底：排除列表导致的例外，或当季硬限定事件占满池子 → 放宽季节限制重试
        pool = [e for e in EXPLORE_EVENTS if e["id"] not in exclude] if exclude else list(EXPLORE_EVENTS)
    if not pool:
        pool = list(EXPLORE_EVENTS)
    # v116 季节偏好：season_boost 匹配当前季节的事件权重 ×1.5（非限定，仅概率上升）
    total = sum(e["weight"] * (1.5 if e.get("season_boost") == season else 1) for e in pool)
    r = random.random() * total
    acc = 0
    for e in pool:
        w = e["weight"] * (1.5 if e.get("season_boost") == season else 1)
        acc += w
        if r <= acc:
            # v116 季节感输出：命中限定/偏好事件时附加前缀标记（浅拷贝，不污染数据池）
            if e.get("season") == season or e.get("season_boost") == season:
                pick = dict(e)
                pick["_season_prefix"] = _SEASON_PREFIX[season]
                return pick
            return e
    return pool[0]

def roll_explore_egg(cur_map_id=None):
    """探索彩蛋判定(02 章 7.5)：常规事件之外独立判定，命中返回蛋事件 dict。

    v97.6 区域彩蛋：事件带 maps（地图 id 列表）时仅对应地图可触发；
    无 maps 字段 = 全局彩蛋。命中后按"当前地图可触发的池子"权重分配。
    """
    if random.random() >= EXPLORE_EGG_CHANCE:
        return None
    pool = [e for e in EXPLORE_EGG_EVENTS
            if not e.get("maps") or (cur_map_id and cur_map_id in e["maps"])]
    if not pool:
        return None
    total = sum(e["weight"] for e in pool)
    r = random.random() * total
    acc = 0
    for e in pool:
        acc += e["weight"]
        if r <= acc:
            return e
    return pool[0]
