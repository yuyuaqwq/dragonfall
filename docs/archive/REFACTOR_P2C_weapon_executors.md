# P2-C weapon_effects 96 handler → ~10 通用执行器收敛 — 只读侦察 + 方案设计（wt_p2c）

> 任务：REFACTOR_PLAN_v181.md P2-C。本文档为**只读侦察 + 方案设计**（未改 game/ 代码），落地给后续改造批次用。
> 侦察基线：worktree w5（wt_p2c @ 329989c，含 P2-D 设计文档 merge）。weapon_effects.py 1463 行 / weapon_effect_data.py 130 行 / battle.py 11291 行。
> 铁律：行为零变化；每步 py_compile + 单测绿；data 纯数据零函数；core 通用执行器+注册表；battle 纯编排零内容名。**本批次零代码改动**。

---

## 0. TL;DR

weapon_effects.py 现有 **79 个注册 key / 93 个 `_we_*` handler 函数（95 个 @register 装饰器）/ 11 个事件类型**，全部为"key → 事件 → 具体逻辑函数"一对一注册，handler 内自带 DEFAULT 数值兜底（v180E 阶段4 已开始读 `WEAPON_EFFECT_DATA` 表，但默认值仍双写）。全部 key 已在数据权威表 weapon_effect_data.py（92 行表项）**有值、零差异**（v180E 阶段4 逐字提取过）；表对 13 个"纯辅助 key"（`*_p` 后缀/无独立注册名）只读不注册。收敛目标：**79 key → ~15 个机制族 → ~10 个参数化通用执行器**（护盾/反伤/控制/治疗/DOT/直伤追击/叠层增幅/下次攻击标记/被动乘区/保命/特殊），装备名全部从 core 消失（数据声明驱动）。battle.py 有 9 个硬接线消费点（特效标记/数值在编排层直读），须按 §6 同步改造才可删 handler 内的旧标记写读。

---

## 1. 目标与范围

### 1.1 目标态（对齐 ARCHITECTURE_TARGET_STATE_v181.md 三层）

```
data/weapon_effect_data.py   ← key → {族: 执行器族名, 事件: [...]?, 数值...}  ← 纯数值+族声明（当前缺"族"字段）
core/weapon_executors.py     ← WE_EXECUTORS = {族名: 参数化执行器(battle, player, ctx, logs, we_data, key)}
                               + 事件分发器 proc_event(battle, player, event, ctx, logs)（保留 weapon_effects.proc 签名兼容）
battle.py                    ← 11 个 proc 挂点不变，只把 import 换到新分发器；9 个"特效标记直读点"改查执行器返回值/数据表
```

判定问题（抄目标态 §判定标准）：
1. 数值/阈值/概率 → data（表已有，补齐 `family`/`event`/`tag` 等元字段即可）。
2. 行为类型是否已有通用执行器 → 有则数据声明；无则判断是否新机制族（注册 ~20 行参数化执行器），不新写 handler。
3. 代码里出现具体内容名 → 错误信号。本文件 **79 key 全收敛后 core 侧不再出现任何装备名/特效 key 字符串**（仅保留 key→族映射表或直接读 data family 字段）。
4. 新增特效装备 → 只改 data（roster 一行 `weapon_effect` + 表一行族声明/数值）。

### 1.2 收编范围（79 注册 key 全量 + 表 13 个纯辅助 key 说明）

- 收编：79 个注册 key 中 **76 个走 weapon 通道**（roster/新手装备直挂）+ 3 个 `divine_execution/dragon_annihilation/star_destruction` 是 **affix 词条通道**（battle.py L5583 直连 affix effect 数据，不经 weapon_effects proc）——**不迁移**，保持现状（e2e 测试明确豁免这 3 key）。
- 表 92 项中 13 个 `*_p`/aux key（`time_staff_p/eternal_codex_p/rune_amp_p/sage_amp_p/thunder_weave_p/trinity_rhythm_p/mountain_break_p/oath_blade_p/combo_end_p/dusk_blade_p/arcane_firmament_p/retort_p/undying_will_t`）是**主 key 的被动消费段参数**（同一表行主 key 已含数值；这 13 行是 v180E 为 battle.py 被动段直读备的冗余/占位）——迁移时合并进主 key 行（见 §4.2 数据表补齐），不新开 key。
- 明确不在范围：battle.py 中**非本文件的特效状态消费**（不死鸟 phoenix_revive、套装 taken_*、affix 反伤减伤、食物特效）——本文件只收 weapon_effects 注册的 key。

### 1.3 非目标（红线）

- 不改任何 game/ 代码（本文档仅侦察+方案）。
- 不搬 handler 进 data/（鱼鱼拍板：搬家不是解耦）；执行器留在 core。
- 不改数值/日志文本/触发顺序；**数值差异以现状 handler 为准**回写表（P2-C 计划原文）。
- 不新增引擎行为（proxy/替身/新触发时机一律不做）。

---

## 2. 侦察发现：现状结构全量

### 2.1 文件与注册表结构

- `WEAPON_EFFECTS = {}`：key → `{event: fn}`（同 key 可注册多事件 → 14 个 key 双事件，见 §2.4）。
- `register(event_or_key, event=None)` 双形态：`@register("hit")`（key=函数名去 `_we_` 前缀）或 `@register("key","event")`（显式 key）。
- `proc(battle, player, event, ctx, logs)`：**遍历 `weapon_effect_ids()`（player.equipment 各槽 `weapon_effect` 字段）→ `WEAPON_EFFECTS[key][event]` → fn(battle, player, ctx, logs)**；异常静默吞（单特效失败不影响主流程）。
- 数据读取器 `effect_data(battle, player, key)`：① 装备实例 `we_data` 覆盖层（roster 生成时拷入）→ ② 表 `WEAPON_EFFECT_DATA[key]` 权威默认 → ③ 空 dict（handler 自带 DEFAULT 兜底）。
- 参数权威 = `_we_defaults(key)`（延迟 import data 表防循环）。

