# -*- coding: utf-8 -*-
"""F1 最终验证（脚本文件版，避免 bash 转义坑）"""
import sys
sys.path.insert(0, "C:/Users/yuyu/qqbot/data/plugins/dragonfall")
import os
os.chdir("C:/Users/yuyu/qqbot/data/plugins/dragonfall")

import game.data._assembly as A

SUB = A.SUBAREAS
MAPS = A.MAPS
INSTANCES = A.INSTANCES

print("SUBAREAS maps:", len(SUB), "| MAPS maps:", len(MAPS), "| INSTANCES:", len(INSTANCES))

bad = []
for kid, inst in INSTANCES.items():
    e = inst.get("entry")
    if not e:
        bad.append((kid, "no entry"))
        continue
    mid, sa = e["map"], e["subarea"]
    if mid not in MAPS:
        bad.append((kid, f"map {mid} not in MAPS"))
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

# 打印完整映射
print("\n=== 22 副本 entry 映射表 ===")
for kid in INSTANCES:
    e = INSTANCES[kid].get("entry")
    if e:
        mid, sa = e["map"], e["subarea"]
        rooms = SUB.get(mid, [])
        nm = next((r.get("name") for r in rooms if r.get("id") == sa), "?")
        print(f"  {kid}: {mid}/{sa} [{nm}]")

print("\n=== 22 处入口子区域 funcs（去重 22，其中 21 处本次新标记 / abyss_gate 入口 ash_temple_1 原已含）===")
for (mid, sa), kids in sorted(uniq.items()):
    rooms = SUB.get(mid, [])
    r = next((x for x in rooms if x.get("id") == sa), None)
    print(f"  {mid}/{sa} funcs={r.get('funcs') if r else None} <- {kids}")

ok1 = len(INSTANCES) == 22 and not bad
ok2 = not missing and all("instance" in (next((x for x in SUB.get(m, []) if x.get('id') == s), {}).get('funcs') or []) for m, s, _ in [(e['map'], e['subarea'], None) for e in [i.get('entry') for i in INSTANCES.values()] if e])
print(f"\n== 22 副本 entry 全齐且指向真实存在: {ok1}")
print(f"== 全部 22 处入口子区域 funcs 均含 instance: {ok2}")
print("PASS" if (ok1 and ok2) else "FAIL")
