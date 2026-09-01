# -*- coding: utf-8 -*-
"""口径常量表（v131 多维度模型 —— 全部来源有据，改数值先改这里并同步 docs/NUMERIC_TOOLKIT.md）。

乘区口径（验证：scripts/_tmp_calib_v2_verify.py 真实引擎逐职误差 ≤3.2%）：
  a. 自由属性点  DEFAULT_ATTR_PTS + 每级 ATTR_PER_LV 点，物理系全 str / 法系全 int
  b. tier        TIER_GROWTH（30/60/90 门槛）+ 攻线分支（evolve_path=1）atk×1.06
  c. 技能轴      ROTATIONS（技能倍率 E.skill_info 实读，Lv.1 保守）
  d. 攻击词条    AFFIX_MULT = 1.20（蓝装 2 条词条 ≈ 等价收益，10 章七）
  e. 附魔        ENCHANT_CRIT = 0.04（ENCHANT_MAX_VALUE.crit，蓝装 1 孔安全上限）
  f. 药水        POTION_ATK / POTION_MATK = +30%（alchemy.py 攻击药水/鲛人之泪，3 回合）

组队口径（32 章三 + 00 章副本公式，保守下界）：
  Boss HP = 模板 × [hp_mult + 0.65×(人数 - min_players)]
  组队 DPS = 人均 × 人数 × TEAM_BUFF（队伍技能：战吼全队攻+30%、元素流转全队魔攻+50% → 保守 1.10）
  ⚠️ 未计元素反应/称号/种族/终结技/控制链 —— 真实只会更快，结论偏保守。
"""
from .env import setup_env  # noqa: F401  确保路径/DB 先就绪

# ---------------- 职业表：(中文名, class_id, 物/法, 自由点主属性) ----------------
CLASSES = [
    ("战士", "cls_zhan_shi", "phys", "str"),
    ("游侠", "cls_you_xia", "phys", "str"),
    ("法师", "cls_fa_shi", "magi", "int"),
    ("牧师", "cls_mu_shi", "magi", "int"),
    ("刺客", "cls_ci_ke", "phys", "str"),
    ("拳师", "cls_wu_seng", "phys", "str"),
    ("诗人", "cls_shi_ren", "magi", "int"),   # v153 第七基础职业（v2.1 补，法系）
]

def cls_id(name_or_id: str) -> str:
    """中文名或 ID → class_id（找不到抛 KeyError，误用立即暴露）。"""
    for _name, _id, *_ in CLASSES:
        if name_or_id in (_name, _id):
            return _id
    raise KeyError(f"未知职业: {name_or_id}（可用: {', '.join(c[0] for c in CLASSES)}）")

def cls_name(cls_id: str) -> str:
    for _name, _id, *_ in CLASSES:
        if _id == cls_id:
            return _name
    return cls_id

# ---------------- 成长乘区 ----------------
TIER_GROWTH = {0: 1.00, 1: 1.15, 2: 1.30, 3: 1.50}   # 27 附章 2.2：30/60/90 级解锁
EVOLVE_ATK_MULT = 1.06                                 # 攻线分支 atk×1.06（v25 BRANCH_BONUS）
DEFAULT_ATTR_PTS = 9                                   # 初始属性点（engine DEFAULT_ATTR_PTS）
ATTR_PER_LV = 3                                        # 每级 +3 点（27 附章 2.1）
ATTR_GAIN = {"str": ("atk", 1.2), "int": ("matk", 1.2), "agi": ("spd", 0.8), "vit": ("hp", 8)}

# ---------------- 输出乘区（默认全开 = 真实玩家） ----------------
POTION_ATK = 0.30      # 攻击药水 攻+30%（3 回合）alchemy.py
POTION_MATK = 0.30     # 鲛人之泪 魔攻+30%（3 回合）alchemy.py
AFFIX_MULT = 1.20      # 蓝装 2 条攻击词条 ≈ ×1.20（10 章七：同品质 2 词条等价收益）
ENCHANT_CRIT = 0.04    # 附魔暴击上限（蓝装 1 孔）enchant.py ENCHANT_MAX_VALUE.crit
TEAM_BUFF = 1.10       # 组队团队技能保守期望（战吼 全队攻+30% / 元素流转 全队魔攻+50%）

# ---------------- 技能轴（每职业一次行动的代表循环；倍率 E.skill_info 实读；Lv.1 保守档） ----------------
ROTATIONS = {
    "cls_zhan_shi": [("嗜血斩", 1.0)],                   # v153：嗜血斩 1.25（T1 狂战士 lv38，吸血 25%）
    "cls_you_xia": [("蓄力射击", 1.0)],                  # v153：蓄力射击 1.2（T1 森语者 lv44；蓄力模型保守按 1.2）
    "cls_fa_shi": [("织焰", 1.0)],                       # v153：织焰 1.48（T1 元素使 lv32 火系）
    "cls_mu_shi": [("骨噬诅咒", 1.0)],                   # v153：骨噬诅咒 1.25（T1 死灵祭司 lv38 暗蚀）
    "cls_ci_ke": [("链舞", 1.0)],                        # v153：链舞 1.14（T1 影舞者 lv44 物理）
    "cls_wu_seng": [("崩拳", 1.0)],                      # v153：崩拳 1.25（T1 格斗士 lv50 物理）
}
ASSASSIN_COND_WEIGHT = 1.09   # 双刃乱舞 HP>70% 条件加权：boss 前 30% 血量生效 → (1+0.3×0.3)
MONK_PUNCH_CYCLE = 1 / 3.0    # 碎骨拳每 3 行动 1 发（3 气）——与纯循环区别，加权由 per_action_dmg 处理
DEF_DOWN_SKILLS = {"cls_zhan_shi": {"猛击": 0.5}}   # 破甲斩后敌方防御减半（DEF_DOWN_MULT=0.5）

