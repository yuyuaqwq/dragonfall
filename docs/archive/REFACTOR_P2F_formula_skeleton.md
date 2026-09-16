# P2-F 底层公式骨架公式化（P2F）— 只读侦察 + 方案设计（wt_p2f）

> 任务：ARCHITECTURE_TARGET_STATE_v181.md「P2 剩余任务方向校准」中鱼鱼 2026-09-07 拍板的
> **底层公式骨架公式化**方向。本文档为**只读侦察 + 方案设计**（未改任何 game/ 代码），落地给后续实施批次用。
> 侦察基线：master `329989c`（含 v181.P2A/P2D 已合并），worktree w4（wt_p2f，与 master 同 commit）。
> 铁律：**行为零变化**；每步 py_compile + 数值门禁绿；data 纯 dict 零函数；core 执行器；表达式用现成 formula_expr。
> 文档只 commit 到 wt_p2f 分支供主 agent 审阅，不合并、不动主仓。

---

## 0. TL;DR

"底层公式骨架"= 引擎数值的**最后一块硬编码层**：公式本体（非线性减伤 / 成长线性叠加 / 兜底幂函数 / 分段曲线斜率）+ 系数（0.15 波动、1.5 暴击、0.9/0.6 怪物经济斜率…）仍写在 Python 函数体里。
数据化 ≠ 一定表达式化。按**难度与风险**分三类推进：

1. **纯参数搬 data（低风险，先做）**：calc_damage 的 variance/暴击倍率/下限、monster_exp/gold 的 1.5/1.3/0.9/0.6/0.7/0.5 指数、_EXP_TABLE 兜底幂函数系数、skill_* 成长默认值 → 全部进一张 `FORMULA_SKELETON` dict，函数体内只留 `读 key 套模板` 的声明式外壳。
2. **公式结构表达式化（中风险）**：calc_damage 的 `atk²/(atk+def)` 减伤段、equip_stats 的线性结构、hp_stage_mult/_stage_mult 分段曲线 → 用现成 `formula_expr` 表达式字符串 + `_stage_mult` 表驱动。**calc_damage 不建议整函数表达式化**（分支/截断顺序/random 是硬逻辑，见 §3）。
3. **结构性声明（高难度，最后）**：player_base_stats 的 7 属性循环 × tier/种族/branch 三段乘区、monster_stats 的分支链 → 属性成长泛化为「声明式模板 + 通用执行器」。

文档按"一公式一表"给全量清单（§2）+ calc_damage 专项（§3）+ 数据表草案（§4）+ 分阶段（§5）+ 风险/门禁（§6）。

---

## 1. 北极星与本任务的定位

ARCHITECTURE_TARGET_STATE_v181.md 三层模型：**数值在 data / 执行器在 core / 编排在 battle**；data 不放函数。
P2A/P2D 收编了套装表、被动 proc 注册表；本任务对准最后一层——**数值公式本身**（引擎的"骨架"）。
判定问题（沿用北极星 §判定标准）：

1. 这个值/斜率/指数/倍率 → 必须进 data（dict 项）。
2. 公式**结构**（`atk²/(atk+def)` 这种形态）→ 能写成表达式字符串就用 formula_expr；
   带分支/截断/随机 → 保留引擎执行器，把**纯参数**抽出。
3. 内容名/公式名不得进 core 逻辑；注册表/解释器分发。

**范围红线**：本任务只动"公式骨架"（计算核心），**不含**：
- battle.py 战斗编排/乘区链（v133 峰值红线已把乘区收敛到 battle_config 表——那是"乘区表"，不是本任务"骨架公式"）
- mech/buff/套装被动 proc（P2C/P2D/P2E 其它批次）
- 内容表（技能/装备/词条/副本），那些已是 data 且消费端读表

---

## 2. 全量公式清单（现状 → 难度 → 建议形态 → 守护测试）

> 调用点计数：`grep -rn`（含定义所在文件内部引用；不含 tests/scripts 消费）。
> 难度：低=纯数值搬 dict；中=公式结构声明化（表达式/表驱动）；高=带分支/截断序依赖的骨架。

