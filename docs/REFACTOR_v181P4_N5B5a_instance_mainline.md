# N5b4-5a 副本战斗重写 v3 —— 行动命令层全重写方案（新会话执行蓝图）

> 2026-09-08 定稿。鱼鱼拍板："战斗+行动命令层全重写（新 InstanceBattle 命令层接管
> 副本行动入口），老 instance.py 战斗路由停用不手术，纯玩法命令按需迁移/保留引用"。
> **本文档是给新会话的执行蓝图**——照做即可，边做边核对行号（代码可能已漂移）。

---

## 0. 已落地状态（wt_ebuffs 分支，勿重复）

- commit `49def5d`：5a 施工图 v2（重写模型）
- commit `e8e62e8`：新控制器骨架 `game/commands/instance_battle.py`（battle2 原生、
  零 import 旧 battle）：
  - `build_battle(st)`：组 sides → B2 → `st["battle"]=to_state`
  - `act(st, gid, qq, action, skill, target)`：from_state → human_act → to_state 落回
    （heal/buff target=None 防奶敌）
  - `sync_views(st, gid)`：actors → st["players"]/enemies/boss 视图 + DB 血量（单点同步）
  - `next_actor_key(st)`：轮转 = sides player 存活 actor ct 最小者
  - 测试 `tests/test_battle2_n5b4_instance.py` 17 断言绿
- 全套 battle2 18 文件 579 断言绿

## 1. 目标架构（v3）

```
CombatCmds（main.py mixin，命令解析层，只留 4 处接线点）
  『攻击/技能/防御/逃跑』 instance 分流行 → 新入口（不再调老 _instance_act）
        │
        ▼
InstanceBattleRouter（新文件，全逻辑新写，命令层薄壳）
  轮转（谁行动/超时自动防御/等待提示）
  行动（调 instance_battle.act）
  结算（敌死→通关/肃清/切怪/失败/同归）
  账务（贡献 dealt/仇恨表/击杀账——5b 完善）
        │
        ▼
instance_battle.py（已落地：build_battle/act/sync_views/next_actor_key）
        │
        ▼
battle2 引擎（B2 human_act/sides/事件）

玩法壳（instance.py 保留：开本/组队/地图/探索/调查/宝箱/任务/撤退/通关奖励）
  读 st["players"]/st["boss"]/st["enemies"] 视图（sync_views 单点喂）
```

## 2. 命令注册约束（侦查结论，方案前提）

- 插件命令 = `Main`（main.py 285）继承命令 Mixin（PlayerCmds/CombatCmds/...），
  handler 经 filter 装饰注册进 astrbot 注册表（`game/commands/_platform.py`）
- **同名 filter 命令无法共存**（MRO 后者覆盖 / 或重复触发）→ 不能注册第二个『攻击』
- 因此『攻击/技能/防御/逃跑』命令的**消息解析层仍由 CombatCmds 提供**，其内部
  instance 分流行是唯一不可避免的接线点（每命令约 1-2 行：调用目标从
  `self._instance_act(...)` 改为新路由入口）——除此之外的副本战斗代码**全部搬新文件
  或删除**，CombatCmds 不承载副本战斗逻辑

## 3. CombatCmds 接线点（4 处小改，目标改调用）

| 文件/函数 | 现状 | 改法 |
|---|---|---|
| combat.py `attack`（~955 `type=="instance"`） | `self._instance_act(event,gid,qid,player,state,"attack",None)` | `self._instance_router(...)` 同参 |
| combat.py `skill`（~1218） | 同上 "skill", skill_name, target | 同上 |
| combat.py `defend`（~1574） | 同上 "defend", None | 同上 |
| combat.py `flee`（~1629 instance 分支） | 直接提示"副本 Boss 锁场不可逃" | 保留（副本战斗内不可逃语义不变） |

> 接线点改动的"老文件接触"仅此 4 行调用目标——把战斗逻辑全部留在新文件，这就是
> 鱼鱼要求的"不手术"（架构上同名命令无法避免的最小接触）。

## 4. 新文件 `game/commands/instance_router.py`（或并入 instance_battle.py）职责

`_instance_router(event, group_id, qq_id, player, state, action, skill_name=None, target=None)`
（async generator，对齐旧 _instance_act 调用协议）逐段重写（**不搬老代码，全新实现**）：

### 4.1 入口守卫
- 取大陆实例 st（`C.get_instance_st(world_id)` 优先，battle_state 行兜底——沿用
  `_instance_battle_for` 语义，逻辑新写）
- 肃清/无敌人 → 引导探索/深入（对应老 2465-2483）
- 当前行动者校验（`instance_battle.next_actor_key`）+ 非请求者 → 超时自动防御或等待
  提示（对应老 2494-2521；自动防御 = 对非请求超时者调 act("defend")，新写）

