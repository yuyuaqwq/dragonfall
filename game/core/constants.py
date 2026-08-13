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

# ================= v102.3 职业 ID 常量 =================
# （逻辑层 7 处裸比较 class_name == "cls_novice"，收敛后改职业 ID 只动数据+这里）
CLASS_NOVICE = "cls_novice"      # 见习冒险者（行会就职判定/隐藏职业解锁）

# ================= v102.6 属性集合常量 =================
# （19 处裸写 ("crit","dodge") 判断"百分比显示属性"，收敛后改显示规则只动这里）
PCT_STATS = ("crit", "dodge", "precise", "pene_phys", "pene_magi", "tenacity", "luck",
             "cdr", "elem_res", "abyss_res", "exp_bonus", "gold_bonus",
             "heal_power", "shield_power",    # v106.2 治疗/护盾强度
             "lifesteal", "crit_dmg", "block",  # v106.3 吸血/暴击伤害/格挡（面板化，2026-08-13 鱼鱼拍板）
             "thorns", "phys_reduce", "magic_reduce", "lifesteal_phys", "lifesteal_magi",
             "summon_power")  # v106.4 反伤/物魔免/物法吸 + v107 召唤强化

# v106：百分比属性上限表（面板聚合 cap 用；crit 0.5 / dodge 0.4 / 其余 0.6 的旧三目表达式统一收敛）
PCT_CAPS = {"crit": 0.5, "dodge": 0.4, "precise": 0.6, "pene_phys": 0.6, "pene_magi": 0.6,
            "tenacity": 0.5, "luck": 0.5,
            "cdr": 0.4, "elem_res": 0.5, "abyss_res": 0.5, "exp_bonus": 0.5, "gold_bonus": 0.5,
            "heal_power": 0.5, "shield_power": 0.5,
            "lifesteal": 0.3, "crit_dmg": 1.0, "block": 0.4,
            "thorns": 0.5, "phys_reduce": 0.4, "magic_reduce": 0.4,
            "lifesteal_phys": 0.3, "lifesteal_magi": 0.3,
            "summon_power": 0.5}  # v106.3/v106.4 吸血30/暴伤100/格挡40/反伤50/物魔免40/物法吸30 + v107 召唤50

# v106.4：特殊属性——面板 0 时不显示，有加成才显示（防面板爆炸，鱼鱼拍板）
OPTIONAL_STATS = ("lifesteal", "crit_dmg", "block", "thorns", "phys_reduce", "magic_reduce",
                  "lifesteal_phys", "lifesteal_magi", "summon_power")  # v107 召唤强化

# v106：百分比穿透属性（多来源乘算合成 1-Π(1-pᵢ)，不加法）
PENE_PCT_STATS = ("pene_phys", "pene_magi")

# ================= v103.3 B3 整数魔法数字 =================
# （第三轮审计 B3：等级阈值/容量/奖励量裸数字，收敛后改数值只动这里）
EVOLVE_LEVELS = {1: 30, 2: 60, 3: 90}      # 转职等级门槛（player.py:405/419/828、world.py:2153、engine.py:633）
EVOLVE_FEES = {1: 500, 2: 2000, 3: 5000}   # 转职重置费用（按当前 tier，player.py:695）
RESET_SKILL_COST = 500                     # 技能洗点费用（player.py:660/752）
DEFAULT_MAX_MP = 50                        # 面板/战斗 max_mp 兜底（battle.py:92/262、combat.py:1329、instance.py:764/765）
PVP_TIMEOUT_SEC = 300                      # PVP 超时秒：5 分钟无行动自动解除（combat.py:1731）
GUILD_EXP_BASE = 300                       # 公会升级经验 = 等级 * 300（social.py:490、store/social.py:394/395）
PROF_EXP_BASE = 20                         # 遗留常量（v105 起由 prof_exp_need 二次曲线取代，保留兼容外部引用）


def prof_exp_need(lv):
    """副业升级经验需求（v105 平衡曲线）：need(lv) = 5*lv² + 15*lv

    设计意图（2026-08-13 鱼鱼拍板"无脑 x20 不合适"）：
    - 累计 2100 满级（原线性累计 900，无脑 x20 前期过快后期无爬升感）
    - 前期快：Lv.1→2 仅 20（新手第一天解锁基础配方），拜师礼 50 可跳 Lv.2
    - 中段平滑爬升：Lv.2→3=50 / Lv.3→4=90 / Lv.4→5=140 / Lv.5→6=200 / Lv.6→7=270
    - 后期冲刺感：Lv.7→8=350 / Lv.8→9=440 / Lv.9→10=540（史诗→传说配方门槛）
    - 满级周期估算：等待型（可挂机）约 1 个月，制造型（体力限制）约 2-3 个月
    - 存量玩家兼容：exp 按级内进度存储，曲线变更只影响后续升级需求，已满级不受影响
    """
    return 5 * lv * lv + 15 * lv
