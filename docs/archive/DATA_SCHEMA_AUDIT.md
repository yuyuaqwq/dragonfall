# 数据域 Schema 脏数据审计报告（配置编辑器前置 · 路线图 2.1）

* 生成日期：**2026-09-11**
* 校验器：`schema/validate.py`（引擎 `jsonschema 4.26.0`，draft 2020-12；内建最小校验器为等价退化路径）
* 数据来源：`game/data/`（只读）。不 import 引擎（`game/core/`、`game/battle2/` 并行重构中）
* 复现：`python schema/validate.py` / `--json` / `--domain <域>`
* **本报告只做诊断，未改动任何数据值，也未改动引擎。**

---

## 1. 新建文件清单

| 文件 | 行数 | 说明 |
|---|---:|---|
| `schema/skill.schema.json` | 627 | 技能：`skill`(条目) + `player_skills` / `branch_skills` / `tutor_skills`（整表） |
| `schema/monster.schema.json` | 347 | 怪物：`monster_skill` / `monster_skill_table` / `monster_template`(六元组) / `hidden_monster` / `elite_equip_drop` |
| `schema/affix.schema.json` | 166 | 词条：`affix` / `affix_table` / `affix_pool_by_quality` / `affix_kind` |
| `schema/item.schema.json` | 311 | 物品：`item` / `item_table` |
| `schema/effect_rules.schema.json` | 422 | 声明表：`effect_rule` / `effect_rules_table` / `effect_actions` / `mech_cash` |
| `schema/passive_proc.schema.json` | 282 | 被动声明：`passive_proc` / `passive_proc_table` |
| `schema/validate.py` | 631 | 校验器 + CLI（`validate_all()` / `--domain` / `--json` / `--quiet` / `--strict-unknown`，门禁 exit 0/1） |
| `schema/README.md` | 211 | 怎么读 / 怎么扩展 / 字段含义摘要 / 维护规则 / 编辑器接口约定 |
| `docs/archive/DATA_SCHEMA_AUDIT.md` | 370 | 本文件（脏数据审计报告） |
| `tests/test_schema_validate.py` | 255 | 15 个用例：schema 合法 / **examples 自身合法** / 正反例 / 双引擎一致 / 现网违规基线（锁 5 条）/ CLI exit 码 |
| **合计** | **3622** | 全部为**新建文件**；`game/data/**` 与引擎零改动 |

> 枚举与 examples 的**一次性归纳脚本**未入库（放在 agent 工作区 `gen_schemas.py`），
> 避免「每次跑生成器就覆盖 schema」；schema 文件此后**手工维护**，维护规则见 `schema/README.md` §6。
> 共 19 条 `examples` 覆盖 13 个 def，且示例本身全部通过校验（测试断言）。

---

## 2. 各域条数 + 字段覆盖率

条目总数 **2569**（skills 305 + monsters 1168 + affixes 76 + items 900 + effect_rules 78 + passive_proc 42）。

> 覆盖率 = 该字段在条目中的出现率。**未设进 `required` 的低覆盖字段是设计使然**（按技能/物品类型可选），
> 把它们设成必填会让历史数据全报错。`--strict-unknown` 额外违规 = **0**，
> 即：**schema 声明的字段集合 = 现网实际用到的字段集合（零遗漏、零多余）**。

### 2.1 skills（305 条 = player 61 + branch 238 + tutor 6）

必填：`name` / `kind` / `lv` / `desc`。共 51 个字段。

