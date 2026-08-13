# -*- coding: utf-8 -*-
"""M24 诊断 v2：修正 elite/boss 扁平条目解析后的真实清单（临时脚本，用完即删）"""
import sys
from collections import defaultdict

sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")

import game.data as C


def collect_entries(slots_source, slots):
    """修正版解析：兼容条目列表与扁平单条目（elite/boss 6 元组）。"""
    for slot in slots:
        ent = slots_source.get(slot)
        if not ent:
            continue
        if isinstance(ent, (tuple, list)) and ent and isinstance(ent[0], (tuple, list)):
            lst = ent
        else:
            lst = [ent]
        for t in lst:
            if isinstance(t, (tuple, list)) and len(t) >= 2 and isinstance(t[1], str):
                yield t[0], t[1]


n2i = C._INDEXES["monsters"]["name_to_id"]

inst_entries = []
for iid, ins in C.INSTANCES.items():
    for si, stage in enumerate(ins.get("stages") or []):
        if not isinstance(stage, dict):
            continue
        for slot in ("monsters", "elite", "boss"):
            for mid, mname in collect_entries(stage, (slot,)):
                inst_entries.append((iid, si, stage.get("name"), slot, mid, mname))

# 1) 实例怪未进索引（按名字查不到）——真实清单
missing = sorted({e[5] for e in inst_entries if e[5] not in n2i})
# 2) 实例怪名字在索引但 id 不同（串号）
mismatch = {}
for e in inst_entries:
    if e[5] in n2i and n2i[e[5]] != e[4]:
        mismatch.setdefault(e[5], (n2i[e[5]], e[4]))
# 3) 实例内部同名不同 id
by_name = defaultdict(set)
for e in inst_entries:
    by_name[e[5]].add(e[4])
intra = {n: ids for n, ids in by_name.items() if len(ids) > 1}
# 4) 子区域/地图同名对照
subarea_names, map_names = {}, {}
for _sas in C.SUBAREAS.values():
    for _sa in _sas:
        for mid, mname in collect_entries(_sa, ("monsters", "elite", "boss")):
            subarea_names.setdefault(mname, mid)
for _m in C.MAPS:
    for mid, mname in collect_entries(_m, ("monsters", "elite", "boss")):
        map_names.setdefault(mname, mid)

print(f"实例 stage 条目总数(修正解析): {len(inst_entries)}，去重名字 {len({e[5] for e in inst_entries})}")
print(f"\n=== 1) 实例怪未进索引: {len(missing)} ===")
for n in sorted(missing):
    ids = sorted({e[4] for e in inst_entries if e[5] == n})
    print(f"  {n:12s} -> {ids}")
print(f"\n=== 2) 名字在索引但 id 串号: {len(mismatch)} ===")
for n, (cur, inst) in sorted(mismatch.items()):
    print(f"  {n:12s} 当前索引→{cur:26s} 实例→{inst}")
print(f"\n=== 3) 实例内部同名不同id: {len(intra)} ===")
for n, ids in sorted(intra.items()):
    print(f"  {n:12s} -> {sorted(ids)}")
print(f"\n=== 4) 子区域同名（实例名 vs 子区域id）===")
cross = {}
for e in inst_entries:
    if e[5] in subarea_names and subarea_names[e[5]] != e[4]:
        cross.setdefault(e[5], (subarea_names[e[5]], e[4]))
for n, (sid, iid) in sorted(cross.items()):
    print(f"  {n:12s} 子区域→{sid:26s} 实例→{iid}")
print(f"\n=== 5) 地图级同名 ===")
cross_m = {}
for e in inst_entries:
    if e[5] in map_names and map_names[e[5]] != e[4]:
        cross_m.setdefault(e[5], (map_names[e[5]], e[4]))
for n, (mid_, iid) in sorted(cross_m.items()):
    print(f"  {n:12s} 地图→{mid_:26s} 实例→{iid}")
print(f"\n=== 6) 子区域内部同名不同id（last-wins 会改变现状的）===")
sa_by_name = defaultdict(set)
for _sas in C.SUBAREAS.values():
    for _sa in _sas:
        for mid, mname in collect_entries(_sa, ("monsters", "elite", "boss")):
            sa_by_name[mname].add(mid)
for n, ids in sorted(sa_by_name.items()):
    if len(ids) > 1:
        print(f"  {n:12s} -> {sorted(ids)}")
