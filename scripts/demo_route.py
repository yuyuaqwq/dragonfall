# -*- coding: utf-8 -*-
"""模拟玩家路线：橡木镇 -> 白鹿城 必经之路体验"""
import sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

import game.data as C

def route(start, goal):
    """BFS 找路径"""
    from collections import deque
    q = deque([(start, [start])])
    seen = {start}
    while q:
        cur, path = q.popleft()
        if cur == goal:
            return path
        for nxt in C.MAP_CONNECTIONS.get(cur, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, path + [nxt]))
    return None

print("=== 路线体验 ===")
for start, goal in [("oak_town", "white_deer"), ("oak_town", "dawn_city"), ("white_deer", "ironharbor")]:
    path = route(start, goal)
    if path:
        names = " → ".join(C.MAP_BY_ID[x]["name"] for x in path)
        print(f"{C.MAP_BY_ID[start]['name']} → {C.MAP_BY_ID[goal]['name']}: {names}")
    else:
        print(f"❌ {start} → {goal}: 无路径!")

print("\n=== 橡木镇地图面板（模拟）===")
m = C.MAP_BY_ID["oak_town"]
print(f"🗺️ 【{m['name']} · {m['subareas'][0]['name']}】")
print("🏘️ 本图位置:")
for i, sa in enumerate(m["subareas"], 1):
    npc = f" · {len(sa.get('npcs',[]))} NPC" if sa.get("npcs") else ""
    print(f"  {i}. {sa['name']}{npc}")
print("📮 可前往:", "  ".join(f"{i}.{C.MAP_BY_ID[n]['name']}" for i, n in enumerate(C.MAP_CONNECTIONS["oak_town"], 1)))