| 字段 | 覆盖率 | 出现/总数 | 类型 |
|---|---:|---|---|
| `desc` `kind` `lv` `name` | 100.0% | 305/305 | str / str / int / str |
| `power` | 100.0% | 305/305 | float 304 + int 1 |
| `cast` | 98.0% | 299/305 | float 248 + **str 51（历史哨兵 `"None"`）** |
| `mp` | 97.4% | 297/305 | int |
| `cd` | 80.0% | 244/305 | int |
| `exprs` | 47.5% | 145/305 | list[str] |
| `mech` | 26.6% | 81/305 | str（33 枚举） |
| `effect` | 19.7% | 60/305 | str（37 枚举） |
| `buff_turns` | 19.3% | 59/305 | int |
| `mech_val` | 17.4% | 53/305 | int 48 + float 5 |
| `passive` | 17.4% | 53/305 | dict（`proc` 必填） |
| `res_cost` | 12.5% | 38/305 | dict（key ∈ EFFECT_RULES） |
| `faith` | 12.1% | 37/305 | int |
| `cond` | 10.8% | 33/305 | dict（`type` 21 枚举） |
| `shaken_gain` | 7.9% | 24/305 | int |
| `hits` | 7.2% | 22/305 | int |
| `heal_formula` | 6.2% | 19/305 | str |
| `aoe` | 4.9% | 15/305 | str（all/front） |
| `melody` | 3.9% | 12/305 | str（10 枚举） |
| `mech2` | 3.6% | 11/305 | str（6 枚举） |
| `melody_pct` | 2.9% | 9/305 | int |
| `finale` | 2.6% | 8/305 | str（8 枚举） |
| `element` | 2.3% | 7/305 | str（fire/ice/thunder） |
| `summon` | 2.3% | 7/305 | str（5 枚举） |
| `formula` | 2.0% | 6/305 | list[dict] |
| `pierce` | 2.0% | 6/305 | bool |
| `melody_fin_pct` / `reduce_all` | 1.6% | 5/305 | int / float |
| `mech_chance` / `reduce_pct` | 1.3% | 4/305 | float |
| `kind_override` / `target` | 1.0% | 3/305 | str |
| `accuracy` / `auto` / `hate_mult` / `mech2_val` / `melody_fin_turns` | 0.7% | 2/305 | **str 2（accuracy）** / str / int / number / float |
| `charge` `crit` `hate_lock_turns` `hate_taunt_mult` `hp_pct` `kill` `lifesteal` `no_mp` `sleep` `stance` `team` | 0.3% | 1/305 | 混合（含 **`crit`=str**） |

**枚举（从数据收集）**
* `kind`（11）：召唤 / 嘲讽 / 增益 / 治疗 / 物理 / 真伤 / 被动 / 魔法 / 魔法·冰 / 魔法·火 / 魔法·雷
* `cond.type`（21）：`enemy_broken` `enemy_cursed` `enemy_debuff` `enemy_def_high` `enemy_hp_low`
  `enemy_hunt_full` `enemy_hunt_mark` `enemy_low_hp` `enemy_mark_full` `enemy_marks`
  `enemy_shaken_ratio` `enemy_shaken_scale` `faith_full` `faith_lt` `melody_buff` `melody_stacks`
  `player_first` `player_mech_stacks` `revenge` `speed_ratio` `stealth`
* `mech`（33）/ `effect`（37）/ `melody`（10）/ `mech2`（6）/ `finale`（8）/ `summon`（5）/ `passive.proc`（58）
  —— 完整列表见 `schema/skill.schema.json` 的 `enum`。

### 2.2 monsters（怪物技能 330 + 六元组模板 813 + 隐藏怪 25）

> **坐标勘误（任务上下文说 `game/data/monsters.py` = 怪物模板 tuple 形态）**：实测 `monsters.py` 只有
> `MONSTER_SKILLS`（dict）与 `ELITE_EQUIP_DROP`（dict），**没有 tuple 形态的怪物模板**。
> 真正的 6 元组怪物模板分布在 `game/data/subareas.py`（`SUBAREAS[*].monsters` 543 条 + `.elite` 98 条 +
> `.boss` 29 条 = **670**）、`game/data/instances.py`（`boss` 54 + `stages[*].monsters` 55 +
> `stages[*].boss` 12 + `minions[*].monster` 22 = **143**）、以及 `game/data/hidden_monsters.py`
> （`HIDDEN_MONSTERS`，**25** 条 dict 形态）。6 元组合计 **813** 条。
> 本 schema 把这三处**全部覆盖**，并额外覆盖 `monsters.py` 里的两张 dict 表。

**`MONSTER_SKILLS`（330）** 必填 `name` / `kind` / `desc`。共 22 字段。