### 2.2 事件 → handler 数量与行号（93 函数；11 事件）

| 事件 | 函数数 | key 数 | 行区 | 代表 key |
|---|---|---|---|---|
| battle_start | 13 | 13 | 249-355, 990-995, 1377-1386, 1437-1445 | starlight_bulwark/gale_step/… |
| hit | 17 | 17 | 362-543, 1362-1374, 1399-1410, 1426-1434 | wind_mark/hunter_open/… |
| skill_hit | 11 | 11 | 549-661 | afterglow_splash/… |
| skill_cast | 5 | 5 | 667-700, 1388-1396, 1448-1459 | rune_amp/sage_amp/… |
| taken | 12 | 12 | 707-862 | sentinel_aegis/thorn_armor/… |
| heal | 7 | 7 | 869-949, 1413-1423 | vital_band/echo_bless/… |
| turn_start | 5 | 5 | 956-1024 | guard_regen/death_dance/… |
| enemy_act | 2 | 2 | 1031-1057 | randuin_weary/ice_vein |
| threshold | 5 | 5 | 1064-1148 | time_freeze/bedrock_crown/… |
| kill | 1 | 1 | 1155-1166 | dusk_blade |
| passive | 15 | 17 | 1173-1349 | twilight_execute/…（增伤/暴伤/乘区） |

> 说明：passive 事件 key 数(17) > 函数数(15) 因为 `retort_p` 一个函数被 3 个 key（gargoyle_retort/titan_retort/ranger_retort）叠装饰器注册（L1313-1316），同一 fn 分别以 3 key 挂 passive 事件；该 fn 体内部自行判断 3 key 中哪个在装备上。

合计：95 个 @register 装饰器（含叠装饰器）→ **93 个 `_we_*` 函数 → 79 个唯一注册 key**（另有 `_we_defaults` 等辅助函数非 handler）。

### 2.3 数据权威表覆盖审计（weapon_effect_data.py 92 项 vs 79 注册 key）

- **79/79 注册 key 全在表内、零值差异**（v180E 阶段4 已逐字下沉；本次复核 `wd.get(param, default)` vs 表值 diff=0）。
- **13 个表项无对应注册 key**（纯辅助被动段/占位，见 1.2）。13 = `arcane_firmament_p/combo_end_p/dusk_blade_p/eternal_codex_p/mountain_break_p/oath_blade_p/retort_p/rune_amp_p/sage_amp_p/thunder_weave_p/time_staff_p/trinity_rhythm_p/undying_will_t`。
- **7 处 handler 读参缺表字段（回退 handler 缺省，需补表）**：
  - `dusk_p` 读 `atk_pct 0.30`（表 `dusk_blade` 只有 `next_atk_pct`）→ 补 `atk_pct` 或改读同一字段。
  - `eternal_codex_p`/`rune_amp_p` 读 `per_pct 0.015/0.02`（表 `eternal_codex/rune_amp` 行是 `dmg_pct_per`）→ 字段名不一致（行为等价，字段名归一）。
  - `frost_ring` 读 `freeze_turns 1 / boss_slow 2`（表 `frost_ring` 行无此二字段；仅"已减速冻结"分支用）→ 补表。
  - `retort_p` 读 `fallback_pct 0.20`（表三 retort 行都是 `next_atk_pct`；fallback 只在无 eff 标记时兜底）→ 补 `fallback_pct` 或归一。
  - `undying_will_t` 读 `heal_pct 0.10`（表 `undying_will` 行无 heal_pct？实有 0.10——逐行核对见 §2.5）。

### 2.4 多事件 key（14 个——proc 遍历语义关键）

| key | 事件组合 | 说明 |
|---|---|---|
| starlight_bulwark | battle_start(唯一，we_starlight_next 刷新再入) | 周期刷新由 battle 2546-2552 触发再 proc |
| eclipse_crown | battle_start | 单事件 |
| undying_will | battle_start + threshold | 登记标记 → 阈值免死 |
| death_dance | battle_start + turn_start | 初始化缓伤池 → 每刻结算 |
| arcane_firmament | battle_start + passive | 挂标记 → 技能乘区 |
| rune_amp / sage_amp / eternal_codex | skill_cast + passive | 叠层 → 下技/每层乘区消费 |
| thunder_weave | hit + passive | 叠层+满层 charge → 下技乘区 |
| time_staff | turn_start + passive | 叠层+回血 → 攻击乘区 |
| trinity_rhythm / mountain_break / oath_blade | skill_hit + passive | 置标记 → 普攻乘区 |
| combo_end | hit + passive | 连段置暴伤标记 → 暴伤消费 |
| dusk_blade | kill + passive | 潜行置标记 → 潜行乘区 |

→ 注册表结构天然是"**事件扇出**"：14 个 key 同一把"置标记/生产"逻辑注册在 A 事件、消费在 B 事件。**通用执行器族的"生产-消费"配对必须作为一对整体迁移**（标记键名/消费字段/清除时点），拆散必行为漂移。

### 2.5 handler 数值 DEFAULT vs 数据表差异

- 逐 handler 扫描 `wd.get(param, DEFAULT)`：**表值 == 代码默认值 100%（0 差异）**——v180E 阶段4 已把数值下沉做干净。
- 残留"双源"形式：**缺字段回退仍写在 handler**（如 `wd.get("chance", 0.25)`——表有值永不触发缺省，但表删字段即静默回退）。迁移时把 DEFAULT 删除、改为"缺字段=无此行为"（对齐 v181.C 铁律）仅在确认表 92 项全量权威后执行。
- 表行额外含 handler 不读的展示字段（如 `shield_hp_pct` 与 `refresh_turns` 都读；无死参，除 §2.3 7 处外字段对齐良好）。

