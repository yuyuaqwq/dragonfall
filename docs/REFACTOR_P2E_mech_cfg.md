# P2-E battle_config 职业命名 CFG → MECH_CFG 单表收敛 — 只读侦察 + 方案设计（wt_p2e）

> 任务：REFACTOR_PLAN_v181.md P2-E（北极星 ARCHITECTURE_TARGET_STATE_v181.md §P2E：**不做"40 个 CFG 搬 data 目录"，而是收敛成 `MECH_CFG = {机制名: {数值}}`，消费点按机制名查**）。
> 本文档为**只读侦察 + 方案设计**（未改任何 game/ 代码；git 干净）。落地执行批次以此为依据。
> 侦察基线：master `329989c`（wt_p2e 分支同点），worktree w6。`game/data/battle_config.py` 774 行 **95 个常量**（审计报告 2 §四 说 701 行/90 个，现状已多 5 个：v181 P0-A 下沉了 TIER_GROWTH/BRANCH_BONUS/BRANCH_BONUS_BY_CLASS/MECH_STACK_MAX + v176 BUFF_MULT/TEAM_BUFF_KEYS 等）。
> 铁律：行为零变化；每步 py_compile + 单测绿；data 纯数据零函数；core 通用执行器 + 注册表；battle 纯编排零内容名。删任何常量须人确认（本批次只出清单）。

---

## 0. TL;DR（给执行批次的一句话）

battle_config 的 **95 个常量按"消费面"分三类**：
- **52 个有真实代码消费点**（§2.1 全表：战斗引擎 battle.py / core 状态机 battle_bars·battle_modes / engine.py / 命令层 economy / scripts 数值仿真 / tests），其中有 17 个是**通用引擎表**（DOT_DEFS/BUFF_MULT/MECH_*_*/ELEMENT_*/REACTION_TABLE/BOSS_ATTACK_MULTS/CONTROL_MECHS 等，本身就以**机制名/效果名**为键，是 MECH_CFG 可直接收编的骨架）。
- **41 个全仓零引用死表**（§2.3 全表，含全部 6 个 ASSASSIN_*、5 个 BERSERKER_*、3 个 RANGER_SNIPE_*、STAR_* 4 件套、暗影神谕 4 件套等——数值**从未被 import 也从未被字符串引用**，纯"设计稿留档"）。
- **2 个仅被注释提到**（GUARD_CORE_CFG / RANGER_CHARGE_CFG —— 引擎里该机制以**字面量**实现，注释里引用已死常量名）。

死因分 5 型（§3.3）：**① 机制以字面量/effect 在 battle_mech/skills 实装**（BONE_RUSH_CFG 0.9×n、CURSE_CFG turns=8、SOUL_MARK_CFG 6%/cap3、STAR_LOCK_CFG 0.12）；**② 双源并存另一份被读的表**（SHAKEN_CFG↔ENEMY_BAR_CFG.shaken、COMBO_CFG 各字段↔classes.py cls_ci_ke.combo dict——后者也零读=双死源）；**③ 职业专属默认值被 core_resources/classes 职业字段取代**（DRAGON_FORM/MAGE_FOCUS_CFG/CHRONOMANCER_STASIS_CFG/SHADOW_DANCE_CFG/ENERGY_VENT → 引擎只读 `player.dual_form/focus/vent`）；**④ 机制整体移除后遗留**（ZEN_HOLD_CFG 随 v151 删 cls_wu_sheng 苦修士禅意；HUNT_MARK_CRIT_EXTRA 随 v151 删星语猎印暴击）；**⑤ 分支/职业文案残留**（BARD_BRANCHES 三个中文分支名现网 CLASSES 数据中不存在 → 消费函数恒 False 死判定）。

**MECH_CFG 落地三步走**（§5）：不先做"大搬家"。先做 §4.1 的**纯死表清理**（41+2 个：除 ZEN_HOLD_CFG 外全部零行为风险，删前过数值复核清单），再做 §4.2 **双源归一**（SHAKEN→ENEMY_BAR.shaken、COMBO_CFG↔classes.combo 收敛到 classes、BARD_BRANCHES 死判定删除），最后 §4.3 把**仍活的机制参数**（MOMENTUM_CFG/ECHO_CFG/ENERGY_HIGH/RAGE_GAIN_HP_SCALE/SHADOW_STEP_CFG/COMBO_CFG 存活字段/ENEMY_BAR_CFG/DUAL_FORM_CFG/FOCUS_CFG/VENT_CFG/CHARGE_CFG…）按机制名收进 `MECH_CFG`。整个 P2-E 执行期**不改任何行为**（死表本来就不触发；双源归一后仍读同一份值；MECH_CFG 只是命名/寻址变化）。

---

## 1. 目标与范围

### 1.1 目标态（北极星 §P2E 判定标准）

1. **机制名 vs 职业名**：data/battle_config.py 顶层常量命名按**机制**（"这个字段配的到底是什么行为"），不是按职业/流派（BARD_/ASSASSIN_/BERSERKER_/RANGER_/DRAGON_/CHRONOMANCER_…）。判据：数值放进 `MECH_CFG[机制名]` 后，新职业/新技能想复用同一机制时**不用改名字典、不用改 battle.py**。
2. **消费点按机制名查**：battle.py/core 的读法从 `from .data.battle_config import BERSERKER_DUAL_ATTACK` 变为 `MECH_CFG["fury_dual_attack"]`（或 `mech_cfg("fury_dual_attack")`），内容名（职业 id/分支中文名/技能名）不出现在引擎。
3. **无双源**：同一机制的数值只有一处权威。现状三类并存必须收敛（§3.2：classes.py dict / core_resources.py dict / battle_config.py CFG 三处）。
4. **无死表**：data 里不存在零引用常量（死表是"设计稿留档"，掩盖"实装其实在字面量里"的事实，调数值时改错地方）。

### 1.2 收编范围（95 个常量全量）

- **收编进 MECH_CFG（机制单表）**：52 个被消费常量中**仍以"职业名"命名**的 CFG/标量（§3.4/§4.2 B 组 12 个职业化命名收编 + A 组 29 个已是机制键的通用表直接收编，键名不变）。
- **留在 battle_config 或迁 core/constants**：引擎刻度/公式参数（本文件目前无 BASE_DELAY/ACT_TICK/SPD_REF——那些在 battle.py 模块级，属 P2-B 范围；本文件内的引擎固有参数实为 DOT_BOSS_PCT_MULT/DOT_PCT_CAP/DOT_RESIST_CAP/QUALITY_* 等"横向全局数值"——归 `ENGINE_CFG` 段或按机制进 MECH_CFG，见 §4.3 尾注）。
- **删除候选（先清单后确认）**：41 死表 + 2 注释-only（§2.3/§3.3），分风险级。

### 1.3 非目标（红线）

- 不改任何 game/ 代码（本文档侦察基线）；执行批次才动。
- 不改任何数值/日志/行为——P2-E 是**寻址与归属重构**，数值以现状为准（与 P2-C 同款"数值有差异时以现状为准写进数据表"）。
- 不把 MECH_CFG 的"机制名"字典当作新机制族注册表（那归 P2-D proc / MECH_EFFECTS）；本表只放**参数数值**，不放 handler/函数。
- 不搬 classes.py 的职业描述字段（evolve/desc/icon 等）——只收敛**机制参数**字段。

---

## 2. 侦察发现：95 常量消费统计

### 2.1 消费统计总表（AST + 全仓代码扫描，含 tests/scripts）