# ---------------- 组队与副本口径（32 章三） ----------------
# hp_mult 档位：单刷 1.6-1.8 / 2-3 人 2.2-2.5 / 4 人 2.7-3.0（取中值入表，实例可覆盖）
BOSS_HP_MULT = {
    1: 1.70,
    2: 2.35,
    3: 2.35,
    4: 2.85,
}
TEAM_PER_PLAYER_ADD = 0.65   # 每多 1 人 Boss HP +0.65（32 章三）

# ---------------- 分阶段数值成长（v156 v2.1，鱼鱼点名"每个阶段"） ----------------
# 阶段划分依据：转职门槛 30/60/90（EVOLVE_LEVELS）+ 副本等级分布 15→94 + 装备品质进度（计划 §一.5.1）。
# 装备档位 = 该阶段典型等级代表性装备（P1 蓝+0 近似新手下限 / P2 蓝+5 / P3 紫+9 / P4 紫+9 / P5 橙+9）。
# loadout 复用 LOADOUTS 档位（team_* 档 players=4 不影响单人面板——gear_loadout 只取 quality/enhance/upgrade/gem/set）。
STAGES = [
    ("P1", 10, "solo_low",      "新手",    "白/绿 +0~+3"),
    ("P2", 24, "solo_mid",      "一职",    "蓝 +0~+5"),
    ("P3", 45, "team_purple9",  "二职",    "蓝+5 / 紫"),
    ("P4", 75, "team_purple9",  "三职",    "紫+9 / 橙"),
    ("P5", 95, "team_orange9",  "毕业",    "橙+9 升10 满加成"),
]
# 阶段成长率约束（计划 §一.5.3，防数值失控；纯等级成长 1.7~2.0×，叠加装备档位 2.2~3.5×）：
#   玩家 HP 每阶段 2.2~3.5× / 技能 DPS 2.5~4.5× / 同级怪 HP 2.0~3.0× / 承伤% ≤2.5% 不恶化
# 门禁断言用 [STAGE_GROWTH_MIN, STAGE_GROWTH_MAX]（宽容带：同档位阶段纯等级成长 ~1.4× 也合法）
STAGE_GROWTH_MIN = 1.25   # 阶段增幅下限（防断档：低于此 = 某阶段成长卡死）
STAGE_GROWTH_MAX = 5.0    # 阶段增幅上限（防爆炸：高于此 = 数值失控）
# Boss 单发占 HP 目标（计划 §一.6.3）：每阶段 8~12%（承伤有压力但不秒杀；后期不得低于 5%）
BOSS_HIT_PCT_MIN = 0.08
BOSS_HIT_PCT_MAX = 0.12
# 普通怪击杀轮目标（32 章三档难度锚点）：裸装同级 4~6 轮
MONSTER_KILL_ROUND_MIN = 4
MONSTER_KILL_ROUND_MAX = 6

# 玩家档位预设（--loadout / gear_loadout；quality 直接对 QUALITY 表 white/green/blue/purple/orange）
LOADOUTS = {
    "naked":       {"quality": "white", "enhance": 0, "players": 1, "label": "裸装"},
    "solo_low":    {"quality": "blue",  "enhance": 0, "players": 1, "label": "单刷 蓝+0"},
    "solo_mid":    {"quality": "blue",  "enhance": 5, "players": 1, "label": "单刷 蓝+5"},
    "team_mid":    {"quality": "blue",  "enhance": 5, "players": 4, "label": "4人 蓝+5"},
    "team_purple9": {"quality": "purple", "enhance": 9, "players": 4, "label": "4人 紫+9"},
    "team_orange9": {"quality": "orange", "enhance": 9, "players": 4, "label": "4人 橙+9"},
    "solo_mid_upgrade": {"quality": "blue", "enhance": 5, "upgrade": 5, "players": 1, "label": "单刷 蓝+5升5"},
    "team_max_full": {"quality": "orange", "enhance": 9, "upgrade": 10, "gem_tier": 6, "set_bonus": True, "players": 4, "label": "4人 橙+9满加成"},
    "legacy":      {"quality": "blue",  "enhance": 0, "players": 1, "label": "旧模型(对照)"},
}

# ---------------- 词条分系常量（v130.2 装备-资源联动词条，31 条按职业线分系） ----------------
# 从 game/data/affixes.py 的 AFFIXES 31 条带 line 字段词条按职业归属聚合（权威数据只读）。
# 职业归属判定：line 前缀（战士·/法师·/游侠·/牧师·/刺客·/拳师·）。
# 用途：装备区分度/词条分系权重（同职业线词条出现权重 0.6 偏好，其余 0.4）。
AFFIX_CLASS_LINES = {
    "战士": ["战意", "怒火熔铸", "战吼回响", "浴血", "残血灼薪", "沸血浇筑"],
    "法师": ["充能汲引", "凝神塑能", "印记铭刻", "反应催化"],
    "游侠": ["精力刀刃", "精力潮汐", "盈满背囊", "暴击蓄能", "疾风余韵"],
    "牧师": ["圣辉回响", "神赐容光", "圣光之心", "圣徽之佑", "虔诚护符"],
    "刺客": ["暴击回点", "终结之技", "连段护持", "连段之锋", "节奏之徽"],
    "拳师": ["连段回收", "气量强化", "磐息", "爆发贯体", "起手之势", "蓄势精通"],
}
# 同职业线词条出现权重（0.6=偏好）；其余职业线 0.4（总和恒 1.0，主 agent 决定是否消费）
AFFIX_LINE_WEIGHT = {name: 0.6 for name in AFFIX_CLASS_LINES}