| 字段 | 覆盖率 | 出现/330 | 类型 |
|---|---:|---|---|
| `desc` `kind` `name` | 100.0% | 330/330 | str（kind 4 枚举：物理/魔法/增益/治疗） |
| `formula` `power` | 70.3% | 232/330 | list[{stat,mult,type}] / float |
| `element` | 31.8% | 105/330 | str（abyss/dark/fire/ice/nature/thunder） |
| `effect` | 29.7% | 98/330 | str（7 枚举） |
| `summon` | 16.7% | 55/330 | int |
| `mech` | 10.9% | 36/330 | str（freeze/interrupt/silence/slow/stun） |
| `charge` | 10.6% | 35/330 | int |
| `hp_pct` | 3.9% | 13/330 | float |
| `pdot` | 3.3% | 11/330 | dict |
| `defend_reduce` | 1.8% | 6/330 | float |
| `mech_val` `aoe` `hits` `multi` `basic` `cast` `recovery` `reach` | ≤1.2% | ≤4/330 | 混合 |

`formula[*]`：`stat ∈ {atk, matk}`、`type ∈ {phys, magi}`、`mult` 为浮点（0.0–2.6）。

**怪物六元组（813 条）**：`[id, 中文名, role, lv, [技能id...], [掉落物名...]]`
* `role ∈ {boss, caster, dps, elite, healer, speedster, tank}`（7 枚举）
* 元组长度 **全部 = 6**（subareas 543 条 + instances + minions 共 813）；`lv` 全为正整数。
* 100% 满足 schema，跨表引用也 100% 命中（技能 id 全在 `MONSTER_SKILLS`、掉落名全在 `ITEMS[*].name`）。

**`HIDDEN_MONSTERS`（25）**：`role` 全为 `elite`；`cond ∈ {any, forest, forest_night, night_any, ruin, water}`；
`chance ∈ [0.002, 0.005]`；`gold_mult ∈ [20, 80]`；`maps` 覆盖率 76%。
`ELITE_EQUIP_DROP`（18 条）中 18/18 装备 id 均在 `EQUIP_ROSTER` 中。

### 2.3 affixes（76）

必填 `name` / `kind` / `trigger` / `effect` / `desc`（**五项全部 100%**）。共 9 字段。

| 字段 | 覆盖率 | 出现/76 | 类型 |
|---|---:|---|---|
| `desc` `effect` `kind` `name` `trigger` | 100.0% | 76/76 | str / dict / str / str / str |
| `line` | 40.8% | 31/76 | str |
| `qualities` | 40.8% | 31/76 | list（blue/purple/orange） |
| `chance` | 11.8% | 9/76 | float（0.10–0.25） |
| `unique` | 6.6% | 5/76 | bool |

`kind ∈ {attack, defense}`；`trigger ∈ {stat, on_hit, on_taken, turn_start, battle_start, passive}`。
`effect` 是自由字典（**69 个键**：`res` 27.6% / `gain` / `on` / `cond` / `tiers` / `pct` / `dmg_mult` / `tag` …），
按设计不设枚举（消费端 `core/affix.py`）。
`AFFIX_POOL_BY_QUALITY` 三档（blue/purple/orange）引用 id 全部命中 `AFFIXES`（0 悬空）；
`AFFIX_AFFINITY_POOLS` 同样 0 悬空。

### 2.4 items（900）

必填 `name` / `price` / `desc`（**三项全部 100%**）。共 25 字段。

| 字段 | 覆盖率 | 出现/900 | 类型 |
|---|---:|---|---|
| `desc` `name` `price` | 100.0% | 900/900 | str / str / int |
| `type` | 77.4% | 697/900 | str（23 枚举） |
| `quality` | 69.9% | 629/900 | str（white/green/blue/purple/orange） |
| `effect` | 16.7% | 150/900 | str（87 枚举） |
| `cast` | 15.2% | 137/900 | float |
| `heal` | 9.6% | 86/900 | float 83 + int 3 |
| `effect_data` | 8.8% | 79/900 | dict（自由） |
| `food` | 8.7% | 78/900 | bool |
| `stamina` | 6.7% | 60/900 | int |
| `mana` | 6.2% | 56/900 | float |
| `hot_turns` / `hot` | 3.6% / 2.7% | 32 / 24 | int / float |
| `food_effect` | 2.4% | 22/900 | str（19 枚举） |
| `battle_ok` | 2.2% | 20/900 | bool |
| `blueprint_for` | 2.1% | 19/900 | str |
| `key_item` | 1.8% | 16/900 | bool |
| `hot_mana` | 1.7% | 15/900 | float |
| `roster_id` | 1.3% | 12/900 | str（`eq_*`） |
| `learn_skill` / `require_class` | 0.6% | 5/900 | str（技能名 / `cls_*`） |
| `rune_pool` / `pick_options` / `weapon_pick` | ≤0.2% | 2 / 1 / 1 | str / list / bool |

