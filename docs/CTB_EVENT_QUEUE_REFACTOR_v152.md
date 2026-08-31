# CTB 事件队列彻底重构 v152（抛掉回合概念）

> 鱼鱼拍板（2026-08-31）：**CTB = 每个事件有起始和结束时刻**。
> 发起攻击*攻击生效，效果触发*效果结束。系统按队列一个个处理每个时刻的事件。
> **不应该有回合的概念**——把回合抛掉来重构整个项目。任何行为都应该有时长（吃药、吃食物、攻击、技能等）。
> **追加拍板：所有跟回合有关的东西都要删掉**——不是换皮，是彻底删除。

## 〇、现状盘点（主 agent 已摸透，子 agent 直接复用）

### 当前是"半 CTB"（v121 → v151 演进）
- ✅ 已有：`p_ct`/单位`u["ct"]` 绝对时刻轴（`BASE_DELAY=100`、`SPD_CT_CAP=80`、`_ct_cost(spd)=100/max(1,min(spd,80))`、`_ct_initial_wait(spd)=100/spd`）
- ✅ 已有：敌方连动段 `_enemy_phase`（while 最小 ct ≤ 0 → 行动 → `_after_actor_ct`）；副本 `_instance_enemy_ct_acts` + `_instance_next_actor`
- ✅ 已有：`_after_actor_ct(side, unit, player)` 行动者 ct += cost、其余存活 ct -= cost（绝对时刻，无漂移）
- ✅ 已有：副本 allies ct 广播（多玩家共享时间轴雏形）
- ❌ **仍保留回合概念**：`self.round += 1`（player_turn 1655）、`_turn_start`（DOT/词条/套装回血）、`_end_round`（buff/CD/护盾递减）、`_tick_cooldowns`（CD 按回合 -1）、Boss 机制 `round % interval`、宠物技能 `round % interval`、DOT 适应回落 `round - last_round >= 2`、新手保护 `round <= 1`、护盾 `turns`、buff `turns`、hot `turns`

### round 在 battle.py 的全部引用（9 处）
1. `234` `self.round = 0`（初始化）
2. `499` `to_state` 序列化 `"round": self.round`
3. `1655` `player_turn` 开头 `self.round += 1`（每玩家行动 +1）
4. `4294` `_boss_mech` 里 `r = self.round` 传给 mech handler
5. `4751` 宠物技能 `self.round % interval != 0`（按 interval 回合触发）
6. `4778` 宠物挡刀 `self.round % interval != 0`
7. `4983` DOT 适应回落 `self.round - _last >= 2`（2 回合未叠层 → 适应 -4%）
8. `5781` 新手闪避保护 `self.round <= 1`
9. `5919` 新手格挡保护 `self.round <= 1`

### 命令层 round 引用
- `instance.py`：`st["round"]` 初始化 1、展示"第 N 轮"、`_instance_next_actor` 后写回 `st["round"] = b.round`（2258/2892）、`last_round`（2671 叠层记录）、`round` 透传（2209/2873）
- `combat.py`：`p_extra_left` 提示（1695-1696，CTB 已弃）、行动顺序按 spd 显示（social.py 352-364）
- `battle_state.py`：`"round": 0` 默认存档键

### 按回合递减的机制清单（`_end_round` 内，全部要改时刻制）
| 机制 | 现状 | 改造 |
|---|---|---|
| `p_buffs`/`e_buffs` 回合数 turns | `_end_round` 每回合 -1 | 改为绝对时刻戳 `expire_at`（存时刻值，队列到点移除） |
| 技能 CD `cooldown` | `_tick_cooldowns` 每回合 -1 | 改为 `ready_at` 绝对时刻 |
| 护盾 `p_shields[key]["turns"]` | 每回合 -1 | 改为 `expire_at` 绝对时刻 |
| 资源增幅 `amps[].turns_left` | 每回合 -1 | 改为 `expire_at` 绝对时刻 |
| 弱点击破/连携 `vuln/dot_amp turns_left` | 每回合 -1 | 改为 `expire_at` 绝对时刻 |
| 特效装备 CD `we_*_cd` | 每回合 -1 | 改为 `ready_at` 绝对时刻 |
| 星辉壁垒刷新 `we_starlight_next` | 每回合 -1 | 改为 `ready_at` 绝对时刻 |
| `reduce_all_left` | 每回合 -1 | 改为 `expire_at` 绝对时刻 |
| 食物 hot `turns` | `_turn_start` 每回合恢复 + `_end_round` 递减 | 改为持续时刻：每 `hot_interval` 时刻恢复一次，`expire_at` 结束 |
| DOT 结算 | `_turn_start` 每玩家行动结算一次 | 改为 DOT 队列事件：每 `dot_interval` 时刻跳一次 |

