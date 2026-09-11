# 引擎 / 内容物理分离方案（阶段一 1.2）

> 仓库：`C:\Users\yuyu\qqbot\data\plugins\dragonfall`
> 侦察方式：**只读**。纯 Python（`os.walk` + `ast` + `re` + `tokenize`）静态分析，未跑任何改文件脚本，未 git add/commit。
> 基线：`git rev-parse HEAD = 780720b`（`feat(v181): 磐核线（G2）+ 挽歌者减益旋律批（G1）并行落地`），工作树干净。
> 回归口径：「241 绿」= `tests/test_*.py` 共 **241** 个文件全绿（`scripts/run_all_tests.py` 逐文件子进程跑，计数即文件数）。
> 目标形态：`framework-engine/`（独立可分发 git 仓库）+ `dragonfall/engine/`（submodule）+ `dragonfall/content/`。

---

## 章节大纲

1. 侦察范围与方法
2. 现状目录清单与三层分类（引擎 / 内容 / 灰色）
3. import 依赖矩阵（双向边 + hub 表）
4. ★ 反向依赖结论（引擎 → 内容，逐条列边）
5. 引擎内游戏知识残留扫描（110 命中，22 不合规 / 88 合规）
6. 对外 API 面盘点（内容 → 引擎 25 符号）
7. 目录拆分方案（engine/ 逐文件 · content/ 逐文件 · 灰色归属 · apply_game_content 收敛）
8. 迁移步骤（9 步，分批可回滚，每步验证 241 绿）
9. 风险清单（12 条）
10. 结论

---

## 1. 侦察范围与方法

| 项 | 值 |
|---|---|
| 扫描根 | `game/`（含全部子包） |
| `.py` 文件数 | **218** |
| 代码总行数 | ≈ 135 900 行 |
| AST 解析失败 | 0（218/218 全部可解析） |
| 动态 import 命中 | 5 处（`importlib.import_module` ×3、`__import__` ×2，均非游戏路径穿透） |
| 引擎候选包 | `game/battle2/`（13 文件 / 3 572 行） |

**方法**：`ast.parse` 提取每条 `Import` / `ImportFrom` 的 `(module, level, alias, lineno)`，相对导入按包名解析成绝对模块名；再按顶层子包分组统计 `source_group -> target_group` 边；中文/游戏词/表名/职业 id 用 `tokenize` 区分「字符串字面量 / 注释 / docstring」后分类计数。

**体量分布（分组）**

| 分组 | py 文件 | 行数 | 定位 |
|---|---:|---:|---|
| `game/battle2/` | 13 | 3 572 | **引擎**（零游戏知识，已重构） |
| `game/core/` | 55 | 14 182 | **灰色**（通用执行器 + 注册表 + 解释器，但含游戏名词与表读点） |
| `game/data/` | 86 | 74 575 | 内容（纯静态表） |
| `game/services/` | 22 | 10 821 | 内容（装配层 + 业务服务） |
| `game/commands/` | 24 | 27 165 | 内容（AstrBot 命令层） |
| `game/store/` | 12 | 3 571 | 内容（SQLite 持久化，零引擎依赖） |
| `game/*`（顶层 5 模块） | 5 | ≈ 2 040 | 见 §2 |

**注**：`game/` 目录内另有 `game_data.db` 及 4 个 `.bak_*`、`game/data/t2i_templates/`（HTML 模板）——均被 `.gitignore` 覆盖，不参与分离。

---

## 2. 现状目录清单与三层分类

### 2.1 引擎（通用，零游戏知识）

| 模块 | 行数 | 说明 |
|---|---:|---|
| `battle2/actors.py` | 9 733B | Actor 模型/工厂 + Sides 容器 + ActCtx + 序列化 |
| `battle2/battle.py` | 25 577B | Battle 主类（构造、act/human_act/actor_auto、结果判定） |
| `battle2/actions.py` | 38 607B | 行动结算链（`_do_skill`/`_do_attack`/`_deal_hit`/`_damage_actor`） |
| `battle2/effects.py` | 27 078B | 效果系统（EFFECT_HANDLERS 单表 + handler 注册） |
| `battle2/effect_triggers.py` | 7 369B | 事件总线 `fire()` + 钩子注册 |
| `battle2/landing.py` | 19 251B | 伤害落地链（闪避/格挡/护盾/免伤/免疫/元素） |
| `battle2/schedule.py` | 19 033B | CTB 时间轴 / 事件队列 / tick |
| `battle2/serialize.py` | 4 562B | `to_state`/`from_state`（sides-only） |
| `battle2/stats.py` | 6 392B | 面板计算（薄封装 `game.engine` 数值函数） |
| `battle2/state_effects.py` | 1 082B | 规则查表门面（`state_def`） |
| `battle2/config.py` | 2 293B | 配置挂载点（`set_config`/`load_game_rules`） |
| `battle2/ai.py` | 7 606B | 怪物 AI（actor_auto） |
| `battle2/__init__.py` | 994B | 公开导出（当前仅 4 符号） |

**引擎可复用的 core 模块（零游戏表读，建议随引擎走）**

| 模块 | 行数 | 复用方数 | 判定 |
|---|---:|---:|---|
| `core/formula_expr.py` | 255 | 3（battle2.actions / commands.player / engine.py） | **引擎**（安全表达式解释器，纯数学） |
| `core/formation.py` | 241 | 3（commands.combat/instance/world） | **引擎**（站位/射程纯函数，`MAX_RANKS` 等参数化） |
| `core/skill_kinds.py` | 119 | 4（commands.combat/instance/instance_router + engine.py） | **引擎（需改）**：类型域枚举值当前写死中文 `物理/魔法/真伤…`，必须改为配置注入 |
| `core/tick_effects.py` | 60 | **0** | **灰色**：通用 tick 框架，但当前无人消费（battle2 用 `schedule.py` 自带 tick） |
| `core/battle_bars.py` | 336 | 4（commands.combat + 3 个 services） | **灰色偏引擎**：纯函数「挂敌身条 + 蓄力三律」，零职业特判；但延迟 `import MECH_CFG` + 键名读 `battle_rules.BAR_STATE_PREFIX` |

### 2.2 内容（奥兰迪亚专属）

- **`game/data/`（86 文件，74 575 行）**：`skills.py`(193KB)、`monsters.py`(83KB)、`instances.py`(147KB)、`items.py`(207KB)、`affixes.py`(87KB)、`equip_roster.py`(206KB)、`quests.py`(245KB)、`subareas.py`(409KB)、`npcs.py`(181KB)、`dialogues.py`(510KB)、`battle_rules.py`(58KB)… 纯静态表。
  例外：`data/_assembly.py`(14KB) 与 `data/__init__.py`(16KB) 含装配逻辑（`build_index`/派生表），是「内容侧装配入口」。
