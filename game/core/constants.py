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

# ================= v99.3 战斗/流程概率常量 =================
# （原散落各文件的裸数字，集中后改平衡参数只动这里）
FLEE_CHANCE = 0.75             # battle.py:538 战斗逃跑成功率
MON_SKILL_CHANCE = 0.3         # battle.py:1294 怪物技能使用概率
MON_SKILL_CRIT = 0.1           # battle.py:1308 怪物技能暴击率
SHIELD_COUNTER_CHANCE = 0.6    # battle.py:1597 v51 盾牌反击概率（反击 120% 伤害）
REFLECT_CHANCE = 0.25          # battle.py:1605 龙鳞套反弹概率（反弹 25% 伤害）
HOLY_TENACITY_CHANCE = 0.20    # battle.py:1648 v64 神圣坚韧受击回复概率
ENCOUNTER_EVENT_CHANCE = 0.35  # combat.py:95 探索随机事件概率（野外/外郊/核心区）
SA_BOSS_CHANCE = 0.05          # combat.py:125/202 子区域 Boss 出现概率
ENCOUNTER_LOW_CHANCE = 0.5     # combat.py:144 普通怪低概率（新手保护）
FISH_RARE_CHANCE = 0.5         # economy.py:211 垂钓稀有档概率
PET_EGG_ORANGE_CHANCE = 0.15   # economy.py:240 月光兔蛋（垂钓传说档）概率
RARE_MAT_CHANCE = 0.10         # economy.py:280 稀有材料额外掉落概率
PROF5_BONUS_CHANCE = 0.3       # economy.py:306 副业 5 级额外产出概率
INST_EVENT_CHANCE = 0.5        # instance.py:278 副本探索事件概率
MOVE_ENCOUNTER_CHANCE = 0.25   # world.py:2026 移动撞怪概率
# v101.5 新增
STARFALL_STUN_CHANCE = 0.20    # battle_mech.py:258 星陨斩眩晕概率
BOSS_BP_DROP_CHANCE = 0.05     # drops.py:69 Boss 图纸惊喜掉率
TRADER_DEAL_CHANCE = 0.5       # event_templates.py:253 流浪商人成交概率
CHEST_BP_CHANCE = 0.5          # item_templates.py:235 宝箱蓝图概率

# 配方副业等级阶梯（economy.py _craft_prof_need：装备等级 → 副业门槛）
RECIPE_LV_TIERS = (10, 30, 50, 70, 90)

# ================= v102.1 地图/子区域类型常量 =================
# （v102 审计：代码层 15+ 处裸比较中文字符串，收敛后改类型名只动数据+这里）
# 地图 type（data/maps.py）
MAP_TYPE_TOWN = "城镇区域"       # 安全区：可触发 POI，无怪
MAP_TYPE_FIELD = "野外"
MAP_TYPE_INSTANCE = "副本"
MAP_TYPE_HIDDEN = "隐藏区域"
# 子区域 type（data/subareas.py）
SUB_TYPE_TOWN = "城镇"           # 中心广场（首个子区域）
SUB_TYPE_STREET = "城镇街道"     # 如东大街：连广场 + 城镇出口
SUB_TYPE_GATE = "城镇出口"       # 如镇郊：出城/进城落点

# ================= v102.2 物品 type 常量 =================
# （item_templates.infer_template 原裸比较中文 type，收敛后改类型文案只动数据+这里）
ITEM_TYPE_PET_EGG = "宠物蛋"
ITEM_TYPE_MOUNT = "坐骑"