扫描方法：AST 提取 battle_config.py 全部 95 个顶层大写赋值常量；全仓 758 个 .py（跳过 .git/__pycache__/_archive_unused）逐行词边界匹配 + **注释剥离复扫**（区分代码引用 vs 注释提及）；字符串字面量引用纳入（防"数值以技能字段/注释形式硬编码"漏判）。

| 类别 | 数量 | 说明 |
|---|---|---|
| A. 真实代码消费（非注释） | **52** | battle.py / engine.py / core 状态机 / 命令层 / scripts / tests 至少一处 import+Name 读取 |
| B. 仅注释提及 | **2** | GUARD_CORE_CFG / RANGER_CHARGE_CFG（引擎用字面量，注释里引用了死名） |
| C. 全仓零引用死表 | **41** | 定义行之外（含注释/字符串）无任何出现 |

> 与审计报告 2 §四"90 常量仅 7 个被 import 引用、~30 个零消费"的差异：审计口径只数了 `from game.data import *` 聚合层（data/__init__.py 只 re-export 18 个）+ 顶层 import，漏了 **battle.py 顶部直连 import（36 个常量）**、函数内延迟 import（ECHO_CFG/ENEMY_BAR_CFG 等）、core 状态机延迟 import、scripts/tests 直读。本次全仓逐词扫描修正为 52/2/41。

**52 个真实消费常量明细**（消费文件:行区 → 引擎函数，§4.3 收敛归属）：

| # | 常量 | 消费点（文件:函数@行） | 收敛机制归属 |
|---|---|---|---|
| 1 | DOT_DEFS | battle.py `_tick_actor_dots@8652`、`_th_actor_dot@524`；numeric_lib/player.py dot_dps | **dot**（机制键表，键名保留） |
| 2 | DOT_BLEED_DOUBLE_HP_PCT | battle.py `_tick_actor_dots@8801` | dot.bleed_double_hp_pct |
| 3 | DOT_ADAPT_DECAY_STEP | battle.py `_tick_actor_dots@8869` | dot.adapt_decay_step |
| 4 | DOT_RESIST_CAP | battle.py `_tick_actor_dots@8756` | dot.resist_cap |
| 5 | DOT_BOSS_PCT_MULT | battle.py `_tick_actor_dots@8769`；numeric_lib | dot.boss_pct_mult |
| 6 | DOT_PCT_CAP | battle.py `_tick_actor_dots@8770`；numeric_lib | dot.pct_cap |
| 7 | MECH_STACK_BONUS | battle.py `_mech_stack_bonus@7269` | **mech_stack**（机制键表） |
| 8 | MECH_STACK_WHITELIST | battle.py `_apply_mech_gain@7345` | mech_stack.whitelist |
| 9 | MECH_STACK_MAX | engine.py `mech_stack_gain@114` | mech_stack.max |
| 10 | MECH_FULL_HP_CRIT | battle.py `_skill_apply_tags_marks@6476`、`_skill_crit_roll@7041` | mech_full_hp_crit（机制键表） |
| 11 | MECH_FROZEN_MULT | battle.py `_skill_assemble_mults@6756` | mech_frozen_mult |
| 12 | MECH_COMBO_STACKS | battle.py `_skill_assemble_mults@6768` | mech_combo_stacks |
| 13 | MECH_PROC_GROUPS | battle.py `_do_player_skill@4391`、`_skill_passive_dmg_bonus@6926`、`_apply_mech_effect@7375` | mech_proc_groups |
| 14 | MECH_STAT_PASSIVES | battle.py `_skill_passive_dmg_bonus@6976` | mech_stat_passives |
| 15 | CONTROL_MECHS | battle.py `_apply_mech_effect@7435`；potion_effects eff_trap | ctrl.control_mechs |
| 16 | SKILL_CC_WHITELIST | battle.py `_skill_hit_settle@6357` | ctrl.skill_cc_whitelist |
| 17 | BOSS_ATTACK_MULTS | battle.py `_enemy_stats@8229` | **boss**（机制键表） |
| 18 | ELEMENT_REACTIONS | engine.py `element_reaction@30` | **element**（机制键表） |
| 19 | REACTION_TABLE | battle.py `_reaction_table_resolve@2802`；potion_effects eff_apply_mark/eff_reaction | element.reaction_table（与 ELEMENT_REACTIONS 双表——P1 遗留，建议并表） |
| 20 | ELEMENT_MARKS_MAX | battle.py `_elem_mark_max@2732`；battle_mech 6 处 mark handler | element.marks_max |
| 21 | ELEMENT_MARK_GAIN_PER_HIT | battle.py 顶部 import（实际读点= _elem_mark_apply 内层 min cap 用 ELEMENT_MARKS_MAX；此常量疑似只剩 import 死链路） | element.mark_gain_per_hit ⚠️ 复核 |
| 22 | ELEMENT_SAME_CAST_EXTRA_CHARGE | battle.py `_last_element_set@2763` | element.same_cast_extra_charge |
| 23 | LUCKY_CRIT_CHANCE | battle.py `_skill_crit_roll@7049` | crit.lucky_chance |
| 24 | LUCKY_CRIT_MULT | battle.py `_skill_seg_damage@7137` | crit.lucky_mult |
| 25 | LUCK_CRIT_CONV | battle.py `_skill_crit_roll@7010` | crit.luck_conv |
| 26 | MULTI_HIT_CRIT_FIRST_ONLY | battle.py `_player_skill@7227` | crit.multi_hit_first_only |
| 27 | BUFF_MULT | battle.py `_apply_buffs@8171`；battle_mech 4 handler；potion_effects | **buff**（机制键表） |
| 28 | TEAM_BUFF_KEYS | battle.py `_skill_buff@6240` | buff.team_keys |
| 29 | RAGE_GAIN_HP_SCALE | battle.py `_on_taken_rewards@10945` | rage_gain_hp_scale（血债怒火=机制名） |
| 30 | ENERGY_HIGH | battle.py `_energy_high_crit@2700`、`_skill_crit_roll@7016`、`_tailwind_regen_bonus@8982` | full_tension（满弦机制，字段阈值 80/0.10/25） |
| 31 | MOMENTUM_CFG | battle.py `_momentum_mult@2674` | chi_hold_bonus（蓄势/气持有加伤——拳师攻线；机制=按资源持有比例加伤，与 zen 同族） |
| 32 | COMBO_CFG | battle.py `_combo_active@2591`(class_id/path)、`_combo_add@2598`(cap)、`_combo_finish_min@2640`(finish_min)、`_combo_dmg_mult@2658`(per_layer/max_bonus) | assassin_combo（刺客连段——class_id/path 字段是"归属职业"数据，机制键=连段链值） |
| 33 | ASSASSIN_ON_CRIT_GAIN | battle.py `_on_crit_resource@5169` | assassin_combo.on_crit_gain |
| 34 | ASSASSIN_ON_TAKE_HIT_PENALTY | battle.py `_on_taken_rewards@10958` | assassin_combo.on_take_hit_penalty |
| 35 | SHADOW_STEP_CFG | battle.py `_on_crit_resource@5164` | shadow_step（影步积攒——stealth_extra 潜行额外） |
| 36 | SHADOW_STEALTH_DMG_MULT | battle.py `_skill_crit_roll@7046`；battle_conds `_c_stealth@453` | stealth_dmg_mult（潜行乘区——技能名→倍率 表，技能名是内容名 → 建议搬 skills.py 技能条目 stealth_mult 字段） |
| 37 | ECHO_CFG | battle.py `_echo_add@2771`、`_th_echo_heal@464`、`_skill_buff@6250` | echo（回声驻留叠层——max_layers/heal_per_layer/buff_extend_per_layer） |
| 38 | BRANCH_RESOURCE_OVERRIDE | battle.py `_branch_keys@1735`、`_is_element_mage@1775`、`_is_bard_skill@2785` | branch_resource_override（分支资源所有权表——机制=分支资源解析） |
| 39 | BARD_BRANCHES | battle.py `_is_bard_skill@2785-2799`（**恒 False 死判定**，现网无这三个分支名） | ⚠️ 死代码入口，删除后 _is_bard_skill 可整体退役（见 §3.1） |
| 40 | DUAL_FORM_CFG | core/battle_modes.py `_battle_cfg@22`（默认值 fallback 字典） | dual_form 引擎默认值（机制=双形态） |
| 41 | FOCUS_CFG | core/battle_modes.py `_battle_cfg@22`（同） | focus 引擎默认值（机制=专注架设） |
| 42 | VENT_CFG | core/battle_modes.py `_battle_cfg@22`（同） | vent 引擎默认值（机制=排气节流） |
| 43 | CHARGE_CFG | core/battle_bars.py `_battle_cfg@22`（同） | charge 引擎默认值（机制=蓄力三律） |
| 44 | ENEMY_BAR_CFG | core/battle_bars.py `_battle_cfg@22`；battle.py `_turn_start@9276`(trigger_effect) | enemy_bar（机制键表：shaken/curse 子键 = 破绽/诅咒条） |
| 45 | TIER_GROWTH | engine.py `player_base_stats@132`；commands/world.py | **成长公式表**（非职业机制——留/归 data 同段即可） |
| 46 | BRANCH_BONUS | engine.py `player_base_stats@140`（默认回退档） | branch_bonus（v156 表默认回退） |
| 47 | BRANCH_BONUS_BY_CLASS | engine.py `player_base_stats@140` | branch_bonus_by_class（职业×分支属性表——键是职业 id，归 classes 数据域） |
| 48 | QUALITY_UPGRADE_CHANCE | commands/economy.py `craft@2506` | craft_quality（锻造品质——非战斗机制，属 economy 数据域） |
| 49 | QUALITY_UPGRADE_MASTER_BONUS | commands/economy.py `craft@2505` | 同上 |
| 50 | QUALITY_UPGRADE_COST | commands/economy.py `craft@2507` | 同上 |
| 51 | MASTERPIECE_CHANCE | commands/economy.py `craft@2526` | 同上 |
| 52 | ZEN_HOLD_CFG | tests/test_v1302f2_engine_fix.py:8（唯一引用=测试读断言 battle_config 值） | ⚠️ v151 删苦修士后引擎零读；**测试 148-155 仍断言该常量数据**——删常量须同步改测试（风险低，机制本身已删） |

