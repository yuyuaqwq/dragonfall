# -*- coding: utf-8 -*-
"""v115 分析：副本材料价值与装备/战力体系联动核查 v2（按 mat_id 全链查询）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data.instances import INSTANCES
from game.data.items import MATERIALS
from game.data.craft import CRAFT_RECIPES
from game.data.alchemy import ALCHEMY_RECIPES
from game.data.cooking import COOKING_RECIPES
from game.data.enhance import ENHANCE_TABLE
from game.data.enchant import ENCHANT_RECIPES
from game.data.runes import RUNE_DROP
from game.data.quests import SIDE_QUESTS, MAIN_QUESTS

# 1) 收集副本材料 mat_id
inst_mat_ids = {}  # iid -> [(中文名, mat_id, price, quality)]
for iid, ins in INSTANCES.items():
    names = set(ins.get("materials") or [])
    boss = ins.get("boss")
    if boss and len(boss) >= 6:
        names.update(boss[5] or [])
    for st in ins.get("stages") or []:
        for f in ("elite", "boss"):
            e = st.get(f)
            if e and len(e) >= 6 and e[5]:
                names.update(e[5])
    ids = []
    for n in names:
        for mid, m in MATERIALS.items():
            if isinstance(m, dict) and m.get("name") == n:
                ids.append((n, mid, m.get("price"), m.get("quality")))
                break
    inst_mat_ids[iid] = ids

all_ids = {}
for iid, lst in inst_mat_ids.items():
    for n, mid, price, q in lst:
        all_ids[mid] = (n, price, q)

print("=== 副本材料全量（%d 种）===" % len(all_ids))
for mid, (n, price, q) in sorted(all_ids.items(), key=lambda x: x[1][1] or 0):
    print(f"  {n} {mid} price={price} q={q}")

# 2) 联动查询
print()
print("=== 联动查询（按 mat_id）===")

def find_usage(mid):
    hits = []
    for rid, r in CRAFT_RECIPES.items():
        if isinstance(r, dict) and mid in (r.get("mats") or {}):
            hits.append(f"锻造:{r.get('name', rid)}")
    for rid, r in ALCHEMY_RECIPES.items():
        if isinstance(r, dict) and mid in (r.get("mats") or {}):
            hits.append(f"炼金:{r.get('name', rid)}")
    for rid, r in COOKING_RECIPES.items():
        if isinstance(r, dict) and mid in (r.get("mats") or {}):
            hits.append(f"烹饪:{r.get('name', rid)}")
    if isinstance(ENHANCE_TABLE, dict):
        for lv, spec in ENHANCE_TABLE.items():
            mm = spec.get("mats") if isinstance(spec, dict) else None
            if isinstance(mm, dict) and mid in mm:
                hits.append(f"强化:Lv{lv}")
    if isinstance(ENCHANT_RECIPES, dict):
        for rid, r in ENCHANT_RECIPES.items():
            if isinstance(r, dict) and mid in (r.get("mats") or {}):
                hits.append(f"附魔:{r.get('name', rid)}")
    if isinstance(RUNE_DROP, dict):
        for rid, r in RUNE_DROP.items():
            if isinstance(r, dict) and mid in (r.get("mats") or {}):
                hits.append(f"符文:{rid}")
    # 任务收集
    qs = []
    for q in SIDE_QUESTS if isinstance(SIDE_QUESTS, list) else SIDE_QUESTS.values():
        qs.append(q)
    for q in MAIN_QUESTS if isinstance(MAIN_QUESTS, list) else MAIN_QUESTS.values():
        qs.append(q)
    for q in qs:
        if not isinstance(q, dict):
            continue
        obj = q.get("objective") or {}
        col = obj.get("collect")
        if isinstance(col, dict) and col.get("item") == mid:
            hits.append(f"任务:{q.get('name')}")
    return hits

no_use = []
for mid, (n, price, q) in sorted(all_ids.items(), key=lambda x: x[1][1] or 0):
    hits = find_usage(mid)
    if hits:
        print(f"  ✅ {n}: {hits}")
    else:
        no_use.append((n, price))
        print(f"  ⬜ {n}: 无任何配方/任务使用")

print()
print(f"=== 结论：{len(all_ids)} 种副本材料中 {len(all_ids)-len(no_use)} 种有联动，{len(no_use)} 种无联动 ===")
if no_use:
    print("无联动清单:", [n for n, _ in no_use])
