# -*- coding: utf-8 -*-
# ⚠️ 已废弃（13.4.6 起城镇直连为合法设计，本族脚本前提失效），禁止运行
"""必经之路：分析城镇直连边，给出每对城镇的可衔接野外路径"""
import sys as _sys
print("已废弃，禁止运行", file=_sys.stderr)
_sys.exit(1)

import sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

from game.data.maps import MAPS, MAP_CONNECTIONS

towns = [m['id'] for m in MAPS if m.get('type') == '城镇区域']
wilds = [m['id'] for m in MAPS if m.get('type') != '城镇区域']

print("=== 城镇直连边 → 可选野外衔接 ===")
for a in sorted(towns):
    for b in MAP_CONNECTIONS.get(a, []):
        if b in towns and b > a:
            # 找共同野外邻居（a 和 b 都连接的野外图）
            a_w = [n for n in MAP_CONNECTIONS.get(a, []) if n in wilds]
            b_w = [n for n in MAP_CONNECTIONS.get(b, []) if n in wilds]
            common = [w for w in a_w if w in b_w]
            print(f"{a} <-> {b}: a野外={a_w} | b野外={b_w} | 共同={common}")