### 2.2 引擎固有参数（横向全局数值，非职业机制）

| 常量 | 归属判断 |
|---|---|
| DOT_BOSS_PCT_MULT / DOT_PCT_CAP / DOT_RESIST_CAP / DOT_ADAPT_DECAY_STEP / DOT_BLEED_DOUBLE_HP_PCT | DOT 体系全局规则 → 归 MECH_CFG["dot"] 子键（它们本来就随 DOT_DEFS 同消费段） |
| MULTI_HIT_CRIT_FIRST_ONLY / LUCK_CRIT_CONV / LUCKY_CRIT_* | 暴击体系全局规则 → MECH_CFG["crit"] |
| BOSS_ATTACK_MULTS | Boss 乘区全局表 → MECH_CFG["boss_attack_mults"]（键名即机制） |
| QUALITY_UPGRADE_* / MASTERPIECE_CHANCE | 锻造品质（economy 域，非战斗）→ 建议**迁出 battle_config** 到 economy 数据段（或保持原位不参与 MECH_CFG） |
| TIER_GROWTH / BRANCH_BONUS / BRANCH_BONUS_BY_CLASS | 属性成长公式表（engine 消费）→ 本就在 battle_config 的 v181 P0-A 下沉段，非职业机制 CFG，**不参与 MECH_CFG 收敛**（§4.3 尾注） |

> 引擎刻度常量（SPD_REF/BASE_DELAY/ACT_TICK/CAST_* 等）**不在本文件**——它们还是 battle.py 模块级常量，属 P2-B（battle.py 引擎常量 → core/constants.py），P2-E 不碰。本文件里真正的"引擎刻度"只有 dot 抗性 cap 这类横向规则，已按上面归 dot/crit 机制子键。

### 2.3 41 死表全表（全仓零引用，含注释/字符串）

`ASSASSIN_CHAIN_DANCE_PER` `ASSASSIN_CORRODE_BONUS` `ASSASSIN_FINISHER_THRESHOLD` `ASSASSIN_HIT_FEED` `ASSASSIN_SPIN_LOCK_THRESHOLD`
`ASTRO_SHIELD_CFG` `BARD_DAWN_HYMN_POWER` `BARD_SELF_GAIN_FACTOR` `BARD_WEAPON_RHYTHM`
`BERSERKER_DUAL_ATTACK` `BERSERKER_ENTRY_STRIKE` `BERSERKER_MASTERY_KEEP` `BERSERKER_RAGE_POTION_GAIN`
`BONE_RUSH_CFG` `CHRONOMANCER_STASIS_CFG` `COMBO_REFLOW_HP_PCT` `COMBO_REFLOW_LAYERS` `COUNTER_CFG`
`CURSE_CFG` `DIRGE_CFG` `DRAGON_FORM` `ENERGY_VENT` `HUNT_MARK_CRIT_EXTRA` `IDLE_FLOOR_TURNS` `MAGE_FOCUS_CFG`
`POISON_BURST_CP` `RANGER_HUNT_FINALE_POWER` `RANGER_SNIPE_BACK_ROW_MULT` `RANGER_SNIPE_REACH`
`SHADOW_DANCE_CFG` `SHAKEN_CFG` `SOUL_MARK_CFG` `STANCE_COUNTER` `STARSTEP_CFG` `STAR_LOCK_CFG`
`TENACITY_CFG` `VENT_AT` `VENT_AUTO` `VENT_MAX_DELAY` `VENT_RECOVERY_EXTRA` `VOW_CFG`

---

## 3. 职业命名 CFG 逐个侦察（机制归属 / 消费点 / 三处并存 / 收敛难度）

### 3.1 职业命名但引擎逻辑是**死的**（删除即可，零行为变化）—— 先清这批

