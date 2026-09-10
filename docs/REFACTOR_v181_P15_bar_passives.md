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

## 二、⚠️ 未闭合的数值缺口（~~待鱼鱼拍板~~ → **2026-09-10 夜已拍板并落地**）

v153 §六 原文（`docs/CLASS_MECHANICS_v153.md:868-879`）与落地情况：

| # | 代码原现况（实证） | 偏差 | 处置（2026-09-10） |
|---|---|---|---|
| ① | `bar_tick` 用 `int(decay_per_turn)` → 实测 **−1/宿主动**且挂在宿主动作上 | 策划案 −1.7 **每刻** | ✅ 已改：`bar_settle` 按 dt 连续结算（小数累计），时钟事件 `time_advance` 驱动；验收 ≈4.5 次出手触发 |
| ② | `immune_turns = 1` 按「宿主动作数」递减；免疫期内继续积蓄；`no_inject_on_trigger` 无消费方 | 策划案「2 刻内不再积蓄」+自锁防护 | ✅ 已改：`immune_secs = 2.0` + 绝对时刻 `immune_until`；期内注入忽略；触发当帧注入 = 0 |
| ③ | 推满 = `effects mode=skip`「下一动」| 策划案 v153 写「定身 2.0 刻」 | ✅ 裁定保留 skip 语义（怪行动间隔 >2 刻，定身会白给）；**策划案 v153 已同步改文** |
| ④ | `bar_preserve`（阶段保留 50%）零调用 | 策划案要求 | ⏳ 另立工单（Boss 阶段钩子：`boss_script` 补 `fire("phase")`） |
| ⑤ | 反震（lv58 被动，`shaken_gain: 3`，desc「受击时…推破绽条」） | —— | ⏳ 另立工单（需 `on_taken` 装配动作 + reflect 通道） |

**另：条上限死锁**（本批发现）——`max 50` 与「阈值递增封顶 ×2.5 = 125」打架
（首次触发后阈值 67 > 上限 50 → 第二次起永远触发不了）→ ✅ 已改 `max = 125`。

### 验收门禁（新增，防再漂）

`tests/test_numeric_bar_decay.py`（纳入 `scripts/run_numeric_tests.py`，25 断言）：
每刻 −1.7 连续衰减 / ≈4.5 次出手触发 / 阈值序列 50→67→90→121→125 / 上限 ≥ 封顶 /
免疫 2 刻不积蓄且到期可再触发 / 触发当帧注入=0 / 条键不与 EFFECT_RULES 撞键 /
条条目不带 expire|period|mode|stacks|stat|mult。

### ①+② 改完的验收断言（可复现）

```text
连招三连（hits=3, shaken_gain=5）一次施放 → 注入 +15
拳师循环 ≈ 2.2 刻 → 衰减 −1.7 × 2.2 = −3.74 → 净 +11.26
净注入累计 / 50（首阈值）≈ 4.4 ≈ 策划案「约 4.5 次出手触发一次破防」✅
（实测 test_numeric_bar_decay 第 2 组：5 次出手触发）
```
