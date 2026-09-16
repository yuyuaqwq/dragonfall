# P2-D 被动 proc 反射化注册表 — 只读侦察 + 设计方案（wt_p2d）

> 任务：REFACTOR_PLAN_v181.md P2-D。本文档为**只读侦察 + 方案设计**（未改 game/ 代码），落地给后续改造批次用。
> 侦察基线：master `6cde807`（含 2026-09-07 鱼鱼拍板《ARCHITECTURE_TARGET_STATE_v181.md》三层目标态北极星），worktree w3（wt_p2d）。battle.py 11291 行 / skills.py 4152 行。
> 铁律：行为零变化；每步 py_compile + 单测绿；data 纯数据零函数；core 通用执行器+注册表；battle 纯编排零内容名。

---

## 0. TL;DR（给执行批次的一句话）

建 `game/core/passive_procs.py` 注册表（proc 名 → 机制族 handler，仿 MECH_EFFECTS / SET_PROC_TYPES），按**机制族**（不是 52 个 proc 名）收敛成 ~12 个通用执行器族；battle.py 现有 12 个挂点改为调注册表（查询 `_proc_pm(player)["proc"]` → `run_proc_family("家族", battle, ctx)`）。52 个 proc 中：**34 个有引擎消费点**（审计口径）、**12 个无消费点空转**（审计口径；现状复核：4 个真空转 + 8 个仅通道开关/占位读）；详见 §2/§3 全量映射表与现状差异说明。

---

## 1. 目标与范围

### 1.1 目标态（对齐 ARCHITECTURE_TARGET_STATE_v181.md）

```
data/skills.py  ← passive: {"proc": "zhan_yi_crit", "stacks": 8, "add": 0.15}   ← 纯数值声明（v181.C 已补齐第一批）
core/passive_procs.py  ← 注册表 + 按机制族参数化通用执行器（读 data passive dict 数值，无具体内容名）
battle.py  ← 12 个挂点改为：proc 族存在 → 查注册表执行；无注册 = 不触发（"配置缺字段=无此行为"）
```

**判定问题**（写 handler 前必问，抄目标态文档 §判定标准）：
1. 这个阈值/概率/倍率 → 已在 `skills.py` passive dict（`stacks/add/mult/layers/spd_add/crit_dmg/reduce/per_core/...`）。若 engine 侧仍有本地默认值 → 迁移时把本地默认值删掉、数值以数据声明为准（v181.C 铁律：缺字段=无此行为）。
2. 这个"行为类型"是否已有通用执行器？有 → 多 proc 同机制族共用；无 → 判断是否**新机制族**（注册 ~20 行参数化执行器），不是新族 = 已有族变体 → 加参数表达，不新写 handler。
3. battle.py 不得出现具体内容名（职业 id/装备/技能中文名）——proc 名是机制族键，可以出现在 core；被动 display 名只进日志。

### 1.2 收编范围（52 个 skills.py passive `{proc}` 全量）

- 收编：52 个中所有**有引擎消费点**的 proc（§3 表 A/B/C 类，约 34+ 个）→ handler 族。
- 保留原位（迁移批次不做）：4 个纯零读 + 8 个通道开关/占位读的 proc 保持原样（§3 表 D/E 类），在文档标注"已知缺口"；**本批次不改任何引擎行为**，只做"搬"。
- 明确**不在本任务范围**：battle.py 消费、但 skills.py **没有** passive `{proc}` 声明的老名字（`pierce/fire_bonus/execute/counter_attack/death_pact/mark_extra/turn_heal/team_regen/arcane_regen/heal_shield/combo_boost/speed_dmg/mark_dmg/poison_dmg/arcane_dmg/element_dmg/res_gain_bonus/attack_res/counter...`）——它们有的是 stat 型被动残留消费、有的是旧格式未数据化；属于 P1-C/P2 其它批次，不是 52 proc 注册表的键。**设计上禁止**把 52 之外的名字注册进新表（表键 = skills.py 的 52 个 proc 名，逐个核对）。
- `_passive_map` 的 `"stat"` 通道（`{stat: [...], cond: ...}` 数据被动）**不迁移**——它已有 PASSIVE_COND_CHECKS 条件注册表（battle_conds.py），保持现有通道。

### 1.3 非目标（红线）

- 不改 skills.py 数据（v181.C 已把数值补进 passive dict；后续行为修正另行派 data 批次）。
- 不新增引擎行为、不改任何数值/日志文本（现有日志含被动 display 名 → handler 内保留原日志串）。
- 不动 `_passive_map/_proc_pm` 结构（`{"proc": {proc名: [(被动名, passive dict), ...]}, "stat": [...]}` 是全引擎公共契约）。
- 不把 handler 搬进 data/ 目录（鱼鱼拍板：那是搬家不是解耦）。

---

## 2. 侦察发现：52 个 proc 全量清单与当前消费点

### 2.1 数据层现状（game/data/skills.py）

- 52 个 `passive: {"proc": ...}` 全部在 `BRANCH_SKILLS`（branch 职业树），每条对应一个分支被动技能（kind=被动、max=1 铁律）。
- 分布（8 职业 16 分支）：战士(狂战士 3 / 盾卫士 4)、法师(元素使 5 / 奥术学者 5)、游侠(森语者 5 / 风行者 3)、牧师(神谕者 3 / 死灵祭司 4)、刺客(影舞者 5 / 毒刃者 4)、武僧(格斗士 3 / 磐石行者 6)、诗人(咏叹者 4 / 挽歌者 2)、+淬血/狂热在狂战士。合计 52。
- 数据字段现状：仅 8 个 proc 带参数（`zhan_yi_crit{stacks,add}`、`arcane_wisdom{stacks,add}`、`focus_surplus_crit{surplus,add}`、`element_core{layers,add}`、`shadow_dance_bonus{spd_add,crit_dmg}`、`arcane_resonance{mult}`、`element_origin{layers,mult}`——共 7 个带参数），其余 45 个**零参数纯 proc 键** → 引擎当前对无参 proc 全靠 handler 内部默认值/本地写死数值（v169.7 接线时数值写死在 battle.py）。⚠️ **迁移顺序前置任务**：把 engine 侧默认数值回填进 skills.py passive dict（v181.C 只补了 7 个乘区 proc），否则"配置缺字段=无此行为"在无参 proc 上会把行为清零。
  - 例外核对：engine 消费时多数读取有 `_ps.get("x", default)` 兜底，且 v181.C 前兜底是"写死数值"（8/15/20%…），v181.C 后 7 个乘区 proc 的兜底改为 0（缺字段=无此行为）→ 若 data 没值，行为已变（这是 v181.C 已提交的有意改变，不是本批次引入）。

### 2.2 引擎消费点结构（_passive_map / _proc_pm）

`battle.py:4784` `_passive_map(player)` → `{"proc": {proc名: [(被动名, passive dict), ...]}, "stat": [(被动名, passive dict), ...]}`；`battle.py:4799` `_proc_pm` = 空 `_passive_map` 重建的轻封装（异常回落空）。**挂点消费模式高度一致**：