| 常量 | 死因证据（文件:行） | 处置 |
|---|---|---|
| BARD_BRANCHES（已消费但恒 False） | battle.py `_is_bard_skill@2785` docstring 自认：**BARD_BRANCHES(吟游诗人/灵魂歌者/黎明颂者) 为 v153 前旧分支名，现网 classes.py 牧师 evolve_branches 无一名命中（神谕者/死灵祭司…）→ 恒 False**。回声判定 v181 已改读 BRANCH_RESOURCE_OVERRIDE 资源键（`_echo_add@2774` 已删 BARD_BRANCHES 特判）。_is_bard_skill 目前仅 battle.py `_skill_hit_settle@4514` 一处调用（random<0.20 伴奏增益——恒不触发） | 删 BARD_BRANCHES + _is_bard_skill 整体退役（调用点改恒 False 常量或删段）。**风险中**：4514 分支现网从不执行，删后等价 |
| HUNT_MARK_CRIT_EXTRA | battle.py `_on_crit_resource@5171` 注释"v151 隐藏职业删除：星语猎印暴击额外（crit_mark）已移除"；无其他引用 | 删（v151 已删机制留档） |
| ZEN_HOLD_CFG（仅测试引用） | v151 删 cls_wu_sheng（苦修士）后禅意整体移除；battle.py 2687 注释"v151 隐藏职业删除"。唯一代码引用 = test_v1302f2_engine_fix.py:8/145-155 断言常量值 | 删 + 改测试（把断言从"读 battle_config 值"改为"无此常量/机制已删"）。**风险低但需动测试** |
| BERSERKER_RAGE_POTION_GAIN | 狂暴药剂实装在 potion_effects.py `eff_crit_dmg_pot@171`（+25% 暴伤乘算），**无怒气 +3 逻辑**；battle.py 7132 注释狂暴药剂 +25% 暴伤乘算（消费的是词条/药剂 effect 不是本常量） | 删 |
| ASSASSIN_FINISHER_THRESHOLD | 战前终结阈值 DSL 实装在 classes.py cls_ci_ke `finisher_threshold@332`（options/default/data_field）+ commands/combat.py `battle_prefs_finisher@3262` 写 `player.battle_prefs.finisher`。**battle.py/engine 无任何读 `battle_prefs.finisher` 的结算消费**（§侦察：搜 快刀/满刃/残血/满段 仅 commands UI 与 classes 数据）→ 阈值档位实为 UI 层死设置；battle_config 常量是第三份重复声明 | 删 battle_config 常量；classes.py finisher_threshold 是数据声明（同样零消费但属 UI 配置声明，可留待 UI 批次） |

### 3.2 双源/三处并存清单（同一机制数值躺在 2-3 个文件）

| 机制 | 并存位置（值） | 权威现状（引擎读谁） | 收敛难度 |
|---|---|---|---|
| **连段链值 combo** | ① battle_config `COMBO_CFG`（cap10/finish_min3/per_layer0.05/max_bonus0.40/**class_id:cls_ci_ke/path:1**）② classes.py cls_ci_ke `combo@338`（cap10/chase_at5/chase_power0.5/finish_min3/per_layer0.05/max_bonus0.40/inject_at8/spin_lock8）—— **两者数值部分重复且都零消费 except battle 读 ①**；chase_at/chase_power/inject_at/spin_lock 全仓零读（设计未实装） | battle.py `_combo_*` 读 ①（class_id/path 归属 + cap/finish_min/per/max_bonus）；**② 零读** | 中：删 ②（classes 双死源）+ ① 字段按机制收敛 `MECH_CFG["assassin_combo"]`；chase/inject/spin 字段属"未实装设计"另立 TODO 表 |
| **破绽条 shaken** | ① battle_config `ENEMY_BAR_CFG["shaken"]`（max50/decay1.7/threshold_base50/inc1.35/cap2.5/immune1/…）② battle_config `SHAKEN_CFG`（max5/stun1/threshold_mult1.3/cap3.0/max_trigger2/boss_dur_halve）—— 两套**并存同文件**，引擎 bar_* 只读 ① | engine=battle_bars `bar_def→ENEMY_BAR_CFG` + battle.py `_turn_start@9276` | 低：删 ②（淬势者撼岳之势的"预留变体"从未接线，其数值与 ① 语义冲突——若未来做淬势者，在 ① 加子键而非新常量） |
| **守护反击 counter** | ① battle_config `COUNTER_CFG`（guard_counter_dmg0.40/res_gain3/flat1/break0.40/break_thresh3）② battle_config `STANCE_COUNTER`（同值 7 字段）—— 同文件双份 | 引擎实装 battle.py 受击反击族（10626+，读套装 effect/技能 counter_attack 字段，非这两个常量）；两常量均零读 | 低：双删或归一并留档（机制在套装 effect 数据+技能字段，不在 battle_config） |
| **圣律 vow 支援** | ① battle_config `VOW_CFG`（max3/per_turn_cap1/support_per_turn1/cost_per_support1/cleanse_mit0.05/guard_mit0.15/bless_atk0.08）② core_resources.py `"vow"@149`（max3/per_turn_cap1/on_heal1…）③ classes.py cls_mu_shi `support@277`（res_key:vow/max3/per_turn_cap1/type:post_action） | 引擎零消费（§侦察：BRANCH_RESOURCE_OVERRIDE 无 (cls_mu_shi,2) 键；`_res_gain vow` / 圣辉支援 handler 全仓无——守线神谕支援**整块未实装**） | 低（删 ①）；②③ 是数据声明层，同属未实装——留数据层待实装，但 ① 的战斗数值（cleanse_mit 等）与 skills.py 的圣辉涤净 effect=cleanse_all + skills.reduce_all 字段重复且引擎读 skills 字段 → ① 冗余 |
| **龙焰/元素架设/时咒/影舞/游侠排气** | ① battle_config `DRAGON_FORM`/`MAGE_FOCUS_CFG`/`CHRONOMANCER_STASIS_CFG`/`SHADOW_DANCE_CFG`/`ENERGY_VENT`（v139 设计初稿全量默认值）② core_resources.py 职业字段 `dual_form/focus/vent`（cls_zhan_shi 狂暴、cls_fa_shi focus、cls_you_xia vent…实际值）③ classes.py 部分同名字段 | **引擎只读 ②**：battle.py `@815/3206` 把 `core_resource_def(player).dual_form/focus/vent` 注入 player dict → battle_modes 纯函数读 `player.dual_form/focus/vent`（`dual_form_def@67/focus_def@214/vent_def@355`）。① 是 battle_modes 的 `_battle_cfg()` 默认值兜底（`_cfg(_battle_cfg("dual_form"), …)` 缺字段才读）→ 实际值都在职业字段 → ① 的"引擎默认值"从不被命中 | 中：① 与 ② 合并成"默认值=字段缺省"语义后删 ①（battle_modes 兜底改读 MECH_CFG 或干脆只留职业字段——行为零变化前提：所有现网职业字段都带全键；复核 core_resources 六个职业 dual_form/focus/vent 键齐全） |
| **电荷制 charge** | ① battle_config `CHARGE_CFG`（max3/gain_per_turn/dmg_per_stage…）② classes.py cls_you_xia `charge@215`（同值 8 字段）③ skills.py **零 charge_cfg**（全表仅 1 处旧 `'charge':1.5` 旧读条 int） | 引擎 battle_bars `charge_def@164` 只读 **skill_info.charge dict / charge_cfg**——② 职业字段与 ③ 技能字段都缺 → 电荷机制数据层悬空；但 battle.py 4420 `charge_tick(player, info)` 兜底 `_battle_cfg("charge")` 读 ① → ① 是最深处的 fallback | 中：电荷机制**数据层整体未接线**（无技能带 charge_cfg）；收敛 = 先立技能数据（把 ① 数值写进实际用它的技能条目或保留 ① 作为默认），再删 ② 死职业字段 |
| **回声 echo** | ① battle_config `ECHO_CFG`（max3/heal6/extend1）② core_resources.py `"echo"@141`（max3/on_skill1 + desc 同语义） | battle.py `_echo_add@2777` 读 ① max_layers；`_th_echo_heal@467` 读 ①（heal_per_layer=6）；core_resources echo.max=3 引擎读吗？`core_resource_gain_key` 按 key 注册上限——回声驻留叠层走 `_p_stacks`（mech_stacks），不走上限注册 → ② max 字段冗余 | 低：双源同值；收 ① → MECH_CFG["echo"]，② 的 max 注明"展示用"或删 |
| **牧师德行歌者双行折算** | ① battle_config `BARD_SELF_GAIN_FACTOR`=0.55 与 `DIRGE_CFG.self_factor`=0.55 **同值双常量** ② classes.py 注释（歌者 100%/自身 55%） | 引擎零消费（歌者双行折算未实装——无团队面幅实现） | 低：0.55 双份归一后随机制实装批次处理；现网无消费 → 死表 |
| **守护姿态/坚韧/磐核** | STANCE_COUNTER/TENACITY_CFG/GUARD_CORE_CFG 三个职业常量 vs battle.py `_tenacity_try_break@4948` 字面 `2 层战意/3 次/场`、`_guard_core_n` 字面、battle_mech 磐核 handler `0.7*cores@1956` 字面 | 引擎用**字面量**实现（TENACITY 消耗 2 层战意——注意 battle_config TENACITY_CFG 说"消耗 1 坚韧跳过"，battle.py 实装是"消耗 2 层战意跳过"=**同一机制两种字段口径完全脱节**） | 中：battle.py 字面量与 TENACITY_CFG 语义冲突 → 收敛时以**引擎现状字面**为准回填数据（行为零变化） |

### 3.3 死表 5 型归因（决定删除/收敛/回填路线）

- **T1 机制以字面量在 battle_mech/battle.py 实装**（CFG 从未接线）：BONE_RUSH_CFG（battle_mech `_m_bone_rush@2089` `0.9*n` 字面）、CURSE_CFG（`_m_curse@2065` turns=8 字面、+20% 只在日志）、SOUL_MARK_CFG（`_m_soul_mark@2053` 6%/cap3 字面）、STAR_LOCK_CFG（`_sb_star_lock@1463` 0.12 字面）、STARSTEP_CFG/ASTRO_SHIELD_CFG（星语者被 v151 删后遗留）、VOW_CFG（skills.reduce_all 字段已承担数值）、COMBO_REFLOW_*/ASSASSIN_HIT_FEED/SPIN_LOCK/CHAIN_DANCE/CORRODE/POISON_BURST_CP/IDLE_FLOOR_TURNS/RANGER_SNIPE_*/HUNT_FINALE（v150-v153 重设计后数值实现在 classes.py 数据/combo dict/技能 cond/desc，常量留档）。**删除风险：零**（无消费）；若要"数值权威化"，把字面量回填进 MECH_CFG[机制名] 供 handler 读（属**执行批次可选项**，改动 handler 一行，行为零变化）。
- **T2 双源并存另一份被读**：SHAKEN_CFG↔ENEMY_BAR_CFG.shaken、STANCE_COUNTER↔COUNTER_CFG、BARD_SELF_GAIN_FACTOR↔DIRGE_CFG.self_factor、ECHO_CFG.max↔core_resources echo.max。删除/归一后仍读活源。
- **T3 引擎默认值兜底被职业字段取代**：DRAGON_FORM/MAGE_FOCUS_CFG/CHRONOMANCER_STASIS_CFG/SHADOW_DANCE_CFG/ENERGY_VENT/VENT_AT/VENT_AUTO/VENT_MAX_DELAY/VENT_RECOVERY_EXTRA（= 星语/游侠排气常量族）→ core_resources/classes 职业字段优先，兜底字典从不命中。
- **T4 机制已删除留档**：ZEN_HOLD_CFG（v151 苦修士）、HUNT_MARK_CRIT_EXTRA（v151 星语）、ASTRO_SHIELD_CFG/STARSTEP_CFG/STAR_LOCK_CFG（v151 隐藏职业族删除后 battle.py 注释明确"已移除"）、DIRGE_CFG（暗影神谕 cls_hymn 职业入口 v151 删除，机制代码保留但死歌三调无实装）。
- **T5 中文分支/内容名残留**：BARD_BRANCHES。

