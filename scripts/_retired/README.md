# scripts/_retired —— 已退役的宿主开发侧脚本

> **退役 = `mv` 到本目录（不是删除）**：文件仍在 git 里可见、可 diff、可随时 `mv` 回去。
> 本 README 由 **两条线合并**而成（2026-09-14）：
> * 批 1（导出器 / 域插件）＝ 导出器线（主 agent，12:39–12:40 搬入）；
> * 批 2（离线工具 14 个）＝ MIG 线（12:5x 搬入）；
> * 两版 README 曾互相覆盖，**本版 = 合并版**：MIG 的逐条退役理由 + 导出器线的**语义账与改数据流程**（下面 §1.1）。

---

## 批 1 · 导出器 / 域插件（2026-09-14 12:39–12:40）

| 条目 | 原位置 | 说明 |
|---|---|---|
| `export_game_package.py` | `scripts/export_game_package.py` | 2,979 行宿主导出器（189,885 B / 2026-09-13 18:08 版）。真源（宿主 `game/data/*.py`）已删 ⇒ 无源可派生，整体退役 |
| `export_game_package.py.bak_b14` | 同上（备份） | 退役当刻原文备份 |
| `verify_package_coverage.py.bak_b14` | `scripts/verify_package_coverage.py`（备份） | 该文件**仍留在 `scripts/`**（已重写为纯包内校验）；这里只是备份 |
| `export_domains/`（17 个文件） | `scripts/export_domains/` | 域插件目录（一个域一个 `.py`，暴露 `DOMAINS = {"<域>": derive_<域>}`）；**自带一份 `README.md`** 说明设计意图 |

### 1.1 ★ 导出器里的语义账（退役后仍然有效，别丢）

这些是对**包内数据**的解释，独立于工具本身：

1. **items 是合表：900 条不是 1704 条**。`ITEMS = dict(MATERIALS)` + `update(CONSUMABLES)` + 若干 `ITEMS.update({...})`；
   `MATERIALS`(598) 与 `CONSUMABLES`(206) 的每个 key 都在 `ITEMS` 里且是同一对象 ⇒ 「900 + 598 + 206」是同一批条目
   按表重复计数（重复量 804）。包内 `content/data/items.json` = **900 条**（合表后的最终态），由
   `tests/test_export_package_sync.py` 冻结。
2. **price 是覆盖后的最终价**：`MATERIAL_PRICE_OVERRIDE`（219 条）在 import 期就地覆盖，而 `ITEMS` 在覆盖之后才构造
   ⇒ 导出的价 = 覆盖值，**不是**源码字面量的旧价。
3. **按名索引不是数据源**：`MATERIALS_BY_NAME`（598 条）是索引、零新信息，不进包。
4. **外层键序 = 字典序**（导出契约 `sort_table`）；源**插入序**参与行为的地方（如配方检索的首次命中、
   鱼池抽样、探索池）用条目内 `seq` 字段显式保存并在读口还原 —— 见 `content/craft.py` / `content/fishing.py` /
   `content/events.py` 的门面注释。
5. **已知非逐字可逆投影（I3 反例，登记在案）**：`maps`（`nodes`/`roles` vs 宿主 `subareas`/`alias`）、
   `items`（迭代序 = 排序键序）、`craft`（外层键字典序 vs 源插入序）。这三处「迁移前必须先补等价」
   在 `ORLANDIA_终态执行计划.md` §7 风险 5 与 §9.2 I3 有登记。

### 1.2 现在改数据该怎么做（B14 开关之后的标准流程）

1. **改数据**：直接编辑包内 `games/orlandia/content/data|rules/<域>.json`，或用编辑器 UI（域 tab 全量可编）。
   **禁**手写宿主 `game/data`（该目录已不存在，只留 4 项资产：`command_specs.json` / `text_specs.json` /
   `tlogs.json` / `t2i_templates/`）。
2. **跑门禁**：
   * `python scripts/verify_package_coverage.py --check` → 域清单四方一致 / 落点 / 条数>0 / 逐条过 schema / 无孤儿文件；
   * `python tests/test_export_package_sync.py` → items 冻结规模 + 落盘规范 + 清单一致；
   * 碰数值/战斗：`python scripts/run_numeric_tests.py`。
3. **落盘规范**（编辑器保存自动满足，手改时照着来）：UTF-8 无 BOM · LF · `indent=2` · 末尾换行 ·
   外层键**升序**（插入序请用条目内 `seq`）。

> 批 1 的归属与去留由**导出器线**（主 agent）决定；MIG 线只登记，未做判断或改动。

---

## 批 2 · 离线工具（MIG 线，2026-09-14 12:5x 搬入，14 个）

