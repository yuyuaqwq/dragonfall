# -*- coding: utf-8 -*-
"""应用必经之路：路图并入 MAPS + 改写 MAP_CONNECTIONS

在 maps.py 的 MAPS 列表末尾插入 ROAD_MAPS，并更新 MAP_CONNECTIONS：
- 删城镇直连（走已有野外）
- 加路图连接（城镇<->路<->城镇）
"""
import os, sys, re

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)
os.chdir(PLUGIN_DIR)

from game.data.roads import ROAD_MAPS

# 在 MAPS 中插入路图（在 "MAP_BY_ID" 之前，即 MAPS 列表结束后的 MAP_BY_ID 定义前）
maps_path = os.path.join(PLUGIN_DIR, "game", "data", "maps.py")
src = open(maps_path, encoding="utf-8").read()

# 1. 把 ROAD_MAPS 注入 MAPS（在 MAPS 列表末尾 ']' 前插入）
# 找到 MAP_BY_ID 前的 "]\n\nMAP_BY_ID" 位置
anchor = "\nMAP_BY_ID = {"
idx = src.find(anchor)
if idx == -1:
    raise SystemExit("找不到 MAP_BY_ID 锚点")
# 在 MAPS 列表闭合 ] 后、MAP_BY_ID 前插入
roads_code = "\n".join("    " + json_line if False else line for line in [])
# 直接用 Python 字面量序列化插入
import json as _json
roads_repr = _json.dumps(ROAD_MAPS, ensure_ascii=False, indent=2)
# 缩进适配（MAPS 元素是 4 空格缩进）
roads_block = "\n".join("    " + l if l.strip() else l for l in roads_repr.split("\n"))
src = src[:idx] + "\n" + roads_block + "\n]" + src[idx:]

# 2. 改写 MAP_CONNECTIONS
# 删除的直连边
REMOVE = [("anvil_fort", "frost_horn"), ("oak_town", "white_deer")]
# 新增路图连接
ADD = []
for r in ROAD_MAPS:
    rid = r["id"]
    a, b = rid.replace("road_", "", 1).split("_", 1)
    ADD.append((a, rid))
    ADD.append((b, rid))
    ADD.append((rid, a))
    ADD.append((rid, b))

# 找到 MAP_CONNECTIONS 块（'MAP_CONNECTIONS = {' 到 '\n}\n' 结束）
conn_anchor = "MAP_CONNECTIONS = {"
cidx = src.find(conn_anchor)
if cidx == -1:
    raise SystemExit("找不到 MAP_CONNECTIONS")
cend = src.find("\n}\n", cidx)
if cend == -1:
    raise SystemExit("找不到 MAP_CONNECTIONS 结束")

block = src[cidx:cend + 3]
# 解析当前连接
import ast
conns = ast.literal_eval(block.split("=", 1)[1].strip().rstrip(","))
# 应用删除
for a, b in REMOVE:
    if a in conns and b in conns[a]:
        conns[a] = [x for x in conns[a] if x != b]
    if b in conns and a in conns[b]:
        conns[b] = [x for x in conns[b] if x != a]
# 应用新增
for src_id, dst_id in ADD:
    if src_id not in conns:
        conns[src_id] = []
    if dst_id not in conns[src_id]:
        conns[src_id].append(dst_id)

# 序列化回（保持原格式：每行 '  "id": [..],'）
new_block = "MAP_CONNECTIONS = {\n"
for k in sorted(conns.keys()):
    v = conns[k]
    items = ", ".join('"{}"'.format(x) for x in v)
    new_block += '    "{}": [{}],\n'.format(k, items)
new_block += "}\n"
src = src[:cidx] + new_block + src[cend + 3:]

open(maps_path, "w", encoding="utf-8").write(src)
print(f"✅ 已更新 {maps_path}")
print(f"   MAPS 新增 {len(ROAD_MAPS)} 张路图")
print(f"   删除直连 {len(REMOVE)} 条，新增连接 {len(ADD)//2} 条")
