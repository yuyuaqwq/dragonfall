# -*- coding: utf-8 -*-
"""统计 skills.py 职业/技能/desc 分布"""
import re

src = open(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py", encoding="utf-8").read()

# 顶层职业块（4空格缩进）
clses = re.findall(r'^    "(cls_[a-z0-9_]+)": \{', src, re.M)
print("顶层职业块数:", len(clses))
print("唯一职业:", len(set(clses)))

# 按出现顺序统计每个职业块的技能数
seen = []
for m in re.finditer(r'^    "(cls_[a-z0-9_]+)": \{', src, re.M):
    cls = m.group(1)
    start = m.end()
    nxt = re.search(r'^    "cls_[a-z0-9_]+": \{', src[start:], re.M)
    end = start + (nxt.start() if nxt else len(src) - start)
    block = src[start:end]
    n_sk = len(re.findall(r'"(sk_[a-z0-9_]+)": \{', block))
    n_desc = len(re.findall(r'"desc":', block))
    seen.append((cls, n_sk, n_desc))
    print(f"  {cls}: {n_sk} 技能, {n_desc} desc")

print("\n总技能 key:", sum(x[1] for x in seen))
print("总 desc:", sum(x[2] for x in seen))
