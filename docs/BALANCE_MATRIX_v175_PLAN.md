# 职业×流派×副本全量平衡门禁设计方案（v175）

> 状态：**待鱼鱼确认**（2026-09-04）
> 触发：鱼鱼"现在的职业数值模型还是差了点意思……希望验证每个职业每个阶段各种玩法之间的平衡性，要更复杂的数值模型门禁"
> 铁律来源：MEMORY「数值不许拍脑袋必建模+门禁」；「playtest闭环」；「文档权威=策划案；数值权威=32_数值设计.md」

## 0. 一句话

把现有"每职业 1 代表技能 / 纯普攻 / 单一加点"的粗糙门禁，升级为
**7 基础职业 × 3 流派 × 典型加点组合 × 技能强度/资源/CD/速度/联动全审计 × 22 副本 Boss 全扫**
的双引擎（期望快速筛 + 真引擎最终验）平衡矩阵门禁。

## 1. 现状盘点（已核实，代码证据）

### 1.1 已有底座（可复用，勿重造）
| 件 | 位置 | 说明 |
|---|---|---|
| 真实引擎战斗 | `game/battle.py` BT.Battle | player_turn/skill/enemy_phase，绝对时刻制，cast/cd/mp/资源全在引擎结算 |
| 模拟战斗助手 | `tests/numeric_sim.py` | class_battle_matrix 纯普攻/单技能，seeds 固定 |
| 真实玩家模型 | `scripts/numeric_lib/player.py` | build_player / per_action_dmg / sustained_dps（含 CD/MP/DOT 折算）/ mp_budget |
| 装备工厂 | `scripts/numeric_lib/gear.py` | make_gear(lv, quality, enhance, upgrade, gem, set_bonus) + gear_loadout |
| 怪物工厂 | `scripts/numeric_lib/monster.py` | build(role, lv) 真实模板 + curve_override |
| 组队/Boss 模型 | `scripts/numeric_lib/team.py` | boss_hp / team_matrix / 承伤侧 / 队伍构成 |
| 分阶段扫描 | `scripts/numeric_lib/stage.py` | 5 阶段 P1-P5 玩家 vs 怪 |
| 数值门禁运行器 | `scripts/run_numeric_tests.py` | 自动跑 tests/test_numeric_*.py，失败 exit 1 |
| 职业数据 | `game/data/classes.py` | 7 基础职业（含诗人），base/growth/evolve 分支 |
| 技能数据 | `game/data/skills.py` PLAYER_SKILLS | 7 职业 × 8-11 技能（v174 skills 子表 + exprs/cast/cd/mp/mech/mech_val） |
| 流派数据 | `game/data/builds.py` BUILDS | 每职业 3 流派 × 技能清单 + desc |
| 副本/Boss | `game/data/instances.py` | 22 本（8 主线+5 区域+6 外域+3 扩展），每 Boss 3 技能+阶段 |
| 技能升级 | `game/data/skill_up.py` | SKILL_UP 每技能 p/m/max |
| 数值权威 | `design/new_world/32_数值设计.md` | 装备/成长/阶段数值模型 |

### 1.2 现有 26 个数值测试覆盖（盘点结果）
| 维度 | 已有测试 | 缺什么（本方案补） |
|---|---|---|
| 面板快照 | test_numeric_panel_snapshot（12职业裸装） | 不同加点面板矩阵没有 |
| 跨级胜率 | test_numeric_battle_matrix（纯普攻 11 级） | 只用普攻、只有 11 级、无技能轴 |
| 技能倍率 | test_numeric_skill_power（每职 2 技能快照） | 只快照不验证平衡；无全技能审计 |
| 装备依赖 | test_numeric_equip_dependency（战士 11 级裸vs满） | 只 1 职业 1 等级 |
| 怪物曲线 | test_numeric_monster_curve | 只锁怪物曲线，无职业×怪交互 |
| 组队/Boss | test_numeric_team_comp（团队构成×多人本） | **无单人职业流派 vs Boss**；无单人本全职业扫描 |
| 承伤/生存 | test_numeric_monster_strength | Boss 单发占比 8-12%，但不看击杀轮 vs 生存轮 |
| MP 经济 | test_numeric_mp_budget | 只法师/战士粗比 |
| 技能vs普攻 | test_numeric_skill_vs_basic | 有技能不该弱于普攻的意识，但只粗扫 |
| 分阶段成长 | test_numeric_stage_growth | 每职业 5 阶段 DPS 单调，不验证流派差异 |

