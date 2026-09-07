# P2E 执行任务书 — battle_config 95 常量 → MECH_CFG 单表收敛（可直接照做版）

> 供后续子 agent 直接执行。只读侦察结论/方案权威 = `docs/REFACTOR_P2E_mech_cfg.md`（391 行）；本任务书是它的**可派工批次化落地版**。
> 铁律：**行为零变化**；每步 `py_compile` + 单测绿；data 纯数据零函数；core 通用执行器+注册表；battle 纯编排零内容名。
> 环境：git-bash。python 用 AstrBot uv python：`"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe"`（下文简称 `PY`）。
> 每批独立 commit：`v181.P2E-P1a <动作描述>`；全仓 grep 必须在删/改后零残留（注释残留按批内清单处理）。
> 所有行号以当前 master（c61f48b，2026-09-07）为准；执行 agent 应先 `git status` 干净 + 行号复核再动手（文件近期 P2C-C9/C10/P2D-D2 合并后行号可能漂移，**以 grep 锚点复核，不以行号死磕**）。

---

## 0. 任务全景与依赖图

| Phase | 内容 | 文件所有权 | 可否并行派工 |
|---|---|---|---|
| **Phase 1**（P1a/P1b/P1c 可拆 3 批） | 清 43 死表（41 死表 + GUARD_CORE_CFG/RANGER_CHARGE_CFG 注释-only）→ 退役 BARD_BRANCHES 消费链 → ZEN_HOLD_CFG+测试 | P1a 只碰 `game/data/battle_config.py`；P1b 碰 `game/battle.py`；P1c 碰 battle_config + `tests/test_v1302f2_engine_fix.py` | P1a 独立；P1b/P1c **串行**（都碰 battle.py/battle_config） |
| **Phase 2**（P2a 归一 classes/core_resources 双源；P2b 职业字段兜底族归一） | 双源归一：classes.combo 死源删、SHAKEN→ENEMY_BAR、VENT/DRAGON_FORM 等 CFG 族 → core_resources 职业字段唯一权威 | P2a 碰 `game/data/battle_config.py` + `game/data/classes.py` + `game/battle.py`(COMBO 读点) + `game/core/battle_bars.py`；P2b 碰 battle_config + `game/core/battle_modes.py` + battle.py | P2a/P2b **串行**（都碰 battle.py + battle_config） |
| **Phase 3**（P3a 建表 + 非 battle 消费点；P3b battle.py 全量读点迁移；P3c 测试/文档收尾） | MECH_CFG 单表成型 + 全量读点迁移 | P3a 碰 `game/data/battle_config.py` + engine.py + battle_bars/battle_modes/battle_mech + economy.py + scripts/numeric_lib + tests；P3b 只碰 `game/battle.py`；P3c tests/docs | P3a → P3b **串行**（3b 独占 battle.py 大改）；P3a 内部引擎侧小步可拆但建议串 |

**与其它批次的文件互斥（务必遵守）**：`game/battle.py` 正在被 P2C-C9/C10（进行中 w5 wt_p2dd2 之后）、P2D-D2（运行中）消费 → **P2E 的 Phase 2/3（凡改 battle.py）必须等 P2C-C10 / P2D 全批 merge 后再开**，且 P2E Phase 2/3 之间、Phase 3b 与任何其他 battle.py 批（P1-B/P1-C/P2-B/P2-D/P2G/P3 e_buffs 收口）**串行**。P4-9（BattleSettlementService，commands/combat.py 1784-2816）不碰 battle.py 但依赖战斗胜利快照网 → 建议 P4-9 与 P2E 均完成后再互相不冲突（P4-9 在 P2E 后执行）。改文件前先查 HANDOFF 进行中批次，同一文件绝不同时两个 agent。

---

## 1. 死表清单（41 个逐个：删 or 留 + 理由）

> 41 死表全部**删**（§2.3 全仓零引用，含注释/字符串；删除风险零的占 41/41）。行为真实源都在引擎字面量/技能表字段/职业字段/ENEMY_BAR_CFG，删除不影响运行时——**前提**：删前把 §1.2 的"行为源证据行"写进 commit message，防止"数值权威档案丢失"。
> 2 个注释-only 常量（GUARD_CORE_CFG / RANGER_CHARGE_CFG）同批删（引擎以字面量实现，battle.py L4849 与 battle_mech L1946 注释引用改述或删）。
> 消费但恒死 2 个：`BARD_BRANCHES`（1b 退役消费段后删）、`ZEN_HOLD_CFG`（1c 改测试后删）。

### 1.1 删-零风险组（41 = 40 死表 + HUNT_MARK_CRIT_EXTRA 已消费死档，逐行证据见附录 A）

删除 = 删 **battle_config.py 下列行区间**（41 死表 + 2 注释-only = 43 个顶层 def 一次性清；含各自 # 段头注释）：

| 删除段 | 行区间(现基线) | 内容 | 数量 |
|---|---|---|---|
| D1 | L245-249 | HUNT_MARK_CRIT_EXTRA（v151 隐藏职业删除留档，battle.py L5212 注释自证"已移除"；引擎零读） | 1 |
| D2 | L419-433 | COUNTER_CFG（六、counter 段头 + dict；受击反击族引擎实装读套装 effect/技能字段 battle.py 10626+，双常量 COUNTER_CFG/STANCE_COUNTER 均零读） | 1 |
| D3 | L435-657 | 「七、职业专属签名技数值」整区段头 + 42 defs：`BERSERKER_DUAL_ATTACK/ENTRY_STRIKE/MASTERY_KEEP/RAGE_POTION_GAIN DRAGON_FORM MAGE_FOCUS_CFG CHRONOMANCER_STASIS_CFG ENERGY_VENT RANGER_CHARGE_CFG(注释-only) RANGER_SNIPE_REACH/BACK_ROW_MULT/HUNT_FINALE_POWER STAR_LOCK_CFG VENT_AT/AUTO/MAX_DELAY/RECOVERY_EXTRA STARSTEP_CFG ASTRO_SHIELD_CFG SHADOW_DANCE_CFG SHAKEN_CFG GUARD_CORE_CFG(注释-only) CURSE_CFG SOUL_MARK_CFG DIRGE_CFG BONE_RUSH_CFG ASSASSIN_HIT_FEED/SPIN_LOCK_THRESHOLD/COMBO_REFLOW_HP_PCT/COMBO_REFLOW_LAYERS/POISON_BURST_CP/CHAIN_DANCE_PER/CORRODE_BONUS STANCE_COUNTER TENACITY_CFG BARD_SELF_GAIN_FACTOR BARD_WEAPON_RHYTHM VOW_CFG BARD_DAWN_HYMN_POWER IDLE_FLOOR_TURNS ASSASSIN_FINISHER_THRESHOLD` | 42 |

> ⚠️ **切勿删**：L276 DUAL_FORM_CFG / L304 FOCUS_CFG / L331 CHARGE_CFG / L354 VENT_CFG / L382 ENEMY_BAR_CFG（battle_modes/battle_bars `_battle_cfg()` 兜底活源——Phase 2b/3 收编对象）。L189 ZEN_HOLD_CFG 与 L215 BARD_BRANCHES 单独批次。

**41 死表逐个处置（删 or 留 + 理由）**：