- **`game/services/`（22 文件）**：`class_mech_proc.py`(115KB)、`battle_we_procs.py`(70KB)、`battle_equip_proc.py`(59KB)、`battle_bridge.py`(19KB)、`battle_bar_procs.py`、`battle_cond_procs.py`、`battle_food_proc.py`、`battle_settlement.py`… = **机制动作注册模块 + 引擎适配桥**。
- **`game/commands/`（24 文件）**：`economy.py`(404KB)、`world.py`(257KB)、`instance.py`(192KB)、`combat.py`(189KB)… = AstrBot 命令层。
- **`game/store/`（12 文件）**：SQLite 持久化，**零 battle2 依赖**（import 边 battle2=0），拆包时风险最低。
- **顶层**：`content.py`(12 行，`data *` + `core *` 薄聚合，保留 `import game.content as C` 兼容路径)、`db.py`(9 行，模块级读 `DB_PATH`)、`drop_engine.py`(591 行)、`reward.py`(216 行)。

### 2.3 灰色地带（重点标记）

| 模块 | 行数 | 为什么灰 | 建议首归 |
|---|---:|---|---|
| **`game/engine.py`** | 1 212 | 名字叫引擎，实际**重度读内容表**：`C.PCT_CAPS`×17、`C.resolve`×12、`C.PCT_STATS`×5、`C.SET_ITEMS/SKILL_UP/ITEMS/RACES/CLASSES/PLAYER_SKILLS/BRANCH_SKILLS/TUTOR_SKILLS`… 同时对外提供 battle2 依赖的**通用数值公式**（`calc_damage`/`resolve_formula`/`skill_*`）。**必须一拆为二** | 内容（`content/rules/`）+ 公式入引擎 |
| **`core/stat_bonus.py`** | 227 | 「外部面板增幅聚合器」设计上是通用的，但实读 `TITLES/ACHIEVEMENTS` 表 + 直连 SQLite（`sqlite3.connect(db.DB_PATH)`），复用方 8 个 | **内容**（`content/core/`） |
| **`core/timed_events.py`** | 218 | 「通用倒计时事件引擎」，零 data import，但持久化落 `event_state` 表（游戏 DB）；引擎与 battle2 均不消费 | **内容**（后续可抽为带 storage 接口的引擎组件） |
| **`core/battle_bars.py`** | 336 | 纯函数 + 数据驱动铁律（无 `class_name` 字符串比较），但读 `MECH_CFG`（`importlib` 延迟导入）与 `BAR_STATE_PREFIX` 键名 | **引擎**（迁 `engine/support/bars.py`，读点改 `config`） |
| **`core/passive_procs.py`** | 1 610 | P2D 建的被动 proc 注册表（53 proc 白名单 + 机制族 handler + `validate_proc_coverage()`）。**⚠️ 本行结论已过期（原文写于 2026-09-11 门禁建立之前）**：**不是孤儿** —— `tests/test_passive_proc_coverage.py` 在跑它，守着「声明集全部有归属 / 族⊆白名单 / 族∩缺口=∅ / 缺口集合钉死」四条不变式；另有 `schema/validate.py` 消息引用 | **内容**（**保留，勿归档**） |
| **`core/battle_conds.py`** | 537 | 条件注册表，消灭 if-elif 硬编码；但注册项含游戏 token（`melody_*`/`enemy_shaken_*`/`guard_core`） | **内容**（`content/core/`） |
| **`core/battle_modes.py`** | 458 | 形态/双形态框架，读 `battle_rules` | 内容 |
| **`core/potion_effects.py`** | 720 | 药水效果注册，读 `battle_rules`+`items` | 内容 |
| **`core/item_templates.py`** | 1 232 | 物品模板生成，读 content/engine | 内容 |
| **`core/effect_actions.py`** | 187 | 效果动作别名（`action_def_down` 等），被 `potion_effects` 消费 | 内容 |
| **`core/class_sets.py` / `core/drops.py` / `core/affix.py` / `core/gems.py` / `core/runes.py` / `core/enchant.py` / `core/maps.py` / `core/pois.py` / `core/index.py` / `core/wild*.py` / `core/rule_engine.py` / `core/position.py` / `core/worlds.py` / `core/stats.py` / `core/exploration.py` …** | — | 全部 `-> game.data` 有直接边（1~3 条），是**内容生成逻辑** | 内容 |
| `core/encounter.py` | 29 | 副本遇怪概率，读 map dict 的 `dungeon.discovery_agro` | 内容（数据取值函数） |
| `core/hidden_cond.py` | 86 | 隐藏怪环境条件注册表（`ENV_KEYWORDS` 含 `forest/water/ruin` 地图 id 关键词） | 内容 |

---

## 3. import 依赖矩阵

### 3.1 分组边矩阵（行 = source 分组，列 = target 分组，数字 = 模块级不同目标数）

```
source          battle2  core  data  services  commands  store  game/*top
game/battle2        33     2     1        0         0      0        5      -> 40
game/core            0    26    43        0         0      2       70      -> 141
game/data            0     3    54        0         0      0       71      -> 128
game/services       20    14     5       10         0      1       47      -> 97
game/commands       16    37    10       25        43      4       66      -> 201
game/store           0     3     0        0         0     13       18      -> 34
game/*top            1     4     6        0         0      3        5      -> 19
```

**读法**：`services -> battle2 = 20`（5 个 services 模块 import 引擎）；`battle2 -> core/data/*top = 8`（引擎反向出边，见 §4）。

### 3.2 ★ 反向依赖结论（引擎 → 内容）

**结论：引擎有反向依赖，且必须先行打破。**

`game/battle2/*` 中 **4 个模块**（`actions` / `battle` / `config` / `stats`）持有 **7 个非引擎目标**的 import 边。其余 9 个引擎模块（`actors` / `ai` / `schedule` / `serialize` / `landing` / `effects` / `effect_triggers` / `state_effects` / `__init__`）**零出边**——引擎内部纯度已很高，问题集中在 4 个文件。