**核心缺口一句话：没有任何测试验证"同一职业不同加点/流派/装备下，输出与生存是否平衡、是否都能打过该阶段副本 Boss"。**

## 2. 设计目标（鱼鱼原话拆解 + 方案落地）

| 鱼鱼要求 | 本方案落地 |
|---|---|
| 不同加点组合 | 每职业 3-4 套加点预设（全力/全智/全敏/均衡/主属性变体），面板+期望 DPS 全扫 |
| 不同流派玩法 | BUILDS 3 流派每职业 → 每个流派提取技能循环（连招序列），算流派期望 DPS/资源节奏 |
| 每个技能的强度 | 全技能审计：每技能 DPE / DPS / cast / cd / mp / 定位函数，异常值红线 |
| mp 消耗 | 每技能 mp 审计 + 流派整体 MP 预算（空蓝轮数） |
| cd 平衡 | 每技能 cd/循环周期审计 + CD 期填充技覆盖 |
| 出手速度 | cast × spd 折算（复用 numeric_lib _interval / sustained_dps 口径） |
| 技能定位 | 每技能按 输出/控制/增益/治疗/减伤/资源 分类，验证"每个定位在流派里的作用" |
| 技能联动强度 | 流派连招 vs 单技能期望对比：连招收益 / 攒资源-消耗资源闭环 / 联动触发 |
| 不同属性装备 | LOADOUTS 档位矩阵（裸/蓝+0/蓝+5/紫+9/橙+9）+ 词条倾向（暴击装 vs 急速装 vs 攻击装） |
| 阶段副本 Boss 模拟对战 | 22 本全 Boss × 单人可进档 × 各阶段装备档 全扫 |

## 3. 矩阵结构设计

### 3.1 玩家侧维度（笛卡尔积，期望模型快扫）
```
职业 cls          ∈ 7 基础职业（战士/法师/游侠/牧师/刺客/拳师/诗人）
等级阶段 stage    ∈ 5 档: P1(10级) P2(24) P3(45) P4(75) P5(95)   # 对齐 numeric_lib STAGES
流派 build        ∈ 每职业 3 流派（BUILDS 全量，如战士=狂战/盾卫/血怒）
加点 attr         ∈ 每职业 3-4 套（全主属性 / 全敏 / 均衡 / 定位变体）
装备档 loadout    ∈ 按阶段档位（P1 solo_low / P2 solo_mid / P3-P4 purple9 / P5 orange9）+ 对照组裸装
技能等级          ∈ 技能按当前阶段可学等级算（转职档位内）
```
→ 期望模型格数：7 职业 × 5 阶段 × 3 流派 × ~3 加点 × ~2 档 = **~630 玩家配置**
每个配置：面板 / 期望 DPS（sustained_dps 口径）/ 生存轮 / 技能经济 / 全技能效率表

