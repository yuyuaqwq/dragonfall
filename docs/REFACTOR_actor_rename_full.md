# REFACTOR：战斗引擎全面去 player/enemy 身份命名 → sides/actor 通用模型

> 状态：APPROVED（鱼鱼 2026-09-07 拍板"全部改干净，一步到位"，引擎内不允许 player/enemy 命名）
> 铁律：不保留任何兼容壳/代理/过渡。battle.py + core + commands 全部同步改。
> 文档权威。每批 py_compile + 相关测试 + 全量回归。

## 1. 目标命名体系

引擎只有三种概念：
- **side**（阵营）：dict[str, list[actor]]。任意多阵营。
- **actor**（行动单位）：全同构 dict（buffs/stacks/hp/atk/side/kind...）。无身份特判。
- **action/ctx**（行动上下文）：一次行动 = (caster_actor, target_actor)，显式传递。

**废除的身份命名**：player / enemy / enemies / monster / boss / pet / companion / ally
（保留 kind 字段作为"表现/数据源"标签：kind="player"/"monster"/"pet"——数据层标签 ≠ 引擎逻辑分支）

### 1.1 容器
| 旧 | 新 |
|---|---|
| `self.player` | `self._focus`（焦点 actor，命令层 UI 用；引擎逻辑用 caster 显式传参） |
| `self.enemies` | `self._focus` 的敌对 side 组（sides 权威，无单列容器） |
| `self.allies` | `self.sides["player"]` 组成员（副本同 side 多 actor） |
| `self.companions` | 各自 actor 在 sides 对应组（side 由 actor.side 决定） |
| `self.e_minions`/`self.summons` | kind="summon" actor 在其所属 side 组 |

### 1.2 属性/方法重命名映射
| 旧（battle.py） | 新 |
|---|---|
| `self.enemy` | `self.primary_hostile(side)` → 返回该 side 的敌对首选 actor |
| `player_act(...)` | `actor_act(focus_actor, action, ...)` |
| `player_turn(...)` | `actor_turn(actor, ...)` |
| `_enemy_phase(player, ...)` | `_hostile_phase(actor, ...)` |
| `_enemy_turn(unit)` | `_hostile_turn(unit)` |
| `_player_skill(player, ...)` | `_act_skill(actor, ...)` |
| `_player_attack(...)` | `_act_attack(...)` |
| `_player_stats(player)` | `_actor_stats(actor)` |
| `_enemy_stats(unit)` | `_actor_stats(actor)`（合并） |
| `_enemy_mitigate(...)` | `_hostile_mitigate(...)` 或并入 actor 承伤链 |
| `_player_dmg_mult(player)` | `_caster_dmg_mult(actor)` |
| `_tgt()` / `_hit_tgt()` | `_cur_target()`（从 _act_ctx 读） |
| `_tgt_is_player()` / `_cast_is_player()` | 删（side_of(actor) 判断） |
| `_player_side_aoe_pool()` | `_aoe_pool(side)` |
| `_boss_*` | `_elite_*`（精英单位，非玩家身份但也不是"玩家专属"，实际是敌对 actor 特性） |
| `_pet_*` / `_companion_*` / `_spawn_companion` | `_summon_actor_*`（actor kind=summon/pet） |
| `_enemy_dead()` | `_hostile_all_dead(side)` |

### 1.3 变量/参数命名
- 参数 `player` → `actor`（行动者）或 `caster`/`target`（明确角色）
- `e`（enemy）→ `target`/`hostile`/`u`（unit）
- `ename` → `uname`
- 局部变量 `_pl_*`/`_p_*` → `_ca_*`/`_ac_*`
- 布尔 `enemy_act` → `auto_act`

## 2. 波及文件
| 文件 | 规模 | 角色 |
|---|---|---|
| game/battle.py | player 1038/enemy 107/47 def | 引擎核心 |
| game/commands/combat.py | b.enemy 37/b.player 12/player_act 6 | 野外战斗命令 |
| game/commands/instance.py | b.player 15/player_act 2 | 副本命令 |
| game/core/battle_mech.py | b.enemy 31/b.player 10 | mech handler |
| game/core/affix_effects.py | b.enemy 39 | 词条 handler |
| game/core/battle_conds.py | b.enemy 20 | 条件判定 |
| game/core/_we_executors.py | b.enemy 13 | 武器族执行器 |
| game/core/food_effects.py | b.enemy 12 | 食物 handler |
| game/core/effect_actions.py | b.enemy 10 | 效果动作 |
| game/core/weapon_effects.py/potion_effects.py | ~5-8 | 装备/药水 |
| game/core/item_templates.py | b.player 73 | 物品模板 |
| game/core/event_templates.py | b.player 25 | 事件 |
| game/core/poi_effects.py/title_conds.py | ~12 | 场景/称号 |
| game/core/passive_procs.py | ~2 | 被动 |
| tests/* | 大量 | 测试同步 |

## 3. 分批计划（每批独立 commit + 门禁）
### B1: battle.py 核心访问器 + focus 化
- `self.player` → `self._focus`（保留内部 `_focus` 字段 + `focus()` 访问器）
- `self.enemy` property → `primary_hostile()`；enemy setter 删
- 引擎方法改名映射（§1.2）中纯内部方法先改（_player_attack/_enemy_stats 等）

### B2: 行动上下文（_act_ctx）取代 _active_target/_target_ctx
- 玩家行动入口 actor_act/actor_turn 建 _act_ctx
- _tgt/_hit_tgt/_cast_* 收口到 _act_ctx
- 删 _active_target

### B3: core 模块（battle_mech/affix/conds/we/food/effect）b.enemy/b.player → caster/target

### B4: 命令层（combat/instance/economy）b.player/b.enemy/player_act → focus/actor_act

### B5: 表现层模板（item_templates/event_templates/poi/title）b.player 状态读 → focus/actor

### B6: tests 全量同步 + 全量回归绿

## 4. 验证矩阵
| 场景 | 代表测试 |
|---|---|
| 单怪野外 | test_commands_battle / test_v59_battle_status / test_v63_control / test_v97_07_quick_battle_use |
| 多怪 AOE | test_aoe_multi_target / test_aoe_status_persist / test_v114_formation |
| 副本 | test_v137_dungeon / test_v141_instance_world / test_commands_instance |
| 世界 Boss | test_v116_boss_trigger_phase |
| PVP | test_v85_pvp_honor |
| 元素/技能 | test_stage5_element / test_v1302c_mechanics |
| mech/词条 | test_v1252_mech_behavior / test_v138_dot / test_v83_bard |
| numeric 门禁 | scripts/run_numeric_tests.py（52 文件） |
