# -*- coding: utf-8 -*-
"""审计：子区域 monsters 配置等级 vs 子区域 lv 偏差"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r"C:\Users\yuyu\qqbot")
from data.plugins.dragonfall.game import content as C

SUBAREAS = getattr(C, "SUBAREAS", None)
if SUBAREAS is None:
    # 尝试常见命名
    for name in dir(C):
        if "SUBAREA" in name.upper():
            print("候选:", name)
    sys.exit(1)

mismatch, no_monster, total = [], 0, 0
for map_id, sa_list in SUBAREAS.items():
  for sa in sa_list:
    if not sa.get("monsters"):
        no_monster += 1
        continue
    sa_lv = sa.get("lv", 0)
    for m in sa["monsters"]:
        total += 1
        m_lv = m[3]
        if m_lv != sa_lv:
            mismatch.append((sa["id"], sa.get("name"), sa_lv, m[1], m_lv))

print(f"地图数: {len(SUBAREAS)}, 无怪子区域: {no_monster}, 怪物配置总数: {total}")
print(f"等级与子区域lv不符: {len(mismatch)}")
for row in mismatch[:40]:
    print(f"  {row[0]} ({row[1]}) sa_lv={row[2]}  怪[{row[3]}] lv={row[4]}")

# 分布统计：怪lv - sa_lv
from collections import Counter
diff = Counter(m[4] - m[2] for m in mismatch)
print("偏差分布:", dict(sorted(diff.items())))
