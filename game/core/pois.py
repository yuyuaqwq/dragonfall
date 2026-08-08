# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - pois.py（v87 02 章 7.6：探索点 POI 系统）

POI 触发与效果结算。纯逻辑：不碰 DB/QQ，效果由命令层落库。
"""
import random


def subarea_pois(map_id: str, subarea_id: str) -> list:
    """返回指定子区域挂载的 POI id 列表（无则空）。"""
    from ..data.pois import SUBAREA_POIS
    key = f"{map_id}:{subarea_id}"
    return SUBAREA_POIS.get(key, [])


def subarea_props(map_id: str, subarea_id: str) -> list:
    """返回指定子区域挂载的场景元素 PROPS id 列表（无则空）。"""
    from ..data.props import SUBAREA_PROPS
    key = f"{map_id}:{subarea_id}"
    return SUBAREA_PROPS.get(key, [])


def roll_poi(group_id: str, qq_id: str, map_id: str, subarea_id: str, chance: float = 0.15):
    """探索时独立判定：chance 概率触发当前子区域随机 POI。

    返回 (poi_id, poi_dict) 或 None。
    """
    ids = subarea_pois(map_id, subarea_id)
    if not ids:
        return None
    if random.random() >= chance:
        return None
    poi_id = random.choice(ids)
    from ..data.pois import POIS
    return poi_id, POIS.get(poi_id, {})
