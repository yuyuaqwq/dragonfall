# v181.M-passive P15：破绽系三被动实装 + 破绽数值缺口（2026-09-10）

前置：推条数据已回填（`ab48caf` 武僧 23 技能 `shaken_gain`，对齐 v153 §六 档位表）；
推条消费链已接线（`ff4289c` `services/battle2_bar_procs.py` + `BAR_INJECT_FIELDS`）。
**本批补的是被动本体**（`PASSIVE_PROC` 表原先对这三个 proc 零声明）。

## 一、本批实装（commit 待记）

| 被动 | 技能数据（`skills.py`） | 实装 |
|---|---|---|
| 气力之心 `shaken_awareness` | lv62 格斗士 `{bar_at: 15, mult: 0.20}` | `dmg_calc` 乘区：目标 `buffs.shaken.val ≥ 15` → ×1.2（judge `target_bar_ge`） |
| 破绽·极 `broken_extend` 乘区段 | lv97 `{extend: 1, broken_mult: 0.50}` | `dmg_calc` 乘区：目标破防态（`trigger_count>0` 且 `immune_turns>0`）→ ×1.5（judge `target_bar_broken`） |
| 破绽·极 `broken_extend` 延长段 | 同上 | `skill_hit` 动作 `passive_bar_extend`：本次命中触发破绽后免疫窗口 +1 刻（`also` 段声明） |
| 多段推条 ×段数 | v153 §六「多段 +3~+5/**段**」 | `BAR_INJECT_FIELDS` 加 `per_hit: True` → 命中注入 = 字段值 × `info.hits`（skill_hit 每次施放只 fire 一次，段循环在 fire 之前） |

语义源 = 旧 `battle.py`（`379a792^` 可取回）：
- `_deal_damage:9714-9731`（气力之心 / 破绽·极乘区段，`_run_proc_family` 前守卫逐字）
- `_skill_hit_settle:6373-6397`（`bar_gain → bar_should_trigger → bar_trigger → broken_extend 延长`，
  **延长段排在触发之后** → 本次触发即吃到延长）

顺序契约：`apply_bar_procs` 的注入条目 `insert(0)` 排 `skill_hit` 首位——被动 `also` 段
（延长）依赖「本次命中先推条并触发」才读得到免疫窗口（旧引擎同序）。已写进两处 docstring。

验收：`tests/test_passive_p15.py` 25/25（装配 ± / 门槛边界 15 vs 14 / 破防态两反例 /
延长 2 vs 对照组 1 / 未触发不延长 / 三段叠加 ×1.8）；
`tests/test_battle2_bar_procs.py` 26/26（新增第 7 组多段：4/段×4=16、单段 15×1、45+5/段×3 触发）。

> 数据核对：24 条带 `shaken_gain` 的技能与 v153 §六 分档表逐条对齐
> （主力 15 / 中档 10~12 / 次要 5 / 多段 3~5 **每段** / 普攻级 2~3），
> 即 `shaken_gain` 字段语义 = **每段**量（连招三连 hits=3 gain=5）。

## 二、⚠️ 未闭合的数值缺口（**待鱼鱼拍板，本批未动**）

v153 §六 原文（`docs/CLASS_MECHANICS_v153.md:868-879`）：

```
衰减：每刻 −1.7
推满 → 目标【破防】：定身 2.0 刻，破绽清零
免疫窗口：触发后 2 刻 内不再积蓄
自锁防护：触发瞬间注入 = 0
阶段转换：保留 50% 积蓄
```

| # | 代码现况（实证） | 偏差 | 影响 |
|---|---|---|---|
| ① | `core/battle_bars.bar_tick` 用 `int(decay_per_turn)` → 配置 1.7 实测 **−1/刻** | 策划案 −1.7 | 破防推进速度偏慢；§六 验算（连招三连 −3.7 → 净 +11.3 → **4.5 次出手触发**）不成立 |
| ② | `ENEMY_BAR_CFG.immune_turns = 1`，且免疫期内**继续积蓄**（val 可涨） | 策划案「2 刻内不再积蓄」+「触发瞬间注入 = 0」（配置里有 `no_inject_on_trigger` 但无消费方） | 「晕→追颅→又满→再晕」自锁风险 |
| ③ | 推满 = `effects mode=skip`「下一动」 | 策划案「定身 2.0 刻」 | 语义近似（CTB 下 2 刻 ≈ 1~2 次行动），**未做** |
| ④ | `bar_preserve`（阶段保留 50%）函数在、**零调用方** | 策划案要求 | Boss 阶段转换进度遗产未接线（属 Boss 机制批） |
| ⑤ | 反震（lv58 被动，`shaken_gain: 3`，desc「受击时…推破绽条」） | —— | 受击推条通道未做（需 `on_taken` 装配，属破绽被动本体批） |

### 建议修法（推荐 A，一次改完用 §六 验算做验收）

- **①A（推荐）**：`bar_tick` 改小数累计 —— `val` 内部 float、展示 floor
  （对齐已拍板的「effects float 层」口径，一处改动同时让 ① 和 破绽感知`shaken_decay_half` 的
  −0.85/刻 成立）。**备选 ①B**：装配层存 `_decay_acc` 小数进位（核心零改动，条容器多一私有键）。
  **备选 ①C**：配置改 `decay_per_turn = 2`（int 语义，刻度偏离策划案）。
- **②**：`bar_gain` 在 `immune_turns > 0` 时跳过注入（= 落实 `no_inject_on_trigger` 与
  「2 刻内不再积蓄」）+ 配置 `immune_turns: 1 → 2`。
- **③④⑤**：另立工单（定身刻数 / Boss 阶段钩子 / 反震受击通道）。

### ①+② 改完的验收断言（可复现）

```text
连招三连（hits=3, shaken_gain=5）一次施放 → 注入 +15
拳师循环 ≈ 2.2 刻 → 衰减 −1.7 × 2.2 = −3.74 → 净 +11.26
净注入累计 / 50（首阈值）≈ 4.4 ≈ 策划案「约 4.5 次出手触发一次破防」✅
```

`shaken_decay_half`（破绽感知，lv85）当前**物理上不可能生效**（`int(1.7/2) = 0`，
旧 `battle.py:9319-9329` 同病）→ 必须随 ① 一起落，否则永远是空转被动。
