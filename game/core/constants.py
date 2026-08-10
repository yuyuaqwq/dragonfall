# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - constants.py（v98.2：全局常量收敛）

原魔法字符串（"oak_town" 等）散落 8 处代码 + 1 处 SQL，收敛后：
- 改新手村/默认城镇 = 只改这里
- 建号默认值从 SQL 字符串提到代码（可测试、可配置）
"""
# 新手村/默认地图（死亡复活、回城兜底、建号出生点）
START_MAP = "oak_town"
START_SUBAREA = "oak_town_1"

# 建号默认值（原写死在 store/players.py SQL 字符串里）
DEFAULT_GOLD = 50
DEFAULT_ATTR_PTS = 9
DEFAULT_STAMINA = 100
