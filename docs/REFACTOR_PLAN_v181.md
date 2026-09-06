# v181 架构审计落地批次（P0→P1 首批：纯搬移 + 数据收口）

> 触发：鱼鱼 2026-09-07 完成 26 子 agent 全项目架构审计（起点 HEAD b4f0239=v180G，报告在
> `_archive_unused/architecture_audit_20260907/`，主汇总结论 docs/ARCHITECTURE_AUDIT_20260907.md）。
> 铁律：重构≠改数值（行为零变化，明确 bug 修复除外）；每批 commit；门禁护航；策划案同步。
> 现状：工作区干净，master @ 553b7fe（审计索引入库后）。

## 审计总建议改造顺序（P0→P5）

| 阶段 | 内容 | 风险 | 备注 |
|---|---|---|---|
| P0 | 纯搬移：engine BRANCH_BONUS_BY_CLASS/MECH_STACK_MAX/TIER_GROWTH 下沉 data | 低 | 消除"换职业改代码"两大点 |
| P1 | 数值收口：battle.py/commands 300+ 字面量兜底清零、双源合一 | 中 | 分文件批 |
| P2 | 注册表收编：被动 proc 反射化、weapon 79→10 执行器、battle_config 职业命名 CFG→MECH_CFG 单表 | 中 | 每批一个注册表 |
| P3 | 玩家状态容器收尾：scalar 槽收纳 p_meta + Battle 实例残留字段迁 actor dict | 高 | 需先补行为快照测试 |
| P4 | 命令层抽 services（BattleSettlement/Quest/Shop/Crafting/Profession…） | 中 | 按审计清单逐个 |
| P5 | battle 拆类 | 高 | 最后做，先白盒黑盒化 |

本计划 = **P0 全部 + P1 首批（battle.py 套装/种族后门）**，为后续 P2-P5 铺安全路。

## P0 详细拆解

### P0-A engine 三表下沉 data（所有权 engine.py + data/battle_config.py）

现状（game/engine.py 模块级硬编码，换职业/新 mech 要改代码）：
- L15 `TIER_GROWTH = {0:1.0,1:1.15,2:1.30,3:1.50}`
- L19-22 `BRANCH_BONUS = {1:{...},2:{...}}`（通用回退档）
- L25-54 `BRANCH_BONUS_BY_CLASS`（7 职业×2 分支属性倾向）
- L157-173 `MECH_STACK_MAX`（15 mech 上限）

方案：
1. `data/battle_config.py` 追加纯数据表 `TIER_GROWTH`/`BRANCH_BONUS`/`BRANCH_BONUS_BY_CLASS`/`MECH_STACK_MAX`
   （搬原值，注释标注迁移来源 v181）
2. `engine.py` 删除本地定义，改 `from .data.battle_config import ...`（对外 `E.TIER_GROWTH` 等名字不变）
3. 消费点检查：E.TIER_GROWTH（commands/world.py:4091）、E.mech_stack_gain 内部引用、E.BRANCH_BONUS_BY_CLASS（engine.py:202）
4. 门禁：全量跑 numeric + run_all（此批纯搬移，预期零行为变化）

验收：
- [ ] `E.TIER_GROWTH`/`E.BRANCH_BONUS`/`E.BRANCH_BONUS_BY_CLASS`/`E.mech_stack_gain` 行为不变
- [ ] engine.py 无本地三表定义（只有 import）
- [ ] 全量回归零新增红

### P0-B skill_up.py 中文 key → 稳定 id（所有权 data/skill_up.py，独立子任务）

现状（审计报告 2 §五 ① 最脏数据层）：SKILL_UP 用中文技能名做 key，628 个赋值中 160 组同名重复
（112 组同名不同值），撞名互相污染，engine 靠"最后一行"侥幸。⚠️ **此任务必须先侦察后动手**——
改 key 会影响 engine `_skill_up` 查询（engine.py:827-836）、tests、以及基础/分支/导师技能引用方式。
属高风险数据迁移，需要先列全量映射表再改，另开会话单做（放 P0-B 观察项，不并行派）。

### P0-C battle_config 职业命名 CFG 死表清理（所有权 data/battle_config.py，独立子任务）

