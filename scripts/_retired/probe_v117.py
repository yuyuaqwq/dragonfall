# -*- coding: utf-8 -*-
"""v117 前置调研：装备模板/强化石/药剂/附魔消耗（一次性工具）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data.equip_roster import EQUIP_ROSTER
from game.data.items import ITEMS, MATERIALS
from game.data.craft import CRAFT_RECIPES
from game.data.alchemy import ALCHEMY_RECIPES

print("=== EQUIP_ROSTER 结构 ===")
k0 = list(EQUIP_ROSTER.keys())[0]
print("key 样例:", k0)
print("value 样例:", str(EQUIP_ROSTER[k0])[:400])

# 高阶橙装（lv>=55 且 quality=orange 或 name 含 系列名）
print()
print("=== 高阶装备模板（lv>=55）===")
hi = []
for rid, e in EQUIP_ROSTER.items():
    if not isinstance(e, dict):
        continue
    lv = e.get("lv") or 0
    if lv >= 55:
        hi.append((lv, e.get("name"), e.get("quality"), e.get("slot"), e.get("series")))
for r in sorted(hi)[:40]:
    print(" ", r)

print()
print("=== 强化石 i_stone_* ===")
for k, v in ITEMS.items():
    if str(k).startswith("i_stone") or (isinstance(v, dict) and "强化石" in str(v.get("name", ""))):
        print(" ", k, "->", str(v)[:150])

print()
print("=== 炼金配方里已用强化石/药剂的样例 ===")
for rid, r in ALCHEMY_RECIPES.items():
    if not isinstance(r, dict):
        continue
    prod = str(list((r.get("product") or {}).keys()))
    if "stone" in prod or "yao" in prod or "potion" in prod:
        print(" ", rid, "->", str(r)[:180])

print()
print("=== 附魔消耗逻辑（economy.py 附魔命令）===")