```python
for _pn, _ps in self._proc_pm(player)["proc"].get("PROC", []):   # 或 _passive_map / pm
    ...读 _ps 数值 / self 战斗状态 → 返回增量或副作用...
    break   # max=1，多数只 break 第一个
```

所有挂点都**以 battle 实例为上下文**（读 `_player_stats/_enemy_stats/_zhan_yi_n/_guard_core_n/_elem_marks/_melody_state/_p_buffs_bag/_p_stacks/_p_res/_p_cooldown...`），消费函数签名各不相同（有返回 float/int、有改 logs/actor/buffs）。→ 注册表 handler 统一签名必须携带 battle + ctx 字典（见 §4）。

### 2.3 消费点分布（battle.py 现有 12 个挂点区，行号以 6cde807 为准）

| 挂点方法 | 行区 | 消费的 proc（本 52 内） | 挂点语义 |
|---|---|---|---|
| `_passive_crit_bonus` | 4865-4924 | zhan_yi_crit / arcane_wisdom / focus_surplus_crit / element_core | 条件暴击率增量（加法并入 crit，PCT_CAPS.crit 截断） |
| `_passive_crit_dmg_mult` | 4926-4939 | shadow_dance_bonus（crit_dmg 部分） | 暴伤加法增量 |
| `_player_stats` | 4608+（4631-4636 影舞速度 / 4705-4725 诗人旋律 3 光环 / 4699 stat cond 通道） | shadow_dance_bonus（spd 部分）/ melody_resonance / melody_full / melody_master | 面板属性乘法增幅（st 内改） |
| `_player_dmg_mult` | 5678-5690 | speed_ratio_dmg | 通用伤害乘区（速度比 ≥2 → ×1.2） |
| `_settle_lifesteal` | 5013-5026 | zhan_yi_lifesteal | 吸血率加算（cap 30%） |
| `_skill_passive_dmg_bonus` | 6891-6997 | arcane_resonance / element_origin / element_sync（+元素同调置 `_elem_sync_bonus`） | 技能被动伤害乘区（连乘 passive_bonus） |
| `_do_player_skill`（奥术恒常） | 4388-4399 | arcane_constant | MP 耗减乘算 |
| `_set_skill_cd` | 2518-2533 | shadow_dance_cd | CD 乘算（影舞态 −20%） |
| `_combo_break` | 2602-2622 | lian_duan_soft | 断连只损 1 段 |
| `player_turn` | 3275-3300 | tenacity（_tenacity_try_break）/ zhan_yi_full_reduce（免眩晕）/ core_full（免控免疫窗口） | 被控/免控兜底 |
| `_mitigate_chain`（受击减伤族） | 10513-10590 | zhan_yi_full_reduce / core_full / core_reduce / core_last_stand / core_overflow | 条件减伤 + 磐核溢出转盾 |
| `_post_hp_lethal`（致死复活族） | 10858-10922 | death_contract / berserk_revive / stance_immortal | 致死复活链 |
| `_retaliations_and_buffs`（受击反击族） | 10706-10734 | counter_chance / counter_up（+counter_attack 非 52 内） | 以守为攻/反击之王 反击 |
| `_deal_damage`（对敌伤害乘区） | 9635-9676 | hunt_mark_up / soul_mark_cap / shaken_awareness / broken_extend / dirge_debuff_dmg | 对敌标记/破绽/挽歌乘区（读 attacker 被动） |
| `_tick_actor_dots`（毒 tick） | 8772-8796 | poison_all_up / poison_weaken | 毒 DOT 乘区 + 减速降防 |
| `_apply_mech_effect`（叠层上限放宽） | 7382-7411 | hunt_mark_cap / soul_mark_cap / poison_cap（+poison_cap_up 经 _poison_cap） | 术后补层（cap 放宽） |
| `_poison_cap` | 4814-4823 | poison_cap_up / poison_cap | 毒层上限 |
| `_skill_hit_settle`（命中后置） | 6330-6400 | element_affinity（引爆置位）/ broken_extend（破防延长）/ dirge_ctrl_up（挽歌控制延长） | 命中结算后置位/延长 |
| `_skill_heal`（治疗溢出转盾） | 6150-6180 | heal_overflow_shield（+heal_shield 非 52） | 治疗溢出转盾族 |
| `_skill_buff`（诗人吟唱） | 6217-6231 | melody_duet（吟唱强度 +1） | 增益技后置 |
| `_summon_entity`（召唤） | 9903-9912 | skeleton_cap | 召唤上限 |
| `_remove_unit`（击杀） | 10134-10145 | focus_full_on_kill | 击杀回满精力 |
| `_turn_start`（破绽条） | 9278-9289 | shaken_decay_half | 破绽衰减减半（回补） |
| 模块级 tick handler（battle.py 顶部注册到 TICK_HANDLERS） | 298-462 | focus_regen_summon（_th_passive_heal）/ arcane_intuition（_th_mech_charge）/ undead_faith（_th_faith_decay）/ faith_overload_heal（_th_faith_decay） | 每刻 regen 族（_ensure_regen_effects 9044-9055 / 9146-9157 做通道开关） |
| `_tenacity_try_break` | 4948-4970 | tenacity | 战意挡控（3 次/场） |

> 注：`tenacity` 一词在 battle.py 还有 5 处是**属性韧性 stat**（8218/8240/9502 等，affix `precise/tenacity`），不是本 52 proc 的消费点；迁移时别误搬。

### 2.4 挂点消费形态三类（决定 handler 归属族）

1. **返回标量型**（读状态算增量返回）：crit_bonus/crit_dmg_mult/player_dmg_mult/skill_passive_dmg_bonus/poison_cap/settle_lifesteal → 挂点方法本身就是"多 proc 聚合器"。
2. **状态副作用型**（改 actor/buffs/logs/置位标记）：_skill_hit_settle 后置 / _mitigate_chain 减伤 / _post_hp_lethal 复活 / _retaliations 反击 / dot tick / cd / combo / summon / kill / melody。
3. **通道开关型**（proc 只参与 _regen_needed/_ensure_regen_effects 名单，不产生独立行为）：见 §3 E 类。

---

## 3. 52 proc 全量映射表（34 消费分类 + 12 空转复核）

### 3.0 表说明与口径

- **审计口径**（REFACTOR_PLAN_v181.md L106，报告 6 §七）：52 中 34 个有引擎消费点、12 个无消费点空转。该口径基于 v181.C 之前的树。
- **现状复核（6cde807，逐行代码扫描）**：52 中 **48 个**在 battle.py/core 有 ≥1 处代码读取（含通道开关读），**4 个零读取**（faith_share / finisher_up / poison_burst_up / poison_spread，后 3 者仅 battle.py 6342/6348 注释提及 TODO）。
- 差异原因：v169.7（接线 40 个消费点）+ v181.C（8 个乘区 proc 数值读入数据）。**设计分类以现状代码为准**，审计 12 空转清单逐条复核如下。

