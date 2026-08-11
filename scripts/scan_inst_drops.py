# -*- coding: utf-8 -*-
"""扫描 instances.py 所有副本怪的掉落池长度分布（确定多元素池有哪些）"""
import sys, re, collections
sys.path.insert(0, r"C:\Users\yuyu\qqbot")
from data.plugins.dragonfall.game import content as C

INST = C.INSTANCES
multi = []   # 掉落池 >1 的怪
ghost = []   # 掉落材料不在 MATERIALS 的怪
single = collections.Counter()
for iid, inst in INST.items():
    for si, st in enumerate(inst.get("stages", [])):
        for m in st.get("monsters", []):
            drops = m[5] if len(m) > 5 else []
            for d in drops:
                if C.resolve("materials", d) not in C.MATERIALS:
                    ghost.append((iid, si+1, m[1], d))
            if len(drops) > 1:
                multi.append((iid, si+1, m[1], drops))
        el = st.get("elite")
        if el and len(el) > 5:
            for d in el[5]:
                if C.resolve("materials", d) not in C.MATERIALS:
                    ghost.append((iid, si+1, "ELITE "+el[1], d))
            if len(el[5]) > 1:
                multi.append((iid, si+1, "ELITE "+el[1], el[5]))
        b = st.get("boss")
        if b and len(b) > 5:
            for d in b[5]:
                if C.resolve("materials", d) not in C.MATERIALS:
                    ghost.append((iid, si+1, "BOSS "+b[1], d))
            if len(b[5]) > 1:
                multi.append((iid, si+1, "BOSS "+b[1], b[5]))

print("=== 掉落池多元素(>1)的怪 ===")
for x in multi:
    print(" ", x)
print(f"\n共 {len(multi)} 个多元素池")
print("\n=== 幽灵材料(不在 MATERIALS 表) ===")
for x in ghost:
    print(" ", x)
print(f"\n共 {len(ghost)} 处幽灵材料")
