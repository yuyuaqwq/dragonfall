# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - enhance.py"""
ENHANCE_TABLE = {
    0: {"rate": 1.00, "cost": 50,   "mult": 1.00},
    1: {"rate": 0.90, "cost": 120,  "mult": 1.10},
    2: {"rate": 0.80, "cost": 250,  "mult": 1.22},
    3: {"rate": 0.65, "cost": 450,  "mult": 1.36},
    4: {"rate": 0.50, "cost": 800,  "mult": 1.52},
    5: {"rate": 0.35, "cost": 1300, "mult": 1.70},
    6: {"rate": 0.22, "cost": 2000, "mult": 1.90},
    7: {"rate": 0.12, "cost": 3200, "mult": 2.12},
    8: {"rate": 0.06, "cost": 5000, "mult": 2.36},
    9: {"rate": 0.03, "cost": 8000, "mult": 2.62},
}

MAX_ENHANCE = 9

ENHANCE_FAIL_DROP = {5: 2}

ENHANCE_SMITH_MAPS = ["vila_street", "stonefist_camp", "shadow_street"]

