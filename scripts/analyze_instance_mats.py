# -*- coding: utf-8 -*-
"""v115 分析：副本专属材料价值与装备/战力体系联动核查（一次性工具）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data.instances import INSTANCES
from game.data.items import MATERIALS
from game.data.craft import CRAFT_RECIPES

print("=== 22 副本专属材料（materials 字段 + boss/elite 掉落）===")
inst_mats = {}
for iid, ins in INSTANCES.items():
    mats = list(ins.get("materials") or [])
    boss = ins.get("boss")
    if boss and len(boss) >= 6:
        mats += list(boss[5] or [])
    for st in ins.get("stages") or []:
        for f in ("elite", "boss"):
            e = st.get(f)
            if e and len(e) >= 6 and e[5]:
                mats += list(e[5])
    inst_mats[iid] = sorted(set(mats))
    print(f'{ins["name"]} ({iid}): {sorted(set(mats))}')

allm = set()
for v in inst_mats.values():
    allm.update(v)

print()
print("=== 材料信息与锻造配方使用 ===")
used = set()
for m in sorted(allm):
    info = MATERIALS.get(m, {})
    price = info.get("price", "?")
    in_recipes = []
    for rid, r in CRAFT_RECIPES.items():
        if not isinstance(r, dict):
            continue
        mats_need = r.get("mats") or r.get("materials") or {}
        if isinstance(mats_need, dict) and m in mats_need:
            in_recipes.append(rid)
    if in_recipes:
        used.add(m)
    print(f"{m}: price={price} 配方使用={len(in_recipes)} {in_recipes[:4]}")

print()
print("被配方使用的副本材料:", sorted(used) if used else "【无！副本材料未进入锻造配方】")