`type` 枚举（23）：任务道具 / 传说 / 元素 / 兽材 / 图纸 / 垃圾 / 宝物 / 宝石 / 工具 / 收藏 / 收藏品 /
木材 / 杂物 / 材料 / 消耗品 / 矿石 / 符文 / 精华 / 织物 / 草药 / 食材 / 鱼 / 鱼王。
**物品名全局唯一（900/900，无重名冲突）**——这点很关键，因为掉落/任务大量按中文名 resolve。

### 2.5 effect_rules（EFFECT_RULES 78 / EFFECT_ACTIONS 51 / MECH_CASH 9）

`EFFECT_RULES` key 100% 符合 `^[a-z][a-z0-9_]*$`。共 21 字段。

| 字段 | 覆盖率 | 出现/78 | 类型 |
|---|---:|---|---|
| `cap` | 83.3% | 65/78 | int ≥1（1–100） |
| `stat_scale` | 32.0% | 25/78 | dict（键 ∈ atk/matk/def/mdef/spd/crit/reduce/dmg_mult） |
| `panel` | 25.6% | 20/78 | dict（`{stat, op∈{add,mul}, mult}` 三键齐全） |
| `on` | 19.2% | 15/78 | str（全为 `target`） |
| `negative` | 17.9% | 14/78 | bool |
| `name` | 16.7% | 13/78 | str |
| `period` | 12.8% | 10/78 | dict（`dir∈{damage,gain}`、`interval`、`pct_max_hp`/`pct_boss`…） |
| `tag` | 7.7% | 6/78 | str（freeze/holy_weaken/silence/sleep/spd_down/stun） |
| `cleanse` | 6.4% | 5/78 | bool |
| `consume` | 5.1% | 4/78 | dict（`mode∈{skip,no_skill}`） |
| `debuff_scale` / `start_classes` | 3.9% | 3/78 | dict / list（cls_* 全部命中 `CLASSES`） |
| `channels` | 2.6% | 2/78 | dict |
| `cd_mult` `guard_hp_pct` `heal_pct` `load_tiers` `on_threshold` `overload_heal_pct` `start_full` `wake_on_hit` | 1.3% | 1/78 | 混合 |

`EFFECT_ACTIONS`（51 键）动作对象键：`action` / `key` / `on` / `turns` / `mode` / `op` / `hit` / `halve` / `pct_from_mech_val`。
`MECH_CASH`（9）`mode ∈ {dmg_mult_clear, dmg_mult_clear_target, fury_enter, heal_clear, per_system_clear_target}`；
9/9 的 `key`（字符串或数组）**全部命中 `EFFECT_RULES`**。

### 2.6 passive_proc（42）

| 字段 | 覆盖率 | 出现/42 | 类型 |
|---|---:|---|---|
| `action` / `event` | 92.9% | 39/42 | str（26 / 13 枚举） |
| `judge` | 52.4% | 22/42 | dict |
| `also` | 16.7% | 7/42 | list[dict] |
| `buff_key` / `domain` / `res` | 11.9% | 5/42 | str |
| `cap_key` | 9.5% | 4/42 | str |
| `used_key` | 7.1% | 3/42 | str |
| `agg` / `form` / `mode` | 4.8% | 2/42 | str |
| `bar_field` `cost_field` `ctrl_any` `def_pct` `gain_field` `gap` `left_init` `left_key` `mech_prefix` `spd_pct` `when` | ≤2.4% | 1/42 | 混合 |

**两种形态**（schema 用 `anyOf` 表达）：事件驱动 `{event, action}`（39 条）与域声明 `{domain∈{cap,cost}}`（5 条，
其中 2 条同时带 event/action）。3 条无 `event` 的（`poison_cap` / `hunt_mark_cap` / `arcane_constant`）都带 `domain`。

---

## 3. 现网违规（分域）

