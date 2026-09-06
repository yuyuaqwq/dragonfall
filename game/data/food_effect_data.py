# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - food_effect_data.py（v180F 清2b 食物效果数值权威表）

食物效果（food_effect，本场战斗生效）的数值统一收口到本表——此前 17 个 handler
数值硬编码在 game/core/food_effects.py 及 battle.py（shield/execute/precise），
违反数据驱动铁律。handler 一律读本表，调数值只改这里。

字段说明（按效果语义取用）：
- chance:   触发概率（0-1）
- pct:      百分比数值（0.01=1%）
- mult:     伤害倍率类（execute/precise 的乘区，1.30=+30%）
- turns:    持续刻数
- stacks/max_n: 叠层相关（bleed/dragon_tongue）
- slow_turns: 减速刻数（element_ice/static）
- value:    其他数值（护盾百分比等）
- label:    效果播报标签（对齐 FOOD_EFFECT_NAMES）

v180F 核对（2026-09-07）：表值与 items.py 食物 desc 逐一核对一致（同效果同数值
设计——regen 高级食物战斗外恢复更强但战斗内回春同为 1%）。改动数值须同步 desc。
"""
FOOD_EFFECT_PARAMS = {
    # ---- 攻击命中（FOOD_HIT_EFFECTS） ----
    "lifesteal":    {"pct": 0.08, "label": "吸血"},               # 蛇羹：攻击回复伤害 8%
    "bleed":        {"chance": 0.20, "stacks": 3, "max_n": 3},    # 烬火辣椒：20% 流血 3 层
    "armor_break":  {"chance": 0.25, "pct": 0.15, "turns": 2},    # 蘑菇汤：25% 破甲 15% 2刻
    "combo":        {"chance": 0.15, "pct": 0.50},                # 鹰蛋：15% 追加 50%
    "dragon_tongue": {"max_n": 5, "pct": 0.02},                   # 龙蛋煎饼：每层 +2% 上限5
    "element_fire": {"pct": 0.05},                                # 灰烬烤饼：5% 火附加
    "element_ice":  {"pct": 0.05, "slow_turns": 2},               # 冰霜浆果：5% 冰附加+减速2刻
    "pierce":       {"chance": 0.20, "atk_pct": 0.60},            # 雪狼肉排：20% 无视防御 60% 攻击
    "charge":       {"chance": 0.10, "pct": 0.50},                # 皇家烤肉/龙血火锅：10% 追加 50%
    "static":       {"chance": 0.20, "turns": 2},                 # 雷雨藤烤串：20% 减速 2刻
    # ---- 受击（FOOD_TAKEN_EFFECTS） ----
    "counter":      {"chance": 0.20, "atk_pct": 0.60},            # 狼肉干：20% 反击 60%
    "thorns":       {"chance": 0.10, "pct": 0.30},                # 鹿奶干酪：10% 反弹 30%
    "aurora_guard": {"pct": 0.15},                                # 极光花蜜：受击 -15%
    # ---- 刻开始（FOOD_TURN_START_EFFECTS） ----
    "regen":        {"pct": 0.01},                                # 树蜜糖/夜雾菇：每刻 1% 生命
    "meditate":     {"pct": 0.01},                                # 月光饼/月光草茶：每刻 1% 魔力
    "dawn_crown":   {"pct": 0.02},                                # 御膳汤：每刻 2% 生命
    # ---- 伤害倍率类（battle._affix_dmg_mult 消费） ----
    "execute":      {"hp_ratio": 0.30, "mult": 1.30},             # 海盗炖鱼：<30% +30%
    "precise":      {"mult": 1.10},                               # 海鲜浓汤：本场 +10%
    # ---- 护盾类（battle._do_use_item 特判消费） ----
    "shield":       {"pct": 0.10, "turns": 3},                    # 圣餐面包：10% 生命护盾 3刻
}