审计 2 §四：battle_config 90 常量仅 7 个被 import 引用，~30 个零消费死表（BARD_DAWN_HYMN_POWER/
COMBO_REFLOW_*/BONE_RUSH_CFG/SHAKEN_CFG/CURSE_CFG/GUARD_CORE_CFG/ZEN_HOLD_CFG/MAGE_FOCUS_CFG…）。
⚠️ 需 AST 扫描核对"零消费"再删（数值可能以技能字段/注释形式硬编码在 skills.py/battle.py）。
风险中：误删被消费常量 = 运行崩。先出清单给人确认，不直接删。

## P1 首批：battle.py 内容硬编码后门清除

按审计报告 0（battle.py 58 内容方法）+ 报告 22（300+ 字面量）拆分，每子任务 = 一个"后门族"，
独立文件所有权，互不冲突：

### P1-A 套装中文名后门（battle.py）
- L195 `"星尘" in set_bonus_5`（星尘 5 件夜间回蓝）→ 套装 effect 声明驱动
- L5995 `E.has_set(...,"圣光套")` 中文名 → 套装 effect 声明
- L5728-5732 `_affix_element_dmg` `"月语"/"海神"/"苍穹" in s5` → bonus_5 数据声明（冰/雷元素伤）
- 同族：报告 22 B1 表套装直连 if（157-170 regen/regen_strong、216-252 圣堂领域、5992-6051 布甲/圣光/永恒、8927/9043 星尘、10644-10649 龙鳞反震、10651-10656 金身 iron、10695-10712 圣徽守护/圣辉圣环）

### P1-B 职业 if 特判族（battle.py）
- L1736 `class_name=="cls_fa_shi" and path==1`、L2315 `==cls_wu_seng`、L2741 `!=cls_mu_shi`、L5397 `==cls_wu_seng`
- L10736 不灭意志/死亡池 0.35 等特效武器数值（10729-10811 复活族）

### P1-C 被动乘区本地兜底（battle.py）
- L4812-4864 4 职业被动暴击本地门槛 → 被动配置读
- L6803-6907 一串被动词条默认值 → _ps.get 兜底改读数据
- L6909-6930 暴击率合成 / 幸运转化

### P1-D 种族后门 + 常量下沉（battle.py → data/races.py）
- L57-58 RACE_BERSERK_MULT=1.20 / RACE_TIMID_MULT=0.90 + L5446-5469 `_race_attack_mult` 标签"🔥无畏/😰怯战/🐲龙之吐息"
- L62 UNDEAD_KEYWORDS + L5236 `tid=="skeleton"` → data 单源

### P1-E 战斗入口/模式注册表化侦察（只读，不派）
审计 25：btype 39+31 硬分派无注册表——改动面大，先只读侦察输出方案，不直接改（避免并行踩雷）。

## P2 注册表收编（第二批，第一批 merge 后才开）

### P2-A class_sets 表下沉 data（纯搬移零逻辑，风险最低，先做）
现状（审计报告 1 §六）：core/class_sets.py `_SERIES_SET_BONUS` L20-157 = **9 系列+16 套具体套装全部数值与敌人关键词表**（橡木/铁港/圣光/霜狼/铁皮/精铁/百炼/学徒/符文/秘法/布衣/祝福/圣堂/猎手/风行/暗夜/轻影/夜行/行者/石拳/壁槌/护林/渡口/巡林/霜猎/龙裔 等），含 `class: cls_*` 职业绑定——这是整套 data/sets.py 同构的具体配置躺在 core。
方案：
1. 建 `game/data/set_bonus_data.py` 纯数据表（原值搬移）
2. core/class_sets.py 删 `_SERIES_SET_BONUS` 内联表，从 data import；`_build_class_sets()` 装配器保留 core（或下沉 _assembly）
3. 门禁 + commit：`v181.P2A class_sets 套装表下沉 data/set_bonus_data.py（纯搬移）`

### P2-B battle.py 引擎常量 → core/constants.py（消除 core→battle 反向引用）
现状（审计报告 1 §四/五）：weapon_effects.py L37 **顶层** `from ..battle import ACT_TICK` + battle_mech.py 六处函数内 `from ..battle import DEBUFF_TURNS/BUFF_TURNS`（L329/814/895/903/911/949）+ race_talent_display L93/101 取 RACE_*_MULT —— core → battle 反向 import 5+ 处。
方案：
1. ACT_TICK/SPD_CT_CAP/BASE_DELAY/BUFF_TURNS/DEBUFF_TURNS/RACE_*_MULT 等引擎刻度常量收进 core/constants.py
2. weapon_effects.py L37 顶层反向引用删除（改从 constants import）——优先级最高
3. battle.py 保留对外名字（`from .core.constants import ...`），battle 内引用不变
4. 门禁 + commit

