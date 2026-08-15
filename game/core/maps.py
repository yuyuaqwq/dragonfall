# -*- coding: utf-8 -*-

from ..data import ENCY_MAP_MONSTERS, ENCY_MATERIAL_SOURCE, ENCY_MONSTER_MAP, MAPS, SUBAREAS
from .constants import SUB_TYPE_GATE, SUB_TYPE_STREET, SUB_TYPE_TOWN  # v102.1 类型常量


"""《剑与魔法》数据层 - maps.py（v48：派生表 key 用 ID，value 存 ID）
v87.6：内容下沉子区域，百科表从 SUBAREAS 构建（地图级字段已清空）。
v87.14：空间连接规则——子区域相邻关系 + 城门出入。
v115：网状子区域核心——subarea_links 切到 SUBAREA_LINKS_INDEX（显式网状，
      含隐藏房间不过滤，可见性由命令层过滤）；新增 subarea_depth /
      is_hidden_room / reveal_met / reveal_progress / bump_explore_count。
"""


def _subarea_links_index():
    """延迟取网状拓扑表（防 data/_assembly 装配期循环导入时机问题，
    与 `from .. import db` 同模式）。无显式定义返回空 dict。"""
    from ..data import SUBAREA_LINKS_INDEX
    return SUBAREA_LINKS_INDEX or {}


def _build_ency():
    for m in MAPS:
        mid = m["id"]
        mname_cn = m["name"]  # 地图中文名（显示用）
        entries = []
        sas = SUBAREAS.get(mid, [])
        for sa in sas:
            for (mid_m, mname, role, lv, skills, drops) in (sa.get("monsters") or []):
                # v101.29：key/显示统一用中文名——v48 ID 重构后百科查询端
                # 用中文名查 ID-keyed 表恒失效（材料/怪物/地图查询全坏），
                # 且掉落来源显示会泄漏 m_*/map_id 内部 ID
                ENCY_MONSTER_MAP.setdefault(mname, []).append((mname_cn, "普通"))
                for d in drops:
                    ENCY_MATERIAL_SOURCE.setdefault(d, []).append((mname_cn, mname))
                entries.append((mname, lv, "普通"))
            if sa.get("elite"):
                (eid, estr, erole, elv, eskl, edrops) = sa["elite"]
                ENCY_MONSTER_MAP.setdefault(estr, []).append((mname_cn, "精英"))
                for d in edrops:
                    ENCY_MATERIAL_SOURCE.setdefault(d, []).append((mname_cn, estr))
                entries.append((estr, elv, "精英"))
            if sa.get("boss"):
                (bid, bstr, brole, blv, bskl, bdrops) = sa["boss"]
                ENCY_MONSTER_MAP.setdefault(bstr, []).append((mname_cn, "首领"))
                for d in bdrops:
                    ENCY_MATERIAL_SOURCE.setdefault(d, []).append((mname_cn, bstr))
                entries.append((bstr, blv, "首领"))
        ENCY_MAP_MONSTERS[mid] = entries
        ENCY_MAP_MONSTERS[mname_cn] = entries  # v101.29 双 key：玩家输中文地图名也能查


def subarea_links(map_id: str, subarea_id: str) -> list:
    """同图内可直达的子区域 id 列表（v87.14 空间连接 + v87.16 街道链 + v115 网状）。

    v115：若 SUBAREA_LINKS_INDEX 有该图的显式网状定义 → 返回该子区域的显式
    连接列表（**包含隐藏房间，不过滤**——隐藏房间的可见性由命令层过滤，这是
    与 G agent 的契约）；否则回退旧逻辑（城镇星形/野外线性）完全不变。

    - 城镇区域：星形拓扑——中心广场（首个子区域）连所有场所 + 街道链首；
      普通场所只连广场；城镇街道（如东大街）连 广场 + 城镇出口；
      城镇出口（如镇郊）连城镇街道。
    - 野外/副本：线性拓扑——按列表顺序相邻（i ↔ i+1），入口 _1 是图内枢纽
    """
    mesh = _subarea_links_index().get(map_id)
    if mesh is not None:
        return list(mesh.get(subarea_id, []))
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


# ---- v115 网状子区域核心 ----

def _explore_count(group_id: str, qq_id: str, map_id: str) -> int:
    """当前探索计数：event_state key = reveal_{map_id}_{qq_id}。
    db 函数内延迟导入（见 wild.py 注释：core 模块用 db 必须 from .. import db）。"""
    from .. import db  # noqa: E402
    raw = db.get_event_state("reveal_{}_{}".format(map_id, qq_id))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def subarea_depth(map_id: str, sa_id: str) -> int:
    """从该图首个子区域（入口）BFS 的深度（入口=0）。

    - SUBAREA_LINKS_INDEX 有该图定义 → BFS 展平深度
    - 否则回退列表索引深度（线性，即 subareas 列表中位置）
    """
    sas = SUBAREAS.get(map_id, [])
    if not sas:
        return 0
    mesh = _subarea_links_index().get(map_id)
    if mesh is not None:
        entry = sas[0]["id"]
        dist = {entry: 0}
        queue = [entry]
        while queue:
            cur = queue.pop(0)
            for nxt in mesh.get(cur, ()):
                if nxt not in dist:
                    dist[nxt] = dist[cur] + 1
                    queue.append(nxt)
        return dist.get(sa_id, len(sas))
    idx = next((i for i, s in enumerate(sas) if s["id"] == sa_id), 0)
    return idx


def is_hidden_room(map_id: str, sa_id: str) -> bool:
    """查 SUBAREAS 中该子区域 dict 的 hidden 字段（默认 False）。"""
    for s in SUBAREAS.get(map_id, []):
        if s.get("id") == sa_id:
            return bool(s.get("hidden"))
    return False


def reveal_met(cond, group_id: str, qq_id: str, map_id: str) -> bool:
    """reveal 条件是否满足。cond 形如：
    - "explore:N"：event_state key=reveal_{map}_{qq} 的探索次数 ≥ N
    - "item:道具名"：db.count_item > 0
    无 cond / 未知格式化 → True（开放）。db 函数内延迟导入防循环。"""
    if not cond:
        return True
    if cond.startswith("explore:"):
        try:
            need = int(cond.split(":", 1)[1])
        except (TypeError, ValueError):
            return False
        return _explore_count(group_id, qq_id, map_id) >= need
    if cond.startswith("item:"):
        from .. import db  # noqa: E402
        item = cond.split(":", 1)[1]
        return db.count_item(group_id, qq_id, item) > 0
    return True


def reveal_progress(group_id: str, qq_id: str, map_id: str):
    """返回 (cur, need)——当前探索计数 与 本图需探索次数的最大值。
    本图无 explore: 型 reveal 房间 → 返回 (0, 0)。"""
    needs = []
    for s in SUBAREAS.get(map_id, []):
        cond = s.get("reveal")
        if cond and cond.startswith("explore:"):
            try:
                needs.append(int(cond.split(":", 1)[1]))
            except (TypeError, ValueError):
                pass
    if not needs:
        return (0, 0)
    return _explore_count(group_id, qq_id, map_id), max(needs)


def bump_explore_count(group_id: str, qq_id: str, map_id: str):
    """探索计数 +1（G agent 会在每次野外探索时调用）。
    event_state key = reveal_{map_id}_{qq_id}。"""
    from .. import db  # noqa: E402
    key = "reveal_{}_{}".format(map_id, qq_id)
    db.set_event_state(key, _explore_count(group_id, qq_id, map_id) + 1)