| # | 公式 / 位置 | 公式本体（现状） | 数值来源 | 调用点 | 现状 | 难度 | 建议形态 | 守护测试 |
|---|---|---|---|---|---|---|---|---|
| F1 | `calc_damage` atk²/(atk+def) 减伤 + 穿透 + 真伤分支 + 波动 + 暴击×1.5 + 下限 | engine.py:1009-1037（见 §3 专项） | **全写死**（variance 默认 0.15、crit 1.5、pene cap 0.6、下限 1） | game 内 6 文件 50+ 处（battle 23 / affix 24 / weapon 6 / effect 4 / battle_mech 1 / skill_kinds 1 + engine resolve_formula 5 处段级转调），**测试 14 文件消费**；engine 外另有 scripts/numeric_lib 5 文件直调 | 混合（结构 in py，数值全写死） | **高**（分支+截断序+random，见 §3） | **参数化 + 表达式段**（保留函数壳，参数进 data；减伤表达式可选用 expr） | test_v106_pene（64）/ test_v107_dmg_type（21）/ test_numeric_basic_atk（10）/ test_numeric_formula（18）/ test_v160_exprs / test_numeric_skill_vs_basic / test_numeric_skill_efficiency / test_v180c_pet_isolation 等直测 calc_damage 的 14 文件 |
| F2 | `exp_to_next`：_EXP_TABLE 查表 + 超出 100 兜底 `int(60·lv^1.45+50)` | stats.py:226-253 | 表已 data 化（stats.py 模块级 _EXP_TABLE dict）；**兜底幂函数系数写死** | 7 处（engine 升级循环、instance 奖励等） | 表 data / 兜底公式 in py | **低** | 兜底公式**参数化**（base=60/exp=1.45/add=50 进 data；默认=现状） | test_core_engine（单调性）/ test_numeric_instance_reward / test_store_concurrency / test_v140_commands / test_legacy_schema_migration |
| F3 | `monster_exp`：`int(int(base×(1+lv×0.9)) × 1.5 × hp_stage_mult(lv)^0.7)` | stats.py:255-261 | base 表 data（MONSTER_EXP_BASE）；**0.9/1.5/0.7 写死** | 2（drops.py:438 + instances.py 通关奖） | 混合 | **低** | 纯参数搬 data（exp_linear_slope=0.9 / combat_len_mult=1.5 / hp_pow=0.7） | test_core_engine / test_numeric_instance_reward / test_numeric_reward_unify / test_numeric_economy_toolkit |
| F4 | `monster_gold`：`int(int(base×(1+lv×0.6)) × 1.3 × hp_stage_mult(lv)^0.5)` | stats.py:264-269 | base 表 data（MONSTER_GOLD_BASE）；**0.6/1.3/0.5 写死** | 2（drops.py:439 + instances.py） | 混合 | **低** | 同上（gold_linear_slope=0.6 / combat_len_mult=1.3 / hp_pow=0.5） | test_core_engine / test_numeric_instance_reward / test_numeric_economy_toolkit / test_numeric_reward_unify |
| F5 | `equip_stats`：`int((base[k]+scaling[k]×lv)×QUALITY.mult)` + weapon 分系重分配 + armor_family 乘区 + 暴击/项链修正 | stats.py:170-206 | base/scaling 表 data（stat_templates）；QUALITY data（equipment.py）；**结构写死**；**WEAPON_DIST/ARMOR_FAMILY 表仍在本文件**（stats.py:153-168，未下沉） | 17（economy/affix/drops/enchant/smith_stock + 自引用） | 混合（数值已 data / 结构+两表 in py） | **中** | WEAPON_DIST/ARMOR_FAMILY/ARMOR_FAMILY_ALIAS 下沉 data/equipment.py（纯 dict，零函数）；crit 公式 `0.02+0.01·lv/10` 与 mdef 修正 `+3·mult` 参数化；结构保留引擎（int 截断序） | test_numeric_equip_split（220）/ test_numeric_actor_equip / test_numeric_gear_full / test_v136_gem_drops 等装备族 |
| F6 | `player_base_stats`：`int(base[k]+growth[k]×(lv-1)×tier_mult×race_mult)` + branch 乘区 | engine.py:119-152 | base/growth data（classes.py）；TIER_GROWTH/BRANCH data（battle_config.py）；**7 属性循环 + 三段乘区结构写死** | 3（battle/面板/升级）+ 多间接（player_final_stats 等） | 混合 | **中-高** | 属性集循环改为读声明（`{stat: {base, growth, mult_tier, mult_race, branch_mode}}`）；branch crit 加法 vs 其余乘法是**结构特例**需声明；默认值=现状 | test_numeric_branch_bonus / test_numeric_panel_snapshot / test_numeric_actor_class / 全职业面板测试 |
| F7 | `skill_power_mult`：`1+(p/100)×(lv-1)`（p 已读 data SKILL_UP） | engine.py:881-886 | p 已 data（skill_up.py）；**公式结构写死**（1/100 系数、lv clamp） | 10（battle pmult 链 / 工具 / 显示） | 混合 | **低** | 参数化（per_lv_divisor=100 可配；缺省=现状），结构保留（clamp 语义是 max/min 硬逻辑） | test_numeric_skill_power（22）/ test_numeric_skill_vs_basic / test_commands_skills |
| F8 | `skill_flat_value`：`BASE + player_lv×PER + skill_lv×PER_SKILL` | engine.py:889-908 | **已 data 化**（skill_up.py SKILL_FLAT_*，v156） | 1+（battle 段级 7223 等） | **已达标** | — | 已公式化（样板），本任务仅列为参考 | test_v160_exprs / test_numeric_formula / test_numeric_skill_vs_basic |
| F9 | `skill_cond_mult` / `skill_mech_val` / `skill_buff_turns` / `skill_lifesteal_pct`：各自成长默认值（+0.05/级、每2级+1层、每级+1刻、每级+2%） | engine.py:911-946 | c/m/l 已 data（SKILL_UP）；**默认值写死**（0.05 / 2 / 1 / 2%、base_turns=3、base lifesteal 0.20） | skill_cond 4 / mech_val 4 / buff_turns 32 / lifesteal 少量（合计 ~40 消费点，battle+mech） | 混合 | **低** | 默认值参数化（进 FORMULA_SKELETON.skill_growth_defaults；battle_mech 内 65 个 handler 中 `int(total×n×0.12)` 类爆发系数**另属 P2C 不动**） | test_commands_skills / test_numeric_ctb_freq（回合数）/ test_numeric_skill_efficiency |
| F10 | `hp_stage_mult`：分段线性曲线 | stats.py:18-27 | **本函数内写死**（阈值 15/30/60 + 斜率 0.05/0.03/0.02） | 3（monster_stats + exp/gold 幂） | 公式 in py | **中** | 已存在**同款表驱动** `_stage_mult(segments, lv)`（stats.py:53-76）+ NORMAL_HP_STAGE_MULT 表 → hp_stage_mult 改为 **读同名表**（slope 语义与表一致：首段末值 1.0，当前 5 段斜率 → `((15,0),(30,0.05),(60,0.03),(999,0.02))` 精确等价，需逐 lv 1..200 验证 ±0） | test_numeric_monster_curve（180 断言含公式一致性）/ test_core_world / test_numeric_toolkit（curve_override 语义依赖 hp_stage_mult 可被替换） |
| F11 | `atk_stage_mult`：`lv≤30→1.0；否则 1.0+(lv-30)×0.004` | stats.py:30-38 | 写死 | 1（monster_stats）+ 测试 | 公式 in py | **低-中** | 参数化（cutoff=30/slope=0.004/起始值 1.0）或 `_stage_mult` 表化 `((30,0),(999,0.004))` | test_numeric_monster_curve / test_core_world（Lv60=608 断言） |
| F12 | `_boss_atk_stage`：`lv≤30→1.0；≤60→1-(lv-30)×0.005；否则 max(0.2, 0.85-(lv-60)×0.004)` | stats.py:41-50 | 写死（含 max clamp） | 2（monster_stats boss 分支）+ 测试 | 公式 in py | **中** | 表化 `((30,0),(60,-0.005),(999,-0.004))` + `floor: 0.2` 声明；⚠️ **两处 int 截断序**（int(线性×_boss_atk_stage) 后再 ×段乘区）是 monster_curve 门禁 ±1 敏感点，表驱动必须同构 | test_numeric_monster_curve（boss lv60 atk 1217 锁定）/ test_core_world |
| F13 | `_stage_mult` 通用分段表 | stats.py:53-76 | 表已 data（NORMAL_HP_STAGE_MULT/BOSS_ATK_STAGE_MULT/INSTANCE_BOSS_ATK_STAGE_MULT/ FIELD_TIER_MULT） | 3（monster_stats 消费）+ tools | **已达标** | — | 样板（本任务推广 F10/F11/F12 用同款） | test_numeric_monster_curve / test_v1252_config_consumption |
| F14 | `monster_stats`：`base+growth×(lv-1)` 线性 + boss/elite hp×min(1+lv×0.06/0.04, 3.0) + def×1.25/1.15 + dot_res 0.9/0.8 + 段乘区链 | stats.py:79-148 | base/growth data；**0.06/0.04/3.0/1.25/1.15/0.9/0.8 写死**；分支链写死 | 1（drops.py:396 统一消费）+ numeric_lib | 混合 | **高**（role 分支语义） | **角色修正参数化**（role_mods: {boss: {hp_cap_mult...}, elite: ...} 进 stat_templates，只把数值搬走，分支保留引擎——分支本身就是"角色模板差异"声明层）；def×1.25/1.15、dot_res 0.9/0.8 一并入表 | test_numeric_monster_curve（180）/ test_core_world / test_numeric_battle_matrix / test_numeric_monster_strength / test_numeric_stage_growth |
| F15 | `skill_learn_cost`：`need_lv//6+2`（技能点定价） | engine.py:741-744 | 写死 | 3（combat/player 学习扣点） | 公式 in py | **低** | 参数化（divisor=6/base=2 进 data） | test_commands_skills / 技能学习流程测试 |
| F16 | `prof_exp_need`：`5·lv²+15·lv`（副业经验曲线，core/constants.py:160-171） | constants.py | 写死（含 def 函数，constants.py 全文件唯一函数） | 少量（economy 副业） | 公式 in py | **低** | 参数化（a=5/b=15）或表化；**constants.py 混函数**本身待清（v125.2 B3 已把日奖励值下沉 prof_config，本曲线是剩件） | test_commands_economy（副业流程） |
| F17 | `DEFAULT_MAX_MP` 等 constants 已有 data 化常量 | constants.py:118-171 | 已 data（B3 收敛） | — | 已达标 | — | 样板 | — |
| F18 | mech 爆发系数（battle_mech 65 handler 内 `int(total×n×0.12)` 等） | battle_mech.py 各 handler | 写死 | mech 结算链 | 数值 in handler | 中 | **不属于本任务**（P2C weapon/handler 收编批）；仅记录 | mech 族测试 |

