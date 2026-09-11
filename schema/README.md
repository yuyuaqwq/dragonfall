# dragonfall 数据域 Schema（配置编辑器前置 · 路线图 2.1）

给策划 / 第三方配内容（不写代码）的**可视化配置编辑器**提供稳定契约：
先有 schema（能校验）→ 再有读写接口 → 最后才是 UI。

本目录 **只读 game/data/**，不 import 引擎（`game/core/`、`game/battle2/` 在并行重构）。
所有枚举、字段、必填判定都是从**现网真实数据**归纳出来的，不是凭空设计。

---

## 1. 文件清单

| 文件 | 域 | 主 schema（`x-primary`） | 覆盖的表 |
|---|---|---|---|
| `skill.schema.json` | 技能 | `skill` | `PLAYER_SKILLS` / `BRANCH_SKILLS` / `TUTOR_SKILLS`（`game/data/skills.py`） |
| `monster.schema.json` | 怪物 | `monster_skill` | `MONSTER_SKILLS`、`ELITE_EQUIP_DROP`（`game/data/monsters.py`）；怪物六元组（`subareas.py` / `instances.py`）；`HIDDEN_MONSTERS` |
| `affix.schema.json` | 词条 | `affix` | `AFFIXES` / `AFFIX_POOL_BY_QUALITY` / `AFFIX_KIND` / `AFFIX_AFFINITY_POOLS`（`game/data/affixes.py`） |
| `item.schema.json` | 物品 | `item` | `ITEMS`（`game/data/items.py`） |
| `effect_rules.schema.json` | 声明表 | `effect_rule` | `EFFECT_RULES` / `EFFECT_ACTIONS` / `MECH_CASH`（`game/data/battle_rules.py`） |
| `passive_proc.schema.json` | 被动声明 | `passive_proc` | `PASSIVE_PROC`（`game/data/battle_rules.py`） |
| `validate.py` | 校验器 + CLI | — | 全 6 域 + 跨表引用完整性 |
| `../docs/DATA_SCHEMA_AUDIT.md` | 脏数据审计报告 | — | 覆盖率 / 违规清单 / 结论 |

> ⚠️ `game/data/battle_rules.py` 正被另一个 agent 重构（行号会漂移）。本目录 schema 只依赖
> **表结构**（key→规则字典），不引用任何行号；若该文件新增状态 key，见 §6 维护规则。

---

## 2. 怎么跑

```bash
# 全量校验（门禁：有违规 exit 1，全绿 exit 0）
"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe" schema/validate.py

# 单域
... schema/validate.py --domain skills

# 机器可读（推荐给编辑器 / CI）
... schema/validate.py --json

# 只打印汇总
... schema/validate.py --quiet

# 把「未在 schema 声明的字段」也算违规（严格档；现网为 0 条，默认不算违规）
... schema/validate.py --strict-unknown
```

Python API：

```python
import importlib.util, os
spec = importlib.util.spec_from_file_location("v", "schema/validate.py")
V = importlib.util.module_from_spec(spec); spec.loader.exec_module(V)

res = V.validate_all()                 # 全量
res["totals"]      # {'entries': 2569, 'errors': 5, 'warnings': 19}
res["domains"]["items"]["errors"]      # 逐条违规
res["domains"]["items"]["field_coverage"]  # 字段覆盖率（presence / cover / types）
V.validate_all(domain="items")         # 单域
```

### 门禁语义

* **违规（errors）** → 计入 exit code。分成两类：
  1. **schema 层**：类型 / 必填 / 枚举 / 数值范围 / key 形态。
  2. **跨表引用（闭合集）**：词条池 → 词条 id、怪物技能 → `MONSTER_SKILLS`、
     掉落物名 → `ITEMS` 名、`MECH_CASH.key` → `EFFECT_RULES`、`start_classes` → `CLASSES`、
     名册图纸 → `EQUIP_ROSTER` 的 `roster_id` 配对。
* **提醒（warnings）** → 只进报告，**不拦门禁**。用于需要人判断的迁移期现象
  （例：被动 proc 在 `saintess_engine PASIVE_PROC` 与 `core/passive_procs` 双注册表并存）。

### 两个校验引擎

优先第三方 `jsonschema`（draft 2020-12）；不可用时自动退化为内置最小校验器
（`validate.py::_min_validate`，支持本仓 schema 用到的关键字子集）。
两条路径对现网数据的判定一致，`tests/test_schema_validate.py` 会断言这一点。
`res["engine"]` 告诉你这次用的是哪一个。

---

## 3. Schema 约定（编辑器怎么读）

1. **每个文件的根是「容器 + `$defs`」**：根节点只放 `$schema` / `$id` / `title` / `$defs` /
   `x-primary`，**真正的 schema 都在 `$defs` 里**。`x-primary` 指向「一条内容条目」的 def
   （编辑器表单应绑定这个）。
2. **「条目」和「整表」分开**：
   * 条目级（`skill` / `item` / `affix` / `monster_skill` / `monster_template` /
     `hidden_monster` / `effect_rule` / `passive_proc`）= 一条数据的全部字段约束。
   * 整表级（`*_table` / `player_skills` / `branch_skills` / `tutor_skills` /
     `affix_pool_by_quality` / `affix_kind` / `elite_equip_drop` / `effect_actions` /
     `mech_cash`）= 只查 key 形态与表结构，**不重复校验条目本体**（避免同一错误报两遍）。
3. **`required` 只列「现网 100% 出现」的字段**，其余一律可选。
   现状是大量字段按技能/物品类型可选（例如 `cd` 只有 80% 技能有），
   把可选项设成 required 会让历史数据全报错 —— 门禁就失去意义。
4. **`additionalProperties: true` 是默认**：新增字段不会让旧数据失败；
   想抓「拼错字段名」用 `--strict-unknown`（现网覆盖率已达 100%，见 §5）。
5. **历史哨兵被显式承认**，不当违规：
   * `skill.cast` 允许数字**或**字符串 `"None"`（51 条被动/瞬发技沿用旧写法）。
   * `skills` 里 `kind=被动` 但 `cast` 是数值的 1 条（森之共鸣）只报提醒。
   * `items.effect_data` / `affix.effect` 是自由字典（值类型随消费端而定），
     只对「同一个键在不同条目里类型不一」报提醒。
6. **枚举 = 现网出现过的取值集合**。它们同时充当「拼写门禁」：写错 `kind` / `trigger` /
   `role` / `event` 会被立刻拦下。代价是**新增取值必须同步 schema**（见 §6）。
7. **每个主 def 都配 `examples`**（现网真实形态的样本，可直接当编辑器空表单的「示例填充」）。
   examples 自身也必须通过 schema —— `tests/test_schema_validate.py` 会断言这一点
   （共 19 条示例，覆盖 13 个 def）。

---

## 4. 各域字段摘要

### skills（305 条：61 player + 238 branch + 6 tutor）

必填 `name` / `kind` / `lv` / `desc`；`power` 现网 100%。
高频：`mp` 97.4%、`cast` 98.0%、`cd` 80.0%、`exprs` 47.5%、`mech` 26.6%、`effect` 19.7%、
`passive` 17.4%、`res_cost` 12.5%、`cond` 10.8%。

* `kind` 枚举（11 个）：召唤 / 嘲讽 / 增益 / 治疗 / 物理 / 真伤 / 被动 / 魔法 / 魔法·冰 / 魔法·火 / 魔法·雷
* `exprs` = 伤害表达式字符串数组（`'atk*1.3 + 20 + player_lv*7.0 + skill_lv*16'`）；纯函数式，无 lambda。
* `mech` / `effect` = 机制与效果键（33 / 37 个），消费端见 `effect_rules` 与引擎。
* `cond` = 触发条件，`cond.type` 21 个枚举（`player_mech_stacks` / `enemy_broken` / …）。
* `passive` = 被动声明，`passive.proc` 指向被动处理器 id（58 个）。
* `res_cost` = 资源消费 `{状态key: 数量}`，key 必须是 `EFFECT_RULES` 已声明的状态。
* **`BRANCH_SKILLS` 的键是中文技能名**（如 `"怒斩"`），不是 `sk_*`；编辑器做 id 生成时注意。
* 元字段（`_cls` / `_scope` / `_branch` / `_branch_lv`）**是校验器注入的标签**，不在数据里、不在 schema 里。

### monsters（330 怪物技能 + 813 六元组 + 25 隐藏怪）

* **怪物技能** `MONSTER_SKILLS`：必填 `name` / `kind` / `desc`；`formula` 70.3%（`[{stat,mult,type}]`，
  `stat∈{atk,matk}`、`type∈{phys,magi}`）、`element` 31.8%、`effect` 29.7%、`summon` 16.7%、`mech` 10.9%。
* **怪物模板**是 **6 元组** `[id, 中文名, role, lv, [技能id...], [掉落物名...]]`，
  `role∈{boss,caster,dps,elite,healer,speedster,tank}`。来源：`SUBAREAS[*].monsters/elite/boss`、
  `INSTANCES[*].boss/stages[*].monsters|boss`、`INSTANCES[*].minions[*].monster`。
  注意 **`drops` 写的是物品中文名**（不是 id），校验器按 `ITEMS[*].name` 反查。
* **隐藏怪** `HIDDEN_MONSTERS`：`lv_off` 是相对等级偏移；`cond∈{any,forest,forest_night,night_any,ruin,water}`；
  `chance` ∈ (0,1)。
* `ELITE_EQUIP_DROP`：`{精英中文名: 名册装备 id}`，id 必须 `eq_*` 且在 `EQUIP_ROSTER` 中。

### affixes（76 条）

必填 `name` / `kind` / `trigger` / `effect` / `desc`（**全部 100%**）。
`kind∈{attack,defense}`；`trigger∈{stat,on_hit,on_taken,turn_start,battle_start,passive}`；
`chance` 11.8%（缺省即恒触发）；`qualities` 40.8%（值 ∈ {blue,purple,orange}）；`unique` 6.6%。
`effect` 是自由字典（69 个键：`res`/`gain`/`on`/`tiers`/`pct`/`dmg_mult`/`tag`…），
**不设枚举**（消费端 = `core/affix.py`）。

### items（900 条）

必填 `name` / `price` / `desc`（100%）。`type` 77.4%（23 个枚举：兽材/杂物/消耗品/任务道具/精华/矿石/图纸/…）、
`quality` 69.9%（`white/green/blue/purple/orange`）、`effect` 16.7%（87 个枚举）、`effect_data` 8.8%、
`food` 8.7%、`stamina` 6.7%、`blueprint_for` 2.1%、`roster_id` 1.3%。
`roster_id` 必须 `eq_*` 形态；`blueprint_for` 与 `roster_id` 是配对字段（见审计 §5 的 2 条真错）。
`pick_options[*]` = 自选礼包选项（`{name,rid,desc}`）。

### effect_rules（EFFECT_RULES 78 / EFFECT_ACTIONS 51 / MECH_CASH 9）

* `EFFECT_RULES[key]`：key 必须 `^[a-z][a-z0-9_]*$`。字段：`cap` 83.3%（整数 ≥1）、
  `stat_scale` 32.0%（每层属性加成 `{atk:0.04}`，键 ∈ `{atk,matk,def,mdef,spd,crit,reduce,dmg_mult}`）、
  `panel` 25.6%（`{stat,op∈{add,mul},mult}`）、`period` 12.8%（DOT/回血：`dir∈{damage,gain}`、`interval`、
  `pct_max_hp`/`pct_boss`/…）、`consume` 5.1%（`mode∈{skip,no_skill}`）、`on` 19.2%（`target`）、
  `negative`/`cleanse` bool、`tag` 7.7%（6 个控制类枚举）、`start_classes`（职业 id）、
  `on_threshold`（key 是数字字符串）、`channels` / `load_tiers` / `debuff_scale` 自由字典。
* `EFFECT_ACTIONS`：`{效果键: [动作对象...]}`，动作必填 `action`，可选 `key/on/turns/mode/op/hit/halve/pct_from_mech_val`。
* `MECH_CASH`：必填 `name` / `mode∈{dmg_mult_clear,dmg_mult_clear_target,fury_enter,heal_clear,per_system_clear_target}`；
  `key` 可以是字符串或字符串数组，且**每个都必须存在于 `EFFECT_RULES`**。

### passive_proc（42 条）

**两种形态**（schema 用 `anyOf` 表达）：

* 事件驱动：`{event, action, judge?, also?}` —— `event` 13 个枚举（`dmg_calc`/`taken_calc`/`turn_start`/`skill_hit`/…），
  `action` 26 个枚举（`passive_dmg_mult`/`passive_taken_reduce`/…）。
* 域声明：`{domain∈{cap,cost}, cap_key?/cost_field?, ...}` —— 不挂事件，改的是上限/消耗口径。

`judge` 是自由字典（判定子句：`kind`/`mech`/`res`/`ge_field`/`bar`/`mark`/…）。

---

## 5. 现网现状（2026-09-11）

* 条目总数 **2569**；违规 **5**；提醒 **19**；`--strict-unknown` 额外违规 **0**
  （即：**schema 声明的字段集合 = 现网实际用到的字段集合，零遗漏零多余**）。
* 逐条清单与归类（真错 / schema 太严 / 历史遗留）见 `../docs/DATA_SCHEMA_AUDIT.md`。

---

## 6. 维护规则（加东西时照这个来）

**改数据的数值 → 不用动本目录。** 只有下面几种情况才动 schema：

| 场景 | 要做的事 |
|---|---|
| 新增一个枚举取值（如新 `kind`=「召唤·兽」、新 `trigger`、新 `role`） | ① 在对应 `.schema.json` 的 `enum` 里加；② 跑 `validate.py`；③ 若违规数变化，同步 `tests/test_schema_validate.py` 的 `BASELINE_*`；④ 更新 README §4 与审计报告 §3。 |
| 新增一个字段 | ① 加进 `.schema.json` 对应条目的 `properties`（类型 + 范围/枚举）；② `--strict-unknown` 必须仍为 0；③ 审计报告 §2 覆盖率表更新。 |
| 新增一个域（如 `quest` / `npc`） | ① 新建 `schema/<x>.schema.json`（沿用 `$defs` + `x-primary` 约定）；② 在 `validate.py` 的 `ALL_DOMAINS` 与 `_run_domain` 加分支；③ 在 `tests/test_schema_validate.py` 的 `SCHEMA_FILES` / `BASELINE_*` 登记；④ 更新本 README 表格。 |
| 发现 schema 太严（历史数据大面积报错） | **先停下来报告，别改数据**。正确做法是放宽 schema（把字段改可选 / 加 `anyOf`），并在审计报告里归类为「schema 太严」，同时记录放宽理由。 |
| `battle_rules.py` 被重构后状态 key 变了 | 本目录不引用行号，只要表结构（key→规则）不变就无需改动；`MECH_CASH.key` 的引用检查会自动把悬空 key 报成违规。 |

**铁律**：schema 与数据冲突时，默认怀疑数据（真错）；只有当冲突面很大且明显是历史写法时，
才放宽 schema —— 并且必须留下文字理由。

---

## 7. 与编辑器的接口约定（下一步）

1. 编辑器读某张表 → 用 `*_table` schema 校验整表，用 `x-primary` schema 渲染单条表单。
2. 枚举下拉框 = 对应字段的 `enum`（直接读 schema，不要在前端硬编码）。
3. 保存前调 `validate_all()`（或 `validate_all(domain=...)`），`errors` 非空就阻断保存并高亮
   `entry` + `field` + `problem`（字段路径已在 `errors[*].field` 给出，可直接定位表单控件）。
4. `warnings` 只做黄条提示。
5. 必填项 = schema `required`（很少，别在前端另立标准）。
