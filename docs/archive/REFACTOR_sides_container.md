# REFACTOR P3d：Battle 容器全面 sides 化（enemies/allies 退役为只读视图）

> 鱼鱼拍板（2026-09-07）：彻底 B——引擎零预设阵营名，sides 完全数据驱动。
> "为啥会有 enemies，应该只有 actor 组吧" "别留兼容" "别又加兼容层"
> 铁律：不新增任何兼容壳；改动一路往前，禁止回滚正确方向。

## 1. 目标形态

Battle 内部**唯一容器 = self.sides**（dict[side_name → list[actor]]）。
- `self.enemies` / `self.allies` **不再是实体容器**——全部退役
- 需要"敌方/我方"聚合读的代码 → 走 `self._side_actors("enemy")`（side 名是数据）或遍历
- actor 归属阵营 = actor["side"] 字段（数据驱动，引擎不预设哪些 side 存在）
- 玩家驱动 = 命令层传 actor + `b.actor_act(...)`（actor 就是那个玩家，无身份特判）

### 1.1 容器退役映射
| 现状 | 去向 |
|---|---|
| `self.enemies` 实体 list（构造/增删/读 50 处） | 删实体；保留**只读 property** `enemies`（读 sides 所有非 "player" 阵营 actor 并集，兼容序列化/遍历旧读点）？——NO，鱼鱼不要兼容壳 |
| `self.allies` 实体 list | 删；读点改 `self.sides.get("player")` |
| `self.companions` | actor 已在 sides["player"] 组，companions 只读视图保留（随从有独立语义：召唤物/宠物归属玩家组但带 kind） |
| `enemy` property | 删（读点改显式目标/遍历敌对 sides） |
| `_focus` | 保留：命令层当前驱动 actor 引用（非引擎逻辑依赖） |

**容器读点改造**（battle.py 内 43+20 处 + core 模块 + commands）：
- `for u in self.enemies` → `for u in self._hostile_actors()`（helper：遍历非 player side）
- `self.enemies[0]` → `self._hostile_primary()`（首个存活敌对 actor）
- `self.allies` → `self.sides.get("player", [])`
- 增删（援军 m / remove unit）→ 操作对应 side 组

## 2. 分批（每批 commit+测试）

### B1: sides 权威化 helper + enemies 只读化准备
- 加 `_hostile_actors()`（所有非 player side 的 actor 扁平）/ `_hostile_primary()`
- 加 `_side_actors(side)` / `_side_primary(side)`
- 把 enemy property 内部改走 `_hostile_primary("player")`

### B2: battle.py 内部 43 处 enemies 读点改 helper
- 遍历→_hostile_actors / 取首→_hostile_primary / allies→sides["player"]
- 增删点改操作 sides

### B3: core 模块（battle_mech/affix/conds/we/food）b.enemies/b.allies 改 helper

### B4: commands（combat/instance/world/tower）b.enemies/b.allies 改 helper

### B5: 删 enemies 实体容器（__init__ 只建 sides；from_state 恢复只建 sides）
- enemies/allies 赋值点全删
- 测试同步

### B6: enemy property 退役（读点已全改 helper）

## 3. 风险控制
- 单怪野外 = sides{"player":[玩家], "enemy":[怪]} 特例，全程必须绿
- 多怪/副本/世界Boss/PVP 代表测试每批跑
- numeric 52 全量门禁
