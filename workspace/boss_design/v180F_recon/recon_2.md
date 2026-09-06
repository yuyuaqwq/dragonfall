审计完成。以下是结构化输出（行号已逐行核对，全部基于只读源码侦察）。

---

# battle.py 5201–8200 区 + 承伤/挡刀/敌方选目标侧玩家容器审计（v180F party actor 化前哨）

## 1) 区 5201–8200 `self.player / self.allies / self.companions` 全量清单

该区共 **9 个直接容器引用行**（另有大量经 `_p_*` 焦点 helper 间接读 `self.player`，区内 13 次、全文件 257 次——见 §5）：

| 行号 | 函数 | 容器 | 代码 | 用途 |
|---|---|---|---|---|
| 6620 | `_apply_mech_effect` | `self.player` | `_pl_cap = getattr(self,"_last_player",None) or self.player or {}` | 读施法者玩家，叠层 cap 术前记录（hunt_mark/soul_mark/poison） |
| 6635 | `_apply_mech_effect` | `self.player` | 同上 `_pl_cap` | 术后补层走 `_proc_pm(_pl_cap)` 被动 |
| 6671 | `_apply_mech_effect` | `self.player` | `_pl_mark = … or self.player or {}` | `mech=mark` 鹰眼/追踪印记额外层用施法者被动 |
| 7076 | `_enemy_turn` | `self.allies` | `if self._st and self.allies and player:` | 副本判定门：有 st+allies → 进入敌方目标重选（见 §4） |
| 7385 | `_apply_buffs` | `self.player` | `_pv = (self.player or {}).get("pet_buff_vals",{}).get(attr)` | 读当前焦点玩家宠物攻/暴 buff 强度（敌方/玩家共用 est 合成） |
| 7724 | `_pet_ensure_actor` | `self.companions` | `self.companions.append(pet)` | **写**：宠物 actor 化入 companions（side=player/kind=pet/hidden/untargetable） |
| 7850 | `_tick_actor_dots` | `self.player` | 注释（caster 回落语义说明） | 玩家毒怪时 caster 缺省回落当前行动玩家 |
| 7867/7870 | `_tick_actor_dots` | `self.player` | `_act_pl = getattr(self,"_last_player",None) or self.player` | 怪被 dot 结算取玩家施法者强度面板（`_last_player` 优先） |

**该区无 `self.allies` 写操作、无 `self.companions` 读（除 7724 追加）**——治疗/增益区的队友目标解析（`_resolve_ally_target`、`_skill_heal` 的 `target_ally`、3742、6410、6434）全部在 5201 行之前/走参数，本区不直接碰容器。

## 2) 承伤侧身份区分（`_damage_actor` / `_damage_player`）

**现状架构（10138-10244，v177/v180-B 已 actor 化）：**
- `_damage_player(10246)` = 薄壳 → `_damage_actor(player,…)`；仅 3 处调用（3069/3346 敌方 cast_done 落地、`_enemy_turn` 直接段）——副本 `_instance_enemy_one_act` **不走** `_damage_player`（见 §4）。
- `_damage_actor` 是统一承伤核心，**actor-agnostic**：B/EFF/RES/MS/CH/HITS/SH/RL 全部读 `actor` 自身 dict 字段（10156-10164）。
- **唯一保留的身份分叉 = `_is_focus_player(actor)`（10165）**，作用仅 3 处：
  1. `TARGET = self.enemy` 反击/反伤目标（10166-10167）；
  2. 蓄力打断清 `self._p_set_charging(None)` vs `actor["charging"]=None`（10180-10183）；
  3. 怪物盾 halve 吸收 vs 玩家盾全额（10215）——以及 10193 `if _is_player: dmg=self._guard_check(...)`（挡刀只服务焦点玩家）。
- `_is_focus_player`（10055-10086）三级判定：**① actor["side"]=="player" 显式优先 → ② 引用相等（`actor is self.player` / `actor in self.allies`）→ ③ class_name 兜底且排除 enemies 阵列**。
- 承伤内部路由仍有一批按 `class_name` 分叉读**焦点袋**而非 actor 自身：`_roll_dodge`（9357-9361 `_p_buffs_bag/_p_eff/_p_res`）、`_mitigate_chain`（9408-9413）、`_retaliations_and_buffs`（9734-9737）、`_post_hp_lethal`（9898-9901）、`_on_taken_rewards`（9995-9998）——**这些都是 `self.player` 焦点引用，不是 actor 参数**。注释自称"actor 通用"但数据源读焦点，是伪 actor 化残留（非焦点玩家挨打会吃到焦点玩家的被动/套装）。