### 3.1 A 类 — 纯计算、可直接搬 handler（读 passive dict + actor/battle 状态 → 返回值/副作用，无隐藏依赖）

这些 proc 的消费逻辑只依赖：`_ps`（passive dict 数值）+ 少量 battle 只读状态（战意/磐核/印记/精力/速度/破绽/毒层…），且这些状态已有 battle 只读 helper（`_zhan_yi_n/_guard_core_n/_elem_marks/_elem_charge/_res_max/_shadow_dance/_melody_state/_p_buffs_bag...`）。**handler 可直接等价搬移**，ctx 传 `player/info/logs/返回值槽` 即可。

| proc | 技能/分支 | 消费挂点 | 数值来源(passive dict 现状) | 迁移族 |
|---|---|---|---|---|
| zhan_yi_crit | 狂热(狂战士) | _passive_crit_bonus:4877 | stacks/add **已配** | proc_crit_cond(资源≥阈值→add) |
| arcane_wisdom | 真知(奥术学者) | _passive_crit_bonus:4883 | stacks/add **已配** | 同上（读 element_charge 或 arcane 叠层） |
| focus_surplus_crit | 疾风之心(风行者) | _passive_crit_bonus:4901 | surplus/add **已配** | 同上（读 _pre_cost_res 快照 + 置 p_eff flag） |
| element_core | 元素之核(元素使) | _passive_crit_bonus:4912 | layers/add **已配** | 同上（读 info.element + 元素印记层） |
| shadow_dance_bonus | 暗影步·极(影舞者) | _passive_crit_dmg_mult:4933 + _player_stats:4634 | spd_add/crit_dmg **已配** | proc_stat_mult（影舞态：spd 乘法 + crit_dmg 加法两消费点） |
| arcane_resonance | 奥术共鸣(奥术学者) | _skill_passive_dmg_bonus:6938 | mult **已配** | proc_dmg_mult_mech（mech∈MECH_PROC_GROUPS.arcane_dmg → ×(1+mult)） |
| element_origin | 元素起源(元素使) | _skill_passive_dmg_bonus:6943 | layers/mult **已配** | proc_dmg_mult_cond（三系印记≥layers） |
| speed_ratio_dmg | 疾风·极(风行者) | _player_dmg_mult:5683 | 无参（本地 2.0/0.20） | proc_dmg_mult_cond（速度比≥ratio → dmg_add）**需补数据** |
| zhan_yi_lifesteal | 淬血(狂战士) | _settle_lifesteal:5017 | 无参（本地 per_layer 0.015） | proc_lifesteal_per_stack **需补数据** |
| poison_cap_up / poison_cap | 剧毒之心(森语者)/淬毒之心(毒刃者) | _poison_cap:4819/4821 | 无参（本地 add 3 cap 8） | proc_stack_cap（cap = 基础 + Σadd，max 8） |
| shaken_awareness | 气力之心(格斗士) | _deal_damage:9656 | 无参（bar_at 15 / mult 0.20） | proc_dmg_mult_tgt_cond **需补数据** |
| dirge_debuff_dmg | 挽歌·极(挽歌者) | _deal_damage:9669 | 无参（per_debuff 0.04 cap 0.40） | proc_dmg_mult_by_debuff_kind **需补数据** |
| hunt_mark_up | 自然之眼(森语者) | _deal_damage:9639 | 无参（per_layer 0.06） | proc_mark_dmg_up（按猎印层） |
| soul_mark_cap | 灵魂锁链(死灵祭司) | _deal_damage:9648 + _apply_mech_effect:7397 | 无参（per_layer 0.08） | proc_mark_dmg_up + proc_stack_cap（双消费点，一 handler 一参数族） |
| hunt_mark_cap | 追猎者(森语者) | _apply_mech_effect:7388 | 无参（add 2） | proc_stack_cap（cap 放宽） |
| lian_duan_soft | 暗影之心(影舞者) | _combo_break:2613 | 无参（损失 1 段固定） | proc_combo_softbreak |
| shadow_dance_cd | 影舞·无间(影舞者) | _set_skill_cd:2522 | 无参（cdr 0.20） | proc_cdr_cond（影舞态 CD×（1-cdr）） |
| arcane_constant | 奥术恒常(奥术学者) | _do_player_skill:4395 | 无参（mp_mult 0.50） | proc_mp_cost_mult（奥术技 MP 乘算） |
| focus_full_on_kill | 追风(风行者) | _remove_unit:10134 | 无参 | proc_on_kill_refill（击杀回满 energy） |
| skeleton_cap | 骷髅海(死灵祭司) | _summon_entity:9907 | 无参（cap 5 add 2） | proc_summon_cap（skeleton 上限） |
| broken_extend | 破绽·极(格斗士) | _skill_hit_settle:6395 + _deal_damage:9664 | 无参（extend 1 / broken_mult 0.50） | proc_broken_extend（双消费点两参数） |
| poison_all_up | 万毒归宗(毒刃者) | _tick_actor_dots:8776 | 无参（mult 0.35） | proc_dot_mult（毒 DOT ×（1+mult）） |
| poison_weaken | 剧毒之触(毒刃者) | _tick_actor_dots:8786 | 无参（layers 5 / spd_down 2 / def_down 2） | proc_dot_weaken（毒层≥N → 目标减速降防） |

> A 类计数：23 个（含同 proc 双消费点）。

### 3.2 B 类 — 状态副作用型，可搬但 handler 需 battle 传入更多上下文（读/改 actor.buffs / self.summons / 一次性 flag / logs）

这类能搬成 handler，但 ctx 必须携带：`actor`（受击/致死方）、`dmg`、`target`、`logs`，handler 内要访问 battle 的实例级一次性标记（`_death_pact_used/_berserk_revive_used/_stance_immortal_used/_core_last_stand_used`）与 `self.summons/companions`（骷髅代受、移除）。**挂点方法本身保持"顺序链"**（多条复活/减伤 if 按原顺序逐个跑），每个 if 体换成查注册表。

