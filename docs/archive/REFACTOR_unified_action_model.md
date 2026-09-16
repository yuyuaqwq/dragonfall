# REFACTOR P4：battle 行动模型统一为「actor 执行配置/输入 → 结算」，引擎零身份

> 鱼鱼 2026-09-07 确认的执行模型：
> 1. 引擎结算入口接收已决定的 target（单 actor / 某层 / None），引擎不找目标
> 2. 怪物自动行动 = actor 的配置（auto_act / 行为数据），引擎读 actor 配置决定它
>    怎么行动；行为树/状态机是另一层实现，不在引擎内
> 3. 不存在玩家行动路径 vs 怪物行动路径——只有一条：actor → 行动 → 结算
> 4. target 可以是任意阵营的任意 actor，可以是某层（aoe），可以无对象

## 1. 目标形态

```
命令层/调度层：决定「哪个 actor、执行什么、打谁(target)」
    ↓ 调用统一入口
Battle.actor_act(actor, action, target)   ← 唯一人类/命令入口（=现 actor_turn+actor_act）
Battle.actor_auto(actor, ...)             ← actor 按配置自动行动（替代 _enemy_turn/_companion_act 身份分叉）
    ↓ 内部纯结算链（全程 target 参数，不摸 self.enemy）
_do_skill(caster, skill_info, target) / _do_attack(caster, target) / _deal_hit(...)
```

关键点：
- **target 类型**：单个 actor dict | side 名（对该层全部）| None（无对象技/自我技）
- 引擎方法签名带 target，不读"当前敌人"
- 不存在"敌方回合/玩家回合"方法——只有"某 actor 的行动"
- actor 的自动行为从 `actor.get("auto_act")` / 技能配置读，行为树/状态机外部实现

## 2. 现状差距
| 概念 | 现在 | 目标 |
|---|---|---|
| 人类行动入口 | actor_turn / actor_act（两套） | actor_act 一个 |
| 自动行动入口 | _enemy_turn（敌方）、_companion_act（随从）、pet tick | actor_auto（读 actor 配置） |
| 目标来源 | self.enemy / _active_target / _target_ctx 隐式全局 | 显式 target 参数 |
| 技能结算 | _actor_skill（玩家）vs _actor_skill_cast（怪）两套 | 一套 _do_skill(caster, info, target) |
| 行动上下文 | _cast_ctx（施法者）+ _target_ctx（目标）分散 | 显式参数或 ctx 对象贯穿 |

## 3. 分批
### A1: 删 4 个 helper（_side_actors/_side_primary/_hostile_actors/_hostile_primary）
### A2: 统一人类行动入口 actor_act（actor_turn 并进来）
### A3: target 显式化——结算链方法加 target 参数，消灭 self.enemy 读点
### A4: 自动行动统一 actor_auto（_enemy_turn/_companion_act 收编）
### A5: 技能管道去身份分叉（_actor_skill vs _actor_skill_cast 合一）
### A6: 全量回归 + 主仓同步

## 4. 验证
- 每批 py_compile + 定向测试
- 单怪/多怪/副本/PVP/世界Boss/随从 代表测试
- numeric 52 门禁