| # | 常量 | 处置 | 理由（行为真实源） |
|---|---|---|---|
| 1 | ASSASSIN_CHAIN_DANCE_PER | 删 | 链舞终结增伤 5%→8% 设计留档；v150-153 重设计数值已另安家（classes combo + 技能被动 proc 数据缺陷 battle.py 6343 TODO） |
| 2 | ASSASSIN_CORRODE_BONUS | 删 | 蚀骨毒爆 +20% 留档；毒爆实装 battle_mech `_m_poison_burst_finisher@2107` per=0.14 字面 |
| 3 | ASSASSIN_FINISHER_THRESHOLD | 删 | 战前终结阈值 DSL 实装在 classes.py cls_ci_ke `finisher_threshold@332`（options/default/data_field）+ commands/combat.py battle_prefs_finisher L3262 写 battle_prefs；battle.py/engine **零读 battle_prefs.finisher 结算** → 常量是第三份重复声明；**classes.py 字段是 UI 层数据声明（命令层读）——留**（风险 §4.2） |
| 4 | ASSASSIN_HIT_FEED | 删 | 段数三线投喂留档；现实现 = classes combo dict + proc 被动 |
| 5 | ASSASSIN_SPIN_LOCK_THRESHOLD | 删 | 旋锋锁未实装（classes combo spin_lock 字段零读=同死） |
| 6 | ASTRO_SHIELD_CFG | 删 | 星语者 v151 删除遗留；引擎无消费 |
| 7 | BARD_DAWN_HYMN_POWER | 删 | 破晓长歌 320% 与 skills.py 实际 power 195%+130 成长不一致 → **技能表是活源，CFG 是错误档案，删更正确** |
| 8 | BARD_SELF_GAIN_FACTOR | 删 | 歌者双行折算 0.55 未实装（无团队面幅实现）；classes 注释载明 55%；与 DIRGE_CFG.self_factor 同值双份 |
| 9 | BARD_WEAPON_RHYTHM | 删 | 谱曲节奏 mace/staff 无实装（skills 无 compose 消费） |
| 10 | BERSERKER_DUAL_ATTACK | 删 | 狂暴双段普攻现实现=技能表 exprs（2×70%）；core_resources cls_zhan_shi.dual_form(maintain 0.6/hit 1) 活源 |
| 11 | BERSERKER_ENTRY_STRIKE | 删 | 破势斩 120% 追加实装=技能表 effect（破势斩条目） |
| 12 | BERSERKER_MASTERY_KEEP | 删 | 狂暴精通（维持/受击 -1→0）实装 core_resources cls_zhan_shi.dual_form 字段（v153 maintain 0.6） |
| 13 | BERSERKER_RAGE_POTION_GAIN | 删 | 狂暴药剂实装 potion_effects.py `eff_crit_dmg_pot@171`（+25% 暴伤乘算），无怒气+3 逻辑 |
| 14 | BONE_RUSH_CFG | 删 | battle_mech `_m_bone_rush@2089` `0.9*n` 字面；`_m_sacrifice@2101` 0.9 字面（handler 是行为源） |
| 15 | CHRONOMANCER_STASIS_CFG | 删 | 时咒时间凝滞核心值 core_resources cls_fa_shi.focus/stasis 字段优先 + battle_modes focus_def 读职业字段（兜底字典从不命中） |
| 16 | COMBO_REFLOW_HP_PCT | 删 | 链点回流未实装（v153 后无 res_gain cp 回流消费；致命预谋返还实装 battle.py `_assassin_finisher_refund@5215`，不走 CFG） |
| 17 | COMBO_REFLOW_LAYERS | 删 | 同上 |
| 18 | COUNTER_CFG | 删 | 受击反击族 battle.py 10626+ 实装（读套装 effect/技能 counter_attack 字段/字面）；与 STANCE_COUNTER 同文件双份均零读 |
| 19 | CURSE_CFG | 删 | battle_mech `_m_curse@2065` turns=8 字面 +20% 只在日志；enemy_bar.curse 注释内嵌 vuln/acc 数值（**ENEMY_BAR_CFG["curse"] 是活源**） |
| 20 | DIRGE_CFG | 删 | 死歌三调无实装（暗影神谕 cls_hymn v151 删入口；vuln 数值在 ENEMY_BAR_CFG curse 子键） |
| 21 | DRAGON_FORM | 删 | 龙焰双形态实装 core_resources cls_dragon_oath.dual_form（enter 8/可下调 6）；battle_modes 只读职业字段，CFG 兜底从不命中 |
| 22 | ENERGY_VENT | 删 | 游侠凝神屏息 v153 废弃（core_resources cls_you_xia.vent trigger=999 永不到达）；数值留 core_resources vent 字段 |
| 23 | GUARD_CORE_CFG（注释-only） | 删 | 磐核实装 battle_mech `_m_guard_core_burst@1956` 0.7×cores 字面 + battle.py `_guard_core_n` 读 resources；battle.py L4849 注释与 battle_mech L1946 注释引名改述 |
| 24 | HUNT_MARK_CRIT_EXTRA | 删 | v151 星语者删除留档；battle.py `_on_crit_resource` 尾注 L5212 "v151 隐藏职业删除：星语猎印暴击额外（crit_mark）已移除" |
| 25 | IDLE_FLOOR_TURNS | 删 | 亡灵祭仪保底律无实装（battle.py L409 只做信念衰减状态机） |
| 26 | MAGE_FOCUS_CFG | 删 | 元素架设实装 core_resources cls_fa_shi.focus（dmg 0.40/taken 0.20/…）；CFG 兜底从不命中 |
| 27 | POISON_BURST_CP | 删 | 毒爆改版 battle_mech `_m_poison_burst_finisher@2107` 字面（吃 cp 3 实现在 mech effect 数据） |
| 28 | RANGER_CHARGE_CFG（注释-only） | 删 | 电荷数据层悬空（skills 全表 0 处 charge_cfg）；classes.py cls_you_xia.charge dict 零读；**注意 CHARGE_CFG(L331) 不能删**（battle_bars charge_def 兜底活源） |
| 29 | RANGER_HUNT_FINALE_POWER | 删 | 狩猎终章 2.20 校准在 skills.py 条目（power/desc 同步）；无 engine 读 RANGER_* |
| 30 | RANGER_SNIPE_BACK_ROW_MULT | 删 | 狙击 rank3 ×1.2 实装 skills.py 条目（穿心箭/死神之箭 reach/cond 字段） |
| 31 | RANGER_SNIPE_REACH | 删 | 同上（reach=3 在技能数据） |
| 32 | SHADOW_DANCE_CFG | 删 | 影舞态实装 core_resources cls_shadow_blade.dual_form（auto_enter/duration 3/lock_gain）；battle_modes dual_form_enter 读 d.duration |
| 33 | SHAKEN_CFG | 删 | 破绽条活源 = ENEMY_BAR_CFG["shaken"]（battle_bars bar_def 读）；SHAKEN_CFG 是淬势者未接线预留变体且与活源数值语义冲突（max 5 层 vs 50 积蓄）→ 删，注释在 ENEMY_BAR_CFG.shaken 尾注"淬势者未来=加子键" |
| 34 | SOUL_MARK_CFG | 删 | battle_mech `_m_soul_mark@2053` 6%/cap3 字面 + battle.py 7397-7405 soul_mark_cap 字面；enemy_bar.curse 注释载 per_layer 0.06/cap 3 |
| 35 | STANCE_COUNTER | 删 | 与 COUNTER_CFG 同值 7 字段双份、均零读；反击实装 battle.py 受击族 |
| 36 | STARSTEP_CFG | 删 | 星语者 v151 删除遗留（星移步） |
| 37 | STAR_LOCK_CFG | 删 | 星轨锁定 effect 实装 battle_mech `_sb_star_lock@1463`（0.12 字面） |
| 38 | TENACITY_CFG | 删 | battle.py `_tenacity_try_break@4948` 字面（消耗 2 层战意/场 3 次）——**与 CFG 语义脱节（CFG 说坚韧 1 点）→ CFG 是错误档案更该删**；字面量行记 commit |
| 39 | VENT_AT / VENT_AUTO / VENT_MAX_DELAY / VENT_RECOVERY_EXTRA | 删 | 星语猎印排气族 v151 删除遗留（VENT_AUTO 等星语专用）；游侠 vent 活源 = core_resources cls_you_xia.vent |
| 40 | VOW_CFG | 删 | 圣律支援整块未实装（BRANCH_RESOURCE_OVERRIDE 无 (cls_mu_shi,2) 键、`_res_gain vow`/圣辉支援 handler 全仓无）；圣辉涤净实装 skills.py effect=cleanse_all + reduce_all 字段（v169.7）→ CFG 冗余；core_resources.vow + classes.support 是数据声明留数据层（UI/数据批次评估） |

