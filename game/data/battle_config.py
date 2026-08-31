# -*- coding: utf-8 -*-
"""战斗主路径数据表（v125.2 B1 数据下沉）——纯数据，无逻辑、无 IO。

从 game/battle.py 伤害结算段 / game/engine.py 下沉的数值与白名单。
消费端：
  - game/battle.py：_mech_stack_bonus / _apply_mech_gain / _tick_dots /
    _enemy_stats（Boss 攻乘区）/ _apply_mech_effect（控制白名单）/
    伤害主路径 mech 特判（满血必暴/碎冰/连击/proc 归属/stat 归属）
  - game/engine.py：element_reaction 查 ELEMENT_REACTIONS（对外接口不变）

调数值只改本文件。
"""
# ============================================================
# 幸运一击（v133 收敛：峰值红线 40% 配套——幅度 1.5→1.3，全职业统一）
# ============================================================
LUCKY_CRIT_CHANCE = 0.30   # 暴击命中后触发概率（battle.py 普攻/技能两处消费）
LUCKY_CRIT_MULT = 1.3      # 触发后的追加增伤倍率（原 1.5，v133 收敛）

# ============================================================
# 多段技能暴击（v133 收敛：峰值红线 40% 配套）：
# multi≥2 时仅首段享受暴击加成（第 2 段起暴击等同于未命中——
# 避免"多段共享单次暴击判定"导致整段连锁暴击的峰值爆炸）
# ============================================================
MULTI_HIT_CRIT_FIRST_ONLY = True

# ============================================================
# 叠层型机制每层增伤（_mech_stack_bonus）：倍率 = 1 + 层数 × 值
# ============================================================
MECH_STACK_BONUS = {
    "rage": 0.12,        # 狂暴：每层 +12%（5 层 +60%）
    "shadow": 0.12,      # 影袭：每层 +12%
    "chi": 0.12,         # 气力：每层 +12%
    "spellblade": 0.08,  # 魔剑士·魔能：每层 +8%
    "dragon_might": 0.10,  # v130.2f 收敛：每层 +10%（原 0.18 满力终曲 EQ 8.96 超标尺且反超苦修天花板；0.10→终曲≈6.4、吐息≈4.68）
    "zen": 0.12,         # v130.2 禅意：每层 +12%（撼岳·终焉/穿岳一击 满禅意 10 层 +120%）
}

# 增益类技能可叠层 mech 白名单（_apply_mech_gain；v59 封顶语义，共 16 个）
MECH_STACK_WHITELIST = (
    "rage", "shield", "wind", "shadow", "chi", "bless", "judge",
    "iron", "mark", "burn", "poison", "freeze", "arcane", "spellblade",
    "zhan_yi", "lian_duan",   # v151 职业重构：战意（战士叠层）/ 连段（刺客计数）
)

# ============================================================
# DOT 混合公式（_tick_dots，契约 §2.2）：
#   每层伤害 = (atk×atk + matk×matk + max_hp×hp) × 层数 × mult × (1 - 总抗)
#   true_dmg=True 的类型（v138.2 律四：腐蚀类）走真伤分支——绕过 _enemy_mitigate 的
#   def/mdef 削减（仍走免疫检查 + Boss 护盾层吸收），使异常流成为第二条独立输出轴。
# ============================================================
DOT_DEFS = {
    "poison": {"atk": 0.5, "matk": 0.0, "hp": 0.015},  # 毒：atk×0.5 + max_hp×1.5%
    "burn":   {"atk": 0.0, "matk": 0.4, "hp": 0.01},   # 灼烧：matk×0.4 + max_hp×1%
    "bleed":  {"atk": 0.6, "matk": 0.0, "hp": 0.015},  # 流血：atk×0.6 + max_hp×1.5%
    # v138.2 律四：腐蚀（真伤轴）——数值参考 atk 0.4 / matk 0.3 / hp 2.0%，
    # 低于毒/流血的 0.5/0.6 攻击系数 + 略高于 1.5% 的生命系数：真伤绕过 def/mdef，
    # 对高防 Boss 的等效收益自动反超，故攻击系数刻意压低防异常流数值反超常规输出轴
    "corros":  {"atk": 0.4, "matk": 0.3, "hp": 0.02, "true_dmg": True},
}
DOT_BLEED_DOUBLE_HP_PCT = 0.30  # 放血：目标当前生命 <30% 时流血伤害 ×2（处决线）
DOT_ADAPT_DECAY_STEP = 0.04     # 适应回落：poison/burn 最近 2 回合未再叠层 → 耐受 -4%
DOT_RESIST_CAP = 0.95           # 总抗上限：min(0.95, dot_res + 适应 adapt)

# ============================================================
# 元素反应（v2.0，12 章 3.1，严格按策划案表；从 engine.py 迁移，结构不变）
# 当前系 × 目标印记 → 反应：
#   蒸发 = 火印(目标) + 冰(当前系) → 增伤 30%，清除印记
#   超载 = 雷印(目标) + 火(当前系) → 全体 120% 伤害，清除印记
#   冻结 = 冰印(目标) + 水(当前系) → 冻结 1 回合（法师暂无水系技能，预留）
#   感电 = 雷印(目标) + 雷(当前系) → 连击 +1，印记保留
# ============================================================
ELEMENT_REACTIONS = {
    ("ice", "fire_mark"):        {"name": "蒸发", "mult": 1.30, "clear": True, "extra": ""},
    ("fire", "thunder_mark"):    {"name": "超载", "mult": 1.00, "clear": True, "extra": "aoe"},
    ("water", "ice_mark"):       {"name": "冻结", "mult": 1.00, "clear": True, "extra": "freeze"},
    ("thunder", "thunder_mark"): {"name": "感电", "mult": 1.00, "clear": False, "extra": "chain"},
}

# ============================================================
# Boss 攻强乘区（_enemy_stats）：enrage/phase/low_hp/pv_broken/stacks
# 叠加后 atk/matk 不得超过基础 × cap（v120 总帽）
# ============================================================
BOSS_ATTACK_MULTS = {
    "enraged": 1.35,     # v58 狂暴：血量 <30% 触发后攻击 +35%
    "phase_step": 0.20,  # v83 多阶段：每阶段 +20%
    "low_hp": 1.25,      # v116.1 条件反制·玩家低血追击 +25%
    "pv_broken": 1.30,   # v116.1 条件反制·玩家大招反扑 +30%
    "stack_step": 0.08,  # v83 叠层强化：每层 +8%
    "cap": 3.0,          # v120 总帽：基础 atk/matk ×3.0
}

# ============================================================
# 控制白名单
# ============================================================
# 控制类 mech 白名单（_apply_mech_effect：Boss 控制时长减半 / 打断蓄力）
CONTROL_MECHS = ("stun", "freeze", "silence")
# 技能 cc 字段白名单（v63：独立于 mech 叠层的额外控制效果——眩晕/沉默/净化）
SKILL_CC_WHITELIST = ("stun", "silence", "cleanse")

