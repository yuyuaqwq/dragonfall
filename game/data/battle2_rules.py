# -*- coding: utf-8 -*-
"""游戏层战斗规则配置（battle2 引擎的注入表）——换这套 = 新游戏。

battle2 引擎不认识这些名词，只通过 config 挂载点查表折算。
引擎代码零改动；调数值/加状态/改规则全在这里。

挂载方式（游戏启动时）：
    from game.battle2 import config
    config.load_game_rules(game.data.battle2_rules)
"""
from __future__ import annotations

# ============================================================
# EFFECT_RULES: 效果规则表（V 系列统一——cap/stat_scale/period/consume/cleanse 全声明）
# state key → 影响规则（cap/stat_scale/dot/on/threshold）
# ============================================================
EFFECT_RULES: dict = {
    # ============ 通用叠层/资源（玩家侧，每层持有即生效） ============
    "zhan_yi": {
        "cap": 10,
        "stat_scale": {"atk": 0.04},          # 每层攻击 +4%
        "on_threshold": {10: {"form": "fury"}},  # 满 10 进狂暴（上层消费）
    },
    "lian_duan": {
        "cap": 10,
    },
    "rage": {
        "cap": 10,
        "stat_scale": {"dmg_mult": 0.12},     # 每层伤害 +12%
    },
    "chi": {
        "cap": 10,
    },
    "arcane": {
        "cap": 10,
    },
    "shield": {
        "cap": 10,
        "stat_scale": {"reduce": 0.03},       # 每层减伤
    },
    # ============ 对敌标记（on=target，谁打都吃） ============
    "hunt_mark": {
        "cap": 3,
        "on": "target",
        "debuff_scale": {"dmg_taken": 0.08},  # 每层承伤 +8%
    },
    "soul_mark": {
        "cap": 3,
        "on": "target",
        "debuff_scale": {"dmg_taken": 0.06},  # 每层承伤 +6%
    },
    # ============ 持续伤害 DOT（on=target） ============
    "burn": {
        "cap": 5,
        "on": "target",
        "dot": {"pct_max_hp": 0.03},          # 每层每刻掉 3% 生命
    },
    "bleed": {
        "cap": 10,
        "on": "target",
        "dot": {"type": "flat", "per_layer": 0},
    },
    "poison": {
        "cap": 5,
        "on": "target",
        "dot": {"pct_max_hp": 0.02},
    },
    "corros": {
        "cap": 5,
        "on": "target",
        "dot": {"pct_max_hp": 0.02, "dmg_type": "true"},  # 真伤 DOT
    },
    # ============ 元素印记（on=target） ============
    "fire_mark": {
        "cap": 5,
        "on": "target",
    },
    "ice_mark": {
        "cap": 5,
        "on": "target",
    },
    "thunder_mark": {
        "cap": 5,
        "on": "target",
    },
    # ============ 装备特效叠层（N9：武器特效 proc_stack 纯叠层 key） ============
    "wind_mark": {
        "cap": 4,
        "stat_scale": {"spd": 0.02},          # 每层速度 +2%（风痕，命中叠层）
    },
    # ============ 装备特效 DOT（N9：proc_dot 武器特效；turns = 限时跳数） ============
    "blaze": {
        "cap": 3,
        "on": "target",
        "dot": {"pct_max_hp": 0.015, "pct_boss": 0.01, "turns": 3},   # 裂伤：1.5%(boss 1%)/跳 3 跳
    },
    "ember": {
        "cap": 3,
        "on": "target",
        "dot": {"pct_max_hp": 0.015, "pct_boss": 0.01, "turns": 3},   # 烬燃：1.5%(boss 1%)/跳 3 跳
    },
    "blood_trace": {
        "cap": 1,
        "on": "target",
        "dot": {"pct_cur_hp": 0.02, "pct_cur_boss": 0.015, "turns": 4},  # 败血：当前生命 2%(boss 1.5%)/跳 4 跳
    },
    # ============ 禁疗（N9 收编：旧 buffs int 直写 → state 层×10% cap50%） ============
    "heal_down": {
        "cap": 5,
        "on": "target",
    },
    # ============ 濒死保护（N9.12：致死时保底不死亡；landing 消费） ============
    # 层数 = 剩余保命次数；触发 = 伤害会致死时 → hp 拉到 guard_hp_pct 并回 heal_pct
    "death_guard": {
        "cap": 1,
        "guard_hp_pct": 0.10,   # 触发后保底到 10% 最大生命（undying_will 语义）
        "heal_pct": 0.10,       # 触发额外回 10% 最大生命
    },
    # ============ 装备叠层放大器（N9.14：proc_stack 生产段叠层 + dmg_calc 消费） ============
    "rune_amp": {"cap": 5},                       # 铭文：每层下一技能 +2%（dmg_calc 消费清层）
    "eternal_codex": {"cap": 8},                  # 永恒契约：每层技能伤 +1.5%（不清层）
    "time_staff": {                                # 岁月流转：每层 atk+1.5%（面板常驻）
        "cap": 10,
        "stat_scale": {"atk": 0.015},
    },
    "thunder_weave": {                             # 雷纹：每层 spd+2%/atk+1%（面板常驻）
        "cap": 5,
        "stat_scale": {"spd": 0.02, "atk": 0.01},
    },
    "sage_amp": {"cap": 2},                        # 秘典充能：计数 need 2 → 下一技能 ×1.25
    # ============ 敌方减速叠层（N9A：randuin/ice_vein，act_done 敌行动叠层） ============
    # 旧语义：敌行动 +1 层（cap 3），_spd_down_pct = spd_down_pct×n 乘算减速
    # （cap 0.5 折算端；3×0.06=0.18 / 3×0.08=0.24 均不触 cap → stat_scale 负值精确等价）
    "randuin_weary": {
        "cap": 3,
        "stat_scale": {"spd": -0.06},              # 兰顿倦意：每层敌速 -6%
    },
    "ice_vein": {
        "cap": 3,
        "stat_scale": {"spd": -0.08},              # 冰脉寒流：每层敌速 -8%
    },
    # ============ affix 词条 DOT（N9.7b：命中流血词条） ============
    # 旧语义（affix bleed）：20% 使目标流血，每刻 5% 生命，3 刻（叠 3 层 cap）
    # → state 层 dot 声明（on=target，pct_max_hp 每层，turns 限时 3 跳清层）
    "affix_bleed": {
        "cap": 3,
        "on": "target",
        "dot": {"pct_max_hp": 0.05, "pct_boss": 0.02, "turns": 3},
    },
    # ============ 静态面板增益（V5 数值入表：buff key → panel 声明） ============
    # 原 EFFECT_ACTIONS 动作参数 stat/op/mult → EFFECT_RULES[key].panel；
    # EFFECT_ACTIONS 瘦身为 {"action": "apply", "key": X}（数值查表，apply 快照进条目）。
    # cap=1 非叠层；同 key 数值唯一（已核），多名词映射共享同一 panel。
    "atk_up":          {"cap": 1, "panel": {"stat": "atk",  "op": "mul", "mult": 1.30}},
    "atk_up_big":      {"cap": 1, "panel": {"stat": "atk",  "op": "mul", "mult": 1.40}},
    "atk_up_small":    {"cap": 1, "panel": {"stat": "atk",  "op": "mul", "mult": 1.20}},
    "def_up":          {"cap": 1, "panel": {"stat": "def",  "op": "mul", "mult": 1.45}},
    "spd_up":          {"cap": 1, "panel": {"stat": "spd",  "op": "mul", "mult": 1.40}},
    "spd_up_small":    {"cap": 1, "panel": {"stat": "spd",  "op": "mul", "mult": 1.20}},
    "crit_up":         {"cap": 1, "panel": {"stat": "crit", "op": "add", "mult": 0.20}},
    "crit_up_big":     {"cap": 1, "panel": {"stat": "crit", "op": "add", "mult": 0.30}},
    "crit_up_small":   {"cap": 1, "panel": {"stat": "crit", "op": "add", "mult": 0.15}},
    "dodge_up":        {"cap": 1, "panel": {"stat": "dodge", "op": "add", "mult": 0.10}},
    "matk_up":         {"cap": 1, "panel": {"stat": "matk", "op": "mul", "mult": 1.50}},
    "matk_up_pot":     {"cap": 1, "panel": {"stat": "matk", "op": "mul", "mult": 1.30}},
    "matk_up_strong":  {"cap": 1, "panel": {"stat": "matk", "op": "mul", "mult": 1.80}},
    "food_atk_up":     {"cap": 1, "panel": {"stat": "atk",  "op": "mul", "mult": 1.10}},
    "food_def_up":     {"cap": 1, "panel": {"stat": "def",  "op": "mul", "mult": 1.15}},
    "food_spd_up":     {"cap": 1, "panel": {"stat": "spd",  "op": "mul", "mult": 1.12}},
    "food_spd_up_small": {"cap": 1, "panel": {"stat": "spd", "op": "mul", "mult": 1.10}},
    "food_matk_up":    {"cap": 1, "panel": {"stat": "matk", "op": "mul", "mult": 1.10}},
    "food_crit_up":    {"cap": 1, "panel": {"stat": "crit", "op": "add", "mult": 0.08}},
}

