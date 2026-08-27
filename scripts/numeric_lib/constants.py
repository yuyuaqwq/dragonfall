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
    "cls_zhan_shi": [("破甲斩", 1.0), ("猛击", 1.0)],   # 破甲斩无视防御+防御debuff → 猛击打半防
    "cls_you_xia": [("瞄准射击", 1.0)],                 # 140% 精力 10/发，每回合回 30 可永续
    "cls_fa_shi": [("元素弹幕", 1.0)],                  # 100%×2 = 200% 魔法
    "cls_mu_shi": [("惩戒", 1.0)],                      # 120% 圣光魔法
    "cls_ci_ke": [("双刃乱舞", 1.0)],                   # 90%×2，HP>70% 时 +30%（加权）
    "cls_wu_seng": [("碎骨拳", 1.0)],                   # 150% 无视防御（3 气/每 3 行动 1 发，加权）
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

# 玩家档位预设（--loadout / gear_loadout；quality 直接对 QUALITY 表 white/green/blue/purple/orange）
LOADOUTS = {
    "naked":       {"quality": "white", "enhance": 0, "players": 1, "label": "裸装"},
    "solo_low":    {"quality": "blue",  "enhance": 0, "players": 1, "label": "单刷 蓝+0"},
    "solo_mid":    {"quality": "blue",  "enhance": 5, "players": 1, "label": "单刷 蓝+5"},
    "team_mid":    {"quality": "blue",  "enhance": 5, "players": 4, "label": "4人 蓝+5"},
    "team_purple9": {"quality": "purple", "enhance": 9, "players": 4, "label": "4人 紫+9"},
    "team_orange9": {"quality": "orange", "enhance": 9, "players": 4, "label": "4人 橙+9"},
    "legacy":      {"quality": "blue",  "enhance": 0, "players": 1, "label": "旧模型(对照)"},
}