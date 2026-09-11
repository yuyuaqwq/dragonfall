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
# 幸运 → 暴击率转化（v181.C 收口，battle.py _skill_crit_roll 消费；原 battle.py 本地 0.3/cap 0.12）
LUCK_CRIT_CONV = {"per_luck": 0.3, "cap": 0.12}

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
# DOT 分类公式（_tick_dots，契约 §2.2 + v156 分类重构）：
#   v156（2026-09-01 鱼鱼拍板）：DOT 分类型，杜绝"一刀割裂流死3只怪"——
#   flat   固定值型：吃攻击力，打谁稳定（毒）——不吃目标血，Boss 不放大
#   pct    百分比型：吃目标 max_hp%，打血牛强（流血/腐蚀）——Boss/精英打折
#   hybrid 混合型：固定值为主 + 少量百分比（灼烧）——Boss 打折只作用于 pct 部分
#   每层伤害 = (atk×atk + matk×matk + max_hp×hp×boss折扣) × 层数 × mult × (1-总抗)
#   true_dmg=True 的类型（v138.2 律四：腐蚀类）走真伤分支——绕过 _enemy_mitigate 的
#   def/mdef 削减（仍走免疫检查 + Boss 护盾层吸收），使异常流成为第二条独立输出轴。
# ============================================================
DOT_DEFS = {
    "poison": {"atk": 0.8, "matk": 0.0, "hp": 0.0, "type": "flat"},       # 毒：atk×0.8 固定值（稳定输出，不吃目标血）
    "burn":   {"atk": 0.0, "matk": 0.6, "hp": 0.005, "type": "hybrid"},   # 灼烧：matk×0.6 + max_hp×0.5%（固定为主+小百分比）
    "bleed":  {"atk": 0.05, "matk": 0.0, "hp": 0.015, "type": "pct"},   # 流血：atk×0.05 + max_hp×1.5%（百分比型，Boss打折；攻击部分低=吃目标血）
    # v138.2 律四：腐蚀（真伤轴）——百分比型真伤（Boss 打折但绕过防御，仍是对高防 Boss 的第二轴）
    "corros":  {"atk": 0.3, "matk": 0.2, "hp": 0.01, "type": "pct", "true_dmg": True},
}
# v156 Boss DOT 减免：百分比/混合 DOT 的 pct 部分在 Boss/精英战 × 该值（防"百分比无脑过 Boss"）
DOT_BOSS_PCT_MULT = 0.5
# v156 百分比部分单层上限：每刻 ≤ 目标 max_hp × 该值（防极端叠层爆炸；1% = 10 层才 10%/刻）
DOT_PCT_CAP = 0.01
DOT_BLEED_DOUBLE_HP_PCT = 0.30  # 放血：目标当前生命 <30% 时流血伤害 ×2（处决线）
DOT_ADAPT_DECAY_STEP = 0.04     # 适应回落：poison/burn 最近 2 刻未再叠层 → 耐受 -4%
DOT_RESIST_CAP = 0.95           # 总抗上限：min(0.95, dot_res + 适应 adapt)