**party actor 化后承伤侧改动清单（diff 级）：**
1. `_is_focus_player` ② 分支：`self.player`/`self.allies` 引用判定 → `actor in self.party`（或去掉——side 字段若全员就位可直用 ①）；③ class_name 兜底逻辑删除。
2. 上面 5 个函数的 `_p_*` 焦点袋读法 → `actor.setdefault(...)` 自身 dict（`_roll_dodge` 9378/9553 的 `_we_ed3(self,self.player,…)`、`_mitigate_chain` 的 novice_first_turn_guard 同理改传 `actor`）。
3. `_damage_actor` 内 `_is_player` 语义从"是否焦点玩家"升级为"是否玩家侧 actor"（is_player_side）——否则 party 里非当前行动者挨打时挡刀（10193）、护盾 halve、反击目标全错。
4. `_player_dead(player)`（10255）与 `_enemy_dead` 是单参数硬编码——party 后死亡判定要对整阵循环。
5. `_p_*` 全文件 257 处（`_p_buffs_bag`73/_p_res 68/_p_eff 37…）需迁到 `actor_of(side)` 参数化（区内 13 处属其中）。

## 3) `_guard_check`（9267-9345）读 companions 的方式

- 过滤：`guard_actors = [s for s in self.companions if s.get("guard",dict) 且 mode∈{absorb,redirect}]`（9279-9281）——**不读 side**，注释说"side=player"但代码没过滤。
- 分两池：`_absorb_pool`（宠物影袭/铁壁缩壳，冷却制，kind=pet 解锁+饱食 gate 9325-9329）；`_redirect_pool`（召唤物，概率制，需 hp>0 且 chance>0，9286-9288）。**redirect 优先于 absorb**（9292）。
- **owner 读取 = `self.player or {}`**（9294 算 summon_power、9303 算 def 反推 atk）——**不是** `_last_player`（对比 `_companion_act` 9102/9136/9147 用 `_last_player or self.player`，此处是反例）。
- 随从死亡/消散直接 `self.companions.remove(s)`（9314/9318）；absorb 命中整伤拦截返 0（9344）。

**已 actor 化的挡刀找 owner：**
- **companion actor 自身没有任何 owner 字段**（`_spawn_companion` 8981-9000 只写 side/kind/buffs/guard，无 owner/owner_id）；owner 全靠在调用时刻猜 `self.player`/`_last_player`。
- 召唤物 `_spawn_companion(cfg, player, …)` 的 player 参数（8951/9011 链路传入）就是召唤者，但**没有落到 actor 上**——party actor 化必须：**装配时写 `actor["owner"] = owner_actor`（或 owner_uid）**，`_guard_check` redirect 池按 owner 归属过滤（谁挨打只触发谁的随从挡刀）、absorb 冷却/文案取 `guard_actor["owner"]`。
- 后果链：随从归主人不归 party，`guard` 触发条件 10193 `_is_focus_player` 在 party 下要变成"被击 actor 是玩家侧 + 该 actor 的 companions 池"。

## 4) 敌方选目标：副本 vs 野外（`_enemy_turn` 7055 / `_pick_enemy_target` 1166）

| 场景 | 分支 | 选目标逻辑 | 结算目标 |
|---|---|---|---|
| **野外/单人**（无 `_st`/无 `self.allies`） | 7076 条件不成立 | `player` 原样传入即目标 | `self.player` = 该玩家 |
| **副本**（`btype=instance`，带 `_st`+`allies`） | 7076-7086 | 原目标已死→重选；`_st["_enemy_pick_target"]` 默认 True → **`_pick_enemy_target(e)`** 按 monster_mods `target_policy`（hate_top/random/weakest/backline/front，缺省 boss=hate_top 否则 front） | 选中者 → `_load_player_state(qq_id)` 把 `self.player` **换绑**为该快照 |
| `_pick_enemy_target` 内部 | 1166-1206 | 嘲讽 `st.taunt_target` 强制优先（1181-1186）；仇恨表 `st.threat`（1188-1191）；`FM.pick_by_policy` 共享算法 | `self._load_player_state(picked qq_id)` 并返回快照 |

**副本实际驱动不在 battle 事件队列**（instance 层 `_instance_enemy_ct_acts` 3201 → `_instance_enemy_one_act` 3317）：instance **每次敌方行动现造一个单怪 Battle**（3384-3388，`allies=[存活成员快照引用]`），`b._load_player_state(tkey)` 后调 `b._enemy_turn(snap, unit)`（3397）→ 引擎内部若重选会换绑 `self.player`，dmg 写回 `snap["hp"]`（3447）。副本的 `_damage_player` 不被直接调用（引擎内 cast_done 分支由 `player_turn(enemy_act=True)` 驱动时才走 3346）。
**敌方可多次行动、每次独立 Battle → `self.player` 换绑/焦点反复横跳是设计行为**，玩家行动侧（2568-2626 from_state + `b.player=snap`）同 Battle 内 allies 引用同步写回。

