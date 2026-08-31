# v152 CTB 事件队列彻底重构 · 交接文档（2026-08-31）

> 鱼鱼拍板：**CTB = 每个事件有起始和结束时刻**。所有行为（普攻/技能/道具/食物/防御/逃跑）有时长。
> **所有跟回合有关的东西都要删掉**——不是换皮，是彻底删除。
> 设计文档：docs/CTB_EVENT_QUEUE_REFACTOR_v152.md（权威）；执行计划：workspace/CTB_v152_EXEC_PLAN.md

## ✅ 已完成并提交（git master，最新 HEAD）

| Commit | 内容 |
|---|---|
| 7e0e5b5 P1 | 引擎事件队列+行为时长+去回合化：`self._now` 全局绝对时刻、heapq 事件队列（`_schedule`/`_process_until`）、`_after_actor_ct` 绝对时刻（next_act_at = now + cast_mult×cost）、行为时长常量、CD/护盾/资源增幅改 expire_at/ready_at、`_end_round`→`_advance_time(dt)`、`_tick_no()` 替代 round |
| 57c30bc P2 | 副本绝对时刻化+特效CD时刻制+存档去round：instance.py 敌方/玩家播种改 `_ct_initial_wait`、`_instance_apply_enemy_act_ct`/`_instance_auto_defend_player` 去相对 -cost、`_instance_reset_player_cts` 改 ref+cost、weapon_effects `we_*_cd` 写入改 ready_at、affix_effects `once_per_round`→`_tick_no()`、battle_conds `battle_start`→`_tick_no()<=1`、battle_state 存档 round→now |
| 4544f0a P3 | 敌方 cast 时长对称（enemy_act 用 CAST_ATK）+ 频率标定脚本 sim_ctb_v152.py（偏差<11%） |
| ce283a0 P4 | 副本 DOT 闸门简化（每行动者 dot_pending=True，删 round_acted 轮转）、_phase_exit.entered_at/holy_halo 改 _tick_no()、self.round 全清零 |
| 83f6030 P5 | instance.py `_ct_initial_wait` 改模块级调用（非 Battle 方法） |
| 681ec89 P6 | 事件队列简化——只保留 enemy_act 调度（DOT/宠物/Boss定时/词条回血由玩家行动 _turn_start / 敌方行动 _boss_mech 触发，避免双重结算） |
| 1ee6048 P7 | 设计文档更新（当前进度+标定结论） |

## 📋 当前状态

### 引擎层（已改完）
- ✅ `self.round`/`getattr(self,"round")` 全清零（grep 无残留）
- ✅ CD：`cooldown` 存 `ready_at` 绝对时刻（now + cd×ACT_TICK）；`_skill_cd_left` 按 now 算剩余
- ✅ 护盾：`p_shields` 存 `expire_at`
- ✅ 特效 CD：`we_*_cd` 存 ready_at；`we_starlight_next` 存 ready_at
- ✅ buff：int 回合值兼容（`_advance_time` 按 int×ACT_TICK 到期）
- ✅ 副本：绝对时刻调度（播种 `_ct_initial_wait`、行动者重排、无相对 -cost 广播）；`st["round"]` 仅展示（= `_tick_no()`）
- ✅ 事件队列：只排 `enemy_act`（敌方按绝对时刻行动）
- ✅ 数值标定：sim_ctb_v152.py 验证频率等价（偏差<11%）

### 测试适配（子 agent 进行中）
- 27 个失败测试，子 agent 已改 24 个文件
- 当前全量 207/222 通过（子 agent 完成前会更高）
- 剩余失败：test_v141 flaky（world_id 残留）、test_ctb_speed 减速断言（已 steer 修正）、test_ctb_audit 睡眠断言

### 待办
1. ⏳ 子 agent 完成测试适配（sa-0-8209573d）
2. ⏳ 文案清理：约 470 处中文"回合"（battle.py 195 / potion_effects 70 / weapon_effects 56 / battle_mech 51...）
   - 大部分是注释（109/195）和展示文案
   - **待鱼鱼拍板**：文案改成"刻/行动/息"哪种说法
   - 数据字段名 turns/max_turns/per_turn 改 ticks 是大工程（涉及所有读取方），需单独评估
3. ⏳ 副本/世界 Boss 冒烟验证（单机已验证）
4. ⏳ 策划案同步（design/new_world/ 独立 git 仓库）
5. ⏳ 双仓库提交 + push
6. ⏳ AstrBot 重启验证

## 🔧 环境
- 项目根：C:/Users/yuyu/qqbot/data/plugins/dragonfall（git: master）
- 回归：`python scripts/run_all_tests.py --serial`
- 标定：`python scripts/sim_ctb_v152.py`
- 测试并发注意：多个测试同时跑会共用 test_game_data.db 导致"你还没有角色"假失败——串行跑才准

## ⚠️ 已知坑
- `_ct_initial_wait` 是**模块级函数**（`battle._ct_initial_wait`），不是 Battle 方法！测试/命令层调用用 `BT._ct_initial_wait(...)`
- 事件队列只调度 enemy_act；DOT/宠物/Boss 机制不要排独立事件（会双重结算）
- `st["round"]` 在 instance.py 是展示键（= `_tick_no()`），不是结算