### 2.6 roster 消费面（99 处 weapon_effect 声明 / 82 distinct key）

- equip_roster.py 697 行装备中 **99 行带 weapon_effect**（82 distinct），we_data 覆盖层齐全（v180E 断链修复）；其中 3 key 走 affix 通道（§1.2 豁免），**76 个 weapon 通道 key 全部注册且有表值**。
- roster 分布（行数前几族）：直伤追击 14 / 护盾 13 / 控制 12 / 治疗 9 / 叠层 7 / 反伤 7 / 加速 6 / DOT 6 / 反击 6 / 下次攻击 5 / 被动乘区 4 / 特殊 3 / buff_stat 2 / 保命 2。
- 新手 8 key（novice_*）均注册且表有值；generate_roster_equip 拷 we_data（drops.py 362-368）。

---

## 3. 机制族归类（79 key 全量表）

### 3.0 归类口径

按 handler 行为语义（docstring + 代码副作用）把 79 key 归为 **15 个细族 → 14 个执行器族 → 13 个宏族**（护盾/反伤/控制/加速/治疗/DOT/直伤/叠层/下次攻击/被动乘区/保命/最大生命/特殊；无召唤族——weapon_effects 不含召唤 handler，召唤在套装/被动通道）。**~10 通用执行器**口径：把"宏族"里同构的再合并（反伤与护盾类被击分支可并、DOT 与直伤同属"命中后对敌负面"分支、被动乘区与保命各成一支），落到 **10 个执行器** 见 §4.1 目标注册表。

### 3.1 护盾族（10 key）

| key | 细族 | 事件 | 参数 | 行为 |
|---|---|---|---|---|
| starlight_bulwark | shield | battle_start | shield_hp_pct 0.10, refresh_turns 5 | 10%maxhp 盾，we_starlight_next 到期 re-proc |
| eclipse_crown | shield | battle_start | shield_hp_pct 0.15, spd_pct 0.10, next_atk_pct 0.15 | 15%盾+持盾速+破盾追伤标记 |
| sentinel_aegis | shield_taken | taken | chance 0.15, base 6, per_lv 0.5, turns 3, cd 1 | 受击概率盾 base+per_lv×lv |
| deeprock_aegis | shield_taken | taken | chance 0.10, shield_pct 0.08, cd 2 | 受击概率盾 %maxhp |
| bedrock_crown | shield_threshold | threshold | threshold 0.25, shield_hp_pct 0.20, turns 4 | 每场1次阈值盾 |
| firmament_crown | shield_threshold | threshold | threshold 0.30, shield_hp_pct 0.12, turns 3, per_battle 2 | 每场N次阈值盾 |
| gargoyle_heart | shield_threshold | threshold | threshold 0.30, shield_hp_pct 0.25, turns 4, heal_pct 0.10 | 阈值盾+回血 |
| echo_bless | heal_overflow_shield | heal | overflow_pct 0.30, cap_hp_pct 0.10 | 治疗溢出转盾 |
| atonement_shield | heal_overflow_shield | heal | cap_hp_pct 0.15 | 溢出全额转盾+持盾减伤标记 |
| endless_radiance | shield_crit | skill_hit | crit_dmg_pct 0.25(面板), shield_hp_pct 0.05, shield_turns 2, cd 3 | 暴击概率盾 CD |

差异点：盾量公式（%maxhp vs base+per_lv×lv）、事件（开战/受击/阈值/暴击/溢出）、CD 有无、次数限制、附带回血/追伤/减伤标记。**一个参数化盾执行器 + 事件 ctx（dmg/hp_ratio/is_crit/overflow）可全表达**。

### 3.2 反伤族（5 key）+ 反击强化族（4 key）

| key | 细族 | 参数 | 行为 |
|---|---|---|---|
| thorn_armor | reflect | reflect_pct 0.15 | ctx.dmg×pct 反弹 |
| retribution_ring | reflect | chance 0.20, reflect_pct 0.30 | 概率反弹 |
| iron_echo | reflect_heal | chance 0.20, reflect_pct 0.40, heal_pct 0.02 | 概率反弹+回血 |
| dragon_spine_mail | reflect_heal_down | chance 0.15, reflect_pct 0.25, heal_down 2 | 概率反弹+敌禁疗 |
| ember_bulwark | reflect_burn | max_hp_pct 0.05, burn_stack 1, burn_cap 5 | maxhp%反伤+叠burn(每刻1次) |
| gargoyle_retort | retort_next_atk | next_atk_pct 0.30 | taken → eff.we_retort=max |
| titan_retort | retort_next_atk | next_atk_pct 0.40 | 同上 |
| ranger_retort | retort_next_atk | next_atk_pct 0.20 | 同上 |
| guardian_will | enemy_weaken_next | chance 0.08, weaken 0.25 | 受击 → 敌下次攻击-25% |

差异点：反伤是否需 chance/是否附加治疗或禁疗或灼烧/每刻限次；反击族三 key 同写 `we_retort=max` 由被动段 `retort_p` 消费，`guardian_will` 走 e_buffs 弱化。**反射执行器 + 反击标记执行器两把**。

### 3.3 控制族（9 key）

