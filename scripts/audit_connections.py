# -*- coding: utf-8 -*-
"""分析城镇-城镇直接连接，为必经之路设计提供数据"""
import sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

from game.content import MAPS, MAP_BY_ID, MAP_CONNECTIONS

towns = [m['id'] for m in MAPS if m.get('type') == '城镇区域']
print(f"总地图: {len(MAPS)}, 城镇: {len(towns)}, 野外: {len(MAPS)-len(towns)}")

print("\n=== 城镇-城镇直接相连的边 ===")
edges = []
for tid in towns:
    for nid in MAP_CONNECTIONS.get(tid, []):
        if nid in towns:
            edges.append((tid, nid))
print(f"共 {len(edges)} 条城镇直连边:")
for a, b in sorted(edges):
    print(f"  {a} <-> {b}")

print("\n=== 城镇的邻居构成（哪些直连城镇、哪些野外）===")
for tid in towns:
    nbs = MAP_CONNECTIONS.get(tid, [])
    t_nbs = [n for n in nbs if n in towns]
    w_nbs = [n for n in nbs if n not in towns]
    print(f"  {tid}: 直连城镇={t_nbs if t_nbs else '无'} | 野外={w_nbs if w_nbs else '无'}")