| proc | 技能/分支 | 消费挂点 | 迁移族 | battle 需传入 |
|---|---|---|---|---|
| tenacity | 坚韧(盾卫士) | player_turn 3277 + _tenacity_try_break:4948 | proc_cc_break_cost（战意≥cost→扣层+次数-1，3 次/场） | player, logs, 序列化字段 `_tenacity_left_n`（已随战斗序列化） |
| zhan_yi_full_reduce | 坚城之姿(盾卫士) | player_turn:3284 + _mitigate_chain:10544 | proc_dr_cond + proc_cc_immune（战意满 stacks → 减伤/免眩晕）双挂点双参数 | player, logs |
| core_full | 磐石之躯(磐石行者) | player_turn:3294 + _mitigate_chain:10549 | proc_dr_cond + proc_cc_immune（磐核满 → 减伤/免控） | player, logs |
| core_reduce | 大地之肤(磐石行者) | _mitigate_chain:10553 | proc_dr_per_core（每磐核 ×per_core） | player, logs |
| core_last_stand | 不动如山(磐石行者) | player_turn:3241 + _mitigate_chain:10519/10560 | proc_last_stand（hp<ratio 触发 1 次：给磐核+置位；已触发后常驻减伤 reduce） | actor, logs, `_core_last_stand_used` |
| core_overflow | 磐石之心(磐石行者) | _mitigate_chain:10564 | proc_overflow_shield（磐核≥stacks → 溢出承伤转盾 _add_shield） | actor, dmg, logs |
| death_contract | 死亡契约(死灵祭司) | _post_hp_lethal:10879 | proc_death_pact_cond（信念≥faith_req 且骷髅在场 → 牺牲骷髅复活 hp_pct） | actor, logs, `_death_pact_used`, self.summons/companions |
| berserk_revive | 血怒·不灭(狂战士) | _post_hp_lethal:10899 | proc_revive_cond（狂暴态首次致死 → 清战意回 hp_pct） | actor, logs, `_berserk_revive_used`, 形态判定 |
| stance_immortal | 铁誓·不动(盾卫士) | _post_hp_lethal:10913 | proc_revive_cond（守护姿态 → 免疫致命 1 次清战意） | actor, logs, `_stance_immortal_used` |
| counter_chance / counter_up | 以守为攻/反击之王(磐石行者) | _retaliations_and_buffs:10711/10712 | proc_counter_cond（聚合 chance/mult：chance max、mult min、counter_up 加 chance_add×dmg_add；cap 0.9） | actor, dmg, logs, _rtgt(攻击者), 反击回气 |
| element_affinity | 元素亲和(元素使) | _skill_hit_settle:6333 | proc_flag_set（element_burst 结算后置 `_elem_affinity_next`） | player, mech, logs |
| element_sync | 元素同调(元素使) | _skill_passive_dmg_bonus:6955 | proc_flag_set（连续同系 → `_elem_sync_bonus`） | player, element, logs |
| melody_duet | 二重唱(咏叹者) | _skill_buff:6220 | proc_melody_stack（吟唱 → _melody.stack +1 cap MELODY_CFG） | player, _melody_state, logs |
| dirge_ctrl_up | 镇魂安魂(挽歌者) | _skill_hit_settle:6368 | proc_ctrl_extend（挽歌技施控 → e_buffs 控制 +add 刻） | player, target_buffs, mech/cc, logs |
| heal_overflow_shield | 圣光回响(神谕者) | _skill_heal:6155 | proc_heal_overflow_shield（溢出 ×pct → 盾；与 heal_shield 同族） | player, target_unit, hp_before/heal, target_ally |
| shaken_decay_half | 破绽感知(格斗士) | _turn_start:9281 | proc_bar_decay_half（破绽条衰减回补一半） | player, e_buffs.shaken, logs |

> B 类计数：16 个（tenacity 单列 1 + 双挂点 5 + 多挂点 2 + 单挂点 8…实际 16 个唯一 proc；含同族 counter 2）。

### 3.3 C 类 — 通道开关型（regen tick 族，消费在模块级 _th_* handler + 挂卡名单）

| proc | 技能/分支 | 消费挂点 | 说明 |
|---|---|---|---|
| focus_regen_summon | 森之共鸣(森语者) | _th_passive_heal:320/331 + _regen_needed:9049 + _ensure_regen_effects:9148 | 召唤物在场每刻回 energy（gain）——行为在 tick handler 内，属"每刻被动回复族"（与 turn_heal/team_regen 同族，但后两者非 52 proc） |
| arcane_intuition | 奥术直觉(奥术学者) | _th_mech_charge:350 + _regen_needed:9048 + _ensure_regen_effects:9150 | 每刻奥术充能+1（focus 时 +gain）——"充能族"（与 arcane_regen/spellblade_regen 同族） |
| undead_faith | 亡灵祭仪(死灵祭司) | _th_faith_decay:418 + _regen_needed:9049 | 亡灵在场每刻回 faith（per_undead）——"信念 tick 族" |
| faith_overload_heal | 信念·圣化(神谕者) | _th_faith_decay:437 + _regen_needed:9049 | 信念过载回血增强（heal_up）——"信念 tick 族" |

> C 类计数：4 个。这些 proc 是**每刻 tick 族**的成员，读点在模块级 handler（`_TICK_HANDLERS` 注册表，battle.py 顶部 247-296 注册到 core/tick_effects.py 同表）——**已经是一条注册表链**，迁移优先级最低（已属"通用 tick 框架"样板），只把 handler 内的 proc 分支抽到 passive_procs 族即可。

### 3.4 D 类 — 真空转（0 处代码读取，skills.py 声明 + battle.py 注释 TODO）→ 12 空转清单之一

| proc | 技能/分支 | 现状证据 | 建议 |
|---|---|---|---|
| faith_share | 信念·流转(神谕者) | skills.py:2502 声明；battle.py:6174 仅注释"单人战斗无分担目标…记录占位"，无代码读 | 补 handler（实例/组队分担伤害，依赖未来 allies 广播）或标记已知缺口（设计文档登记：单人无意义，副本多目标场景由 instance 层广播，引擎当前无此通道）。**建议：本批登记缺口不补**，避免为不存在的组队承伤通道发明行为 |
| finisher_up | 链舞(影舞者) | skills.py:2767；battle.py:6343-6348 注释：proc 挂在**主动技**「链舞」上（kind=物理非被动）→ `E.passive_skills_learned` 按 kind=被动 过滤，聚合不到 → 引擎无法接 | **数据缺陷**（不在本批修）：待 skills 批次把链舞改 kind=被动/或移除 passive 另立被动条目；引擎侧预案：mech=finisher 分支读 `_proc_pm(...)["proc"]["finisher_up"]` 提 per_stack——设计好 handler 占位，数据修好后零引擎改动生效 |
| poison_burst_up | 蚀骨(毒刃者) | skills.py:2846；battle.py:6339-6342 注释：依赖 battle_mech agent 在 `_m_poison_burst` handler 内补读（毒爆结算在 battle_mech.py 内部，battle.py 插不进） | **依赖方在 battle_mech.py**：设计为 proc_dot_burst_mult 族（毒爆伤害乘区 / 爆后层数），battle_mech `_m_poison_burst` 内查注册表——与 P2-D 分开派（battle_mech 文件所有权），登记跨文件缺口 |
| poison_spread | 毒刃·共鸣(毒刃者) | skills.py:3161；同上注释 | 同上（毒爆击杀扩散），跨文件缺口 |

> D 类 = 审计"12 空转"里的 4 个真空转。

### 3.5 E 类 — 审计口径"12 空转"复核差异（8 个：读得到但无独立行为/仅占位/读在别的通道）