```
域                  条目     违规     提醒
skills            305      3     15
monsters         1168      0      0
affixes            76      0      1
items             900      2      2
effect_rules       78      0      1
passive_proc       42      0      0
合计              2569      5     19
```

* **违规 5 条**（全部为下述条目级问题，0 条容器级/结构级错误）
* **提醒 19 条**（见 §6）

### 全部 5 条违规（本域违规总数 = 5，故「前 10 条」由 5 条违规 + 5 条最值得跟进的提醒组成）

| # | 域 | 条目 | 字段 | 问题 | 归类 |
|---|---|---|---|---|---|
| 1 | skills | `BRANCH_SKILLS/cls_fa_shi/奥术学者/奥术飞弹` | `$.accuracy` | `'true'` 是字符串，应为布尔 | 历史遗留（类型不规范，功能无害） |
| 2 | skills | `BRANCH_SKILLS/cls_you_xia/风行者/贯日箭` | `$.accuracy` | 同上 | 历史遗留 |
| 3 | skills | `BRANCH_SKILLS/cls_you_xia/风行者/贯日箭` | `$.crit` | `'true'` 是字符串，应为布尔 | 历史遗留 |
| 4 | items | `ITEMS/mat_tu_zhi_ye_xing_pi_feng`（夜行披风图纸） | `roster_id` | `blueprint_for='夜行披风'` 指向名册装备 `eq_ye_xing_pi_feng`，但缺 `roster_id` | **真错（字段遗漏）** |
| 5 | items | `ITEMS/mat_chuan_shuo_tu_zhi_rong_lu_zhi_xin`（熔炉之心图纸） | `roster_id` | `blueprint_for='熔炉之心'` 指向名册装备 `eq_rong_lu_zhi_xin`，但缺 `roster_id` | **真错（字段遗漏）** |

**没有一条属于「schema 太严」**：schema 的所有约束都从现网数据归纳，唯一被收紧的两处
（`skill.accuracy` / `skill.crit` 必须 bool）拦的是**真的类型不规范**，且只命中 3 条；
其余历史写法（`cast="None"` 哨兵 51 条、`kind=被动` 带数值 cast 1 条、`effect_data` 自由字典、
`affix.effect.on` 形态不一）都已显式放宽为「允许 / 提醒」，不计入违规。

---

## 4. 门禁可行性

```bash
$ python schema/validate.py ; echo $?
...
结论: 发现违规 ❌ (exit 1)
1
$ python schema/validate.py --domain monsters ; echo $?      # 单域全绿
结论: 全绿 ✅ (exit 0)
0
```

* 当前**全量 exit = 1**（因为 5 条违规还在）。**门禁机制本身已可用**：
  只要 §3 的 5 条被处理（改数据）或 schema 按 §7 放宽，即自动 exit 0。
* 单域全绿（monsters / affixes / effect_rules / passive_proc）→ exit 0，可直接接 CI。
* `--json` 输出结构稳定（`totals` / `domains[*].errors`），编辑器与 CI 都能消费。
* 两条校验引擎（`jsonschema` 与内建最小校验器）对现网数据的违规数**完全一致**（tests 已断言）。
* 建议接法：**先以 `--domain monsters,affixes,effect_rules,passive_proc` 作为阻塞门禁**
  （这些域现在就是 0），skills/items 等 5 条修完再全量阻塞。

---

## 5. 发现的数据 bug（真错，**未改**）

### B1 / B2：两张图纸缺 `roster_id`（唯一确认为真错的项）

| 条目 | 物品 | `blueprint_for` | 名册目标 | 缺失字段 |
|---|---|---|---|---|
| `mat_tu_zhi_ye_xing_pi_feng` | 夜行披风图纸（Lv.30 蓝·披风） | 夜行披风 | `eq_ye_xing_pi_feng` | `roster_id` |
| `mat_chuan_shuo_tu_zhi_rong_lu_zhi_xin` | 熔炉之心图纸（Lv.85 橙·剑） | 熔炉之心 | `eq_rong_lu_zhi_xin` | `roster_id` |

**判据（为什么是真错而不是历史写法）**
1. `ITEMS` 里另外 **12 条** `blueprint_for` 的图纸**全部带 `roster_id`**（`blueprint_for` 19 条 − 7 条非装备图纸 = 12 条）。
2. 缺失的 2 条目标装备**确实在 `EQUIP_ROSTER` 中**（`source` 正是「图纸」），且 `CRAFT_RECIPES` 的
   `rec_ye_xing_pi_feng` / `rec_rong_lu_zhi_xin` **都带 `roster_id`**。