## 一、核心模型：全局绝对时刻 + 事件队列（真·重构，非混合）

### 1.1 时刻与队列
- **时刻（time）**：float，战斗开始 = 0.0，单调递增。全局单一时钟 `self._now`。
- **每个单位**（玩家/每个敌方）：`next_act_at`（绝对时刻，下次可行动时间）。初始 = `BASE_DELAY/spd`（快者先行动）。行动后 `next_act_at += 行动耗时`。
  - 玩家：`self.p_ct` 语义升级为 `next_act_at`（存档键兼容旧值，旧档从 0 兜底重建）
  - 敌方：`u["ct"]` 语义升级为 `u["next_act_at"]`（旧 ct 读法兼容换算）
- **事件队列** `self._events`：heapq 按 (t, seq) 升序。事件 = `{"type": str, ...}`。
  - 事件类型：`enemy_act`（敌方行动）、`player_ready`（轮到玩家）、`dot_tick`（DOT 跳动）、`mech_tick`（Boss 定时机制）、`pet_tick`（宠物技能）、`cast_done`（玩家行为生效）、`buff_expire`（惰性检查，可不排事件）
- **调度循环**：
  ```
  _process_until(until_t):
      while 队列非空 and 队首 t <= until_t:
          (t, _, ev) = heappop
          self._now = max(self._now, t)
          dispatch(ev)          # 按 type 分发
  ```
- **玩家操作流程**（player_turn）：
  ```
  1. 校验（技能可用/CD ready_at 判断/目标解析）
  2. 立即结算玩家行为效果（伤害/治疗/增益当场生效）
  3. 玩家 next_act_at = now + 行为总耗时（cast_time + cost）
  4. _process_until(玩家 next_act_at)   # 期间敌方行动、DOT 跳、buff/CD 到期、Boss 机制
  5. 战斗结束检查；未结束 → "轮到你了"
  ```
- **行为总耗时** = cast_time（前摇）× 行动 cost：
  | 行为 | cast_mult | 说明 |
  |---|---|---|
  | 普攻 | 0.5 | 读条一半即命中 |
  | 技能 | 0.8 | 大技能更慢 |
  | 道具 | 0.5 | 吃药有时长 |
  | 食物 | 0.5 | 吃食物有时长 + 持续效果按时刻跳 |
  | 防御 | 0.3 | 快动作 |
  | 逃跑 | 1.0 | 慢，易失败 |
  - cost = BASE_DELAY / max(1, min(spd, SPD_CT_CAP))（沿用标定值）
- **cast 期间敌方可行动**（真时刻制）：玩家提交攻击后，敌方若 next_act_at 在玩家生效前，会在玩家读条时先行动（日志顺序：你开始蓄力 → 敌方攻击你 → 你的攻击命中）。
- **v152 不做打断**（cast 期间受击不打断施法），行为必生效，cast_time 只影响行动频率与敌方穿插时序。

### 1.2 绝对时刻替代 round 的语义映射
| 旧（回合制） | 新（时刻制） |
|---|---|
| `round` 玩家行动计数 | `_now`（绝对时刻）；`_p_acts` 玩家行动次数（展示用） |
| buff `turns` 回合数 | `expire_at = now + duration`（duration = turns × ACT_TICK） |
| 技能 CD `cd` 回合 | `ready_at = now + cd × ACT_TICK` |
| 护盾 `turns` | `expire_at = now + turns × ACT_TICK` |
| DOT 每回合跳 | `dot_tick` 事件：挂 DOT 时排 `t = now + ACT_TICK`，跳完排下一个，到 expire_at 停 |
| `round % interval` Boss 机制 | `mech_tick` 事件每 `interval × ACT_TICK` 排一次，handler 内用 `_tick_no()` 换算轮次 |
| 宠物技能 `round % interval` | `pet_tick` 事件同上 |
| 新手保护 `round <= 1` | `_tick_no() <= 1`（即 now < ACT_TICK） |
| 词条/套装"回合开始回血" | 每 ACT_TICK 排一个 `regen_tick` 事件（或并入 dot_tick 统一节奏） |

**ACT_TICK** = 2.0（= BASE_DELAY/50，参考 spd 50 的行动间隔；Agent D 模拟复核）。
**行动轮次换算** `_tick_no()` = `int(now / ACT_TICK) + 1`——仅用于"每隔 N 次"类机制的展示/触发判定，不是回合概念。