### 4.2 行动
- `instance_battle.build_battle(st)` 已在遭遇/切怪时调用过 → 直接用 `st["battle"]`
- `logs, ended, nxt = instance_battle.act(st, gid, qq, action, skill, target)`
- `instance_battle.sync_views(st, gid)`

### 4.3 账务（薄壳，5a 基础版）
- dealt/贡献/仇恨：从行动前后敌 hp 差算（沿用思路，新写读 st["battle"] sides）
- 防御挑衅/仇恨技 hate_mult 文案：5a 保留基础（读技能 cfg），仇恨选目标 5b

### 4.4 结算分支（对应老 2793-3045，全重写为读 actors 结果）
- 玩家倒地（sync_views 已标记 alive=False）→ 全员倒地失败 `_instance_defeat`（玩法壳
  函数保留引用调用）
- 敌全灭（st["enemies"] 视图空）→ 分支判定：
  - secret_guard_pending → 精英守卫奖励/宝箱（玩法壳函数引用）
  - rooms Boss 房 → boss_alive 标记 + `_instance_victory`（玩法壳引用）
  - stage_pending 有怪 → 击杀奖励 + 切下一只（**切怪 = build_battle 重新构造**）
  - stages 层清 → 地图模式/深入提示
  - 末层/无 stages → `_instance_victory`
- 死亡账：`battle.killed_actors` uid → st["killed_enemies"]/击杀任务（新写读
  battle state killed 键）

### 4.5 收尾展示
- 行动日志 + `_instance_battle_footer`（玩法壳保留，改读视图）+ "轮到 X 行动"提示
- `sync_players_db` 已由 sync_views 内 DB 同步替代

## 5. instance.py 删除清单（被 v3 替代，整段删，不留死代码）

| 删 | 说明 |
|---|---|
| `_instance_act` 战斗主体（约 2444-3077） | 被 router 替代 |
| `_instance_battle_cb`（2395） | 5b on_event 替代 |
| `_apply_team_effect`（3078）+ taunt 消费段 | 5b on_event 翻译器（暂删，5b 新写） |
| CT helpers 全家（3155-3230：living_player_cts/min_*_ct/next_actor/auto_defend_player/ct_queue/next_player_name） | 轮转 = instance_battle.next_actor_key + router 4.1 |
| `_sync_enemy_unit`（3277） | actors 权威 |
| `_instance_reset_player_cts`（1064） | ct 在 actors（遭遇/切怪 build 时播种） |
| `_enter_stage_combat` 的 Battle 构造段 | 玩法初始化保留，构造段调 build_battle |
| 旧 import：`from .. import battle as BT` / `BT._ct_*` 引用（1078/1143/1146/1172/198 等处） | 清零 |

**保留（玩法壳，只读视图）：** `_instance_build_state`/`_instance_start`（开本）、
`join_battle`（加入——ct 播种改 battle2 schedule 初值）、`_instance_build_enemy_array`
（敌组构造，build_battle 用）、`_instance_enemies_compact`（视图压缩）、
`_instance_kill_reward`/`_instance_victory`/`_instance_defeat`（结算奖励/任务）、
`_instance_map_view`/探索/调查/宝箱/撤退/任务/`_instance_battle_footer`（展示）。

## 6. 分步执行 + 验证（每步 commit）

| 步 | 内容 | 验证 |
|---|---|---|
| R1 | 写 `instance_router`（4.1-4.5 全逻辑，调 instance_battle + 玩法壳引用） | 单测：肃清守卫/轮转/超时自动防御/切怪/通关/失败 分支 |
| R2 | CombatCmds 4 处接线点改指向 router | 现有 battle2 全套 + 命令层冒烟 |
| R3 | instance.py 删除清单执行 + `grep BT.Battle` 清零 + 残留调用清零 | grep 验证 + 全套测试 |
| R4 | 端到端副本流程测试（拟真 DB 2 人开本 → 小怪/精英/Boss/死亡/通关） | 新流程测试绿 |
| R5 | HANDOFF 更新 + diff 给鱼鱼过目 + commit | — |

## 7. 行为差异（v3 完成后，5a 边界内）
- Boss 仇恨/嘲讽：回落默认目标（5b target_picker）
- 团队群奶/群体增益：不广播（5b on_event）
- 副本旧毒（boss.debuffs.poison）：battle2 state 不认 → 毒结算断（内容批迁 state dot）
- Boss 剧本 mech（转阶段/召唤/低血）：不触发（5c）
- 宠物：只存不驱动（宠物批）
- 玩家词条种子护盾（_instance_seed_battle_start_affixes）：玩法壳保留调用（行为不变，
  装配启用待拍板）
- 轮转细节以 battle2 ct/schedule 为准（不再有旧 CT 队列）

## 8. 会话接力口令
「继续 N5b4-5a v3，读 docs/REFACTOR_v181P4_N5B5a_instance_mainline.md（v3 执行蓝图）
+ HANDOFF §0.5 记录 8，从 R1 开始」
