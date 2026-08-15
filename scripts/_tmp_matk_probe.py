# -*- coding: utf-8 -*-
"""临时：获取龙裔誓约 30 级 matk（测试期望值重算用）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT

p = {"class_name": "龙裔誓约", "level": 30, "hp": 500, "max_hp": 500,
     "mp": 100, "max_mp": 100,
     "equipment": {"weapon": {"name": "测试剑", "stats": {"atk": 100, "matk": 100}, "affixes": [], "enhance": 0}},
     "attributes": {"str": 10, "int": 10},
     "learned_skills": [], "race": "human"}
b = BT.Battle("怪物", {"name": "t", "hp": 10000, "max_hp": 10000, "atk": 0, "def": 20, "mdef": 20, "spd": 10}, {}, p)
st = b._player_stats(p)
print("atk =", st["atk"], "matk =", st["matk"])