# ============================================================
# mech 特判收敛（伤害结算主路径查表，v125.2 B1）
# ============================================================
# 满血必暴：mech 命中且目标满血 → 必定暴击（影袭）
MECH_FULL_HP_CRIT = ("shadow",)
# 碎冰增伤：mech 命中且目标冻结中 → 伤害 ×值（冰霜）
MECH_FROZEN_MULT = {"freeze": 1.5}
# 连击追加：mech 命中 → 连击次数 += 该 mech 自身层数（风印）
MECH_COMBO_STACKS = ("wind",)
# proc 型被动 mech 归属：被动组名 → 命中即生效的 mech 集合（毒系/奥术系）
MECH_PROC_GROUPS = {
    "poison_dmg": ("poison", "poison_burst"),
    "arcane_dmg": ("arcane",),
}
# stat 型被动 mech 归属：被动 stat 键 → 对应 mech（命中该 mech 才生效）
MECH_STAT_PASSIVES = {
    "judge": "judge",    # 审判之心
    "shadow": "shadow",  # 暗影之心
}


# ============================================================
# v130.2 并入附录（2026-08-19 鱼鱼拍板：勿为每个版本单开数据文件，
# 原 v130_config.py 整体并入本文件并删除原文件。以下为 v130.2 引擎新机制数值表）
# ============================================================
# ============================================================
# 法师：元素印记 / 引爆反应表 / 同系连发（攻线·元素法师进档解锁，mage_转职.md §1.0）
# ============================================================
# 目标侧三系印记上限（每目标每系独立 0..3；目标 dict 的 element_marks 字段）
ELEMENT_MARKS_MAX = 3
# 施法命中按技能 element 字段叠加印记层数
ELEMENT_MARK_GAIN_PER_HIT = 1
# 引爆反应表：引爆系 × 目标印记系 → 反应结算（mage_转职.md §1.0②；cond type='reaction' 引爆技接入）
#   mult  ：伤害倍率（蒸发 1.30，其余 1.00 由 extra 效果体现）
#   clear ：反应后清除目标哪系印记（"" = 不清除）
#   extra ：aoe=全体 120% 魔攻伤害 / freeze=冻结 1 回合 / chain=感电连击 +1
REACTION_TABLE = {
    ("fire", "ice"):     {"kind": "vaporize",      "name": "蒸发", "mult": 1.30, "clear": "ice",     "extra": ""},
    ("fire", "thunder"): {"kind": "overload",      "name": "超载", "mult": 1.00, "clear": "thunder", "extra": "aoe"},
    ("ice", "thunder"):  {"kind": "frozen",        "name": "冻结", "mult": 1.00, "clear": "thunder", "extra": "freeze"},
    ("thunder", "ice"):  {"kind": "electro_chain", "name": "感电", "mult": 1.00, "clear": "",        "extra": "chain"},
}
# 同系连发奖励（被动「元素凝聚」重定义自 dump 万象亲和：连续两次同系施放，第二次额外 +1 充能）
ELEMENT_SAME_CAST_EXTRA_CHARGE = 1

# ============================================================
# 战士：血债怒火（攻线·狂战士 T1，warrior_转职/总纲 §7.2；受击回怒随缺失血量缩放）
#   受击回怒 = base + ⌊缺失HP% × coef⌋，封顶 cap；满血=1、缺25%血=2、缺一半=3、濒死=5
# ============================================================
RAGE_GAIN_HP_SCALE = {"base": 1, "coef": 4.0, "cap": 5}

# ============================================================
# 游侠：满弦状态（守线·风行者，ranger_转职 §3；精力 ≥ threshold 时 低耗/连射技能 暴击率 +bonus）
#   max_cost：判定「低耗/连射档」的精力消耗上限（≤ 该值享受满弦暴击加成）
# ============================================================
ENERGY_HIGH = {"threshold": 80, "crit_bonus": 0.10, "max_cost": 25}

# ============================================================
# 刺客：on_crit 暴击攒点 + 受击回退 + 连段计数（攻线·影舞者，assassin_转职 §1.0）
#   combo cap：命中 +1 / 受击或落空归零；终结技（res_cost cp）combo≥finish_min 起每层 +per_layer，
#   上限 max_bonus（8 层 × 5% = 40%）
# ============================================================
COMBO_CFG = {"cap": 10, "finish_min": 3, "per_layer": 0.05, "max_bonus": 0.40}
# 攻线·影舞者 on_crit 暴击命中额外 +n 连击点
ASSASSIN_ON_CRIT_GAIN = 1
# 攻线·影舞者 受击回退 -1（高风险高回报：受击丢 1 点并 combo 归零）
ASSASSIN_ON_TAKE_HIT_PENALTY = -1

# ============================================================
# 拳师：蓄势 Momentum（攻线·格斗士 T1，monk_转职 §3.0；每 1 气持有 物理伤害 +per_chi，封顶 cap_chi）
#   持久比例加伤：随当前 chi 动态结算（气耗尽自然归 0）；破势（chi_burst）时清 0 由引擎重置
# ============================================================
MOMENTUM_CFG = {"per_chi": 0.03, "cap_chi": 10}

# ============================================================
# 苦修士·武僧：禅意持有加伤（monk.md §5.2 / core_resources.py 禅意 desc：
#   每 1 禅意 物理伤害 +per_zen，封顶 cap_zen，满 10 +40%）
#   与拳师蓄势同型：持久比例加伤，随当前 zen 动态结算（消耗/倾泻后自然回落）
# ============================================================
ZEN_HOLD_CFG = {"per_zen": 0.04, "cap_zen": 10}

# ============================================================
# 暮影：影步积攒（cls_shadow_blade，assassin.md §5.2）
#   暴击命中 on_crit +1 / 闪避成功 on_dodge_success +1 / 潜行出手额外 +1 / 受击清空全部
#   （on_crit / on_dodge_success 数值已按资源 key 在 core_resources.py 声明，此处只放战斗常量）
# ============================================================
SHADOW_STEP_CFG = {"stealth_extra": 1, "stealth_proc": "stealth"}

# ============================================================
# 暮影：潜行伤害乘区（技能名 → 潜行出手时伤害倍率，assassin.md §5.2）
#   终结·破影一击 潜行×1.5 / 幽影刃 潜行×1.25（skills.py desc 声称，v130.2f2 引擎落地）
#   潜行判定与「潜行必暴」共享同一字段 p_buffs["stealth"]（battle.py 攻击时消费即视为潜行出手）；
#   仅表内技能命中才乘，其余技能恒 1.0（不影响其他职业/技能）
# ============================================================
SHADOW_STEALTH_DMG_MULT = {"终结·破影一击": 1.5, "幽影刃": 1.25}

