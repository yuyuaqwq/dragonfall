# -*- coding: utf-8 -*-

from ..data import ENCY_MAP_MONSTERS, ENCY_MATERIAL_SOURCE, ENCY_MONSTER_MAP, MAPS, SUBAREAS
from .constants import SUB_TYPE_GATE, SUB_TYPE_STREET, SUB_TYPE_TOWN  # v102.1 类型常量


"""《剑与魔法》数据层 - maps.py（v48：派生表 key 用 ID，value 存 ID）
v87.6：内容下沉子区域，百科表从 SUBAREAS 构建（地图级字段已清空）。
v87.14：空间连接规则——子区域相邻关系 + 城门出入。
"""


def _build_ency():
    for m in MAPS:
        mid = m["id"]
        entries = []
        sas = SUBAREAS.get(mid, [])
        for sa in sas:
            for (mid_m, mname, role, lv, skills, drops) in (sa.get("monsters") or []):
                ENCY_MONSTER_MAP.setdefault(mid_m, []).append((mid, "普通"))
                for d in drops:
                    ENCY_MATERIAL_SOURCE.setdefault(d, []).append((mid, mid_m))
                entries.append((mid_m, lv, "普通"))
            if sa.get("elite"):
                (eid, estr, erole, elv, eskl, edrops) = sa["elite"]
                ENCY_MONSTER_MAP.setdefault(eid, []).append((mid, "精英"))
                for d in edrops:
                    ENCY_MATERIAL_SOURCE.setdefault(d, []).append((mid, eid))
                entries.append((eid, elv, "精英"))
            if sa.get("boss"):
                (bid, bstr, brole, blv, bskl, bdrops) = sa["boss"]
                ENCY_MONSTER_MAP.setdefault(bid, []).append((mid, "首领"))
                for d in bdrops:
                    ENCY_MATERIAL_SOURCE.setdefault(d, []).append((mid, bid))
                entries.append((bid, blv, "首领"))
        ENCY_MAP_MONSTERS[mid] = entries


def subarea_links(map_id: str, subarea_id: str) -> list:
    """同图内可直达的子区域 id 列表（v87.14 空间连接 + v87.16 街道链）。

    - 城镇区域：星形拓扑——中心广场（首个子区域）连所有场所 + 街道链首；
      普通场所只连广场；城镇街道（如东大街）连 广场 + 城镇出口；
      城镇出口（如镇郊）连城镇街道。
    - 野外/副本：线性拓扑——按列表顺序相邻（i ↔ i+1），入口 _1 是图内枢纽
    """
    sas = SUBAREAS.get(map_id, [])
    if not sas:
        return []
    idx = next((i for i, s in enumerate(sas) if s["id"] == subarea_id), None)
    if idx is None:
        return []
    center = sas[0]
    if center.get("type") == SUB_TYPE_TOWN:
        cur_type = sas[idx].get("type")
        if subarea_id == center["id"]:
            # 广场连所有场所 + 街道链首（不含城镇出口——镇郊需经东大街）
            out = [s["id"] for s in sas
                   if s["id"] != center["id"] and s.get("type") != SUB_TYPE_GATE]
            # v95.12 无街道链城镇（白鹿城/铁港城）对称防断链：广场直连出口，
            # 否则广场→出口 "先经过XX(自己)" 死循环，玩家出不了城
            if not any(s.get("type") == SUB_TYPE_STREET for s in sas):
                out += [s["id"] for s in sas if s.get("type") == SUB_TYPE_GATE]
            return out
        if cur_type == SUB_TYPE_STREET:
            # 街道：连出口（链尾）+ 广场（链首）
            out = [s["id"] for s in sas if s.get("type") == SUB_TYPE_GATE]
            out.append(center["id"])
            return out
        if cur_type == SUB_TYPE_GATE:
            # 出口：只连城镇街道（链首）；无街道时直连广场（防断链，v95 实测白鹿城/铁港城缺街道）
            streets = [s["id"] for s in sas if s.get("type") == SUB_TYPE_STREET]
            if streets:
                return streets
            return [center["id"]]
        return [center["id"]]
    # 线性
    out = []
    if idx > 0:
        out.append(sas[idx - 1]["id"])
    if idx < len(sas) - 1:
        out.append(sas[idx + 1]["id"])
    return out


def map_exit_subarea(map_id: str) -> str:
    """离开该图必须所在的子区域（v87.14 + v87.16）。

    - 城镇：城镇出口子区域（镇郊）；无城镇出口则退回 _gate 结尾（旧数据）
    - 非城镇：首个子区域（入口）
    """
    sas = SUBAREAS.get(map_id, [])
    if not sas:
        return ""
    if sas[0].get("type") == SUB_TYPE_TOWN:
        for s in sas:
            if s.get("type") == SUB_TYPE_GATE:
                return s["id"]
        for s in sas:
            if s["id"].endswith("_gate"):
                return s["id"]
    return sas[0]["id"]


def map_entry_subarea(map_id: str) -> str:
    """跨图进入该图的落点子区域（v87.14 + v87.16）。

    - 城镇：城镇出口子区域（从野外进城先到镇郊，再经东大街进广场）
    - 非城镇：首个子区域（入口）
    注：注册/传送/回家等"城内直达"场景用 subareas[0]（广场），不走城门。
    """
    sas = SUBAREAS.get(map_id, [])
    if not sas:
        return ""
    if sas[0].get("type") == SUB_TYPE_TOWN:
        for s in sas:
            if s.get("type") == SUB_TYPE_GATE:
                return s["id"]
        for s in sas:
            if s["id"].endswith("_gate"):
                return s["id"]
    return sas[0]["id"]