> 合计：41 死表（D1 1 个 + D2 1 个 + D3 39 个）= 41 ✓；D3 另含 GUARD_CORE_CFG/RANGER_CHARGE_CFG 2 个注释-only → P1a 总删 **43 个 def**。

### 1.2 删除复核前置（批 1a 执行 agent 必做）

删除前先跑（证据已在本侦察完成，重跑确认无漂移即可）：
```bash
cd /c/Users/yuyu/qqbot/data/plugins/dragonfall
# 1) 全仓（game/scripts/tests/docs/design/audit + .md）零代码引用复核——应只剩 battle_config.py 定义行与 docs/design 历史文档提及
for c in <43 名单>; do grep -rn --include='*.py' "\b$c\b" game/ tests/ scripts/ | grep -v 'game/data/battle_config.py' | grep -v __pycache__; done   # .py 期望零输出
# 2) game/*.py 注释残留白名单（删后改述）：battle.py L4849 / battle_mech.py L1946（GUARD_CORE_CFG 名）→ 批内同步改注释
# 3) docs/CLASS_MECHANICS_v153.md / CLASS_REDESIGN_FRAMEWORK_v150.md / design/new_world/ 引用已死常量名 → 标注"已删，数值见 X"（可选批内，至少 commit message 记）
# 4) 引擎字面量证据行抄进 commit message（§1.1 理由列）
```

---

## 2. Phase 1 批次细化（清死表，低风险先行）

### P1a — 43 死表删除（只碰 game/data/battle_config.py + 2 处注释）

**改什么**：
1. `game/data/battle_config.py` 删除段：
   - D1：L245-249（HUNT_MARK_CRIT_EXTRA 段头+def）
   - D2：L419-433（六、counter 段头 + COUNTER_CFG dict）
   - D3：L435-657（七、职业专属签名技段头 + 42 defs，含 GUARD_CORE_CFG/RANGER_CHARGE_CFG）
   - 保留文件其余全部（dual_form/focus/charge/vent/enemy_bar/COMBO_CFG/ECHO_CFG/MOMENTUM_CFG/…/BUFF_MULT/TEAM_BUFF_KEYS/TIER_GROWTH/BRANCH_*/MECH_STACK_MAX 与 L245 之前、L657 之后的段）
   - 删除后 L244 空行 + L250(v139 头) 之间至多留 1 空行；L417(ENEMY_BAR 尾) + L658(v176 增益头) 之间保留 1 空行
2. `game/battle.py` L4849 注释 `GUARD_CORE_CFG max=5` → 改 `磐核 0-5（core_resources/resources.guard_core；MECH_CFG 未含磐核段，数值=guard_core_burst handler 字面）`
3. `game/core/battle_mech.py` L1946 注释同改（去掉 GUARD_CORE_CFG 名）

**验证清单（行为零变化 + 门禁）**：
```bash
PY="C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe"
cd /c/Users/yuyu/qqbot/data/plugins/dragonfall
# a) 语法
"$PY" -m py_compile game/data/battle_config.py game/battle.py game/core/battle_mech.py game/engine.py
# b) 零残留（.py 全仓）：43 名单一个都不该出现在 game/ 除已改注释外
# c) import 冒烟
"$PY" -c "import sys; sys.path.insert(0,'.'); import game.data.battle_config as bc; print('ok', len([n for n in dir(bc) if n.isupper()]))"   # 期望 ≈ 52 个存活常量（95-43）
"$PY" -c "import sys; sys.path.insert(0,'.'); from game.data import battle_config; from game import battle; from game import engine; print('engine+battle import ok')"
# d) 单测（P2E 专属相关）
"$PY" tests/test_v1252_audit_closure.py          # battle_config 表接线 identity 断言（只查存活 18 个导出，不查死表）
"$PY" tests/test_v138_dot.py
"$PY" tests/test_v130_resources.py               # BC.COMBO_CFG / BC.RAGE_GAIN_HP_SCALE 断言——均存活，应绿
"$PY" tests/test_numeric_p0_effect_fixes.py
"$PY" tests/test_v1302f3_qa_fixes.py
# e) numeric 门禁（改动数值/表必跑）：全量 ~2min
"$PY" scripts/run_numeric_tests.py
# f) 行为零变化：死表零消费 → 全量单测 = 与基线同绿数（跑一次 run_all 对照）
"$PY" scripts/run_all_tests.py
```
**验收**：py_compile 0 错；单测全绿（绿数 ≥ 基线）；numeric 全绿（52/52 当前口径，见 §5 门禁注）；run_all 无新增红；git diff 仅删 43 def + 2 注释改述。

---

### P1b — BARD_BRANCHES 消费链退役 + 删除（中风险，碰 game/battle.py）

**背景（恒 False 证据链）**：BARD_BRANCHES=(“吟游诗人”,“灵魂歌者”,“黎明颂者”) 是 v153 前牧师攻线旧分支名。现网：cls_mu_shi.evolve_branches = 神谕者/死灵祭司/大主教/亡魂引渡者/圣光先知/黯灵君主（classes.py），cls_shi_ren(独立诗人)分支=咏叹者/挽歌者/晨曦歌者/安魂歌者/天籁颂者；**无任何职业分支叫这三个名字** → `_is_branch_of(player,*BARD_BRANCHES)` 恒 False → `_is_bard_skill` 恒 False。伴奏被动技能数据（skills.py）已不存在（仅 scripts/v1123_bard_surgery.py 历史脚本有）→ 4552 的 `is_passive_learned(伴奏)` 恒 False。回声唯一生产者 = battle.py L4553（死）；回声=0 → 回声治疗/续时不触发（6311 分支被 _is_bard_skill 恒 False 短路，且需 echo_layers>0）。

**改什么**（battle.py）：
1. 顶部 import L33：`ECHO_CFG, BARD_BRANCHES,` → `ECHO_CFG,`（删 BARD_BRANCHES）
2. 删 `_is_bard_skill` 方法本体（L2819-2834 整 def）
3. 删伴奏触发块（L4547-4554 注释 4 行 + if 块 3 行）——`_do_player_skill` 内（读条立即结算路径之后）
4. 删 `_skill_buff` 内回声续时扩展块（L6310-6312 注释 1 + if 2 行）——即删
   ```python
   # v130.2 歌者回声：增益技持续 + 回声层数 刻（priest_转职.md §3.0）
   if self._is_bard_skill(player, info):
       base_turns += int(ECHO_CFG.get("buff_extend_per_layer", 1) or 1) * self._echo_layers()
   ```
   保留 `self._cast_buffs()[key] = max(...)` 行。⚠️ `buff_extend_per_layer` 字段仍在 ECHO_CFG（Phase3 随 MECH_CFG["echo"] 收编时一并评估去留——若引擎不再读该字段，Phase3 从 dict 摘除）