### 1.4 玩家交互语义（QQ 聊天异步）
- 玩家发指令 = 排一个"玩家行为事件"。引擎处理到该玩家 `next_act_at` 时，生成"轮到你了"提示并等待玩家输入（真人操作，超时自动防御）。
- 单机（monster/worldboss）：`player_turn` 仍是入口（行为即时结算），但内部把"敌方段"换成"事件队列推进到玩家下一次可行动"。
- **不做真·异步实时**（QQ 是回合式聊天，没法毫秒级操作）。v152 的"事件队列"是**结算模型**：所有时间推进、CD 到期、DOT 跳动都在处理玩家行为的同一刻批量推进到 `next_act_at`，玩家看到的仍是"你行动一次 → 系统结算中间发生的一切 → 你又行动"，但**内部没有回合计数**，一切按绝对时刻。

### 1.5 关键：内部去回合后交互仍是"行动一次 → 系统结算到下次行动"（但无回合计数）
QQ 文字交互的天然节奏 = 玩家发一条消息 = 一次操作。彻底异步会变成"系统弹一堆提示等玩家挨个回"，体验灾难。
v152 方案：**结算引擎时刻制（内部无 round 无回合）**，交互上玩家行动后系统结算到其下一次可行动点。
- 玩家行动 → 结算其行为（cast_time 后生效）→ **推进 now 到玩家下一次 `next_act_at`**（期间处理所有敌方行动、CD 到期、DOT 跳动、buff 到期）→ 展示中间日志 → 等玩家下一步。
- 效果上：**不再有"回合"字样、不再有 round 计数、不再有"第 N 回合"**——只有"你行动了，时刻推进到 T，期间发生了什么，现在又轮到你了"。
- 快慢速真实拉开：快方在玩家两次操作之间动更多次，CD 也更早好（按时刻而非按玩家行动次数）。

## 二、实施分阶段（子 agent 分工）

### Phase 1：引擎层去回合化（battle.py，主 agent 亲写）
1. 新增 `self._now`（绝对时刻，从 `p_ct`/单位 ct 迁移或并存）、`self._queue`（heapq 事件队列）、`self._p_acts`（玩家行动计数，展示用）。
2. `_end_round()` 改造为 `_advance_time(dt)`：把 buff/CD/护盾/资源增幅/DOT 的回合递减改为按时刻到期检查。**保留 `_end_round` 函数名做兼容壳**（内部 = 推进到玩家下次行动点）。
3. `_turn_start` 的 DOT/词条结算 → 改为 DOT 事件（在队列里排 `dot_tick`）。
4. `_tick_cooldowns` → CD 改绝对时刻 `ready_at`；`_skill_on_cd` 判断 `now >= ready_at`。
5. `round % interval` Boss 机制/宠物技能 → 定时事件（`schedule(now + interval * ACT_TICK, ...)`）。
6. `round <= 1` 新手保护 → `now < ACT_TICK`。
7. 行为时长：`player_turn` 内 attack/skill/use_item/food/defend/flee 各算 `cast_time`，生效排事件。
8. `to_state`/`from_state`：round 键保留（兼容）但内部弃用；新增 `now`/队列序列化（或重建）。

### Phase 2：副本 instance.py（可子 agent）
1. `_instance_next_actor` 已按 ct 选人 → 改为按 `next_act_at`（绝对时刻）选人。
2. 敌方行动段、玩家超时自动防御 → 同样用 `_advance_time` 推进。
3. `st["round"]` 展示改为"第 N 轮"仍可保留（= `_p_acts` 或敌方段计数），内部不依赖。
4. 玩家快照 `ct` → `next_act_at`（存档兼容：读旧 `ct` 转新字段）。

### Phase 3：存档与命令层（可子 agent）
1. `battle_state.py` 默认状态加 `now: 0.0`。
2. `combat.py` 清理 `p_extra_left` 残留（若还有）；行动顺序展示改用 `next_act_at` 排序。
3. `social.py` 行动顺序按 ct 排序 → 按 `next_act_at`。

### Phase 4：数值标定（Agent D 模拟）
1. `scripts/sim_ctb_v152.py`：对比 v121 与 v152 的 3:1/5:1 配速行动比、胜率、战斗时长。
2. 标定 `ACT_TICK`、cast_time 系数、buff/CD 时长换算。
3. 结论写回本设计文档第五节。

### Phase 5：测试（Agent C）
1. 删 `tests/test_v61_speed_progress.py`（若有），新建 `tests/test_ctb_v152_event_queue.py`：
   - 事件队列按时刻顺序处理
   - 普攻/技能/道具/食物有时长（cast_time 后生效）
   - CD 按时刻到期（快 CD 在慢方两次行动间转好）
   - buff/护盾按时刻到期（不是按玩家行动次数）
   - DOT 按时刻跳（两次玩家行动间可能跳多次）
   - 敌方连动仍成立（快怪在玩家两次操作间多动）
   - 存档往返：now/队列恢复
   - 副本：next_act_at 选人、超时自动防御
   - PVP 不介入（保持真人轮流）