# ============================================================
# 牧师歌者双资源：回声驻留叠层（priest_转职.md §3.0；echo 落 mech_stacks 驻留叠层，战斗内不清零）
# ============================================================
ECHO_CFG = {
    "max_layers": 3,             # 回声叠层上限（对应 core_resources echo max）
    "heal_per_layer": 6,         # 每层回合初始全队恢复体力
    "buff_extend_per_layer": 1,  # 增益技持续 + 回声层数 回合
}
# 歌者攻线分支（牧师 cls_mu_shi evolve_path=1）：凡落在这些分支名下的技能 = 歌类技（施放 +1 回声）
BARD_BRANCHES = ("吟游诗人", "灵魂歌者", "黎明颂者")

# ============================================================
# 分支级 resource_override：转职分支决定该分支用什么资源（核心资源 key 列表）
#   用于 battle.py 判定「该分支用什么资源」——player.class_name 仍是基础职业（如 cls_mu_shi），
#   转职歌者后仍取 faith，需要分支侧覆盖。key 需已注册进 CORE_RESOURCES（含按 key 注册的副资源）。
#   未命中的 (class, path) 回落 core_resources 按 class 默认单资源。
# ============================================================
BRANCH_RESOURCE_OVERRIDE = {
    # 基础法师无资源（纯蓝施法者）；攻线·元素法师 / 守线·奥秘法师 转职首获 元素亲和充能条(0-5)
    ("cls_fa_shi", 1): ("element",),
    ("cls_fa_shi", 2): ("element",),
    # 牧师攻线·歌者：双资源 = 共鸣（燃料条 resources）+ 回声（驻留叠层 mech_stacks）
    ("cls_mu_shi", 1): ("resonance", "echo"),
}

# ============================================================
# 锻造品质随机（v135 实装 19 章未落地项；消费端 economy.py craft handler）：
#   蓝→紫 / 紫→橙 基础 5% 概率品质+1；锻造副业 Lv.10 神锻名家 额外 +2%（7%）；
#   橙装 2% 概率出「精良」前缀（属性 ×1.15）；品质提升需消耗稀有材料（背包没有则跳过提升）
# ============================================================
QUALITY_UPGRADE_CHANCE = 0.05          # 品质+1 基础概率（蓝→紫、紫→橙）
QUALITY_UPGRADE_MASTER_BONUS = 0.02    # 神锻名家（锻造副业 Lv.10）额外概率加成
MASTERPIECE_CHANCE = 0.02              # 橙装「精良」前缀概率（属性 ×1.15）
QUALITY_UPGRADE_COST = {               # 品质提升额外消耗的稀有材料
    "mat_jing_jin": 1,                 #   精金锭（精金）
    "mat_shen_hai_shui_jing": 1,       #   深海水晶
}

# ============================================================
# v151 隐藏职业删除：HUNT_MARK_ON_LAND_HIT（星语者猎印）已移除
# ============================================================
HUNT_MARK_CRIT_EXTRA = 1

# ============================================================
# 隐藏线进阶变奏（总纲 §7.3，已由 core_resources 声明，此处仅留档说明）
#   龙力 dragon_might：回合末自然回 regen=1（_turn_start 通用 regen 管线已消费，龙脉沸腾）
#   时之沙 time_sand：自动积沙 regen=1（同上）
#   悼咏 canticle：overflow_shield=True 满溢转盾（见 core_resources，引擎溢出段消费）
#   禅意 zen：慢热 regen=0 无特殊，靠 per-zen 加伤（ZEN_HOLD_CFG 每 1 禅意物理 +4%，引擎挂点 battle.py _zen_hold_mult）
# ============================================================

# ============================================================
# v139 职业融合·6 大通用引擎机制（docs/EXTENSIBILITY_REFACTOR_PLAN_v139.md 实现基准）
#   数据驱动：职业差异全部进各职业 core_resources dual_form/focus 字段与技能表，
#   本文件只放 6 个通用机制（dual_form/focus/charge/vent/enemy_bar/counter）的引擎级数值，
#   以及 13 份职业方案（design/new_world/参考_云海猎团职业融合_v139_*.md）提炼的职业签名技数值。
#   铁律：battle.py 禁止职业特判 if-elif；新增常量须 core/constants.py + core/__init__.py 导出；
#   无字段 = 默认不启用（兼容旧数据）；数值过 run_numeric_tests.py 门禁 + v133 峰值红线（≤42% 同级怪血）。
# ============================================================

# ============================================================
# 一、dual_form 双形态（通用形态机，v139 §1）
#   消费端：battle.py 通用形态机（_dual_form_enter/_tick/_hit/_exit/_mult）；
#   各职业差异字段在 core_resources.py 该职业的 dual_form 键下（enter_requirement /
#   maintain_cost / hit_cost / hit_cost_cap / force_return / return_penalty / form /
#   auto_enter / duration / lock_gain / no_hit_clear），本 CFG 只放引擎级通用数值与默认值。
#   免费切换是承重墙：进入/退出不占行动、不耗资源；强制回形态无惩罚（P1）；
#   受击不清零（P3）：单回合至多扣 hit_cost_cap；状态随战斗 to_state/from_state 序列化。
# ============================================================
DUAL_FORM_CFG = {
    "default_enter_requirement": 10,  # 默认入形态门槛：资源 ≥ N 可进入（战前可下调）
    "default_maintain_cost": 1,       # 默认形态维持：形态中每回合 -N 资源
    "default_hit_cost": 1,            # 默认受击扣减：形态中受击 -N（P3：不清零）
    "default_hit_cost_cap": 1,        # 默认单回合受击扣减上限（至多 N）
    "default_force_return": 4,        # 默认强制回基础形态阈值：资源 < N 强制回
    "default_return_penalty": "none", # 默认强制回惩罚：P1 归零无惩罚（不晕/不空过）
    "auto_duration": 3,               # 自动形态持续回合（暮影影舞 auto_enter=True 时 3 回合）
    "dmg_bonus": 0.20,                # 形态增伤倍率默认值（狂暴/龙焰/影舞等形态内技能伤害 +20%）
    # 各职业差异字段说明（实际值在 core_resources.py 对应职业 dual_form 键，引擎读职业字段）：
    #   cls_zhan_shi（攻线狂战士 fury）：enter_requirement 10 / maintain 1 / hit 1 / cap 1 /
    #     force_return 4 / return_penalty none / form fury；狂暴中双段普攻 2×70%，
    #     破势斩入狂暴当回合自动追加 120% 物理（不占行动）；狂暴精通（被动）维持/受击 -1 → 0。
    #   cls_dragon_oath（龙裔 dragon_flame）：enter_requirement 8（战前可下调 6）/ maintain 1 /
    #     hit 1 / cap 1 / force_return 4 / form dragon_flame；龙焰形态龙息/龙爪/龙焰吐息 +20%，
    #     龙焰初击入焰当回合追加 70% 真伤，龙焰吐息消耗 -1（-5→-4），龙脉终曲龙焰限定。
    #   cls_shadow_blade（暮影 dance 影舞态）：auto_enter True / duration 3 / lock_gain True /
    #     no_hit_clear True；影舞态内潜行乘区叠乘（破影一击 ×1.5 / 幽影刃 ×1.25）、CD 全 -1。
    #   cls_wu_sheng（淬势者蓄势/倾泻）：显式化既有骨架，无形态动作不占行动，P1 归零无惩罚。
}