**骨架公式全量外沿补充**（已 data 化 / 已表达式化，作"达标样板"列此参考）：
- skill_flat_value / SKILL_FLAT_*（skill_up.py）— v156 已公式化
- SKILL_UP p/c/m/l（技能成长）— v56.4/v180 已 data
- TIER_GROWTH / BRANCH_BONUS_BY_CLASS / MECH_STACK_MAX（battle_config）— v181 P0-A 已下沉
- LUCKY_CRIT_CHANCE/MULT、MULTI_HIT_CRIT_FIRST_ONLY（battle_config）— v133 已下沉
- DOT_DEFS / DOT_BOSS_PCT_MULT / DOT_PCT_CAP（battle_config）— v156 已下沉
- PCT_CAPS / STAT_KEYS 等百分比上限（constants.py）— v106 已收敛
- resolve_formula 的 stat/mult/flat + expr 表达式段 — v156/v159 已表达式化（唯一官方表达式解释器入口）

---

## 3. calc_damage 专项（最高危，188→50+ 调用点横跨 7 文件 + scripts 系）

### 3.1 现状拆解（engine.py:1009-1037，逐行语义）

```
if dmg_type == "true" or pierce:        # ← 分支① 真伤/无视防御：dmg = atk
    dmg = atk
else:                                    # ← 分支② 物理/魔法走减伤：
    eff_def = def_                       #   v106 穿透：eff_def = max(0, int(def×(1-pct))-flat)
    ... cap pct ∈[0,0.6]（0.6 写死）、flat≥0；atk+eff_def≤0 → return 1（防除零）
    dmg = atk*atk/(atk+eff_def)          #   ← 核心减伤公式（v22 非线性）
dmg = max(1, dmg)                        # 下限 1（写死）
dmg = int(dmg × (1+U(-variance,+variance)))  # 波动（默认 0.15，调用方 battle.py 显式传 0.15 / 0 禁波动）
if is_crit:
    dmg = int(dmg × 1.5)                 # 暴击 ×1.5（写死；crit_dmg/残忍/幸运是 battle 段外另乘，不入此）
return max(1, dmg)                       # 二次下限
```