### 3.2 Boss 侧维度（全扫）
```
22 本 → 每本 boss（lv 15-99，role=boss，3 技能，阶段模板）
单人可进（min_players=1）: 12 本（哥布林/海蚀/老王/精灵废墟/烬山/深渊裂隙/鹿角/圣光试炼/月神/沉船/灰矮人部分）
多人本（min_players>=2）: 10 本 —— 用对应阶段"标准 4 人队"口径 + 单人铁律（min 进不去标注）
每 Boss 按玩家阶段档位选：玩家 lv 对齐 Boss 附近阶段
```
→ Boss 侧格数：22 Boss × 每 Boss 对应阶段装 2-3 档 = ~55 Boss 格
→ 对战矩阵（期望模型）：~630 玩家配置 × 可打 Boss ≈ **数千格期望计算**（秒级）
→ 真引擎抽样：每职业 × 每阶段 × 关键流派 × 对应当前阶段主线 Boss ≈ **~35-70 场实战斗**（分钟级，最终验证）

## 4. 双引擎架构

### 4.1 期望模型（层 1：快速全矩阵扫描 + 迭代调参）
新模块 `scripts/numeric_lib/build_matrix.py`（或同族拆分）：
```
期望DPS(cls, stage, build, attr, loadout):
  1. 面板：build_player（真实引擎公式）
  2. 流派循环：BUILDS.skills 全列表 → 过滤到"该阶段可学技能（lv<=阶段）"
  3. 循环模拟：资源机（战意/怒气/连击点/气/精力/信仰/蓝）按 mech 简化累积，
     攒点技→终结技，CD 拦截，mp 拦截 → 稳态轮转 DPS
  4. 生存：承伤侧（复用 team._comp_survive 思路单角色版）
  5. 输出=期望伤害/行动周期，技能等级取该阶段可学的成长档（非恒 Lv.1）
```
输出矩阵：每配置 = {面板, DPS, 击杀轮, 生存轮, 资源空窗, 蓝耗预算}

### 4.2 真引擎模拟（层 2：最终验证 + 门禁仲裁）
新模块 `scripts/numeric_lib/battle2.py`（扩展 numeric_sim，支持多技能循环）：
```
battle_clear(cls, stage, build, attr, loadout, boss_id, seeds=8):
  1. 构造玩家：真实 player dict（含 learned_skills = 流派技能全列表）
  2. 构造 Boss：C.build_monster 展开真实 Boss（含阶段/技能）
  3. BT.Battle 循环：玩家按流派循环顺序施放（攒点/终结/CD 就绪检测）
     → 复用 numeric_sim 的 seed 固定 / 拦截转普攻 / _MAX_TURNS
  4. 返回 (胜场, 平均击杀轮, 平均生存轮)
```
仲裁规则（鱼鱼铁律：真实引擎为准）：
- 期望模型预测 vs 真引擎实测 ≤1.5 轮误差（参考 test_numeric_toolkit 的 ≤1 轮口径放宽到 1.5）
- 真引擎是门禁判定源；期望模型只用于快速初筛/调参

## 5. 门禁断言设计（新增 test_numeric_* 文件）

### 5.1 文件拆分（每个独立可跑，自动纳入 run_numeric_tests.py）
| 新测试文件 | 断言内容 | 耗时估 |
|---|---|---|
| `test_numeric_build_matrix.py` | 流派×加点×装备全矩阵期望 DPS 一致性 + 击杀轮带 | 秒级 |
| `test_numeric_skill_efficiency.py` | 全技能 DPE/DPS/cd/mp 审计红线（无废技能/无超模技能） | 秒级 |
| `test_numeric_build_vs_boss.py` | 每职业×流派×阶段 vs 对应主线 Boss 期望击杀轮带 + 生存 vs 击杀 | 秒级 |
| `test_numeric_boss_engine_verify.py` | 真引擎抽验：关键格胜率 ≥ 阈值 + 期望 vs 实测误差 ≤1.5 轮 | 分钟级 |
| `test_numeric_attr_sensitivity.py` | 加点敏感性：主属性加点 vs 均衡加点差距在带内（防单属性碾压） | 秒级 |
| `test_numeric_combo_chain.py` | 流派连招 vs 单技能收益（联动必须有正收益） | 秒级 |