# ============================================================
# 元素反应（12 章 §3.1 表 ↔ CLASS_MECHANICS_v153 §2；2026-09-11 两版冲突已裁决 = 以 v153 为准）
# 当前系（引爆系）× 目标印记 → 反应：
#   蒸发 = 火印(目标) + 冰(当前系) → 增伤 ×1.30，清除参与印记
#   超载 = 雷印(目标) + 火(当前系) → 转为全体 AOE，清除参与印记
#   冻结 = 冰印(目标) + 雷(当前系) → 冻结（跳过其下次行动），清除参与印记
#   感电 = 雷印(目标)满 3 层 + 雷(当前系) → 连击 +1，印记保留（不结算）
# ============================================================
ELEMENT_REACTIONS = {
    # 2026-09-11 修正（对齐 CLASS_MECHANICS_v153 §2 :385-388「元素反应」）：
    #   · 冻结原写作 ("water", "ice_mark") —— 游戏里**没有 water 元素**（三系 fire/ice/thunder），
    #     按 §2「冰印 + 雷印 = 冻结」应为 thunder → 已改（否则冻结永不触发）。
    #   · 感电按 §2 需「雷印**满 3 层**」→ 新增 min_layers 门槛（缺省 1 = 有印即反应）。
    ("ice", "fire_mark"):        {"name": "蒸发", "mult": 1.30, "clear": True, "extra": ""},
    ("fire", "thunder_mark"):    {"name": "超载", "mult": 1.00, "clear": True, "extra": "aoe"},
    ("thunder", "ice_mark"):     {"name": "冻结", "mult": 1.00, "clear": True, "extra": "freeze"},
    ("thunder", "thunder_mark"): {"name": "感电", "mult": 1.00, "clear": False,
                                  "extra": "chain", "min_layers": 3},
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
# 引爆反应表：引爆系 × 目标印记系 → 反应结算（mage_转职.md §1.0②；cond type='reaction' 引爆技接入）
#   mult  ：伤害倍率（蒸发 1.30，其余 1.00 由 extra 效果体现）
#   clear ：反应后清除目标哪系印记（"" = 不清除）
#   extra ：aoe=全体 120% 魔攻伤害 / freeze=冻结 1 刻 / chain=感电连击 +1
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
COMBO_CFG = {"cap": 10, "finish_min": 3, "per_layer": 0.05, "max_bonus": 0.40,
             # v176: 连段机制归属数据化（原 _combo_active 职业特判 cls_ci_ke+攻线）
             "class_id": "cls_ci_ke", "path": 1}
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
# 暮影：影步积攒（cls_shadow_blade，assassin.md §5.2）——v151 已删隐藏职业，本段仅留档
#   暴击命中 on_crit +1 / 闪避成功 on_dodge_success +1 / 潜行出手额外 +1 / 受击清空全部
#   （on_crit / on_dodge_success 数值原声明于 core_resources.py，已随 v181.M-R2c 退役删除）
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
    "max_layers": 3,             # 回声叠层上限（对应原 core_resources echo.max——R2c 退役；现展示表 job_guide EXTRA_RESOURCE_GUIDE echo.max 同值 3）
    "heal_per_layer": 6,         # 每层刻初始全队恢复体力
    "buff_extend_per_layer": 1,  # 增益技持续 + 回声层数 刻（P1b 退役歌类技判定后引擎不再读）
}

