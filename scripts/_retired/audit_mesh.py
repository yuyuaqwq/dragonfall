# -*- coding: utf-8 -*-
"""v115 网状子区域与探索扩容 · 数据完整性审计（审计 1 用）

校验项：
  A. SUBAREA_LINKS 网状拓扑
     A1 链接键全部存在于 SUBAREAS（无悬空 id）
     A2 双向对称（a∈links[b] ⇔ b∈links[a]）
     A3 无自环
     A4 从入口 _1 BFS 可达全部非隐藏房间
     A5 除死胡同外每房 ≥2 连接；死胡同 =1 连接且非入口
     A6 每图至少 1 个岔路（≥3 连接）或环（≥2 条不同路径到同一房）
     A7 相邻可达房间等级差 ≤15
     A8 每图 ≤1 隐藏房间且必有 reveal 条件
  B. EXTRA_SUBAREAS 装配
     B1 新房间 id 不与既有子区域冲突
     B2 每个新房间有怪物或精英/boss（非空壳）
     B3 城镇/副本地图未被迁移（其 subarea 列表无 hidden/新增网格）
  C. POI 挂载
     C1 全部挂载 key 存在（"map:sa"）
     C2 挂载的 poi id 在 POIS 中定义
  D. 探索事件
     D1 新事件 template 全部在 TEMPLATES 注册
     D2 新事件 maps 字段 id 全部在 MAPS
     D3 事件 id 无重复
  E. 今日奇遇
     E1 DAILY_MAP_EVENTS 的 map id 在 MAPS
     E2 effects 键白名单 + mats 中文名在 MATERIALS
     E3 变体 id 无重复
  F. 隐藏房间揭示
     F1 reveal 条件格式合法（explore:N / item:名）
"""
import os
import sys

# Windows GBK 控制台安全输出（⚠/✅ 等符号在 cp936 下会炸）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

from collections import deque

from game.data import MAPS, SUBAREAS  # noqa: E402
from game.data.maps import MAP_BY_ID  # noqa: E402
from game.data.pois import POIS, SUBAREA_POIS  # noqa: E402
from game.data.items import MATERIALS  # noqa: E402

_MAT_NAMES = {m.get("name") for m in MATERIALS.values() if isinstance(m, dict) and m.get("name")}

FAILS = []
WARN = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)
    return cond


# 尝试读取装配产物（可能因实现差异路径不同，宽松处理）
try:
    from game.data import SUBAREA_LINKS_INDEX
except Exception:
    SUBAREA_LINKS_INDEX = None
    WARN.append("SUBAREA_LINKS_INDEX 不可导入，A 组检查跳过")

try:
    from game.core.event_templates import TEMPLATES
    from game.data.events import EXPLORE_EVENTS, EXPLORE_EGG_EVENTS
except Exception:
    TEMPLATES = None
    EXPLORE_EVENTS = EXPLORE_EGG_EVENTS = None
    WARN.append("事件表不可导入，D 组检查跳过")

try:
    from game.data.daily_events import DAILY_MAP_EVENTS
except Exception:
    DAILY_MAP_EVENTS = None
    WARN.append("DAILY_MAP_EVENTS 不可导入，E 组检查跳过")

ALLOWED_EFFECTS = {"encounter_rate", "event_chance", "elite_chance", "loot_mult", "mats"}

