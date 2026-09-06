# v180F 战斗引擎通用 actor 化（v2.1——函数级改造蓝图）

> 基于 v2.0（通用 side 架构）+ 侦察报告的暗雷清单，落到函数级。
> 原则：每步跑测 + commit，最终形态无 player 中心残留（sides 可任意阵营）。

---

## A. 暗雷清单（该读 actor 自身、却读焦点/写死的点）

### A1. `_player_stats(player)` —— 面板聚合读焦点 buffs（伪 actor 化）
- L3987 `self._apply_buffs(st, self._p_buffs_bag())` → 应读 `player.get("buffs", {})`
- L3989-3991 `_p_poi_buff()` → 应读 `player.get("poi_buff")`
- L3994 `self._p_buffs_bag()` spd_down → `player["buffs"]`
- L3997 `self._p_buffs_bag().get("shadow_dance")` → `player["buffs"]`
- 修法：统一读入参 `player` 自身的 buffs（setdefault 惰性建袋）
- ⚠️ 连带：`_apply_buffs(st, buffs)` 本身已是纯函数（st, buffs）——好

### A2. `_enemy_stats(unit=None)` —— 无参默认 self.enemy
- 语义：读"当前行动敌方单位"面板；通用化后应显式传 actor
- 大量无参调用点（15 处）→ 需逐个确认上下文（大多在敌方行动结算中，unit 是行动者）
- 修法：默认参数改读 `self._active_target or self.enemy`（已有概念），长期改显式传

### A3. `_cast_stats()` 双轨（L1510-1513）
- `_cast_ctx` 为空 → `_player_stats(self.player)`；否则 `_enemy_stats(u)`
- 通用化：读 `_cast_ctx or self.focus`（任意 actor），不判断"是不是玩家"

### A4. `_is_focus_player(actor)` 判定（L10055）
- ①side ②引用相等 ③class_name 兜底
- 通用化后：应变成 `side_of(actor)` / `is_player_side(actor)`（按 side 字段，不按引用）

### A5. 承伤链 5 函数读焦点袋（伪 actor 化）
- `_roll_dodge`(9357-9361) / `_mitigate_chain`(9408-9413) / `_retaliations_and_buffs`(9734)
  / `_post_hp_lethal`(9898) / `_on_taken_rewards`(9995)：按 class_name 读 `_p_*`
- 修法：一律读入参 `actor` 自身 dict

### A6. `_guard_check` 只服务焦点玩家（10193）+ 挡刀池无 owner
- `if _is_player: dmg = self._guard_check(dmg, logs)` → 任意玩家侧 actor 受击都查挡刀
- 随从补 owner 字段；挡刀池按"受击者的随从"过滤

### A7. `_last_player or self.player` 隐式归属（8+ 处）
- 6620/6635/6671/7870/9102/9136/9147/9294/9303 → 应显式 owner/施法者 actor

### A8. `_damage_enemy` / `_damage_player` 命名即玩家中心
- `_damage_enemy(dmg, target=...)` 已有 target 参数 → 通用 `_damage_actor` 已存在
- `_damage_player(player, dmg)` = `_damage_actor` 薄壳 → 保留兼容
- 战斗核心伤害落地统一走 `_damage_actor(actor, dmg)`（按 actor.side 决定阵营）

### A9. 行动调度：`_process_until` 只排 enemy_act，玩家行动外部同步驱动
- 通用化：事件类型 `actor_act`（unit=任意 actor）；human control 的 actor 由外部驱动
- `_after_actor_ct("p"/"e")` → `_after_actor_ct(actor)` 写 actor["ct"]

### A10. 结局判定
- `_player_dead(player)` / `_enemy_dead()` → 按 side 全灭
- result: victory/defeat → winner_side/loser_side（兼容旧值映射）

### A11. 目标选择
- `_pick_enemy_target`（从 allies 选）→ `_pick_target(attacker)` 从敌对 side 选
- `_resolve_ally_target`（从 allies 选队友奶）→ 从同 side 选

### A12. 序列化（to_state/from_state 单焦点扁平键）
- → sides 数组落档（每 actor 状态自带）+ 旧档兼容读

---

## B. 改造顺序（依赖序，每步跑测+commit）

1. **sides 装配 + side 字段播种**：__init__ 支持 sides 入口；actor 全带 side；
   `side_of()`/`hostile()` helper
2. **A4** `_is_focus_player` → 按 side；**A1** `_player_stats` 读入参 buffs；
   **A3** `_cast_stats` 读 focus
3. **A5** 承伤链 5 函数读 actor 自身袋
4. **A8** 伤害落地统一 `_damage_actor`（消灭 _damage_enemy/_damage_player 命名中心）
5. **A6** 随从 owner + 挡刀按归属
6. **A7** `_last_player` 隐式归属 → owner/施法者
7. **A11** 目标选择按 side 敌对
8. **A9** 行动调度通用（actor_act + human/ai 来源）
9. **A10** 结局按 side
10. **A12** 序列化 sides
11. instance/combat 命令层适配
12. 测试迁移 + 门禁（怪vs怪 demo）
