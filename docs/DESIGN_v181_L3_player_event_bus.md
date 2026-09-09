# L3 玩家事件层（Player Event Bus）——设计 + 排期

> 2026-09-09 鱼鱼拍板：「类似 Unity QFramework 这种框架你觉得怎么样」→ 格温评估：
> QFramework 全家桶（EventSystem+Command/IOC/BindableProperty）是单机客户端框架，整体不搬；
> 摘其「事件总线解耦」思想 + DDD 领域事件同步语义，做 L3 玩家级事件层。本文件 = 设计 + 排期。
> 关联：docs/DESIGN_effect_system_v2.md（L1 战斗内效果总线 N8 已落地）+
> docs/HANDOFF_battle2_effect_v2.md §9（L2 战斗级观察者 on_event 已落地）。
> 状态：✅ P0 字段级任务书已出（2026-09-09，真实代码侦察修订）——
> **docs/REFACTOR_v181_L3_P0_task.md**（ctx schema 逐字段/订阅注册表/回填顺序对照表/P1-P4 任务书）。
> 关键修订：手动接线已随 P4-9 落 combat._handle_victory 壳 L2034-2118（非 victory_settle 内）；
> 公会每日任务=每场+1 订阅 battle_victory（非逐只）；升级段建模为订阅方保行序。
> 审过后 P1（总线核心）可开工。
> 状态2：✅ **P1-P3 已落地**（同日）——P1 e26f92a 总线核心 / P2a b7f509c tower+weekly 下沉 /
> P2 ee19c45 field 迁移（combat 壳 L2034-2118 → 6 订阅方）/ P3 0f722cd instance+worldboss 收编
> （语义决策「任何击杀都算数」）。✅ **P4 收尾**（f9493e5 验证网+接入文档 + 本次 settlement
> 死字段瘦身与回写，见 §3 排期表 P4 行）。**L3 全批完成**。
> 新玩法加战斗反应 = services 里 `register("battle_victory", handler, blank_line=...)` 一行，
> 指南见 docs/L3_player_event_subscription_guide.md，不改任何结算函数。

## 0. 三层事件全景（为什么要补 L3）

| 层 | 位置 | 服务对象 | 粒度 | 状态 |
|---|---|---|---|---|
| L1 战斗内效果总线 | `battle2/effect_triggers.py` fire()，23 时机 | actor 效果（装备特效/词条/套装/Boss机制挂 actor.triggers） | 一场战斗 fire 数百次 | ✅ N8 落地，16 引擎点位插桩 |
| L2 战斗级观察者 | `battle.on_event` 注入钩子（fire 尾部广播） | 命令层：团队广播 `_instance_team_event` + Boss 导演 `make_script_event` | 战斗内联动 | ✅ N5b4-5E/5c 落地 |
| **L3 玩家级事件** | **缺位** | **任务/成就/公会/野王/塔卫/剧情/声望**（玩家账号级跨模块反应） | 一次战斗只有胜利/失败/每击杀 | ⚠️ 无总线，靠结算大函数手动接线 |

### 痛点（L3 要消灭的）
- `victory_settle`（services/battle_settlement.py 590 行）编排里**手动逐个调**：
  任务 `_update_quests` / 公会 `guild_kill_progress` / 成就 `check_achievements`（25 处调用）/
  野王 `wild_king_on_kill` / 塔卫 `tower_guard_on_kill` / 图鉴声望……
- 新加一个「击杀/胜利后要反应」的模块 = 去胜利结算大函数加一行 → 膨胀回 N8 要消灭的
  「硬编码触发链」病（战斗外版本）。
- 各模块要的上下文相同（group_id/qq_id/player/monster/result），却各自去结算函数里捞。

## 1. 方案要点（DDD 领域事件同步语义，非 QFramework EventSystem）

```
# 事件 = 已经发生的事实，带完整上下文；发布时订阅方可回填结果文案（同步）
# game/services/player_event_bus.py（新）
EVENTS = ("battle_victory", "battle_defeat", "monster_killed")   # 起步全集，可扩展

register(event, subscriber)     # 订阅：任务/成就/公会各自注册自己的 handler
fire(event, ctx) -> list        # 发布：按注册顺序跑订阅方，收集回填文案行

ctx = {group_id, qq_id, player, monster, result, lines: []}
# 订阅方往 ctx["lines"].append(...) 回填要追加进战斗结算的文案（任务进度行/成就解锁行）
```

### 关键设计约束（北极星对齐）
1. **引擎零游戏知识**：L3 在 services 层，battle2 完全不 import；战斗引擎只通过
   现有 on_event（L2）把「战斗结束/击杀」事实递给命令层 → 命令层/结算层 fire L3。
2. **同步 + 回填**：不是 fire-and-forget。订阅方文案必须回填进战斗结算日志
   （顺序 = 注册顺序，与现有手动调用的行序对齐，零文案变化）。
3. **分层不合并**：L3 ≠ L1。L1 一次战斗 fire 数百次（actor 级效果），L3 一次战斗只
   3 类事件（玩家级）。塞进同一总线 = 任务模块过滤几百个噪音。
4. **只摘 QF 思想，不搬全家桶**：不做 Command 类化 / IOC / BindableProperty / 弱引用
   自动反注册（无 UI 生命周期，Python 模块级注册表足够）。
5. **订阅方保持薄**：handler 只做「查自己进度 → 推进 → 回填行」，逻辑留在原 service
   函数（quests_flow.update_quest_after_battle 等原样搬进 handler 壳）。