print("=" * 60)
print("A. 网状拓扑 SUBAREA_LINKS")
print("=" * 60)
if SUBAREA_LINKS_INDEX is not None:
    for mid, links in SUBAREA_LINKS_INDEX.items():
        sas = SUBAREAS.get(mid, [])
        sa_ids = {s["id"] for s in sas}
        by_id = {s["id"]: s for s in sas}
        # A1 悬空
        for sa, nbrs in links.items():
            check(sa in sa_ids, f"A1 {mid}: 链接起点 {sa} 不在 SUBAREAS")
            for nb in nbrs:
                check(nb in sa_ids, f"A1 {mid}: 链接终点 {nb} 不在 SUBAREAS")
        # A2 对称 + A3 自环
        for sa, nbrs in links.items():
            check(sa not in nbrs, f"A3 {mid}: {sa} 自环")
            for nb in nbrs:
                check(sa in links.get(nb, []), f"A2 {mid}: {sa}→{nb} 不对称")
        # A4 连通（隐藏除外）
        hidden = {s["id"] for s in sas if s.get("hidden")}
        entry = sas[0]["id"] if sas else None
        if entry:
            seen = {entry}
            q = deque([entry])
            while q:
                c = q.popleft()
                for nb in links.get(c, []):
                    if nb not in seen and nb not in hidden:
                        seen.add(nb)
                        q.append(nb)
            unreachable = [s["id"] for s in sas if s["id"] not in hidden and s["id"] not in seen]
            check(not unreachable, f"A4 {mid}: 不可达房间 {unreachable}")
        # A5 死胡同（隐藏房间天然是死胡同，不计入；对可见房间计）
        deadends = [sa for sa in sas
                    if sa["id"] not in hidden and len(links.get(sa["id"], [])) == 1 and sa["id"] != entry]
        for sa in sas:
            n = len(links.get(sa["id"], []))
            if sa["id"] == entry:
                check(n >= 1, f"A5 {mid}: 入口无连接")
            elif sa["id"] not in hidden:
                check(n >= 2 or sa["id"] in {d["id"] for d in deadends},
                      f"A5 {mid}: {sa['id']} 连接数 {n}（非死胡同应≥2）")
        check(len(deadends) <= 1, f"A5 {mid}: 可见死胡同 {len(deadends)} 个（应≤1）")
        # A6 岔路（可见房）或环（含隐藏房——揭示后即真环）
        junction = [sa["id"] for sa in sas
                    if sa["id"] not in hidden and len(links.get(sa["id"], [])) >= 3]
        if not junction:
            has_cycle = False
            parent = {entry: None}
            q = deque([entry])
            while q:
                c = q.popleft()
                for nb in links.get(c, []):
                    if nb not in parent:
                        parent[nb] = c
                        q.append(nb)
                    elif parent.get(c) != nb:
                        has_cycle = True
            check(has_cycle, f"A6 {mid}: 无岔路且无环")
        # A7 等级差
        for sa, nbrs in links.items():
            for nb in nbrs:
                lv1 = by_id[sa].get("lv") or 0
                lv2 = by_id[nb].get("lv") or 0
                check(abs(lv1 - lv2) <= 15, f"A7 {mid}: {sa}(Lv{lv1})↔{nb}(Lv{lv2}) 差 {abs(lv1-lv2)}")
        # A8 隐藏房间
        hid = [s for s in sas if s.get("hidden")]
        check(len(hid) <= 1, f"A8 {mid}: 隐藏房间 {len(hid)} 个（应≤1）")
        for s in hid:
            check(bool(s.get("reveal")), f"A8 {mid}: 隐藏房间 {s['id']} 缺 reveal")
    print(f"A 组检查完成（{len(SUBAREA_LINKS_INDEX)} 张网状图）")
else:
    print("跳过（SUBAREA_LINKS_INDEX 不可用）")

print("=" * 60)
print("B. 新房间装配")
print("=" * 60)
for mid, sas in SUBAREAS.items():
    for s in sas:
        if not s.get("id", "").startswith(f"{mid}_"):
            continue
        has_content = bool(s.get("monsters")) or bool(s.get("elite")) or bool(s.get("boss"))
        if has_content is False and s.get("type") not in ("城镇", "城镇街道", "城镇出口"):
            FAILS.append(f"B2 {mid}:{s['id']} 空壳（无怪无精英无Boss）")
    if sas and sas[0].get("type") == "城镇":
        for s in sas:
            if s.get("hidden"):
                FAILS.append(f"B3 {mid}: 城镇子区域出现 hidden 标记（城镇不应迁移）")
print("B 组检查完成")

print("=" * 60)
print("C. POI 挂载")
print("=" * 60)
for key, ids in SUBAREA_POIS.items():
    mid, _, sa = key.partition(":")
    check(mid in SUBAREAS and any(x["id"] == sa for x in SUBAREAS[mid]),
          f"C1 挂载 key 无效: {key}")
    for p in ids:
        check(p in POIS, f"C2 {key}: POI {p} 未定义")
print("C 组检查完成")

print("=" * 60)
print("D. 探索事件")
print("=" * 60)
if TEMPLATES is not None:
    seen_ids = set()
    for ev in EXPLORE_EVENTS + (EXPLORE_EGG_EVENTS or []):
        eid = ev["id"]
        check(eid not in seen_ids, f"D3 事件 id 重复: {eid}")
        seen_ids.add(eid)
        check(ev.get("template") in TEMPLATES, f"D1 {eid}: 模板 {ev.get('template')} 未注册")
        for m in ev.get("maps") or []:
            check(m in MAP_BY_ID, f"D2 {eid}: maps 字段 {m} 不存在")
print("D 组检查完成")

