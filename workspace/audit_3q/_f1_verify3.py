# -*- coding: utf-8 -*-
"""F1 最终验证 v3：MAPS 是 list（每条含 id），修正检查逻辑"""
import sys, os
sys.path.insert(0, "C:/Users/yuyu/qqbot/data/plugins/dragonfall")
os.chdir("C:/Users/yuyu/qqbot/data/plugins/dragonfall")

import game.data._assembly as A

SUB = A.SUBAREAS
INSTANCES = A.INSTANCES
# MAPS 是 list，MAP_BY_ID 是 dict
MAP_BY_ID = A.MAP_BY_ID

print("INSTANCES:", len(INSTANCES), "| SUBAREAS maps:", len(SUB), "| MAP_BY_ID:", len(MAP_BY_ID))

bad = []
for kid, inst in INSTANCES.items():
    e = inst.get("entry")
    if not e:
        bad.append((kid, "no entry"))
        continue
    mid, sa = e["map"], e["subarea"]
    if mid not in MAP_BY_ID:
        bad.append((kid, f"map {mid} not in MAP_BY_ID"))
    rooms = SUB.get(mid, [])
    if not any(r.get("id") == sa for r in rooms):
        bad.append((kid, f"{mid}/{sa} not exist"))
print("entry 问题:", bad if bad else "无")

uniq = {}
for kid, inst in INSTANCES.items():
    e = inst.get("entry")
    if e:
        uniq.setdefault((e["map"], e["subarea"]), []).append(kid)
print("去重入口子区域数:", len(uniq))

missing = []
for (mid, sa), kids in uniq.items():
    rooms = SUB.get(mid, [])
    r = next((x for x in rooms if x.get("id") == sa), None)
    if r is None:
        missing.append((mid, sa, "NOT EXIST"))
        continue
    if "instance" not in (r.get("funcs") or []):
        missing.append((mid, sa, r.get("funcs")))
print("funcs 缺 instance:", missing if missing else "无")

ok1 = len(INSTANCES) == 22 and not bad
ok2 = not missing
print(f"\n== 22 副本 entry 全齐且指向真实存在(在 MAP_BY_ID + SUBAREAS): {ok1}")
print(f"== 22 处入口子区域 funcs 均含 instance: {ok2}（21 处本次新增标记 + ash_temple_1 原有）")
print("PASS" if (ok1 and ok2) else "FAIL")
