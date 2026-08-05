# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - mounts.py"""
MOUNT_POOL = [
    {"key": "mount_horse",  "name": "老马",  "icon": "🐴", "lv": 1,  "price": 500, "discount": 0.10, "elite_bonus": 0.0,  "boss_bonus": 0.0,
     "desc": "温顺可靠的老马，腿脚虽慢但从不尥蹶子。传送费 -10%"},
    {"key": "mount_steed",  "name": "骏马",  "icon": "🐎", "lv": 15, "price": 0,  "discount": 0.20, "elite_bonus": 0.0,  "boss_bonus": 0.0,
     "desc": "脚程极快的良种骏马，跑商赶路两不误。传送费 -20%（精英掉落『骏马缰绳』）"},
    {"key": "mount_wolf",   "name": "雪狼",  "icon": "🐺", "lv": 30, "price": 0,  "discount": 0.30, "elite_bonus": 0.05, "boss_bonus": 0.0,
     "desc": "北境驯化的雪狼，嗅觉灵敏专挑厉害的打。传送费 -30%，探索精英率 +5%（Boss 掉落『雪狼缰绳』）"},
]

MOUNT_BY_KEY = {m["key"]: m for m in MOUNT_POOL}

MOUNT_DROP_ELITE = {"mount_steed": 0.06}

MOUNT_DROP_BOSS = {"mount_wolf": 0.10}