宿主 `game/data/*.py` 于 2026-09-14 全删（74,707 行 / 87 文件）——全部内容搬进内容包
`framework/games/orlandia/`（域 JSON 在 `content/data/`，门面在 `game/content.py`）。
删表后这些脚本的 `import game.data.*` 全部 `ModuleNotFoundError`；逐个复核后判定
**产物已固化进包内域 JSON / 口径已被后续重构取代 ⇒ 重跑无意义**，故退役而非改取件。
（仍值得重跑的 14 个已就地改成读包内同源，见 `overnight/W-MIG.md`。）

判据：
1. **生成器**：产物（原 `game/data/*.py` 里那些表）现在住在包内域 JSON，重跑只会写出一个**宿主已不存在**的文件；
2. **一次性调研 / 分析**：脚本文档自述「一次性工具」，结论已固化进设计文档 / 已并入版本实现；
3. **口径已被取代**：依赖已删的**旧战斗引擎 `game/battle.py`**（379a792「v181.N10-C 删旧」删掉 11,000 行），
   或依赖已并入其它域的战役数据（`mesh_rooms_*` 三域已并入包内 `content/data/subareas.json`）。

| 文件 | 类型 | 退役原因 | 产物 / 结论现在在哪 |
|---|---|---|---|
| `gen_subareas.py` | 生成器 | 生成 `game/data/subareas.py`（子区域拆分表） | 包内 `content/data/subareas.json`（628 子区域） |
| `gen_instance_stages.py` | 生成器 | 为副本补 `stages` 层结构 | 包内 `content/data/instances.json`（27 副本 stages 已固化） |
| `gen_monster_formulas.py` | 生成器 | v157 批量生成怪物技能 `formula`（143 条） | 包内 `content/data/monsters.json` / `monster_roster.json` |
| `gen_skill_formulas.py` | 生成器 | v157 一次性补齐 129 个伤害技能 `formula` | 包内 `content/data/skills.json` |
| `gen_skill_exprs.py` | 生成器 | v161 生成技能 `exprs` 表达式（样板：战士+法师） | 包内 `content/data/skills.json` |
| `gen_doc_rooms_v115.py` | 生成器（文档） | 按实际数据打印野外图房间列表，供设计章手工同步 | 设计章已定稿；数据看 `content/data/subareas.json` |
| `gen_drop_pools.py`（原在仓根） | 生成器 | 从「老数据」全量生成 `game/data/drop_pools.py`；老数据本身已不在仓 | 包内 `content/data/drop_pools.json`（596 池） |
| `analyze_instance_mats.py` | 一次性分析 | v115 副本专属材料价值核查（文档自述「一次性工具」） | 结论已进设计报告 |
| `analyze_instance_mats2.py` | 一次性分析 | 同上 v2（按 mat_id 全链查询） | 同上 |
| `analyze_instance_rewards.py` | 一次性分析 | v115 副本通关奖励 + 锻造产出等级 | 同上 |
| `probe_v117.py` | 一次性调研 | v117 前置调研：装备模板/强化石/药剂/附魔消耗 | v117 已实现（`equip_roster.json` / `enhance_table.json` / …） |
| `probe_v117b.py` | 一次性调研 | v117 前置调研 2：同名装备/食物/附魔/符文途径 | 同上 |
| `audit_mesh.py` | 一次性战役审计 | v115 网状子区域战役的「基线 vs 新增」对拍：B/G 组直接读已删宿主源码文本与已并域的 `mesh_rooms_*` 三模块 ⇒ 语义无法平移到包内域 | 战役数据已并入 `content/data/subareas.json`；域形状由 `schemas/subareas.schema.json` 守 |
| `sim_audit_a4.py` | 一次性数值审计 | Audit A4 的 CTB 口径锚在**旧战斗引擎** `game.battle`（`BASE_DELAY`/`SPD_CT_CAP`/`Battle(..., player=)`），该引擎已随 379a792 删除；现引擎 CTB = `saintess_engine/battle/schedule.py` 绝对时刻模型 ⇒ 结论口径已失效 | 现行 CTB 数值门禁 = `scripts/run_numeric_tests.py` + `scripts/numeric_lib/*` |

---

## 想复活某个？

1. `git mv scripts/_retired/<f> scripts/<f>`（生成器要改**输出路径**：写包内
   `framework/games/orlandia/content/data/<域>.json`，而不是宿主 `game/data/*.py`）；
2. 取件统一走 `game.content`（`import game.content as C` / `from game.content import 名字`）——
   `C.<大写名>` 名字面与删表前**逐名相同**（B14 门禁 `overnight/b14_catalog_gate.py` 证）；
3. 若还需 `Battle` / 战斗常量：`from saintess_engine import Battle` + 包内 `content/constants.py`
   （宿主 `game.battle` 已在 379a792 删除，别照旧 import）。