### 3.4 已消费但命名职业化的常量 → MECH_CFG 建议键（12 个；其余已机制键化的直接归 §4.2 A 组）

| 现常量 | 建议 MECH_CFG 机制键 | 字段备注 |
|---|---|---|
| MOMENTUM_CFG | `chi_hold_dmg`（气持有比例加伤） | per_chi/cap_chi → per_resource/cap |
| ZEN_HOLD_CFG | （删除——机制已删；若保留禅意族则 `zen_hold_dmg` 同型） | per_zen/cap_zen |
| COMBO_CFG | `assassin_combo` | cap/finish_min/per_layer/max_bonus/class_id/path → 归属字段保留数据性 |
| ASSASSIN_ON_CRIT_GAIN | `assassin_combo.on_crit_gain` | |
| ASSASSIN_ON_TAKE_HIT_PENALTY | `assassin_combo.on_take_hit_penalty` | |
| SHADOW_STEP_CFG | `shadow_step` | stealth_extra |
| SHADOW_STEALTH_DMG_MULT | `stealth_mult`（技能名→倍率键表 → 建议迁 skills 条目） | 技能中文名是内容名 |
| ECHO_CFG | `echo` | max_layers/heal_per_layer/buff_extend_per_layer |
| ENERGY_HIGH | `full_tension`（满弦） | threshold/crit_bonus/max_cost |
| RAGE_GAIN_HP_SCALE | `blood_debt_gain`（血债怒火） | base/coef/cap |
| ENEMY_BAR_CFG | `enemy_bar`（键表） | shaken/curse 子键（机制键天然） |
| DUAL_FORM_CFG / FOCUS_CFG / VENT_CFG / CHARGE_CFG | `dual_form` / `focus` / `vent` / `charge`（引擎默认值段） | core 状态机 `_battle_cfg(name)` 读法不变（内部改查 MECH_CFG[name]） |
| BRANCH_RESOURCE_OVERRIDE | `branch_resources`（分支资源所有权） | (class,path)→keys |

> 其余"职业名常量但字段即机制键"的直接映射如 §2.1 表内"机制归属"列（dot/buff/crit/mech_*/boss/element 等本就是机制键表，搬进 MECH_CFG 键名不变，消费点改 `MECH_CFG["dot"]` 即可，改动面=import 行 + 读点字符串）。
---

## 4. MECH_CFG 单表结构草案

### 4.1 结构

```python
# game/data/mech_cfg.py（或 battle_config.py 内 MECH_CFG 段——见 §4.4 落位）
MECH_CFG = {
    # ---- 机制键表（现状通用表直接收编，键名不变，消费点改查表）----
    "dot":                {**DOT_DEFS, "boss_pct_mult": 0.5, "pct_cap": 0.01,
                            "bleed_double_hp_pct": 0.30, "adapt_decay_step": 0.04, "resist_cap": 0.95},
    "mech_stack":         {"bonus": {...}, "whitelist": (...), "max": {...}},
    "buff":               {"mult": {...}, "team_keys": {...}},
    "element":            {"reactions": ELEMENT_REACTIONS, "reaction_table": REACTION_TABLE,
                            "marks_max": 3, "mark_gain_per_hit": 1, "same_cast_extra_charge": 1},
    "crit":               {"lucky_chance": 0.30, "lucky_mult": 1.3, "luck_conv": {...},
                            "multi_hit_first_only": True, "full_hp_mechs": ("shadow",),
                            "frozen_mult": {"freeze": 1.5}, "combo_mechs": ("wind",)},
    "boss":               {"attack_mults": {...}},
    "ctrl":               {"mechs": ("stun","freeze","silence"), "skill_cc_whitelist": (...),
                            "proc_groups": {...}, "stat_passives": {...}},
    "enemy_bar":          {"shaken": {...}, "curse": {...}},   # 死表 SHAKEN_CFG 并入此（未实装字段不迁）
    # ---- 机制键（职业 CFG 收敛后按机制命名）----
    "dual_form":          {...DUAL_FORM_CFG},     # 引擎默认值（字段实际值在 core_resources 职业字段）
    "focus":              {...FOCUS_CFG},
    "vent":               {...VENT_CFG},
    "charge":             {...CHARGE_CFG},
    "assassin_combo":     {...COMBO_CFG 现字段 + on_crit_gain + on_take_hit_penalty},
    "shadow_step":        {...SHADOW_STEP_CFG},
    "echo":               {...ECHO_CFG},
    "full_tension":       {...ENERGY_HIGH},
    "blood_debt_gain":    {...RAGE_GAIN_HP_SCALE},
    "branch_resources":   {...BRANCH_RESOURCE_OVERRIDE},
    "chi_hold_dmg":       {...MOMENTUM_CFG},       # 若保留
    # ---- 机制名已删除的留档/未实装设计：不入表，仅 §3.3 清单待清理 ----
}
```