2. 全量回归 `python scripts/run_all_tests.py --serial`，修因 CTB 破坏的测试，无关失败只报告。

## 三、铁律（不可破坏的语义）
1. **伤害公式、暴击/闪避/格挡/穿透/韧性、装备词条、被动、符文、药水效果数值、宠物、召唤、AOE、站位/射程/仇恨/嘲讽、Boss 机制数值** —— 全部不动，只改"触发节奏"。
2. **PVP（btype=="pvp"）不介入**——保持真人轮流异步（CTB 调度不参与）。
3. 玩家一次操作 = 推进到下一次玩家可行动点（交互节奏不变，QQ 聊天体验优先）。
4. `round` 键在存档中保留（兼容旧档），但引擎内部不再依赖它做结算。
5. 存档不兼容允许（鱼鱼已拍板 v151 纯新表不搞历史兼容）；老存档兜底 from_state 照旧。
6. 任何行为都有时长（鱼鱼明确要求：吃药/吃食物/攻击/技能等）。

## 四、风险与对策
| 风险 | 对策 |
|---|---|
| 时刻制下 CD/持续效果换算后强度漂移 | Agent D 模拟标定 ACT_TICK，换算系数写死并回归 |
| 队列推进时敌方连动过多/死循环 | 保留敌方连动硬上限（现 8 动），事件处理加总步数上限 |
| 快方在玩家两次操作间触发大量 DOT 跳动 | dot_interval 用 ACT_TICK 统一，展示合并（一跳合并多跳文案） |
| 老存档 round 依赖 | from_state 把旧回合制 buff/CD 按 `turns × ACT_TICK` 换算成时刻 |
| 子 agent 并行改同一文件 | battle.py 主 agent 亲写；instance.py 一个子 agent；存档/命令层一个子 agent |

## 五、验收标准（鱼鱼：所有跟回合有关的东西都要删掉）
1. `grep -rn "round" game/` 无残留（`st["round"]`、`self.round`、`b.round` 全删，存档键也删）。
   **当前状态**：battle.py `self.round`/`getattr(self,"round")` 全清零；instance.py `st["round"]` 仅剩展示用（= `_tick_no()` 行动轮次）+ 初始化占位；存档 `round` 键 → `now`。`round_acted` 已删。
2. `grep -rn "回合" game/` 无残留（文案也删——不再说"第 N 回合"，改"时刻 T"或"你行动了"）。
   **当前状态**：约 470 处中文"回合"残留（battle.py 195 / potion_effects 70 / weapon_effects 56 / battle_mech 51...），
   绝大多数是**展示文案**（"持续 3 回合"）和**数据字段名**（turns/max_turns/per_turn）。结算逻辑已全部时刻制。
   **待鱼鱼拍板**：文案改成"刻/行动/息"哪种说法（clarify 超时未答）。
3. 全量回归通过（CTB 无关既有失败除外）。**当前**：207/222 通过，15 失败（子 agent 适配中）。
4. 模拟脚本产出标定结论（ACT_TICK/cast_time/换算系数）。**已产出**（scripts/sim_ctb_v152.py）：
   - 行动频率实测比 vs 真实 spd 比偏差 < 11%（v152 事件队列保持速度频率等价）
   - 行为时长：普攻 0.5 / 技能 0.8 / 道具 0.5 / 食物 0.5 / 防御 0.3 / 逃跑 1.0 × cost，p_ct 推进精确
   - ACT_TICK = 2.0（BASE_DELAY/50）待最终复核
5. 野外/世界 Boss/副本三条路径冒烟可用。**单机已验证**（完整战斗 victory）；副本待子 agent 测试绿后验证。

## 六、备注
- 本设计文档是主 agent 分析的共享结论，子 agent 直接复用，勿重复全量读项目。
- 涉及文件：`game/battle.py`（主）、`game/commands/instance.py`、`game/store/battle_state.py`、`game/commands/combat.py`、`game/commands/social.py`、`game/core/battle_mech.py`（Boss handler 的 round 参数）、`game/data/skills_v151_overrides.py`（技能 CD 字段，只读不改）、`tests/`。
- **已提交进度**（git master）：
  - 7e0e5b5 P1 引擎事件队列+行为时长+去回合化
  - 57c30bc P2 副本绝对时刻化+特效CD时刻制+存档去round
  - 4544f0a P3 敌方cast时长对称+频率标定
  - ce283a0 P4 副本DOT闸门简化+去round残留
  - 83f6030 P5 instance.py _ct_initial_wait 模块级调用
  - 681ec89 P6 事件队列简化（只留 enemy_act 调度）