### 3.2 哪些能表达式化 / 哪些必须留引擎

| 段 | 能否表达式化 | 说明 |
|---|---|---|
| `atk²/(atk+def)` 减伤段 | ✅（formula_expr 现成支持：`(atk*atk)/(atk+def)`） | formula_expr 已支持 `+ - * / () 一元负号`；VARIABLE_WHITELIST 含 **atk/def/matk/mdef/max_hp/hp/spd/crit/player_lv/skill_lv/crit_mult/target_max_hp/base** → **atk/def 现成够用**；但 `eff_def`（穿透后有效防御）不在白名单 → 需新增变量或先算 eff_def 注入。**改动代价 vs 收益**：此段纯数值函数，换字符串表达式不带来新配置能力（"换配置=换公式"对骨架价值低，且引入编译/求值顺序/除零差异风险）→ **建议保留引擎写法，只参数化**（见 §4）。真要做"可换公式"（如改线性减伤），表达式化是唯一路径——门禁是"等值回测"（§6.3 全 atk/def 网格）。
| pierce/true 分支 + eff_def 穿透计算 | ❌ 必须留引擎 | max/min/int 截断 + `dmg_type`/`pierce` 布尔分派是**控制流**，非数值公式；表达式解释器无比较/分支原语 |
| `max(1, dmg)` 下限 / 除零兜底 `return 1` | ❌ 引擎（clamp 语义） | 可参数化（min_dmg=1 进 data），结构留引擎 |
| `int(dmg×(1+U(-var,var)))` 波动 | ⚠️ 半表达式化 | random 在表达式外；参数 variance（默认 0.15）进 data。**注意 battle.py 显式传 variance=0.15/0 覆盖默认**——参数化默认值不改变 21 处显式传参行为 |
| `int(dmg×1.5)` 暴击 | ⚠️ 参数化 | crit_mult=1.5 进 data（battle.py 对 crit 段另乘 crit_dmg/残忍/幸运——那是"外部乘区"不入 calc_damage；本处 1.5 是**唯一**基础暴击倍率，formula_expr.build_vars 已注入 crit_mult=1.5 但战斗路径从不消费该变量——可作为新参数默认值来源）。**风险**：crit 倍率若做成全局可配，峰值红线口径依赖（BURST_REDLINE_v133 文档 `×1.5` 多次出现）→ 参数化后需在表单注释 + 归口测试锁定 1.5 |
| int 截断次序（先 int(减伤) → 波动 int → 暴击 int → 二次 max） | ❌ 引擎 | 截断序是 ±1 门禁敏感点（test_v106_pene 全用 int(...) 期望表达式断言） |