| # | source:line | 目标 | 形态 | 用途 | 性质 |
|---|---|---|---|---|---|
| **R1** | `battle2/actions.py:16` | `game.engine`（`as E`） | 模块级 | `E.calc_damage`×3 / `E.resolve_formula` / `E.skill_power_mult`×3 / `E.skill_flat_value` / `E.skill_formula_expr` / `E.skill_formula_expr_for_seg` / `E.skill_level_of`×4 / `E.skill_lifesteal_pct`×2 | **核心反向边**（21 处调用点中的 20 处） |
| **R2** | `battle2/actions.py:17` | `game.core.constants`（`as K`） | 模块级 | **未使用（死 import）** | 死边 |
| **R3** | `battle2/actions.py:35` | `game.content`（`as C`） | 函数内（惰性） | `C.resolve("classes", …)` + `C.CLASSES.get(cid).basic_skill` | **内容表直读** |
| **R4** | `battle2/actions.py:296` | `game.core.formation`（`as _fm`） | 函数内 | `_fm.select_aoe_targets` | 合规（通用纯函数，层级归属待迁） |
| **R5** | `battle2/actions.py:679` | `game.core.formula_expr` | 函数内 | `compile_expr` / `eval_expr` / `build_vars` | 合规（通用解释器） |
| **R6** | `battle2/actions.py:726` | `game.engine` | 函数内 | `skill_buff_turns(lv, info=…)` | **反向边**（技能成长公式） |
| **R7** | `battle2/actions.py:727` | `game.core.constants`（`as C`） | 函数内 | **未使用（死 import）** | 死边 |
| **R8** | `battle2/actions.py:758` | `game.engine` | 函数内 | `skill_mech_val(info, lv)` | **反向边** |
| **R9** | `battle2/battle.py:120` | `game.engine`（`as E`） | 函数内 | `E.skill_info(class_name, sk)` / `E.skill_by_key(sk)` | **反向边**（读 `C.PLAYER_SKILLS`/`BRANCH_SKILLS`/`TUTOR_SKILLS`） |
| **R10** | `battle2/battle.py:121` | `game.content`（`as C`） | 函数内 | `C.MONSTER_SKILLS.get(sk)` | **内容表直读** |
| **R11** | `battle2/stats.py:16` | `game.engine`（`as E`） | 模块级 | `E.player_final_stats(...)`（玩家职业面板公式：装备/等级/转职/称号/种族/属性被动全算） | **最重的反向边** |
| **R12** | `battle2/config.py:38` | `game.data.battle_rules` | 函数内（`load_game_defaults`） | `load_game_rules(battle_rules)` 装配 `EFFECT_ACTIONS`/`EFFECT_RULES` | **已注释声明为「游戏侧装配」**，但物理上落在引擎包内 → 应移出 |
| **R13** | `battle2/stats.py:97` | 字面量 `"战士"` | 硬编码 | `actor.get("class_name", "战士")` 默认职业名 | **内容名侵入** |
| **R14** | `battle2/actions.py:22-26` | 字面量中文 kind | 硬编码 | `K_PHYS="物理"` / `K_MAGI="魔法"` / `K_TRUE="真伤"` / `K_HEAL="治疗"` / `K_BUFF="增益"` | **与数据表 kind 值耦合的内容语义** |
| **R15** | `battle2/actions.py:42` | 字面量 `"攻击"` | 硬编码兜底 | 兜底普攻 `{"name": "攻击", …}` | **内容名侵入** |

**反向依赖边统计**：**15 条**（其中 **2 条死 import**：R2/R7；**2 条合规通用**：R4/R5；**11 条真反向耦合**）。

> ⚠️ 关键点：`R4/R5` 只是「层级归属」问题（通用纯函数当前住在 core/），不是内容耦合。
> ⚠️ `R12` 被 docstring 自我豁免为「游戏侧装配」，但物理位置在 `engine` 包内 —— 分离后必须搬到 content 侧，否则 submodule 里会带一条指向游戏仓库的 import。

### 3.3 hub 表（被依赖最多的模块）

| 模块 | 引用方数 | 备注 |
|---|---:|---|
| `game.content`（聚合层） | 55 | 内容层内部枢纽（引擎 2 个文件在列） |
| `game.db` | 47 | 内容层持久化 |
| `game.engine` | 34 | **内容 + 引擎共用的巨型枢纽**（含 battle2 的 3 个文件） |
| `game.data` | 28 | 含 `battle2/config.py` |
| `game.battle2`（包） | 10 | 引擎外部入口 |
| `game.core` | 8 | 含 `battle2/actions.py` |

---

## 4. 引擎内游戏知识残留扫描

扫描口径：引擎目录 = `game/battle2/`（13 文件 / 3 572 行）。
模式：中文（区分 STRING / COMMENT / DOCSTRING）、游戏史实名词（`melody` / `faith` / `破绽` / `磐核` / `旋律` / `信仰` / `奥兰迪亚` / `余烬`…）、表名（`PLAYER_SKILLS` / `MONSTER_SKILLS` / `INSTANCES` / `CLASSES` / `SKILL_UP` / `MECH_CFG` / `EFFECT_ACTIONS` / `EFFECT_RULES`…）、职业 id（`cls_*`）。

### 4.1 总量

| 项 | 数量 |
|---|---:|
| 扫描模式命中总行 | **110** |
| ├─ **不合规**（真反向耦合 / 内容名侵入） | **22** |
| └─ **合规**（数据驱动契约 / 显示文案 / 注释举例） | **88** |
| 职业 id（`cls_*`）命中 | **0** ✅ |
| 表名 `PLAYER_SKILLS`/`INSTANCES` 命中 | **0** ✅（仅 `MONSTER_SKILLS` 直读 1 处 + `CLASSES` 1 处） |

### 4.2 不合规 22 条逐条清单

| # | 文件:行 | 代码片段 | 合规？ |
|---|---|---|---|
| 1 | `actions.py:16` | `from .. import engine as E` | ❌ 反向边 |
| 2 | `actions.py:17` | `from ..core import constants as K` | ❌ 死 import + 反向边 |
| 3 | `actions.py:22` | `K_PHYS = "物理"` | ❌ 内容语义常量 |
| 4 | `actions.py:23` | `K_MAGI = "魔法"` | ❌ 同上 |
| 5 | `actions.py:24` | `K_TRUE = "真伤"` | ❌ 同上 |
| 6 | `actions.py:25` | `K_HEAL = "治疗"` | ❌ 同上 |
| 7 | `actions.py:26` | `K_BUFF = "增益"` | ❌ 同上 |
| 8 | `actions.py:35` | `from .. import content as C` | ❌ 反向边 |
| 9 | `actions.py:36` | `cid = C.resolve("classes", class_name or "")` | ❌ 内容表直读 |
| 10 | `actions.py:37` | `bs = (C.CLASSES.get(cid, {}) or {}).get("basic_skill") or {}` | ❌ 内容表直读 |
| 11 | `actions.py:42` | `return {"name": "攻击", "kind": K_PHYS, "exprs": ["atk*1.0"]}` | ❌ 内容名兜底 |
| 12 | `actions.py:296` | `from ..core import formation as _fm` | ⚠️ 合规（通用纯函数），仅层级归属待改 |
| 13 | `actions.py:679` | `from ..core.formula_expr import compile_expr, eval_expr, build_vars` | ⚠️ 合规（通用解释器） |
| 14 | `actions.py:726` | `from ..engine import skill_buff_turns` | ❌ 反向边 |
| 15 | `actions.py:727` | `from ..core import constants as C` | ❌ 死 import |
| 16 | `actions.py:758` | `from ..engine import skill_mech_val` | ❌ 反向边 |
| 17 | `battle.py:120` | `from .. import engine as E` | ❌ 反向边 |
| 18 | `battle.py:121` | `from .. import content as C` | ❌ 反向边 |
| 19 | `battle.py:137` | `info = (C.MONSTER_SKILLS or {}).get(sk)` | ❌ 内容表直读 |
| 20 | `config.py:38` | `from game.data import battle_rules`（`load_game_defaults` 内） | ⚠️ 已声明「游戏侧装配」——**位置不合规**，需移出引擎包 |
| 21 | `stats.py:16` | `from .. import engine as E` | ❌ 反向边 |
| 22 | `stats.py:97` | `actor.get("class_name", "战士")` | ❌ 内容名默认值 |