现状复核：以下 proc 在 battle.py 有代码读，但**读点是通道开关/名单成员/占位注释/属性同名干扰**，不构成"独立行为消费点"；审计把它们列进 12 空转（v181.C 前更接近真空）。

| proc | 读点真相（6cde807） | 复核结论 |
|---|---|---|
| faith_overload_heal | 只有 `_th_faith_decay:437` + `_regen_needed:9049` 名单 | 行为挂在**信念过载路径**（`if _f_before >= max` 内），非独立挂点；行为存在但属于"过载增强"变体 → 归 C 类 tick 族 |
| focus_regen_summon | 只有 `_th_passive_heal` + 名单 | 同上，归 C 类 |
| undead_faith | 只有 `_th_faith_decay:418` + 名单 | 同上 |
| arcane_intuition | 只有 `_th_mech_charge:350` + 名单 | 同上 |
| zhan_yi_full_reduce / core_full | player_turn 免控分支 + _mitigate_chain 减伤分支——v169.7 接线后行为完整 | **已有完整消费**（审计口径滞后）；本表不列为空转 |
| heal_overflow_shield | 6155 同族循环（heal_shield/heal_overflow_shield 两 proc 一循环）+ 6173 占位注释 | 行为存在（溢出转盾 0.5），但**无独立挂点**（与 heal_shield 共用循环）→ 归 B 类 |
| tenacity | proc tenacity 消费在 _tenacity_try_break；另 5 处"tenacity"是属性 stat | 行为存在；注意名干扰 |

> 结论：审计 12 空转 = D(4) + E(8 中的 4 个 tick 族 + 4 个已接线但当时未接线)。**给后续批次的可执行口径**：真空转 4（D 类）+ 读点仅名单/占位、无独立行为的 4 个 tick 族成员（它们行为在 tick 框架内，迁移优先级最低）。**合计"无独立挂点/空转语义" 8 个**；其余 4 个（zy_full_reduce/core_full/heal_overflow_shield/tenacity）审计时未接线、现已完整接线 → 从空转清单划出。

---

## 4. 注册表 API 设计（新文件 game/core/passive_procs.py）

### 4.1 设计原则（对齐目标态三层）

- **键**：机制族名（不是 proc 名直接当键也行，见 4.3 两表设计）。
- 分两张表：
  - `PROC_FAMILIES = {proc名: 族名}` —— 数据语义映射（哪个 proc 属于哪个族；族名 = core 执行器键）。这层让"新 proc 只要声明族即可复用执行器"，skills.py 未来只加 `{"proc": X}` + 本文件一行映射（或直接在 passive dict 加 `"family"` 字段——见 4.3 取舍）。
  - `FAMILY_HANDLERS = {族名: handler}` —— 机制族通用执行器（参数化，读 `_ps` 数值 + ctx）。
- handler 统一签名（仿 MECH_EFFECTS / SET_PROC_TYPES，battle 实例作第一参）：
  ```python
  # 返回值型族：handler 返回增量并写入 ctx["out"] 槽；副作用型族：直接改 battle/actor/logs
  def handler(battle, ctx: dict, ps: dict, ps_name: str) -> Any:
      # ctx 至少含: player(actor), info, logs, kind/mech, target, dmg, st/est(惰性自取), plus 挂点私有字段(见 §3 B类"battle 需传入")
      # ps = passive dict（skills.py 数据，数值唯一权威；代码零默认值：缺字段=无此行为）
  ```
- 分发函数（battle.py 挂点调用，消灭散点 if）：
  ```python
  # game/core/passive_procs.py
  def run_proc_family(battle, proc_names: list[str], ctx: dict) -> Any
  #   → 对每个 proc 名：族 = PROC_FAMILIES[proc]；handler = FAMILY_HANDLERS[族]；handler(battle, ctx, ps, name)
  #   返回聚合结果（挂点按需取 ctx["out"] 或 handler 返回值列表）
  def register_family(family: str)            # 装饰器：FAMILY_HANDLERS[family] = fn（仿 battle_mech.register）
  def declare_proc(proc: str, family: str)    # 数据映射：PROC_FAMILIES[proc] = family（重复声明 = 报错，防覆盖）
  ```
- **无注册 = 不触发**：`PROC_FAMILIES.get(proc)` 取不到族 → run 直接跳过（等价"配置缺字段=无此行为"）。**绝不允许** handler 内部再 fallback 到旧默认数值。
- 表外名字防御：`run_proc_family` 只接受 52 白名单内 proc（`PROC_FAMILIES` 已声明）；battle.py 旧消费点迁移时逐个删，若 grep 发现还有 52 外名字（pierce 等）在旧点 → 那是 P1-C 遗留，不注册。

### 4.2 族划分（52 proc → ~16 族；先期收敛 12 族，B/D/E 族后续开）

| 族（FAMILY_HANDLERS 键） | 机制 | 收编 proc（A/B/C 类） | 参数（读 _ps） |
|---|---|---|---|
| `crit_cond_add` | 资源/印记满层 → 暴击率加 add | zhan_yi_crit, arcane_wisdom, focus_surplus_crit, element_core | stacks/layers/surplus/add；ctx: res_kind(战意/奥术充能/精力快照/元素印记), info.element |
| `stat_mult_cond` | 条件 → 面板属性乘法（spd/全属性） | shadow_dance_bonus(spd 段), melody_resonance, melody_full, melody_master, speed_ratio_dmg | spd_add/mult/per_stack/ratio/dmg_add；ctx: 属性键列表 |
| `dmg_mult_cond` | 条件 → 伤害乘区（连乘 1+mult） | arcane_resonance, element_origin, shaken_awareness, dirge_debuff_dmg, hunt_mark_up, soul_mark_cap(乘区段), broken_extend(乘区段) | mult/per_layer/per_debuff/cap/cond 键；ctx: mech/element/target 状态 |
| `lifesteal_add` | 每层战意 → 吸血率加算 | zhan_yi_lifesteal | per_layer |
| `stack_cap_add` | 叠层上限放宽 | poison_cap_up, poison_cap, hunt_mark_cap, soul_mark_cap(cap 段) | add/cap；ctx: mech/层键 |
| `mp_cost_mult` | 特定系技能 MP 乘算 | arcane_constant | mp_mult；ctx: mech/res_gain |
| `cdr_mult_cond` | 条件 → CD 乘算 | shadow_dance_cd | cdr；ctx: buff 态 |
| `combo_soft_break` | 断连只损 1 段 | lian_duan_soft | —（固定语义） |
| `dot_mult_cond` | 毒 DOT 乘区 | poison_all_up | mult |
| `dot_weaken` | 毒层 → 目标减速降防 | poison_weaken | layers/spd_down/def_down |
| `dr_cond` | 条件减伤（_mitigate_chain 段） | zhan_yi_full_reduce, core_full, core_reduce, core_last_stand(常驻段) | stacks/reduce/per_core；ctx: 资源量/hp_ratio |
| `cc_immune_cond` | 条件免控/免眩晕 | zhan_yi_full_reduce, core_full | stacks |
| `cc_break_cost` | 战意挡控（3 次/场） | tenacity | cost；ctx: 次数字段 |
| `revive_cond` | 致死复活（一次性 flag） | berserk_revive, stance_immortal, death_contract | hp_pct/faith_req/姿态条件 |
| `counter_cond` | 受击反击族（聚合） | counter_chance, counter_up | chance/mult/chance_add/dmg_add |
| `on_kill_refill` | 击杀回资源 | focus_full_on_kill | — |
| `summon_cap_add` | 召唤上限 | skeleton_cap | add/cap |
| `flag_set_cond` | 命中后置位标记 | element_affinity, element_sync, broken_extend(延长段), dirge_ctrl_up, melody_duet | add/extend |
| `heal_overflow_shield` | 治疗溢出转盾 | heal_overflow_shield | pct |
| `tick_regen` / `tick_mech_charge` / `tick_faith` | 每刻 tick 族 | focus_regen_summon, arcane_intuition, undead_faith, faith_overload_heal | gain/mech/per_undead/heal_up |

