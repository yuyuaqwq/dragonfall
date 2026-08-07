# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - pets.py

24 章宠物系统：统一从数据层（game/data/pets.py）re-export。
旧版（7 品种无技能）已随删档废弃，此处保留兼容路径。
"""
from ..data.pets import PET_POOL, make_pet_egg, pet_exp_need, pet_skill_label  # noqa: F401
