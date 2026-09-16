# REFACTOR：battle 全面 sides/actor 化（去主怪单焦点）

> 状态：DRAFT（等鱼鱼确认方向）
> 触发：鱼鱼指出"不应该有主怪/怪物组概念，应该是每个阵营有自己的 actor 组"——
>   sides 基建（_rebuild_sides/side_of/hostile_sides/_pick_hostile_target）已存在，
>   但玩家侧主循环/伤害结算/显示仍大量绕 self.player vs self.enemy 单焦点。

## 1. 目标架构（Target State）

战斗的唯一组织方式 = **sides：dict[side_name → list[actor]]**，actor 全同构。

```
Battle
├── sides: {"player": [p1, p2, pet], "enemy": [e1, e2], "wolf_pack": [w1, w2, w3]}
├── 任意多阵营、任意多 actor；无"玩家/怪物"身份特判
├── side_of(actor) → "player" | "enemy" | "wolf_pack" | ...
├── hostile_sides(side) → 非自身阵营（通用敌对）
└── 所有行动 = (caster_side, caster_actor) 选敌对阵营目标行动
```

### 1.1 容器收敛
| 旧字段 | 去向 |
|---|---|
| `self.player` | `sides["player"][0]`（焦点 actor 引用保留 `self._focus` 供命令层 UI，非引擎逻辑依赖） |
| `self.enemies` | 废弃 → `sides` 各敌对阵营 |
| `self.enemy`（主怪代理） | 删除 |
| `self.allies` | `sides["player"]` 组成员 |
| `self.companions` | `sides["player"]` 组 |
| `self.e_minions`/`self.summons` | 归属各自召唤者 side |

### 1.2 访问器收敛
| 旧 | 新 |
|---|---|
| `self.enemy` | `self._focus_target_of(caster)` 或遍历敌对 sides |
| `self._tgt()` | `self._resolve_target(caster)`（按 caster side 的敌对阵营选） |
| `self.player` | `self._focus`（焦点玩家引用，仅命令层/UI 用） |
| `_active_target` | 删除 → 行动上下文 `_act_ctx`（caster, target）显式传参 |

## 2. 现状差距盘点

### 已 sides/actor 化（保留）
- enemies/allies/companions 阵列 + 单位级 buffs/stacks/defending/charging/ct
- sides 视图 + side_of/hostile_sides/_pick_hostile_target（敌方 AI 已用）
- 玩家 actor dict 播种（v180-B）
- e_buffs 删除（P3a 完成）
- 双向 actor 技能管线（_cast_ctx/_target_ctx，怪可施玩家技能打玩家）

### 残留单焦点（本次改造目标）
- [ ] `self.enemy` property + 49 处使用（主怪代理）
- [ ] `self.player` 200+ 处直读（很多应改 caster/actor）
- [ ] `_tgt()`/`_hit_tgt()`/`_cast_*()` 二元假设
- [ ] `_active_target` 全局漂移目标
- [ ] `to_state/from_state` 的 enemy 兼容键（收口后删）
- [ ] 显示层 `b.enemy` 直读
- [ ] 命令层（combat/instance）`b.enemy`/`b.player` 直读

## 3. 批次计划（每批 commit + 测试门禁）

### P1 焦点收敛（低风险，纯引用整理）
- self.enemy → self._enemy_primary()（= 焦点玩家的敌对主目标，保留语义）
- 为 P2 铺路：先加 `_side_actors(side)`/`_alive_side_actors(side)` helper
- 机械替换 self.enemy 使用点，语义保持

### P2 行动上下文化（核心，中高风险）
- 玩家行动入口 `player_act`：建 `_act_ctx = {caster, target}` 上下文
- 技能管线 `_cast_ctx` 保留；`_target_ctx` 从 _act_ctx 读
- 删除 `_active_target` 全局状态 → 行动上下文传递
- 敌方行动 `_enemy_turn/_enemy_phase`：已 sides 化，微调

### P3 伤害链 actor 化（中高风险）
- `_boss_dmg_filter`（已加 target）→ 全面 target 化
- `_deal_damage`/`_mitigate_chain`/`_damage_actor` 收口为 actor-only
- `_skill_finalize_damage` 等玩家技能链：caster/target 显式传参

### P4 显示层（低风险）
- combat.py/instance.py 状态栏：多阵营多 actor 展示（enemy → 遍历敌对 sides）
- PVP 显示同样处理

### P5 序列化收口（低风险）
- to_state 删 enemy 兼容键（改 sides/enemies 全量）
- from_state 读 sides/enemies（兼容旧档包装）

### P6 命令层适配（中风险）
- combat/instance 战斗入口、回合调度、结算：从 player/enemy 改 sides/focus

## 4. 风险与控制
- 每批：py_compile + 相关测试 + 全量回归
- 行为零变化优先（P1-P3 是重构不换行为；P4/P6 可能微调显示）
- 单怪=单阵营单 actor 特例必须全程绿（绝大多数测试是单怪）
- 多怪/副本/世界 Boss/PVP 各跑代表测试

## 5. 验证矩阵
| 场景 | 代表测试 |
|---|---|
| 单怪野外 | test_commands_battle / test_v59_battle_status / test_v63_control |
| 多怪 AOE | test_aoe_multi_target / test_aoe_status_persist / test_v114_formation |
| 副本多玩家 | test_v137_dungeon / test_v141_instance_world |
| 世界 Boss | test_v116_boss_trigger_phase |
| PVP | test_v85_pvp_honor |
| 元素/技能 | test_stage5_element / test_v1302c_mechanics |
| numeric 门禁 | scripts/run_numeric_tests.py |
