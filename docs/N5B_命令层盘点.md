# N5b 命令层切换盘点（battle2 接命令层）——开工前必读

> 2026-09-08 会话。承接 docs/HANDOFF_battle2_new_session.md §5（N5b 还没开始）。
> 目的：把命令层对旧 `game.battle` 的全部依赖盘清，给 battle2 补 API / 改命令层的决策依据。

## 1. 引用旧 battle 的生产文件（9 个）

| 文件 | import | BT.Battle 用点 | 依赖深度 |
|---|---|---|---|
| game/commands/combat.py | `from .. import battle as BT` | 9 | 🔴 重（核心战斗循环） |
| game/commands/instance.py | 同 | 7 + BT._ct_initial_wait×4 | 🔴 重（副本战斗循环） |
| game/commands/economy.py | 同 | 3 | 🟡 中（约战/比试战斗恢复） |
| game/commands/player.py | 同 | 1 | 🟡 中（战斗内实时面板） |
| game/commands/tower.py | 同 | 1 | 🟢 轻（构造+存盘） |
| game/commands/world.py | 同 | 0 实际用 | 🟢 轻（仅 import） |
| game/commands/base.py | 同 | 0 | 🟢 轻（仅 import） |
| game/commands/misc.py | 同 | 0 | 🟢 轻（仅 import） |
| game/commands/social.py | 同 | 0 | 🟢 轻（仅 import） |

> scripts/* 的引用是临时脚本/旧模拟，不在切换范围（N6 删旧引擎时一起清）。

## 2. 命令层调用的旧 Battle 表面（b.xxx 全景）

### 2.1 构造 / 恢复
- `BT.Battle(btype, enemy, title_bonus, player=..., pet=..., enemies=..., dmg_mult=...)`（combat/economy/tower）
- `BT.Battle.from_state(state_json)`（恢复存档）
- 注：battle2 构造签名不同——`Battle(btype, sides, title_bonus, ...)`，无 player/pet/enemies 命名参数（sides-only）

### 2.2 存取 / dict 语义（battle 被当 dict 用！）
- `b.to_state()` → db.save_battle
- `b.get("map"/"name"/"hp"/"skills"/"buffs"/"debuffs"/"dot_res"/"adapt"/...)`（读战斗级字段，世界Boss）
- `b.setdefault("buffs", {})` / `b.setdefault("dot_act", 0)` ...（写战斗级字段）
- `b["name"] = ...`（世界Boss 直接塞键）

### 2.3 敌方查询（enemies/enemy）
- `b.enemies` → list[dict]（直接读 `u["hp"]`、`u["uid"]`、改 `u["hp"]` 同步全局Boss血量）
- `b.enemy` → 主目标 dict（死后变 {} → .get 兜底）
- `b.killed_enemies`（instance）、`b.e_minions`
- `b._enemy_dead()` → 敌全灭判定
- `b.e_defending` → 敌方防御中
- `b._tick_actor_dots(enemies, logs, force=True, caster=...)` → 强制结算敌方 dot

### 2.4 结果 / 行动
- `b.result`（"victory"/"defeat"/"fled"）
- `b.actor_act(action, skill_name, player, target=...)` → `(logs, ended, who)`（普攻/技能/防御/逃跑共用）
- `b.actor_turn(action, skill_name, player, enemy_act=False)` → `(logs, ended)`（PVP 用）
- `b.btype`（"monster"/"worldboss"/"instance"/"pvp"）
- `b.actor_turn`、`b._player_hit`（instance）

### 2.5 玩家内部查询（_p_* 私有方法）
- `b._p_buffs_bag()` → 玩家 buffs 袋（读 echo_bless/stealth/神龛）
- `b._p_poi_buff()` → 神龛祝福
- `b._p_stacks()` / `b.mech_stacks` → 玩家叠层
- `b._p_shields_bag()` → 玩家护盾
- `b._p_res()` → 玩家资源
- `b._focus` → 玩家 actor 引用（命令层直接改 `_focus["charging"]`、`_focus["buffs"]`、`_focus.setdefault(...)`）
- `b._player_stats(player)` → 战斗内实时面板（player.py）
- `b.p_ct` → 玩家 ct（instance）
- `b._now` / `b._tick_no` / `b._st` → 时刻/状态

### 2.6 常量
- `ACT_TICK`（combat import from battle：护盾剩余刻数折算 1刻=ACT_TICK秒）
- `BT._ct_initial_wait(spd)`（instance 构造怪物初始等待）
- `battle._remove_unit` / `battle._add_shield`（instance 直接调模块级函数？—— 待确认）

## 3. 架构张力（核心矛盾）

旧 battle.py 身兼两职：
1. **战斗引擎**（行动/伤害/效果结算）
2. **战斗状态容器**（dict 子类，命令层直接读写 enemies/玩家 buffs/战斗级字段，且序列化 JSON = battle_state.state）

battle2 设计（鱼鱼拍板）：**纯 sides-only 引擎**——`sides: {player:[...], enemy:[...]}`，玩家只是 human_controlled actor，引擎零游戏知识。

→ 命令层大量 `b.get/b.setdefault/b.enemies/b._p_*` 用法，**与 battle2 架构不兼容**。N5b 不能只换 import。

## 4. 适配选项（供拍板）

### 选项 A：battle2 加"命令层视图 API"（薄兼容层，不进引擎核心）
- battle2 的 Battle 加只读/低风险查询：
  - `enemies` → property 返回 sides["enemy"]（命令层读 hp/uid 同步用）
  - `enemy` → 主目标（首个存活或首个）
  - `result` → 战斗结果枚举（victory/defeat/fled）
  - `btype` → 已构造时存
  - `focus_actor` → 返回 human_controlled actor
- 玩家 buffs/资源查询 → 命令层改为 actor 字段直读（battle2 actor 有统一 state 容器）
- 战斗级自定义字段（map/name/hp）→ 命令层**不该写引擎对象**，改存 DB battle_state 旁路字段或 actor 无关的 battle["meta"]
- 优点：引擎仍干净；命令层改造可控
- 缺点：仍要改命令层所有调用点

### 选项 B：命令层大改，全面切到 battle2 新 API
- combat/instance/economy 全部重写调用逻辑：sides_of/hostile_of/focus/alive_actors + actor 直读
- 战斗级字段（map/name/全局血量同步）改走 battle_state.state 的"外壳字段"（to_state 结构已有 sides/type/now/... 之外可扩展）
- 优点：彻底，不留旧语义
- 缺点：工作量最大，改动面广，风险高（战斗是核心玩法，改错 = 玩家打不了架）

### 选项 C：分场景切换（先野外单体，再世界Boss/PVP/副本）
- 每个场景单独切 + 单独验证，逐步收口
- 优点：风险可控，每步可玩
- 缺点：命令层存在混合期（两套引擎并存代码路径）

## 5. 建议

先做**盘点文档细化 + battle2 补只读视图 API（选项 A 核心）**，再按场景逐个切。因为：
- 命令层"当 dict 用"的字段大多是战斗级元数据（map/name 等），本就不该进引擎——切到 battle_state 外壳字段符合架构
- 玩家 buffs/资源在 battle2 里是 actor 字段，命令层读 actor 即可（不再需要 _p_* 私有方法）
- 战斗核心（actor_act 语义）battle2 已有 act/human_act/actor_auto 对齐

真正硬骨头是 **worldboss 血量同步 + PVP 特殊逻辑 + instance 副本状态机**，这些要逐个拆。