| key | 细族 | 参数 | 行为 |
|---|---|---|---|
| frost_ring | slow_or_freeze | chance 0.25, slow_turns 2, slow_pct 0.40, freeze_turns 1, boss_slow 2 | 已减速→冻结否则减速 |
| holy_judgment_field | slow_heal_down | chance 0.30, slow_turns 2, slow_pct 0.30, heal_down 2 | 减速+禁疗 |
| everfrost_domain | freeze_cd | chance 0.30, freeze_turns 1, boss_slow 2, cd 3 | skill_hit 冻结 CD |
| everfrost_scepter | freeze | chance 0.20, freeze_turns 1, boss_slow 2 | skill_hit 冻结 |
| frost_crown | freeze_taken_limited | chance 0.10, max_per_battle 2, freeze_turns 1, boss_slow 2 | taken 冻结限次 |
| holy_word_bind | freeze_heal | chance 0.20, freeze_turns 1, boss_slow 2 | heal 事件冻结(非溢出段) |
| time_freeze | threshold_stun | threshold 0.30, per_battle 1 | 阈值→敌 stun |
| randuin_weary | enemy_spd_down_stack | max_stack 3, spd_down_pct 0.06 | enemy_act 叠层减速 |
| ice_vein | enemy_spd_down_stack | max_stack 3, spd_down_pct 0.08 | enemy_act 叠层减速 |

差异点：事件（hit/skill_hit/taken/heal/threshold/enemy_act）、冻结 vs 减速 vs 禁疗 vs 定身、CD/限次。**一个控制执行器 + mode 参数（slow/freeze/stun/spd_down_stack/heal_down）全表达**（Boss 免疫退化逻辑冻结族统一 `_freeze_enemy`）。

### 3.4 加速/面板族（7 key）

| key | 细族 | 参数 | 行为 |
|---|---|---|---|
| gale_step | spd_buff_battle_start | spd_pct 0.15, turns 3 | buffs.gale_step + eff.gale_step_pct |
| swift_boots | 同上 | spd_pct 0.20, turns 3 | 同上（同名 buff 同键 gale_step） |
| deadman_stride | 同上 | spd_pct 0.15, turns 4 | 同上 |
| temple_stride | 同上 | spd_pct 0.20, turns 4 | 同上 |
| void_stride | 同上 | spd_pct 0.25, turns 4 | 同上 |
| novice_wind_spd | spd_buff_on_hit | spd_pct 0.05, turns 2 | hit → buffs.novice_wind_spd |
| wind_mark | stack_spd | max_stack 4, spd_pct_per 0.02 | hit 叠层 → _player_stats 乘 |
| thunder_weave | stack_atk_spd | max_stack 5, spd_pct_per 0.02, atk_pct_per 0.01, charge_pct 0.20 | hit 叠层(面板双乘)满层置 charge |
| abyss_barrier | maxhp_buff | max_hp_pct 0.08 | battle_start 永久加 maxhp |
| arcane_firmament | passive_dmg_mult_kind | matk_pct 0.15, skill_dmg_pct 0.10 | battle_start 挂标记；passive 魔法乘区 |

差异点：buff 键名/数值/层数语义（同名 gale_step 家族共享键 = 面板 `_player_stats` 读 `gale_step_pct`）。**加速执行器（写 buffs+eff 键）+ 面板叠层执行器**。

### 3.5 治疗族（9 key）

| key | 细族 | 参数 | 行为 |
|---|---|---|---|
| vital_band | heal_amp | heal_pct 0.15 | ctx.heal ×(1+pct)（溢出段跳过） |
| holy_radiance_mail | heal_amp | heal_pct 0.20 | 同上 |
| echo_band | heal_amp | heal_pct 0.25 | 同上 |
| novice_regen_heal | heal_amp | heal_pct 0.10 | 同上 |
| guard_regen | regen_turn_start | pct 0.02 | 每刻回已损% |
| dawn_regen | regen_turn_start | pct 0.02 | 每刻回 max% |
| undying_band | regen_turn_start | pct 0.015 | 每刻回 max% |
| time_staff | regen_turn_start | per_pct 0.015, max_stack 10 | 每刻叠层+回 max% |
| novice_dawn_mana | mp_regen_once | mp 10 | skill_cast 首次回蓝 |

差异点：加成 vs 每刻回复 vs 回蓝；regen 三式（已损%/max%/带叠层）。**治疗执行器（heal ctx 增幅/溢出转盾已有 §3.1）+ 回血执行器 + 回蓝执行器**（≈可并回治疗族一把）。

### 3.6 DOT 族（4 key）

| key | 参数 | DOT 键 |
|---|---|---|
| smith_blaze_wound | chance 0.20, dot_pct 0.015, dot_pct_boss 0.01, turns 3 | blaze |
| rong_lu_yu_wen | chance 0.20, dot_pct 0.03, dot_pct_boss 0.015, turns 2 | burn |
| ember_burn | chance 0.30, dot_pct 0.015, dot_pct_boss 0.01, turns 3 | ember |
| blood_trace | chance 0.25, pct 0.02, pct_boss 0.015, turns 4 | blood_trace（当前生命%） |

差异点：DOT 键名/概率/比例（最大 vs 当前生命）/Boss 比例/turns。**一个 DOT 执行器（参数含 dot_key/pct/boss_pct/turns）+ `_apply_dot` 共享动作**。

### 3.7 直伤/追击族（11 key）