**查表辅助**（core 状态机现有 `_battle_cfg(name)` 就是此形态，直接推广）：

```python
def mech_cfg(mech: str) -> dict:      # core/mech_cfg_loader 或 battle 内 helper
    return MECH_CFG.get(mech, {})     # 无配置 = 默认不启用（铁律）
```

### 4.2 现有 CFG → MECH_CFG 映射总表（95 常量去向，成员全列）

**→ A. MECH_CFG 键表收编 · 键名/键组即机制，消费点直接改查 MECH_CFG（29 个，全部存活）**
`DOT_DEFS` `DOT_BLEED_DOUBLE_HP_PCT` `DOT_ADAPT_DECAY_STEP` `DOT_RESIST_CAP` `DOT_BOSS_PCT_MULT` `DOT_PCT_CAP`（→ `MECH_CFG["dot"]` 合并子键）
`MECH_STACK_BONUS` `MECH_STACK_WHITELIST` `MECH_STACK_MAX`（→ `mech_stack`）
`MECH_FULL_HP_CRIT` `MECH_FROZEN_MULT` `MECH_COMBO_STACKS` `MECH_PROC_GROUPS` `MECH_STAT_PASSIVES`（→ 各自保留键名）
`CONTROL_MECHS` `SKILL_CC_WHITELIST`（→ `ctrl`）
`BOSS_ATTACK_MULTS`（→ `boss`）
`ELEMENT_REACTIONS` `REACTION_TABLE`（→ `element`，两表 P1 遗留建议并表）`ELEMENT_MARKS_MAX` `ELEMENT_MARK_GAIN_PER_HIT` `ELEMENT_SAME_CAST_EXTRA_CHARGE`（→ `element` 子键）
`LUCKY_CRIT_CHANCE` `LUCKY_CRIT_MULT` `LUCK_CRIT_CONV` `MULTI_HIT_CRIT_FIRST_ONLY`（→ `crit` 子键）
`BUFF_MULT` `TEAM_BUFF_KEYS`（→ `buff`）
`ENEMY_BAR_CFG`（→ `enemy_bar`，键名不变）

**→ B. MECH_CFG 机制键改名收编（12 个，全部存活）**
`RAGE_GAIN_HP_SCALE`→`blood_debt_gain`；`ENERGY_HIGH`→`full_tension`；`MOMENTUM_CFG`→`chi_hold_dmg`（若保留）；
`COMBO_CFG`+`ASSASSIN_ON_CRIT_GAIN`+`ASSASSIN_ON_TAKE_HIT_PENALTY`→`assassin_combo`（合并 3 个）；
`SHADOW_STEP_CFG`→`shadow_step`；`SHADOW_STEALTH_DMG_MULT`→`stealth_mult`（技能名键表，建议迁 skills 条目）；`ECHO_CFG`→`echo`；
`DUAL_FORM_CFG`→`dual_form`；`FOCUS_CFG`→`focus`；`VENT_CFG`→`vent`；`CHARGE_CFG`→`charge`（4 个 core 状态机默认值段）；
`BRANCH_RESOURCE_OVERRIDE`→`branch_resources`

**→ C. 迁出 battle_config（7 个，非职业机制域，归数据/经济段）**
`QUALITY_UPGRADE_CHANCE` `QUALITY_UPGRADE_MASTER_BONUS` `QUALITY_UPGRADE_COST` `MASTERPIECE_CHANCE`（economy 域）
`TIER_GROWTH` `BRANCH_BONUS` `BRANCH_BONUS_BY_CLASS`（属性成长公式段，v181 P0-A 下沉来源保持原位即可）

**→ D. 删除候选（45 个，§3.3 归因 + 附录 A 行为源）**
死表 41 个（§2.3 全表）+ 注释-only 2 个（GUARD_CORE_CFG / RANGER_CHARGE_CFG）+ 消费但恒死 2 个（BARD_BRANCHES 先退役消费段再删 / ZEN_HOLD_CFG 随测试同步）

> 合计：A 29 + B 14 + C 7 + D 45 = **95 ✓**（B 组 14 = RAGE_GAIN_HP_SCALE/ENERGY_HIGH/MOMENTUM_CFG/COMBO_CFG/ASSASSIN_ON_CRIT_GAIN/ASSASSIN_ON_TAKE_HIT_PENALTY/SHADOW_STEP_CFG/SHADOW_STEALTH_DMG_MULT/ECHO_CFG/DUAL_FORM_CFG/FOCUS_CFG/VENT_CFG/CHARGE_CFG/BRANCH_RESOURCE_OVERRIDE；D 的 2 个消费但退役常量从 52 消费面扣除后，A+B+C 恰覆盖剩余 50 个存活消费常量）。分组按"去向"互斥计数，权威映射 = §2.1 逐常量归属列 + §3.4 键名表。

> **删除前置铁律**：删任何常量前执行 §7 验证（尤其"数值以字面量存在于 battle_mech/skills/classes"的 T1/T3 型——先在引擎 grep 对应字面量确认真实行为源，避免把"常量删了但字面量才是活源"误当清干净）。

### 4.3 消费点改动量预估（执行批次）

| 消费文件 | 改动类型 | 估行 |
|---|---|---|
| game/battle.py | 顶部 import 36 常量 → `MECH_CFG`（或 `from .data.mech_cfg import MECH_CFG as _MC`）；读点 `X.get(k)` → `_MC["mech"].get(k)`。~50 处读点，机械替换 | ~90 行（import + 读点），**纯文本等价** |
| game/engine.py | 顶部 import ELEMENT_REACTIONS/TIER_GROWTH/BRANCH_BONUS/BRANCH_BONUS_BY_CLASS/MECH_STACK_MAX → 从 MECH_CFG 或保留原位段读；engine.py 3 处读点 | ~10 行 |
| game/core/battle_bars.py | `_battle_cfg` 内 cfg_map 两行 → 查 MECH_CFG（结构不变） | ~6 行 |
| game/core/battle_modes.py | 同上 | ~6 行 |
| game/core/battle_mech.py | 顶部模块级 import ELEMENT_MARKS_MAX/BUFF_MULT（L1789/947 等）→ MECH_CFG | ~8 行 |
| game/commands/economy.py | QUALITY_* 读点 → 保持原位或迁 economy 域（若迁：读点同步） | ~4 行 |
| scripts/numeric_lib/player.py + constants.py | DOT_* 读点（模拟器） | ~6 行 |
| tests | test_v1252_audit_closure.py（L388-397 断言 battle_config 表存在）/test_v130_resources/test_v1302f2/test_v1302f3/test_v1302c/test_v138_dot 等 import 断言 | 逐个同步（保留一个"MECH_CFG 结构断言"测试替代） |