### 3.3 保真验证方案（零变化证明）

1. **确定性探针**：现有 test_v106_pene.py（64 断言）已把 calc_damage 直测网格（穿透组合/cap/下限/pierce）锁死；test_v107_dmg_type.py（21）锁 true 分支 + 真伤暴击。任何重构后跑这两文件 = 第一道门。
2. **补等值回测测试**（实施批次加，只读侦察不动代码）：`random.seed(k)` 固定 → 遍历 atk∈{1,10,50,100,300,1000,5000} × def∈{0,1,10,50,100,300,1000} × {phys/magi/true × pierce × pene_pct∈{0,0.2,0.6} × pene_flat∈{0,30,100} × crit∈{T,F}}，断言重构后 == 重构前（先落 baseline 快照文件再改）。
3. **battle 级回测**：test_numeric_skill_vs_basic / test_numeric_basic_atk / test_v180c_pet_isolation 走真引擎普攻/技能路径 → 复算防御/波动口径。
4. **51 numeric 全量**（scripts/run_numeric_tests.py）= 终门（已在沙盒预跑：✅ 51/51，29s）。

### 3.4 calc_damage 专项结论

**不建议把 calc_damage 整体表达式化**（pierce/true/穿透/除零/截断序/random 是控制流与离散截断，不是可配置数值公式，硬表达式化会为 1% 收益引入 99% 回归面）。
**推荐"参数化 + 可选表达式段"**：
- 第一步（低风险，先做）：`variance 默认 0.15 / crit_mult 1.5 / min_dmg 1 / pene_cap 0.6 / 除零兜底 1` → `FORMULA_SKELETON.damage` 子表；函数壳不变（读表替换字面量）。行为零变化：默认值=现状，21 处显式传参不受影响。
- 第二步（可选，中风险，单独批次）：把"减伤公式体"做成可选字段 `FORMULA_SKELETON.damage.mitigation_expr`（默认 `None` = 走引擎 `atk²/(atk+def)`；配了字符串则走 formula_expr 求值，eff_def 预注入变量）。**默认 None 保证零变化**，表达式只在策划明确换公式时才启用——把"改公式"从改代码变成改数据，但风险完全隔离在 opt-in 路径。
- **formula_expr VARIABLE_WHITELIST 结论**：atk/def 现成；表达 eff_def 需加 `eff_def` 变量（或调用方预算好 def 注入）；**不建议**为骨架表达式扩展函数原语（min/max/分支）——那是引擎职责。

