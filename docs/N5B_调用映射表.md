# N5b 命令层调用映射表（b.xxx → battle2 等价）——施工图

> 2026-09-08 深夜自主推进。基于盘点文档 + combat.py 逐行分析。
> 目标：命令层文件从 `from .. import battle as BT` 切到 battle2，每个 b.xxx 怎么改。
> 红线：battle2 零改动（鱼鱼拍板选项 B）。翻译/适配全在命令层或桥里做。

## 0. 总原则

- **构造/恢复**：`BT.Battle(btype, enemy, tb, player=..., pet=..., enemies=...)` → `B2.Battle(btype, sides=bridge.build_sides(player, enemies), title_bonus=tb, pet=...)`
  - 注意：battle2 Battle 构造签名 `(btype, sides, title_bonus, dmg_mult, pet, st, hostile_map)`
- **存档恢复**：`BT.Battle.from_state(st)` —— battle2 也有 from_state，但只认 sides 结构
  - 新开战斗（battle2 to_state 产物）→ 直接用
  - 存量旧档（enemies/enemy 键）→ 先 migrate_old_state（桥实现）再 from_state
- **行动**：`b.actor_act(action, skill_name, player, target=...)` → `b.human_act(action, skill_name, player, target=...)`
  - 签名顺序完全一致！返回 (logs, ended, who) 一致
  - `b.actor_turn(action, skill_name, player, enemy_act=...)`（PVP）→ battle2 无对应
    → 用 human_act（battle2 玩家行动后自动推进——PVP 每回合玩家决策点不同，需验证）

## 1. 映射表（combat.py）

| 旧用法 | 位置 | battle2 等价 | 难度 |
|---|---|---|---|
| `BT.Battle(...)` | 探索/野王/世界Boss/PVP | `B2.Battle(btype, sides=bridge.build_sides(...))` | 中 |
| `BT.Battle.from_state(st)` | attack/skill/defend/flee | 同签名（新档直用；旧档先 migrate） | 中 |
| `b._focus = player` | 恢复路径多处 | battle2 不用设——sides["player"][0] 即焦点；`b.focus()` 返回 | 低 |
| `b._p_buffs_bag()` | 349/418/947/1650 | `actor = b.focus(); actor.get("buffs") or {}`（battle2 actor.buffs） | 低 |
| `b._p_poi_buff()` | 350/421 | `b.focus().get("poi_buff")`（make_actor 有 poi_buff 键） | 低 |
| `b._p_stacks()` / `b.mech_stacks` | 1668 | `b.focus().get("state")`（旧 stacks → battle2 state 容器） | 中 |
| `b._p_shields_bag()` | 1678 | `b.focus().get("shields")` | 低 |
| `b._p_res()` | 1755 | `b.focus().get("state")`（旧 resources → state 容器） | 中 |
| `b.enemies`（list 读） | 1790/2132/2144/2156/2165/2170/2254 | `b.sides_of("enemy")` | 低 |
| `b.enemy` | _b_enemy 已 sides 化 | `b.sides_of("enemy")` 首个存活 | ✅已改 |
| `b.result` | 多处 | battle2 同字段（victory/defeat/fled） | 低 |
| `b.btype` | 938/1183/1514 | battle2 同字段 | 低 |
| `b.actor_act(...)` | 942/1187/1518/1564/2145 | `b.human_act(...)` 同签名 | 低 |
| `b.actor_turn(...)` | 2558 PVP | battle2 无；用 human_act（验证推进语义） | 高 |
| `b.to_state()` | 多处 | battle2 同方法（sides 结构） | 低 |
| `b._now` | 1806 | battle2 有 _now | 低 |
| `b._enemy_dead()` | 2119 | 需迁移——改 `not any(alive in sides enemy)` | 中 |
| `b._tick_actor_dots(...)` | 2154 | battle2 DOT 由 schedule 自动结算；命令层强制 force 结算 → 无等价（battle2 human_act 后已推进含 DOT） | 高 |
| `b.killed_enemies` | instance | battle2 killed_actors（uid 列表） | 中 |
| `b.e_defending` | 2549 PVP | battle2 actor["defending"]（目标 actor 字段） | 低 |
| `b._focus["charging"]` 等 | 2536/2577 PVP | battle2 actor["charging"]（focus() 返回的 actor） | 低 |
| `b.get("map")` 等 | 世界Boss展示 2006/2010 | **战斗级元数据**（map/name/hp）→ battle_state.state 外壳字段（battle2 无 dict 语义） | 高 |
| `b.setdefault(...)` | 2060-2079 世界Boss | 同上 → state 外壳 | 高 |

