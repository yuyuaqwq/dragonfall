# EXTENSIBILITY_REFACTOR_PLAN_v158.md — 副本战斗引擎合并（一套代码）

> 日期：2026-09-01
> 触发：鱼鱼拍板「只做成一套代码，共同的部分抽出来，必须独立的再各自实现」——
>       2026-09-01 副本连续 3 bug（卡战斗/通关误判/无限回合）全是"instance 外部轮转
>       与 battle 内部引擎脱节"造成，玩家在群里直指「没道理怪物跟玩家不是同一个代码」
> 范围：game/battle.py + game/commands/instance.py（副本战斗核心）
> 状态：📋 计划（待鱼鱼拍板）

## 1. 问题

当前**两套战斗驱动**：

| | 野外/世界Boss（正确） | 副本（错误） |
|---|---|---|
| 时间轴 | battle.py `_process_until` 事件队列（一套，玩家怪物同队列） | instance.py 手写轮转 `_instance_next_actor` |
| 敌方行动 | battle `_enemy_turn`（事件队列驱动） | instance `_instance_enemy_one_act`（外部手动） |
| 时间流逝 | `_now` 累积，事件按绝对时刻弹出 | `_now` 不持久化（今天 bug 根因，已临时修） |
| 玩家行动 | `b.player_turn` | `b.player_turn`（共用 ✅） |
| 多玩家 | 单人 | 副本多玩家（allies 快照） |

**代价**：instance 的轮转与 battle 引擎不同步，v152/v154 绝对时刻制改造后连续暴露 3 个 bug。
根因 = 副本绕过了 battle 事件队列，自己算"谁该动"，但 ct/时间/伤害结算全在 battle 里。

## 2. 目标架构：一套时间轴，instance 只留副本特有逻辑

```
battle.py（引擎，唯一时间轴）
  _process_until 事件队列：驱动 玩家行动 + 敌方行动 + cast_done + DOT + 宠物
  _after_actor_ct：行动者 next_act_at = now + 动作耗时（玩家/敌方同一逻辑）
  allies 快照：多玩家支持（已存在，治疗指定队友等）

instance.py（副本特有，不再碰战斗时间轴）
  ✅ 保留：房间移动、队长带队、组队锁、掉落结算、通关判定、Boss 阶段演出
  🗑️ 删除：_instance_next_actor / _instance_enemy_ct_acts / _instance_enemy_one_act
            （轮转/敌方行动全部交给 battle 事件队列）
  ➕ 新增：battle 事件回调钩子——敌方行动后/玩家行动后通知 instance
           （同步血量/仇恨/贡献/房间状态）
```

## 3. 核心设计：battle 事件队列驱动副本

### 3.1 副本 player_turn 改传 enemy_act=True

```python
# instance.py _instance_act
logs, ended = b.player_turn(action, skill_name, snap, enemy_act=True, target=target)
#      ^^^^^^^^^^^^^^^^^^^^ 原来 False（副本自己管敌方），改为 True（battle 管）
```

battle `_enemy_phase` 在 `enemy_act=True` 时调 `_process_until(p_ct)`，事件队列自动：
- 弹出 `enemy_act` 事件 → `_enemy_turn`（敌方行动，用当前玩家防御状态）
- 弹出 `cast_done` 事件 → 玩家伤害结算
- 弹出 `pet_tick` / DOT 等 → 持续效果

### 3.2 battle 加副本回调钩子（敌方行动后同步给 instance）

```python
# battle.py __init__ 增加可选参数
def __init__(self, ..., st: dict | None = None, ...):
    self._inst_cb = (st or {}).get("_cb")  # 副本回调（instance 注入）

# _process_until enemy_act 分支，敌方行动后：
if self._inst_cb:
    self._inst_cb("enemy_acted", {"unit": unit, "logs": mlogs})
```

instance 在回调里同步：敌方 hp 写回 st["enemies"]、仇恨/贡献累加、玩家倒地检查。
（回调是"通知"，不做决策——决策全在 battle 队列。）

### 3.3 多玩家轮流 = 各玩家独立 ct + battle 队列

- 每个玩家快照有独立 `ct`（绝对时刻）
- 副本命令层只需：**下一个玩家是谁** = `min(存活玩家 ct)`（一行代码，不再需要 `_instance_next_actor` 的敌我比较——敌方由 battle 队列驱动）
- 玩家行动后 `snap["ct"] = b.p_ct`（battle 算好，与野外一致）

### 3.4 超时自动防御

保留 instance 现有逻辑（60s 超时自动防御），但改为：**轮到该玩家时，若超时 → 调 `b.player_turn("defend")` 代替等 TA**。这与野外一致（battle 处理 defend）。

## 4. 迁移步骤（分批，每批过测试+提交）

### 批 1：battle 加回调钩子（无行为变化）
- `Battle.__init__` 加 `_inst_cb`（默认 None，野外不受影响）
- `_process_until` enemy_act 分支加回调调用（cb 为空 = 无操作）
- 全量回归

### 批 2：instance 玩家行动改 enemy_act=True
- `_instance_act` 的 `player_turn` 改传 True
- **先验证敌方行动由 battle 驱动**（用本地模拟工具 local_battle_sim.py）
- 回调同步敌方 hp/仇恨/贡献
- 副本测试 test_v137_dungeon + 全量回归

### 批 3：删除 instance 轮转死代码
- 删 `_instance_next_actor` / `_instance_enemy_ct_acts` / `_instance_enemy_one_act` 及依赖
- `_instance_act` 主循环大幅简化（只剩：选下一个玩家 → 调 player_turn → 回调同步）
- 全量回归

### 批 4：收尾
- 更新 test_v137_dungeon（若断言依赖旧轮转行为）
- 删临时修复（敌方 ct 流逝 / now 写回——合并后 battle 队列天然正确，可能不再需要）
- 全量回归 + 数值门禁

## 5. 一致性保证

- 野外战斗行为**零变化**（cb 默认 None，enemy_act=True 是野外既有路径）
- 副本战斗数值**不变**（同一套 player_turn/伤害公式/ct 折算）
- 每个批次先跑 local_battle_sim 复现 → 确认修复 → 全量回归 → 提交
- 合并后删掉的临时补丁（敌方 ct 流逝）由 battle 队列天然替代

## 6. 风险与回滚

- 风险：副本组队/房间逻辑与 battle 回调耦合出错 → 用 test_v137_dungeon + 本地模拟兜底
- 风险：敌方行动时机变化（原来 instance 手动，现在 battle 队列）→ 可能影响 Boss 阶段演出节奏，
  但数值/伤害结算不变（同一套 _enemy_turn）
- 回滚：每批独立 commit，git checkout 秒回

## 7. 完成定义

- [ ] 副本战斗时间轴完全走 battle 事件队列（enemy_act=True）
- [ ] instance 不再有轮转/敌方行动代码（纯副本逻辑）
- [ ] 野外战斗零变化（全量回归）
- [ ] 副本 3 个历史 bug（卡战斗/通关误判/无限回合）不复发
- [ ] 数值门禁 17/17 + 全量回归 231/231 全绿