5. 注释同步：L2821-2825 docstring（echo 所有权说明）保留但删 BARD_BRANCHES 字样；L4550 注释改述（删 BARD_BRANCHES 名）；L4551/L4692-4698 伴奏面板扣除残留段——4692-4698 段 `_bz = E.skill_info(...伴奏...)` 读 skills 数据恒空（数据已删）→ **可同批删**（数据不存在则恒不扣；与 P2E 边界外不动 battle.py 主伤路径，仅清死段）。保守做法：只删 4553 触发 if + 6310 扩展 if + _is_bard_skill；4692-4698 伴奏面板扣除段因引用 skill_info 空表亦恒空，**建议同批删**（记录 commit：数据层无伴奏技能 → skill_info 返回 None → 该段恒跳过，删除等价）
6. battle_config.py L214-215 BARD_BRANCHES def + 其注释行 → 删

**验证清单**：
```bash
# a) 语法 + import
# b) 全仓 grep：BARD_BRANCHES 在 game/ 零残留（battle_config 定义也删了）；_is_bard_skill 零残留
# c) 行为门禁：echo 无生产者 → 现有测试本就不触发回声闭环（test_v1302c test_bard_echo_loop 测的是信仰负载，非 echo）
"$PY" tests/test_v1302c_mechanics.py
"$PY" tests/test_v130_resources.py      # 含 (cls_mu_shi,1) override 遗留注释与 echo max def 断言——仍绿（只查 core_resources）
# d) 诗人 smoke：test_v83_bard.py（v153 诗人独立职业，走 melody 引擎不碰 BARD_BRANCHES）
"$PY" tests/test_v83_bard.py
# e) 回声相关无回归：test_v1302f2（SHADOW_STEALTH/MOMENTUM 断言）、run_numeric_tests、run_all
# f) 风险点专项 smoke：牧师攻线 path1 转职（BRANCH_RESOURCE_OVERRIDE (cls_mu_shi,1)→resonance+echo）造战打 3 回合
#   断言：无伴奏被动→无回声+1；增益技持续 = skill_buff_turns（无回声续时）；日志无 🎵 回声驻留
```

---

### P1c — ZEN_HOLD_CFG 删除 + 测试同步（低风险，碰 battle_config + tests）

**改什么**：
1. battle_config.py L184-189 段（苦修士注释头 + `ZEN_HOLD_CFG` def）删；L255 注释（“禅意 zen：…靠 per-zen 加伤（ZEN_HOLD_CFG 每 1 禅意物理 +4%，引擎挂点 battle.py _zen_hold_mult）”）→ 改述“v151 已删（苦修士随 cls_wu_sheng 移除）；拳师蓄势 MOMENTUM_CFG 同型”
2. tests/test_v1302f2_engine_fix.py：**不删测试函数**（它断言的是 MOMENTUM_CFG 蓄势——存活）；只改文件头 docstring L8“（ZEN_HOLD_CFG）随隐藏职业删除——改断言：…”→“（苦修士 ZEN_HOLD_CFG）随 v151 删除——v151 后由拳师蓄势（MOMENTUM_CFG）承担持有加伤”（若该文件仍有任何 `import … ZEN_HOLD_CFG`/断言（L8 只有注释、L145-155 测 MOMENTUM），确认 grep 后仅注释清理）

**验证**：
```bash
"$PY" tests/test_v1302f2_engine_fix.py   # 2 个 test 全绿（潜行乘区 + 蓄势）
"$PY" tests/test_v130_resources.py       # MOMENTUM_CFG 断言若在（§2.1 表 31 无）——实际 MOMENTUM 断言在 test_v1302f2
# grep ZEN_HOLD_CFG → battle_config 定义删净；tests 仅 docstring 无引用
```
**若测试 L145-155 之前断言 ZEN_HOLD_CFG 常量存在（侦察显示实际已改为 MOMENTUM 断言，无需动）**——复核后若仍见常量断言，把断言改为“v151 已删：ZEN_HOLD_CFG 不存在于 battle_config（hasattr False）”。

---

## 3. Phase 2 批次细化（双源归一，中风险，逐机制）

> 前置：Phase 1 全绿 + P2C/P2D battle.py 批已 merge。P2a/P2b 串行。
> 归一原则：**同一机制数值只留一处权威；删的是“从未被引擎读”的那份；引擎当前读哪份就留哪份**（现状为准）。

### P2a — 连段 combo / 破绽 shaken / 回声 echo 双源归一（碰 battle_config + classes.py + battle_bars.py）

**子任务**：
1. **COMBO_CFG ↔ classes.py cls_ci_ke.combo（L338-342）双源**：
   - classes.combo dict 现网零读（引擎读 battle_config COMBO_CFG：battle.py `_combo_active/_combo_add/_combo_finish_min/_combo_dmg_mult` L2623-2694；`_combo_dmg_mult` per_layer/max_bonus；L6521 显示）→ **删 classes.py combo dict**，改注释“连段数值权威 = battle_config COMBO_CFG（P2E 后 = MECH_CFG['assassin_combo']）；chase_at/chase_power/inject_at/spin_lock 未实装设计，机制 TODO”
   - chase_at/chase_power/inject_at/spin_lock 是全仓零读字段 → 挪入 classes.py combo 位置的注释 TODO 块（不保留数值 dict）
   - battle_config COMBO_CFG 读点暂不动（Phase3 迁 MECH_CFG["assassin_combo"]）
2. **SHAKEN_CFG**：P1a 已删（含在 D3）；此处仅补 ENEMY_BAR_CFG["shaken"] 尾注（L397-398 已有“淬势者撼岳之势（SHAKEN_CFG 变体）…”注释）→ 改“（变体数值已随 P2E-P1a 删 SHAKEN_CFG；未来淬势者=本子键加参数，不新开常量）”
3. **ECHO_CFG ↔ core_resources echo.max（L141-147）双源同值**：core_resources echo dict 的 `max:3` 与 ECHO_CFG.max_layers=3 重复。引擎回声叠层走 `_echo_add`（mech_stacks 槽 + ECHO_CFG.max_layers），**不走上限注册** → core_resources echo.max 是展示/注册死字段。处置：core_resources echo dict 注明 `# max 字段=展示用（叠层实际由 ECHO_CFG.max_layers/MECH_CFG['echo'] 管）；引擎 _res_gain echo→mech_stacks 不经 core_resource_gain_key`，**不删**（CORE_RESOURCES 注册表 key 需存在以支持 _branch_keys/资源所有权查询）。echo 字段 value 归一处 = Phase3 MECH_CFG["echo"]
4. **classes.py 死字段总账（本批只清 combo）**：charge(L215)/support(L277)/vent(L208)/dual_form/focus 等 classes 侧字段——**本批不碰**（§4 风险 6：命令层 UI 展示读 classes 字段——finisher_threshold 等留 UI/数据批次）。仅在 classes.py 头注追加“P2E：classes 内机制参数字段与 battle_config/core_resources 并存属历史双源；删除评估在数据批次，引擎读 core_resources”

**验证**：
```bash
"$PY" tests/test_v130_resources.py    # 连段 5 段断言（BC.COMBO_CFG cap/finish_min/per/max_bonus + _combo_* 引擎行为）——全绿证明 COMBO_CFG 仍是活源
"$PY" tests/test_v1302c_mechanics.py  # 元素印记/反应/信仰负载
"$PY" tests/test_v1252_audit_closure.py
grep -rn "chase_at\|spin_lock\|inject_at\|chase_power" game/ tests/ | grep -v __pycache__   # 期望仅 classes.py 注释 TODO（零代码读）
grep -rn "\.combo\b\|get(\"combo\"" game/battle.py | grep -v COMBO_CFG    # 引擎无 classes.combo 读点确认
"$PY" scripts/run_numeric_tests.py && "$PY" scripts/run_all_tests.py
```
**行为零变化判据**：classes.combo 零读 → 删除后引擎读值不变（仍 COMBO_CFG）。