## 2. instance.py 额外

| 旧用法 | 说明 |
|---|---|
| `BT.Battle()._player_stats(snap)` | 无状态构造调面板 → `E.player_final_stats(...)` 或 bridge.player_stats(snap) |
| `BT.Battle()._ct_cost(spd)` | 行动耗时 → battle2 schedule 有 action_time（查等价函数） |
| `BT._ct_initial_wait(spd)` | 初始等待 → battle2 构造播种 ct（act_time?） |
| `b.p_ct` | → b.focus()["ct"] 或 sides player ct |
| `battle._remove_unit` / `_add_shield` | 副本直接调旧引擎模块级函数 → 改走 battle2 landing/移除逻辑 |
| `b._st` | 副本内聚状态引用 → 命令层自己持有 st（battle2 无 _st） |
| `b._tick_no` | 时刻 → battle2 _now 换算 |
| `b.e_minions` | 敌方援军 → 无等价（命令层自己管理或 actors side） |
| `b.killed_enemies` | → battle2 killed_actors |
| `b._player_hit` | 战斗级 flag → state 外壳 |

## 3. 展示辅助（combat 内部方法改造）

| 方法 | 现依赖 | 改法 |
|---|---|---|
| `_b_enemy(b)` | 已 sides 化 ✅ | 不动 |
| `_battle_formation_panel(player, b)` | b.enemies 存活 | b.sides_of("enemy") |
| `_battle_footer(player, b, monster)` | monster dict | 不动（入参已是 dict） |
| `_resource_line(player, b)` | b._p_res() | b.focus()["state"] 映射 |
| `_battle_footer` 内 `_now` | b._now | battle2 有 |

## 4. 战斗级元数据（map/name/hp/dot_res...）去哪？

旧 Battle 是 dict 子类，命令层直接 `b.setdefault("map", ...)` 塞战斗级字段（世界Boss 的全局标识）。
battle2 Battle 不是 dict——不能塞。

**方案**：命令层维护"战斗外壳 state"（放 battle_state.state 的兄弟键或 meta 字段）：
- 世界Boss 开战时，map/name/dot_res 等存 battle_state JSON 的顶层（db row 的 state 之外 or state["meta"]）
- 展示时从 battle_state 读，不从 b 读
- 这符合架构：战斗级元数据不属于引擎对象，属于"存档外壳"

## 5. 存量旧档迁移（migrate_old_state）

桥里实现：
- 输入旧 state（enemies/enemy/player 键，怪含 lv）
- 输出 battle2 state（sides 结构）
- 旧怪 dict → actor（lv→level）；旧玩家 buffs/stacks/resources → actor 字段
- 命令层恢复战斗时：先判断 state 有没有 sides → 没有则 migrate

## 6. 切换顺序建议（每步可验证）

1. ✅ 数据桥 battle2_bridge（done, 64ab806）
2. 桥补 migrate_old_state + 战斗外壳 helper
3. 展示辅助方法改造（不依赖 BT 引擎的纯读函数）
4. combat.py 探索/遇怪构造切 battle2（新开战斗）
5. combat.py attack/skill/defend/flee 行动切 battle2
6. worldboss 分支切（battle_state 外壳 + 血量同步）
7. PVP 分支切
8. instance.py 切（最复杂，副本状态机）
9. economy/player/tower 轻文件切
10. 删旧 import + 全量验证
