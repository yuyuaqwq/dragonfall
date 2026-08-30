# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - pois.py（v87 02 章 7.6：探索点 POI 系统）

POI 触发与效果结算。纯逻辑：不碰 DB/QQ，效果由命令层落库。
"""
import random


def subarea_pois(map_id: str, subarea_id: str) -> list:
    """返回指定子区域挂载的 POI id 列表(无则空)。

    注（v141 审计 2026-08-30）：大陆克隆 subareas 当前无命令层消费，
    保留待动态化——副本内 POI 查询走 instance.py 直读数据表（_map_scene/_enter_stage
    经 C.subarea_pois 以克隆图 id 查询全局 SUBAREA_POIS，非克隆 subareas 字段）。
    """
    from ..data.pois import SUBAREA_POIS
    key = f"{map_id}:{subarea_id}"
    return SUBAREA_POIS.get(key, [])


def subarea_props(map_id: str, subarea_id: str) -> list:
    """返回指定子区域挂载的场景元素 PROPS 列表（无则空）。

    元素为 prop id 字符串，或 (prop_id, 专属名) 元组——元组表示该处
    使用专属名显示/交互（同一 prop 在不同子区域可有不同名字）。
    """
    from ..data.props import SUBAREA_PROPS
    key = f"{map_id}:{subarea_id}"
    return SUBAREA_PROPS.get(key, [])


def prop_entry(entry):
    """PROPS 挂载条目 → (prop_id, display_name 或 None)。

    支持 str（用默认名）或 (prop_id, 专属名) 元组（v87.11 专属命名）。
    """
    if isinstance(entry, (tuple, list)) and len(entry) >= 2:
        return entry[0], entry[1]
    return entry, None


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