---

## 4. 数据表设计草案（默认值=现状 → 行为零变化）

> 落点：新建 `game/data/formula_skeleton.py`（纯 dict，零 import 零函数，参照 stat_templates.py 文档头）。
> 导出：`game/data/__init__.py` 聚合行（与 stat_templates 同款），`core/stats.py` / `engine.py` 顶部 from-import。
> 样式：key = 公式族；value = dict，每项默认值 = 现状字面量（注释标注现状出处与消费点）。

```python
# game/data/formula_skeleton.py（草案——纯数据零函数）
"""P2-F 底层公式骨架数值（2026-09-07 鱼鱼拍板公式化；默认值 = 重构前引擎字面量，行为零变化）。

消费端：core/stats.py（怪物曲线/装备/经验）与 engine.py（伤害/技能成长）函数体读本表。
改数值 = 改这里；公式结构（分支/截断/随机）仍由 core/engine 执行器承担（见 REFACTOR_P2F_formula_skeleton.md §3/§4）。
"""
FORMULA_SKELETON = {
    # ---- F1 calc_damage（engine.py:1009）----
    "damage": {
        "variance_default": 0.15,     # 默认波动 ±15%（engine 签名默认；battle.py 显式传 0.15/0 覆盖不受影响）
        "crit_mult": 1.5,             # 基础暴击倍率 ×1.5（calc_damage is_crit；v133 峰值红线口径，勿轻改）
        "min_dmg": 1,                 # 下限（两处 max(1,…)）
        "pene_cap": 0.6,              # v106 穿透百分比 cap（兜底 clamp；聚合层 PCT_CAPS.pene_* 同为 0.6）
        "zero_guard": 1,              # atk+eff_def≤0 除零兜底返回值
        "mitigation_expr": None,      # 减伤公式可选表达式（None=引擎 atk²/(atk+def)；配字符串走 formula_expr，eff_def 注入）
    },
    # ---- F2 exp_to_next 兜底（stats.py:253，超出 100 级）----
    "exp_fallback": {"base": 60, "power": 1.45, "add": 50},
    # ---- F3/F4 怪物经济（stats.py:255/264）----
    "monster_exp": {"linear_slope": 0.9, "combat_len_mult": 1.5, "hp_pow": 0.7},
    "monster_gold": {"linear_slope": 0.6, "combat_len_mult": 1.3, "hp_pow": 0.5},
    # ---- F5 equip_stats 修正系数（stats.py:202-205）----
    "equip_crit": {"base": 0.02, "per_lv_div": 10, "per_lv": 0.01},   # crit = (0.02 + 0.01×lv/10)×(mult-1)
    "necklace_mdef": {"flat": 3},                                      # 项链 mdef += int(3×mult)
    # ---- F6 player_base_stats 成长骨架（engine.py:135）----
    "base_growth": {"stats": ["hp", "mp", "atk", "def", "matk", "mdef", "spd"],
                    "branch_crit_add": True},   # crit 走加法 round(…,3)，其余乘 int —— 结构声明
    # ---- F7/F9 技能成长骨架（engine.py）----
    "skill_growth": {
        "power_per_lv_divisor": 100,   # skill_power_mult: 1+(p/100)(lv-1)
        "cond_default": 0.05,          # skill_cond_mult 未配 c 默认每级 +0.05
        "mech_default_div": 2,         # skill_mech_val 未配 m 默认每 2 级 +1 层
        "buff_turns_base": 3,          # skill_buff_turns 默认 base 3
        "buff_turns_per_lv": 1,        # 每级 +1 刻
        "lifesteal_default": 0.20,      # skill_lifesteal_pct 未配 lifesteal 默认 20%
        "lifesteal_per_lv_pct": 2,      # 配 l 每级 +2%
    },
    # ---- F15 技能点定价（engine.py:744）----
    "skill_learn_cost": {"divisor": 6, "base": 2},   # need_lv//6 + 2
    # ---- F16 副业经验曲线（core/constants.py:171）----
    "prof_exp_need": {"a": 5, "b": 15},              # a·lv² + b·lv
}
# ---- F10-F12 分段曲线（建议直接并入 stat_templates.py 同区，与 NORMAL_HP_STAGE_MULT 同构）----
HP_STAGE_MULT = ((15, 0.0), (30, 0.05), (60, 0.03), (999, 0.02))        # 现值=hp_stage_mult 逐 lv 精确
ATK_STAGE_MULT = ((30, 0.0), (999, 0.004))                              # 现值=atk_stage_mult（31+ 每级+0.4%）
BOSS_ATK_STAGE_MULT_LEGACY = {"seg": ((30, 0.0), (60, -0.005), (999, -0.004)), "floor": 0.2}
# ---- F14 monster_stats 角色修正（并入 stat_templates.py）----
MONSTER_ROLE_MODS = {
    "boss":   {"hp_linear": 0.06, "hp_cap": 3.0, "def_mult": 1.25, "mdef_mult": 1.25, "dot_res": 0.9},
    "elite":  {"hp_linear": 0.04, "hp_cap": 3.0, "def_mult": 1.15, "mdef_mult": 1.15, "dot_res": 0.8},
}
```

