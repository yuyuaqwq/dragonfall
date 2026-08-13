# -*- coding: utf-8 -*-
"""M10 材料来源覆盖检查 v2：正确解析 (mid,name,role,lv,skills,drops) 结构"""
import sys, os, re
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
os.chdir(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
import game.data as D
from game.data import (CRAFT_RECIPES, MATERIALS, MATERIALS_BY_NAME, SUBAREAS, MAPS,
                       SHOP_SUBAREA_ITEMS, SHOP_SMITH_MATERIALS, FISH_POOL,
                       GATHER_MAP_POOLS, GATHER_COND_POOLS, MINING_DEEP_POOLS,
                       CAMP_SPOTS, MINE_SPOTS, INSTANCES, ALCHEMY_RECIPES, POIS, SUBAREA_POIS)

NAME2ID = {m["name"]: mid for mid, m in MATERIALS.items()}
def norm_mat(name):
    """掉落名 → mat_id；支持 铁矿石 / 铁矿石×2 / mat_xxx"""
    if not isinstance(name, str):
        return None
    name = name.strip()
    if name.startswith("mat_") and name in MATERIALS:
        return name
    m = re.match(r"^(.*?)[×xX*](\d+)$", name)
    if m:
        name = m.group(1).strip()
    return NAME2ID.get(name)

drop_mats = set()
def collect(slots):
    for t in (slots or []):
        if not isinstance(t, (list, tuple)) or len(t) < 6:
            continue
        for d in (t[5] or []):
            if isinstance(d, dict):
                mid = norm_mat(d.get("id") or d.get("mat") or next(iter(d), ""))
            else:
                mid = norm_mat(d)
            if mid:
                drop_mats.add(mid)

for sas in SUBAREAS.values():
    for sa in sas:
        collect(sa.get("monsters")); collect(sa.get("elite")); collect(sa.get("boss"))
for m in MAPS:
    collect(m.get("monsters")); collect(m.get("elite")); collect(m.get("boss"))
for ins in INSTANCES.values():
    for st in (ins.get("stages") or []):
        collect(st.get("monsters")); collect(st.get("elite")); collect(st.get("boss"))

gather_mats = set()
def collect_pool(pool):
    for item in (pool if isinstance(pool, list) else []):
        if isinstance(item, (tuple, list)) and item:
            mid = norm_mat(item[0]) or norm_mat(str(item[0]))
            if mid: gather_mats.add(mid)
        elif isinstance(item, dict) and item.get("id"):
            gather_mats.add(item["id"])
for p in list(GATHER_MAP_POOLS.values()) + list(GATHER_COND_POOLS.values()) + list(MINING_DEEP_POOLS.values()):
    collect_pool(p)
for p in list(CAMP_SPOTS.values()) + list(MINE_SPOTS.values()):
    collect_pool(p)

shop_mats = set()
for lst in SHOP_SUBAREA_ITEMS.values():
    for it in (lst or []):
        mid = norm_mat(it)
        if mid: shop_mats.add(mid)
for lst in (SHOP_SMITH_MATERIALS or {}).values():
    for t in (lst or []):
        if isinstance(t, (tuple, list)) and t:
            mid = norm_mat(t[0])
        else:
            mid = norm_mat(t)
        if mid: shop_mats.add(mid)

# POI 可交互材料
poi_mats = set()
for p in list(POIS.values()) + list(SUBAREA_POIS.values()):
    if isinstance(p, dict) and p.get("material"):
        mid = norm_mat(p["material"])
        if mid: poi_mats.add(mid)
    elif isinstance(p, dict) and p.get("items"):
        for it in p["items"]:
            mid = norm_mat(it)
            if mid: poi_mats.add(mid)

fish_mats = set()
for f in FISH_POOL:
    mid = norm_mat(f.get("id", ""))
    if mid: fish_mats.add(mid)

rec_mats = {}
for rk, r in CRAFT_RECIPES.items():
    for m in r["mats"]:
        rec_mats.setdefault(m, []).append(rk)

print(f"配方引用材料 {len(rec_mats)} 种 | 掉落 {len(drop_mats)} | 采集/挖掘 {len(gather_mats)} | 商店 {len(shop_mats)} | POI {len(poi_mats)} | 垂钓 {len(fish_mats)}")
missing = []
for m, rks in sorted(rec_mats.items()):
    srcs = []
    if m in drop_mats: srcs.append("掉落")
    if m in gather_mats: srcs.append("采集/挖掘")
    if m in shop_mats: srcs.append("商店")
    if m in poi_mats: srcs.append("POI")
    if m in fish_mats: srcs.append("垂钓")
    if m == "mat_tu_zhi_can_ye": srcs.append("图纸残页")
    if not srcs:
        missing.append((m, MATERIALS.get(m, {}).get("name", m), len(rks)))
print(f"=== 无任何来源的材料 {len(missing)} 种 ===")
for m, nm, n in missing:
    print(f"  {m} {nm} 用于 {n} 个配方")
print("=== 各材料来源明细 ===")
for m, rks in sorted(rec_mats.items()):
    srcs = []
    if m in drop_mats: srcs.append("掉落")
    if m in gather_mats: srcs.append("采集/挖掘")
    if m in shop_mats: srcs.append("商店")
    if m in poi_mats: srcs.append("POI")
    if m in fish_mats: srcs.append("垂钓")
    print(f"  {MATERIALS.get(m,{}).get('name',m)} ({m}): {','.join(srcs) if srcs else '❌无来源'} 配方x{len(rks)}")