> 说明：上表族粒度较细（20 族），但**很多族是同构的**（`crit_cond_add`/`dmg_mult_cond`/`stat_mult_cond`/`dr_cond` 都是"条件成立 → 数值乘/加"，差异只在 ctx 里取哪个状态函数）。执行批次可进一步收敛成 3-4 个"谓词+数值"通用执行器（读 ctx["cond_fn"]/ctx["stat_key"]），**目标态样板里 SET_PROC_TYPES 就是这套**。粒度取舍见 §7.3。

### 4.3 取舍：proc→族映射放哪

- 方案 A（推荐）：`game/core/passive_procs.py` 内 `declare_proc("zhan_yi_crit", "crit_cond_add")` 显式声明表（白名单 + 启动校验：skills.py 52 个 proc 必须全覆盖或登记为已知缺口，防新增被动静默空转——仿 battle_mech `_REG_ORDER` 启动校验）。
- 方案 B：skills.py passive dict 加 `"family": "crit_cond_add"` 字段。优点：换配置连 core 都不改；缺点：data 出现机制族名（仍属"机制"非内容名，可接受），且引擎对未知族会静默（缺字段=无此行为，符合铁律）。
- **推荐 A + B 混合**：core 表权威（校验用），data 不加字段（data 改动最小；新 proc 只要 core 一行映射）。未来若"配置换新游戏"要支持纯数据加被动 → 再开 B（`family` 字段 + core 兜底表），本批不做。

---

## 5. battle.py 改动点清单（哪个方法哪个挂点改成调注册表）

> 全部改动 = 把 §3 表中"消费挂点"列出的 for 循环体换成 `run_proc_family(...)`；挂点顺序/日志串/副作用顺序逐字保留。按方法列：

| # | 方法 | 行区（6cde807） | 现状散点 | 改为 |
|---|---|---|---|---|
| 1 | `_passive_crit_bonus` | 4865-4924 | 4 个独立 for（zy_crit/arcane_wisdom/focus_surplus/element_core）+ 状态取数内联 | 查族 `crit_cond_add`；ctx 带 info；逐 proc run，返回值累加 |
| 2 | `_passive_crit_dmg_mult` | 4926-4939 | shadow_dance_bonus for | 族 `stat_mult_cond`（crit_dmg 段） |
| 3 | `_player_stats` | 4631-4636 / 4705-4725 | 影舞 spd for + 旋律 3 for（同段聚合 _mel_pct） | 族 `stat_mult_cond` 两处（spd / 全属性）；旋律段保持"先聚 _mel_pct 再统一乘"顺序 |
| 4 | `_player_dmg_mult` | 5678-5690 | speed_ratio_dmg for | 族 `dmg_mult_cond` |
| 5 | `_settle_lifesteal` | 5013-5026 | zhan_yi_lifesteal for | 族 `lifesteal_add` |
| 6 | `_skill_passive_dmg_bonus` | 6936-6963 | arcane_resonance/element_origin/element_sync 3 for（+pierce 等非 52 不动） | 族 `dmg_mult_cond` + `flag_set_cond`（element_sync） |
| 7 | `_do_player_skill` MP 段 | 4388-4399 | arcane_constant for | 族 `mp_cost_mult` |
| 8 | `_set_skill_cd` | 2518-2533 | shadow_dance_cd for | 族 `cdr_mult_cond` |
| 9 | `_combo_break` | 2602-2622 | lian_duan_soft for | 族 `combo_soft_break` |
| 10 | `player_turn` 免控段 | 3275-3300 | tenacity 前置 + zy_full_reduce for + core_full for | 族 `cc_break_cost`（调 _tenacity_try_break，内部改查表）+ `cc_immune_cond`×2 |
| 11 | `_mitigate_chain` | 10513-10590 | 5 个 for + 内联磐核补 | 族 `dr_cond`×4 + `overflow_shield`（core_overflow）+ last_stand 首触发保持顺序 |
| 12 | `_post_hp_lethal` | 10858-10922 | death_contract/berserk_revive/stance_immortal 3 for（+death_pact 非 52 不动） | 族 `revive_cond`×3（各带一次性 flag 参数） |
| 13 | `_retaliations_and_buffs` | 10706-10734 | counter_chance/counter_up 双 for 聚合 | 族 `counter_cond`（聚合逻辑进 handler：chance/mult/chance_add/dmg_add + cap 0.9 + 反击回气） |
| 14 | `_deal_damage` | 9635-9676 | hunt_mark_up/soul_mark_cap/shaken_awareness/broken_extend/dirge_debuff_dmg 5 段 | 族 `dmg_mult_cond`×5（ctx: target debuffs/attacker） |
| 15 | `_tick_actor_dots` | 8772-8796 | poison_all_up/poison_weaken 2 段 | 族 `dot_mult_cond` + `dot_weaken` |
| 16 | `_apply_mech_effect` | 7382-7411 | hunt_mark_cap/soul_mark_cap for + _poison_cap 调 | 族 `stack_cap_add`×2（post-cap 补层段保持）；`_poison_cap` 本体族化 |
| 17 | `_poison_cap` | 4814-4823 | poison_cap_up/poison_cap 2 for | 族 `stack_cap_add` |
| 18 | `_skill_hit_settle` | 6330-6400 | element_affinity/broken_extend/dirge_ctrl_up 3 段 | 族 `flag_set_cond`×3 |
| 19 | `_skill_heal` | 6150-6180 | heal_overflow_shield 同族循环（+heal_shield） | 族 `heal_overflow_shield`；**heal_shield 非 52 保留旧循环**（两 proc 拆开各自跑 = 行为等价：现状同一循环两次迭代，拆成 旧proc 循环 + 新族调用，顺序/日志保持） |
| 20 | `_skill_buff` | 6217-6231 | melody_duet for | 族 `flag_set_cond`（melody_duet 段） |
| 21 | `_summon_entity` | 9903-9912 | skeleton_cap for | 族 `summon_cap_add` |
| 22 | `_remove_unit` | 10134-10145 | focus_full_on_kill for | 族 `on_kill_refill` |
| 23 | `_turn_start` | 9278-9289 | shaken_decay_half for | 族 `flag_set_cond`/独立族 `bar_decay_half` |
| 24 | tick handler `_th_*` | 298-462 | 4 proc 分支（focus_regen_summon/arcane_intuition/undead_faith/faith_overload_heal） | 抽族 `tick_regen`/`tick_mech_charge`/`tick_faith`（最后做，已在注册表框架内） |

