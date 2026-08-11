# -*- coding: utf-8 -*-
"""验证 v95.30 随机性配置：
1. roam 子区域必须存在于对应地图
2. roam 子区域必须与 home_sa 同图
3. period 必须是合法时段
4. appear 在 (0,1]
5. lines 至少 2 条
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
from game.data.npcs import NPCS
from game.data.subareas import SUBAREAS
from game.data.maps import MAPS

VALID_PERIODS = {"day", "night", "dawn", "dusk", "morning", "afternoon", "evening"}

# 地图 → 子区域 id 集合
sa_by_map = {}
for mid, sas in SUBAREAS.items():
    sa_by_map[mid] = {sa["id"] for sa in sas}

# 每个 NPC 的 map 和所属子区域（从挂载反查）
npc_home_sa = {}  # npc_id -> set(sa_ids)
for mid, sas in SUBAREAS.items():
    for sa in sas:
        for nid in (sa.get("npcs") or []):
            npc_home_sa.setdefault(nid, set()).add(sa["id"])

errs = []
checked = 0
for nid, npc in NPCS.items():
    if not any(k in npc for k in ("roam", "appear", "period", "lines")):
        continue
    checked += 1
    # period
    for p in (npc.get("period") or []):
        if p not in VALID_PERIODS:
            errs.append(f"{nid}: 非法时段 {p}")
    # appear
    ap = npc.get("appear")
    if ap is not None and not (0 < ap <= 1):
        errs.append(f"{nid}: appear 越界 {ap}")
    # lines
    ls = npc.get("lines")
    if ls and len(ls) < 2:
        errs.append(f"{nid}: lines 不足 2 条")
    # roam 同图验证
    roam = npc.get("roam")
    if roam:
        home_maps = set()
        for sa_id in npc_home_sa.get(nid, []):
            for mid, sas in sa_by_map.items():
                if sa_id in sas:
                    home_maps.add(mid)
        # 如果没有反查到挂载，用 npc.map 推断
        if not home_maps and npc.get("map"):
            home_maps = {npc["map"]}
        for sa_id in roam:
            belongs = any(sa_id in sa_by_map.get(mid, set()) for mid in home_maps)
            if not belongs:
                errs.append(f"{nid}: roam {sa_id} 不在同图 {home_maps}")
        # roam 内的子区域必须与挂载子区域相连（星形：至少共享地图）
        for sa_id in roam:
            if sa_id not in [s for mid in home_maps for s in sa_by_map.get(mid, set())]:
                errs.append(f"{nid}: roam {sa_id} 不存在于任何挂载地图")

print(f"检查带随机字段的 NPC: {checked}")
print(f"错误: {len(errs)}")
for e in errs[:30]:
    print(f"  ⚠️ {e}")
