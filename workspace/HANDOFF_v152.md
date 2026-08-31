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
| d07d96c P8 | 修复 weapon_effects ACT_TICK 引用（模块级常量非 Battle 属性）——哨兵壁垒/永冻领域/无尽辉光/深岩壁垒/星辉壁垒 CD 失效 bug |
| e95623e P9 | 测试适配：26 文件 27 测试全绿（子 agent sa-0-8209573d） |
| b760950 P10 | 文案清理：'回合'→'刻'全量替换（game/ 1486 处 + 策划案 683 处，鱼鱼拍板「刻」）；game/ 下'回合' 0 残留；测试断言同步（food_hot/v59）；全量回归 222/222 全绿 |

## ✅ 当前状态（2026-08-31 深夜）

- **全量回归 222/222 全绿**（`python scripts/run_all_tests.py --serial`）
- **数值标定**：sim_ctb_v152.py 验证频率等价（实测比 vs 真实 spd 比偏差<11%）、行为时长精确
- **策划案同步**：design/new_world 27_战斗规则引擎.md 已更新 v152 章节（commit 9de46ac）
- **待办**：
  1. 文案清理：约 1190 处中文"回合"（battle.py 195 / items.py 119 / equip_add_effects 92 / skills.py 73 / battle_config 73 / equip_roster 63...），大头是数据 desc 文案 + 注释 + 数值字段名。**待鱼鱼拍板**：文案改成"刻/行动/息"哪种说法
  2. 副本/世界 Boss 冒烟验证（单机已验证；副本测试已绿 test_v137/v141）
  3. 双仓库 push（dragonfall + design/new_world）
  4. AstrBot 重启验证

## 🔧 环境
- 项目根：C:/Users/yuyu/qqbot/data/plugins/dragonfall（git: master）
- 回归：`python scripts/run_all_tests.py --serial`
- 标定：`python scripts/sim_ctb_v152.py`
- 测试并发注意：多个测试同时跑会共用 test_game_data.db 导致"你还没有角色"假失败——串行跑才准

## ⚠️ 已知坑
- `_ct_initial_wait` 是**模块级函数**（`battle._ct_initial_wait`），不是 Battle 方法！测试/命令层调用用 `BT._ct_initial_wait(...)`
- 事件队列只调度 enemy_act；DOT/宠物/Boss 机制不要排独立事件（会双重结算）
- `st["round"]` 在 instance.py 是展示键（= `_tick_no()`），不是结算
