# -*- coding: utf-8 -*-
"""最终验证：subareas.py 全量子区域 desc 非占位符、非过短"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
from game.data.subareas import SUBAREAS
from game.data.maps import MAPS

map_cn = {}
for m in MAPS:
    map_cn[m["id"]] = m.get("name", m["id"])

total = 0
placeholder = 0
too_short = 0
for map_id, sas in SUBAREAS.items():
    cn = map_cn.get(map_id, map_id)
    for sa in sas:
        total += 1
        desc = (sa.get("desc") or "").strip()
        name = sa.get("name", "")
        if not desc or desc == name or desc == f"{cn}·{name}" or desc == cn or desc.endswith("入口") and len(desc) < 10:
            placeholder += 1
            print(f"⚠️ 仍占位: {map_id} | {name} | {desc!r}")
        if len(desc) < 15:
            too_short += 1
            print(f"⚠️ 过短: {map_id} | {name} | {desc!r}")

print(f"总子区域: {total}, 占位符: {placeholder}, 过短(<15字): {too_short}")