**真耦合（❌）= 19 条**（含 2 条死 import）× **位置不合规（⚠️）= 3 条**。
`config.py:5` 的 `from game.battle2 import config` 出现在 **docstring 示例**里，合规，不计入。

### 4.3 合规 88 条的性质（为什么不算游戏知识）

| 类别 | 典型 | 说明 |
|---|---|---|
| **配置契约名**（最多） | `EFFECT_ACTIONS` / `EFFECT_RULES` / `MECH_CFG` / `BAR_STATE_PREFIX` | 引擎与游戏之间的**装配接口名**，正是「换配置=换游戏」的正确形态；`config.py` 的 `set_config/load_game_rules/state_def` 是这条契约的实现 |
| **显示文案**（中文 log） | `f"🩸 吸血：回复 {heal} 点生命！"`、`f"💨 {name} 逃跑了！"` | 引擎直接产出中文播报 = 本地化/展示层问题（i18n），**不含**表名/职业名/技能名的硬编码（唯二例外是第 4.2 表 #11/#22） |
| **注释举例** | `# 引擎零语义：stacks 允许 float（faith 每刻 -0.7 衰减等小数刻度）`、`# N7.5a 承伤乘区（vulnerable 破绽）` | 用游戏实例解释**通用机制**，`effects.py:32` / `schedule.py:334` / `landing.py:85` 均属此类；建议分离时统一改写为中性描述（可选） |
| **通用谓词名** | `st["_state_dmg_mult"]`、`mode=add/set/consume` | 引擎动词，非游戏名词 |

---

## 5. 对外 API 面盘点（内容 → 引擎）

**14 个引擎外包模块**直接 import 引擎（命令层 8 + 服务层 5 + `game/engine.py` 1）：

| 层 | 模块 |
|---|---|
| commands | `battle_item_use` / `boss_script` / `combat` / `instance` / `instance_battle` / `player` / `tower` / `world` |
| services | `battle_bridge` / `battle_bar_procs` / `battle_cond_procs` / `battle_we_procs` / `class_mech_proc` |
| top | `game/engine.py`（`from game.battle2.actions import _skill_pay_of`） |

**实际被消费的 25 个符号**（引用点数）：

| 符号 | 来源模块 | 引用点 | 应否公开 |
|---|---|---:|---|
| `deal_damage` | `battle2.landing` | 15 | ✅ 公开 |
| `state_def` | `battle2.state_effects` | 13 | ✅ 公开 |
| `heal_actor` | `battle2.landing` | 10 | ✅ 公开 |
| `Battle` | `battle2` | 10 | ✅ 公开 |
| `actor_alive` | `battle2.actors` | 8 | ✅ 公开 |
| `act_apply` | `battle2.effects` | 8 | ✅ 公开 |
| **`_cap_of`** | `battle2.effects` | **7** | ⚠️ **私有 → 应升公开**（`cap_of`） |
| `actor_stats` | `battle2.stats` | 6 | ✅ 公开 |
| `apply_effects` | `battle2.effects` | 5 | ✅ 公开 |
| **`_now_of`** | `battle2.battle` | **5** | ⚠️ **私有 → 应升公开**（`now_of`） |
| `stats`（模块） | `battle2` | 4 | ✅ 公开 |
| `register_action` | `battle2.effects` | 4 | ✅ 公开 |
| `config`（模块） | `battle2` | 2 | ✅ 公开 |
| `fire` | `battle2.effect_triggers` | 2 | ✅ 公开 |
| `all_state_effects` | `battle2.state_effects` | 2 | ✅ 公开 |
| `action_time` | `battle2.schedule` | 2 | ✅ 公开 |
| `initial_ct` | `battle2.schedule` | 2 | ✅ 公开 |
| `hostile_sides` | `battle2.actors` | 2 | ✅ 公开 |
| `act_shield` | `battle2.effects` | 2 | ✅ 公开 |
| **`_norm_stack`** | `battle2.effects` | **2** | ⚠️ 私有 → 应升公开 |
| `effects`（模块） | `battle2` | 1 | ✅ 公开 |
| **`_heal_amount`** | `battle2.actions` | **1** | ⚠️ 私有 → 应升公开 |
| **`_skill_pay_of`** | `battle2.actions` | **1** | ⚠️ 私有 → 应升公开 |
| `make_actor` | `battle2` | 1 | ✅ 公开 |
| `get_effect_rules` | `battle2.config` | 1 | ✅ 公开 |
| `get_effect_actions` | `battle2.config` | 1 | ✅ 公开 |

**属性式访问（`BT.x` / `FX.x` / `_b2config.x` 形态）**：`B2.from_state`、`Battle.from_state`、`_b2c.get_effect_rules`、`_b2cfg.load_game_defaults`、`_b2config.get_effect_actions`。

> **结论**：内容层已经绕过 `battle2/__init__.py`（现仅导出 4 符号）**直接 import 引擎内部模块**（`battle2.effects` / `battle2.landing` / `battle2.state_effects` / `battle2.stats` / `battle2.actors` / `battle2.schedule` / `battle2.actions` / `battle2.battle` / `battle2.config`），并触及 **5 个下划线私有符号**。这是 submodule 化前必须固化的**公开 API 面**。

---

## 6. 目录拆分方案

### 6.1 目标形态

```
framework-engine/                 # 独立 git 仓库（可分发，pip/zip 均可）
  framework_engine/
    __init__.py                   # 公开 API 门面（re-export §5 的 25 符号）
    api.py                        # 【新】显式公开 API 清单 + __all__ + 版本号
    plugin.py                     # 【新】插件骨架：register_action / register_trigger / register_handler 钩子
    events.py                     # 【新】事件协议常量（事件名 / ctx 契约 / 触发时机枚举）
    battle.py  actions.py  actors.py  ai.py  effects.py  effect_triggers.py
    landing.py  schedule.py  serialize.py  state_effects.py  stats.py
    config.py                     # 挂载点（去掉 load_game_defaults）
    formulas.py                   # 【新】自 game/engine.py 拆出的纯数值公式（见 6.4）
    support/
      formula_expr.py             # ← core/formula_expr.py
      formation.py                # ← core/formation.py
      skill_kinds.py              # ← core/skill_kinds.py（kind 值改为配置注入）
      bars.py                     # ← core/battle_bars.py（读点改 config）
      tick_effects.py             # ← core/tick_effects.py（灰色，可延后）
  pyproject.toml  README.md  tests/  LICENSE

dragonfall/                       # 游戏仓库
  engine/                         # submodule → framework-engine
  content/
    data/        # ← game/data/（含 _assembly.py）
    core/        # ← game/core/（灰色模块全部落这里）
    services/    # ← game/services/
    commands/    # ← game/commands/
    store/       # ← game/store/
    rules/       # 【新】自 game/engine.py 拆出的内容规则（skills/classes/panel 表读）
    bootstrap.py # 【新】content 侧单点装配：load_engine_config() + apply_game_content()
    apply.py     # 【新】apply_game_content(actor, ctx) 单一装配入口
```