# ============================================================
# 二、focus 架设态（通用专注机，v139 §2）
#   消费端：battle.py 通用专注机（_focus_enter/_tick/_hit/_mult/_block/_exit）；
#   职业差异在 core_resources.py 各职业 focus 字段；本 CFG 放引擎级默认值 + 法师/时咒数值。
#   核心规则：打断不清零（P3，资源保留只退态）；增伤不作用于耗资源大爆发技（防 EQ 超上限）；
#   免费解除（承重墙）；受击打断概率挂 v130.2 批次 2 受击挂点。
# ============================================================
FOCUS_CFG = {
    "enter_turn": 1,            # 进入占 1 回合（站桩吟唱，当回合不出伤）
    "enter_gain": 1,            # 进入时资源 +N（预装，G1）
    "gain_per_turn": 1,         # 专注中每回合额外 +N 资源（G2，主来源完全自主）
    "dmg_bonus": 0.40,          # 专注中技能伤害 +40%（乘区挂 pmult，受 SKILL_PMULT_CAP=6.0 封顶）
    "taken_bonus": 0.20,        # 专注中受击 +20%（走 _damage_player 惩罚分支）
    "interrupt_rate": 0.30,     # 受击打断概率（P3：打断不清零，资源保留）
    "max_turns": 3,             # 维持回合上限，第 max_turns+1 回合自动解除（时间过载）
    "blocked": ("attack", "skill", "swap"),  # 专注中禁止的行动（可防御/道具/逃跑）
    "free_exit": True,          # 主动解除 = 免费无损（承重墙，不扣充能不惩罚）
    "no_burst_skills": True,    # 增伤不作用于耗资源大爆发技（防 EQ 超上限，时咒教训）
    # 各职业差异字段说明（实际值在 core_resources.py 对应职业 focus/stasis 键）：
    #   cls_fa_shi 攻线元素架设（MAGE_FOCUS_CFG）：dmg_mult 0.40 / taken_mult 0.20 /
    #     cast_gain_extra 1（架设中施法命中充能 +1）/ interrupt_charge_loss 1（打断只掉 1 层）/
    #     ctrl_break True（被晕/冻/沉默强制解除）/ stay_actions ("defend","use_item","flee")；
    #     守线深度冥想：arcane_auto_per_turn 1（架设中每回合 arcane 叠层 +1，与奥术直觉叠加 = 每回合 +2）。
    #   cls_chronomancer 时间凝滞（stasis）：enter_turn 1 / enter_gain 1 / gain_per_turn 1 /
    #     dmg_bonus 0.40（不作用于耗沙大爆发）/ taken_bonus 0.20 / interrupt_rate 0.30 /
    #     max_turns 3 / erosion_power 0.60（凝滞态每回合自动「时间侵蚀」60% 魔法伤害，不占行动）。
}

# ============================================================
# 三、charge 蓄力三律（通用电荷机，v139 §3）
#   消费端：battle.py 通用电荷机（_charge_tick/_hit/_release/_state）+ 技能级 charge 字段；
#   三律：P1 蓄力也出伤（边攒边打，被打断也已打出伤害）/ P2 打断仅 -1 阶不清零 /
#   P3 满阶强制释放（不占行动，禁止继续蓄力）。
# ============================================================
CHARGE_CFG = {
    "max": 3,                        # 电荷上限（阶数 0-3）
    "gain_per_turn": 1,              # 每回合蓄 1 阶（蓄力动作）
    "dmg_per_stage": [0.7, 1.3, 1.9],  # 边攒边打：各阶自动出伤倍率（云海口径 0.7 起步 + 每阶 +0.6）
    "interrupt_penalty": 1,          # 打断仅 -1 阶不清零（P3）
    "force_release": True,           # 满阶强制释放（不占行动）
    "release_power": 2.8,            # 满阶释放威力（M = 0.7 × (电荷+1)，电荷 3 时 2.8）
    "release_extra": {"pierce": True, "reach": 3},  # 满阶释放附加：破防 + reach=3（可指定 rank=3 后排）
    # 各职业差异字段说明（实际值在技能级 charge 字段 / RANGER_CHARGE_CFG）：
    #   cls_you_xia 守线电荷制蓄力狙击（RANGER_CHARGE_CFG）：charge_cost 10（蓄力动作耗 10 精力，
    #     低耗档 ≤25 判定内）/ m_base 0.7 / m_step 0.6 / snipe_m_base 0.7 / snipe_min 1
    #     （狙击保底门槛：电荷 ≥1 才能放，云海附 B 第 2 条平衡铁律）/ snipe_reach 3；
    #     旧 charge=1 读条存档降级兼容（不走新分支仍按旧读条结算）。
    #   cls_chronomancer 蓄力三律落凝滞态：P1 时间侵蚀自动出伤（erosion_power 0.60）/
    #     P2 打断不清零（沙全保留）/ P3 沙满 5 强制释放（禁止攒沙技，必须放耗沙大爆发）。
}

# ============================================================
# 四、vent 排气节流阀（通用排气机，v139 §4）
#   消费端：battle.py 通用排气机（_vent_check/_apply/_relief/_delay）；
#   核心规则：满值强制排气（P3 防死锁）/ 位移闪避泄压（位移从成本变收益）/
#   排气后低耗技段数 +1（补偿，爆发前置不是惩罚）；三向权衡（常规硬吃/快排泄压/深排等窗口）DPR 持平。
# ============================================================
VENT_CFG = {
    "trigger": 100,                   # 资源 = 上限触发排气（游侠精力 100 / 星语猎印 5）
    "auto": True,                     # 回合开始自动执行（不占玩家决策、不占行动，托管照常）
    "reset": 0,                       # 触发后资源归 N（0 = 清空）
    "seg_bonus": 1,                   # 排气后下回合低耗/连射档技能 段数 +1（补偿）
    "low_cost_max": 25,               # 低耗/连射档判定上限（与 ENERGY_HIGH.max_cost 同值 25）
    "bonus_duration": 1,              # 段数加成持续回合（深排 → 2）
    "vent_on_dodge": 15,              # 闪避成功泄压量（-15，伪装帷幕期间）
    "vent_on_mobile": 15,             # 机动技（风之疾走/风神降临）施放泄压量（-15）
    "max_delay": 1,                   # 最大可推迟回合（深排：凝神屏息延迟 1 回合释放，对齐倒地窗口）
    # 各职业差异字段说明（实际值在 core_resources.py 对应职业 vent 字段）：
    #   cls_you_xia 凝神屏息（ENERGY_VENT）：trigger 100 / auto True / reset 0 / seg_bonus 1 /
    #     seg_low_cost_max 25 / seg_duration 1 / vent_on_dodge 15 / vent_on_mobile 15 / deep_delay 1；
    #     触发后屏息窗口标记 p_buffs["breathe_window"]（持续 1 回合）供技能 cond/联动消费。
    #   cls_wild_hunter 猎印节流阀：VENT_AT=5 / VENT_AUTO=True / VENT_RECOVERY_EXTRA=1
    #     （排气余烬：排气后下回合首次命中猎印额外 +1）/ VENT_MAX_DELAY=1；
    #     星移步闪避成功猎印 -1（泄压），占卜期间泄压 -2。
}

