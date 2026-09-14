# -*- coding: utf-8 -*-
"""验证 v3 子区域 NPC 分配"""
import sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

from game.content import SUBAREAS, NPCS

# 验证城镇：每个子区域必须有内容
print("=== 城镇子区域内容检查（空壳应=0）===")
empty = []
total_sa = 0
for mid, sas in SUBAREAS.items():
    for sa in sas:
        if sa.get("type") == "城镇":
            total_sa += 1
            if not sa.get("npcs") and not sa.get("funcs") and not sa.get("shop") and not sa.get("healer"):
                empty.append((mid, sa["name"]))
print(f"城镇子区域: {total_sa}, 空壳: {len(empty)}")
for e in empty:
    print(f"  {e}")

print("\n=== 行政 NPC 归属检查 ===")
check = [
    ("oak_town", "npc_mayor", "镇长办公处"),
    ("oak_town", "npc_guild_clerks", "冒险者广场"),
    ("white_deer", "npc_baron", "城主府"),
    ("white_deer", "npc_priest", "白鹿圣堂"),
    ("white_deer", "npc_doctor", "医师馆"),
    ("white_deer", "npc_cook_master", "烹饪坊"),
    ("white_deer", "npc_enhance_master", "强化工坊"),
    ("white_deer", "npc_blacksmith2", "鹿角铁匠铺"),
    ("dawn_city", "npc_king", "圣光王宫"),
    ("dawn_city", "npc_pope", "圣光大教堂"),
    ("frost_horn", "npc_north_chief", "酋长大厅"),
    ("frost_horn", "npc_field_priest", "随军圣堂"),
    ("maple_village", "npc_oak_elder", "村长屋"),
    ("ironharbor", "npc_guildmaster", "冒险者行会总部"),
    ("ironharbor", "npc_auctioneer", "金槌拍卖行"),
]
for mid, nid, expect in check:
    found = ""
    for sa in SUBAREAS.get(mid, []):
        if nid in sa.get("npcs", []):
            found = sa["name"]
            break
    mark = "✅" if found == expect else "❌"
    print(f"  {mark} {mid}::{NPCS[nid]['name']} → {found} (期望 {expect})")
