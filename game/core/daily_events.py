# -*- coding: utf-8 -*-
"""《奥兰迪亚·余烬纪年》今日奇遇核心（v115）

日期哈希从 DAILY_MAP_EVENTS 中为某张野外图选出"今日奇遇"变体。
同一天全服一致（参考 game/core/wild.py::_day_hash 的 seed×2654435761+salt 设计）。

调用方（v115）：
  - game/commands/combat.py :: explore()——取今日奇遇的 effects 微调探索数值
  - game/commands/world.py :: map_view()——地图面板底部显示今日奇遇行
"""
import datetime

from ..data.daily_events import DAILY_MAP_EVENTS


def _day_hash(seed: int, salt: str = "") -> int:
    h = seed * 2654435761 + (sum(ord(c) for c in salt) if salt else 0)
    return h & 0x7FFFFFFF


def today_map_event(map_id, now=None):
    """当前位置地图的今日奇遇（日期哈希选中，同一天全服一致）。

    参数：
      map_id : 地图 id（仅 `野外` 类型迁移图有配置）
      now    : datetime.date / datetime.datetime / None（默认今天）
    返回：
      选中的变体 dict（含 id/name/desc/effects），无配置返回 None。
    """
    variants = DAILY_MAP_EVENTS.get(map_id)
    if not variants:
        return None
    _now = now or datetime.date.today()
    if isinstance(_now, datetime.datetime):
        ordinal = _now.date().toordinal()
    else:
        ordinal = _now.toordinal()
    # 用 map_id 作 salt，避免不同图同 seed 顶到同一下标的比例失配
    idx = _day_hash(ordinal, "daily:" + map_id) % len(variants)
    return variants[idx]


def today_event_effects(map_id, now=None):
    """今日奇遇的 effects 合并结果；无奇遇返回 {}。

    供 combat.py explore() 直接 .get 消费；
    注意：请不要直接修改返回 dict（内部持有数据引用）。
    """
    ev = today_map_event(map_id, now)
    if not ev:
        return {}
    return ev.get("effects") or {}