# ============================================================
# 五、enemy_bar 挂敌身资源条（通用敌身条，v139 §5）
#   消费端：battle.py 通用敌身条（_enemy_bar_gain/_tick/_trigger/_preserve）；
#   载体：enemy.buffs 新键（如 shaken 键 = {"val", "threshold", "trigger_count", "immune_turns"}），
#   随战斗序列化、敌方单位级（多目标各自独立）；
#   核心规则：积蓄挂敌身独立于异常免疫（不吃 immune_dots/异常抗性/反弹，免疫怪唯一软解）/
#   阈值递增 ×threshold_inc 封顶 threshold_cap 防无限控 / 触发后免疫窗口 immune_turns 防连控锁 Boss /
#   阶段转换保留 phase_preserve_pct（进度遗产）。
# ============================================================
ENEMY_BAR_CFG = {
    "shaken": {  # 拳师破绽（攻线签名，云海斗士晕眩积蓄翻译；淬势者撼岳之势同型不同阈值）
        "max": 50,                 # 积蓄上限 0-50（云海 100 归一化缩放 100→50）
        "decay_per_turn": 4,       # 每回合衰减 4（100→50 同比例缩放，8→4）
        "threshold_base": 50,      # 初始触发阈值
        "threshold_inc": 1.35,     # 每次触发后阈值 ×1.35 递增
        "threshold_cap": 2.5,      # 阈值递增封顶 ×2.5（max×2.5 = 125，防无限晕）
        "auto_trigger": True,      # 自动触发（系统维护阈值，无需玩家判断/在线）
        "immune_turns": 1,         # 触发后破绽免疫期 1 回合（期内积蓄保留不衰减，免疫结束回合初自动触发）
        "phase_preserve_pct": 0.5, # 阶段转换保留 50% 积蓄（进度遗产，触发计数不清零）
        "trigger_effect": "skip_turn",  # 触发效果：敌方跳过下回合行动（破绽）
        "no_inject_on_trigger": True,   # 破绽触发当回合注入 = 0（防「晕→追颅→又满→再晕」自锁）
        # 注入源（技能表 res_gain 旁路挂载）：三连击破 +15 / 碎颅势 +15 / 旋风踢 +5/目标 / 无影连打每段 +3
        # 机制边界：不是第十种异常——不进 DOT_DEFS/DOT_MAX_TRIGGER、不吃 immune_dots、不吃异常抗性
        # Boss 霸体：按 _boss_ctrl_dur 语义时长减半至少 1 回合（初版照常触发 1 回合，待数值门禁复核）
        # 淬势者撼岳之势（SHAKEN_CFG 变体）：max 5 层 / stun_turns 1 / threshold_mult 1.3 /
        #   threshold_cap 3.0 / max_trigger 2（每场上限，对齐 DOT_MAX_TRIGGER 饱和）
    },
    "curse": {  # 暗影神谕骨噬诅咒（挂 enemy.debuffs["curse"]，净化白名单不含 curse → 天然不可驱散）
        "max": 1,                  # 诅咒唯一性：同一单位身上只挂 1 份主诅咒（换挂旧诅咒自然到期，不叠加）
        "decay_per_turn": 0,       # 不按回合衰减（由 持续回合数 递减）
        "threshold_base": 1,       # 施加即达阈值（挂上即生效）
        "threshold_inc": 1.0,      # 阈值不递增
        "threshold_cap": 1.0,      # 阈值封顶 1.0
        "auto_trigger": True,      # 自动触发（挂上即生效）
        "immune_turns": 0,         # 无免疫窗口（靠唯一性 + 续期成本限频）
        "phase_preserve_pct": 1.0, # 阶段转换保留（诅咒不因阶段清除）
        "trigger_effect": "debuff",  # 触发效果：全队对目标伤害 +20% + 全队命中 +10%（3 回合）
        "vuln": 0.20,              # 骨噬易伤：全队对受诅咒目标伤害 +20%
        "acc": 0.10,               # 骨噬命中：全队对受诅咒目标命中 +10%
        "turns": 3,                # 骨噬持续 3 回合（墓穴低语续期至 3 回合）
        # 灵魂标记（soul_mark，骷髅铺场联动）：per_layer 0.06（每层全队对目标伤害 +6%）/
        #   cap 3（最多 3 层，3 层 = +18%，与骨噬 +20% 叠加可达 +38% 集火增伤）/
        #   sync_to_undead True（标记随骷髅存活数在回合开始同步衰减，骷髅死 1 只 → 标记层 -1，保底 1 层）
    },
}

# ============================================================
# 六、counter 防御即生产（复用已有 counter_attack 段，v139 §6）
#   消费端：battle.py:5476-5498 counter_attack 段（拳师反击已接线）+ skills.py passive proc="counter_attack"；
#   守线盾卫士守护姿态升级：受击自动反击 40% 物理（不耗怒、不吃 CD、每受击至多 1 次，吃 _boss_dmg_filter 过滤）。
# ============================================================
COUNTER_CFG = {
    "guard_counter_dmg": 0.40,    # 守护姿态受击自动反击 40% 物理（普攻 4 折低值，防托管无脑站桩）
    "guard_counter_res_gain": 3,  # 反击时回怒 3（防御是产出不是空过）
    "guard_counter_flat": 1,      # 回合末保底回怒 1（_end_round，挨打+保底双渠道）
    "break_counter_dmg": 0.40,    # 破格自动衔接低伤盾击 40%（嘲讽失效/格挡被破当回合自动触发）
    "break_counter_thresh": 3,    # 受击 ≥3 触发破格衔接（顿足盾击）
    # 规则：顿足盾击与姿态反击互斥触发（嘲讽失效/破格 vs 受击），同回合至多各 1 次；
    # 圣盾格挡成功触发一次 40% 反击（守护姿态生效时，复用 block_counter 挂点）；
    # 守护誓言（T3）期间姿态反击倍率 40% → 50%。
}

# ============================================================
# 七、职业专属签名技数值（13 份方案提炼，design/new_world/参考_云海猎团职业融合_v139_*.md）
# ============================================================