要点：
- **`default=None/默认=现状` 是零变化锚点**：任何可配项默认值必须等于重构前字面量；实施批次断言 `FORMULA_SKELETON == 现状提取值` 的对照测试先过再动函数。
- **两处 int 截断序**（F12 monster_curve ±1、F5 equip_stats int）在参数化后保持"先乘后 int"原序——表单注释写明，回测网格兜底。
- hp_stage_mult 表化（F10）必须**逐 lv 1..100 断言 == 现函数输出**再切（斜率语义差异：现函数首段返回 1.0、表驱动 _stage_mult 首段末值 1.0 + slope 语义一致，但 15/16 边界是"≤15 恒 1.0 vs 16 起 +"的 off-by-one 高发区）。

---

## 5. 分阶段建议

| 阶段 | 内容 | 风险 | 前置 | 验收 |
|---|---|---|---|---|
| **P2F-1（先做，1 批次）** | F2/F3/F4/F7/F9/F15/F16 全部**纯参数化**（新建 formula_skeleton.py + 替换字面量） | 低（默认=现状） | 无 | py_compile + test_core_engine/test_numeric_instance_reward/test_numeric_economy_toolkit/test_numeric_reward_unify/test_commands_skills/test_commands_economy + 51 numeric 全量 |
| **P2F-2（中风险）** | F10/F11/F12 分段曲线**表驱动化**（hp/atk/boss_atk_stage → _stage_mult 同构表）；F5 WEAPON_DIST/ARMOR_FAMILY 表下沉 data + equip_crit/necklace 参数化 | 中 | P2F-1（表文件已建） | 逐 lv 1..200 新旧等值断言（monster_curve 锁 6 role×5 lv + Lv60 boss atk 1217）→ 51 numeric |
| **P2F-3（高难度，最后）** | F6 player_base_stats 成长骨架声明化 + F14 monster_stats role_mods 参数化（F14 分支保留引擎） | 高 | P2F-1/2 | panel/actor 全族测试 + monster_curve 180 断言 + battle_matrix |
| **P2F-X（可选隔离批次）** | calc_damage：第一步参数化（variance/crit/min/pene_cap）并入 P2F-1；第二步 `mitigation_expr` opt-in 表达式段**独立批次**，默认 None | 见 §3.4 | P2F-1 | 等值回测网格（§3.3-2）+ test_v106/test_v107 + 51 numeric |

**排序逻辑**：纯搬参数（P2F-1）先行建立"骨架表"落点与对照测试惯例 → 曲线表化（P2F-2）动公式结构但全是**确定性纯函数**（逐 lv 网格可证等价）→ 结构性骨架（P2F-3）最后（波及面板全链路）。
calc_damage 的表达式化**永远放最后且 opt-in**（默认 None 零风险）；若鱼鱼只想要"系数可配"，P2F-1 已覆盖 9 成收益。

---

## 6. 风险与门禁策略

