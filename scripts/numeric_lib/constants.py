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

# ---------------- 出手频率（v161 可持续 DPS：cast+spd 折算） ----------------
# 引擎 battle.py v161 新曲线（鱼鱼拍板：取消 cap 线性，改边际递减永续公式）：
#   折算系数 = (SPD_REF / spd)^0.5，SPD_REF = 50（速度 50 → 耗时=cast 原值）
#   - 速度 50 → 1.0；25 → 1.41；100 → 0.71；200 → 0.50；400 → 0.35
#   - 永不封顶、永不归零、每点速度边际递减 → 堆速度永远有意义、不爆炸
#   - 旧 SPD_CT_CAP=80 已废弃（cap 让 P3 起速度属性全溢出，鱼鱼否决）；保留常量防外部引用
SPD_REF = 50.0         # 基准速度（速度 50 → 耗时=cast 原值；spd 高 → 更快）
SPD_CT_CAP = 80.0      # ⚠️ 已废弃（v161 起不再使用；保留兼容旧引用）

# 机制稳态倍率表（v161 可持续 DPS：长盘稳态期望，覆盖 ROTATIONS 主力技能）
# 键: 技能名 → 稳态倍率（无机制/未标注 = 1.0，不写）
# 折算依据：条件增伤按覆盖率、叠层按触发周期、联动按收益期望（详见 docs/SUSTAINABLE_DPS_MODEL_v161.md §2.3）
MECH_MULT = {
    # 刺客 收割：cond enemy_low_hp hp_lt 40 mult 1.45 → 血<40% 时段占 40% → 1+0.45×0.40
    "收割": 1.18,
    # 拳师 气力裂空：cond enemy_broken mult 1.5 → 破绽覆盖 ~40% → 1+0.5×0.40
    "气力裂空": 1.20,
    # 诗人 天籁：cond melody_stacks 4 层 ×1.3 → 旋律满层覆盖 ~70% → 1+0.3×0.70
    "天籁": 1.21,
    # 法师 万象天雷：cond enemy_mark_full thunder 3 层 combo+2 → 雷印满层连击收益折 ~1.10
    "万象天雷": 1.10,
    # 战士 战争化身：mech burn 3 层 → 灼烧 DPS 附加 ≈ 直伤 8% 稳态
    "战争化身": 1.08,
    # 刺客 万毒噬心：mech corros 4 层 → 腐蚀 DPS 附加 ≈ 直伤 6% 稳态
    "万毒噬心": 1.06,
}

# ---------------- 技能轴（每职业按阶段选代表技能；倍率 E.skill_info 实读；Lv.1 保守档） ----------------
# v161 修正：不同阶段用不同技能（鱼鱼拍板"不同阶段不是有不同的技能吗"）。
#   原 ROTATIONS 每职业只写 1 个 T1 技能，P1-P5 全用它算——P1 玩家根本不会 T1 技能（Lv32+），
#   导致 P1 梯队失真。改为按等级段给技能：P1/P2 基础、P3 T1、P4 T2、P5 T3。
#   格式：{cls: [(max_lv, 技能名, 权重), ...]}，_skill_dmg 按玩家等级选 <=max_lv 的技能。
ROTATIONS = {
    "cls_zhan_shi": [
        (30, "挥砍", 1.0),      # P1/P2 基础
        (60, "嗜血斩", 1.0),    # P3 T1 狂战士
        (90, "龙息之怒", 1.0),  # P4 T2
        (999, "战争化身", 1.0), # P5 T3
    ],
    "cls_you_xia": [
        (30, "连射", 1.0),
        (60, "蓄力射击", 1.0),
        (90, "穿云箭", 1.0),
        (999, "死神之箭", 1.0),
    ],
    "cls_fa_shi": [
        (30, "火球术", 1.0),
        (60, "织焰", 1.0),
        (90, "元素洪流", 1.0),
        (999, "万象天雷", 1.0),
    ],
    "cls_mu_shi": [
        (30, "圣光惩戒", 1.0),
        (60, "骨噬诅咒", 1.0),
        (90, "骸骨洪流", 1.0),
        (999, "永恒安魂", 1.0),
    ],
    "cls_ci_ke": [
        (30, "刺击", 1.0),
        (60, "链舞", 1.0),
        (90, "收割", 1.0),
        (999, "万毒噬心", 1.0),
    ],
    "cls_wu_seng": [
        (30, "直拳", 1.0),
        (60, "碎颅势", 1.0),   # v162: 原崩拳需Lv50，P3(Lv45-59)用不了 → 改Lv44碎颅势
        (90, "气力裂空", 1.0),
        (999, "撼岳·终焉", 1.0),
    ],
    "cls_shi_ren": [
        (30, "音刃", 1.0),
        (60, "哀歌", 1.0),
        (90, "破晓长歌", 1.0),
        (999, "天籁", 1.0),
    ],
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
# 阶段成长率约束（计划 §一.5.3，防数值失控；v161 可持续 DPS 口径更新）：
#   v161 新口径（单发×频率+DOT）下，P2→P3 是转职质变（基础技能→T1 + 蓝装→紫装 + 装备 spd 提频），
#   引擎实测 4~7×（法师 4.2 / 刺客 5.3 / 战士 7.0）；模型口径（含 DOT 稳态假设）略高估到 8~9×。
#   上限放宽到 9.0 容纳模型高估；真实引擎成长 4~7× 仍健康（转职质变合理）。
#   同档位阶段（P3→P4、P4→P5）纯等级成长仍要求 ≥1.25×（防卡死）。
STAGE_GROWTH_MIN = 1.25   # 阶段增幅下限（防断档：低于此 = 某阶段成长卡死）
STAGE_GROWTH_MAX = 9.0    # 阶段增幅上限（防爆炸；v161 新口径转职质变 4~7×，模型略高估到 9）
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