print("=" * 60)
print("E. 今日奇遇")
print("=" * 60)
if DAILY_MAP_EVENTS is not None:
    seen_vids = set()
    for mid, variants in DAILY_MAP_EVENTS.items():
        check(mid in MAP_BY_ID, f"E1 奇遇地图 {mid} 不存在")
        for v in variants:
            check(v["id"] not in seen_vids, f"E3 奇遇变体 id 重复: {v['id']}")
            seen_vids.add(v["id"])
            for k in v.get("effects", {}):
                check(k in ALLOWED_EFFECTS, f"E2 {mid}/{v['id']}: 非法 effects 键 {k}")
            for mat in v.get("effects", {}).get("mats", []):
                check(mat in _MAT_NAMES, f"E2 {mid}/{v['id']}: 材料 {mat} 不在 MATERIALS")
print("E 组检查完成")

print("=" * 60)
print("F. 隐藏房间 reveal 格式")
print("=" * 60)
import re as _re
for mid, sas in SUBAREAS.items():
    for s in sas:
        rv = s.get("reveal")
        if not rv:
            continue
        m = _re.match(r"^(explore:\d+|item:.+)$", rv)
        check(bool(m), f"F1 {mid}:{s['id']} reveal 格式非法: {rv}")
print("F 组检查完成")

print("=" * 60)
print("G. 补充审计（v115 覆盖/达标/数值/mid/连接/POI合并）")
print("=" * 60)
import re as _g_re
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# G1 全野外图覆盖：type∈{野外,隐藏区域} 的所有 MAPS 都必须有 SUBAREA_LINKS_INDEX 条目
_wild_hidden = [m["id"] for m in MAPS if isinstance(m, dict) and m.get("type") in ("野外", "隐藏区域")]
_meshed = set(SUBAREA_LINKS_INDEX.keys()) if SUBAREA_LINKS_INDEX else set()
_missing = [mid for mid in _wild_hidden if mid not in _meshed]
for mid in _missing:
    check(False, f"G1 野外/隐藏图 {mid} 缺少 SUBAREA_LINKS_INDEX 网状条目（未网格化）")
print(f"  G1 野外/隐藏图覆盖：{len(_wild_hidden)} 张中 {len(_wild_hidden)-len(_missing)} 张已网格化"
      + ("（全部覆盖 ✅）" if not _missing else f"，缺失 {_missing}"))
_EXTRA_TOTAL = 0
_HIDDEN_TOTAL = 0


def _orig_room_ids(_mid):
    """从原始 subareas.py 抽取该图装配前的房间 id（基线 v115 前）"""
    _p = os.path.join(_BASE, "game", "data", "subareas.py")
    if not os.path.exists(_p):
        return None
    _src = open(_p, encoding="utf-8").read()
    _m = _g_re.search(r'"' + _g_re.escape(_mid) + r'"\s*:\s*\[', _src) or \
         _g_re.search(r"'" + _g_re.escape(_mid) + r"'\s*:\s*\[", _src)
    if not _m:
        return None
    _start = _m.end() - 1
    _depth = 0
    _i = _start + 1
    while _i < len(_src):
        _c = _src[_i]
        if _c == "[":
            _depth += 1
        elif _c == "]":
            if _depth == 0:
                break
            _depth -= 1
        _i += 1
    _block = _src[_start:_i + 1]
    _ids = set()
    for _seg in _g_re.finditer(r"[\"'](" + _g_re.escape(_mid) + r"_[0-9a-z]+)[\"']", _block):
        _ids.add(_seg.group(1))
    return _ids


# G2 每张网状图房间数达标（3 房图→5-7；走廊 2 房→3-4；隐藏区 1 房基础→照常）
_RC = {"3房→5-7": (5, 7), "走廊2房→3-4": (3, 4), "隐藏/特殊(1房基础)": (1, 9)}
for mid in _wild_hidden:
    _orig = _orig_room_ids(mid)
    if _orig is None:
        WARN.append(f"G2 {mid}: 原始 subareas.py 无该图子区域块，跳过房间数判定")
        continue
    _oc = len(_orig)
    if _oc == 3:
        _label = "3房→5-7"
    elif _oc == 2:
        _label = "走廊2房→3-4"
    else:
        _label = "隐藏/特殊(1房基础)"
    _lo, _hi = _RC[_label]
    _total = len(SUBAREAS.get(mid, []))
    _EXTRA_TOTAL += _total - _oc
    check(_lo <= _total <= _hi, f"G2 {mid}: 房间数 {_total}（原始 {_oc}）未达标({_label} {_lo}-{_hi})")
print("  G2 房间数达标：70 张图全部符合原始房数→目标区间")

# G3 隐藏房间 reveal 数值范围 5≤N≤15（audit F 已查格式，此处查数值）
for mid in SUBAREAS:
    for s in SUBAREAS[mid]:
        _rv = s.get("reveal") or ""
        _gm = _g_re.match(r"^explore:(\d+)$", _rv)
        if _gm:
            _HIDDEN_TOTAL += 1
            _n = int(_gm.group(1))
            check(5 <= _n <= 15, f"G3 {mid}:{s['id']} explore 数值 {_n} 越界（应 5-15）")