## 5) 判断：离 party actor 数组还差什么

**好消息（已就位）：** 承伤核心已 actor dict 化（`_damage_actor` 10138）；玩家战斗可变状态权威已迁 actor dict（__init__ 660-703 播种，焦点只留指针）；随从/宠物已收 `companions`（side/kind/buffs）；敌方阵列 `side=enemy`（8925 等）；`_is_focus_player` side 优先判定已存在；敌方选目标算法共享 `FM.pick_by_policy`。

**缺口清单（按改造优先级）：**

| # | 缺口 | 证据行 | 影响 |
|---|---|---|---|
| 1 | **`self.player` 单焦点指针横跨全场**——没有 party 数组，只有"当前焦点"可承伤/挡刀/被点名；非焦点成员只是 allies 被动引用 | 10068、2622、3390、1070 | party 化 = 焦点语义 → 数组索引语义，全局重构点（_p_* 257 处） |
| 2 | **承伤函数伪 actor 化残留**：`_roll_dodge/_mitigate_chain/_retaliations_and_buffs/_post_hp_lethal/_on_taken_rewards` 按 class_name 读 `_p_*` 焦点袋而非 actor 自身 | 9408-9413、9734-9737、9995-9998 | 非焦点玩家受击吃错被动/套装/资源 |
| 3 | **`_is_focus_player` 是唯一身份口且绑 self.player/allies 引用**——必须泛化为 side 判定 + party 归属，并新增 `is_player_side()` | 10055-10086 | party 挡刀 10193/反击 10166/盾 halve 10215 全依赖它 |
| 4 | **companions 无 owner 字段**：挡刀/宠物行为/召唤物归属全靠猜 `self.player`/`_last_player` | 9294、9303、9102 vs 9314；装配 8981-9000 | 需 `actor["owner"]` 落库，guard 池按 owner 过滤 |
| 5 | **`_guard_check` 只服务焦点玩家**（10193 `_is_player` 门）+ 挡刀池不过滤 side | 10193、9279-9281 | party 前排坦克挡刀、他人随从不误挡 |
| 6 | **敌方单体目标结算只有单焦点**：`_pick_enemy_target` 一次选一人、`_load_player_state` 换绑，无"AOE 打多人/点名分摊"落地（instance 每动现造 Battle 也印证） | 1166-1206、3384-3397 | party 后敌方 AOE/群体结算需遍历 party，而非换绑单焦点 |
| 7 | **`_last_player` 与 `self.player` 双轨**：`_apply_mech_effect`(6620/6635/6671)、`_tick_actor_dots`(7870)、`_companion_act`(9102+) 都 `_last_player or self.player`——party 后应统一为"事件关联 actor" | 5630、8407、1294 | 谁施放谁吃被动必须跟 actor 走 |
| 8 | `_player_dead(player)`/`_enemy_dead()` 单参；死亡结算、victory/defeat 判定按单人写死 | 10255、10250、3195-3197 | 全员倒地判定需遍历 party |
| 9 | 治疗/增益的队友目标 = allies **按名字/编号解析**，技能管线 `_target_ctx` 是瞬态上下文非数组成员 | 2650-2669、6410、6946-6949 | party 内索引寻址需替换 |
| 10 | `self.summons` 是 companions 的兼容 property；`_post_hp_lethal` 死亡契约 9929/9933、`_remove_unit` ally 侧 9256-9264 都在容器级 remove，无归属路由 | 700-703、930-955、9256-9264 | 数组化后 remove/compact 需按 side+owner |

**一句话结论**：承伤/挡刀/敌方选目标这块**核心结算层已 actor 化大半**（`_damage_actor` 通吃 + side 字段就位），但玩家侧仍是"**单焦点玩家 actor（self.player）+ allies 引用列表 + 无归属 companions**"的三件套——差的是：①一个 `self.party`/`player_actors` 权威数组（allies 列表 + 焦点语义合一）；②承伤链 5 个函数从 `_p_*` 焦点袋迁到 actor 自身袋；③`_is_focus_player` 泛化 + companions/随从补 owner；④敌方目标/挡刀从"换绑单焦点"升级为"按数组选/按归属过滤"。改造后 `_damage_player` 薄壳、`_pick_enemy_target`、`_guard_check` 三者都可保持签名、只改内部取值源。

---

**备注**：5201-8200 行区间本身不含 `_guard_check`（9267）/`_damage_actor`（10138）/`_is_focus_player`（10055）——三者位于承伤侧（9267-10256），已在 2/3/5 节按任务要求覆盖。所有行号已用逐行脚本核对，无改动文件。