# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - pets.py

24 章宠物系统：统一从数据层（game/data/pets.py）re-export。
旧版（7 品种无技能）已随删档废弃，此处保留兼容路径。
"""
from ..data.pets import PET_POOL, PET_EGG_ROLL, PET_MAX_LEVEL, \
    make_pet_egg, pet_exp_need, pet_exp_mult, pet_skill_label, pet_quality_label, pet_line, \
    pet_exp_bonus, pct_str  # noqa: F401  v133.2 品质分级经验加成；v173.2 封顶50+等级差乘区
