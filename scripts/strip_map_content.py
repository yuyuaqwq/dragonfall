# -*- coding: utf-8 -*-
"""v87.6 地图级内容字段清理 v2：逐行深度匹配，避免正则嵌套陷阱。

架构（鱼鱼定）：地图=显示层+共有属性，所有内容（怪物/NPC/交互）在子区域配置。
对 MAPS/MAP_BY_ID 中的 npcs/monsters/elite/boss 整块替换为空。
用法：python scripts/strip_map_content.py --write  （默认仅统计）
"""
import os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(BASE, "game", "data", "maps.py")
text = open(path, encoding="utf-8").read()
lines = text.split("\n")

HEAD_RE = re.compile(r'^\s*"(npcs|monsters|elite|boss)": (\[|None),?\s*$')
# 单行内联列表： "npcs": ["a", "b"], / "elite": ["x", ...],
INLINE_RE = re.compile(r'^(\s*)"(npcs|monsters|elite|boss)": \[.*\],?\s*$')

stats = {"npcs": 0, "monsters": 0, "elite": 0, "boss": 0}
out = []
i = 0
while i < len(lines):
    m = HEAD_RE.match(lines[i])
    if m and m.group(2) == "[":
        key = m.group(1)
        # 从该行起跟踪括号深度，找到配对闭合
        depth = lines[i].count("[") - lines[i].count("]")
        j = i
        while depth > 0 and j < len(lines):
            j += 1
            if j >= len(lines):
                break
            depth += lines[j].count("[") - lines[j].count("]")
        if depth != 0:
            print(f"⚠️ 未闭合: {lines[i].strip()[:40]} 行 {i+1}")
            out.append(lines[i])
            i += 1
            continue
        # 整块替换（j 是闭合行）
        rep = "[]" if key in ("npcs", "monsters") else "None"
        indent = re.match(r"\s*", lines[i]).group(0)
        out.append(f'{indent}"{key}": {rep},')
        stats[key] += 1
        i = j + 1
        continue
    mi = INLINE_RE.match(lines[i])
    if mi:
        key = mi.group(2)
        rep = "[]" if key in ("npcs", "monsters") else "None"
        indent = mi.group(1)
        out.append(f'{indent}"{key}": {rep},')
        stats[key] += 1
        i += 1
        continue
    out.append(lines[i])
    i += 1

print("=== 统计 ===")
for k, v in stats.items():
    print(f"  {k}: {v} 处")
print(f"共 {sum(stats.values())} 处")

if "--write" in sys.argv:
    open(path, "w", encoding="utf-8").write("\n".join(out))
    print("✅ 已写回 maps.py")