# 战士·攻线狂战士：狂暴态双段普攻 + 破势斩 + 狂暴精通（狂战士样板 §2.3/§3.1）
BERSERKER_DUAL_ATTACK = {"segments": 2, "power_each": 0.70}   # 狂暴态普攻变双段 2×70% 物理
BERSERKER_ENTRY_STRIKE = 1.20    # 破势斩：入狂暴当回合自动追加 1 次 120% 物理（不占行动）
BERSERKER_MASTERY_KEEP = True    # 狂暴精通（被动）：狂暴中维持 -1 → 0，受击 -1 → 0（攻线）
BERSERKER_RAGE_POTION_GAIN = 3   # 狂暴药剂（道具）：使用后怒气 +3（狂暴中吸血翻倍 50% 由技能表承担）

# 龙裔：龙焰初击 / 龙焰形态增伤 / 吐息降耗 / 内燃（龙裔 §4.1/§4.3）
DRAGON_FORM = {
    "enter_requirement_default": 8, "enter_requirement_low": 6,  # 入龙焰门槛（默认 ≥8，战前可下调 6）
    "maintain_cost": 1, "hit_cost": 1, "hit_cost_cap": 1, "force_return": 4,
    "flame_dmg_bonus": 0.20,       # 龙焰形态下 龙息/龙爪/龙焰吐息 伤害 +20%（不作用于龙脉终曲，防 EQ 7.68 超上限）
    "entry_strike_power": 0.70,    # 「龙焰初击」入龙焰当回合自动追加 70% 真伤（不占行动）
    "breath_cost_reduce": 1,       # 龙焰形态下龙焰吐息 -5→-4
    "regen_base_blood": 2,         # 蓄能律：龙血形态 regen 1→2（1 点自然回 + 1 点蓄能律保底，龙焰形态不生效）
    "inner_fire_true_dmg": True,   # 内燃：对免疫灼烧目标，灼烧层按真伤轴结算（参照 v138 corros 先例，绕过 immune_dots）
    "inner_fire_burn_mult": 1.15,  # 内燃保留灼烧伤害 +15%（非免疫目标继续叠加）
    "inferno_breath_cond": 10,     # 龙焰吐息 ≥8 力 ×1.2 满力档（EQ 4.94 保留不动）
}

# 法师：元素架设（攻线元素聚焦/守线深度冥想，法师 §4.1/§4.2）
MAGE_FOCUS_CFG = {
    "dmg_mult": 0.40,              # 架设魔法技能增伤 +40%（乘区挂 pmult，受 SKILL_PMULT_CAP=6.0 封顶）
    "taken_mult": 0.20,            # 架设受击 +20%
    "cast_gain_extra": 1,          # 架设中施法命中充能 +1（攻线元素/奥术技命中时 element_charge +1 追加）
    "interrupt_charge_loss": 1,    # 打断只掉 1 层充能（不清零；原 50% MP 返还保留并存）
    "ctrl_break": True,            # 被眩晕/冻结/沉默 → 架设强制解除（确定性替代随机 30% 崩架）
    "stay_actions": ("defend", "use_item", "flee"),  # 架设中允许的行动（普攻/技能/换系被拦）
    "arcane_auto_per_turn": 1,     # 守线深度冥想：架设中每回合 arcane 叠层 +1（与奥术直觉叠加 = 每回合 +2）
    "burst_immune": True,          # 架设增伤不作用于耗充能大爆发（元素湮灭基础 ×1.4 但受 pmult cap 封顶）
}

# 时咒：时间凝滞 / 时间侵蚀 / 时之守护 / 时间共鸣 / 时间过载（时咒 §4.1-§4.3）
CHRONOMANCER_STASIS_CFG = {
    "enter_turn": 1,               # 进入占 1 回合（站桩吟唱，当回合不出伤）
    "enter_gain": 1,               # G1 进入凝滞态时沙 +1（预装）
    "gain_per_turn": 1,            # G2 凝滞态每回合额外 +1 沙（与 regen+1 叠加 = 每回合 +2）
    "dmg_bonus": 0.40,             # 凝滞态技能伤害 +40%（不作用于耗沙大爆发，防 EQ 5.46 超上限）
    "taken_bonus": 0.20,           # 凝滞态受击 +20%
    "interrupt_rate": 0.30,        # 崩架：受击 30% 概率打断凝滞态（沙保留，P3 不清零）
    "max_turns": 3,                # 维持上限 3 回合，第 4 回合自动解除（时间过载）
    "erosion_power": 0.60,         # 弓手 P1 翻译：凝滞态每回合自动「时间侵蚀」60% 魔法伤害（不占行动）
    "erosion_no_wake": True,       # 时间侵蚀不唤醒睡眠/停滞目标（时间属性伤害不打断自己的控制链）
    "guard_break_reduce": 0.15,    # 时之守护：打断率 30%→15% + 受击 -30%（T2，持续 2 回合）
    "resonance_gain": 2,           # 时间共鸣（T2）：90% 伤害 + 沙 +2（快弦/绷紧翻译）
    "overload_power": 3.50,        # 时间过载（T3）：350% 单体（凝滞限定，无控场纯输出峰值，-3 沙，立即结束凝滞态）
}

# 游侠：凝神屏息节流阀 + 电荷制蓄力三律 + 狙击指定层（游侠 §4.1-§4.3）
ENERGY_VENT = {
    "trigger": 100,                # 精力 =100 触发凝神屏息
    "auto": True,                  # 回合开始自动执行，不占玩家决策（云海 P3 防死锁）
    "reset": 0,                    # 触发后精力归 0
    "seg_bonus": 1,                # 下回合低耗档技能 段数 +1
    "seg_low_cost_max": 25,        # 低耗/连射档判定上限（与 ENERGY_HIGH.max_cost 同值 25）
    "seg_duration": 1,             # 段数加成持续 1 回合（深排 → 2）
    "vent_on_dodge": 15,           # 闪避成功泄压量（-15 精力）
    "vent_on_mobile": 15,          # 机动技（风之疾走/风神降临）施放泄压量
    "deep_delay": 1,               # 深排：凝神屏息可延迟 1 回合释放，段数加成持续 2 回合
}
RANGER_CHARGE_CFG = {
    "max": 3,                      # 电荷上限 0-3
    "charge_cost": 10,             # 蓄力动作精力消耗（低耗档，≤25 判定内）
    "m_base": 0.7,                 # 蓄力动作出伤基数（P1 边攒边打）
    "m_step": 0.6,                 # 每阶增伤步进（0.7/1.3/1.9）
    "snipe_m_base": 0.7,           # 狙击 M = 0.7 × (电荷+1)
    "interrupt_loss": 1,           # 受击 -1 阶（不清零，P2）
    "full_force": True,            # 电荷=3 禁止继续蓄力，强制释放（P3）
    "snipe_min": 1,                # 狙击保底门槛：电荷 ≥1 才能放（云海附 B 第 2 条平衡铁律）
    "snipe_reach": 3,              # 狙击 reach=3（可指定 rank=3 后排，任意部位任选等价翻译）
}
RANGER_SNIPE_REACH = 3             # 狙击指定层：reach=3 覆盖（可指定 rank=3 后排目标）
RANGER_SNIPE_BACK_ROW_MULT = 1.20  # 对 rank=3 后排目标伤害 ×1.2（加法联动，穿心箭/死神之箭挂载）
RANGER_HUNT_FINALE_POWER = 2.20    # 狩猎终章 P0 校准：power 1.78 → 2.20（desc 同步 220%，100 精力档重获终结意义）

