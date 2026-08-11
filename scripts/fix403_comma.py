# -*- coding: utf-8 -*-
"""v95.32 #403 修复：插入掉落名时原末项缺尾逗号导致隐式字符串拼接
（"幽灵之尘"+"鬼魂精华" = "幽灵之尘鬼魂精华"）——给前一行补逗号"""
import io

PATH = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\subareas.py"

with io.open(PATH, "r", encoding="utf-8") as f:
    txt = f.read()

# 目标模式：无逗号的掉落名行 紧跟 新插入行（缺逗号 → 隐式拼接）
FIXES = [
    ('"幽灵之尘"\n                        "鬼魂精华",\n',
     '"幽灵之尘",\n                        "鬼魂精华",\n'),
    ('"堕落精灵护符"\n                        "妖精之尘",\n',
     '"堕落精灵护符",\n                        "妖精之尘",\n'),
    ('"熔岩核心"\n                        "熔岩石",\n',
     '"熔岩核心",\n                        "熔岩石",\n'),
]
for old, new in FIXES:
    n = txt.count(old)
    if n == 0:
        print(f"MISS: {old.strip()!r}")
        continue
    txt = txt.replace(old, new)
    print(f"OK x{n}: {old.strip()!r}")

with io.open(PATH, "w", encoding="utf-8") as f:
    f.write(txt)
print("done")