| key | 细族 | 参数 | 行为 |
|---|---|---|---|
| afterglow_splash | splash_magi | chance 0.30, atk_pct 0.15 | skill_hit 奥术溅射 |
| spellblade_echo | splash_magi | atk_pct 0.25 | skill_hit 奥术溅射 |
| annihilation_echo | splash_magi | chance 0.35, atk_pct 0.30 | skill_hit 奥术溅射 |
| wind_split | extra_phys | chance 0.25, atk_pct 0.50 | hit 物理追加 |
| phantom_barrage | extra_phys_pene | chance 0.20, atk_pct 0.30, pene_pct 0.50, guarantee 5 | hit 破防追加+保底 |
| endless_blade | extra_phys_oncrit | atk_pct 0.20 | skill_hit 暴击追击(每刻1) |
| hunter_open | true_dmg_nth_hit | count 3, atk_pct 0.12 | 每N次真伤 |
| siren_fang | true_dmg_nth_hit | count 3, atk_pct 0.40 | 每N次真伤 |
| star_pierce | true_dmg_nth_hit | count 4, atk_pct 0.20, lost_hp_pct 0.03, cap_pct 0.05 | 每N次真伤(已损加成) |
| soul_eater | curhp_dmg_heal | cur_hp_pct 0.02 | 敌当前生命%伤+回等量 |
| novice_lifesteal | lifesteal | heal_pct 0.05 | 伤害5%吸血 |

差异点：伤害类型（物/奥/真）、防御穿透、概率、计数触发 vs 每击、吸血/自愈。**1-2 把"命中后追加伤害"执行器（mode: phys/magi/true/pene/nth/crit + 参数）表达**。

### 3.8 叠层增幅族（7 key）

| key | 事件 | 参数 | 行为 |
|---|---|---|---|
| rune_amp | skill_cast+passive | max_stack 5, dmg_pct_per 0.02 | 叠层→下技×(1+2%/层)后清 |
| sage_amp | skill_cast+passive | need 2, charge_pct 0.25 | 计数→charge 下技×1.25 |
| eternal_codex | skill_cast+passive | max_stack 8, dmg_pct_per 0.015 | 叠层→每层+1.5% |
| thunder_weave | hit+passive | max_stack 5, spd/atk_pct_per, charge_pct | 叠层满→charge |
| wind_mark | hit | max_stack 4, spd_pct_per 0.02 | 叠层→面板速度 |
| time_staff | turn_start+passive | per_pct 0.015, max_stack 10 | 叠层→攻击乘区 |
| novice_hunt_combo | hit | per_stack 0.08, max_stack 5 | 暴击叠层→连击率 |

差异点：事件、消费时点（下技 vs 每层常驻）、面板 vs 乘区、清空/不清空。**叠层执行器（mode: per_cast/hit/crit + 消费参数 + 目标槽 stacks/eff 键）**。

### 3.9 下次攻击标记族（5 key）

| key | 事件 | 参数 | 行为 |
|---|---|---|---|
| trinity_rhythm | skill_hit+passive | atk_pct 0.30, thunder_pct 0.15 | 标记 we_trinity(+thunder) |
| mountain_break | skill_hit+passive | atk_pct 0.25 | 标记 we_mountain |
| oath_blade | skill_hit+passive | atk_pct 0.25 | 标记 we_oath（每刻1） |
| novice_spark_followup | skill_cast | atk_pct 0.10 | 标记 novice_spark |
| dusk_blade | kill+passive | next_atk_pct 0.30 | 潜行+标记 we_dusk_dmg |

差异点：事件（skill_hit vs skill_cast vs kill）、标记键、清除点、潜行附赠。**"下次攻击强化"执行器 + battle 攻击消费点查表**。

### 3.10 被动乘区族（4 key）

| key | 参数 | 条件 |
|---|---|---|
| twilight_execute | threshold 0.40, dmg_mult 1.25 | 敌 hp<40% ×1.25 |
| star_slayer_edge | threshold 0.70, dmg_mult 1.15, crit_dmg 0.30 | 敌 hp>70% ×1.15 + 暴伤面板+0.3 |
| arcane_firmament | skill_dmg_pct 0.10 | 魔法技 ×1.10 |
| combo_end | crit_dmg 0.40, combo_need 3 | 连段≥3 暴伤+0.4 |

差异点：条件谓词（hp 上下限/kind/连段）、数值作用面（mult 乘区 vs crit_dmg 加法 vs 面板）。**被动乘区执行器（cond 键 + mode: mult/crit_dmg）**。

### 3.11 保命/特殊族（5 key）

| key | 细族 | 参数 | 行为 |
|---|---|---|---|
| death_dance_armor | passive_dr_revive | taken_reduce_pct 0.08, revive_hp_pct 0.12 | passive taken −8%；致死复活 12%（battle 复活链消费，本文件只置位/乘区） |
| undying_will | threshold_immune_revive | hp_pct 0.10, threshold 0.20 | 阈值免死+回血 10% |
| death_dance | dot_pool | pool_pct 0.35, pay_pct 0.10, max_turns 10 | 缓伤池（taken 填充 35% → turn_start 结算 10%） |
| novice_first_turn_guard | marker_first_turn_dr | reduce_pct 0.10 | battle_start 标记 → 10454 减伤 |
| novice_first_turn_dodge | marker_first_turn_dodge | dodge_pct 0.05 | battle_start 标记 → 闪避判定读 |

特殊：death_dance 的 pool 填充在 battle.py `_post_hp_lethal` 硬编码 `dmg*0.35`（L10844，**不在 weapon_effects 内**——同 key 双事件但填充点在 battle 编排层）；`undying_will` 免死回拉也在 battle L10837-10841（读 eff 标记）。**这类 key 的"编排层消费段"迁移时需 battle 一并改**（§6 风险表）。

---

## 4. 设计：机制族收敛方案

### 4.1 目标注册表（~10 通用执行器，仿 SET_PROC_TYPES / MECH_EFFECTS）

新文件 `game/core/weapon_executors.py`（或改造 weapon_effects.py 内部，见 §4.3 取舍）：

