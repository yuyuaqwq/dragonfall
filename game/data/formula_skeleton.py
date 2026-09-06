# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - formula_skeleton.py（P2F-1：2026-09-07 鱼鱼拍板公式骨架参数化）

底层公式骨架数值（F2/F3/F4/F7/F9/F15/F16 纯参数批）。默认值 = 重构前引擎字面量，
行为零变化；公式结构（分支/截断序/随机）仍由 core/engine 执行器承担。

改数值 = 改这里（数值进 data）；公式结构见 REFACTOR_P2F_formula_skeleton.md §3/§4。
对齐北极星三层：数值在 data / 执行器在 core / 编排在 battle。

消费端：
- exp_fallback    → core/stats.py exp_to_next 超出 100 级兜底
- monster_exp     → core/stats.py monster_exp（hp 补偿幂 + 战斗拉长补偿）
- monster_gold    → core/stats.py monster_gold
- skill_growth    → engine.py skill_power_mult / skill_cond_mult / skill_mech_val /
                     skill_buff_turns / skill_lifesteal_pct（成长默认值，调用方可传参覆盖）
- skill_learn_cost→ engine.py skill_learn_cost（技能点定价）
- prof_exp_need   → core/constants.py prof_exp_need（副业经验二次曲线，函数本体仍在 constants）
"""
FORMULA_SKELETON = {
    # ---- F2 exp_to_next 超出 100 级兜底（core/stats.py:253）----
    # 表内等级 1..100 查 _EXP_TABLE；>100 走 int(base * lv**power + add) 防越级不崩。
    "exp_fallback": {"base": 60, "power": 1.45, "add": 50},

    # ---- F3 怪物经验（core/stats.py:255-261）----
    # exp = int(int(base*(1+lv*linear_slope)) * combat_len_mult * hp_stage_mult(lv)**hp_pow)
    # v56.2：怪 hp 变肉经验补偿（×hp_mult^0.7）；v131：战斗拉长补偿 ×1.5
    "monster_exp": {"linear_slope": 0.9, "combat_len_mult": 1.5, "hp_pow": 0.7},

    # ---- F4 怪物金币（core/stats.py:264-269）----
    # gold = int(int(base*(1+lv*linear_slope)) * combat_len_mult * hp_stage_mult(lv)**hp_pow)
    "monster_gold": {"linear_slope": 0.6, "combat_len_mult": 1.3, "hp_pow": 0.5},

    # ---- F7/F9 技能成长骨架（engine.py:881-946）----
    # p/c/m/l 成长斜率已 data（game/data/skill_up.py SKILL_UP）；这里是未配置时的引擎默认值。
    # v180：p 无默认兜底（没配 p=无成长，恒 1.0）——仅 /100 系数参数化。
    "skill_growth": {
        "power_per_lv_divisor": 100,   # F7 skill_power_mult: 1 + (p/divisor)*(lv-1)
        "cond_default": 0.05,          # F9 skill_cond_mult 未配 c 默认每级 +0.05
        "mech_default_div": 2,         # F9 skill_mech_val 未配 m 默认每 2 级 +1 层（m≤0 亦按此兜底）
        "buff_turns_base": 3,          # F9 skill_buff_turns 默认 base 3 刻（info 配 buff_turns 覆盖）
        "buff_turns_per_lv": 1,        # F9 skill_buff_turns 每级 +1 刻
        "lifesteal_default": 0.20,     # F9 skill_lifesteal_pct 未配 lifesteal 字段默认 20%
        "lifesteal_per_lv_divisor": 100,  # F9 l 配值单位 %：l/100 每级（skill_up 表内 l=2 → +2%/级）
    },

    # ---- F15 技能点定价（engine.py:741-744）----
    # cost = need_lv // divisor + base
    "skill_learn_cost": {"divisor": 6, "base": 2},

    # ---- F16 副业经验曲线（core/constants.py:192-203）----
    # need(lv) = a*lv² + b*lv（v105 平衡曲线，累计 2100 满级；函数本体仍在 constants.py）
    "prof_exp_need": {"a": 5, "b": 15},
}
