# -*- coding: utf-8 -*-
"""终极修复：从干净基础重建 MAP_CONNECTIONS

- 基础 = 原始 MAP_CONNECTIONS（城镇直连全删，只留 maple_village<->oak_town）
- 加必经之路：road_{a}_{b} 连接 a/b 城镇
"""
import os, sys, ast, re

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)
os.chdir(PLUGIN_DIR)

path = os.path.join(PLUGIN_DIR, "game", "data", "maps.py")
src = open(path, encoding="utf-8").read()

from game.data.maps import MAPS
from game.data.roads import ROAD_MAPS

byid = {m["id"]: m for m in MAPS}
towns = [m["id"] for m in MAPS if m.get("type") == "城镇区域"]
KEEP = {("maple_village", "oak_town")}

# 1. 从当前 conns 提取"非 road 图"连接（这些是原始野外连接，保留）
conn_anchor = "MAP_CONNECTIONS = {"
cidx = src.find(conn_anchor)
cend = src.find("\n}\n", cidx)
block = src[cidx:cend + 3]
conns = ast.literal_eval(block.split("=", 1)[1].strip().rstrip(","))

# 2. 重建：只保留 非城镇/非road 的连接（野外图之间的原始连接）
#    城镇出口只连野外；road 图只连两端城镇
new_conns = {}
for k, vs in conns.items():
    if k.startswith("road_"):
        continue  # road 图后面重建
    if k in towns:
        # 城镇：只保留指向野外的连接（删指向城镇和 road 的）
        keep_vs = [v for v in vs if v not in towns and not v.startswith("road_")]
        new_conns[k] = keep_vs
    else:
        # 野外图：保留所有非 road 连接（可能指向城镇或野外）
        new_conns[k] = [v for v in vs if not v.startswith("road_")]

# 3. 加回 maple_village<->oak_town（同村近邻直连）
for x, y in [("maple_village", "oak_town"), ("oak_town", "maple_village")]:
    if x in new_conns and y not in new_conns[x]:
        new_conns[x].append(y)
    elif x not in new_conns:
        new_conns[x] = [y]

# 4. 加必经之路连接
for r in ROAD_MAPS:
    rid = r["id"]
    rest = rid.replace("road_", "", 1)
    cands = sorted(towns, key=len, reverse=True)
    a = next((t for t in cands if rest.startswith(t + "_")), None)
    b = next((t for t in cands if rest.endswith("_" + t)), None)
    if not a or not b:
        print(f"❌ 无法拆分 {rid}")
        continue
    for x, y in [(a, rid), (b, rid), (rid, a), (rid, b)]:
        new_conns.setdefault(x, [])
        if y not in new_conns[x]:
            new_conns[x].append(y)

# 5. 写回
new_block = "MAP_CONNECTIONS = {\n"
for k in sorted(new_conns.keys()):
    items = ", ".join('"{}"'.format(x) for x in new_conns[k])
    new_block += '    "{}": [{}],\n'.format(k, items)
new_block += "}\n"
src = src[:cidx] + new_block + src[cend + 3:]
open(path, "w", encoding="utf-8").write(src)

# 验证
import importlib
import game.data.maps as maps_mod
importlib.reload(maps_mod)
byid2 = {m["id"]: m for m in maps_mod.MAPS}
bad = []
for k, vs in maps_mod.MAP_CONNECTIONS.items():
    if k not in byid2: bad.append(f"源不存在:{k}")
    for v in vs:
        if v not in byid2: bad.append(f"目标不存在:{k}->{v}")
print(f"✅ 写回完成。连接一致性: {'✅' if not bad else bad[:5]}")
direct = sorted(set(tuple(sorted([a,b])) for a in towns for b in maps_mod.MAP_CONNECTIONS.get(a,[]) if b in towns))
print(f"剩余城镇直连: {direct}")
print(f"橡木镇可前往: {[byid2[x]['name'] for x in maps_mod.MAP_CONNECTIONS['oak_town']]}")
print(f"白鹿城可前往: {[byid2[x]['name'] for x in maps_mod.MAP_CONNECTIONS['white_deer']]}")