---

### P2b — 职业字段取代 CFG 兜底族 + 三处并存收敛（碰 battle_config + battle_modes.py + battle_bars.py + battle.py 小段）

**子任务**：
1. **兜底字典语义核对（前置复核，非删）**：battle_modes `_battle_cfg()` cfg_map 读 DUAL_FORM_CFG/FOCUS_CFG/VENT_CFG；battle_bars 读 ENEMY_BAR_CFG/CHARGE_CFG。P1a 未删这 5 个（活兜底）。现网职业字段键齐全性：core_resources 六个职业块（cls_zhan_shi/cls_fa_shi/cls_you_xia/cls_mu_shi/cls_ci_ke/cls_wu_seng）只有 zhan_shi(dual_form)/fa_shi(focus)/you_xia(vent) 三块带机制字段；**cls_dragon_oath/cls_shadow_blade/cls_chronomancer/cls_wild_hunter/cls_wu_sheng 不在 CORE_RESOURCES**（这些是旧隐藏职业/设计，现网 classes.py 亦无独立键？→ 复核 classes.py 职业键全集 + core_resource_def 解析链）。**结论待批内复核**：
   - 若现网唯一走兜底路径的 = cls_zhan_shi/fury 等已带全键职业 → 兜底字典“从不命中”成立，可把 CFG 语义改为“MECH_CFG['dual_form'/'focus'/'vent'/'charge'] 纯默认值段，改读法不改值”（Phase3 统一查表，本批不动数值）
   - **不删** DUAL_FORM_CFG/FOCUS_CFG/VENT_CFG/CHARGE_CFG（P1a 已排除）；仅清理 VENT_CFG 注释里已删常量名（ENERGY_VENT/VENT_AT/…星语族已在 P1a 删）→ 注释改述
2. **charge 数据层悬空收口（§3.2 电荷制）**：skills.py 全表 0 处 `charge_cfg`、classes.py cls_you_xia.charge(L215) 零读 → 本批把 classes.charge dict 标注释“死字段：技能无 charge_cfg 挂载、引擎兜底读 battle_config CHARGE_CFG；删除归数据批次”；**CHARGE_CFG 保留**（battle_bars charge_def `_cfg(_battle_cfg("charge"),…)` 兜底活源——L195/218/227/234/248/262/263）
3. **battle.py 字面量回填（TENACITY/磐核——可选回填批）**：battle.py `_tenacity_try_break@4948`（2 层战意/3 次）与 battle_mech `_m_guard_core_burst@1956`（0.7×cores）字面——P1a 已删其 CFG。**回填 = 改 handler 读 MECH_CFG["tenacity"]/["guard_core"]（数值=现字面）**——改动 battle.py/battle_mech 各 1 行，行为零变化（字面值原样搬表）。属可选项：若执行 agent 判断回填收益低，可留“字面量档案”在 commit message 即可（P2E 文档 §3.3 T1 允许此路线）。**本任务书建议：暂不回填，字面量行号记入 commit（保守，避免引入新读表面）**——除非鱼鱼要求“数值权威化”再单独小批。
4. **data/__init__.py 聚合导出不动**（只导出存活 18 个：MECH_STACK_BONUS/WHITELIST/DOT_*/ELEMENT_REACTIONS/BOSS_ATTACK_MULTS/CONTROL/SKILL_CC/MECH_FULL_HP/FROZEN/COMBO_STACKS/PROC_GROUPS/STAT_PASSIVES/QUALITY_4）——P1a 删的都不在其中，无需改

**验证**：
```bash
# battle_modes/battle_bars 纯函数直测（dual_form/focus/vent/charge/enemy_bar 各取现网职业路径）
"$PY" -c "import sys; sys.path.insert(0,'tests'); from conftest import *; " ...  # 或跑现有机制测试
"$PY" tests/test_v130_resources.py && "$PY" tests/test_v1302c_mechanics.py && "$PY" tests/test_v1252_audit_closure.py
"$PY" scripts/run_numeric_tests.py && "$PY" scripts/run_all_tests.py
# 复核：core_resources 现网职业（6 基础 + 副资源键）字段覆盖 vs battle_modes/battle_bars 兜底命中路径 —— 产出一行结论写 commit
grep -rn "charge_cfg" game/data/skills.py    # 期望 0（维持现状；若未来接线 charge 需先立技能数据）
```

---

## 4. Phase 3 批次细化（MECH_CFG 单表成型 + 读点迁移，纯寻址，低-中风险）

> 方案 §4.4 **方案 A**：battle_config.py 内部重构为 MECH_CFG 单 dict + 引擎固有段（TIER_GROWTH/BRANCH_* 保持原位）。**不新建文件**。过渡期对外兼容层可选：保留顶层旧名别名 `COMBO_CFG = MECH_CFG["assassin_combo"]`（供 tests/scripts 未同步前不炸）——P2D-D0 先例：数据层承诺“加一行零改引擎”。**推荐：测试断言同步改读 MECH_CFG，兼容别名仅 P3b 过渡提交存在，P3c 移除**。

### P3a — MECH_CFG 结构落地 + 非 battle 消费点迁移（不碰 battle.py 顶部 import 主体？——见下，3a 允许动 battle.py 内 501 行函数内延迟 import 段与 2501 显示读点，但**建议 P3b 一次性**）

**MECH_CFG 结构**（放 battle_config.py 顶部或 v176 段后）：
```python
MECH_CFG = {
    # 机制键表（原通用表键名不变，直接收编）
    "dot":     {**DOT_DEFS, "boss_pct_mult": DOT_BOSS_PCT_MULT, "pct_cap": DOT_PCT_CAP,
                "bleed_double_hp_pct": DOT_BLEED_DOUBLE_HP_PCT, "adapt_decay_step": DOT_ADAPT_DECAY_STEP,
                "resist_cap": DOT_RESIST_CAP},
    "mech_stack": {"bonus": MECH_STACK_BONUS, "whitelist": MECH_STACK_WHITELIST, "max": MECH_STACK_MAX},
    "buff":       {"mult": BUFF_MULT, "team_keys": TEAM_BUFF_KEYS},
    "element":    {"reactions": ELEMENT_REACTIONS, "reaction_table": REACTION_TABLE,
                   "marks_max": ELEMENT_MARKS_MAX, "mark_gain_per_hit": ELEMENT_MARK_GAIN_PER_HIT,
                   "same_cast_extra_charge": ELEMENT_SAME_CAST_EXTRA_CHARGE},
    "crit":       {"lucky_chance": LUCKY_CRIT_CHANCE, "lucky_mult": LUCKY_CRIT_MULT,
                   "luck_conv": LUCK_CRIT_CONV, "multi_hit_first_only": MULTI_HIT_CRIT_FIRST_ONLY,
                   "full_hp_mechs": MECH_FULL_HP_CRIT, "frozen_mult": MECH_FROZEN_MULT,
                   "combo_mechs": MECH_COMBO_STACKS},
    "ctrl":       {"mechs": CONTROL_MECHS, "skill_cc_whitelist": SKILL_CC_WHITELIST,
                   "proc_groups": MECH_PROC_GROUPS, "stat_passives": MECH_STAT_PASSIVES},
    "boss":       {"attack_mults": BOSS_ATTACK_MULTS},
    "enemy_bar":  ENEMY_BAR_CFG,
    # 机制键（职业化 CFG 收敛后按机制命名；原 CFG dict 值原样搬，键名变化仅此一处）
    "dual_form":  DUAL_FORM_CFG, "focus": FOCUS_CFG, "vent": VENT_CFG, "charge": CHARGE_CFG,
    "assassin_combo": {**COMBO_CFG, "on_crit_gain": ASSASSIN_ON_CRIT_GAIN,
                       "on_take_hit_penalty": ASSASSIN_ON_TAKE_HIT_PENALTY},
    "shadow_step": SHADOW_STEP_CFG,
    "echo":       ECHO_CFG,
    "full_tension": ENERGY_HIGH,
    "blood_debt_gain": RAGE_GAIN_HP_SCALE,
    "branch_resources": BRANCH_RESOURCE_OVERRIDE,
    "chi_hold_dmg": MOMENTUM_CFG,
    # 引擎固有/经济域不入表：TIER_GROWTH/BRANCH_BONUS/BRANCH_BONUS_BY_CLASS（engine/命令层读，保持原位）；
    # QUALITY_UPGRADE_* / MASTERPIECE_CHANCE（economy 域，保持原位+C 导出）
    # SHADOW_STEALTH_DMG_MULT（技能名键表→内容名；P2E 文档建议迁 skills 条目 stealth_mult 字段——本批不动，另行 TODO）
}
def mech_cfg(mech: str) -> dict:   # 查表辅助（core 状态机 _battle_cfg 同形态推广）
    return MECH_CFG.get(mech, {})
```
> ⚠️ 键命名最终以 Phase2 归一后存活字段为准；**数值一字不改**（P2E 与 P2-C 同款“以现状为准”）。
> ⚠️ `ELEMENT_MARK_GAIN_PER_HIT` 侦察标记“疑似只剩 import 死链路”（battle.py 仅 L29 import、无读点）——P3a 复核后若确认零读 → 同 P1a 流程单删（并入 P3a 或单列 P3a-2，需人确认，因它属 52 消费名单、删前 grep 全仓）。

