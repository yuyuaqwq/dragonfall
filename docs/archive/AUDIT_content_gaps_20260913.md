# 审计：包/数据侧发现的「需内容侧拍板」项（2026-09-13）

> 来源：把奥兰迪亚真数据做成引擎包（18 域 / 4189 条）过程中逐域研究 + 独立复核。
> 这些**都不是**导出/包的问题（包忠实搬运了真源）；它们是**游戏仓自己的数据/机制缺口**，
> 改哪一条都是「内容侧语义决定」，所以只登记 + 给建议修法，**没有被静默修掉**。
> 每条都写了 可复现的定位（文件:行号或命令）；带 ⚠️ 的是**玩家可见**的问题。

---

## ⚠️ 1. 93 条传说专属特效**没有任何行为挂点**（展示有、实战不生效）

- 位置：`game/data/affixes.py:548` 的 `LEGENDARY_EFFECTS`（93 条）
- 事实：按 id 分派的翻译器表 `game/services/battle_equip_proc.py` 的 `_AFFIX_TRANSLATORS`（33 条）
  与 93 个特效 id **交集 0** → 这些特效的字段（`extra_atk` / `lifesteal` / …）**没有任何代码读**
- 玩家看到的：装备详情里那行「✨ 专属·影袭连刺：暴击后 50% 概率追加一次 40% 伤害的追击…」
  照常显示，但**不会发生**
- 影响面：橙装（`legendary` 字段引用这批特效）的专属效果全部只有文案
- 建议（内容侧决定）：
  1. 给这 93 条补翻译器（= 机制工作，一条要定「触发时机 + 数值怎么落到引擎钩子」）；
  2. 或短期内先**不要在文案里承诺**（去掉详情展示 / 标注「未实装」）。
- 本审计不改任何数据：补行为是设计活，删文案是产品决定。

## 2. 那 1 条越界 `trigger="on_crit"`

- 位置：`game/data/affixes.py:1017-1021`（`LEGENDARY_EFFECTS` 最后一条，「影袭连刺」，越界值在 `:1018`）
- 为什么越界：合法 `trigger` 表（三份副本）都不含 `on_crit`；`on_crit` 只在**另一处**合法 ——
  `battle_equip_proc.py:518-528` 的 `_AFFIX_RES_GAIN_ON` 映射的是 **`effect.on`（内层字段）**，
  不是顶层 `trigger`（两者别混：`affixes.py:368/412` 是合法用法）
- 修法 A（数据）：`on_crit` → `on_hit` —— 语义变宽（「暴击后」变「命中后」）→ 触发频率上升；
  若要保持强度应同步把 `chance` 从 0.50 降到贴近「暴击率×0.5」的档（如 0.15~0.25）并改 `desc`
- 修法 B（机制）：内容侧给战斗补一条 **crit 触发链**，保持原语义
- 不要做的：在框架 schema 的 `trigger.enum` 里加 `on_crit` —— 那是把内容侧时机抄进框架，
  且战斗侧仍无挂点（只把红变绿，不改行为）

## 3. 4 件道具的召唤 `tid` 指向**不存在**的模板

- 位置与值：`game/data/items.py:3292-3295`
  `i_jin_ling_xiang_lu → ember_wisp` · `i_sheng_hui_ti_shen_xiang → holy_totem` ·
  `i_jing_ji_kui_lei_zhong → thorn_golem` · `i_zhan_di_yi_zhe_mo_ou → medic_golem`
- 事实：这 4 个值**既不在** `game/data/pets.py` 的 `PET_POOL`（16 条，键是 `pet_*`），
  **也不在** `game/data/summons.py` 的 `SUMMONS`（5 条：`skeleton/vine_guard/treant/fire_elemental/thunder_elemental`）
  → 语义是「召唤物模板 id」，但目标表里都没有这些 id（**休眠/失效字段**）