### 6.1 行为零变化的风险点
1. **int 截断序**：monster_curve Lv60 boss atk 1217↔1218 ±1 门禁 = 两级 int 顺序敏感（F12）；equip_stats 每属性 int（F5）。→ 参数化绝不重排运算序。
2. **随机依赖**：calc_damage 波动 random 使"重构前/后"无法逐次相等 → 用 `random.seed` 固定 + 分布区间断言（现有 test_v107 已用 seed(7)+范围），另加基线快照对拍。
3. **from-import 绑定**（numeric_lib/monster.py 注释 v131 教训）：stats.py 已 `from ..data import MONSTER_ROLE_*` **绑定名**——若把数值从 stats.py 本地表改从 data 读，必须保持 data 单源 + 覆盖测试同绑（curve_override 已双绑 data+stats）。
4. **显式传参覆盖**：calc_damage/resolve_formula 21 处 battle.py 显式传 variance → 只参数化"默认值"不碰显式传参点。
5. **hp_stage_mult 的曲线_override 测试**（test_numeric_toolkit）直接替换 `ST.hp_stage_mult` 函数 → 表驱动后函数仍须存在（读表实现），签名不变。
6. **表达式解释器边界**：formula_expr 无 min/max/分支；除零返回 0（eval_expr `/` 当 b==0 → 0）与 calc_damage 除零兜底语义不同 → mitigation_expr opt-in 必须在文档标注除零差异。

### 6.2 门禁清单
- **py_compile**（game/ 全量，w4 原地）——每批必跑。
- **单测族**（沙盒 df_wt_copy3 已预跑全绿，实施批每批复跑）：
  - calc_damage 直测：`test_v106_pene.py`（64）/ `test_v107_dmg_type.py`（21）
  - 怪物曲线/经济：`test_numeric_monster_curve.py`（180）/ `test_core_engine.py`（7）/ `test_numeric_instance_reward.py`（221）/ `test_numeric_economy_toolkit.py`（23）/ `test_numeric_reward_unify.py`（14）
  - 装备：`test_numeric_equip_split.py`（220）/ 装备族（actor_equip/gear_full/gem_drops…）
  - 技能成长：`test_numeric_skill_power.py`（22）/ `test_numeric_skill_vs_basic.py` / `test_commands_skills.py`
  - 面板/成长：`test_numeric_branch_bonus.py` / `test_numeric_panel_snapshot.py` / `test_numeric_stage_growth.py`（220）/ `test_core_world.py`
- **51 numeric 全量**（scripts/run_numeric_tests.py）= 终门（沙盒基线：✅ 51/51，29s）。
- 行为零变化专项（新增）：对照测试 `assert FORMULA_SKELETON 参数值 == 重构前从现状提取值`；P2F-2 曲线批加 `逐 lv 1..200 新旧函数等值`。

### 6.3 等值回测网格（calc_damage / 曲线批次专用）
```
atk × def × dmg_type × pierce × pene_pct × pene_flat × is_crit × variance 全叉积
random.seed(k) 固定 → 新旧实现输出全等（波动路径同 seed 同序）
```
实施批次落地为 tests/test_p2f_equivalence.py 先跑旧实现生成 baseline 快照，再改代码复跑对拍。

---

## 7. 附：侦察方法与验证记录

- worktree w4（wt_p2f）只读；沙盒 = df_wt_copy3（复制 w4 + data/plugins 父链）跑测试。
- 基线测试预跑（沙盒，全绿）：test_v106_pene 64/64、test_v107_dmg_type 21/21、test_numeric_basic_atk PASS 10、test_numeric_formula 18/18、test_v160_exprs 29/29、test_core_engine 7/7、test_numeric_skill_power 22/22、test_numeric_equip_split 220/220、test_numeric_stage_growth 220/220、test_numeric_instance_reward 221/221、test_numeric_reward_unify 14/14、test_numeric_economy_toolkit 23/23；**scripts/run_numeric_tests.py → 51 文件全 ✅（29s）**。
- 探针（沙盒）：calc_damage(100,100,variance=0)=50、true=100、crit true=139（seed 固定）、exp_to_next(101)=48402（兜底 60·101^1.45+50≈48401.6→48402 ✓）、monster_exp(60,dps)=1468、equip_stats 重甲/分系输出与公式一致、skill_power_mult(5,p=10)=1.4。
- 文档 commit：wt_p2f 分支（本文件 docs/archive/REFACTOR_P2F_formula_skeleton.md）。主仓与其它 worktree 未动。