```python
WE_EXECUTORS = {}   # 族名 → fn(battle, player, ctx, logs, we: dict, key: str)
# we = effect_data(battle, player, key) 解析后的参数 dict（含 family 字段）
# ctx = proc 挂点语义字典（dmg/heal/taken/is_crit/hp_ratio/overflow/target…），各挂点保持现状字段
# 分发器（保留 weapon_effects.proc 签名兼容，先双轨后替换）：
def proc_event(battle, player, event, ctx=None, logs=None): ...
```

| # | 族（注册键） | 覆盖 key 数 | 读参数 | 事件 |
|---|---|---|---|---|
| 1 | `proc_shield` | 10 | shield_base/shield_hp_pct/per_lv/refresh_cd/limit(+heal_pct/next_atk_pct) | battle_start/taken/threshold/skill_hit(暴击)/heal(溢出) |
| 2 | `proc_reflect` | 5 | chance/reflect_pct/附赠(heal_pct/heal_down/burn)/每刻限次 | taken |
| 3 | `proc_retort_mark` | 4 | next_atk_pct/weaken | taken（置标记/敌弱化） |
| 4 | `proc_control` | 9 | mode(slow/freeze/stun/spd_down/heal_down)/turns/pct/cd/limit | hit/skill_hit/taken/heal/threshold/enemy_act |
| 5 | `proc_buff` | 6 | buff_key/buff_val_pct/turns | battle_start/hit |
| 6 | `proc_heal` | 9 | mode(amp/regen_max/regen_lost/mp_once)/pct | heal/turn_start/skill_cast |
| 7 | `proc_dot` | 4 | chance/dot_key/pct/boss_pct/turns | hit/skill_hit |
| 8 | `proc_extra_dmg` | 11 | mode(phys/magi/true/pene/nth/crit/lifesteal)/chance/pct/count/pene | hit/skill_hit |
| 9 | `proc_stack` | 7 | mode(cast/hit/crit)/max_stack/per_pct/consume/charge/面板键 | skill_cast/hit/passive |
| 10 | `proc_next_atk_mark` | 5 | mark_key/atk_pct/extra | skill_hit/skill_cast/kill |
| 11 | `proc_passive_mult` | 4 | cond(threshold/kind/combo)/mode(mult/crit_dmg)/值 | passive |
| 12 | `proc_dr_revive` / `proc_special` | 5 | 见 §3.11 | passive/taken/threshold/battle_start/turn_start |

> 说明：12 个注册键（比 ~10 略多是因为缓伤池/首刻标记需要独立编排协作位）。若把 `proc_heal` 的 regen/mp 与 heal_amp 分拆即回 12；把 `proc_special` 3 key 并入对应族（death_dance 的 pool 结算可并入 heal？不可——建议保留独立族）则 ~13。**落地方案建议先 12-13 个族注册、全绿后再评估合并**（粒度先细后粗，抄 P2-D §7.3）。

### 4.2 数据表补齐方案（weapon_effect_data.py 增量字段）

当前表 = key → {数值参数}；收敛后需要每条 key 额外声明（**纯数据，零函数**）：

```python
WEAPON_EFFECT_DATA = {
  "starlight_bulwark": {
      "family": "proc_shield",              # ← 新：执行器族名（core 分发键）
      "event": ["battle_start"],            # ← 可选：不写则按 family 默认事件表（少写少错）
      "shield_hp_pct": 0.10, "refresh_turns": 5,
      "shield_key": "we_starlight",         # ← 新：标记键（现硬编码在 handler）
      "log": "✨ 星辉壁垒：战斗开始获得 10% 最大生命护盾！",  # ← 新：日志串（行为零变化保留原文案）
  }, ...
}
```

补齐清单：
1. **`family` 字段**：79 注册 key 全量标注（§3 表即为标注底稿）；roster we_data 覆盖层不覆盖 family（装备实例不该改行为类型）。
2. **`event` 字段（或默认族事件表）**：14 个多事件 key 要显式声明（`rune_amp: ["skill_cast","passive"]`），否则分发器要按"置标记段 vs 消费段"拆——建议**族默认事件表 + key 显式覆盖**。
3. **标记键下沉**：handler 内 `we_starlight/we_retort/gale_step_pct/hunter_cnt…` 44 个标记键（§5.2）全部写成表字段（`stack_key/mark_key/buff_key/shield_key/...`），执行器只读参数。
4. **补 7 处缺表字段**（§2.3）：`dusk_blade.atk_pct=0.30`、`eternal_codex.per_pct=0.015`、`rune_amp.per_pct=0.02`（或消费侧改读 `dmg_pct_per`）、`frost_ring.freeze_turns/boss_slow`、`retort_p` 三行 `fallback_pct`、核对 `undying_will.heal_pct`。
5. **13 个 `*_p`/aux 表项**：并入主 key 行（同主 key 的被动段参数），表内不再出现未注册 key 行（除 affix 通道 3 key 说明注释）。
6. **删除 handler 内 DEFAULT**：表全量权威后，handler/执行器内 `wd.get(x, default)` → `wd.get(x)`（缺字段=无此行为）；但**第一步必须保行为**——先全量核表（本批已完成 diff=0），再分族改。

### 4.3 文件布局取舍

- 方案 A（推荐）：**改造 weapon_effects.py 本体**——保留 `proc(battle,player,event,ctx,logs)`/`weapon_effect_ids`/`effect_data`/`has_effect` 对外 API（battle.py 19 个 import 点不炸），内部把 93 个函数换成 12 个族执行器 + key→族映射（或读 data family）。文件名/对外符号不动，diff 最小、风险最低。
- 方案 B：新文件 `weapon_executors.py` + weapon_effects.py 变薄壳。更"干净"但 battle.py import 目标要改（19 处函数内 import）+ 双模块引用表（P2-B 已把 ACT_TICK 迁 constants——同批顺手）。
- **推荐 A 起步**（行为零变化最稳），收尾后如要"core 零内容名"验收再拆 B（此时纯搬壳）。