### 6.2 `engine/` 逐文件清单

**直接迁入（13 个，零改动）**：`actors.py` · `battle.py` · `actions.py` · `effects.py` · `effect_triggers.py` · `landing.py` · `schedule.py` · `serialize.py` · `state_effects.py` · `ai.py` · `__init__.py`
**改名/改写后迁入（2 个）**：`config.py`（删 `load_game_defaults`，保留 `set_config`/`load_game_rules`/`state_def`/`get_effect_*`）· `stats.py`（去 `from .. import engine`、去 `"战士"` 默认值，改走 `config.panel_fn`）
**需断链改写（1 个）**：`actions.py`（R1/R2/R3/R6/R7/R8 —— 21 处 `E.*` 调用 + 2 处内容表读 + 2 处死 import）
**从 core 迁入（4 个）**：`formula_expr.py` · `formation.py` · `skill_kinds.py`（改 kind 注入）· `bars.py`（← `battle_bars.py`，读点改 config）
**新建（4 个）**：`api.py` · `plugin.py` · `events.py` · `formulas.py`

### 6.3 `content/` 逐文件清单

| 目标 | 来源 | 说明 |
|---|---|---|
| `content/data/` | `game/data/*`（86 文件，74 575 行） | 纯静态表，**原样迁移**；`_assembly.py` + `__init__.py` 保留装配职责 |
| `content/core/` | `game/core/*`（55 文件，除迁走的 4 个） | 灰色模块**全部落这里**（`stat_bonus` / `timed_events` / `passive_procs` / `battle_conds` / `battle_modes` / `potion_effects` / `item_templates` / `effect_actions` / `class_sets` / `drops` / `affix` / `gems` / `runes` / `enchant` / `maps` / `pois` / `index` / `wild*` / `rule_engine` / `position` / `worlds` / `stats` / `exploration` / `encounter` / `hidden_cond` / `achievements*` / `title_conds` / `dialogue*` / `shop_stock` / `smith_stock` / `craft` / `daily_events` / `events` / `event_templates` / `world_event_templates` / `factions` / `fishing` / `formula_expr` 的调用方 / `instance_gate` / `monsters` / `mounts` / `pets` / `poi_effects` / `portals` / `time_weather` / `worlds` / `skill_kinds` 的调用方 …) |
| `content/services/` | `game/services/*`（22 文件） | 机制动作注册模块 + `battle_*_proc` 装配层 + `battle_bridge` |
| `content/commands/` | `game/commands/*`（24 文件） | AstrBot 命令层 |
| `content/store/` | `game/store/*`（12 文件） | 零引擎依赖，风险最低，**建议最后迁**（或最先，见 §7 顺序） |
| `content/rules/`**【新】** | 自 `game/engine.py` 拆出 | 读表的技能/职业/面板函数：`skill_info` / `skill_by_key` / `skill_owner_cls` / `skills_for_level` / `is_skill_learned` / `skill_level_of` / `branch_skill_owner` / `branch_path_index` / `player_final_stats` / `race_stats` / `race_name` / `_skill_up` / `skill_max_level` … |
| `content/bootstrap.py`**【新】** | 新 | 单点装配：`load_engine_config()`（把 `battle_rules.EFFECT_ACTIONS/EFFECT_RULES`、`MECH_CFG`、面板函数、技能查询函数注入引擎 `config`） |
| `content/apply.py`**【新】** | 新 | `apply_game_content(actor, ctx=None)` 单一装配入口（见 6.5） |

### 6.4 `game/engine.py`（1 212 行）拆分（最大单点风险）

| 去向 | 内容 |
|---|---|
| `engine/formulas.py` | `calc_damage` · `resolve_formula` · `skill_formula_expr` · `skill_formula_expr_for_seg` · `skill_power_mult` · `skill_flat_value` · `skill_buff_turns` · `skill_mech_val` · `skill_lifesteal_pct` · `skill_cond_mult` · `skill_max_level` · `skill_learn_cost` · `skill_mp_pay_of` |
| → 参数化 | `FORMULA_SKELETON`（`data/formula_skeleton.py`）与 `SKILL_FLAT_*`（`data/skill_up.py`）改为**配置注入**（`config.set_config("formula_skeleton", …)`），公式函数不再读 `data` |
| `content/rules/skills.py` | `skill_info` · `skill_by_key` · `skill_owner_cls` · `skills_for_level` · `is_skill_learned` · `skill_level_of` · `branch_skill_owner` · `branch_path_index` · `_sk_table` · `_br_table` · `_build_skill_key_index` |
| `content/rules/panel.py` | `player_final_stats` · `player_stats_detail` · `race_stats` · `race_name` · `_PASSIVE_STAT_APPLY` 及面板全部表读点 |
| 桥接 | 引擎侧通过 `config.panel_fn` / `config.skill_lookup_fn` 调用；未注入时走纯怪路径（`stats._monster_base_stats`） |

### 6.5 灰色地带处置策略

**原则：先移「内容」，引擎只保留无条件通用件。「先移哪边」的判据 = 「引擎是否需要它」** —— 引擎需要 → 引擎（并断掉其内容读点）；引擎不需要 → 内容。

| 模块 | 处置 | 时点 |
|---|---|---|
| `core/stat_bonus.py` | → `content/core/`（引擎不读它，命令层/存档读） | 第一批（随 core 迁移） |
| `core/timed_events.py` | → `content/core/`（引擎不消费）；后续如需通用化，抽 `storage` 接口后再入引擎 | 第一批 |
| `core/battle_conds.py` | → `content/core/`（battle2 不 import 它；旧 battle.py 已删） | 第一批 |
| `core/passive_procs.py` | → `content/core/`（**保留**：被 `tests/test_passive_proc_coverage.py` 作为活门禁消费；原「孤儿归档」建议已作废，见 §8-R13） | 第一批 |
| `core/battle_bars.py` | → `engine/support/bars.py`（引擎需要它：`services/battle_bar_procs` 与 `class_mech_proc` 依赖其纯函数），读点改 `config.MECH_CFG` + `config.bar_prefix` | 第二批 |
| `core/battle_modes.py` / `potion_effects.py` / `item_templates.py` / `effect_actions.py` | → `content/core/` | 第一批 |
| `game/engine.py` | 一拆为二（§6.4） | **独立一批（最高风险）** |
| `core/formula_expr.py` / `formation.py` / `skill_kinds.py` | → `engine/support/`（通用），旧路径留 shim | 第二批 |
| `core/tick_effects.py` | → `engine/support/` 或留 content（零消费者，可延后） | 最后 |

