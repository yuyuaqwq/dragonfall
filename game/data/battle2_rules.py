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
    # v181.M-R2b：name 展示名单源化（源 core_resources.py v130.2 旧表，文件本体随 M-R2c 退役删除——
    # rage 怒气/faith 信仰值/
    # cp 连击点/element 元素亲和/chi 气 对照旧表 name；zhan_yi 战意/lian_duan 连段/arcane 奥术
    # 对齐 commands/combat RESOURCE_STACK_CN v181.M-R3 现网展示名）。cap 即旧 max（同值）。
    "zhan_yi": {
        "name": "战意",
        "cap": 10,
        "stat_scale": {"atk": 0.04},          # 每层攻击 +4%
        "on_threshold": {10: {"form": "fury"}},  # 满 10 进狂暴（上层消费）
    },
    # v153 战士狂暴态（CLASS_MECHANICS_v153 战士血怒线）：血祭（zhan_yi_fury 兑现）
    # 花 4 战意进入 → effects[fury] 1 层 = 狂暴中。攻击 +20%（stat_scale）；吸血 25% /
    # 普攻双段 2×70% / 维持衰减每刻 -0.6 / 跌破 4 强退 = v153 细节，吸血与衰减需
    # lifesteal stat_scale / time tick 装配点——标注缺口待补（引擎 stat_scale 折算
    # 现支持 atk 面板乘算；普攻双段动引擎 basic 逻辑，不糙做）。
    "fury": {
        "name": "狂暴",
        "cap": 1,
        "stat_scale": {"atk": 0.2},           # 狂暴中攻击 +20%（v153）
    },
    "lian_duan": {
        "name": "连段",
        "cap": 10,
    },
    "rage": {
        "name": "怒气",
        "cap": 10,
        "stat_scale": {"dmg_mult": 0.12},     # 每层伤害 +12%
        # ⚠️ v181.M-R2d 核实：技能域渠道死 key——现网 skills.py 全表零 mech/res_gain/res_cost
        # rage（v151 后战士主资源=zhan_yi 战意，rage 满 10 狂暴/背水随 battle.py 形态机退役、
        # battle2 无 dual_form 消费端）；若事件渠道误喂，满层 +120% dmg 无人消费 = 数值崩坏。
        # → 职业渠道不接（affix 词条域 war_spirit/blood_bath/boiling_blood 仍由 R4
        #   we_affix_res_gain 通道喂，勿在本域重建）。待清死数据（详见
        #   docs/REFACTOR_v181_CLASS_MECH_ASSEMBLY.md『M-R2d 渠道装配设计』§3）。
    },
    # 龙语印记（dragon_tongue：龙蛋煎饼料理 / 龙语圣剑传奇词条）——每层伤害 +2%，
    # 攻击命中叠层（cap 5）。stat_scale.dmg_mult 通用通道（同 rage），stats 折算
    # _state_dmg_mult → actions 伤害乘区消费；命中叠层由装配层/翻译器声明。
    "dragon_mark": {
        "cap": 5,
        "stat_scale": {"dmg_mult": 0.02},     # 每层伤害 +2%（上限 5 层 = +10%）
    },
    "chi": {
        "name": "气",
        "cap": 10,
        # ⚠️ v181.M-R2d 核实：技能域渠道死 key——现网技能零 mech/res_gain/res_cost chi
        # （v151 武僧=破绽条 shaken + 磐核体系，v130「3 气崩拳/10 气破岳拳」随技能重做消失；
        # guard_core_burst 磐核攒端 = v153 机制缺口见蓝图 §7 R1d）。
        # → 职业渠道不接（affix 词条域 rock_rest/opening_stance 仍由 R4 通道喂）。待清死数据。
    },
    "arcane": {
        "name": "奥术",
        "cap": 10,
    },
    # v181.M-melody：诗人旋律光环（v153 设计 docs/CLASS_MECHANICS_v153.md『七、吟游诗人』）
    # 驻留旋律 = 全队光环，效果随强度：效果% = melody_pct(技能 desc 基础) × (1+0.25×(强度-1))
    # （1 层=desc 值，5 层=×2=+100%；公式注释标待 v153 重做确认）。
    # 实现：stat_scale per=0.01（每层 1%），广播时写等效层数=目标%（float 层支持——
    # 目标%不整时小数层，stats 折算 n×0.01 得精确效果）。条目只作折算声明，由装配层
    # class_melody_act 广播写全员 effects（施法者 effects["melody_state"] 存状态）。
    "melody_atk": {
        "stat_scale": {"atk": 0.01},        # 每层 +1% atk（层数=目标%）
    },
    "melody_atk_matk": {
        "stat_scale": {"atk": 0.01, "matk": 0.01},
    },
    "melody_spd": {
        "stat_scale": {"spd": 0.01},
    },
    "melody_def": {
        "stat_scale": {"reduce": 0.01},     # 每层 +1% 减伤（reduce 承伤乘区，cap 0.9）
    },
    "melody_finale_atk": {
        "stat_scale": {"atk": 0.01},        # 终章爆发 buff（expire 8-10 刻后消散，可叠加驻留）
    },
    "melody_finale_crit": {
        "stat_scale": {"crit": 0.01},
    },
    # R4（N9.7e affix 资源词条 gain clamp 声明）：energy/faith/cp/element 是
    # affix res+gain 词条（暴击蓄能/圣辉回响/暴击回点/充能汲引等）的资源容器 key，
    # cap 源 = core_resources legacy max（文件本体 R2c 退役；精力 100/信仰 10/连击点 5/元素亲和 5）。
    # 纯 cap 声明（无 stat_scale/period/consume → 引擎惰性条目，只 clamp 不折算）；
    # 渠道喂养/单源化属 R2 批次，词条装配 R4 先落地。
    "energy": {
        "cap": 100,
        # v181.M-R2（游侠专注流量制，源 core_resources.cls_you_xia v176，文件 R2c 退役）：
        # - start_full：开局满额（装配层初始化 effects[energy] = cap）
        # - period dir=gain：每刻自然回 18（schedule 时间驱动，静默回复 clamp cap）
        "name": "精力", "start_full": True,
        "start_classes": ["cls_you_xia"],   # 开局满额归属职业（装配层按 class 判）
        "period": {"dir": "gain", "interval": 1.0, "amount": 18},
    },
    "faith": {
        "name": "信仰值",
        "cap": 10,
        # v181.M-R2d 攒取渠道（源 core_resources.cls_mu_shi on_heal:2/on_hit:1，文件 R2c 退役）：
        #   heal_cast 治疗施放 +2 / taken 受击 +1——装配层 class_mech_proc 按 start_classes
        #   归属挂事件钩子（clamp cap；圣光/死灵两线共用 cls_mu_shi）。攻击系攒信念 = v130
        #   per-skill res_gain 数据语义，v153 skills 重做未回填 → 缺口见
        #   docs/REFACTOR_v181_CLASS_MECH_ASSEMBLY.md『M-R2d 渠道装配设计』§4。
        "start_classes": ["cls_mu_shi"],
        "channels": {"heal_cast": 2, "taken": 1},
        # v181.M-R2e 负载制闭环（B2/B3，方案 docs/REFACTOR_v181_M_R2e_engine_ext_plan.md）：
        # - load_tiers：四档负载（v130 设计逐字，desc 参考 JOB_GUIDE『档位 0-3/4-7/8-9/10
        #   (过载)』）——装配层 class_faith_load_tier 按 heal_calc 事件查自身层落档，
        #   专注 ×1.25 / 透支 ×1.5 / 过载档 heal_mult 1.0（过载由 threshold 钩子处理）
        # - overload_heal_pct：叠到满 cap 当次过载（class_faith_overload）清零 +
        #   我方全员回复 max_hp×0.015（v130 旧值；圣化被动 heal_up 属旧被动域未接）
        # - period dir=gain amount=-0.7：每刻 -0.7 慢衰减（B3 effects float 通用层——
        #   schedule gain 分支支持负 amount，clamp 下限 0；~14 刻从满归 3 清醒档）
        "load_tiers": [
            {"max": 3, "heal_mult": 1.00, "label": "清醒"},
            {"max": 7, "heal_mult": 1.25, "label": "专注"},
            {"max": 9, "heal_mult": 1.50, "label": "透支"},
            {"max": 10, "heal_mult": 1.00, "overload": True},
        ],
        "overload_heal_pct": 0.015,
        "period": {"dir": "gain", "interval": 1.0, "amount": -0.7},
    },
    "cp": {
        "name": "连击点",
        "cap": 5,
        # ⚠️ v181.M-R2d 核实：技能域渠道死 key——现网技能零 mech/res_gain/res_cost cp
        # （v151 刺客主资源=lian_duan 连段，技能 mech 命中攒段已通，finisher 兑现 R1a 已装）。
        # → 职业渠道不接（affix 词条域 crit_return 仍由 R4 通道喂）。待清死数据。
    },
    "element": {
        "name": "元素亲和",
        "cap": 5,
        # ⚠️ v181.M-R2d 核实：技能域渠道死 key——现网技能零使用（v151 印记体系
        # fire/ice/thunder_mark mech 取代 v139 element 充能条，BRANCH 元素法师挂印不挂亲和）。
        # → 职业渠道不接（affix 词条域 arcana_flux 仍由 R4 通道喂）。待清死数据。
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
    # v181.M-R1c：牧师/死灵 骨噬诅咒（v153）——全队对其伤害 +20%（8 刻）。
    # desc 限时 8 刻 = 叠层到期机制（引擎 schedule 层）待扩展，先按叠层生效；
    # curse_refresh（刷新时长）依赖到期机制，同步记缺口。
    "curse": {
        "cap": 1,
        "on": "target",
        "debuff_scale": {"dmg_taken": 0.20},
    },
    # ============ 持续伤害 DOT（on=target；V5：dot → period 统一声明） ============
    # period = {dir, interval, 数值字段}：schedule 按 dir 分流结算（damage/heal/mana）。
    # damage 方向 pct 字段 = 每层每跳（×stacks）；turns 限跳数（0=无限）；dmg_type=true=真伤
    "burn": {
        "cap": 5,
        "on": "target",
        "period": {"dir": "damage", "interval": 1.0, "pct_max_hp": 0.03},   # 每层每刻掉 3% 生命
    },
    "bleed": {
        "cap": 10,
        "on": "target",
        "period": {"dir": "damage", "interval": 1.0, "type": "flat", "per_layer": 0},
    },
    "poison": {
        "cap": 5,
        "on": "target",
        "period": {"dir": "damage", "interval": 1.0, "pct_max_hp": 0.02},
    },
    "corros": {
        "cap": 5,
        "on": "target",
        "period": {"dir": "damage", "interval": 1.0, "pct_max_hp": 0.02, "dmg_type": "true"},  # 真伤 DOT
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
        "period": {"dir": "damage", "interval": 1.0, "pct_max_hp": 0.015, "pct_boss": 0.01, "turns": 3},   # 裂伤：1.5%(boss 1%)/跳 3 跳
    },
    "ember": {
        "cap": 3,
        "on": "target",
        "period": {"dir": "damage", "interval": 1.0, "pct_max_hp": 0.015, "pct_boss": 0.01, "turns": 3},   # 烬燃：1.5%(boss 1%)/跳 3 跳
    },
    "blood_trace": {
        "cap": 1,
        "on": "target",
        "period": {"dir": "damage", "interval": 1.0, "pct_cur_hp": 0.02, "pct_cur_boss": 0.015, "turns": 4},  # 败血：当前生命 2%(boss 1.5%)/跳 4 跳
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
    # → state 层 period 声明（on=target，pct_max_hp 每层，turns 限时 3 跳清层）
    "affix_bleed": {
        "cap": 3,
        "on": "target",
        "period": {"dir": "damage", "interval": 1.0, "pct_max_hp": 0.05, "pct_boss": 0.02, "turns": 3},
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
    # ============ 控制 tag（V5② 表声明：consume.mode 语义 + 净化标记；技能 mech 分派
    # 靠 effects._mech_to_effect「无 consume/panel 才走叠层」判据防劫持——
    # 纯控制 mech（stun 等）走 EFFECT_ACTIONS 名词路径，与入表前行为一致） ============
    # 注意：sleep 不可净化（受击醒），cleanse 不标——对齐原 CLEANSE_TAGS（无 sleep）
    "stun":     {"cap": 1, "consume": {"mode": "skip"}, "tag": "stun", "cleanse": True, "negative": True},
    "freeze":   {"cap": 1, "consume": {"mode": "skip"}, "tag": "freeze", "cleanse": True, "negative": True},
    "sleep":    {"cap": 1, "consume": {"mode": "skip"}, "tag": "sleep", "wake_on_hit": True,
                 "negative": True},          # 不可净化（原 CLEANSE_TAGS 无 sleep）
    "silence":  {"cap": 1, "consume": {"mode": "no_skill"}, "tag": "silence", "cleanse": True, "negative": True},
    # ============ 可净化减伤/状态（V5④：原 CLEANSE_TAGS 硬清单成员表化） ============
    # spd_down：双语义（装配层 _slow 减速 stat + EFFECT_ACTIONS 控制 skip）→ 不设 consume
    #   （动作参数优先，协议 §7 判据）；仅作净化标记
    "spd_down": {"cap": 1, "tag": "spd_down", "cleanse": True, "negative": True},
    # reduce：value 型减伤（effects[key].v）；净化遍历查表清（原 CLEANSE_TAGS 含 reduce）
    "reduce":   {"cap": 1, "cleanse": True, "negative": True},
    # ============ N9.7 收尾（m_affixtail）：purify 圣洁削弱 ============
    # 净化词条（purify）驱散成功后给敌方挂的 1 刻攻击 -10%（panel atk×0.90 快照，
    # we_affix_purify 动作经 engine act_apply 写入；negative 标记使增益判定/净化
    # 遍历天然不把它当增益回扫——语义记录 + 规则表一致性的纯声明行）
    "holy_weaken": {"cap": 1, "tag": "holy_weaken", "negative": True,
                    "panel": {"stat": "atk", "op": "mul", "mult": 0.90}},
}

# ============================================================
# 名词效果 → 引擎动词动作序列
# （技能数据/怪物模板里的 effect/mech 名词，经这里翻译成引擎动词）
# ============================================================
EFFECT_ACTIONS: dict = {
    # ---- 控制类（写 target.effects[tag]；V5②：mode 语义已入 EFFECT_RULES[key].consume，
    #      stun/freeze/sleep/silence 瘦身 key-only 查表——spd_down 双语义保留动作参数）----
    # mode=skip 整跳（行动级消费：轮到行动跳过+清）；mode=no_skill 禁技（技能转普攻）
    "stun":      [{"action": "apply", "key": "stun", "on": "target", "turns": 1}],
    "freeze":    [{"action": "apply", "key": "freeze", "on": "target", "turns": 1}],
    "sleep":     [{"action": "apply", "key": "sleep", "on": "target", "turns": 1}],
    "silence":   [{"action": "apply", "key": "silence", "on": "target", "turns": 2}],
    "slow":      [{"action": "apply", "key": "spd_down", "on": "target", "turns": 2, "mode": "skip"}],
    "spd_down":  [{"action": "apply", "key": "spd_down", "on": "target", "turns": 2, "mode": "skip"}],
    # ---- 属性增益（写 caster.effects[key]；数值 V5 已入 EFFECT_RULES[key].panel，
    #      动作瘦身 key-only——apply 参数缺省查表快照进条目；单源查表）----
    # 数值参考旧 battle_config.BUFF_MULT（N7.1 全新填：desc/策划案为准，旧表对照）：
    #   atk_up=×1.30 / matk_up=×1.50 / matk_up_strong=×1.80 / def_up=×1.45 /
    #   spd_up=×1.40 / crit_up=+0.20 / magic_resist=+0.15 / mon_atk_down=×0.70
    # panel 声明见上方 EFFECT_RULES（V5 静态增益入表段，数值与旧动作参数逐条核验一致）。
    "atk_up":    [{"action": "apply", "key": "atk_up"}],
    "dodge_buff":  [{"action": "apply", "key": "dodge_up"}],
    "spd_buff":    [{"action": "apply", "key": "spd_up"}],
    "crit_hit_buff": [{"action": "apply", "key": "crit_up"}],
    "cc_immune":    [{"action": "apply", "key": "cc_immune"}],   # 无面板折算（纯免疫状态）
    "purify_immune": [{"action": "apply", "key": "cc_immune"}],  # 净化免疫药（I5 映射 cc_immune）
    # 团队/全员增益 → 自身有效键（旧 team_keys 同语义）
    "atk_all":   [{"action": "apply", "key": "atk_up"}],
    "def_all":   [{"action": "apply", "key": "def_up"}],
    "matk_all":  [{"action": "apply", "key": "matk_up_strong"}],
    "crit_all":  [{"action": "apply", "key": "crit_up"}],
    "spd_all":   [{"action": "apply", "key": "spd_up"}],
    "atk_matk_all": [{"action": "apply", "key": "atk_up"},
                     {"action": "apply", "key": "matk_up"}],
    # ---- N7.5b 药水/食物纯属性别名（items.py effect → EFFECT_RULES panel；special:* 类 N8 事件）----
    "buff_atk":    [{"action": "apply", "key": "atk_up"}],
    "buff_atk_big":[{"action": "apply", "key": "atk_up_big"}],
    "buff_atk_small":[{"action": "apply", "key": "atk_up_small"}],
    "buff_atk_food":[{"action": "apply", "key": "food_atk_up"}],
    "buff_def":    [{"action": "apply", "key": "def_up"}],
    "buff_def_food":[{"action": "apply", "key": "food_def_up"}],
    "buff_spd":    [{"action": "apply", "key": "spd_up"}],
    "buff_spd_small":[{"action": "apply", "key": "spd_up_small"}],
    "buff_spd_food":[{"action": "apply", "key": "food_spd_up"}],
    "buff_crit":   [{"action": "apply", "key": "crit_up"}],
    "buff_crit_small":[{"action": "apply", "key": "crit_up_small"}],
    "buff_crit_big":[{"action": "apply", "key": "crit_up_big"}],
    "buff_crit_food":[{"action": "apply", "key": "food_crit_up"}],
    "buff_matk":   [{"action": "apply", "key": "matk_up_pot"}],
    "buff_matk_strong":[{"action": "apply", "key": "matk_up_strong"}],
    "buff_matk_food":[{"action": "apply", "key": "food_matk_up"}],
    "food_spd_up_small":[{"action": "apply", "key": "food_spd_up_small"}],
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

# ============================================================
# MECH_CASH: 技能 mech 兑现声明表（v181.M 职业机制装配层）
# mech 值 → 兑现行为（引擎零知识；class_mech_proc 装配时参数化挂事件钩子，
# 动作只写"怎么兑现"，差异全在本表）。新兑现机制 = 加一行声明；
# 模式覆盖不了的真新语义才写新动作（~15 行）。
#
# 模式（mode，R1b 起 owner 方向由 mode 推断，装配时写入效果 dict 参数 owner）：
#   dmg_mult_clear        伤害乘区按持有层加成（dmg_calc）＋命中后清层（skill_hit）
#                          owner=caster（缺省，finisher 行为不变）：读/清 caster effects
#   dmg_mult_clear_target 同上但 owner=target（B2 burst 引爆族：印记/毒层全在 target
#                          effects 上——读/清 fire ctx 的 target）
#   heal_clear            花 N 层换治疗（技能内兑现，R1c）
#   bonus_clear           层数转附加伤害后清层（备用形态，R1b 未用——burst 族已由
#                          dmg_mult_clear_target 覆盖：乘区即兑现，无需独立附伤段）
#
# 通用声明字段：
#   key        消费的叠层条目；支持 [k1, k2, …] 多印记 key 列表（乘区层数 = 各 key 之和；
#              清层清全部）——语义按 EFFECT_RULES[key] 条目 stacks 字段折算
#   per_layer  每层伤害加成（技能 info.per_stack 可覆盖）
#   clear      命中后清主 key（info.keep_on_kill = 不清，技能级覆盖）
#   clear_extra 主清之外的并列清层 [{"owner": caster|target, "key": ...}, …]
#   name/layer_label/unit/icon  文案 flavor（动作零硬编码；日志 = "{icon} {name}！…"）
# ============================================================
MECH_CASH = {
    "finisher": {
        "name": "终结技",
        "mode": "dmg_mult_clear",        # owner=caster（缺省）：读/清 caster effects
        "key": "lian_duan",              # 消费的叠层条目
        "per_layer": 0.10,               # 每层伤害 +10%（技能 info.per_stack 可覆盖：链舞 +6%）
        "upgrade": {"proc": "finisher_up", "per_layer_add": 0.06},
        # 链舞（kind=物理 主动技带 passive.proc=finisher_up——装配器只扫 kind=被动不装配）：
        # 学到链舞 → 终结技每段系数 10% → 16%（desc「终结技系数+6%（每段 10% → 16%）」）
        "clear": True,                   # 命中后清层（info.keep_on_kill = 不清，技能级覆盖）
        "crit_at": 4,                    # 连段 ≥4 必定暴击（处刑；crit roll 前钩子就绪后生效——声明先行）
        "layer_label": "连段", "unit": "段", "icon": "🔪",
    },
    # ---- B2 target 方向兑现（R1b burst 引爆族：mode dmg_mult_clear_target = owner=target）----
    "zhan_yi_fury": {
        "name": "狂暴",
        "mode": "fury_enter",          # 血祭：花 res 层战意 → 进入狂暴（无视 10 层门槛）
        "res": "zhan_yi",
        "label": "血祭",
        "icon": "🔥",
        # mech_val（技能数据 4）= 进入消耗的战意层数——兑现动作读 mech_val_field 扣层
    },
    "element_burst_all": {
        "name": "元素迸发",
        "mode": "dmg_mult_clear_target",  # 印记在 target effects（EFFECT_RULES fire/ice/thunder_mark on=target）
        "key": ["fire_mark", "ice_mark", "thunder_mark"],   # 多印记 key：层数=各 key 之和；清层清全部
        "per_layer": 0.12,               # desc 元素迸发：结算目标全部印记，每层 +12% 伤害
        "clear": True,
        "layer_label": "元素印记", "icon": "💥",
    },
    "element_burst_3": {
        "name": "元素裁决",
        "mode": "per_system_clear_target",   # v181.M-R1c：三系各自 stacks≥1 → 每系 ×(1+per_system)；印记在 target
        "key": ["fire_mark", "ice_mark", "thunder_mark"],
        "per_system": 0.20,               # desc：结算三系印记，每系 ×1.2（层数≥1 的系才乘）
        "clear": True,
        "layer_label": "元素印记", "icon": "⚖️",
    },
    # element_burst（基础 lv16 元素引爆：结算印记并触发对应反应）= 元素反应系统，单独设计，非本轮。
    "poison_burst": {
        "name": "荆棘爆",
        "mode": "dmg_mult_clear_target",
        "key": "poison",                 # 毒在 target effects（EFFECT_RULES poison on=target cap=5）
        "per_layer": 0.15,               # desc：引爆毒层，每层 +15% 伤害
        "clear": True,
        # 注：desc"5 层上限，最高 ×1.75" = 1+0.15×5 封顶值本身（5 层全引爆即 ×1.75），
        #    无需额外 cap_mult 乘区；层数受 EFFECT_RULES poison cap=5 自然 clamp（apply op=add）。
        "layer_label": "毒", "icon": "☠️",
    },
    "poison_burst_finisher": {
        "name": "毒爆",
        "mode": "dmg_mult_clear_target",
        "key": "poison",
        "per_layer": 0.14,               # desc：引爆全部毒层，每层 +14% 伤害
        "clear": True,
        # desc 明写"结算后连段归零"：主清 target 毒层之外，并列清 caster 连段（clear_extra）
        "clear_extra": [{"owner": "caster", "key": "lian_duan"}],
        "layer_label": "毒", "icon": "☠️",
    },
    # ⚠️ arcane_burst（奥术脉冲/奥术洪流：燃尽全部充能每层 +15%；奥术洪流满 5 层 ×1.75）——
    #    R1b 版本漂移核对结论：EFFECT_RULES.arcane cap=10 ≠ 技能 desc"满 5 层"世代
    #    （旧 mech cap 表 battle_config 亦记 arcane: 5 → EFFECT_RULES 系复制漂移）。
    #    未声明（未硬改任何 cap）——兑现裁决留主 agent：cap 收敛 5 后填
    #    owner=caster key=arcane per_layer=0.15；另"架设中只烧一半"（v139 focus 形态）同属缺口。
    # ✅ zhan_yi_cash（冷静：花 5 层战意回 20% 生命）v181.M-R1c 走 **res_cost 数据通道**
    #   （skills.py 冷静已加 hp_pct=0.20 + res_cost={zhan_yi:5}：引擎 _spend_skill_cost 扣层 +
    #   _skill_usable 前置拦截）——不需要 heal_clear 装配模式。清 1 减益 + curse 到期
    #   机制记缺口（见 EFFECT_RULES curse 注释）。
    # ✅ faith_unload（卸负：卸 3 点信念回 80% 魔攻+成长）v181.M-R2e 兑现接通（heal_clear
    #   R1c 同族先例 = 技能内 res_cost 兑现）：
    #   - skills.py sk_xie_fu 已加 res_cost={faith:3}（引擎 _skill_usable 前置拦截 +
    #     _spend_skill_cost 扣层 + kind=治疗 heal_formula 回血 = 施放时查 faith≥3 → 扣 3 →
    #     自身回血 80% 魔攻+成长）
    #   - 消费端配套（R2e 同批）：faith 渠道攒取（heal_cast+2/taken+1）、档位乘区
    #     （heal_calc load_tiers）、过载（threshold）、每刻 -0.7 衰减（period）全闭环
    "faith_unload": {
        "name": "卸负",
        "mode": "heal_clear",             # 技能内兑现（res_cost 数据通道，无事件钩子）
        "key": "faith",                   # 消费的叠层条目（声明记录——兑现经 skills res_cost）
        "amount": 3,                      # 每施放扣 3 层（mech_val=3 同源）
        "note": "兑现走 skills.py sk_xie_fu res_cost={faith:3} + kind=治疗 heal_formula",
    },
}

# ============================================================
# 被动 proc 声明表 PASSIVE_PROC（v181.M-passive · 插件形态样板）
# ============================================================
# 技能 kind=被动 + passive.proc 字段 → 本表声明 {event 触发事件, action 动作,
# judge 判定模板}——装配器扫已学被动 → 被动参数(passive dict 的 mult/dmg_add/layers/
# chance…)并入 effect dict 参数 → 挂 actor.triggers[event]。动作读 ctx+params 执行，
# **零 proc 硬编码**（语义源 = 技能 desc + passive dict；旧 battle.py 时代 52 proc 全空转，
# 方案 docs/REFACTOR_v181_PASSIVE_PROC_PLAN.md）。
# judge 模板：装配时合并判定所需字段；被动参数归一 mult（mult/dmg_add/per_layer→mult）。
PASSIVE_PROC: dict = {
    # ---- P1 样板族：dmg_calc 条件乘区（零引擎改动通道——对齐 N9.7d we_dmg_mult_cond）----
    "arcane_resonance": {   # 奥术共鸣：奥术系技能伤害 +15%
        "event": "dmg_calc", "action": "passive_dmg_mult",
        "judge": {"kind": "mech_eq", "mech": "arcane"},
    },
    "element_origin": {     # 元素起源：三系印记齐 ≥2 层 → ×1.2
        "event": "dmg_calc", "action": "passive_dmg_mult",
        "judge": {"kind": "target_marks_all_ge", "marks": ["fire_mark", "ice_mark", "thunder_mark"]},
    },
    "speed_ratio_dmg": {    # 疾风·极：我方速度 ≥ 敌方 ×2 → 伤害 +20%
        "event": "dmg_calc", "action": "passive_dmg_mult",
        "judge": {"kind": "speed_ratio_ge", "ratio_field": "ratio"},
    },
    # ---- P1 样板族：on_kill 回能 ----
    "focus_full_on_kill": {  # 追风：击杀 → 专注回满（EFFECT_RULES energy start_full 口径）
        "event": "on_kill", "action": "passive_kill_gain",
    },
    # ---- 静态域（domain：不挂 triggers，装配器直接写 bonus 容器——纯配置量）----
    "poison_cap": {          # 淬毒之心：毒层上限 +3（bonus.cap[poison]）
        "domain": "cap", "cap_key": "poison",
    },
    "poison_cap_up": {       # 剧毒之心：毒层上限 +3（毒爆增伤部分 P2 动作）
        "domain": "cap", "cap_key": "poison",
    },
    "hunt_mark_cap": {       # 追猎者：猎印上限 +2（至 5 层）
        "domain": "cap", "cap_key": "hunt_mark",
    },
    "soul_mark_cap": {       # 灵魂锁链：魂标上限 +2（per_layer 乘区部分 P2）
        "domain": "cap", "cap_key": "soul_mark",
    },
    "arcane_constant": {     # 奥术恒常：奥术技能耗蓝 −50%（bonus.cost when mech_prefix arcane）
        "domain": "cost",
        "when": [{"judge": {"mech_prefix": ["arcane"]}}],
    },
    # ---- P2 族：on_taken 受击反击（聚合族——装配器族级归并，旧挂点13 语义）----
    "counter_chance": {      # 以守为攻：受击 35% 概率反击（普攻的 80%）
        "event": "on_taken", "action": "passive_counter", "agg": "counter",
    },
    "counter_up": {          # 反击之王：反击概率 +25%、反击伤害 +50%（聚合增强，只首条）
        "event": "on_taken", "action": "passive_counter", "agg": "counter",
    },
    # ---- P2 族：dmg_calc 乘区扩展（judge 谓词扩展：target_mark_any/mech_prefix）----
    "hunt_mark_up": {        # 自然之眼：猎印每层增伤额外 +6%（基础 8% 走 debuff_scale 引擎天然段）
        "event": "dmg_calc", "action": "passive_dmg_mult",
        "judge": {"kind": "target_mark_any", "mark": "hunt_mark"},
    },
    "soul_mark_cap": {       # 灵魂锁链：cap 段（P1b 已收）+ 每层伤害 +8% 乘区段（本声明双通道）
        "domain": "cap", "cap_key": "soul_mark",
        "event": "dmg_calc", "action": "passive_dmg_mult",
        "judge": {"kind": "target_mark_any", "mark": "soul_mark"},
    },
    "poison_burst_up": {     # 蚀骨：毒爆伤害 +25%（mech_prefix poison_burst 覆盖两种毒爆技）
        "event": "dmg_calc", "action": "passive_dmg_mult",
        "judge": {"kind": "mech_prefix", "mech": "poison_burst"},
    },
    "poison_cap_up": {       # 剧毒之心：cap 段（P1b）+ 毒爆增伤 +20%（本声明双通道）
        "domain": "cap", "cap_key": "poison",
        "event": "dmg_calc", "action": "passive_dmg_mult",
        "judge": {"kind": "mech_prefix", "mech": "poison_burst"},
    },
    # ---- P2 族：act_cast 条件暴击（资源层数门槛 → 本次行动 crit 加算 buff）----
    # 旧挂点1 _passive_crit_bonus（crit_cond_add）语义：资源 ≥ 阈值 → 暴击率 +add
    # （绝对点加算——面板 crit 是小数概率）。buff 快照型 effects 条目（stat/mult/op=add），
    # 动作每行动重写/清除，无残留。
    "zhan_yi_crit": {        # 狂热：战意 ≥8 → 暴击 +15%
        "event": "act_cast", "action": "passive_cond_crit",
        "judge": {"kind": "res_ge", "res": "zhan_yi", "ge_field": "stacks"},
        "buff_key": "passive_crit_zhan_yi",
    },
    "arcane_wisdom": {       # 真知：奥术充能满 5 → 奥术系技能暴击 +20%（desc「奥术暴击」）
        "event": "act_cast", "action": "passive_cond_crit",
        "judge": {"kind": "res_ge", "res": "arcane", "ge_field": "stacks",
                  "mech": "arcane"},
        "buff_key": "passive_crit_arcane",
    },
    "focus_surplus_crit": {  # 疾风之心：结余 ≥40 → 下次技能暴击 +20%（普攻不吃）
        "event": "act_cast", "action": "passive_cond_crit",
        "judge": {"kind": "res_ge", "res": "energy", "ge_field": "surplus",
                  "not_basic": True},
        "buff_key": "passive_crit_focus",
    },
    # ---- P2 族：taken_calc 条件减伤 + turn_start 免控（战士坚城之姿双段）----
    # 旧挂点11 _mitigate_chain（dr_cond）语义：战意 ≥ stacks → 受击减伤 reduce；
    # 旧挂点10 player_turn（cc stun_clear）语义：战意 ≥ stacks → 移除眩晕。
    "zhan_yi_full_reduce": {   # 坚城之姿：战意满 10 → 减伤 +10%、免疫眩晕
        "event": "taken_calc", "action": "passive_taken_reduce",
        "judge": {"kind": "res_ge", "res": "zhan_yi", "ge_field": "stacks"},
        "also": [{"event": "turn_start", "action": "passive_cc_clear",
                  "judge": {"kind": "res_ge", "res": "zhan_yi", "ge_field": "stacks"},
                  "ctrl": "stun"}],
    },
    # ---- P2 族：turn_start 战意挣脱控制（tenacity 坚韧 每场 3 次）----
    "tenacity": {              # 坚韧：被控制时消耗 2 层战意跳过（每场 3 次）
        "event": "turn_start", "action": "passive_cc_break",
        "ctrl_any": True, "res": "zhan_yi", "cost_field": "cost",
        "left_key": "tenacity_break_left", "left_init": 3,
    },
    # ---- P2 族：act_cast 吸血/治疗溢出（战士淬血 + 牧师圣光回响）----
    "zhan_yi_lifesteal": {     # 淬血：每层战意提供 1.5% 吸血（行动内 lifesteal 面板加算 buff）
        "event": "act_cast", "action": "passive_lifesteal_buff",
        "res": "zhan_yi", "buff_key": "passive_lifesteal_zhan_yi",
    },
    "heal_overflow_shield": {  # 圣光回响：治疗溢出量的 50% 转为护盾（heal_calc 落地前算溢出）
        "event": "heal_calc", "action": "passive_heal_overflow_shield",
    },
    # ---- P2 族：dot_calc DOT 乘区（万毒归宗——引擎 N9.14 dot_calc 广播事件）----
    "poison_all_up": {         # 万毒归宗：所有毒层造成的伤害 +35%（dot_calc 乘区）
        "event": "dot_calc", "action": "passive_dot_mult",
        "judge": {"dot_key": "poison"},
    },
    # ---- P2 族：dot_calc 毒层条件 debuff（剧毒之触——毒每跳维护目标减速降防）----
    "poison_weaken": {         # 剧毒之触：目标毒 ≥5 → 减速 30%、降防 20%
        "event": "dot_calc", "action": "passive_poison_weaken",
        "judge": {"dot_key": "poison", "layers_field": "layers"},
        "spd_pct": 0.30, "def_pct": 0.20, "hold": 2.0,   # desc 权威：30%/20%，续期 2 刻（毒 1s/跳）
    },
    # ---- P2 族：元素印记增强（act_cast 挂印/引爆通道——元素机制现网活）----
    # 挂印技 mech=fire_mark/ice_mark/thunder_mark（effects_from_skill mech→state 通用
    # apply op=add）；引爆技 mech=element_burst_*（MECH_CASH dmg_mult_clear_target）。
    # 挂印增强 = act_cast 时（效果段 apply 前）先给 target 印记 +1，基础段再 +1 = 总 2。
    "element_affinity": {      # 元素亲和：引爆后，下次挂印 +1 层
        "event": "act_cast", "action": "passive_mark_enhance", "mode": "affinity",
    },
    "element_sync": {          # 元素同调：连续两次同系施法，第二次挂印 +1 层
        "event": "act_cast", "action": "passive_mark_enhance", "mode": "sync",
    },
    "element_core": {          # 元素之核：单系印记满 3 → 该系结算暴击 +20%
        "event": "act_cast", "action": "passive_element_core_crit",
    },
    # ---- P2 族：狂暴中死亡复活（血怒·不灭——v153 战士血怒线）----
    "berserk_revive": {        # 血怒·不灭：狂暴中首次死亡 → 清战意复活回 hp_pct
        "event": "on_death", "action": "passive_revive_berserk",
        "form": "fury", "used_key": "_berserk_revive_used",
    },
    # ---- P2 族占位（填表即接；动作族见方案文档）----
    # stance_immortal/undead_faith 等职业批续（C 桶映射见 roadmap）
}


