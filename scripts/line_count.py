# -*- coding: utf-8 -*-
"""统计 dragonfall 代码/数据行数"""
import os
from collections import defaultdict

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
GAME = os.path.join(ROOT, "game")

tot = defaultdict(int)
files = defaultdict(int)
for d, _, fs in os.walk(GAME):
    for f in fs:
        if not f.endswith(".py"):
            continue
        p = os.path.join(d, f)
        n = sum(1 for _ in open(p, encoding="utf-8"))
        if "/data" in d or d.endswith("data"):
            layer = "data 数据层"
        elif "/core" in d or d.endswith("core"):
            layer = "core 核心逻辑"
        elif "/store" in d or d.endswith("store"):
            layer = "store 存储层"
        elif "/commands" in d or d.endswith("commands"):
            layer = "commands 命令层"
        else:
            layer = "game 根"
        tot[layer] += n
        files[layer] += 1
        tot["_all"] += n
        files["_all"] += 1

for k in ["data 数据层", "core 核心逻辑", "store 存储层", "commands 命令层", "game 根", "_all"]:
    if k == "_all":
        print("game/ 合计: %d 行 (%d 文件)" % (tot[k], files[k]))
    else:
        print("  %s: %d 行 (%d 文件)" % (k, tot[k], files[k]))

# main.py
mp = os.path.join(ROOT, "main.py")
print("main.py: %d 行" % len(open(mp, encoding="utf-8").readlines()))

# tests/
td = os.path.join(ROOT, "tests")
tn = sum(len(open(os.path.join(td, f), encoding="utf-8").readlines())
         for f in os.listdir(td) if f.endswith(".py"))
print("tests/: %d 行 (%d 文件)" % (tn, len([f for f in os.listdir(td) if f.endswith('.py')])))

# 脚本目录
sd = os.path.join(ROOT, "scripts")
sn = sum(len(open(os.path.join(sd, f), encoding="utf-8").readlines())
         for f in os.listdir(sd) if f.endswith(".py"))
print("scripts/: %d 行" % sn)