### 6.6 `apply_game_content` 单一装配入口收敛

**现状（分散并列调用，共 6 处命令层调用点 + 1 处内容侧自调用）**

| 位置 | 调用 |
|---|---|
| `commands/combat.py:621` | `battle_equip_proc.apply_to_actor` |
| `commands/combat.py:622` | `class_mech_proc.apply_class_mech` |
| `commands/combat.py:2808` | `battle_equip_proc.apply_to_actor`（PVP 路径） |
| `commands/combat.py:2851` | `class_mech_proc.apply_class_mech`（PVP 路径） |
| `commands/tower.py:151` | `battle_equip_proc.apply_to_actor` |
| `commands/tower.py:156` | `class_mech_proc.apply_class_mech` |
| `commands/battle_item_use.py:52` | `battle2.config.load_game_defaults()` |
| `services/class_mech_proc.py` | 内部：`apply_class_mech` 尾段 import `battle_bar_procs.apply_bar_procs` + `battle_cond_procs.apply_cond_procs`（原 L2143/L2149，并发改动后为 L2303/L2309） |

装配顺序契约（散落在注释里）：`bar_gain` 须先于 mech 段 → equip → class_mech → bar → cond → food。

**目标收敛**

```python
# content/apply.py
def apply_game_content(actor: dict, ctx: dict | None = None) -> dict:
    """唯一装配入口。顺序契约在此固化，命令层不再并列调用。"""
    ensure_engine_configured()          # 幂等；等价旧 load_game_defaults
    equip_proc.apply_to_actor(actor, ctx)      # ① 装备/词条
    class_mech_proc.apply_class_mech(actor, ctx)  # ② 职业 mech（内部先 bar→mech）
    bar_procs.apply_bar_procs(actor, ctx)      # ③ 挂敌身条
    cond_procs.apply_cond_procs(actor, ctx)    # ④ 技能条件
    food_proc.install_food_fx(actor, ctx)      # ⑤ 食物效果
    return actor
```

- 命令层 6 处 → 各 1 行 `apply_game_content(actor)`；`battle_item_use.py:52` 改为 `ensure_engine_configured()`。
- 幂等由 `apply.py` 内部 `ctx["_applied_content"]` 标记保证（沿用 `class_mech_proc.apply_class_mech` 现有幂等语义）。
- 引擎侧仍不知内容：`apply_game_content` 住在 content，引擎只提供 `config`/`register_action`/`fire` 三个通用挂载面。

---

## 7. 迁移步骤（9 步 · 分批 · 可回滚）

> 每步的验证点统一含：**`python scripts/run_all_tests.py` 跑满 241/241 绿**（用 AstrBot uv python：
> `C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe scripts/run_all_tests.py`）。
> 每步一个独立 commit（或一组，但**必须可单独 revert**）。跑全量期间不改任何源文件。

| 步 | 动作 | 验证点 | 回滚 |
|---|---|---|---|
| **S0** | 冻结基线：记录 `git rev-parse HEAD`（=780720b）+ 跑一次全量确认 241 绿；写入本档 | 241/241 绿，基线 hash 存档 | 无（只读） |
| **S1** | **断反向边（不移动任何文件）**：① `stats.py:97` 默认 `"战士"` → `""`；② `stats.py:16` + `actions.py:16,726,758` + `battle.py:120` 的 `E.*` 改走 `config` 注入（`config.panel_fn` / `config.formulas`）；③ `actions.py:35-37` 的 `C.CLASSES` 与 `battle.py:121,137` 的 `C.MONSTER_SKILLS` 改走 `config.skill_lookup` / `config.basic_skill_fn`；④ 删死 import `actions.py:17,727`；⑤ `config.py:38` `load_game_defaults` 移到内容侧（旧名留 shim 函数委托）；⑥ `actions.py:22-26` kind 常量 + `actions.py:42` `"攻击"` 兜底改为 `config.kinds` / `config.basic_fallback`；⑦ `config.py:35` 的 `load_game_defaults` 保留为**兼容 shim**（52 个测试依赖它） | 241 绿 + **新增 `tests/test_engine_no_content.py`**：AST 断言 `game/battle2/**` 零 `game.content` / `game.data` / `game.engine` / `game.core.constants` import 边 | `git revert <S1 commit>`（纯逻辑改动，不动文件） |
| **S2** | **固化公开 API**：新增 `battle2/__init__.py` 全量 re-export（§5 的 25 符号）；把 5 个私有符号提升为公开（`cap_of` / `now_of` / `norm_stack` / `heal_amount` / `skill_pay_of`），**保留下划线旧名别名**；内容层 import 全部改走包门面 | 241 绿 + grep 断言：`game/`（非 battle2）不再出现 `battle2.effects._`/`battle2.battle._` 等下划线符号 | revert |
| **S3** | **通用件入引擎**：`git mv core/formula_expr.py core/formation.py core/skill_kinds.py core/battle_bars.py → game/battle2/support/`；旧路径留 shim 模块（`from ..battle2.support.X import *`）；`skill_kinds` 中文 kind 值改配置注入 | 241 绿（shim 保证旧路径可用） | `git revert`（mv 可逆） |
| **S4** | **引擎包改名**：`git mv game/battle2 → game/engine`；新增 `game/battle2/__init__.py` shim（`from game.engine import *`）；`tests/*` 的 `from game.battle2 …` 暂不动 | 241 绿（两条路径都能 import） | revert |
| **S5** | **`game/engine.py` 一拆为二**：拆出 `game/engine/formulas.py`（引擎）与 `game/content_rules/{skills,panel}.py`（内容，暂用顶层目录避免与 S6 冲撞）；`game/engine.py` 留 shim 转发全部旧符号 | 241 绿（shim 转发 + 数值不变）；额外：`skill_max_level`/`skill_power_mult`/`player_final_stats` 数值抽样对拍 `tests/_battle_settlement_snapshot.baseline.json` | revert |
| **S6** | **内容层重组（5 子步，自底向上）**：`data → core → store → services → commands` 依次 `git mv` 进 `game/content/`；每子步在旧路径留 `__init__.py` shim（`from game.content.X import *` + 关键子模块 `sys.modules` 别名）；**每子步单独跑一次全量** | 241 绿 ×5 | 每子步独立 revert |
| **S7** | **单一装配入口**：新增 `game/content/apply.py: apply_game_content()` + `game/content/bootstrap.py: ensure_engine_configured()`；把 §6.6 的 9 处并列调用改为 `apply_game_content`（6 处）+ `ensure_engine_configured()`（1 处）+ 内部串接（2 处） | 241 绿 + **新增装配顺序契约测试**（断言 bar→mech→equip→cond→food 调用序 + 幂等） | revert |
| **S8** | **拆仓库**：新建 `framework-engine/` git 仓库，`git filter-repo`/`subtree split` 导出 `game/engine/` 历史；`dragonfall/` 加 `.gitmodules` + `git submodule add`；`main.py`/`conftest.py` 加 `engine` 到 `sys.path` 或安装为包 | 241 绿（submodule 就位后 import 路径不变） | 删除 submodule + 恢复 `git mv` 前的目录树 |
| **S9** | **收口清理**：删过渡 shim（`game.battle2` / `game.core.formula_expr` / 顶层 `game.engine.py` shim）；`_retired_old_engine/` + 孤儿 `passive_procs.py` 归档决策；更新 `ARCHITECTURE.md` / `AGENTS` 类文档 | 241 绿 + grep 断言全仓库零 `game.battle2` 残留（除 docs 历史档） | revert |