**非 battle 消费点迁移**（P3a 范围）：
| 文件 | 改什么 |
|---|---|
| game/engine.py | L6 import 5 常量 → `from .data.battle_config import MECH_CFG, ELEMENT_REACTIONS, TIER_GROWTH, BRANCH_BONUS, BRANCH_BONUS_BY_CLASS, MECH_STACK_MAX`（引擎固有段保 import 兼容）或 `MECH_CFG` 读；读点 L40（ELEMENT_REACTIONS→`MECH_CFG["element"]["reactions"]`）、L118（MECH_STACK_MAX→`MECH_CFG["mech_stack"]["max"]`）、L134/147（TIER_GROWTH/BRANCH_* 保原位不迁） |
| game/core/battle_bars.py | `_battle_cfg()` 两 cfg_map 分支 → 查 `MECH_CFG`（相对导入 `..data.battle_config import MECH_CFG`；cfg_map={"enemy_bar": MECH_CFG["enemy_bar"], "charge": MECH_CFG["charge"]}） |
| game/core/battle_modes.py | 同上（dual_form/focus/vent → MECH_CFG） |
| game/commands/economy.py | QUALITY_* 读点（L1867-1888）经 C. 聚合不变——原位不动；**不迁**（economy 域结论） |
| scripts/numeric_lib/player.py | L462 `from …battle_config import DOT_DEFS, DOT_BOSS_PCT_MULT, DOT_PCT_CAP` → `MECH_CFG` 读（`MECH_CFG["dot"]` 子键）或保 import 别名（若保留顶层旧名兼容层则零改动） |
| tests | 逐个 import 断言改读 `MECH_CFG[机制键]`（见 §5 测试同步表） |
| game/data/__init__.py | 聚合导出 18 个保原样（P1a 后存活集合）；MECH_CFG 建议加导出（`from .battle_config import MECH_CFG`）供命令层/测试 |

**验证**：每文件改完 py_compile + 对应单测；最后 engine/battle_bars/battle_modes/battle_mech import + `_battle_cfg` 纯函数冒烟；numeric 全量。

### P3b — battle.py 全量读点迁移（独占 battle.py，~150-200 行机械替换）

**改什么**：
1. 顶部 import L22-36 36 常量 → `from .data.battle_config import MECH_CFG as _MC`（或保留个别原位段常量）。battle.py 内全部读点按 §2.1 归属列机械替换（读点行号基线，P1b 后漂移 ±10）：
   - `DOT_DEFS`/DOT_5 子键 → `_MC["dot"]`（L568/569/590/8799-8965/9342 等 15 处）
   - `MECH_STACK_BONUS` → `_MC["mech_stack"]["bonus"]`；`MECH_STACK_WHITELIST` → `["whitelist"]`；L4853 注释 MECH_STACK_MAX → `["max"]`
   - `MECH_FULL_HP_CRIT` → `_MC["crit"]["full_hp_mechs"]`；`MECH_FROZEN_MULT` → `["frozen_mult"]`；`MECH_COMBO_STACKS` → `["combo_mechs"]`；`MECH_PROC_GROUPS` → `_MC["ctrl"]["proc_groups"]`；`MECH_STAT_PASSIVES` → `["stat_passives"]`
   - `CONTROL_MECHS` → `_MC["ctrl"]["mechs"]`；`SKILL_CC_WHITELIST` → `["skill_cc_whitelist"]`
   - `BOSS_ATTACK_MULTS` → `_MC["boss"]["attack_mults"]`
   - `REACTION_TABLE` → `_MC["element"]["reaction_table"]`；`ELEMENT_MARKS_MAX` → `["marks_max"]`；`ELEMENT_MARK_GAIN_PER_HIT`（若复核存活）→ `["mark_gain_per_hit"]`；`ELEMENT_SAME_CAST_EXTRA_CHARGE` → `["same_cast_extra_charge"]`
   - `LUCKY_CRIT_CHANCE/MULT`、`LUCK_CRIT_CONV`、`MULTI_HIT_CRIT_FIRST_ONLY` → `_MC["crit"][…]`
   - `BUFF_MULT` → `_MC["buff"]["mult"]`；`TEAM_BUFF_KEYS` → `_MC["buff"]["team_keys"]`
   - `RAGE_GAIN_HP_SCALE` → `_MC["blood_debt_gain"]`；`ENERGY_HIGH` → `_MC["full_tension"]`；`MOMENTUM_CFG` → `_MC["chi_hold_dmg"]`；`COMBO_CFG` → `_MC["assassin_combo"]`；`ASSASSIN_ON_CRIT_GAIN` → `[“assassin_combo”][“on_crit_gain”]`；`ASSASSIN_ON_TAKE_HIT_PENALTY` → `["on_take_hit_penalty"]`；`SHADOW_STEP_CFG` → `_MC["shadow_step"]`；`SHADOW_STEALTH_DMG_MULT` → **保原位**（内容名键表待迁 skills 条目，本批不动或加 `_MC["stealth_mult"]` 引用别名）；`ECHO_CFG` → `_MC["echo"]`（L501 函数内延迟 import、L2501 显示、L2811/6311 若存活——6311 已在 P1b 删）；`BRANCH_RESOURCE_OVERRIDE` → `_MC["branch_resources"]`
2. `_is_element_mage`/`_branch_keys` 读 BRANCH_RESOURCE_OVERRIDE（L1777/1810-1816）同步
3. `_resource_label` L2501 `ECHO_CFG['max_layers']` → `_MC["echo"].get("max_layers",3)`
4. 顶部模块级 `_TICK_HANDLERS`/`_th_echo_heal`（L501-517 函数内延迟 import ECHO_CFG）同步

