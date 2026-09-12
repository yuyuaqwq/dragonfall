# -*- coding: utf-8 -*-

from ..data import ENCY_MAP_MONSTERS, ENCY_MATERIAL_SOURCE, ENCY_MONSTER_MAP, MAPS, SUBAREAS, MONSTER_LOCS
from .constants import SUB_TYPE_GATE, SUB_TYPE_STREET, SUB_TYPE_TOWN  # v102.1 类型常量


"""奥兰迪亚·余烬纪年数据层 - maps.py（v48：派生表 key 用 ID，value 存 ID）
v87.6：内容下沉子区域，百科表从 SUBAREAS 构建（地图级字段已清空）。
v87.14：空间连接规则——子区域相邻关系 + 城门出入。
v115：网状子区域核心——subarea_links 切到 SUBAREA_LINKS_INDEX（显式网状，
      含隐藏房间不过滤，可见性由命令层过滤）；新增 subarea_depth /
      is_hidden_room / reveal_met / reveal_progress / bump_explore_count。
v183（2026-09-12）：**几何形状搬进引擎** `saintess_engine.space` —— 邻接 / 深度 /
      出入口 / 必经路径由引擎 `Space` 派生，本文件只留「角色映射」适配：
      子区域 type → 角色（hub/through/exit）+ 首节点角色 → 拓扑（star/chain）。
      对外函数名与返回**一字不变**（逐格一致由 tests/test_v183_space_shape.py
      用「冻结的旧实现」全图比对守护）。
"""


def _subarea_links_index():
    """延迟取网状拓扑表（防 data/_assembly 装配期循环导入时机问题，
    与 `from .. import db` 同模式）。无显式定义返回空 dict。"""
    from ..data import SUBAREA_LINKS_INDEX
    return SUBAREA_LINKS_INDEX or {}


# ---- v183 引擎形状适配：本游戏的「角色映射」----------------------------------
# 引擎只认角色名（hub/through/exit），**取值**由内容侧给 —— 这三条映射就是全部内容。
_ROLES = {"hub": "hub", "through": "through", "exit": "exit"}
_ROLE_BY_TYPE = {
    SUB_TYPE_TOWN: "hub",        # 中心广场（首个子区域）
    SUB_TYPE_STREET: "through",  # 如东大街：枢纽 ↔ 出口的通道层
    SUB_TYPE_GATE: "exit",       # 如镇郊：出城/进城落点
}


def map_space(map_id: str):
    """本图的引擎 `Space`（节点 = 子区域，角色 = type 映射；显式连通表优先）。

    不缓存：`SUBAREAS` 运行期可被副本克隆增补（缓存会读到半成品）；构造很便宜
    （每图 ≤ 十余节点），移动路径上的调用量级可接受。
    """
    from saintess_engine.space import MESH, Space
    sas = SUBAREAS.get(map_id) or []
    nodes = [{"id": s["id"], "name": s.get("name"), "role": _ROLE_BY_TYPE.get(s.get("type"))}
             for s in sas]
    mesh = _subarea_links_index().get(map_id)
    # 旧数据兜底（v87 时期的老图）：城里没有「城镇出口」类型节点时，出入口退回
    # id 以 `_gate` 结尾者。属**内容策略**（引擎不认识 id 命名习惯），故在适配层算好传进去。
    gate_override = None
    if (nodes and nodes[0]["role"] == _ROLES["hub"]
            and not any(n["role"] == _ROLES["exit"] for n in nodes)):
        gate_override = next((n["id"] for n in nodes if str(n["id"]).endswith("_gate")), None)
    if mesh is not None:
        return Space(nodes=nodes, topology=MESH, roles=_ROLES, links=mesh,
                     label_key="name", gate=gate_override)
    topo = "star" if (nodes and nodes[0]["role"] == _ROLES["hub"]) else "chain"
    return Space(nodes=nodes, topology=topo, roles=_ROLES, label_key="name", gate=gate_override)


def map_center(map_id: str) -> str:
    """枢纽节点 id（星形图的中心）；链状/网状图无枢纽 → ""。"""
    sp = map_space(map_id)
    return sp.root if sp.role_of(sp.root) == _ROLES["hub"] else ""


def map_route(map_id: str, src: str, dst: str) -> list:
    """同图必经路径（**含两端**）；同点 → 单元素；任一端未知或不可达 → []。

    用途：把「不能直达，需要先经过 X、Y」这类提示从手算改成问引擎
    （v183 之前该判断在 travel / world 各抄了一份星形链首逻辑）。
    """
    return map_space(map_id).route(src, dst)


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

def _build_monster_locs():
    """v130.3 意见#3：怪名 → [(子区域显示名, 地图名, 等级, 类型)] 详细分布（含等级/子区域粒度）"""
    for m in MAPS:
        mid, mname_cn = m["id"], m["name"]
        for sa in (SUBAREAS.get(mid) or []):
            sa_name = sa.get("name") or sa.get("id", "")
            for (_, mname, _, lv, _, _) in (sa.get("monsters") or []):
                MONSTER_LOCS.setdefault(mname, []).append((sa_name, mname_cn, lv, "普通"))
            if sa.get("elite"):
                (_, estr, _, elv, _, _) = sa["elite"]
                MONSTER_LOCS.setdefault(estr, []).append((sa_name, mname_cn, elv, "精英"))
            if sa.get("boss"):
                (_, bstr, _, blv, _, _) = sa["boss"]
                MONSTER_LOCS.setdefault(bstr, []).append((sa_name, mname_cn, blv, "首领"))

_build_monster_locs()



def subarea_links(map_id: str, subarea_id: str) -> list:
    """同图内可直达的子区域 id 列表（v183：派生搬进引擎 `saintess_engine.space`）。

    显式网状连通表（SUBAREA_LINKS_INDEX）优先；否则按拓扑派生：**城镇星形
    （枢纽 ↔ 场所、通道 ↔ 出口，含无通道时枢纽直连出口的防断链分支）/ 野外线性**。
    结果**包含隐藏房间，不过滤** —— 隐藏房间的可见性由命令层过滤（历史契约不变）。

    注（v141 审计）：副本大陆克隆的 subareas 无命令层消费本函数 —— 保留待动态化；
    命令层副本移动走 SUBAREA_LINKS_INDEX（instance.py _subarea_arrive 直读数据表）。
    """
    return map_space(map_id).links(subarea_id)


def map_exit_subarea(map_id: str) -> str:
    """离开该图必须所在的子区域（v183：= 引擎 `Space.gate()`）。

    城镇：城镇出口子区域；非城镇：首个子区域（入口）。
    ★ 与 `map_entry_subarea` **同义** —— v183 之前这两份实现逐字重复，现已合一
    （两者都问引擎同一个 gate，名字保留只为调用方零改动）。
    """
    return map_space(map_id).gate()


def map_entry_subarea(map_id: str) -> str:
    """跨图进入该图的落点子区域（v183：= 引擎 `Space.gate()`，与 map_exit_subarea 同义）。

    城镇：出口子区域（从野外进城先到镇郊，再经东大街进广场）；非城镇：首个子区域。
    注：注册/传送/回家等「城内直达」场景用 subareas[0]（广场），不走城门。
    """
    return map_space(map_id).gate()


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
    """从该图首个子区域（入口）算的深度（v183：口径由引擎定）。

    - SUBAREA_LINKS_INDEX 有该图定义 → 从入口 BFS（网状图没有天然顺序）
    - 否则 → 声明序（子区域列表位置：链状/星形图里顺序本身就是作者给的由近及远）
    """
    return map_space(map_id).depth(sa_id)


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