**总计：9 步（含 S6 的 5 个子步 = 13 个独立可回滚批次）。**

**S5 的补充说明**：这是风险最高的一步。建议先做「只搬不改」——`formulas.py` 逐字复制 `calc_damage`/`resolve_formula`/`skill_*`，`content_rules/` 逐字复制表读函数，`game/engine.py` 变 shim；**不重构内部**。数值不变可以用现有 `tests/test_numeric_*` + `_battle_settlement_snapshot.baseline.json` 对拍佐证。

---

## 7.5 ⚠️ 方案修正（2026-09-11 实施期发现，父 agent 实测确认）

### 缺陷一：S4 的包名 `engine` 与既有 `game/engine.py` **冲突**

方案 S4 写「`git mv game/battle2 → game/engine`」，但仓库里**已存在** `game/engine.py`
（1212 行的内容文件，S5 才处理）。**实测确认**：同目录下包优先于同名模块 ——

```
$ mkdir game/engine && echo "X='pkg'" > game/engine/__init__.py
$ echo "X='mod'" > game/engine.py
$ python -c "from game import engine; print(engine.X)"
取到: pkg          ← 旧 game/engine.py 变成不可达
```

影响面实测：引用 `game.engine` 的语句 **79 条 / 67 个文件**（game/ 28 + tests/ 26 + 归档 12 + audit 1）。
按原文执行会让这 54 个活文件安静地拿到错对象。

**修正**：
- **先做 S5（拆掉 `game/engine.py`），后做重命名**；且 S5 的引擎侧落点改为
  **`game/battle2/formulas.py`**（而非原文的 `game/engine/formulas.py`，否则过渡期仍然冲突）
- 内容侧落点 `game/content_rules/{skills,panel}.py`
- 包重命名（`battle2` → 新名）**推迟到 S8 拆仓库时**：届时框架仓库给自己的包随便起名，
  游戏侧只需留一个薄 shim（包名未定，候选 `game/ctb` 之类不冲突的名字）

### 缺陷二：S6 的路径假设

S6 计划把 `data → core → store → services → commands` 依次 `git mv` 进 `game/content/`。
但 S3 已把 4 个通用件移出 `core/`（`battle2/support/`），S5 又拆了 `engine.py`
（内容侧去 `game/content_rules/`）→ **S6 的起点与原文描述已不同**，实施前需重新盘点
（写新快照，而不是照旧清单搬）。

### 实施顺序修正后

```
S1 ✅ → S2 ✅ → S3 ✅ → S5'（拆 engine.py，落 battle2/formulas.py + content_rules/）
  → S6'（内容层重组，先重新盘点）→ S7（单一装配入口）→ S8（拆仓库 + 包重命名）
  → S9（收口）
```

## 8. 风险清单（13 条）

| # | 风险 | 触发条件 | 缓解 |
|---|---|---|---|
| **R1** | **静态 import 链环形** | `core ↔ data` 已有环：`core/battle_bars.py:30` 注释明说「不在此处顶层 import data.battle_config（core ↔ data 循环导入）」，改用函数内 `importlib.import_module`；`data/__init__ → core/__init__ → core/smith_stock → db → store.connection → content` 亦有环（`core/__init__.py:59-61` 注释记录） | 迁移**必须保持延迟导入点原样**；子包重排时先跑 `python -c "import game.content"` 冷启动冒烟（比全量回归快 20×）再跑全量 |
| **R2** | **`sys.path` 假设** | `conftest.py:29-30` 同时 `sys.path.insert` **QQBOT_DIR** 与 **PLUGIN_DIR**；全仓库并存两种 import 风格：包式 `from data.plugins.dragonfall.game import content`（conftest）与裸式 `from game import content`（241 个测试内联模板） | 拆包时必须**两套路径同时可用** → 旧路径 shim + `engine/` submodule 加进 `sys.path`；S8 后严禁删 shim 直到 S9 |
| **R3** | **测试的 `sys.path.insert` 手抄模板** | 241 个测试文件里 **261 处** path/import 语句，其中绝大多数是手抄的 4 行模板（`PLUGIN_DIR` / `QQBOT_DIR` / `TEST_DB` / `shim_astrbot`）。目录一改就集体失效 | 用脚本批量替换模板（**只改 path 计算，不改 import 名**）；先在一个测试上验证模板，再全量批处理 |
| **R4** | **`run_all_tests.py` 硬编码推导** | 脚本内部用 `PLUGIN_DIR = dirname(dirname(__file__))` 反推 + `SERIAL_SLOT`（2 个共享库测试）+ `_SHARED_DB_RE` 自动探测；`PYTHON = "C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe"` 硬编码 | 步骤 S1 之前先确认「241 绿」的可复现命令写进本档；改目录时同步改脚本的 PLUGIN_DIR 推导与 SERIAL_SLOT 路径 |
| **R5** | **git 历史** | 用 `mv` 而非 `git mv` 会丢 blame；`git mv` 会让 241 个测试的 diff 显示为 rename | 一律 `git mv`；`framework-engine/` 抽取用 `git subtree split -P game/engine` 保历史，**不要**复制粘贴 |
| **R6** | **submodule 工作流** | submodule 化后，`dragonfall` 的 CI/回归不再自动包含引擎改动；`engine` 单测与游戏回归**双轨**容易漂移 | 引擎仓库自带走 `tests/`；`dragonfall` 侧在 `scripts/run_all_tests.py` 前置一步跑引擎单测（或 CI 双 job） |
| **R7** | **`load_game_defaults` 有 52 个测试调用点** | `grep` 统计：52 个 `tests/*.py` 调 `_b2c.load_game_defaults()` / `_b2config.load_game_defaults()` | 迁移时**保留函数名 + 位置 shim**（`battle2/config.py` 里留 `load_game_defaults` 转发到 content bootstrap），改名分两步（先加新名 → 批量改测试 → 删旧名） |
| **R8** | **引擎 `config` 空挂载静默降级** | 引擎大量 `try/except: pass` + `config.state_def()` 无挂载返回 `{}`（= 纯数值无规则）。S1 断链后若 content 未装载，引擎会**静默空放**（测试假绿、线上静默失效） | 引擎加 `config.strict` 开关：无挂载时抛 `EngineNotConfigured`；测试环境默认 strict=1，生产 =0 但启动期显式 `ensure_engine_configured()` |
| **R9** | **`game/engine.py` 拆分错位** | 65 KB / 1 212 行，通用公式与内容表读混在一起（`C.PCT_CAPS`×17、`C.resolve`×12…）。拆错会把公式留在 content → 引擎仍依赖 content | 按 §6.4 的表**逐函数列白名单**拆分；`formulas.py` 迁入后用 `test_engine_no_content.py` 断言引擎零 `content` import |
| **R10** | **嵌套 git 仓库误纳** | `design/new_world/.git` 存在（`design/` 已被 `.gitignore` 忽略），拆 `framework-engine` 时若用 `git add -A` 可能误纳 | 用显式路径 `git add game/engine`；拆仓库前 `git status --ignored` 核对 |
| **R11** | **存档/PVP 兼容** | `serialize.py:90-106` 有 v181.M-bonus 一次性迁移（旧档 `stat_bonus`/`cap_bonus` 旧键 → `bonus` 容器）；拆包不影响数据，但 shim 漏导出 `from_state`/`to_state` 会导致旧档反序列化炸 | S2 的 API 面必须显式含 `Battle.from_state` / `to_state`；加旧档反序列化冒烟测试 |
| **R12** | **`__pycache__` 幽灵字节码** | 仓库内已有 `tests/audit_pyc_bytecode.py` / `audit_pyc_diff.py` 先例；旧 `game/battle2/*.pyc` 在 shim 删除后可能被解释器优先命中 | S4/S8/S9 每步前清 `__pycache__`（或跑 `python -B`）；用现有 audit 脚本核对 |
| **R13** | **孤儿代码误当资产迁移** | ⚠️ **本条一半是错的（2026-09-11 复核）**：`core/passive_procs.py`（1 610 行）**不是孤儿** —— `tests/test_passive_proc_coverage.py` 消费它做启动全覆盖校验（53 proc 白名单 + 缺口钉死）；当年判「零消费者」是因为门禁建在该判断之后。`core/tick_effects.py`（60 行）确为死代码 | **教训**：「零引用清单」必须用**当前**仓库状态重跑一遍再决策；旧清单会把后来新增的消费方漏掉 |