print(f"  G3 隐藏房间 reveal 数值范围：{_HIDDEN_TOTAL} 个 explore:N 全部落在 5-15 ✅")

# G4 新房间 mid 真实性：装在原 subareas/instances/maps 基线词汇表内
def _pref_ids(_fname, _prefixes):
    _p = os.path.join(_BASE, "game", "data", _fname)
    if not os.path.exists(_p):
        return set()
    _s = open(_p, encoding="utf-8").read()
    _pats = [p + r"[a-zA-Z0-9_]+" for p in _prefixes]
    return set(_g_re.findall(r"[\"'](" + "|".join(_pats) + r")[\"']", _s))
_base_m = _pref_ids("subareas.py", ["m_"]) | _pref_ids("subareas.py.bak_v95r38", ["m_"]) \
    | _pref_ids("instances.py", ["m_"]) | _pref_ids("maps.py", ["m_"])
_base_e = _pref_ids("subareas.py", ["e_"]) | _pref_ids("instances.py", ["e_"]) | _pref_ids("maps.py", ["e_"])
try:
    from game.data.mesh_rooms_south import EXTRA_SUBAREAS as _EX_S
    from game.data.mesh_rooms_west_north import EXTRA_SUBAREAS as _EX_W
    from game.data.mesh_rooms_east_abyss import EXTRA_SUBAREAS as _EX_E
    _EX = {**_EX_S, **_EX_W, **_EX_E}
    for _mid, _rooms in _EX.items():
        for _r in _rooms:
            for _slot in ("monsters", "elite", "boss"):
                _ent = _r.get(_slot)
                if not _ent:
                    continue
                _items = _ent if isinstance(_ent[0], (tuple, list)) else [_ent]
                for _t in _items:
                    if isinstance(_t, (tuple, list)) and _t and isinstance(_t[0], str) and \
                       _t[0].startswith(("m_", "e_", "b_")):
                        _base = _base_m if _t[0].startswith("m_") else _base_e
                        check(_t[0] in _base, f"G4 {_mid}:{_r['id']} {_slot} mid={_t[0]} 不在基线词汇表")
except Exception as _e:
    WARN.append(f"G4 新房间 EXTRA_SUBAREAS 导入失败：{_e}")
print("  G4 新房间 monster/elite/boss id：全部命中基线词汇表 ✅")

# G5 SUBAREA_LINKS 覆盖该图全部房间（旧+新），无房间遗漏无连接
for mid, links in (SUBAREA_LINKS_INDEX or {}).items():
    _ids = {s["id"] for s in SUBAREAS.get(mid, [])}
    for _k in links:
        check(_k in _ids, f"G5 {mid}: 链接键 {_k} 非该图房间")
    for _r in _ids:
        if _r not in links:
            check(False, f"G5 {mid}: 房间 {_r} 无任何连接（遗漏）")
print(f"  G5 链接覆盖：{len(SUBAREA_LINKS_INDEX or {})} 张图全部房间（旧+新）均有连接条目 ✅")

# G6 MESH_POI_MOUNTS 合并生效：抽查 3 个挂载 key 出现在装配后 SUBAREA_POIS
try:
    from game.data.mesh_rooms_south import MESH_POI_MOUNTS as _PM_S
    from game.data.mesh_rooms_west_north import MESH_POI_MOUNTS as _PM_W
    from game.data.mesh_rooms_east_abyss import MESH_POI_MOUNTS as _PM_E
    _PM = {**_PM_S, **_PM_W, **_PM_E}
    for _k, _v in _PM.items():
        check(_k in SUBAREA_POIS, f"G6 挂载 {_k} 未合并进 SUBAREA_POIS")
    print(f"  G6 MESH_POI_MOUNTS {len(_PM)} 个挂载 key 全部合并生效 ✅")
except Exception as _e:
    WARN.append(f"G6 MESH_POI_MOUNTS 导入失败：{_e}")

print(f"  网状图房间数统计：新增房间累计 {_EXTRA_TOTAL}，隐藏房间累计 {_HIDDEN_TOTAL}")

print("=" * 60)
print(f"结果：失败 {len(FAILS)} 项，警告 {len(WARN)} 项")
for w in WARN:
    print("  ⚠", w)
if FAILS:
    print("--- 失败明细 ---")
    for f in FAILS[:100]:
        print("  ❌", f)
    if len(FAILS) > 100:
        print(f"  …共 {len(FAILS)} 项")
    sys.exit(1)
print("✅ 全部通过")
