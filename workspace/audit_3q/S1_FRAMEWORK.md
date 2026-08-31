# S1 套装去模板化 - 公共框架（FRAMEWORK）

## 背景
92 套套装严重模板化：6 个 effect 模板被 9-11 套复用（dodge_set 11 / regen 10 / pierce 10 / execute 10 / thunder 9 / lifesteal_set 9），2 件套属性也是 6 组数值换皮。鱼鱼要求"不要模板化"。

## 目标
每套套装 = **专属 4 件效果**（有名字、有机制、不与他人重复），区域套 5 件全给 cond 特殊效果，职业套 12 套保留不动（已独特）。

## 引擎消费方式（已确认）
- `set_bonus_4`（engine.py:675）返回已激活套装的 4 件 effect 名列表
- on_hit 类：battle.py:4092-4099 按 effect 名查 `SET_PROC_EFFECTS`（core/affix_effects.py）分发
- turn_start 类：battle.py:4989 硬编码 `regen`/`regen_strong` 分支
- 受击类：battle.py:5762 硬编码 `reflect` 分支
- **新增 effect 名需要在 SET_PROC_EFFECTS 注册 handler**（或改 battle.py 硬编码分支）——设计时标注清楚

## 拆批（按模板族，5 个 agent 并行）
| agent | 模板族 | 套数 | 内容 |
|---|---|---|---|
| A | dodge_set（闪避） | 11 套 | 给 11 套各设计专属 4 件效果（不再共享 dodge_set） |
| B | regen（回血）+ execute（处决） | 10+10 套 | 20 套各设计专属效果 |
| C | pierce（破甲）+ thunder（雷击） | 10+9 套 | 19 套各设计专属效果 |
| D | lifesteal_set（吸血） | 9 套 | 9 套各设计专属效果 |
| E | 区域套 5 件 cond 效果 | 38 套区域套 | 给没有 cond 特殊效果的套设计 5 件专属机制（已有 5 套保留） |

## 设计铁律
1. **每套效果必须唯一**：effect 名不与他人重复（不再 6 模板轮播）
2. **贴合套装主题**：套装名/职业/主题决定效果方向（铁皮=物理抗性、秘银=法术防护、烈焰=灼烧、雷霆=雷击……）
3. **数值守恒**：新效果强度 ≈ 原模板强度（参考原模板：dodge 10%、regen 5%、pierce 30%×减半、execute <30%+25%、thunder 25%×60%、lifesteal 30%×15%），**不强于原模板太多**（ΔE ≤ 原模板 +5%）
4. **强效果有代价/条件**：如"低血才触发""需要叠层""每场限 N 次"
5. **引擎兼容**：新效果尽量复用既有 effect 语义（chance/pct/stats/desc 结构），需要新 handler 的标注"需注册 SET_PROC_EFFECTS"
6. **不破坏既有测试**：改 effect 名会影响测试断言（grep tests/ 里引用旧 effect 名的），设计时列出受影响测试
7. **2件套属性**：顺手差异化（不再 6 组数值换皮），但保持强度守恒

## 输出格式
每 agent 输出：
1. **专属效果设计表**：套装名 + 新 effect 名 + 效果描述 + trigger（on_hit/turn_start/受击/passive）+ 数值 + 与旧模板强度对比
2. **引擎改动清单**：哪些 effect 需注册新 handler（SET_PROC_EFFECTS）、哪些改硬编码分支
3. **受影响测试**：grep 出来的引用旧 effect 名的测试文件

报告写 `workspace/audit_3q/S1_<族>.md` + summary 返回全文（中文）

## 必读
- `game/data/sets.py`（92 套数据）
- `game/core/affix_effects.py`（SET_PROC_EFFECTS 注册表）
- `game/engine.py:675-683`（set_bonus_4 消费）
- `game/battle.py:4092-4099`（on_hit 分发）、`4989`（regen 分支）、`5762`（reflect 分支）
- `tests/` 里引用 dodge_set/regen/pierce/execute/thunder/lifesteal_set 的测试