# 星语者：猎印节流阀（流星陨落强制排气）+ 星轨锁定 + 星移步 + 星光庇护（星语者 §四）
STAR_LOCK_CFG = {
    "min_marks": 2,                # 星轨锁定门槛：猎印 ≥2 才可施放（签名必须带门槛，云海附 B 第 2 条）
    "cost": 1,                     # 锁定消耗 1 印
    "duration": 3,                 # 锁定持续 3 回合（目标死亡或超时自动解除）
    "cd": 4,                       # 冷却 4 回合
    "first_hit_mark_extra": 1,     # 锁定期间首次命中额外标记 +1
    "crit_mark_extra": 1,          # 对锁定目标暴击时猎印额外 +1
    "dmg_mult": 1.20,              # 对锁定目标伤害 ×1.2（星陨/命运之轮/星祭挂载，加法联动）
}
VENT_AT = 5                        # 猎印满 5 触发强制排气
VENT_AUTO = True                   # 满 5 印下回合开始自动强制释放流星陨落（系统执行、托管照常）
VENT_RECOVERY_EXTRA = 1            # 排气余烬：排气后下回合首次命中猎印额外 +1
VENT_MAX_DELAY = 1                 # 最大可推迟回合（深排：星辉祈愿延迟 1 回合释放，伤害仍享满印 cond ×1.15）
STARSTEP_CFG = {
    "dodge": 0.30,                 # 星移步：闪避 +30% 持续 2 回合
    "vent": 1,                     # 效果期间成功闪避 → 猎印 -1（泄压）
    "vent_extra": 1,               # 占卜期间泄压量 +1（-2 印）
}
ASTRO_SHIELD_CFG = {
    "pct": 0.15,                   # 星光庇护：15% 最大生命护盾（吃 shield_power，3 回合）
    "turns": 3,                    # 护盾持续 3 回合
    "dodge": 0.10,                 # 持盾期间闪避 +10%
    "break_back": 1,               # 护盾被击破时猎印 +1（星光余烬·命运在受创时仍回馈一印）
}

# 暮影：影舞态（满步自动进入 / 锁死不累积 / 3 回合退出 / 姿态内受击不清空）+ 暮刃之舞（暮影 §4.1）
SHADOW_DANCE_CFG = {
    "enter_requirement": 5,        # 影步满 5 自动进入影舞态（战内零菜单，不可手动提前——防「存一半开爆发」投机）
    "duration": 3,                 # 持续 3 回合，3 回合末自动清零退出
    "lock_accumulate": True,       # 影舞态内不累积影步（锁死，防无限续杯，爆发覆盖率限 60%）
    "hit_clear": False,            # 影舞态内受击不清空（高风险缓解窗口，姿态外受击仍清空）
    "cd_reduce": 1,                # 影舞态内 CD 全 -1（暮刃之舞被动追加，云海旋锋风缆折扣翻译）
    "extra_seg_power": 0.5,        # 影舞态内 幽影袭/幽影连刺 追加 1 段（0.5×，吃潜行乘区）
    "extra_seg_no_step": True,     # 追加段不计影步、不计满步（续杯漏洞封死，云海「旋锋态内不累积」同原则）
    "stealth_mult_apply": True,    # 影舞态内潜行乘区叠乘（破影一击 ×1.5 / 幽影刃 ×1.25，窗口上限 EQ≈7.2）
}

# 淬势者：撼岳之势（独立软控槽，淬势者 §4.2）
SHAKEN_CFG = {
    "max": 5,                      # 蓄力条：挂在敌人身上（e.buffs["shaken"] 层数 0-5），不占玩家资源位
    "stun_turns": 1,               # 满层触发「震慑」1 回合（眩晕级硬控，复用 e_buffs["stun"] 语义）
    "threshold_mult": 1.3,         # 每次触发后下次阈值 ×1.3（封顶 3.0，防无限复读，沿用 v138 律一）
    "threshold_cap": 3.0,          # 阈值递增封顶
    "max_trigger": 2,              # 每场上限：震慑触发次数达上限后不再触发（对齐 DOT_MAX_TRIGGER 饱和）
    "boss_dur_halve": True,        # Boss 控制时长减半（复用 _boss_ctrl_dur，至少 1 回合）
    "immune_soft_sole": True,      # 免疫怪唯一软解：不吃 immune_dots（独立槽，异常免疫 Boss 也能被震慑）
}

# 拳师：守线磐核（承伤即收益 + P2 蓄能律保底，拳师 §4.2）
GUARD_CORE_CFG = {
    "max": 5,                      # 磐核 0-5（新资源键，core_resource_def_by_key 注册，不受 overflow_shield 影响）
    "on_defend_hit": 1,            # 守御姿态受击 +1（受击渠道）
    "on_defend_idle": 1,           # 守御姿态未受击 +1（P2 蓄能律，敌方段结束 _end_round 前结算）
    "on_skill_hit": 1,             # 守线技能命中 +1（P1 自主）
    "discharge_base": 1.0,         # 磐岩释能：M = 1.0 + 0.7n（线性刻意，清空全部磐核）
    "discharge_per_core": 0.7,     # 每核 +0.7（3 核 3.10 / 5 核 4.50，全职业单发上限 M 4.50）
    "burst_cores": 3,              # 磐核爆发固定 3 核（M 3.10，破绽目标 ×3.60；早放高频路径）
}

# 暗影神谕：骨噬诅咒 / 灵魂标记 / 死歌三调 / 余韵 / 骸骨洪流（暗影神谕 §四）
CURSE_CFG = {
    "vuln": 0.20,                  # 骨噬诅咒：全队对受诅咒目标伤害 +20%
    "acc": 0.10,                   # 全队对受诅咒目标命中 +10%（取德鲁伊 MARK_ACC 常量）
    "turns": 3,                    # 持续 3 回合
    "unique": True,                # 唯一性：同一单位身上只挂 1 份主诅咒（换挂时旧诅咒自然到期，不叠加）
    "undispellable": True,         # 不可驱散：净化白名单不含 curse 键（_m_cleanse 按白名单弹键 → 天然免疫净化）
}
SOUL_MARK_CFG = {
    "per_layer": 0.06,             # 灵魂标记：每层全队对目标伤害 +6%
    "cap": 3,                      # 最多 3 层（3 层 = +18%，与骨噬 +20% 叠加可达 +38% 集火增伤）
    "sync_to_undead": True,        # 标记随骷髅存活数在回合开始同步衰减（骷髅死 1 只 → 标记层 -1，保底 1 层）
}
DIRGE_CFG = {
    "team_factor": 1.00,           # 死歌团队增益按全队 100% 结算
    "self_factor": 0.55,           # 施法者自身仅享 55%（歌者/神谕/暗影神谕三张支援面卡共用口径，防多人重复计数）
    "layer_decay": 0.70,           # 重奏叠层：第 2 层 ×0.70（三调互斥，换调强制结算）
    "reprisal_turns": 3,           # 死歌持续 3 回合
    "lingering_gain": 1,           # 余韵：死歌到期自动返还 +1 悼咏（换调强制结算也触发）
}
BONE_RUSH_CFG = {
    "per_skeleton": 0.90,          # 骸骨洪流：消耗全部存活骷髅，每只 90% 全体暗蚀（3 骷髅 = 270% ≈ 安魂曲 0.9 倍）
    "curse_bonus": 0.30,           # 对带诅咒（骨噬/灵魂标记）目标追加 +30% 伤害
    "cd": 5,                       # 冷却 5 回合（无骷髅时不可用，防空放）
}