### 4.4 迁移顺序（批次粒度）

| 批 | 内容 | 风险 | 依赖 battle 改造点 |
|---|---|---|---|
| C1 | **数据表补齐**（family/event/标记键/日志串字段 + 7 处缺参 + 13 aux 并入）纯 data commit | 极低 | 无（表加字段 = 行为零变化） |
| C2 | 试点族：`proc_dot`（4）+ `proc_reflect` 纯反伤（thorn/retribution）+ `proc_heal` amp（vital/holy_radiance/echo_band/novice_regen_heal）——**无标记键、无编排层直读** | 低 | 无（纯事件内替换） |
| C3 | `proc_shield` 族（10 key）——**starlight 周期刷新依赖 battle 2546 重 proc** | 中 | 2546-2552 保留（re-proc battle_start 语义不变） |
| C4 | `proc_extra_dmg`（11）+ `proc_dot` 收尾 | 中 | 无 |
| C5 | `proc_control`（9） | 中 | 无（全走 e_buffs/_freeze_enemy 共享动作） |
| C6 | `proc_buff` + `proc_stack` 面板段（wind_mark/thunder_weave/gale 族——**`_player_stats` 直读 gale_step_pct/层数**） | 中高 | `_player_stats` 4736-4778 改查执行器输出/数据表（此段 8 处直读 effect_data + 状态键） |
| C7 | `proc_next_atk_mark` + `proc_retort_mark`（**标记键被 `_player_attack`/`_decay_buff_table`/被动段消费**） | 中高 | `_player_attack` 6645 novice_spark、`_decay_buff_table` 9360 we_oath、被动段消费点 |
| C8 | `proc_passive_mult` + `proc_stack` 乘区段（被动 15 函数收敛） | 中 | 无（passive 挂点统一 ctx） |
| C9 | 保命/特殊族：`undying_will`/`death_dance`/`death_dance_armor`/novice 首刻标记（**battle `_post_hp_lethal`/`_mitigate_chain` 直读 eff 标记与 0.35 池填充**） | **高** | `_post_hp_lethal` 10837-10844 与 `_mitigate_chain` 10446-10448 改查表（0.35→pool_pct 表读） |
| C10 | 收尾：删旧 handler 死代码、删 `wd.get` DEFAULT、全量回归 + numeric 门禁 | 中 | grep 断言 battle.py 无 we_* 内容名直读 |

> 先 C1（数据补齐），再低风险独立族（C2-C5），高风险 battle 状态深依赖（C6-C9）殿后——每批独立 commit + py_compile + 相关单测绿。

---

## 5. 测试策略（等价验证 OLD vs NEW）

### 5.1 已有测试覆盖盘点（沙盒实跑全绿）

| 测试 | 覆盖 | 结果 |
|---|---|---|
| tests/test_v140_weapon_effects.py | 10 类时机抽样 12 断言：星辉盾/疾风步 buff/风痕 3 层/余波概率/哨兵盾/圣辉+20%/晨曦回血/暮光处决/磐石盾/暮裂潜行/奥术魔攻 | ✅ 12 通过 |
| tests/test_numeric_weapon_effect_chain.py | 断链回归 7 断言：roster→实例带 key+we_data/effect_data 回退表/穿星 4 连真伤 | ✅ 7 通过 |
| tests/test_numeric_weapon_effect_e2e.py | 99 件全链路 8 断言：覆盖表全 key/四事件抽样触发 | ✅ 8 通过 |

覆盖缺口：**只抽样 79 key 中 ~15 个**；无被动段（passive 15 函数/12 key）、无 heal 溢出转盾、无控制族、无叠层增幅族、无缓伤池、无保命族单测。e2e 已保证"全 key 有表值"。

### 5.2 建议探针策略

1. **族级 OLD vs NEW 差分探针**（新测试文件，仿 test_v140 的 mk_player 直挂 key 模式）：对每族抽 2-3 代表 key，同一 battle 场景下跑 `weapon_effects.proc`（OLD）与 `proc_event`（NEW）→ 断言 logs/ctx/state（hp/shields/buffs/stacks/eff/debuffs/e_buffs）逐字段相等。固定 random.seed。
2. **标记键状态快照对比**：对每个会写 eff/stacks/buffs 的 handler，探针断言迁移前后 44 个标记键（§3.2 侦察：we_starlight_next/gale_step_pct/hunter_cnt/…/novice_*）写读完全一致。
3. **双事件 key 专门探针**（14 个）：A 事件置标记 → B 事件消费链全流程 OLD/NEW 对比（含清除时点：rune_amp passive 消费后清 0）。
4. **battle 编排层直读点探针**（9 处）：`_player_stats` 面板（gale/wind_mark/thunder_weave/novice_wind_spd/奥术/暴伤）/ `_player_attack` novice_spark / `_mitigate_chain` taken+守御 / `_post_hp_lethal` 不死+池 / `_decay_buff_table` we_oath / `_skill_dodge` novice_dodge —— 每点构造战斗场景断言等价。
5. **回归网**：沙盒 `scripts/run_numeric_tests.py`（51 文件数值门禁铁律）+ `run_all_tests.py`（318）全绿；refactor_baseline 对比。

---

## 6. 风险清单

