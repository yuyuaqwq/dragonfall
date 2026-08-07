# -*- coding: utf-8 -*-
"""补全城镇出口：城镇 -> 野外 连接（从野外图反向推导，保证双向）"""
import os, sys, ast

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)
os.chdir(PLUGIN_DIR)

path = os.path.join(PLUGIN_DIR, "game", "data", "maps.py")
src = open(path, encoding="utf-8").read()

conn_anchor = "MAP_CONNECTIONS = {"
cidx = src.find(conn_anchor)
cend = src.find("\n}\n", cidx)
block = src[cidx:cend + 3]
conns = ast.literal_eval(block.split("=", 1)[1].strip().rstrip(","))

from game.data.maps import MAPS
towns = {m["id"] for m in MAPS if m.get("type") == "城镇区域"}

# 反向推导：野外图 X 连城镇 T，则 T 也应连 X（若 T 是城镇且 X 非 road 非城镇）
added = 0
for k, vs in list(conns.items()):
    if k.startswith("road_"):
        continue
    for v in vs:
        if v in towns and v != k:
            # k 连到城镇 v → v 也应连 k（若 k 是野外且不是 road）
            if k not in conns.get(v, []):
                conns.setdefault(v, [])
                conns[v].append(k)
                added += 1

# 写回
new_block = "MAP_CONNECTIONS = {\n"
for k in sorted(conns.keys()):
    items = ", ".join('"{}"'.format(x) for x in conns[k])
    new_block += '    "{}": [{}],\n'.format(k, items)
new_block += "}\n"
src = src[:cidx] + new_block + src[cend + 3:]
open(path, "w", encoding="utf-8").write(src)
print(f"✅ 补全 {added} 条城镇出口连接")