# 刺客：段数三线投喂 + 链值滚雪球 + 旋锋锁 + 链点回流 + 战前终结档位（刺客 §4.1-§4.5）
ASSASSIN_HIT_FEED = {"cp": 1, "combo": 1, "poison": 1}   # 每段每线 +1（cap 分线封顶：cp 5 / combo 10 / poison 5）
ASSASSIN_SPIN_LOCK_THRESHOLD = 8    # 旋锋锁：链值 ≥8 后追加段只喂链值不再喂连击点/毒层（锁死不累积，爆发覆盖率限 60%）
COMBO_REFLOW_HP_PCT = 0.10          # 链点回流：终结伤害 ≥ 敌方 max_hp×10% 才返还链值（打空/闪避/低伤害不返还）
COMBO_REFLOW_LAYERS = 3             # 链点回流返还 3 层链值（终结·暗影绞杀 5cp 档返还 5 层）
POISON_BURST_CP = 3                 # 毒爆改版：吃 3 cp 引爆（mech poison_burst，n×atk×0.30 + 余毒虚弱）
ASSASSIN_CHAIN_DANCE_PER = 0.08     # 本命「链舞」：链值每层终结技增伤 5%→8%（只放大连段终结一轴）
ASSASSIN_CORRODE_BONUS = 0.20       # 本命「蚀骨」：毒层引爆伤害 +20%（只放大毒层引爆一轴）

# 战士·守线盾卫士：守护姿态反击 + 顿足盾击 + 坚韧抗控 + 行军囊（战士守线 §四）
STANCE_COUNTER = {
    "mult": 0.40,                  # 守护姿态受击自动反击 40% 物理（不耗怒、不吃 CD、每受击至多 1 次，吃 _boss_dmg_filter 过滤）
    "res_gain": 3,                 # 反击时回怒 3
    "flat_gain": 1,                # 回合末保底回怒 1（_end_round）
    "shield_mult": 0.40,           # 圣盾格挡成功触发一次 40% 反击（守护姿态生效时，复用 block_counter 挂点）
    "vow_mult": 0.50,              # 守护誓言（T3）期间姿态反击倍率 40% → 50%
    "break_counter_dmg": 0.40,     # 顿足盾击：破格/嘲讽失效自动衔接低伤盾击 40%
    "break_counter_thresh": 3,     # 破格阈值：受击 ≥3 触发（与姿态反击互斥，同回合至多各 1 次）
}
TENACITY_CFG = {
    "max": 3,                      # 坚韧 0-3（守线副资源，仅姿态期攒、被控才消费，非免疫）
    "consume_on_cc": 1,            # 被控时消耗 1 坚韧跳过控制（每场至多 3 次）
}

# 牧师：歌者双行折算 + 谱曲节奏 + 圣辉支援 + 圣律燃料（牧师 §3.1/§4.3/§4.4）
BARD_SELF_GAIN_FACTOR = 0.55       # 歌者/神谕/暗影神谕共用：团队增益对施法者自身仅按 55% 折算（防多人组队重复计数）
BARD_WEAPON_RHYTHM = {             # 谱曲节奏（武器型 T 值翻译，快慢械零数值惩罚，差异只在附加节奏语义）
    "mace": {"compose_gain": 1, "opening_heal": 0},   # 慢锤：谱曲 +1 共鸣（倾向满共鸣一次性大谱）
    "staff": {"compose_gain": 1, "opening_heal": 5},  # 快杖：谱曲 +1 共鸣 + 起手回合全体回复 5 体力（倾向高频小谱）
}
VOW_CFG = {
    "max": 3,                      # 圣律 0-3（守线神谕随附支援燃料条）
    "per_turn_cap": 1,             # 每回合至多 +1（治疗命中/受击，防多段多目标速满，对标云海应急整备节奏）
    "support_per_turn": 1,         # 每回合至多施放 1 件圣辉支援（防无限支援）
    "cost_per_support": 1,         # 每件支援消耗 1 圣律（不足自动跳过保护：支援整段跳过，主行动照常，绝不空过）
    "cleanse_mit": 0.05,           # 圣辉涤净：清除 1 异常 + 全队减伤 5%（1 回合，折算当量 0.08）
    "guard_mit": 0.15,             # 圣辉守护：自身 1 回合减伤 15% + 恢复 5% 生命
    "bless_atk": 0.08,             # 圣辉祝福：全队攻 +8%（1 回合）+ 自身攻 +4.4%
}
BARD_DAWN_HYMN_POWER = 3.20        # 破晓长歌（攻线 T3 伤害终结）：320% 单体圣咏魔法，-5 共鸣，命中回声 +1（EQ ≈ 4.8）

# ============================================================
# 暗影神谕：亡灵祭仪保底律（参考_云海猎团职业融合_v139_暗影神谕.md §二.5）
#   亡灵被清场连续 N 回合非治疗/受击零采集 → 保底 +1 悼咏
#   （防「亡灵清场 + 敌不aoe」两头断供，云海德鲁伊 P2 孢囊律翻译）
# ============================================================
IDLE_FLOOR_TURNS = 2

# ============================================================
# 刺客：终结阈值 DSL（参考_云海猎团职业融合_v139_刺客.md §三，战前可配 4 档）
#   终结技（res_cost cp 3/5 档）是刺客全职业唯一判断消耗点；
#   档位A 快刀(cp≥3 即终结) / 档位B 满刃(cp=5 满档) / 档位C 残血(敌HP<40%+cp≥3) / 档位D 满段(链值≥8，攻线专属)
# ============================================================
ASSASSIN_FINISHER_THRESHOLD = {
    "tiers": ["快刀", "满刃", "残血", "满段"],
    "default": "满刃",
    "desc": "战前终结阈值 DSL——A快刀(cp≥3 即终结)/B满刃(cp=5 满档)/C残血(敌HP<40%+cp≥3)/D满段(链值≥8，攻线专属)",
}
