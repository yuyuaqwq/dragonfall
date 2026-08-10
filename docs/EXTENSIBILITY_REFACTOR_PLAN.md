# 《剑与魔法》可扩展性重构设计文档（v98 系列）

> 日期：2026-08-10
> 背景：v97 系列已完成事件/规则/道具三大模板引擎（数据驱动化示范）。本次按 2026-08-10 全模块扫描结果，系统性消灭剩余硬编码分发。
> 原则：**行为零变化**（重构不改数值/文案/概率），测试兜底，全量回归后台跑。

---

## 一、问题清单（扫描定位）

### P1 战斗机制巨型 elif 链（最高风险）
- `battle.py:1421-1600`：mech 机制 32 分支 × 15 个函数体（rage/shield/burn/freeze/stun/silence/mark/wind/arcane/spellblade/judge/shadow/poison/chi/iron/bless_shield…）
- `battle.py:1313-1380`：ctype 触发条件 22 分支 × 7 个函数体（enemy_hp_low/player_shield/player_buffed…）
- `battle.py:1637-1651`：词条效果 6 分支（frost/burn/thunder/pierce/lifesteal_set/execute）
- **扩展成本**：每加 1 个机制 ≈ 改 15 处 elif；加 1 个条件 ≈ 改 7 处

### P2 命令层硬编码数据表（纯搬移，零风险）
- `economy.py:66-173` `_GATHER_MAP_POOLS`：61 图采集物绑定表（~500 行）
- `economy.py:32-41` `PROF_TUTORS`：副业导师表（与 data/npcs.py 重复维护）
- `economy.py:820` `DAILY_PROF_TASKS`：每日副业任务
- `economy.py:174` `_PROF_WAIT_BASE`：等待型副业时长
- `economy.py:29` `BAG_FILTER_TYPES`：背包过滤类型

### P3 魔法字符串 `"oak_town"` 散落（8 处 + SQL）
- `store/players.py:69`（建号 SQL 默认值）、`combat.py:1494/2037`、`instance.py:1197`、`player.py:201-203`、`world.py:331`、`item_templates.py:191`、`economy.py:62/2945`
- 连带：建号默认 gold=50/attr_pts=9/stamina=100 写死在 SQL 字符串

### P4 中小分发链（模板化收益明确）
- `economy.py:1822-1860` 称号效果 tid 23 分支
- `player.py:371-390` 种族天赋 k 12 分支
- `core/dialogue.py:72-114` 对话条件 need 13 分支
- `social.py:853` 世界事件 etype 6 分支
- `combat.py:278` 环境关键词元组（forest/water/ruin → 隐藏怪 cond 判定）

### P5 魔法数字
- `battle.py` 词条触发概率 ~15 处（0.75/0.20/0.25/0.15/0.10…）→ affixes 数据字段
- `combat.py:95-202` 遇怪概率（0.35/0.05/0.5）→ maps 数据字段
- `economy.py:1234-1242` 配方等级阶梯 10/30/50/70/90

### P6 架构模式（远期，本期不做）
- 145 个 `@filter.regex` 分散注册，无集中命令表 → 帮助菜单手写漂移（misc.py）

---

## 二、阶段方案（按风险从低到高）

### v98.1 数据下沉（P2）—— 纯搬移，零行为变化
新建 `game/data/gather_pools.py`、`game/data/prof_tutors.py`，把 economy.py 的 4 张表搬过去，
data/__init__.py 聚合导出；economy.py 改为引用。验收：采集/副业/每日任务相关测试全绿。

### v98.2 魔法字符串收敛（P3）—— 常量 + 数据字段
- `game/core/constants.py` 新增 `START_MAP="oak_town"`、`START_SUBAREA="oak_town_1"`、建号默认值常量
- 8 处 oak_town 替换为 START_MAP；players.py SQL 改为参数绑定
- `data/maps.py` 给地图加 `default_*` 字段（如死亡复活点优先读地图数据，回退常量）
验收：死亡复活/回城/建号路径测试全绿。

### v98.3 小分发链模板化（P4）—— 照 v97.3/v97.7 模板模式
- 称号效果：`core/title_templates.py`（TEMPLATES 注册表，tid → 函数）
- 种族天赋：`core/race_traits.py`（trait key → 计算函数）
- 对话条件：`core/dialogue_conds.py`（need key → 判定函数）
- 世界事件：`core/world_event_templates.py`
- 隐藏怪环境判定：HIDDEN_MONSTERS 数据加 `env` 字段（forest/water/ruin/night…），删 combat.py 关键词元组
验收：称号/种族/对话/世界事件相关测试全绿。

### v98.4 战斗机制注册表（P1）—— 最高风险，最后单独做
- `core/battle_mechs.py`：`MECHANICS = {"rage": fn(state, mval), ...}` 注册表
- `core/battle_conds.py`：`CONDITIONS = {"enemy_hp_low": fn(state, player), ...}` 注册表
- battle.py 的 15 个 elif 函数体改为查表调用（保持每个机制函数体原样搬移，只改分发骨架）
- 词条效果 → affixes 数据加 `trigger` 字段 + `core/affix_effects.py` 注册表
验收：battle 相关全部测试（test_v83_boss_mech、test_v87_spellblade、test_v85_pvp…）逐条通过；
全量回归必须后台跑满 2 次确认稳定（随机性高）。

### v98.5（可选，远期）命令注册表 + 帮助自动生成
集中 `COMMANDS` 表（regex、分类、帮助文案、handler），帮助菜单自动生成。

---

## 三、测试与回归策略

1. 每个阶段独立提交，提交信息标注 `v98.x`
2. 阶段内：相关测试单跑 → 全量后台跑（`run_all_tests.py`，~5 分钟，notify_on_complete）
3. **全量跑期间绝不改源文件**（吸取 v97.5 教训：跑全量时改代码导致中间态误判）
4. v98.4 前先冻结 battle 行为快照（跑 3 次 test_v83_boss_mech 等随机测试确认基线）

## 四、验收标准

- 所有既有测试全绿（74+ 文件）
- 新增 2-3 个测试验证注册表扩展性（注册新机制/新称号 = 一行注册，零改动分发骨架）
- git log 每个 v98.x 一个干净提交