### 事件全集设计（起步 3 类，扩展靠 data 声明不靠加 if）
| 事件 | ctx 关键字段 | 订阅方（现有手动接线迁移） | 回填行示例 |
|---|---|---|---|
| `battle_victory` | player/result/extra_kills | 成就（战果类）、图鉴、声望 | 📜 支线进度 3/5 |
| `battle_defeat` | player/result | 成就（失败计数类，若有） | — |
| `monster_killed` | player/monster（逐只） | 任务 kill_any/kill_elite/kill_boss、公会 kill_progress、野王/塔卫、成就击杀类 | 🎯 公会任务 4/5 |

> 说明：victory 内逐只怪 fire `monster_killed`（带 monster dict），任务/公会按怪匹配；
> 一次性战果类成就听 `battle_victory`。跟现有 combat._update_quests(k) 逐只调语义一致。

## 2. 落点与接线

```
game/services/player_event_bus.py    # 总线核心（EVENTS/register/fire，零业务 import）
game/services/battle_settlement.py   # victory_settle/defeat_settle 尾部 fire（替换手动段）
game/services/quests_flow.py         # 订阅 monster_killed → 原 update_quest_after_battle 逻辑
game/services/guild.py               # 订阅 monster_killed → 原 guild_kill_progress
game/services/... (成就/图鉴/野王/塔卫 后续批)
```

- fire 入口收拢在 settlement 编排尾部（或 router 3.5 账务段），命令层不散 fire。
- from_state/恢复路径不涉及 L3（纯同步一次广播，不落盘）。

## 3. 排期（依赖 N10 删旧合并 master 后）

| 批 | 内容 | 前置 | 验收 |
|---|---|---|---|
| L3-P0 | 字段级任务书 | ✅ **REFACTOR_v181_L3_P0_task.md**（2026-09-09，真实代码侦察修订：接线在 _handle_victory 壳；6 订阅方注册表含 blank 空行规则；ctx 加 kind/killed/side_effects 字段） | 设计文档定稿 commit |
| L3-P1 | 总线核心 `player_event_bus.py`（EVENTS/register/fire/容错/顺序）+ 纯单元测试 | P0 审过 | ✅ **e26f92a**（2026-09-09）：EVENTS 三元组/register 未知事件 raise/fire 容错+blank 空行规则/clear_registry(仅测试)；单测 15 断言全绿，零生产 import |
| L3-P2 | field 迁移试点：_handle_victory 壳 L2034-2118 整段 → fire（6 订阅方：guild/levelup/quests/weekly/野王/塔卫/成就；升级建模订阅方保行序；前置下沉 tower/weekly 的 inst 依赖） | P1 | ✅ **b7f509c+P2a 下沉 + ee19c45 主步**（2026-09-09）：tower/weekly 状态族迁 services；combat 壳手动段→battle_victory 订阅（行序+blank 总线保证）；删 _update_quests；全量 **208/208 绿**（含 2 测试断言过时更新） | 
| L3-P3 | instance + worldboss 收编（fire kind=instance/worldboss；成就订阅方 kind 分支；主线推进语义决策点交鱼鱼）+ 战斗入口成就调用收敛数可数下降 | P2 | ✅ **0f722cd**（2026-09-09）：语义决策落地（任何击杀都算数，quests/公会全 kind 推；levelup kind 守卫仅 field 保副本不升级节奏）；instance kill_reward/victory 逐成员 fire + worldboss 逐 contrib 玩家 fire；删 _instance_main_kill_progress；战斗入口成就调用 3→0。全量 **208/208 绿** |
| L3-P4 | settlement 瘦身收口（victory_settle 只留掉落/经验核心）+ 新订阅方接入文档（含剧情/声望示例）+ 回写本文件 | P3 | ✅ **f9493e5+收尾**（2026-09-09）：验证网 test_l3_player_events 18 断言 + 接入指南 docs/L3_player_event_subscription_guide.md（f9493e5）；收尾= settlement 瘦身以 P2/P3 为主体（玩家级反应已全出结算链——壳段 6 订阅方 + instance/worldboss 收编），settlement 段8 图鉴/声望按 P0 差异表 #1 **范围外不迁**（行序夹资源行中段，迁移=行序重组+零收益，记录在案）；本次死字段收口：victory_settle 返回 dict 删 16 个零消费者键（全仓仅壳消费 lines_pre/player/rule_txt，玩家可见输出零变化，快照测试全等）+ 设计/任务书/HANDOFF/指南四文档回写 |

> 冲突规避：L3 实施期避开 N10 C/D（删 battle.py + 测试处置）并行——settlement/combat/
> instance 同批文件会被两头改。N10 合并 master 后才开 L3-P1。

## 4. 明确不做（QF 评估否决项，防回潮）
- ❌ Command/Query 类化（commands 层已是路由 + services 已收业务，再套 = 每杀一只怪 new 对象）
- ❌ IOC 容器（无对象实例依赖网，模块级注册表够）
- ❌ BindableProperty（无 UI 实时刷新，输出是文字日志）
- ❌ 弱引用/自动反注册（无 UI 生命周期问题）
- ❌ L1/L3 合并单总线（语义粒度不同，合并 = 噪音过滤地狱）

## 5. 验收北极星
- 战斗结算**文案零变化**（订阅方回填行与现手动行逐行 diff）
- 新玩法加反应 = 注册一行订阅，**不改结算函数**
- 全量回归零新增红；numeric 52 门禁（若那时重建）绿