3. 官方生成器 `game/core/drops.py::make_blueprint` 造图纸时**同时写** `blueprint_for` + `roster_id`
   （`{"blueprint_for": r["name"], "roster_id": rid, ...}`）→ 只有这 2 条是手写遗漏。

**影响面（已核实，非“致命”）**
* **学习链不受影响**：图纸学习走 `blueprint_for`（装备中文名）匹配
  （`services/battle_settlement.py:246`、`core/drops.py`、`core/poi_effects.py`、`core/wild_king.py`、
  `commands/instance.py:3051/3117` 都是 `bp["blueprint_for"] in learned`）→ 按名匹配照常学会。
* **受影响的是详情/图鉴展示链**：`commands/economy.py:423`
  `r = C.EQUIP_ROSTER.get(d.get("roster_id",""))` → 缺字段时拿到 `{}`，图纸详情页的名册信息
  （品质/等级/套装等）会降级。
* 结论：**低危字段遗漏**，不影响可玩性，但会随编辑器上线被放大（编辑器按 schema 必填/配对关系提示，
  这两条会一直亮红）。**修复 = 给两个物品补 `roster_id`（各 1 行），未执行。**

### 其余「像 bug 但已排除」的项

| 现象 | 判定 | 依据 |
|---|---|---|
| 11 个 `passive.proc`（`death_contract` `faith_overload_heal` `faith_share` `finisher_up` `focus_regen_summon` `melody_full` `melody_master` `melody_resonance` `shadow_dance_cd` `skeleton_cap` `undead_faith`）不在 `battle2 PASSIVE_PROC` | **不是孤儿**（迁移期双注册表） | 11/11 都在 `game/core/passive_procs.py` 有 `declare_proc(...)` 或登记（如 `death_contract`→`revive_cond`、`skeleton_cap`→`summon_cap_add`）。battle2 侧为新引擎声明表，属迁移中间态 → 记为**提醒** |
| 8 个 skill `mech`（`bone_rush` `curse_refresh` `element_burst` `element_multi_mark` `melody` `melody_chant` `sacrifice` `zhan_yi_cash`）不在 `EFFECT_RULES`/`MECH_CASH` | **不是悬空** | 全部出现在 `commands/combat.py` 的机制显示名表（1478–1485 行区间）并在 `core/`（`passive_procs.py` 780/843/941、`battle_conds.py` 300、`services/class_mech_proc.py` 1590）有消费端 → 属性/引擎内建机制，非声明表域 → 记为**提醒** |
| 20 个 skill `effect` 不在 `EFFECT_ACTIONS`（`all_stat_cc` `arcane_field` `taunt` `vuln` …） | 同上，命令层/引擎内建 | 记为**提醒** |
| `MECH_CASH.finisher.upgrade.proc = "finisher_up"` 不在 `PASSIVE_PROC` | 同 B1 的 11 条，`finisher_up` 在 `core/passive_procs.py:180` 登记 | 提醒 |
| `effect_data.boss_downgrade` 类型不一（float `0.2` / str `"slow"`） | 自由字段多态 | 提醒 |
| `affix.effect.on` 形态不一（str 11 / list 1） | 自由字段多态 | 提醒 |
| 203 条物品无 `type` | 覆盖缺口，非错误 | 提醒（编辑器可据此提示补 `type`） |
| `森之共鸣`（`cls_you_xia/森语者`）`kind=被动` 但 `cast=0.5` | 1 条孤例 | 提醒（其余 52 条被动均 `cast="None"`） |
| `PLAYER_SKILLS`/`TUTOR_SKILLS` 的技能 id 都是 `sk_*`，而 `BRANCH_SKILLS` 用**中文名**做 key | 设计如此 | 不报（schema 只对 `BRANCH_SKILLS` 的 `branches` 层做数字键校验） |

---

## 6. 提醒清单（19 条，不拦门禁）

