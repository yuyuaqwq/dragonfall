# -*- coding: utf-8 -*-

from ..data import ENCY_MAP_MONSTERS, ENCY_MATERIAL_SOURCE, ENCY_MONSTER_MAP, MAPS


"""《剑与魔法》数据层 - maps.py（v48：派生表 key 用 ID，value 存 ID）"""
def _build_ency():
    for m in MAPS:
        mid = m["id"]
        entries = []
        for (mid_m, mname, role, lv, skills, drops) in (m.get("monsters") or []):
            ENCY_MONSTER_MAP.setdefault(mid_m, []).append((mid, "普通"))
            for d in drops:
                ENCY_MATERIAL_SOURCE.setdefault(d, []).append((mid, mid_m))
            entries.append((mid_m, lv, "普通"))
        if m.get("elite"):
            (eid, estr, erole, elv, eskl, edrops) = m["elite"]
            ENCY_MONSTER_MAP.setdefault(eid, []).append((mid, "精英"))
            for d in edrops:
                ENCY_MATERIAL_SOURCE.setdefault(d, []).append((mid, eid))
            entries.append((eid, elv, "精英"))
        if m.get("boss"):
            (bid, bstr, brole, blv, bskl, bdrops) = m["boss"]
            ENCY_MONSTER_MAP.setdefault(bid, []).append((mid, "首领"))
            for d in bdrops:
                ENCY_MATERIAL_SOURCE.setdefault(d, []).append((mid, bid))
            entries.append((bid, blv, "首领"))
        ENCY_MAP_MONSTERS[mid] = entries
