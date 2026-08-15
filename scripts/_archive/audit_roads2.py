# -*- coding: utf-8 -*-
# ⚠️ 已废弃（13.4.6 起城镇直连为合法设计，本族脚本前提失效），禁止运行
# 已作废：13.4.6 后城镇直连为有意保留（如 anvil_fort↔frost_horn 要塞相邻），
# 本审计前提失效，勿据此修改连通。
"""必经之路设计：两城之间已有中间图检测"""
import sys as _sys
print("已废弃，禁止运行", file=_sys.stderr)
_sys.exit(1)

import sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

from game.data.maps import MAPS, MAP_CONNECTIONS

byid = {m['id']: m for m in MAPS}
pairs = [
    ('oak_town', 'white_deer'), ('oak_town', 'maple_village'),
    ('white_deer', 'ironharbor'), ('white_deer', 'silver_brook'),
    ('dawn_city', 'ironshield_town'), ('dawn_city', 'moon_gate'),
    ('moon_gate', 'star_song'), ('frost_horn', 'anvil_fort'),
    ('frost_horn', 'aurora_town'), ('anvil_fort', 'cold_ridge'),
    ('anvil_fort', 'deep_tunnel'), ('dragon_pass', 'moon_court'),
    ('dragon_pass', 'dragon_kin'), ('dragon_pass', 'wind_city'),
    ('jade_port', 'shell_town'), ('jade_port', 'nameless_harbor'),
    ('nameless_harbor', 'pearl_city'),
]
print("=== 两城之间已有中间图（两边都连X）===")
for a, b in pairs:
    mids = []
    for m in MAPS:
        x = m['id']
        if x in (a, b):
            continue
        if a in MAP_CONNECTIONS.get(x, []) and b in MAP_CONNECTIONS.get(x, []):
            mids.append(x)
    print(f"{a} <-> {b}: 中间图={[byid[x]['name'] + '(' + x + ')' for x in mids] if mids else '无'}")

print("\n=== 单边已有衔接（a→X→b 或 b→X→a）===")
for a, b in pairs:
    ways = []
    for x in MAP_CONNECTIONS.get(a, []):
        if x != b and b in MAP_CONNECTIONS.get(x, []):
            ways.append(f"a→{byid[x]['name']}→b")
    for x in MAP_CONNECTIONS.get(b, []):
        if x != a and a in MAP_CONNECTIONS.get(x, []):
            ways.append(f"b→{byid[x]['name']}→a")
    print(f"{a} <-> {b}: {'; '.join(ways) if ways else '无'}")