**替换纪律**：每处替换 = 纯文本等价（`X.get(k, default)` → `_MC["mech"].get(k, default)`），**default 值原样保留**（引擎 .get 兜底不可丢——防未来表缺键行为漂移）；凡 `X['key']` 直取改 `.get(key)` 保守化需逐点人工确认等价（值必在表内可保持 `[...]`，但推荐统一 `.get` + 原位默认）。

**验证清单**：
```bash
# 语法 + import
"$PY" -m py_compile game/battle.py
"$PY" -c "import sys; sys.path.insert(0,'.'); from game import battle; print('battle import ok')"
# 读点全量替换复核（每常量旧名在 battle.py 只剩注释/零残留）：
for c in COMBO_CFG ENERGY_HIGH MOMENTUM_CFG ECHO_CFG RAGE_GAIN_HP_SCALE SHADOW_STEP_CFG BUFF_MULT TEAM_BUFF_KEYS; do grep -c "\b$c\b" game/battle.py; done  # 期望 0（或仅 docstring 白名单）
# 单测全家桶（重点：v1252 identity 断言需改为 MECH_CFG identity —— BT.MECH_CFG is C.MECH_CFG）
"$PY" tests/test_v1252_audit_closure.py && "$PY" tests/test_v130_resources.py && "$PY" tests/test_v1302f2_engine_fix.py && "$PY" tests/test_v1302f3_qa_fixes.py && "$PY" tests/test_v138_dot.py && "$PY" tests/test_v1302c_mechanics.py && "$PY" tests/test_numeric_p0_effect_fixes.py && "$PY" tests/test_v83_bard.py
# numeric 全量 + run_all 全量（318 → 与基线同绿）
# 行为快照：conftest 造 6 职业×满装×代表技能战斗 OLD vs NEW logs+资源+结算 diff 恒等（P2E §7.1 三层验证第 3 层；若 P3b 已过全量可抽 3 职业冒烟）
```

### P3c — 测试/文档收尾（碰 tests + docs，不碰 game/）

**改什么**：
1. test_v1252_audit_closure.py L388-397 断言从“BT.X is C.X”改为“BT.MECH_CFG is C.MECH_CFG（identity）”；新增“MECH_CFG 结构断言”：`MECH_CFG["dot"]["boss_pct_mult"] == 0.5`、`MECH_CFG["assassin_combo"]["cap"]==10`、`["mech_stack"]["max"]["poison"]==5`、`["ctrl"]["mechs"]==("stun","freeze","silence")` 等（数值=现状表值）
2. test_v130_resources.py：`BC.COMBO_CFG` → `BC.MECH_CFG["assassin_combo"]`；`BC.RAGE_GAIN_HP_SCALE` → `BC.MECH_CFG["blood_debt_gain"]`；`BC.BRANCH_RESOURCE_OVERRIDE` → `BC.MECH_CFG["branch_resources"]`
3. test_v1302f2_engine_fix.py：`MOMENTUM_CFG` → `MECH_CFG["chi_hold_dmg"]`；`SHADOW_STEALTH_DMG_MULT` 保原位（或按 stealth_mult 落位）
4. test_v1302f3：`BC.SHADOW_STEALTH_DMG_MULT` 同步；test_v1302c import BC 检查
5. test_v138_dot / test_numeric_p0_effect_fixes：`DOT_DEFS` → `MECH_CFG["dot"]`（保留顶层别名则零改动）
6. scripts/numeric_lib/player.py 同步（若 P3a 未做）
7. docs 联动（§8）：REFACTOR_PLAN_v181.md P2-E 标记完成；ARCHITECTURE_TARGET_STATE_v181.md §P2E 勾选；CLASS_MECHANICS_v153/CLASS_REDESIGN_FRAMEWORK_v150 已死常量引用标注“已删，数值见 X”；P2E_mech_cfg.md 附录回写删除清单

**验证**：全量 `run_numeric_tests.py` + `run_all_tests.py`；grep 全仓旧常量名（除 docs 标注外零残留）；`git diff --stat` 净减 ~400 行。

---

## 5. 验证门禁汇总（每批必过）

| 门禁 | 命令 | 期望 |
|---|---|---|
| 语法 | `"$PY" -m py_compile <改动文件>` | exit 0 |
| 零残留 | `grep -rn --include='*.py' '\b<常量名>\b' game/ tests/ scripts/` | 零输出（批内注释白名单除外） |
| 专项单测 | 每批“验证清单”列出的 tests | 全绿，绿数 ≥ 基线 |
| numeric 门禁 | `"$PY" scripts/run_numeric_tests.py` | 全绿（当前 52/52 或按 run_numeric 输出口径；P2E 零数值改动 → 绿数必须与基线一致） |
| 全量回归 | `"$PY" scripts/run_all_tests.py` | 318 测试与基线同绿数（死表本就不该有任何测试依赖——若某测试读死表 → 不是真死，打回 P1a 复核） |
| 行为快照 | P2E §7.1 第 3 层（Phase 2/3 用） | OLD/NEW 战斗 logs+资源+结算 diff 恒等 |

> **numeric 门禁注**：run_numeric_tests.py 以子进程跑 tests/test_numeric_*.py；若 P3a 改了 scripts/numeric_lib 的 import，numeric 全量必须重跑（模拟器读 DOT_* 常量点 = scripts/numeric_lib/player.py L462）。

---

## 6. 风险点与缓解（含误删 classes.py 字段风险）

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| 1 | 死表删除误删“被 import 但链在 data/__init__ 聚合”的常量 → 运行崩 | 中 | data/__init__.py 只 re-export 18 个（全在存活列）；P1a 删除批先全仓 grep（§1.2 步骤 1） |
| 2 | 死表数值是引擎字面量的“唯一档案”，删后调数值无档案 | 中 | 每常量行为源证据行（§1.1 理由列 + 附录 A 文件:行）抄 commit message；docs 标注“数值见 X” |
| 3 | BARD_BRANCHES 删除影响伴奏触发/回声续时链（4553/6310） | 中 | 现网恒 False 证据（分支名无命中 + 伴奏技能数据已删）；删除前跑 test_v1302c/test_v130_resources/test_v83_bard + 牧师攻线 3 回合 smoke |
| 4 | ZEN_HOLD_CFG 测试引用 | 低 | P1c 改测试 docstring/断言同步 |
| 5 | Phase 3 读点替换漏点/误改 .get 语义 → 行为变化 | 低-中 | 机械替换 default 原样保留；全量单测 + numeric + 行为快照（§7.1 第 3 层） |
| 6 | **classes.py 死字段（combo/charge/support/vent/finisher_threshold 等）误删影响命令层 UI** | 低 | **只删 battle_config 侧；classes.py 数据声明（finisher_threshold.options 被 commands/combat.py battle_prefs_form/finisher L3169-3230 展示读、combo dict 被 classes 描述体系引用）一律留待 UI/数据批次统一评估**；本 P2E 唯一动 classes.py 的动作 = P2a 删 cls_ci_ke.combo dict（零读证据：engine/battle/commands 无 `chase_at/spin_lock/inject_at` 读点）+ 注释 TODO；charge/support/vent 类同只标注释不删 |
| 7 | 命令层 battle_prefs UI 读 classes.finisher_threshold 而 P1a 删了 battle_config 版 → UI 无感 | 低 | battle_prefs 读 classes.py（L332 options/default）不读 battle_config 常量 → 删除零影响；§3.1 证据：commands/combat.py L3164 注释“classes.py finisher_threshold.options” |
| 8 | 引擎字面量档案缺失（TENACITY/磐核 0.7/curse turns8/bone_rush 0.9/soul_mark 6%） | 低 | 已选择“暂不回填”保守路线；字面量行号记 commit（battle_mech L1463/2053/2065/2089/2101/2107/1956、battle.py L4948） |
| 9 | potion_effects eff_reaction 引用 REACTION_TABLE 未 import（NameError 隐患，只在使用元素共鸣石时触发） | 中（存量） | 非本 P2E 引入；P3a 迁移 REACTION_TABLE 到 MECH_CFG 时**一并修**：eff_reaction 函数内延迟 `from ..data.battle_config import MECH_CFG` 读 `MECH_CFG["element"]["reaction_table"]`（或查 battle._reaction_table_resolve 已封装的读表）——行为等价且消灭隐晦 NameError |
| 10 | ELEMENT_MARK_GAIN_PER_HIT 疑似 import 死链路（52 名单内） | 低 | P3a 复核（battle.py 仅 L29 import 无读点）：确认零读 → 单删 + grep 门禁；保守则随 MECH_CFG["element"]["mark_gain_per_hit"] 收编不删 |
| 11 | Phase2/3 与其它 battle.py 批（P2C-C9/C10、P2D-D2、P1-B/C、P2-B/D、P2G、P3 e_buffs）撞文件 | 中 | 严格串行：查 HANDOFF“进行中”列；一个文件同一时刻只允许一个 agent；P3b 独占期最长（~90 行读点替换） |
| 12 | test_v1252_audit_closure identity 断言（BT.X is C.X）在 P3b 改名后红 | 低 | P3c 同步为 MECH_CFG identity；P3b 过渡期若保顶层旧名兼容别名则不断 |
| 13 | docs/design 大量引用已死常量名（CLASS_MECHANICS_v153/CLASS_REDESIGN_FRAMEWORK_v150/design/new_world/v139_*.md） | 低 | 不改设计稿数值语义；标注“已删（P2E），数值见 X”或 commit message 全量列出 |

