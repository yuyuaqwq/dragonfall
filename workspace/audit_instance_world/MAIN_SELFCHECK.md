# 主 agent 自查（与 4 审计 agent 并行，交叉验证用）

> 2026-08-30，审计副本/野外合并期间，主 agent 独立核查的高风险点。子 agent 报告回来后对比。

## 自查发现

### A. battle.py `_inst_*` 方法群 = 半成品/死代码（实锤）
- battle.py:1757-1945 有完整 v137 副本多人 CTB 调度方法群：`_inst_living_cts` / `_inst_min_player_ct` / `_inst_min_enemy_ct` / `_inst_next_actor` / `_inst_pick_target` / `_inst_enemy_one_act` / `_inst_enemy_phase` / `_inst_auto_defend` / `_inst_reset_cts`
- 注释自称"语义平移自 instance.py 的 _instance_next_actor/.../时钟统一 v130.10"
- **grep 全项目 `_inst_` 调用方：只有 battle.py 内部互调（1781/1793/1794/1799/1839/1893/1899），instance.py 及其他文件 0 处调用**
- `_inst_enemy_phase`（敌方段主循环）→ 无任何调用方
- 结论：v137 Phase2 把 CTB 代码"平移"进 battle.py，但 instance.py 没切过去用，battle.py 这套 = **半成品死代码**（写了没人调）

### B. instance.py 老模式 CTB 方法群 = 仍在用
- instance.py 的 `_instance_next_actor`(2527)/`_instance_apply_enemy_act_ct`(2541)/`_instance_enemy_ct_acts`(2567)/`_instance_auto_defend_player`(2598)/`_instance_ct_queue`(2621)/`_instance_enemy_one_act`(2645) 仍被 instance.py 自身调用（2090 等 BT.Battle 调用点 + 行动推进）
- instance.py 2090 行 `BT.Battle.from_state({"type":"instance",...})` 仍当**单怪结算器**用（创建 Battle 后只调伤害公式，CTB 调度在 instance.py 侧手写）

### C. v141 Position 结构体 = 纸面落地
- `game/core/position.py` 定义 Position/from_player/from_db/key/resolve_map/resolve_subareas/as_mainland/cur_map_obj/player_position/position_to_db
- `game/core/__init__.py:119-121` 聚合导出 C.Position / C.cur_map_obj / C.player_position / C.position_to_db
- **grep 全项目消费方：只有定义处，命令层 0 处调用**（world.py/combat.py/instance.py 仍裸 cur_map/cur_subarea）
- 结论：结构体是"设计落地了一半"，命令层没铺开

### D. world_id 写入点齐全（v141 主链路 OK）
- 开本：instance.py:1911/1914 → inst:<uuid>
- 离开：instance.py:645 → mainland + destroy(646)
- 失败回城：instance.py:3369 → mainland + destroy(3374)
- 退队：social.py:477 → mainland
- 孤儿自愈：instance.py:245 → mainland + destroy(244)（在 instance_cmd 入口 236-247）
- 开本前清孤儿：instance.py:1892-1893

### E. cleanup_stale_instances 没人调（潜在泄漏）
- worlds.py:169 定义 cleanup_stale_instances，core/__init__.py:126 导出
- **grep 全项目：无调用方** → 大陆实例 24h 过期清理不生效，event_state 表膨胀 + 内存泄漏（P1 级）

### F. 显示层已统一（好事）
- instance.py `_instance_map_view` rooms 分支复用 world.py 的 `_map_nav_body`/`_map_blocks`（1318-1319）
- 回退 `_stage_virtual_map`(1368) 只对无 rooms 的老存档

## 补充自查（等待子 agent 期间）
### G. 副本遇怪 vs 野外遇怪 = 两份实现（实锤）
- `_instance_dungeon_move`（world.py:1725-1747）：`random.random() < discovery_agro(0.85)` 固定概率 + 从 `rooms[cur_room].monsters_left` 弹出
- `_travel_ambush`（world.py:1771+）：等级差概率（≥地图+5 不撞 / ≤地图-5 30% / 同级 8-18%）+ 子区域 monsters 池构建
- 副本**没有等级差威慑逻辑**（副本有等级门槛，固定概率可能是设计意图，但确是两份实现）
### H. 副本移动复用 `_subarea_arrive`（好事）
- `_instance_dungeon_move` 1723 行复用野外 `_subarea_arrive` 做到达视图 → 到达展示层统一
### I. v141 设计 = 分阶段收口（Phase 1-3）
- docs/CONTINENT_ISOLATION_v141.md:179 "不一次性改 389 处，用适配层分阶段收口"
- 当前只做到"定义了 cur_map_obj/cur_subareas 适配函数"（Phase 1 的雏形），热路径替换（Phase 2）未做
- 测试只测了 Position 结构体单测，没测命令层是否用了它
- 结论倾向：**这是"分阶段计划中途"，不是"落地不完整 bug"**——但确实存在"副本大陆里查错地图"的潜在风险（如果副本内代码用了裸 MAP_BY_ID.get）

## 待子 agent 确认/补充
- 老模式战斗（_instance_* CTB）是否真的还能被玩家触达（旧存档恢复？还是所有新本都走地图模式）
- 副本图门禁漏网（传送/组队跟随等入口）
- event_state 序列化 default=str 的类型风险（investigated set 落库前已转 list，其他路径待确认）
