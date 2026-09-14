# -*- coding: utf-8 -*-
"""验证：①所有挂载的 npc id 都在 NPCS 定义中 ②同子区域无重复挂载 ③看关键城镇 NPC 密度"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
from game.content import SUBAREAS, NPCS

total_mounted = 0
missing = set()
dup = []
for map_id, sas in SUBAREAS.items():
    for sa in sas:
        npcs = sa.get("npcs") or []
        total_mounted += len(npcs)
        seen = set()
        for nid in npcs:
            if nid not in NPCS:
                missing.add(nid)
            if nid in seen:
                dup.append((sa["id"], nid))
            seen.add(nid)

print(f"总挂载: {total_mounted}")
print(f"未定义 NPC: {missing if missing else '无'}")
print(f"子区域内重复挂载: {dup if dup else '无'}")

# 关键城镇密度检查
for map_id in ["oak_town", "white_deer", "ironharbor", "dawn_city"]:
    m = next((m for m in sys.modules if False), None)
    for sa in SUBAREAS[map_id]:
        names = []
        for nid in (sa.get("npcs") or []):
            n = NPCS.get(nid)
            if n:
                names.append(n["name"])
        print(f"  {map_id}/{sa['name']}: {len(names)} NPC -> {', '.join(names)}")