### 5.2 断言红线（数值权威 = 32_数值设计.md，先建模后定标）
- 击杀轮带：对标 test_numeric_team_comp 已用 60-80 轮目标（副本 Boss 长盘化设计意图）
- 生存轮 ≥ 击杀轮×0.9（先活着再谈输出——旧教训"48.5轮可打其实是先死"）
- 流派 DPS 离差：同职业 3 流派期望 DPS 极差 ≤ 30%（防某流派废/超模）
- 加点敏感：主属性最优 vs 次优加点 DPS 差距 ≤ 15%（防单属性碾压）→ 覆盖鱼鱼"不同加点组合"
- 全技能 DPE 无 < 普攻×0.8（防废技能）无 > 普攻×4（防超模，参考现有 skill_vs_basic 口径）
- MP 预算：长盘（60-100 轮）法系不能空蓝超 40% 时间（技能经济）
- Boss 战可胜：真引擎抽验格胜率 ≥ 6/8（多数能过）

## 6. 任务拆分（多子 agent 并行）

按鱼鱼铁律：任务卡写死怎么做、禁全量读、同文件并行=独立新文件+主 agent 合并、引擎主 agent 亲写。

| agent | 负责 | 产出文件 | 依赖 |
|---|---|---|---|
| A1 期望引擎核心 | 新期望模型 build_matrix.py（纯新文件） | scripts/numeric_lib/build_matrix.py | 无（读 numeric_lib 现有） |
| A2 真引擎扩展 | 扩展 numeric_sim → 多技能循环 battle2.py | scripts/numeric_lib/battle2.py + tests/numeric_sim2 若需 | 无 |
| B1 战士/法师 | 全技能效率表 + 流派循环定义 + 加点预设 | 每职业数据文件（纯数据） | A1/A2 接口定了后 |
| B2 游侠/牧师 | 同上 | 同上 | 同上 |
| B3 刺客/拳师/诗人 | 同上 | 同上 | 同上 |
| C1 门禁测试 | 6 个 test_numeric_*.py 骨架 + 断言 | tests/ | A/B 全齐后 |
| C2 Boss 对战矩阵 | Boss 侧提取 + 22 本×职业矩阵 | 数据/Boss 档位 | A1/A2 |
| D 主 agent | 架构设计/接口定义/合并/门禁集成/最终报告 | docs/ 方案 + 汇总 | 全部 |

依赖链：接口冻结（A1/A2 函数签名）→ B 各职业数据并行 → C 门禁组装 → 主 agent 全量跑+定标+写报告

## 7. 验证与交付

1. 接口冻结后每 agent 独立跑通自检
2. 全量 `python scripts/run_numeric_tests.py`（新增 6 个文件全绿 + 既有 26 个不回归）
3. 产出 `docs/BALANCE_MATRIX_v175.md` 存档报告（全量表格）
4. 聊天贴摘要（门禁新增项 + 失衡点 + 修复建议）
5. 双仓库提交（dragonfall + dragonfall-designer 同步策划案侧新门禁说明）

## 8. 风险 / 待鱼鱼拍板

| 项 | 问题 | 建议 |
|---|---|---|
| R1 期望模型对机制近似度 | 战士狂暴/刺客连击/拳师气等资源机复杂，期望模型会近似 | 以真引擎为准，期望只做粗筛（鱼鱼已拍板双引擎） |
| R2 技能等级口径 | 现有 numeric_lib 恒 Lv.1 保守；流派矩阵要不要按阶段可学等级算 | 建议按阶段可学等级（更真实），需接受与旧测试基线偏离 |
| R3 22 本单人可进 | min_players>1 本单人进不去 | 单人职业矩阵只打单人本（12 本）+多人本用对应队伍档（队伍口径已有 team_comp） |
| R4 诗人流派 | 诗人 3 流派输出差异极大（辅助 vs 输出） | 分定位口径：输出流按 DPS 评，辅助流按"团队增益等效"评 |

## 9. 变更记录
- 2026-09-04 v1 初稿（格温）
