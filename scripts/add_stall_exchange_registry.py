# -*- coding: utf-8 -*-
"""向 _registry.py 插入 stall_exchange 正则（用 python raw 字符串精确替换，避免 patch 双写转义）"""
import io

path = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\commands\_registry.py"
with io.open(path, "r", encoding="utf-8") as f:
    src = f.read()

old = '    "stall_view": r\'^(?:\\[At:\\d+\\]\\s*)?摊位(?:[\\s\\S]*)$\',\n'
new = old + '    "stall_exchange": r\'^(?:\\[At:\\d+\\]\\s*)?换(?:[\\s\\S]*)$\',\n'

if "stall_exchange" in src:
    print("stall_exchange already present, skip")
elif old in src:
    src = src.replace(old, new, 1)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("inserted stall_exchange")
else:
    print("ERROR: anchor not found")
    print([l for l in src.splitlines() if "stall_view" in l])