> 挂点顺序约束：`_post_hp_lethal`/`_mitigate_chain`/`player_turn` 内**多条 if 有严格先后**（如坚韧先于坚城免眩晕、血怒先于铁誓、磐石触发顺序），迁移时把 if 骨架保留、只换 if 内部查表，禁止重排。

---

## 6. 风险与迁移顺序

### 6.1 风险清单

| 风险 | 等级 | 说明 | 缓解 |
|---|---|---|---|
| 默认数值双源（battle 本地写死 vs skills 数据） | **高** | 45 个无参 proc 数值仍写死在 battle.py；若 handler 只读 _ps 而 _ps 无值 → 行为清零（v181.C 已对 7 个乘区 proc 这么干） | **第一批先补数据**：把 45 个无参 proc 的引擎默认值回填 skills.py passive dict（纯 data commit，行为零变化——回填值 = 现引擎兜底值）；然后 handler 才可安全删本地默认 |
| 双消费点 proc（同 proc 两个挂点不同参数/不同语义） | 高 | shadow_dance_bonus(spd+crit_dmg)/soul_mark_cap(cap+乘区)/hunt_mark_cap/core_full 等 | 族内参数化 + 挂点 ctx 区分；handler 不得假设 proc 只有一个消费点。等价测试按"每挂点"做探针 |
| 聚合器顺序语义（多 proc 累加/连乘/break） | 中 | 原代码多数 `for...break`（max=1）但 counter 族是"多被动逐个 roll 不 break"；旋律族是"3 段聚合再统一乘" | handler 内逐字保留 break/聚合语义；测试锁定 |
| 一次性战斗标记序列化 | 中 | _berserk_revive_used/_stance_immortal_used/_core_last_stand_used/_death_pact_used/_tenacity_left_n 随 to_state/from_state 序列化（1266-1269/1556-1559） | handler 读写必须走 battle 属性（getattr/setattr），不落 actor dict 局部；from_state 已有这些字段 → 保持 |
| 模块级 tick handler 与 battle.py 顶部 _TICK_HANDLERS 注册 | 低-中 | _th_passive_heal 等注册到 core/tick_effects.py 同表，签名 (battle, actor, eff, logs) 与类方法不同 | 抽族时保留外层 tick 包装，族 handler 只做"某 proc 的数值/副作用" |
| 52 外名字消费点（pierce/fire_bonus/execute/counter_attack/death_pact/heal_shield/mark_extra/turn_heal/...） | 中 | battle.py 还有约 15+ 个非 52 proc 名字消费（stat 型/旧格式残留） | 明确不迁移、不注册；它们继续走旧通道（P1-C 遗留）。grep 回归断言：迁移后 battle.py 不得出现 `passive`-dict 之外的新名字直读 |
| 与其它 worktree 并行冲突 | 中 | w1(wt_p2a)/w2(wt_p2b) 也在 battle.py 域（P2-A/P2-B 注册表批次） | 主 agent 串行 merge；本批只动 battle.py + 新文件 passive_procs.py（新文件无冲突）；文档与 REFACTOR_PLAN 同步 |

### 6.2 迁移顺序（批次粒度，每批独立 commit + py_compile + 单测绿）

1. **P2-D0 数据回填（纯 data，行为零变化）**：skills.py 45 个无参 proc 补引擎兜底数值（per_layer/ratio/mult/cap/stacks/reduce/per_core/...）；顺带把 7 个已配参数 proc 核数值与引擎一致。产出：数据 = 引擎数值唯一权威。
2. **P2-D1 基建 + 试点 5 个独立 proc**（新文件 passive_procs.py + 挂点 1/5/17 改造）：
   - 试点集（A 类最独立、无双消费点、纯计算）：`speed_ratio_dmg`(挂点4)、`zhan_yi_lifesteal`(挂点5)、`poison_cap_up+poison_cap`(挂点17)、`focus_full_on_kill`(挂点22)、`skeleton_cap`(挂点21)。
   - 每挂点：OLD 探针 vs NEW 探针 输出等价（见 §7）；只动 1 个挂点 + 对应族。
3. **P2-D2 暴击/暴伤/面板族**：挂点 1/2/3（crit_cond_add ×4 + shadow_dance_bonus 双段 + 旋律 3）——注意 zhan_yi_crit/arcane_wisdom 等带 info 参数 & `_pre_cost_res` 快照。
4. **P2-D3 伤害乘区族**：挂点 4/6/14（dmg_mult_cond：speed_ratio/arcane_resonance/element_origin/element_sync 标记 + _deal_damage 5 段）。
5. **P2-D4 受击减伤/免控/致死复活族**：挂点 10/11/12（dr_cond/cc_immune_cond/cc_break_cost/revive_cond）——**本批风险最高**（顺序语义 + 一次性 flag），等价测试最重。
6. **P2-D5 反击/毒/杂项副作用族**：挂点 13/15/16/18/19/20/23（counter_cond/dot 族/flag_set/overflow_shield/heal_overflow）。
7. **P2-D6 tick 族收敛**：挂点 24（tick_regen/mech_charge/tick_faith；把模块 handler 内 proc 分支抽族，纯搬）。
8. **P2-D7 收尾校验**：grep battle.py 确认 52 proc 名字只剩 run_proc_family 调用（无直读 for）；启动校验函数（52 proc 全覆盖 or 已知缺口表）进 conftest 类测试；全量 run_all + numeric 绿。

> 前置依赖：P1-C 已 merge（9925a62 已在本树）✓。与 P2-A/P2-B（w1/w2）同文件域 → 主 agent 串行 merge。

---

## 7. 测试策略（等价验证：OLD vs NEW 探针）

### 7.1 三层验证

