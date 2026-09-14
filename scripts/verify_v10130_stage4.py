# -*- coding: utf-8 -*-
"""v101.30 阶段四验证：高级钓点材料闭环 / 鱼饵上架 / 淬火石 / 配方 key 完整性"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\yuyu\qqbot\data\plugins\dragonfall')

from game.content import (MATERIALS, ITEMS, COOKING_RECIPES, ALCHEMY_RECIPES,
                       FISH_POOL, SHOP_SUBAREA_ITEMS, MINING_DEEP_POOLS, RUNES)
from game.core import constants as KC

ok = True
def check(name, cond, detail=""):
    global ok
    print(f"  {'✅' if cond else '❌'} {name} {detail}")
    if not cond:
        ok = False

print("=== 1. 新物品定义 ===")
for k, name in (("i_pearl_tonic","珍珠明目水"),("i_abyss_echo","深渊回响药剂"),("i_rainbow_elixir","彩虹药剂"),
                ("i_storm_chowder","风暴贝汤"),("i_thunder_elixir","雷晶药剂"),("i_dragonbone_elixir","龙骨药剂")):
    v = ITEMS.get(k, {})
    check(f"{name}({k})", bool(v), f"price={v.get('price')} effect={v.get('effect')} hot={v.get('hot')}")

print("=== 2. 新配方 key 完整性 ===")
for rk, r in ALCHEMY_RECIPES.items():
    for m in r["cost"]:
        if m.startswith("mat_") and m not in MATERIALS:
            check(f"{rk} 材料 {m}", False, "❌ MATERIALS 无此 key")
        elif not m.startswith("mat_") and m not in ITEMS:
            check(f"{rk} 材料 {m}", False, "❌ ITEMS 无此 key")
    for p in r["product"]:
        check(f"{rk} 产物 {p}", p in ITEMS, "" if p in ITEMS else "❌ ITEMS 无此 key")
for rk, r in COOKING_RECIPES.items():
    for m in r["cost"]:
        if m.startswith("mat_") and m not in MATERIALS:
            check(f"{rk} 材料 {m}", False, "❌")
        elif not m.startswith("mat_") and m not in ITEMS:
            check(f"{rk} 材料 {m}", False, "❌")
    for p in r["product"]:
        check(f"{rk} 产物 {p}", p in ITEMS, "" if p in ITEMS else "❌")

print("=== 3. 效果键在战斗分发器支持范围 ===")
# ★ MIG（2026-09-14）：原读 `game/battle.py`（旧战斗引擎，已随 379a792 删除）与
#   `game/core/item_templates.py`（已薄壳化）→ 改读**包内同源**真源（effect 定义现居包内）。
_PKG = os.path.join(r'C:\Users\yuyu\qqbot\data\plugins\dragonfall', 'framework', 'games', 'orlandia')
src = open(os.path.join(_PKG, 'content', 'item_templates.py'), encoding='utf-8').read()
src2 = open(os.path.join(_PKG, 'content', 'data', 'item_templates.json'), encoding='utf-8').read()
for k in ("buff_crit_small", "buff_matk", "next_atk_up", "buff_atk_big", "buff_atk_big_def"):
    check(f"effect {k}", (k in src2) or (k in src), "")

print("=== 4. 垂钓材料 6 种全部有消费点（闭环） ===")
consumed = set()
for r in ALCHEMY_RECIPES.values():
    consumed.update(m for m in r["cost"] if m.startswith("mat_"))
for r in COOKING_RECIPES.values():
    consumed.update(m for m in r["cost"] if m.startswith("mat_"))
for rk, r in __import__('game.content', fromlist=['CRAFT_RECIPES']).CRAFT_RECIPES.items():
    consumed.update(r.get("mats", {}))
for name, mid in (("湖珍珠","mat_hu_zhen_zhu"),("深渊珍珠","mat_shen_yuan_zhen_zhu"),("彩虹露珠","mat_cai_hong_lu_zhu"),
                  ("风暴贝","mat_feng_bao_bei"),("雷晶砂","mat_lei_jing_sha"),("古代鱼骨","mat_gu_dai_yu_gu"),
                  ("深海水晶", None), ("鲛人泪", None), ("龙涎香", None)):
    if mid is None:
        mid = next((k for k, v in MATERIALS.items() if v.get("name") == name), None)
    check(f"{name} 有消费点", mid in consumed, f"(key={mid})" if mid else "❌ 材料不存在")

print("=== 5. 鱼饵上架 ===")
bait_in_shop = []
for sa, lst in SHOP_SUBAREA_ITEMS.items():
    for it in lst:
        if isinstance(it, str) and it in ("it_glow_bait", "it_dough_bait", "it_blood_bait"):
            bait_in_shop.append((sa, it))
check("鱼饵商店在架", len(bait_in_shop) >= 4, str(bait_in_shop))

print("=== 6. 淬火石 ===")
m = MATERIALS.get("mat_qiang_hua_shi", {})
check("改名淬火石", m.get("name") == "淬火石", str(m.get("name")))
check("入 hill_mine 矿池", any(mid == "mat_qiang_hua_shi" for mid, _w in MINING_DEEP_POOLS.get("hill_mine", [])))

print("=== 7. 古代鱼骨价格统一 ===")
check("MATERIALS 古代鱼骨 200", MATERIALS.get("mat_gu_dai_yu_gu", {}).get("price") == 200)
f = next((x for x in FISH_POOL if x["name"] == "古代鱼骨"), {})
check("FISH_POOL 古代鱼骨 200", f.get("price") == 200)

print("\n" + ("✅ 阶段四验证全部通过" if ok else "❌ 有失败项"))
sys.exit(0 if ok else 1)
