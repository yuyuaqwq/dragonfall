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
    # v181.M-R2b：name 展示名单源化（源 core_resources.py v130.2 旧表退役迁移——rage 怒气/faith 信仰值/
    # cp 连击点/element 元素亲和/chi 气 对照旧表 name；zhan_yi 战意/lian_duan 连段/arcane 奥术
    # 对齐 commands/combat RESOURCE_STACK_CN v181.M-R3 现网展示名）。cap 即旧 max（同值）。
    "zhan_yi": {
        "name": "战意",
        "cap": 10,
        "stat_scale": {"atk": 0.04},          # 每层攻击 +4%
        "on_threshold": {10: {"form": "fury"}},  # 满 10 进狂暴（上层消费）
    },
    "lian_duan": {
        "name": "连段",
        "cap": 10,
    },
    "rage": {
        "name": "怒气",
        "cap": 10,
        "stat_scale": {"dmg_mult": 0.12},     # 每层伤害 +12%
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
    },
    "arcane": {
        "name": "奥术",
        "cap": 10,
    },
    # R4（N9.7e affix 资源词条 gain clamp 声明）：energy/faith/cp/element 是
    # affix res+gain 词条（暴击蓄能/圣辉回响/暴击回点/充能汲引等）的资源容器 key，
    # cap 源 = core_resources legacy max（精力 100/信仰 10/连击点 5/元素亲和 5）。
    # 纯 cap 声明（无 stat_scale/period/consume → 引擎惰性条目，只 clamp 不折算）；
    # 渠道喂养/单源化属 R2 批次，词条装配 R4 先落地。
    "energy": {
        "cap": 100,
        # v181.M-R2（游侠专注流量制，源 core_resources.cls_you_xia v176）：
        # - start_full：开局满额（装配层初始化 effects[energy] = cap）
        # - period dir=gain：每刻自然回 18（schedule 时间驱动，静默回复 clamp cap）
        "name": "精力", "start_full": True,
        "start_classes": ["cls_you_xia"],   # 开局满额归属职业（装配层按 class 判）
        "period": {"dir": "gain", "interval": 1.0, "amount": 18},
    },
    "faith": {
        "name": "信仰值",
        "cap": 10,
    },
    "cp": {
        "name": "连击点",
        "cap": 5,
    },
    "element": {
        "name": "元素亲和",
        "cap": 5,
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
        "clear": True,                   # 命中后清层（info.keep_on_kill = 不清，技能级覆盖）
        "crit_at": 4,                    # 连段 ≥4 必定暴击（处刑；crit roll 前钩子就绪后生效——声明先行）
        "layer_label": "连段", "unit": "段", "icon": "🔪",
    },
    # ---- B2 target 方向兑现（R1b burst 引爆族：mode dmg_mult_clear_target = owner=target）----
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
}