# ============================================================
# 分支级 resource_override：转职分支决定该分支用什么资源（核心资源 key 列表）
#   用于 battle.py 判定「该分支用什么资源」——player.class_name 仍是基础职业（如 cls_mu_shi），
#   转职歌者后仍取 faith，需要分支侧覆盖。key 集合 = EFFECT_RULES 注册 key（name/cap 单源）或
#   job_guide EXTRA_RESOURCE_GUIDE 副资源 key（resonance/echo；原 core_resources.py 注册表 R2c 退役）。
#   未命中的 (class, path) 回落职业默认单资源。
# ============================================================
BRANCH_RESOURCE_OVERRIDE = {
    # 基础法师无资源（纯蓝施法者）；攻线·元素法师 / 守线·奥秘法师 转职首获 元素亲和充能条(0-5)
    ("cls_fa_shi", 0): (),          # v176: 基础态(未转职)无资源——原 battle.py 842 cls 特判数据化
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
# 隐藏线进阶变奏留档（总纲 §7.3——v151 删隐藏线 + core_resources.py R2c 退役后无现网数据源，仅留档说明）
#   龙力 dragon_might：刻末自然回 regen=1（_turn_start 通用 regen 管线已消费，龙脉沸腾）
#   时之沙 time_sand：自动积沙 regen=1（同上）
#   悼咏 canticle：overflow_shield=True 满溢转盾（v151 已删隐藏线；原 core_resources 字段 R2c 退役）
#   禅意 zen：v151 已删（苦修士随 cls_wu_sheng 移除）；拳师蓄势（MOMENTUM_CFG）同型
#     承担“持有资源加伤”，引擎挂点 battle.py _momentum_mult
# ============================================================

# ============================================================
# v139 职业融合·通用机制数值（docs/EXTENSIBILITY_REFACTOR_PLAN_v139.md 实现基准）
#   数据驱动：职业差异原进各职业 core_resources dual_form/focus 字段（v181.M-R2c 退役删除，
#   字段值全文留档 docs/REFACTOR_v181_CLASS_MECH_ASSEMBLY.md『v139 形态层设计留档』章 §0-§6）
#   与技能表；本文件放通用机制数值 + 13 份职业方案
#   （design/new_world/参考_云海猎团职业融合_v139_*.md）提炼的职业签名技数值。
#   铁律：数值过 run_numeric_tests.py 门禁 + v133 峰值红线（≤42% 同级怪血）。
# ============================================================

# ============================================================
# v139 职业融合·通用引擎机制 —— 在役状态
#   原「6 大通用机制」（dual_form / focus / charge / vent / enemy_bar / counter）
#   的引擎侧消费端是旧 battle.py 的通用状态机，随 battle2 重构（N10）整体消失。
#   2026-09-11 复核（当前仓库状态逐项 grep）后处置：
#     · dual_form / focus / charge / vent —— **已删**（四张 CFG 一并移除）。
#       形态层未在 battle2 落位；职业差异字段早已随 core_resources.py（R2c）退役，
#       通用数值与设计口径全文留档
#       docs/REFACTOR_v181_CLASS_MECH_ASSEMBLY.md『v139 形态层设计留档』章 §0-§6。
#       现网技能不再声明这四个机制的字段（狂暴态由内容层 class_mech_proc 的
#       fury 效果 + 战意资源承载，不走通用形态机）。
#     · counter —— 见下方 BUFF_MULT 段说明。
#     · enemy_bar —— **在役**（唯一存活的通用机制；消费端 saintess_engine.gauge
#       battle_bars + 内容装配层 battle_bar_procs），见下节。
# ============================================================

# ============================================================
# enemy_bar 挂敌身资源条（通用敌身条，v139 §5）
#   消费端：saintess_engine.gauge 的 battle_bars（bar_def/bar_gain/bar_settle/bar_trigger/
#   bar_preserve）+ 内容装配层 game/services/battle_bar_procs.py；
#   载体：actor 的 effects["bar:*"] 条目（如 shaken = {"val", "threshold", "immune_until"}），
#   随战斗序列化、敌方单位级（多目标各自独立）；
#   核心规则：积蓄挂敌身独立于异常免疫（不吃 immune_dots/异常抗性/反弹，免疫怪唯一软解）/
#   阈值递增 ×threshold_inc 封顶 threshold_cap 防无限控 / 触发后免疫窗口 immune_turns 防连控锁 Boss /
#   阶段转换保留 phase_preserve_pct（进度遗产）。
# ============================================================
ENEMY_BAR_CFG = {
    "shaken": {  # 拳师破绽（攻线签名，云海斗士晕眩积蓄翻译）
        "name": "破绽",             # 展示/日志名（战报「💥破绽 32/50」）
        "max": 125,                 # 积蓄上限 = threshold_base × threshold_cap
                                    #   （原 50 与递增阈值打架：首次触发后阈值 67 > 上限 50
                                    #   → 第二次起永远触发不了，整条机制死锁）
        "decay_per_turn": 1.7,      # v153 §六：每刻衰减 1.7（小数累计，不再取整）
        "threshold_base": 50,       # 初始触发阈值
        "threshold_inc": 1.35,      # 每次触发后阈值 ×1.35 递增
        "threshold_cap": 2.5,       # 阈值递增封顶 ×2.5（50→67→90→122→125）
        "auto_trigger": True,       # 自动触发（系统维护阈值，无需玩家判断/在线）
        "immune_secs": 2.0,         # v153 §六：触发后 2 刻内不再积蓄（期内注入忽略）
        "phase_preserve_pct": 0.5,  # 阶段转换保留 50% 积蓄（进度遗产，触发计数不清零）
        "trigger_effect": "skip_turn",  # 触发效果：敌方跳过下次行动（破绽）
        "no_inject_on_trigger": True,   # 破绽触发当刻注入 = 0（防「晕→追颅→又满→再晕」自锁）
        # 注入源（技能表 shaken_gain 字段）：主力 +15 / 中档 +10~12 / 次要 +5 /
        #   多段 +3~+5 每段（per_hit）/ 普攻级 +2~+3——档位表见 v153 §六
        # 机制边界：不是第十种异常——不进 DOT_DEFS/DOT_MAX_TRIGGER、不吃 immune_dots、不吃异常抗性
        # Boss 霸体：按 _boss_ctrl_dur 语义时长减半至少 1 刻（初版照常触发 1 刻，待数值门禁复核）
        # 条状态载体 = actor.effects["bar:shaken"]（BAR_STATE_PREFIX + key）
    },
    "curse": {  # 暗影神谕骨噬诅咒（条状态 effects["bar:curse"]，净化白名单不含 curse → 天然不可驱散）
        "name": "骨噬诅咒",         # 展示/日志名
        "max": 1,                  # 诅咒唯一性：同一单位身上只挂 1 份主诅咒（换挂旧诅咒自然到期，不叠加）
        "decay_per_turn": 0,       # 不按刻衰减（由 持续刻数 递减）
        "threshold_base": 1,       # 施加即达阈值（挂上即生效）
        "threshold_inc": 1.0,      # 阈值不递增
        "threshold_cap": 1.0,      # 阈值封顶 1.0
        "auto_trigger": True,      # 自动触发（挂上即生效）
        "immune_secs": 0.0,        # 无免疫窗口（靠唯一性 + 续期成本限频）
        "phase_preserve_pct": 1.0, # 阶段转换保留（诅咒不因阶段清除）
        "trigger_effect": "debuff",  # 触发效果：全队对目标伤害 +20% + 全队命中 +10%（3 刻）
        "vuln": 0.20,              # 骨噬易伤：全队对受诅咒目标伤害 +20%
        "acc": 0.10,               # 骨噬命中：全队对受诅咒目标命中 +10%
        "turns": 3,                # 骨噬持续 3 刻（墓穴低语续期至 3 刻）
        # 灵魂标记（soul_mark，骷髅铺场联动）：per_layer 0.06（每层全队对目标伤害 +6%）/
        #   cap 3（最多 3 层，3 层 = +18%，与骨噬 +20% 叠加可达 +38% 集火增伤）/
        #   sync_to_undead True（标记随骷髅存活数在刻开始同步衰减，骷髅死 1 只 → 标记层 -1，保底 1 层）
    },
}

# ============================================================
# v176 从 battle.py 下沉的增益倍率映射表（原硬编码在战斗引擎）
#   效果 effect → (修正属性, 倍率/加成)；加新 buff = 加一行，零改引擎
# ============================================================
# 增益倍率映射：effect -> (修正属性, 倍率/加成)
BUFF_MULT = {
    "atk_up":         ("atk", 1.30),
    "atk_up_strong":  ("atk", 1.75),
    "echo_bless":     ("atk", 1.05),   # v97.4 回音洞穴祝福：本场攻击 +5%（一次性，探索事件写入）
    "matk_up":        ("matk", 1.50),   # #244a：与技能描述 matk+50% 对齐（原 1.35 与 desc 不符）
    "matk_up_strong": ("matk", 1.80),
    "matk_up_pot":    ("matk", 1.30),   # 9.3 鲛人之泪：本刻魔攻 +30%
    "def_up":         ("def", 1.45),
    "spd_up":         ("spd", 1.40),
    "crit_up":        ("crit", 0.20),      # 暴击率 +20%
    # v173.3 意见#95（鱼鱼拍板 B 方案）：命中 buff——鹰眼锁定 desc「命中 +15%」落地
    # precise 是敌方闪避抵消率（_target_dodge_check my_hit），加法并入词条精准
    "hit_up":         ("precise", 0.15),
    # v101.28f 药水强度分档（名字不同效果不同的真实落地：战吼/龙力 +40%、蛮力 +20%、风灵 +20%、致命 +30%、锐目 +15%）
    "atk_up_big":     ("atk", 1.40),
    "atk_up_small":   ("atk", 1.20),
    "spd_up_small":   ("spd", 1.20),
    "crit_up_small":  ("crit", 0.15),
    "crit_up_big":    ("crit", 0.30),
    # v101.28b 食物增益（战斗料理线：数值约为药水 1/3，价格低+带战斗外恢复）
    "food_atk_up":    ("atk", 1.10),
    "food_def_up":    ("def", 1.15),
    "food_spd_up":    ("spd", 1.12),
    "food_crit_up":   ("crit", 0.08),
    "food_matk_up":   ("matk", 1.10),
    "food_spd_up_small": ("spd", 1.10),  # v105 M16 精灵果酱：战斗中本场速度+10%（策划 19:129）
    "mon_atk_up":     ("atk", 1.30),
    "mon_atk_up_strong": ("atk", 1.70),
    "mon_def_up":     ("def", 1.40),
    "mon_atk_down":   ("atk", 0.70),   # v51 挫志怒吼：敌方攻击 -30%
    # v180F 清2a：magic_resist 药剂（龙鳞/深渊）此前挂 buff 无消费端（引擎魔免读 magic_reduce
    # stat）→ 空转。挂 magic_reduce 加法（cap 由 _apply_buffs PCT_CAPS 管）
    "magic_resist":   ("magic_reduce", 0.15),
}

# v104 M02 P1-4：团队增益 effect=xx_all → 施放者自身有效 buff 键（与 instance.py buff_effects 同口径）
TEAM_BUFF_KEYS = {
    "def_all": "def_up", "atk_all": "atk_up",
    "matk_all": "matk_up_strong", "crit_all": "crit_up", "spd_all": "spd_up",
}


# ============================================================
# v181 P0-A 从 game/engine.py 下沉的三张纯数据表（迁移来源：v181 架构审计 P0-A，
# engine.py 顶部 import 保持对外接口 E.TIER_GROWTH / E.BRANCH_BONUS /
# E.BRANCH_BONUS_BY_CLASS / E.MECH_STACK_MAX，行为零变化）
# ============================================================

# 转职成长加成（tier 0-3 → 0/15%/30%/50%）
TIER_GROWTH = {0: 1.0, 1: 1.15, 2: 1.30, 3: 1.50}
# v25 转职分支属性倾向（左=攻击/速度，右=防御/生命）
# v156 职业×分支差异化（计划 §3）：每职业攻线/守线独立加成；
# 旧结构 {1:..., 2:...} 作为默认回退（未配置职业用通用档，向后兼容）
BRANCH_BONUS = {
    1: {"atk": 1.06, "spd": 1.04},   # 左：进攻路线（默认回退）
    2: {"def": 1.08, "hp": 1.06},    # 右：防御路线（默认回退）
}
# v156 职业×分支差异化表（计划 §3 权威）：class_name → {evolve_path: {属性: 倍率}}
# key 用职业 ID（cls_zhan_shi 等，与 C.CLASSES 一致）；中文名会在查询处 resolve 成 ID
BRANCH_BONUS_BY_CLASS = {
    "cls_zhan_shi": {
        1: {"atk": 1.10, "spd": 1.04, "hp": 0.95},   # 狂战士：攻高但血少
        2: {"def": 1.14, "hp": 1.10, "atk": 0.95},   # 盾卫士：防高但攻低
    },
    "cls_fa_shi": {
        1: {"matk": 1.12, "hp": 0.92},   # 元素使：魔攻高但脆
        2: {"matk": 1.08, "mp": 1.10},   # 奥术学者：魔攻+蓝量
    },
    "cls_you_xia": {
        1: {"atk": 1.10, "spd": 1.06},   # 森语者
        2: {"spd": 1.12, "atk": 1.06},   # 风行者
    },
    "cls_mu_shi": {
        1: {"matk": 1.12, "hp": 0.95},   # 死灵祭司
        2: {"matk": 1.06, "mdef": 1.10}, # 神谕者
    },
    "cls_ci_ke": {
        1: {"atk": 1.12, "crit": 0.04},  # 影舞者
        2: {"atk": 1.08, "hp": 1.04},    # 毒刃者
    },
    "cls_wu_seng": {
        1: {"atk": 1.10, "spd": 1.04},   # 格斗士
        2: {"def": 1.12, "hp": 1.10, "atk": 0.95},  # 磐石行者
    },
    "cls_shi_ren": {
        1: {"matk": 1.08, "mp": 1.10},   # 咏叹者
        2: {"matk": 1.08, "hp": 1.06},   # 挽歌者
    },
}

# ============================================================
# v59 叠层上限（防数值爆炸：一场战斗叠 25 层金身=无敌、灼烧 10 层=烧死 Boss）
# 层数封顶后依然能用爆发技能一次性清空，只是限制无限滚雪球。
# ============================================================
MECH_STACK_MAX = {
    "burn": 5,     # 灼烧：5 层 = 每刻 15% 生命（结算后逐层衰减消散）
    "poison": 5,   # 毒层：5 层 = 每刻 25% 生命（结算后逐层衰减消散）
    "rage": 5,     # 狂暴：5 层 = +60% 伤害
    "shadow": 5,   # 影袭：5 层 = +60% 伤害
    "chi": 5,      # 气力：5 点 = +60% 伤害
    "judge": 5,    # 审判：5 层 = +75% 伤害
    "mark": 5,     # 标记：5 层 = +100% 伤害
    "wind": 3,     # 风印：3 层 = 4 连击（再多连击刷屏）
    "iron": 5,     # 金身：5 层 = 减伤 20%
    "shield": 5,   # 圣盾：5 层减伤
    "bless": 10,   # 神恩：10 层护盾
    "arcane": 5,   # 奥术充能：5 层（共鸣爆发前置，叠满 5 层=每层 +15% 爆发）
    "spellblade": 5,  # v87 魔剑士·魔能：5 层（叠层→爆发节奏）
    "zhan_yi": 10,    # v151 战士战意：0-10 叠层（持有即生效，从不消耗）
    "lian_duan": 10,  # v151 刺客连段：0-10 命中计数（miss/闪避归零）
}



# ============================================================
# v181 P2E（P2E-P3a）：MECH_CFG 机制单表——战斗机制参数按「机制名」聚合
#   北极星：不做"40 个 CFG 搬 data 目录"，而是收敛成 {机制名: {数值}} 单表，
#   消费点按机制名查（battle.py/core 状态机/engine 全部改查 MECH_CFG[机制键]）。
#   数值以现状为准一字不改（P2E 与 P2-C 同款"以现状为准"）；本表只是聚合寻址。
#   ⚠️ 不入表（各自域原位保留）：
#     - TIER_GROWTH / BRANCH_BONUS / BRANCH_BONUS_BY_CLASS（属性成长公式段，engine 读）
#     - QUALITY_UPGRADE_* / MASTERPIECE_CHANCE（economy 锻造域，C. 聚合导出）
#     - SHADOW_STEALTH_DMG_MULT（技能名→倍率 内容名键表，待迁 skills 条目 stealth_mult 字段，另行 TODO）
#   顶层旧名保留 = 兼容层（P3b 读点迁移完成后仅 tests/scripts 未同步前防炸；P3c 移除或保留）
# ============================================================
MECH_CFG = {
    # ---- 机制键表（通用表直接收编，键名即机制）----
    "dot": {
        **DOT_DEFS,
        "boss_pct_mult": DOT_BOSS_PCT_MULT,
        "pct_cap": DOT_PCT_CAP,
        "bleed_double_hp_pct": DOT_BLEED_DOUBLE_HP_PCT,
        "adapt_decay_step": DOT_ADAPT_DECAY_STEP,
        "resist_cap": DOT_RESIST_CAP,
    },
    "mech_stack": {
        "bonus": MECH_STACK_BONUS,
        "whitelist": MECH_STACK_WHITELIST,
        "max": MECH_STACK_MAX,
    },
    "buff": {
        "mult": BUFF_MULT,
        "team_keys": TEAM_BUFF_KEYS,
    },
    "element": {
        "reactions": ELEMENT_REACTIONS,
        "reaction_table": REACTION_TABLE,
        "marks_max": ELEMENT_MARKS_MAX,
        "same_cast_extra_charge": ELEMENT_SAME_CAST_EXTRA_CHARGE,
        # ELEMENT_MARK_GAIN_PER_HIT 已随 P2E-P3a 删（battle.py 仅 import 死链路，零读点）
    },
    "crit": {
        "lucky_chance": LUCKY_CRIT_CHANCE,
        "lucky_mult": LUCKY_CRIT_MULT,
        "luck_conv": LUCK_CRIT_CONV,
        "multi_hit_first_only": MULTI_HIT_CRIT_FIRST_ONLY,
        "full_hp_mechs": MECH_FULL_HP_CRIT,
        "frozen_mult": MECH_FROZEN_MULT,
        "combo_mechs": MECH_COMBO_STACKS,
    },
    "ctrl": {
        "mechs": CONTROL_MECHS,
        "skill_cc_whitelist": SKILL_CC_WHITELIST,
        "proc_groups": MECH_PROC_GROUPS,
        "stat_passives": MECH_STAT_PASSIVES,
    },
    "boss": {
        "attack_mults": BOSS_ATTACK_MULTS,
    },
    "enemy_bar": ENEMY_BAR_CFG,
    # ---- 机制键（职业化 CFG 收敛后按机制命名；原 dict 值原样搬）----
    "assassin_combo": {
        **COMBO_CFG,
        "on_crit_gain": ASSASSIN_ON_CRIT_GAIN,
        "on_take_hit_penalty": ASSASSIN_ON_TAKE_HIT_PENALTY,
    },
    "shadow_step": SHADOW_STEP_CFG,
    "echo": ECHO_CFG,
    "full_tension": ENERGY_HIGH,
    "blood_debt_gain": RAGE_GAIN_HP_SCALE,
    "branch_resources": BRANCH_RESOURCE_OVERRIDE,
    "chi_hold_dmg": MOMENTUM_CFG,
}


def mech_cfg(mech: str) -> dict:
    """MECH_CFG 查表辅助（core 状态机 _battle_cfg 同形态推广）：无配置 = 默认不启用。"""
    return MECH_CFG.get(mech, {})