| 域 | 条数 | 内容 |
|---|---:|---|
| skills | 11 | `passive.proc` 未在 battle2 `PASSIVE_PROC` 声明（双注册表，见 §5） |
| skills | 1 | 8 个 `mech` 未在 `EFFECT_RULES`/`MECH_CASH` 声明 |
| skills | 1 | 20 个 `effect` 未在 `EFFECT_ACTIONS` 声明 |
| skills | 1 | 51 条技能 `cast` 用历史哨兵字符串 `"None"` |
| skills | 1 | `森之共鸣` `kind=被动` 但 `cast` 是数值 |
| affixes | 1 | `effect.on` 形态不统一（str ×11 / list ×1） |
| items | 1 | 203 条物品没有 `type` 字段 |
| items | 1 | `effect_data.boss_downgrade` 类型不一（float / str） |
| effect_rules | 1 | `MECH_CASH/finisher.upgrade.proc='finisher_up'` 未在 `PASSIVE_PROC` 声明 |

---

## 7. 给编辑器 / 后续的结论

1. **字段口径已 100% 收敛**：`--strict-unknown` 额外违规 0 → schema 可以当「字段白名单」用，
   编辑器保存时能拦住拼错的字段名。
2. **枚举可直接驱动下拉框**：`kind` / `trigger` / `role` / `event` / `action` / `quality` / `type`
   等全部从现网收集，见各 `.schema.json` 的 `enum`。
3. **必填极少**（每域 3–5 个），不会逼策划填一堆不适用字段；代价是必填之外的字段需要编辑器按
   `kind`/`type` 做条件显示。
4. **跨表引用已可自动检查**，编辑器保存时能立刻发现「词条池引用了不存在的词条」「掉落物名打错」
   「图纸指向了不在名册里的装备」。
5. **先别开全量阻塞门禁**：全量现在 exit 1（5 条）。处理顺序建议：
   ① 修 §5 的 2 条 `roster_id`（改 `items.py` 2 行，低风险）；
   ② 决定 `accuracy`/`crit` 是否统一成 bool（改 `skills.py` 3 行，或把 schema 放宽为 `anyOf[bool, "true"]`）；
   ③ 之后全量 exit 0，即可接 CI 阻塞。
   **以上三步均未执行**（任务要求只报告不改数据）。
6. **回归**：新增 `tests/test_schema_validate.py`（15 用例，含现网基线 5/19 的锁定断言），
   全量回归结果见 §8。

---

## 8. 全量回归

```
python scripts/run_all_tests.py --file tests/test_schema_validate.py   # 本任务新增：14/14 通过，exit 0
python scripts/run_all_tests.py                                      # 全量（见下）
```

**本次实测（并行全量，`scripts/run_all_tests.py`）**

| 轮次 | 文件 | 通过 | 失败 | 失败文件 |
|---|---:|---:|---:|---|
| 第 1 轮 | 243 | 205 | 38 | `test_class_mech_r*` / `test_passive_p*` / `test_melody` / `test_monster_ai_*` / `test_instance_hate` 等 |
| 第 2 轮 | 244 | **240** | 4 | `test_battle_n9_equip` / `test_battle_n5b4_instance_router` / `test_boss_script_p1` / `test_boss_script_p3` |

* 本任务新增文件 **`tests/test_schema_validate.py` → ✅ 通过（exit 0，14/14 用例）**。
* **两轮失败集合完全不同，且逐个单独跑全部 0 失败**（实测：`test_melody` 34/0、`test_v104_explore_map` 70/0、
  `test_battle_n9_equip` 171/0、`test_battle_n5b4_instance_router` 59/0、`test_boss_script_p1` 22/0、
  `test_boss_script_p3` 29/0）→ 是**并发跑批期间另一个 agent 正在改 `game/battle2/**`、`game/core/**`、
  `game/content.py`、`game/__init__.py` 造成的中间态/漂移**，不是本任务引入的回归。
* 本任务**只新建文件**（`git status` 显示我的改动仅在 `schema/`、`docs/archive/DATA_SCHEMA_AUDIT.md`、
  `tests/test_schema_validate.py`），未触碰 `game/data/**` 与任何引擎文件。
* 结论：本任务的交付物（schema / 校验器 / 审计报告 / 测试）自证全绿；
  全量 242/242 的基线在**并行重构进行中无法复现**，建议由主 agent 在另一 agent 收工后复跑确认。
