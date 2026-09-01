# EXTENSIBILITY_REFACTOR_PLAN_v161.md — 全技能公式表达式化 + 数值职业矩阵标定

> 日期：2026-09-01
> 触发：鱼鱼拍板"所有技能的公式重新设计 + 结合数值职业矩阵"（v160 exprs 引擎能力就位后，数据层全面迁移）
> 范围：98 个玩家技能（56 基础 + 42 分支）的 formula → expr/exprs 表达式化 + 按职业矩阵重新标定
> 状态：📋 计划待审

## 1. 现状（代码证据）

- **引擎能力已就位（v159/v160）**：expr/exprs 表达式 + 中文翻译 + 技能详情全等级展示，已提交（fa56773）
- **数据层零迁移**：98 个玩家技能中 29 个配了 formula（stat/mult/flat 固定模式），**0 个配 expr/exprs**
- 技能详情现在对旧 formula 技能仍显示百分比（`伤害 82%`），对表达式技能显示实际数值
- **关键依赖**：scripts/numeric_lib/player.py `_skill_dmg` **只读 `power` 字段**（L106），技能改 exprs 后若丢 power → 职业矩阵 DPS 全崩

## 2. 目标（鱼鱼口径）

1. **全部技能公式表达式化**：每技能一条 `exprs`（逐级）或 `expr`（单条，内含 skill_lv 成长），替代 stat/mult/flat 固定模式
2. **结合数值职业矩阵标定**（32 章 1.1 + numeric_lib）：
   - 职业 DPS 锚点：法 S / 刺 S / 游 A / 战·拳 B / 牧·诗 C（P1~P5 每阶段）
   - **职业加点倾向适配**（鱼鱼核心洞察）：战士主加耐力 → atk 低 → 表达式基础值补偿；不同职业成长曲线不同，不能全用"atk×X%"纯百分比
   - 门禁：技能 DPS ≥ 普攻×1.1（test_numeric_skill_vs_basic.py）+ 阶段成长率 1.25~5.0×
3. **技能详情展示全面生效**：每个技能都有 📐 公式行 + 按玩家当前属性代入的每级实际数值

## 2.1 鱼鱼拍板（2026-09-01）

- **单轨**：删 power 只留 exprs——最干净，同步改 numeric_lib 和所有读 power 的测试/工具
- **先做样板**：战士 + 法师 2 个职业（基础技能）表达式化 + 标定，鱼鱼确认手感后再铺开全部
- 样板验证通过后：7 职业基础（56）→ 7 职业分支（42）分批推进

## 3. 技术方案

### 3.1 numeric_lib 兼容 expr/exprs（必须先做）

`_skill_dmg` 增加表达式分支：
```python
info = E.skill_info(...)
_expr = E.skill_formula_expr(info, 1)  # Lv.1 保守档（与现 ROTATIONS 口径一致）
if _expr:
    # 用 E.skill_expr_preview 代入 st 面板算期望基础值（variance=0）
    base = E.skill_expr_preview(info, 1, st)
else:
    power = float(info.get("power", 0)) * E.skill_power_mult(1, info)
    base = int(stat * power) + skill_flat
```
保留 power 字段作 fallback（双轨兼容，迁移期不崩）。

### 3.2 表达式设计模板（按职业）

每职业一个**基础值成长曲线**（补偿主加非攻击属性的职业）：

| 职业 | 主攻属性 | 加点倾向 | 表达式策略 |
|---|---|---|---|
| 战士 | atk | str+vit 混（耐战） | `atk*X + player_lv*Y + base`（基础值补偿 vit 不吃攻） |
| 法师 | matk | int 纯 | `matk*X + player_lv*Y`（法系面板高，基础值占比低） |
| 游侠 | atk | agi 主（快） | `atk*X + player_lv*Y`（spd 高，DPS 靠频率） |
| 牧师 | matk | int 纯 | `matk*X + player_lv*Y` |
| 刺客 | atk | agi 主（爆） | `atk*X + player_lv*Y + crit 联动` |
| 拳师 | atk | str+vit 混 | `atk*X + player_lv*Y + base` |
| 诗人 | matk | int 纯 | `matk*X + player_lv*Y`（辅助，DPS 低锚点） |

通用形态：`主攻属性×mult + player_lv×per_lv + base`，逐级公式 exprs 表达成长：
- Lv.1: `atk*0.8 + player_lv*3 + 12`
- Lv.2: `atk*0.85 + player_lv*3 + 16`
- Lv.5: `atk*1.0 + player_lv*3 + 28`

### 3.3 标定流程（对齐职业矩阵锚点）

1. 每职业选技能轴代表技能（ROTATIONS 现有技能）
2. 用 numeric_lib `per_action_dmg` 实测：技能 DPS / 普攻 DPS ≥ 1.1
3. 用 `gen_numeric_matrix.py` 实测各阶段击杀轮：对齐 32 章 1.1 目标
4. 调表达式 mult/per_lv/base 直到矩阵达标
5. 更新 32 章 1.1 表（若锚点微调）

## 4. 任务拆分（多 agent）

| 卡 | 内容 | 归属 |
|---|---|---|
| A | numeric_lib expr/exprs 兼容 + 门禁更新 | 主 agent 亲写（引擎依赖） |
| B | 7 职业基础技能（56 个）表达式化 + 标定 | 子 agent × 7（每职业一张卡） |
| C | 7 职业分支技能（42 个）表达式化 + 标定 | 子 agent × 7 |
| D | 测试适配（test_numeric_skill_power 快照/test_numeric_formula/全量回归） | 主 agent 收尾 |
| E | 策划案同步（32 章 4.4b 补公式模板 + 12 章 1.9 补每职业示例） | 主 agent |

## 5. 风险与回滚

- **风险 1**：numeric_lib 不兼容 exprs → 职业矩阵 DPS 全崩（先做卡 A 再动数据）
- **风险 2**：表达式标定后 DPS 偏移 → 每职业标定完立即跑门禁
- **风险 3**：power 字段删除后旧测试断言崩 → 保留 power 字段双轨（表达式优先，power 作展示/兼容 fallback）
- 回滚：git checkout 秒回（每张卡独立 commit）
