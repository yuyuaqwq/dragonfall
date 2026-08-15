# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心 - exploration.py（v115 探索见闻/探索进度）

方案五（33_网状子区域与探索扩容方案_v115.md §六）：
- visited_subareas 表按"地图:子区域"粒度记录探索到访；
- 首访奖励：经验 = 图等级 × 8，金币 = 图等级 × 3；隐藏房间首访额外随机 1 个材料；
- 『探索进度』指令按地图 region 字段聚合，展示每域进度与全大陆探索度。

协作接口（§7 契约，G agent 调用）：
    C.exploration_record_visit(group_id, qq_id, map_id, sa_id)
        → 本模块 record_visit 的别名（game/core/__init__.py 导出），到达子区域时调用。
    C.region_progress(qq_id) / C.overall_progress(qq_id) 供『探索进度』指令渲染。

⚠️ 不要模块级 from .. import db——data/_assembly 加载时会循环导入（connection import content）。
所有用 db 的函数内延迟导入（from .. import db）。
"""
import random

from ..data import MAPS, SUBAREAS

# v115 隐藏房间首访奖励的随机材料池（固定池）。
# 以材料中文名为池项，运行时用 C.resolve("materials", 名) 取稳定 mat_ 拼音 id 入包。
_FIRST_VISIT_MAT_POOL = ("草药", "铁矿石", "兽肉", "浆果", "蜂蜜")


def _map_by_id(map_id: str) -> dict:
    """在 MAPS 中按 id 定位地图 dict（避免依赖 _assembly 注入的 subareas 字段）。"""
    for _m in MAPS:
        if _m.get("id") == map_id:
            return _m
    return {}


def _is_hidden(sa: dict) -> bool:
    """子区域是否隐藏房间（v115 新字段 hidden）。"""
    return bool(sa.get("hidden"))


def record_visit(group_id, qq_id, map_id, sa_id) -> dict | None:
    """到达子区域时调用：记录到访 + 首访奖励。

    返回：
      - sa 不存在 / map 无子区域 → None
      - 首访 → {"first": True, "exp": n, "gold": n, "mat": 材料名 or None}
      - 非首访 → {"first": False}
    """
    from .. import db  # noqa: E402（延迟导入防 data/_assembly 循环）

    sas = SUBAREAS.get(map_id) or []
    sa = next((s for s in sas if s.get("id") == sa_id), None)
    if not sas or sa is None:
        return None

    # 判断是否首访（先查集合，命中则非首访）
    visited = db.get_visited_subareas(qq_id)
    key = f"{map_id}:{sa_id}"
    if key in visited:
        return {"first": False}

    # 首访：记录 + 发奖
    db.add_visited_subarea(group_id, qq_id, map_id, sa_id)
    cur = _map_by_id(map_id)
    lv = int(cur.get("lv", 1) or 1)
    exp = lv * 8
    gold = lv * 3

    player = db.get_player(group_id, qq_id)
    if player:
        # v115 §6.2：只加数值，不处理升级（get_player 读档有惰性升级兜底，审计确认无副作用）
        db.update_player(group_id, qq_id,
                         exp=player.get("exp", 0) + exp,
                         gold=player.get("gold", 0) + gold)

    mat = None
    if _is_hidden(sa):
        # 隐藏房间首访额外随机 1 个材料入包
        name = random.choice(_FIRST_VISIT_MAT_POOL)
        mat_id = C_resolve_material(name)
        if mat_id:
            mat_name = C_display_material(mat_id)
            db.add_item(group_id, qq_id, mat_id,
                        {"name": mat_name, "type": "材料", "stackable": True,
                         "price": C_material_price(mat_id)})
            mat = mat_name or name
        else:
            mat = name

    # v115 协作契约：reward 为给命令层拼接展示的友好文案（world.py _subarea_arrive/传送
    # 读取 rv["reward"] → 追加 "🎉 {reward}"）。隐藏房间首访附材料，普通首访仅经验/金币。
    _reward = f"首次探索（{lv} 级区域）！获得经验 +{exp}、金币 +{gold}"
    if mat:
        _reward += f"，并拾得 {mat}"
    return {"first": True, "exp": exp, "gold": gold, "mat": mat, "reward": _reward}


def region_progress(qq_id) -> list:
    """按地图 region 字段聚合：返回 [{region, total, visited, hidden_total, hidden_found}, ...]。

    - total        该 region 全部地图的非隐藏子区域数
    - visited      其中已到访（非隐藏）计数
    - hidden_total 该 region 的隐藏房间总数
    - hidden_found 其中已到访的隐藏房间计数
    region 顺序按 MAPS 出现顺序去重。
    """
    from .. import db  # noqa: E402

    visited = db.get_visited_subareas(qq_id)

    # 按 region 聚合统计
    agg = {}          # region -> 统计 dict
    order = []        # region 出现顺序
    for _m in MAPS:
        region = _m.get("region") or ""
        sas = SUBAREAS.get(_m.get("id")) or []
        if not sas:
            continue
        if region not in agg:
            agg[region] = {"region": region, "total": 0, "visited": 0,
                           "hidden_total": 0, "hidden_found": 0}
            order.append(region)
        st = agg[region]
        for _sa in sas:
            is_hidden = _is_hidden(_sa)
            hit = f"{_m['id']}:{_sa['id']}" in visited
            if is_hidden:
                st["hidden_total"] += 1
                if hit:
                    st["hidden_found"] += 1
            else:
                st["total"] += 1
                if hit:
                    st["visited"] += 1

    return [agg[r] for r in order]


def overall_progress(qq_id) -> dict:
    """全大陆探索度：{visited, total, hidden_found, hidden_total, pct}。"""
    agg = region_progress(qq_id)
    visited = sum(r["visited"] for r in agg)
    total = sum(r["total"] for r in agg)
    hidden_found = sum(r["hidden_found"] for r in agg)
    hidden_total = sum(r["hidden_total"] for r in agg)
    pct = int(round(visited * 100.0 / total)) if total else 0
    return {"visited": visited, "total": total,
            "hidden_found": hidden_found, "hidden_total": hidden_total, "pct": pct}


# ---- 材料解析辅助（延迟导入 C 即可用，防模块级循环）----
def _content():
    from .. import content as _c  # noqa: E402
    return _c


def C_resolve_material(name):
    """材料中文名 → mat_ 拼音 id（查不到返回原名字，add_item 兜底）。"""
    try:
        return _content().resolve("materials", name)
    except Exception:
        return name


def C_display_material(mat_id):
    """mat_ id → 显示名。"""
    return _content().display("materials", mat_id)


def C_material_price(mat_id):
    """mat_ id → 商店价（无定义给 10）。"""
    try:
        m = _content().MATERIALS.get(mat_id, {})
        return m.get("price", 10)
    except Exception:
        return 10
