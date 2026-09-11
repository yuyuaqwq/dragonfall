# -*- coding: utf-8 -*-
"""
⚠️ 一次性迁移已内化，勿重跑：
导致当前生命 > 上限（如 150/142）。本脚本扫描全服角色，hp 溢出时 clamp 到最终 max_hp。
用法：python scripts/fix_over_hp.py（幂等，可重复跑）"""
print('已废弃，禁止运行', file=__import__('sys').stderr)
__import__('sys').exit(1)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.content_rules.panel import player_stats_detail
from game.store import players as db

import json


def _j(v, default):
    if isinstance(v, dict):
        return v
    if isinstance(v, str) and v:
        try:
            return json.loads(v)
        except Exception:
            return default
    return default


fixed = []
checked = 0
for group_id in db.get_player_groups():
    for p in db.all_players(group_id):
        checked += 1
        st, _ = player_stats_detail(
            p["class_name"], p["level"], _j(p.get("equipment"), {}),
            p.get("class_tier", 0), _j(p.get("attributes"), None), p.get("evolve_path", 0),
            None, p.get("race"),
        )
        max_hp = st["max_hp"]
        hp = p.get("hp", 0)
        if hp > max_hp:
            db.update_player(group_id, p["qq_id"], hp=max_hp)
            fixed.append((group_id, p["qq_id"], p.get("name"), hp, max_hp))

print(f"检查 {checked} 个角色，修复 {len(fixed)} 个溢出:")
for g, q, n, old, new in fixed:
    print(f"  group={g} qq={q} {n}: {old} -> {new}")
