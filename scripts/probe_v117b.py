# -*- coding: utf-8 -*-
"""v117 前置调研 2：同名装备匹配/食物/附魔消耗/符文途径（一次性工具）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data.equip_roster import EQUIP_ROSTER
from game.data.items import ITEMS, MATERIALS
from game.data.cooking import COOKING_RECIPES

unused = ["古王剑", "马尔库斯的法冠", "圣光圣徽", "魔像核心", "克罗的罗盘", "灰矮人徽记",
          "石炉之锤", "地底龙鳞", "深渊珍珠", "赫尔加的祭器", "烬核", "要塞残片", "奥拉圣印碎片",
          "蓝歌之冠", "澜歌之泪", "潮汐之泪", "试炼徽记", "幽灵船票", "月辉碎片", "永冻之核",
          "古王碎片", "黎明之光碎片", "龙语传承", "龙魂碎片", "黑渊之眼", "云怒之核", "风暴之核", "龙宫珠"]

print("=== 闲置材料 ↔ 装备花名册同名匹配 ===")
for n in unused:
    hits = [(rid, e.get("name"), e.get("slot"), e.get("lv"), e.get("quality"))
            for rid, e in EQUIP_ROSTER.items()
            if isinstance(e, dict) and e.get("name") == n]
    if hits:
        print(f"  ✅ {n} -> {hits}")
    else:
        print(f"  ⬜ {n}: 无同名模板")

print()
print("=== 烹饪产物（现有食物 id）===")
foods = {}
for rid, r in COOKING_RECIPES.items():
    if isinstance(r, dict):
        for pk in (r.get("product") or {}):
            foods[pk] = r.get("name")
for pk, nm in list(foods.items())[:30]:
    print(" ", pk, "->", nm)

print()
print("=== 附魔消耗（economy.py 中 enchant 相关行）===")
import re
src = open("game/commands/economy.py", encoding="utf-8").read()
for m in re.finditer(r".*(enchant_match_material|附魔.*材料|扣.*材|consume.*mat).*", src):
    print(" ", src[m.start():m.end()][:150])