**总量预估 ≈ 150-200 行等价替换 + 43 常量删除 ≈ -400 行净减**。分阶段执行后每批 py_compile + 全量单测绿。

### 4.4 落位决策（两种，执行批次先定）

- **方案 A（推荐）**：battle_config.py 保留为"战斗参数表"文件，在其内部重构为 `MECH_CFG` 单 dict + 少量引擎固有段（TIER_GROWTH 等）；对外兼容层 `X = MECH_CFG["..."]` 仅在迁移过渡期保留（或直接全量改读点）。**不新建文件** → git 历史/审计引用干净。
- 方案 B：新建 `game/data/mech_cfg.py` 单表文件，battle_config.py 只留引擎段。新建文件需同步 data/__init__.py 聚合导出与 docs 引用 → 成本略高。

---

## 5. 分阶段建议（每批独立 commit + 门禁）

### Phase 0（侦察）✅ 本文档
产出：全量消费统计 + 死表清单 + 机制映射 + 落位方案（人工确认点）。

### Phase 1：纯死表清理（低风险，先行）—— 45 个常量
1. **批 1a 真空死表删除**（38 个，无任何消费/注释/测试依赖）：ASSASSIN_CHAIN_DANCE_PER/ASSASSIN_CORRODE_BONUS/ASSASSIN_HIT_FEED/ASSASSIN_SPIN_LOCK_THRESHOLD/ASTRO_SHIELD_CFG/BARD_DAWN_HYMN_POWER/BARD_SELF_GAIN_FACTOR/BARD_WEAPON_RHYTHM/BERSERKER_DUAL_ATTACK/BERSERKER_ENTRY_STRIKE/BERSERKER_MASTERY_KEEP/BERSERKER_RAGE_POTION_GAIN/BONE_RUSH_CFG/CHRONOMANCER_STASIS_CFG/COMBO_REFLOW_HP_PCT/COMBO_REFLOW_LAYERS/COUNTER_CFG/CURSE_CFG/DIRGE_CFG/DRAGON_FORM/ENERGY_VENT/GUARD_CORE_CFG/IDLE_FLOOR_TURNS/MAGE_FOCUS_CFG/POISON_BURST_CP/RANGER_CHARGE_CFG/RANGER_HUNT_FINALE_POWER/RANGER_SNIPE_BACK_ROW_MULT/RANGER_SNIPE_REACH/SHADOW_DANCE_CFG/SHAKEN_CFG/SOUL_MARK_CFG/STANCE_COUNTER/STARSTEP_CFG/STAR_LOCK_CFG/TENACITY_CFG/VENT_AT/VENT_AUTO/VENT_MAX_DELAY/VENT_RECOVERY_EXTRA/VOW_CFG（41-3 见下）
   - 复核后再删的 3 个：BARD_DAWN_HYMN_POWER（先确认 破晓长歌 数值在 skills.py 条目 power 字段——见 §6 复核项）、HUNT_MARK_CRIT_EXTRA、ASSASSIN_FINISHER_THRESHOLD（确认 battle_prefs.finisher 无结算消费——已确认）。
2. **批 1b BARD_BRANCHES 消费段退役**（先删 `_is_bard_skill` 调用点 4514 恒 False 分支 + 函数本体，再删常量——中风险，用"现网分支名不命中"证据）。
3. **批 1c ZEN_HOLD_CFG + 测试同步**（test_v1302f2_engine_fix.py L145-155 改断言）。
4. 验证：py_compile + run_numeric_tests.py + 相关单测（test_v1252_audit_closure 若断言 90 常量数 → 同步）。

### Phase 2：双源归一（中风险，逐机制）—— classes/core_resources/battle_config 三处并存收敛
1. COMBO_CFG ↔ classes.py cls_ci_ke.combo（删 classes 侧死源；chase_at/spin_lock 等未实装字段移入"机制 TODO"注释；battle 读点改 MECH_CFG["assassin_combo"]）。
2. 职业字段取代 CFG 族：把 DRAGON_FORM/MAGE_FOCUS_CFG/CHRONOMANCER_STASIS_CFG/SHADOW_DANCE_CFG/ENERGY_VENT/VENT_* 从 battle_config 删除，battle_modes `_battle_cfg` 兜底改读 MECH_CFG 通用键（或删兜底——需复核 core_resources 六职业字段键齐全）。
3. SHAKEN_CFG ↔ ENEMY_BAR_CFG.shaken：删 SHAKEN_CFG（未来淬势者 = ① 加子键）。
4. ECHO_CFG ↔ core_resources echo：值归一（max 3 一处权威）。
5. TENACITY/磐核/守护姿态字面量 → 回填 MECH_CFG（以引擎现状为准）。
6. 验证同上 + 行为快照对比（§7）。

### Phase 3：MECH_CFG 单表成型 + 读点迁移（低-中风险，纯寻址）
1. 建 MECH_CFG（§4.1 结构）+ mech_cfg() 查表 helper。
2. 消费点机械替换（§4.3 预估 150-200 行）。
3. 更新 data/__init__.py 聚合导出（保留对外旧名兼容层可选——v125.2 先例：engine 顶部 import 保接口）。
4. 文档/测试同步；全量回归。

> **批次依赖**：Phase 1 先清死表（零行为影响）→ Phase 2 双源归一（消灭三处并存）→ Phase 3 命名收敛（机制化）。Phase 3 的 MECH_CFG 键名以 Phase 2 归一后的存活字段为准。battle.py 的 Phase 2/3 改动与 P1-B/P1-C/P2-B/P2-D 撞同一文件 → **串行派工**（冲突矩阵同 REFACTOR_PLAN §分批派工：battle.py 文件所有权互斥）。

---

## 6. 风险清单

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| 1 | 死表删除误删"被消费但 import 链在 data/__init__ 聚合"的常量 → 运行崩 | 中 | 已复核：data/__init__.py 只 re-export 18 个（§2.1 全在 52 消费列）；死表 41 个不在任何 import；删除批先 grep 全仓 |
| 2 | 死表数值其实是"引擎字面量的权威档案"，删后改数值无档案 | 中 | §3.3 T1 型先做"字面量 → MECH_CFG/技能字段"回填（或文档建档：把字面量所在行写进删除 commit message） |
| 3 | BARD_BRANCHES 删除影响 _is_bard_skill 调用链（4514 伴奏） | 中 | 现网恒 False 证据 + 删除前跑诗人职业战斗 smoke（test_v83_bard.py） |
| 4 | ZEN_HOLD_CFG 测试引用（test_v1302f2_engine_fix.py） | 低 | 同步改测试断言 |
| 5 | Phase 3 读点替换漏点 → 行为变化 | 低-中 | 机械替换后全量单测（numeric 51 文件 + run_all）+ §7 OLD/NEW 探针 |
| 6 | classes.py 死字段（combo/charge/support/vent 等）误删影响命令层 UI（battle_prefs 展示读 classes.finisher_threshold） | 低 | 只删 battle_config 侧；classes 数据声明留待 UI/数据批次统一评估 |

---

## 7. 测试策略（行为零变化验证）