# ============================================================
# 名词效果 → 引擎动词动作序列
# （技能数据/怪物模板里的 effect/mech 名词，经这里翻译成引擎动词）
# ============================================================
EFFECT_ACTIONS: dict = {
    # ---- 控制类（写 target.buffs[tag]=刻数）----
    # mode=skip 整跳（行动级消费：轮到行动跳过+清）；mode=no_skill 禁技（技能转普攻）
    "stun":      [{"action": "apply", "key": "stun", "on": "target", "turns": 1, "mode": "skip"}],
    "freeze":    [{"action": "apply", "key": "freeze", "on": "target", "turns": 1, "mode": "skip"}],
    "sleep":     [{"action": "apply", "key": "sleep", "on": "target", "turns": 1, "mode": "skip", "wake_on_hit": True}],
    "silence":   [{"action": "apply", "key": "silence", "on": "target", "turns": 2, "mode": "no_skill"}],
    "slow":      [{"action": "apply", "key": "spd_down", "on": "target", "turns": 2, "mode": "skip"}],
    "spd_down":  [{"action": "apply", "key": "spd_down", "on": "target", "turns": 2, "mode": "skip"}],
    # ---- 属性增益（写 caster.buffs[key]，数值=动作参数 stat/op/mult 快照进条目）----
    # 数值参考旧 battle_config.BUFF_MULT（N7.1 全新填：desc/策划案为准，旧表对照）：
    #   atk_up=×1.30 / matk_up=×1.50 / matk_up_strong=×1.80 / def_up=×1.45 /
    #   spd_up=×1.40 / crit_up=+0.20 / magic_resist=+0.15 / mon_atk_down=×0.70
    "atk_up":    [{"action": "apply", "key": "atk_up",    "stat": "atk",  "op": "mul", "mult": 1.30}],
    "dodge_buff":  [{"action": "apply", "key": "dodge_up", "stat": "dodge", "op": "add", "mult": 0.10}],
    "spd_buff":    [{"action": "apply", "key": "spd_up",   "stat": "spd",  "op": "mul", "mult": 1.40}],
    "crit_hit_buff": [{"action": "apply", "key": "crit_up", "stat": "crit", "op": "add", "mult": 0.20}],
    "cc_immune":    [{"action": "apply", "key": "cc_immune"}],   # 无面板折算（纯免疫状态）
    # 团队/全员增益 → 自身有效键（旧 team_keys 同语义）
    "atk_all":   [{"action": "apply", "key": "atk_up",       "stat": "atk",  "op": "mul", "mult": 1.30}],
    "def_all":   [{"action": "apply", "key": "def_up",       "stat": "def",  "op": "mul", "mult": 1.45}],
    "matk_all":  [{"action": "apply", "key": "matk_up_strong", "stat": "matk", "op": "mul", "mult": 1.80}],
    "crit_all":  [{"action": "apply", "key": "crit_up",      "stat": "crit", "op": "add", "mult": 0.20}],
    "spd_all":   [{"action": "apply", "key": "spd_up",       "stat": "spd",  "op": "mul", "mult": 1.40}],
    "atk_matk_all": [{"action": "apply", "key": "atk_up",    "stat": "atk",  "op": "mul", "mult": 1.30},
                     {"action": "apply", "key": "matk_up",   "stat": "matk", "op": "mul", "mult": 1.50}],
    # ---- N7.5b 药水/食物纯属性别名（items.py effect → BUFF_MULT 数值；special:* 类 N8 事件）----
    "buff_atk":    [{"action": "apply", "key": "atk_up",       "stat": "atk",  "op": "mul", "mult": 1.30}],
    "buff_atk_big":[{"action": "apply", "key": "atk_up_big",   "stat": "atk",  "op": "mul", "mult": 1.40}],
    "buff_atk_small":[{"action": "apply", "key": "atk_up_small","stat": "atk", "op": "mul", "mult": 1.20}],
    "buff_atk_food":[{"action": "apply", "key": "food_atk_up", "stat": "atk",  "op": "mul", "mult": 1.10}],
    "buff_def":    [{"action": "apply", "key": "def_up",       "stat": "def",  "op": "mul", "mult": 1.45}],
    "buff_def_food":[{"action": "apply", "key": "food_def_up", "stat": "def",  "op": "mul", "mult": 1.15}],
    "buff_spd":    [{"action": "apply", "key": "spd_up",       "stat": "spd",  "op": "mul", "mult": 1.40}],
    "buff_spd_small":[{"action": "apply", "key": "spd_up_small","stat": "spd", "op": "mul", "mult": 1.20}],
    "buff_spd_food":[{"action": "apply", "key": "food_spd_up", "stat": "spd",  "op": "mul", "mult": 1.12}],
    "buff_crit":   [{"action": "apply", "key": "crit_up",      "stat": "crit", "op": "add", "mult": 0.20}],
    "buff_crit_small":[{"action": "apply", "key": "crit_up_small","stat": "crit","op": "add","mult": 0.15}],
    "buff_crit_big":[{"action": "apply", "key": "crit_up_big", "stat": "crit", "op": "add", "mult": 0.30}],
    "buff_crit_food":[{"action": "apply", "key": "food_crit_up","stat": "crit","op": "add","mult": 0.08}],
    "buff_matk":   [{"action": "apply", "key": "matk_up_pot",  "stat": "matk", "op": "mul", "mult": 1.30}],
    "buff_matk_strong":[{"action": "apply", "key": "matk_up_strong","stat": "matk","op": "mul","mult": 1.80}],
    "buff_matk_food":[{"action": "apply", "key": "food_matk_up","stat": "matk", "op": "mul", "mult": 1.10}],
    "food_spd_up_small":[{"action": "apply", "key": "food_spd_up_small","stat": "spd","op": "mul","mult": 1.10}],
    # ---- 一次性出手消费（hit 子键：出手增伤 / 必暴；效果参数可被调用方 effect_data 覆盖）----
    "next_atk_up":   [{"action": "apply", "key": "next_atk_up",   "hit": {"dmg_mult": 1.50}}],
    "buff_phys_next":[{"action": "apply", "key": "buff_phys_next","hit": {"dmg_mult": 1.40}}],
    "stealth":       [{"action": "apply", "key": "stealth",       "hit": {"guaranteed_crit": True}}],
    # ---- N7.5a 战斗核心：治疗/叠层置值/打断（怪 heal_self/heal_pct、on_interrupt 族）----
    # vulnerable 易伤：完整语义（写 target 承伤乘区 + 持续刻）属 N8 事件总线接入，
    # 不在词表假映射——landing 已支持 _dmg_taken_mult 字段（上层直写即生效）
    "heal_self":   [{"action": "heal", "on": "caster"}],
    "heal_pct":    [{"action": "heal", "on": "caster"}],
    "regen":       [{"action": "heal", "on": "caster"}],     # 持续回复族（regen 单发）
    "stacks_set":  [{"action": "apply", "op": "set", "on": "target"}],
    "interrupt":   [{"action": "interrupt"}],
    # ---- 减伤（value 型 buff：mech_val 折算百分比 45→0.45）----
    "reduce":    [{"action": "apply", "key": "reduce", "pct_from_mech_val": True}],
    # ---- 护盾 ----
    "shield_self": [{"action": "shield", "halve": False}],
    "shield":      [{"action": "shield", "halve": True}],
    # ---- 净化 ----
    "cleanse":     [{"action": "cleanse"}],
    "cleanse_all": [{"action": "cleanse_all"}],
}

# 净化应清的控制键（buff 容器里的控制 tag）
CLEANSE_TAGS = ["stun", "silence", "freeze", "spd_down", "reduce"]