| 风险 | 等级 | 说明 | 缓解 |
|---|---|---|---|
| battle.py 9 处特效状态/数值直读（编排层内容名残留） | **高** | `_player_stats` 8 段直读（4736-4778 gale/wind_mark/thunder/novice_wind_spd/奥术 matk/星陨暴伤/辉光暴伤）、`_player_attack` 6645 novice_spark、`_mitigate_chain` 10454 novice_guard_active、`_skill_dodge` 10283 novice_dodge_active、`_decay_buff_table` 9360 we_oath、`_post_hp_lethal` 10837-10844 we_undying_immune/we_death_pool **0.35 硬编码** | 迁移族时同步改这些点读表/读执行器返回值（C6/C7/C9 批次内）；0.35 → `death_dance.pool_pct` 表读 |
| 缓伤池 death_dance 双向（handler 结算 10% + battle 填充 35%） | 高 | pool 填充在 battle `_post_hp_lethal` 不在 weapon_effects；只收 handler 会漏半条链 | C9 一并迁移 battle 填充段；探针锁定池数值 |
| 14 个双事件 key 生产-消费配对 | 高 | 拆开迁移 → 标记键/清除时点漂移 | 按 key 整体迁移（A+B 事件一次换）；标记键快照探针 |
| 面板属性段（_player_stats 直读层数/pct） | 中高 | gale/wind_mark/thunder_weave 的数值读在 battle 面板合成处，handler 只写标记 | C6 同步改 `_player_stats`（读表 per_pct） |
| 共享 buff 键（gale_step 家族 5 key 同键） | 中 | 5 个 key 写 `buffs.gale_step` + `eff.gale_step_pct`；若执行器按 key 单写会互相覆盖语义变化 | 参数 `buff_key=gale_step` 显式共享；diff 探针 |
| we_data 覆盖层与表 family 冲突 | 中 | 装备实例 we_data 只应覆盖数值，若含 family 会改行为类型 | effect_data 合并时剥离非数值键（白名单） |
| 周期刷新 starlight 双路径 | 中 | battle 2546-2552 到期 re-proc battle_start（写 we_starlight_next），收盾执行器时保留该编排回路 | C3 单批；不动 2546-2552 |
| 日志文案依赖（测试/玩家攻略） | 低-中 | 现有 27 测试与攻略引用日志串（"星辉壁垒"/"哨兵壁垒"等） | 日志串原样下沉表 `log` 字段；测试回归 |
| 与并行 worktree 冲突 | 中 | w1/w2/w4/w6 在 battle.py/data 域并行 | 主 agent 串行 merge；本批文档先行 |
| 删除 wd.get DEFAULT 前表权威校验 | 中 | 表 92 项若缺某 key 行为即清零 | C1 先补全 + C10 收尾才删 DEFAULT；数值门禁护航 |

### 6.1 必须由 battle 传入/协作的（执行器签名 ctx 扩展）

- taken 事件：`ctx.dmg`（reflect 基数）、`ctx.taken`（被动减伤链改写值）、target hp 存活检查（enemy 已死不反伤）——现状已传。
- threshold 事件：`ctx.dmg` + actor hp/max_hp 比（handler 自读 actor 即可）。
- heal 事件：两段（加成段 ctx.overflow=0 / 溢出段 ctx.overflow=real）——执行器要能区分（现状 has ctx.overflow 标志）。
- `_player_stats`/`_player_attack`/闪避判定/缓伤池填充：**在 battle 编排层，不经 proc 事件**——迁移必须提供"面板加成查询"API（如 `weapon_stat_bonus(battle, player, st)` 替代 8 段散读）或保留 battle 读表。

---

## 7. 交付物

- 本文档：`docs/archive/REFACTOR_P2C_weapon_executors.md`（wt_p2c 分支 commit）。
- 落地批次更新 `docs/archive/REFACTOR_PLAN_v181.md` P2-C 卡片。
- 侦察数据副产品（临时，不入仓）：79 key 归类表 / 92 表项覆盖 diff=0 / 44 标记键写读矩阵 / roster 99 行族分布——已并入本文档 §2-§3。

---

## 附录 A：79 注册 key → 宏族速查（供 C1 数据表批直接引用）

- 护盾(10)：starlight_bulwark eclipse_crown sentinel_aegis deeprock_aegis bedrock_crown firmament_crown gargoyle_heart echo_bless atonement_shield endless_radiance
- 反伤(5)：thorn_armor retribution_ring iron_echo dragon_spine_mail ember_bulwark
- 反击标记(4)：gargoyle_retort titan_retort ranger_retort guardian_will
- 控制(9)：frost_ring holy_judgment_field everfrost_domain everfrost_scepter frost_crown holy_word_bind time_freeze randuin_weary ice_vein
- 加速/面板(7)：gale_step swift_boots deadman_stride temple_stride void_stride novice_wind_spd wind_mark(+thunder_weave 面板段/abyss_barrier/arcane_firmament 面板段)
- 治疗(9)：vital_band holy_radiance_mail echo_band novice_regen_heal guard_regen dawn_regen undying_band time_staff(回血段) novice_dawn_mana
- DOT(4)：smith_blaze_wound rong_lu_yu_wen ember_burn blood_trace
- 直伤(11)：afterglow_splash spellblade_echo annihilation_echo wind_split phantom_barrage endless_blade hunter_open siren_fang star_pierce soul_eater novice_lifesteal
- 叠层(7)：rune_amp sage_amp eternal_codex thunder_weave wind_mark time_staff novice_hunt_combo
- 下次攻击(5)：trinity_rhythm mountain_break oath_blade novice_spark_followup dusk_blade
- 被动乘区(4)：twilight_execute star_slayer_edge arcane_firmament combo_end
- 保命/特殊(5)：death_dance_armor undying_will death_dance novice_first_turn_guard novice_first_turn_dodge

（注：wind_mark/time_staff/thunder_weave/arcane_firmament 等跨面板+乘区双消费，宏族归类按主事件，族内参数化解决双段。）