### 7.1 三层验证
1. **静态等价**：每批删除/改名后，`rg` 确认无残留引用；删除 commit 里附"该常量字面量/行为源在 X:Y"证据行（§3.3 归因）。
2. **py_compile + 单测**：门禁 python 跑 tests/test_v1252_audit_closure.py（断言 battle_config 表存在）→ 该测试需随 Phase 1 同步为"MECH_CFG 结构断言"；numeric 相关（test_v130_resources/test_v1302f2/test_v1302f3/test_v1302c/test_v138_dot/test_numeric_burst_redline）逐个跑。
3. **行为快照对比（Phase 2/3 用）**：仿 P2-D §7——用 tests/conftest 造 6 职业 × 满装 × 代表技能的战斗，跑 OLD(baseline commit) vs NEW 全量 logs+资源+结算 diff，恒等才算过。

### 7.2 特殊验证点
- 删除 41 死表后 **run_all_tests.py 全量**（318 测试）必须与基线同绿数——死表本来就不该有任何测试依赖；若某测试读死表 → 该常量不是真死，打回 Phase 1 复核。
- ZEN_HOLD_CFG：改测试后跑 test_v1302f2。
- BARD_BRANCHES：跑 test_v83_bard.py + 诗人 30/60/90 分支战斗 smoke（回声不触发伴奏分支恒 False → 结果不变）。
- Phase 2 双源归一后跑 test_v130_resources.py（COMBO_CFG 断言 L184）+ test_v1302f2（MOMENTUM_CFG 断言 L149）——断言若引用常量名需随 MECH_CFG 键同步。

---

## 8. 交付物与文档联动

- **本批次交付**：本文档（docs/REFACTOR_P2E_mech_cfg.md，commit 到 wt_p2e 分支）。未改 game/ 代码。
- **执行批次交付**：Phase 1-3 每个 commit + 删除/改名清单回写本文档附录。
- **联动文档**：REFACTOR_PLAN_v181.md P2-E 段标记完成；ARCHITECTURE_TARGET_STATE_v181.md §P2E 验收勾选；CLASS_MECHANICS_v153 / CLASS_REDESIGN_FRAMEWORK_v150（大量引用已死常量名做机制说明——改引用或标注"已删，数值见 X"）；P2-D 文档 §1.2 的"老名字 counter_attack"等与 STANCE_COUNTER/COUNTER_CFG 的关系。

---

## 附录 A：41 死表 + 2 注释-only 的行为源定位（删除复核用）

| 常量 | 行为真实源（文件:行） | 删除风险 |
|---|---|---|
| BONE_RUSH_CFG | battle_mech `_m_bone_rush@2089` `0.9*n` 字面；`_m_sacrifice@2101` `0.9` | 零（数值在 handler 字面，删除后不影响；未来回填 `MECH_CFG["bone_rush"]` 时 handler 改读表） |
| CURSE_CFG | battle_mech `_m_curse@2065` turns=8 字面；`_m_curse_refresh@2074`；enemy_bar.curse 注释内嵌 vuln/acc | 零 |
| SOUL_MARK_CFG | battle_mech `_m_soul_mark@2053` 6%/cap3 字面；battle.py 7397-7405 soul_mark_cap | 零 |
| SHAKEN_CFG | ENEMY_BAR_CFG["shaken"] 是活源（bar_* 读）；SHAKEN_CFG 从未读 | 零（删后淬势者未实装变体留注释） |
| COUNTER_CFG / STANCE_COUNTER | battle.py 受击反击族 10626+ 实装（读套装 effect/技能字段/字面）；两常量零读 | 零 |
| DRAGON_FORM | core_resources cls_dragon_oath.dual_form 活源；battle 注入 dual_form 字段 | 零（引擎默认值兜底从不命中——需复核：现网无职业走兜底路径） |
| MAGE_FOCUS_CFG / CHRONOMANCER_STASIS_CFG | core_resources cls_fa_shi.focus 活源 | 零 |
| SHADOW_DANCE_CFG | core_resources cls_shadow_blade.dual_form(auto_enter/duration) 活源（battle_modes dual_form_enter 读 d.duration） | 零 |
| ENERGY_VENT / VENT_AT / VENT_AUTO / VENT_MAX_DELAY / VENT_RECOVERY_EXTRA | core_resources cls_you_xia.vent(trigger 999 v153 废弃) / classes.py vent 死字段；star 语者 v151 删除 | 零 |
| TENACITY_CFG | battle.py `_tenacity_try_break@4948` 字面（2 层战意/场 3 次）——与 CFG 语义脱节（CFG 说坚韧 1 点） | 零（删除时把字面量记录进 commit；CFG 与实装语义冲突 = CFG 是错误档案，更该删） |
| GUARD_CORE_CFG | battle.py `_guard_core_n`/battle_mech `_m_guard_core_burst@1956` `0.7*cores` 字面；classes.py L403 注释引用 | 零 |
| VOW_CFG | skills.py 圣辉涤净 effect=cleanse_all + reduce_all 字段（v169.7 实装）；vow 资源无 res_gain/无 BRANCH 覆盖 → 机制未接线 | 零 |
| BARD_DAWN_HYMN_POWER | skills.py "破晓长歌"@3811 power/exprs（195%+130 成长，非 320%——CFG 与技能表数值不一致，技能表是活源） | 零（CFG 3.20 vs skills 实际——删除更正确） |
| BARD_SELF_GAIN_FACTOR / DIRGE_CFG | 双行折算无实装；classes.py 注释 55% | 零 |
| BARD_WEAPON_RHYTHM | 谱曲节奏 mace/staff 无实装（skills 无 compose 消费） | 零 |
| ASSASSIN_HIT_FEED / SPIN_LOCK / COMBO_REFLOW_* / CHAIN_DANCE / CORRODE / POISON_BURST_CP | classes.py cls_ci_ke.combo dict（chase_at/inject_at/spin_lock 零读=同死）；battle_mech `_m_poison_burst_finisher@2107` per=0.14 字面；skills 链舞/蚀骨 passive proc 数据缺陷（battle.py 6343 TODO） | 零（重设计 v150-v153 后数值已另安家） |
| IDLE_FLOOR_TURNS | 亡灵祭仪保底律无实装（battle.py 409 只做信念衰减状态机） | 零 |
| RANGER_CHARGE_CFG / CHARGE_CFG 职业侧 | charge_cfg 技能字段全表 0 处；classes.py cls_you_xia charge dict 零读；battle_bars charge_def 读 skill_info | 零（数据层悬空，收敛时先立技能数据或保留 CHARGE_CFG 引擎默认值——**CHARGE_CFG 是活兜底**（battle_bars `_cfg(_battle_cfg("charge"),…)`），只删 classes 侧） |
| RANGER_SNIPE_REACH / BACK_ROW_MULT / HUNT_FINALE_POWER | v150 校准记录在 docs；技能实际在 skills.py 条目（穿心箭 res_cost 45/cond hunt_full；死神之箭同理）；无 engine 读 RANGER_* | 零 |
| ASTRO_SHIELD_CFG / STARSTEP_CFG / STAR_LOCK_CFG | 星语者 v151 删除；星轨锁定 effect 实装在 battle_mech `_sb_star_lock@1463`（0.12 字面） | 零 |
| BERSERKER_DUAL_ATTACK / ENTRY_STRIKE / MASTERY_KEEP | 狂战士狂暴机制实装在 core_resources cls_zhan_shi.dual_form（maintain 0.6/hit 1 等）——battle_mech 无"双段普攻"消费点（v139 形态机只维护形态，双段普攻由技能表 exprs 承担） | 零 |

> 注：**CHARGE_CFG 不能删**（battle_bars 兜底活源）；RANGER_CHARGE_CFG 删后 classes.py charge 死字段一并清理。此差异已在前文体现（CHARGE_CFG 在 52 消费列）。

---

*（end of doc — 侦察基线 master 329989c / wt_p2e，未改 game/ 代码）*
