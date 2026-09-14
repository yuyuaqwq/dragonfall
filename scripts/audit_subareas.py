# -*- coding: utf-8 -*-
"""统计 SUBAREAS 空壳子区域"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from game.content import SUBAREAS

total_sa = 0
empty = []
with_content = []
for mid, sas in SUBAREAS.items():
    for sa in sas:
        total_sa += 1
        if not sa.get('npcs') and not sa.get('monsters') and not sa.get('funcs') and not sa.get('shop') and not sa.get('healer'):
            empty.append((mid, sa['id'], sa['name']))
        else:
            with_content.append((mid, sa['id'], sa['name']))

print(f"总子区域: {total_sa}, 空壳: {len(empty)}, 有内容: {len(with_content)}")
print("\n=== 空壳子区域 ===")
for mid, sid, name in empty:
    print(f"  {mid} :: {sid} :: {name}")

print("\n=== 有内容的子区域（前60）===")
for mid, sid, name in with_content[:60]:
    print(f"  {mid} :: {sid} :: {name}")