1. **静态等价**：每批迁移后 `git diff` 逐段人审（挂点 if 骨架未动、顺序未动、日志串未动）；`py_compile`。
2. **行为等价探针（推荐主手段）**：为每个挂点写"OLD vs NEW 双实现对比测试"——
   - 测试文件内保留该挂点迁移前逻辑副本（OLD），跑同一组 battle 场景（技能施放矩阵/受击矩阵/毒 tick/致死场景），断言 `run_proc_family` 输出 == OLD 输出。
   - 探针形态：直接构造 Battle（仿 tests/test_v109_2_passive_datadrive.py 的 mk_player/clean_db 模式），对每个 proc 学与不学两态 × 边界状态（资源 0/满、hp 30% 上下、debuff 层数 0/3/8）做差分。
   - 已有关卡 test_v109_2_passive_datadrive.py / test_v64_passive.py / test_v107_skills / test_stage6_skills_v2（conftest run 模式）作回归基线。
3. **全量回归**：`scripts/run_all_tests.py`（318） + `scripts/run_numeric_tests.py`（数值门禁铁律）全绿；`refactor_regression` 基线（docs/refactor_baseline_v176.json）可对比。

### 7.2 特殊验证点

- **双消费点 proc**：每挂点单独探针（不是 per-proc 一次）。
- **一次性 flag 复活链**：同一场战斗两次致死（第二次不触发）+ 战斗序列化恢复后再致死（_used 字段从 state 恢复，仍不触发）。
- **counter 聚合**：以守为攻+反击之王 双被动（60% ×120%）vs 单被动 vs 无被动 三态 roll 差分（用固定 random seed）。
- **52 全覆盖校验测试**：遍历 skills.py 52 proc → 断言 `PROC_FAMILIES` 含全部，或显式列入 KNOWN_GAPS（D 类 4 个 + E 类 4 个 tick）→ 未来新增 passive proc 若漏声明即测试红。

### 7.3 粒度提醒

族粒度粗 vs 细的取舍：**先细后粗**——第一批按 §4.2 的 20 族搬（每族 = 现有挂点代码直搬，行为最稳），全部绿后可选做"同构族合并"（crit_cond_add/dmg_mult_cond/stat_mult_cond/dr_cond → 谓词式通用执行器）作为纯重构批次。不要第一步就上大统一抽象（过度抽象风险，见 ENGINE_ARCHITECTURE_AUDIT §三）。

---

## 8. 交付物与文档联动

- 本设计文档：`docs/archive/REFACTOR_P2D_passive_proc_registry.md`（wt_p2d，已 commit）。
- 落地批次更新 `docs/archive/REFACTOR_PLAN_v181.md` P2-D 卡片（勾选 + 注明各批 commit）。
- 与 `docs/ARCHITECTURE_TARGET_STATE_v181.md` 保持对齐：core 注册表 + data 数值 + battle 编排三层验收线（§红线：data 无函数 / core 无内容名 / battle 无 if 分发链）。
- D 类 4 个空转与 E 类复核结论登记到技能引擎缺口清单（下批修复计划引用），不静默。

---

## 附录 A：52 proc 数据声明总表（skills.py 行号 + 分支 + 当前字段）

| proc | 行 | 分支/技能 | 被动字段（6cde807） |
|---|---|---|---|
| zhan_yi_lifesteal | 902 | 狂战士/淬血 | — |
| zhan_yi_crit | 1104 | 狂战士/狂热 | stacks 8, add 0.15 |
| tenacity | 1129 | 盾卫士/坚韧 | — |
| berserk_revive | 1245 | 狂战士/血怒·不灭 | — |
| zhan_yi_full_reduce | 1296 | 盾卫士/坚城之姿 | — |
| stance_immortal | 1318 | 盾卫士/铁誓·不动 | — |
| element_affinity | 1401 | 元素使/元素亲和 | — |
| arcane_intuition | 1430 | 奥术学者/奥术直觉 | — |
| element_sync | 1523 | 元素使/元素同调 | — |
| element_core | 1547 | 元素使/元素之核 | layers 3, add 0.20 |
| arcane_resonance | 1599 | 奥术学者/奥术共鸣 | mult 0.15 |
| element_origin | 1676 | 元素使/元素起源 | layers 2, mult 0.20 |
| arcane_wisdom | 1743 | 奥术学者/真知 | stacks 5, add 0.20 |
| arcane_constant | 1753 | 奥术学者/奥术恒常 | — |
| hunt_mark_up | 1968 | 森语者/自然之眼 | — |
| hunt_mark_cap | 1978 | 森语者/追猎者 | — |
| poison_cap_up | 2003 | 森语者/剧毒之心 | — |
| focus_surplus_crit | 2043 | 风行者/疾风之心 | surplus 40, add 0.20 |
| focus_full_on_kill | 2113 | 风行者/追风 | — |
| focus_regen_summon | 2183 | 森语者/森之共鸣 | — |
| speed_ratio_dmg | 2238 | 风行者/疾风·极 | — |
| heal_overflow_shield | 2326 | 神谕者/圣光回响 | — |
| faith_share | 2502 | 神谕者/信念·流转 | — |
| skeleton_cap | 2514 | 死灵祭司/骷髅海 | — |
| undead_faith | 2524 | 死灵祭司/亡灵祭仪 | — |
| death_contract | 2534 | 死灵祭司/死亡契约 | — |
| faith_overload_heal | 2633 | 神谕者/信念·圣化 | — |
| soul_mark_cap | 2685 | 死灵祭司/灵魂锁链 | — |
| finisher_up | 2767 | 影舞者/链舞 | — |
| poison_burst_up | 2846 | 毒刃者/蚀骨 | — |
| lian_duan_soft | 2902 | 影舞者/暗影之心 | — |
| shadow_dance_bonus | 2966 | 影舞者/暗影步·极 | spd_add 0.25, crit_dmg 0.20 |
| poison_cap | 2978 | 毒刃者/淬毒之心 | — |
| poison_weaken | 3002 | 毒刃者/剧毒之触 | — |
| shadow_dance_cd | 3095 | 影舞者/影舞·无间 | — |
| poison_all_up | 3121 | 毒刃者/万毒归宗 | — |
| poison_spread | 3161 | 毒刃者/毒刃·共鸣 | — |
| counter_chance | 3333 | 磐石行者/以守为攻 | — |
| shaken_awareness | 3357 | 格斗士/气力之心 | — |
| shaken_decay_half | 3412 | 格斗士/破绽感知 | — |
| core_overflow | 3439 | 磐石行者/磐石之心 | — |
| counter_up | 3449 | 磐石行者/反击之王 | — |
| core_reduce | 3486 | 磐石行者/大地之肤 | — |
| broken_extend | 3558 | 格斗士/破绽·极 | — |
| core_full | 3584 | 磐石行者/磐石之躯 | — |
| core_last_stand | 3621 | 磐石行者/不动如山 | — |
| melody_duet | 3682 | 咏叹者/二重唱 | — |
| melody_resonance | 3841 | 咏叹者/共鸣 | — |
| dirge_ctrl_up | 3927 | 挽歌者/镇魂安魂 | — |
| melody_full | 3982 | 咏叹者/万籁和鸣 | — |
| melody_master | 3992 | 咏叹者/咏叹·极 | — |
| dirge_debuff_dmg | 4058 | 挽歌者/挽歌·极 | — |
