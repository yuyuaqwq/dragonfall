# CTB 彻底化 v152 执行方案（鱼鱼已拍板：所有回合概念全删）

## 一、核心改动思路（已定稿，见 docs/CTB_EVENT_QUEUE_REFACTOR_v152.md）

**结算引擎彻底时刻制**：所有行为（普攻/技能/吃药/食物/防御/逃跑）有 cast_time，CD/buff/护盾/DOT 全部按绝对时刻 `expire_at`/`ready_at` 到期。**round 字段全删、回合文案全删**。

## 二、改动范围（已摸底）

- **引擎层（battle.py，主 agent 亲写）**：`self.round` 9 处 → 删；`_end_round` → 改 `_advance_time`；`_turn_start` DOT/词条 → 时刻事件；`_tick_cooldowns` CD → `ready_at`；Boss/宠物 `round % interval` → 定时事件；新手保护 `round <= 1` → `now < ACT_TICK`
- **副本 instance.py**：`st["round"]` → 删；`_instance_next_actor` → `next_act_at`；展示"第 N 轮"删
- **存档 battle_state.py**：`round` 键删
- **命令层 combat.py/social.py**：`p_extra_left` 清理、行动顺序按 `next_act_at`
- **机制层 core/**：battle_conds `round <= 1`（战争咆哮）→ 时刻；battle_mech 的 `last_round`/`summoned_round`/`healed_round`/`r % N` → 时刻戳；affix_effects/weapon_effects 的 `once_per_round`/`round` → 时刻
- **数据层**：1201 处"回合"文案里，技能/装备 desc 的"持续 N 回合"→ 改"持续 N 时刻"（或按 ACT_TICK 换算秒感）；数值字段 `turns`/`cd`（回合数）→ 按 ACT_TICK 换算成时刻值

## 三、执行节奏（按铁律：每块改完测试+提交再动下一块）

### 阶段 A：引擎核心（battle.py）
1. 新增 `self._now`（绝对时刻）、`_schedule(ev)`、`_advance_time(dt)`、`_next_player_act_at`
2. `_ct_cost`/`_ct_initial_wait` 保留（就是时刻计算），ct 语义升级为 `next_act_at`（= now + cost）
3. `player_turn` 改造：行为 cast_time → 结算到玩家下一次可行动点
4. `_end_round`/`_turn_start`/`_tick_cooldowns` 全删（或改纯时刻版）
5. `to_state`/`from_state`：round 键删，加 now/next_act_at

### 阶段 B：副本 instance.py
1. `st["round"]` 全删
2. `_instance_next_actor` 按 `next_act_at`
3. 展示改"时刻 T"，不写"第 N 轮"

### 阶段 C：存档 + 命令层
1. `battle_state.py` round 键删
2. `combat.py`/`social.py` 清理

### 阶段 D：机制层 core/
1. `battle_conds.py`：`round <= 1` → `now < ACT_TICK`
2. `battle_mech.py`：`last_round`/`summoned_round`/`healed_round`/`r % N` → 时刻戳
3. `affix_effects.py`/`weapon_effects.py`：`once_per_round` → `once_per_interval`（按时刻）
4. `battle_bars.py`/`battle_modes.py`/`class_sets.py`/`food_effects.py`/`potion_effects.py`：回合递减 → 时刻到期

### 阶段 E：数据层文案（量大，可子 agent 并行）
- 47 个文件 1201 处"回合"：技能/装备/怪物 desc 文案"持续 N 回合"→ 换算时刻（N × ACT_TICK）
- 数值字段 `turns`/`cd`：按 ACT_TICK 换算
- **注意**：desc 文案与数值字段要一起改，不能只改文案不改数值

### 阶段 F：测试
- 新建 `tests/test_ctb_v152_event_queue.py`
- 全量回归 `python scripts/run_all_tests.py --serial`

## 四、风险控制
- 引擎层主 agent 亲写（同一文件并行冲突）
- 机制层/数据层按文件分给子 agent，先出独立改动再合并
- 每阶段跑测试，绿了再提交
- ACT_TICK 初值 `BASE_DELAY/50 ≈ 2.0`，模拟标定后写回

## 五、标定
- `scripts/sim_ctb_v152.py`：3:1/5:1 配速行动比、胜率、战斗时长 vs v121 对比
- 产出 ACT_TICK/cast_time/换算系数结论