---

## 7. 派工建议（主 agent 排期）

1. **P1a（死表 43 删）** → 独立 agent，先派（零行为风险，唯一碰 battle_config+2 注释）。
2. **P1b（BARD_BRANCHES 退役）** 与 **P1c（ZEN_HOLD_CFG）** → 串行或同 agent 连做（都碰 battle_config；P1b 还碰 battle.py 顶部 import/4553/6310/2819——**battle.py 所有权窗口**：若 P2C-C9/C10/P2D-D2 并行进行中，P1b 需等其 merge 或走“侦察补丁→主 agent 合并”路线）。
3. **P2a/P2b（双源归一）** → 等 Phase1 全绿 + battle.py 无并行批后开；P2a 动 classes.py（低风险小段）+ battle_config；P2b 主要复核 + 注释（改动极小）。
4. **P3a（建表 + 非 battle 消费点）** → 可单独 agent（engine/battle_bars/battle_modes/economy/scripts/tests），**不动 battle.py**。
5. **P3b（battle.py 全量读点迁移）** → 独占 battle.py 的 agent，P3a merge 后开。
6. **P3c（测试/文档收尾）** → 最后 agent，跑全量门禁。
7. 每批独立 commit + 门禁；最终 P2E 完成判定（北极星 §P2E）：battle_config 顶层无职业名常量；读点按机制名查 MECH_CFG；无双源；无死表（grep 全仓零残留）。

---

## 附录 A：P1a 43 个删除常量 → 行为源证据行（commit message 用）

| 常量 | 行为真实源（文件:行） |
|---|---|
| BONE_RUSH_CFG | battle_mech `_m_bone_rush` L2089 `0.9*n`；`_m_sacrifice` L2101 `0.9` |
| CURSE_CFG | battle_mech `_m_curse` L2065 turns=8；`_m_curse_refresh` L2074；ENEMY_BAR_CFG["curse"] 注释 vuln/acc |
| SOUL_MARK_CFG | battle_mech `_m_soul_mark` L2053 6%/cap3；battle.py 7397-7405 |
| SHAKEN_CFG | ENEMY_BAR_CFG["shaken"]（活源） |
| COUNTER_CFG / STANCE_COUNTER | battle.py 受击反击族 10626+（套装 effect/技能 counter_attack 字段/字面） |
| DRAGON_FORM | core_resources cls_dragon_oath.dual_form（实际值）+ battle_modes 读职业字段 |
| MAGE_FOCUS_CFG / CHRONOMANCER_STASIS_CFG | core_resources cls_fa_shi.focus / stasis 字段 |
| SHADOW_DANCE_CFG | core_resources cls_shadow_blade.dual_form(auto_enter/duration/lock_gain)；battle_modes dual_form_enter 读 d.duration |
| ENERGY_VENT / VENT_AT / VENT_AUTO / VENT_MAX_DELAY / VENT_RECOVERY_EXTRA | core_resources cls_you_xia.vent（trigger 999 v153 废弃）；星语者 v151 删 |
| TENACITY_CFG | battle.py `_tenacity_try_break` L4948 字面（2 层战意/3 次）——CFG 语义冲突=错误档案 |
| GUARD_CORE_CFG | battle_mech `_m_guard_core_burst` L1956 `0.7×cores`；battle.py `_guard_core_n` L4848 |
| VOW_CFG | skills.py 圣辉涤净 effect=cleanse_all + reduce_all 字段（v169.7）；vow 资源无 res_gain/无 BRANCH 覆盖 |
| BARD_DAWN_HYMN_POWER | skills.py “破晓长歌” L3811 power 195%+130（≠CFG 3.20） |
| BARD_SELF_GAIN_FACTOR / DIRGE_CFG | 双行折算无实装；classes 注释 55% |
| BARD_WEAPON_RHYTHM | 谱曲节奏无实装（skills 无 compose 消费） |
| ASSASSIN_HIT_FEED / SPIN_LOCK / COMBO_REFLOW_* / CHAIN_DANCE / CORRODE / POISON_BURST_CP | classes.py cls_ci_ke.combo dict（chase/inject/spin 零读）；battle_mech `_m_poison_burst_finisher` L2107 per=0.14 字面 |
| IDLE_FLOOR_TURNS | 亡灵祭仪保底律无实装（battle.py L409 仅信念衰减） |
| RANGER_CHARGE_CFG | charge_cfg 技能字段全表 0 处；classes cls_you_xia.charge 零读；CHARGE_CFG 是活兜底（battle_bars L195+）——只删 classes/注释侧 |
| RANGER_SNIPE_REACH / BACK_ROW_MULT / HUNT_FINALE_POWER | skills.py 条目（穿心箭/死神之箭 res_cost/cond/reach 字段） |
| ASTRO_SHIELD_CFG / STARSTEP_CFG / STAR_LOCK_CFG | 星语者 v151 删；星轨锁定 effect battle_mech `_sb_star_lock` L1463（0.12 字面） |
| BERSERKER_DUAL_ATTACK / ENTRY_STRIKE / MASTERY_KEEP / RAGE_POTION_GAIN | core_resources cls_zhan_shi.dual_form（maintain 0.6/hit 1/…）；potion_effects `eff_crit_dmg_pot` L171（+25% 暴伤乘算，无怒气+3）；技能表 exprs |
| HUNT_MARK_CRIT_EXTRA | v151 删除；battle.py `_on_crit_resource` L5171 注释“已移除” |
| ASSASSIN_FINISHER_THRESHOLD | classes.py cls_ci_ke.finisher_threshold（UI 数据声明）+ commands/combat.py battle_prefs_finisher L3262；引擎零读 battle_prefs.finisher |

---
*（end of task book — 依据 docs/REFACTOR_P2E_mech_cfg.md，侦察基线 master c61f48b / wt_p2e 方案 commit 7083dbe；执行前复核行号）*