---

## 9. 结论

> **现在不能直接拆。** 引擎（`game/battle2/`）自身纯度已经很高（13 个模块里 **9 个零出边**、**0 处 `cls_*`**、**0 处 `PLAYER_SKILLS`/`INSTANCES`**），但 **4 个文件（`actions` / `battle` / `stats` / `config`）持有 15 条指向内容层的 import 边**，且内容层绕过包门面直接依赖引擎内部模块与 **5 个下划线私有符号**。
>
> **前置 = 第 7 节的 S1 + S2 + S3**（三步都不移动文件、都能单独 revert、每步都有「241 绿 + 零反向边」的机器可验证断言）：
> 1. **S1 断链**：把 `E.*`（21 处调用点）、`C.CLASSES`/`C.MONSTER_SKILLS`/`C.resolve`（3 处）、`"战士"`/`"攻击"`/kind 字面量（7 处）、2 处死 import、`load_game_defaults` 全部改走 `config` 注入挂载点 —— 这一步完成后引擎才具备「换配置=换游戏」的物理条件。
> 2. **S2 固化公开 API 面**：25 个被消费符号 + 5 个私有符号升级 —— 内容层不再依赖引擎内部结构。
> 3. **S3 通用件归位**：`formula_expr` / `formation` / `skill_kinds` / `battle_bars` 迁入引擎（旧路径留 shim）。
>
> 三步之后才是 S4 起的**物理搬迁**（改名 → 拆 `engine.py` → 内容层重组 → 单一装配入口 → submodule 拆仓库 → 收口），每一步都以「241 绿」为闸门。
>
> **一句话**：先做 S1–S3 的「断反向边 + 固 API + 通用件归位」（不动目录、可逐 commit revert），再谈 submodule 物理分离；直接 `git mv` 会带着 15 条反向 import 边一起进 submodule，等于把耦合换个地方放。

---

### 附：关键文件行号索引（供实施期快速定位）

| 项 | 位置 |
|---|---|
| 反向边 R1/R6/R8 | `game/battle2/actions.py:16,726,758`（+ 调用点 `112,347,472,484,492,494,508,511,513,594,622,691,708,710,729`） |
| 反向边 R3（内容表直读） | `game/battle2/actions.py:35-42` |
| 死 import | `game/battle2/actions.py:17,727` |
| 反向边 R9/R10 | `game/battle2/battle.py:120-137` |
| 反向边 R11 + R13 | `game/battle2/stats.py:16,96-105`（默认值在 `:97`） |
| 位置不合规 R12 | `game/battle2/config.py:33-39` |
| 引擎 kind 常量 | `game/battle2/actions.py:22-26` |
| 装配调用点（6 处） | `commands/combat.py:621,622,2808,2851`；`commands/tower.py:151,156` |
| 配置装载点 | `commands/battle_item_use.py:52`；`data/battle_rules.py:9` |
| 内部串联（2 处） | `services/class_mech_proc.py`（`apply_class_mech` 尾段；行号随并发改动漂移：侦察时 L2143/2149，其后 L2303/2309） |
| 测试 path 模板 | `tests/conftest.py:16-38`；单测样板见 `tests/test_battle_n3_effects.py:17-34` |
| 回归入口 | `scripts/run_all_tests.py`（`PLUGIN_DIR` 推导 `:46-48`、`SERIAL_SLOT` `:58-61`） |
| 循环导入已知点 | `core/battle_bars.py:30-31`；`core/__init__.py:59-61,66-67`；`services/__init__.py:11` |

> ⚠️ **行号时效**：本档全部行号取自 `HEAD=780720b` 的只读侦察快照（2026-09-11 00:10–00:23）。
> 侦察期间检测到**并行 agent 正在改动** `game/data/battle_rules.py` 与 `game/services/class_mech_proc.py`（00:24–00:25 落盘），
> 故这两个文件的**行号已漂移**（`class_mech_proc.apply_class_mech` L2041→L2201、内部串联 L2143/2149→L2303/2309）。
> **引擎侧（`game/battle2/*`）全部锚点未变**，反向依赖边与残留结论不受影响。实施期以符号名检索为准，勿硬编码行号。