- 后果：这 4 件道具的 `effect: summon` 永远召不出东西
- 建议：① 改成 `SUMMONS` 里已有的 id（要选一个语义接近的）；或 ② 承认不生效、删 `tid`（但道具文案若承诺了召唤，要一起改）

## 4. 11 个被动 proc 名被技能引用、但**没有声明**（同域双真源）

- 事实：`game/data/battle_rules.py` 的 `PASSIVE_PROC`（42 条声明）**不是**唯一真源 ——
  `game/core/passive_procs.py` 的 `PROC_FAMILIES` / `KNOWN_GAPS` 与 `game/services/class_mech_proc.py`
  的旁路各自认一批名字；两边并集后仍有 **11 个**被技能引用却没进声明表
- 影响：包内 `passive_proc` 域显示 42 条，技能引用里有 11 个悬空（编辑器给不出候选）
- 建议：把两份表收敛成一份（声明表是权威，旁路改成查表）→ 11 个补齐；这是**内容侧合并**，不是导出问题

## 5. 「链舞」是被动语义、但永远装配不上

- 位置：`game/data/skills.py:2815`（`kind=物理`，却带 `passive.proc=finisher_up`）
- 事实：装配器只扫 `kind=被动` 的技能（`game/data/battle_rules.py:631-632` 明写）
  → 这条技能的被动**运行期从不装配**（源侧即有的事实，非本次引入）
- 建议：要么把这条技能的 `kind` 改成被动（若它本来就是被动），要么把 `passive` 字段摘掉（若设计上是主动技）
  —— 两者都改行为，需拍板

## 6. POI 双份数据：`instances.stages[].poi_data` vs 新 `pois` 域

- 事实：新域 `pois`（457 条挂载表）的取值源是 `game/data/dungeon_pois.py` 与 `mesh_rooms_*.py`（**权威**）；
  副本域里 `stages[].poi_data` 是**内联副本**（同一个 POI 两份），实测字段逐值一致（55/55）
- 影响：目前无错，但两份会漂（改一处忘另一处）
- 建议：后续单独做一次迁移（`stages[].poi_data` 改成引用 `pois` 域的键），迁移需要**冻结比对门禁**；
  不建议顺手做（涉及副本运行期数据流）

## 7. 怪物**重名 10 例** → 按名查 id 会歧义

- 事实：运行期索引 `game/data/_assembly.py:207-253` 的 `_INDEXES["monsters"]` 建的是
  `name→id(345) / id→name(354)`，重名时规则是「`SUBAREAS` 先、同名首个胜出；`INSTANCES.stages` 后、同名**无条件覆盖**」
  → 有 10 个中文名对应多个 id，**静默取了一个**
- 影响面：运行期不直接 `roll("mon:…")`（`mon:`/`elite:` 池键只被导出器/审计/生成器消费）
  → 目前不会导致玩家拿到错的怪；但**工具链按名解析时可能指错怪**
- 建议：名册域（`monster_roster`，实现中）会把「名字 → 多个 id」如实暴露；
  运行期索引的「首个胜出/覆盖」规则建议显式化（或加一条门禁把重名清单钉住，别人改动时能被抓住）

---

## 附：怎么复现/复核这一份

```bash
cd C:/Users/yuyu/qqbot/data/plugins/dragonfall
# 1) 特效翻译器与特效 id 的交集（应输出 0）
python -c "import sys;sys.path.insert(0,'.');from game.services import battle_equip_proc as P;from game.data import affixes as A;print(len(set(P._AFFIX_TRANSLATORS)&set(A.LEGENDARY_EFFECTS)))"
# 2) 越界 trigger
grep -n 'on_crit' game/data/affixes.py
# 3) 4 件道具的 tid 与两表键空间
python -c "import sys;sys.path.insert(0,'.');from game.data import pets as P, summons as S;print(sorted(P.PET_POOL)[:5], sorted(S.SUMMONS))"
# 4) 重名清单（名册报告 §2 / 实现报告里有全量）
```