### P2-C weapon_effects 79 key → 通用执行器 + 数值读表（weapon_effect_data 已建权威表）
现状（审计报告 1 §三/六）：weapon_effects.py 1463 行 ~96 个 handler 全是具体特效装备名；docstring L25-29 自认"部分特效数值写在 special 文案，为可控实现，数值以本文档 handler 内 DEFAULT 为准"——**绕开数据层**。数值权威表 weapon_effect_data.py（130 行）已存在但未全接。
⚠️ 此任务改动面大（1463 行文件重构），且直接触碰战斗特效行为——**单线做**，侦察产出"数值表 vs handler DEFAULT 差异清单"后逐族改。行为零变化铁律（数值有差异时以现状 handler 为准写进数据表，不改变行为）。

### P2-D 被动 proc 反射化注册表（消灭 34 处散点 if）
现状（审计报告 6 §七）：52 个 passive proc 中 34 个有引擎消费点，消费点**散在 battle.py 各挂点手工 if**（_passive_crit_bonus/_skill_passive_dmg_bonus/_deal_damage 等），12 个 proc 无消费点空转；加新被动类型须人工逐个接线。
方案（仿 MECH_EFFECTS/affix formula 注册表模式）：
1. core 建 `passive_procs.py` 注册表：proc 名 → handler（参数化：读 player 被动数据 + actor 上下文）
2. battle.py 各挂点改为查注册表（消灭散点 if），无注册 = 不触发（"配置缺字段=无此行为"）
3. 先出"52 proc → 34 消费点 → 12 空转"全量映射清单，逐个核对 handler 与原逻辑等价
⚠️ 与 P1-C（被动乘区本地兜底）改动面重叠——**必须等 P1-C merge 后才开**。高风险，需配套行为快照测试（先黑盒后重构，见审计 21 建议）。

### P2-E battle_config 职业命名 CFG → MECH_CFG 单表（消灭双源与死表）
现状（审计报告 2 §四）：battle_config ~40 常量以职业/流派命名（BARD_BRANCHES 硬编码中文分支名、SHADOW_STEP_CFG、ECHO_CFG、COMBO_CFG 带 class_id 等）；~30 个零消费死表（AST 扫描 90 常量仅 7 被 import）；同一机制字段 classes.py/core_resources/battle_config 三处并存无双源权威。
⚠️ 需先 AST 扫描核对"零消费"（数值可能以技能字段/注释硬编码在 skills.py/battle.py）。出清单给人确认再删。**侦察先行，改动单线**。

## 分批派工（文件所有权互斥）

| 批次 | 子任务 | 所有权文件 | 风险 |
|---|---|---|---|
| B1 | P0-A engine 三表下沉 | engine.py + data/battle_config.py | 低 |
| B2 | P1-D 种族后门下沉 | battle.py + data/races.py | 低 |
| B3 | P1-A 套装中文名后门 | battle.py + core/class_sets.py + data/sets.py | 中 |
| B4 | P1-C 被动乘区兜底 | battle.py | 中 |
| B5 | P1-B 职业 if 特判族 | battle.py | 中 |

**冲突矩阵**：B1 只碰 engine.py/data/battle_config.py；B2/B3/B4/B5 都碰 battle.py —— ⚠️ 同文件并行冲突！
**调整**：battle.py 的 B2/B3/B4/B5 **串行**或按改动行号分区后主 agent 合并。**推荐：B1 单独先派，
battle.py 各族收口各派一个子 agent 侦察 + 产出补丁，主 agent 逐个合并**（符合记忆"同文件并行=独立新文件+主 agent 合并"）。

## 门禁（每批必须）
- 改动文件 py_compile 过 + 相关单测绿（`"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe" tests/test_xxx.py`）
- 每批独立 commit：`v181.A 内容描述（做了什么+验证结果）`
- 全量最后跑（所有批完成后）：`python scripts/run_all_tests.py`（不动源文件）

## 策划案同步
- 架构层迁移属"代码重构"，策划案（design/new_world/）不改数值/玩法 → 同步 commit 说明即可。
- 若 P1 收口改变任何对外数值 → 回写 32_数值设计.md 对应条目（本批预期零数值变化）。

## 安全网
- git 干净起步 ✓（master @ 553b7fe）；每批 commit 可回退
- numeric 51 文件 + run_all 318 作行为网
- refactor_regression 基线 docs/refactor_baseline_v176.json 可对比（P3+ 拆类前才需要）
