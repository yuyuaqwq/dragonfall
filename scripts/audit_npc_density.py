# -*- coding: utf-8 -*-
"""总结：城镇类子区域 NPC 分布统计"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
from game.data.subareas import SUBAREAS
from game.data.npcs import NPCS

town_total = 0
town_1 = 0
town_2plus = 0
town_0 = 0
for map_id, sas in SUBAREAS.items():
    for sa in sas:
        if sa.get("type") in ("城镇", "城镇街道", "城镇出口"):
            town_total += 1
            n = len(sa.get("npcs") or [])
            if n == 0:
                town_0 += 1
            elif n == 1:
                town_1 += 1
            else:
                town_2plus += 1

print(f"城镇类子区域总数: {town_total}")
print(f"  0 NPC: {town_0}")
print(f"  1 NPC: {town_1}")
print(f"  2+ NPC: {town_2plus}")

# 仍只有 1 个的城镇子区域（看看哪些还冷清）
print("\n=== 仍只有 1 NPC 的城镇子区域 ===")
for map_id, sas in SUBAREAS.items():
    for sa in sas:
        if sa.get("type") in ("城镇", "城镇街道", "城镇出口") and len(sa.get("npcs") or []) == 1:
            names = [NPCS[n]["name"] for n in (sa.get("npcs") or []) if n in NPCS]
            print(f"  {map_id}/{sa['name']}: {names[0] if names else '?'}")
