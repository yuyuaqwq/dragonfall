所有关键路径已经核查完毕（8201–10255 段 + 前文依赖点 + 命令层调用点）。以下是结构化审计清单。

---

# 审计：battle.py 8201–10255「tick/随从/序列化/收尾区」玩家侧容器使用模式

## 0. 容器总览（先厘清当前 4 个容器的角色差异）

| 容器 | 定义/初始化 | 内容物 | 身份判定 | 状态容器存放 |
|---|---|---|---|---|
| `self.player` | 660 行 `= player or {}`（dict 引用） | 当前焦点玩家 actor | `_is_focus_player` ①`side=='player'`②引用相等 | **Battle 级焦点字段实际指向它**：`_p_buffs_bag/_p_res/_p_eff/_p_stacks/_p_shields_bag/_p_hot/_p_cooldown`（1523-1536 全部 `(self.player or {}).setdefault(...)`）→ 全引擎玩家 buffs/resources/DOT/hot/regen 落它身上 |
| `self.allies` | 636-639（instance 引用 st 存活玩家快照）/ 659 `= allies or []` | **只装玩家**（副本全存活玩家快照引用；野外不传=空） | `_is_focus_player` ②引用相等兜底 | 玩家快照自身 dict（与 self.player 同构）；敌方行动直接扣快照 hp |
| `self.companions` | 703 `= []` | **我方非玩家实体**（kind=pet / kind=summon，side=player） | 不参与玩家焦点判定 | actor 自身 dict（buffs/hp/guard/auto_act 字段全在自己身上） |
| `self.summons` | **property（930-951）** | companions 里 `kind=='summon'` 的过滤视图 | — | 无（读=写回 companions；setter 整袋替换时保留非 summon） |

→ **注意**：`self.summons` 在 8201+ 段里是「写回 companions 的纯读视图」，不是独立数组。

## 1. 8201–10255 玩家侧容器全部使用点（行号=实际文件行号，函数=所属方法）

### self.player（20 处）
| 行 | 函数 | 用途 |
|---|---|---|
| 8607 | `_advance_time` | 兜底取 `_pl_now = self.player or {}` → 喂 `_process_tick_effects`（regen/dot 卡 actor 为空的回落 player） |
| 8663 | `_monster_dodge_check` | 攻方玩家精准上限钳制（读 self.player 面板 precise） |
| 8753 | `_damage_enemy` | `attacker is None → self.player` 作默认攻击 actor（被动乘区来源） |
| 8819 | `_damage_enemy` | 守卫压制条件读玩家等级（`self.player or {}.get("level")`） |
| 9004 | `_spawn_companion` | 古树光环 `atk_up_all` 挂 p_buffs 需 player 在场 |
| 9102/9136/9147 | `_companion_act` | 宠物技能 owner = `_last_player or self.player`（伤害面板/治疗目标/buff 目标） |
| 9235-9245 | `_remove_unit` | 击杀时 `_we_proc(kill)` 特效 + `focus_full_on_kill` 回满精力（读 `_p_res()/self.player`） |
| 9294/9303 | `_guard_check` | 召唤物 redirect 挡刀读 owner summon_power/def（反推 atk） |
| 9378 | `_roll_dodge` | 新手首刻闪避词条（`_we_ed3(self, self.player, ...)`） |
| 9553 | `_mitigate_chain` | 新手首刻格挡词条（`_we_ed4(self, self.player, ...)`） |
| 10060-10068 | `_is_focus_player` | 引用相等 → 玩家；allies 成员同判 |

### self.allies（4 处）
| 行 | 函数 | 用途 |
|---|---|---|
| 9258-9264 | `_remove_unit`(side=ally) | 副本玩家死亡：过滤 hp>0 存活 + `compact(self.allies)` 压缩站位——**玩家死亡移除走 allies** |
| 10070 | `_is_focus_player` | allies 成员引用判定 |

### self.companions（10 处）
| 行 | 函数 | 用途 |
|---|---|---|
| 9001 | `_spawn_companion` | **召唤入队**：`self.companions.append(actor)`（唯一增入口，宠物/召唤共用装配） |
| 9178/9190 | `_companions_trigger` | auto_act 触发扫描 + 死亡清理扫描（遍历副本） |
| 9195 | `_companions_trigger` | **死亡移除**：hp<=0（排除 pet/无 hp actor）`self.companions.remove(c)` |
| 9279 | `_guard_check` | 挡刀池构建：`[s for s in self.companions if guard dict]`（absorb+redirect 双池） |
| 9314 | `_guard_check` | absorb_once 随从挡 1 次后 **直接 remove 消散** |
| 9318 | `_guard_check` | redirect 随从 hp<=0 **remove** |
| 9933 | `_post_hp_lethal` | 死亡契约祭品池 = `[c for c in companions if kind=='summon']`（排除宠物） |
| 9938 | `_post_hp_lethal` | 暗影祭司死亡契约牺牲 → **remove** |
| 9956 | `_post_hp_lethal` | 牧师死灵线死亡契约牺牲骷髅 → **remove** |

### self.summons（3 处，全部是 property 视图读）
| 行 | 函数 | 用途 |
|---|---|---|
| 9021 | `_summon_entity` | 同模板数量上限判定 `[s for s in self.summons if tid]` |
| 9929 | `_post_hp_lethal` | 死亡契约可用性 `self.summons and not _death_pact_used` |
| 9947 | `_post_hp_lethal` | 死灵骷髅代死条件 `[s for s in self.summons if tid=='skeleton' and hp>0]` |

## 2. 重点：companions 增删 / 宠物 actor 化 / auto_act 触发

### 增删链路总表
| 动作 | 函数（行） | 当前实现 | 收编 party 后的变化 |
|---|---|---|---|
| 技能召唤 | `_skill_apply` 6421 → `_summon_entity`(9011) → `_spawn_companion`(8951, **9001 append**) | 计数查 `summons` 视图 → `companions.append` | append 目标换成 party；**上限计数** 9021、skeleton_cap 9026 需改扫 party kind=='summon' |
| 药水召唤 | `potion_effects.py` 429 → `_spawn_companion` | 同上（不吃 summon_power） | 同上（potion_effects 直接读 `battle.summons` 423 行也需换） |
| 宠物入列 | `_pet_ensure_actor`(7670, **7724 append**) | 同 dict 就地补字段 + append | 宠物进 party 数组后：① 需要从 party 里能**引用恢复**（现靠 `self.pet` 独立引用 + `any(c is pet)` 幂等 7688）；② hidden/untargetable 字段仍是字段，位置语义（rank/reach）需补播种 |
| 挡刀消散 | `_guard_check` 9314/9318 | `companions.remove(s)` | remove 换 party.remove（同引用即可） |
| 死亡移除 | `_companions_trigger` 9195 | `companions.remove(c)` | 同上 + 需同步 `allies`（玩家）压缩逻辑是否统一 |
| 死亡契约牺牲 | `_post_hp_lethal` 9938/9956 | `companions.remove(fallen)` | 同上；`_skels`/`_sacrifice_pool` 过滤 `kind=='summon'` 保留即可 |
| 副本玩家死亡 | `_remove_unit` side='ally' 9258-9264 | allies 过滤+compact | **若 allies 也被 party 收编**：这是现成模板——玩家死亡=过滤+compact |

### `_pet_ensure_actor` / `_pet_ensure_guard`（7670 / 7728，都在 8201 前但直接支撑本区）
- 调用点：__init__ 834-835（新战）、from_state 1380-1381（恢复）、`_reschedule_pet_tick` 7760-7761（幂等兜底）。
- **依赖 `self.pet` 独立引用**（7685 `pet = self.pet or {}`）与 `self.companions` 同 dict 双向绑定：actor 化=给 pet dict 补 `side/kind/buffs/hidden/untargetable/auto_act`，guard=补 `guard` dict；auto_act 从 PET_POOL skill_type 翻译（7700-7723），block 型不配 auto_act 走 guard。
- **收编 party 的炸点**：只要 pet dict 仍以 `self.pet` 持有、同引用进 party，`_pet_ensure_actor` 的幂等检查 `any(c is pet for c in companions)` 换成扫 party 即可，语义不变。但 from_state 的 pet_act tick 恢复用 `actor_ref == "pet"` → 需要 pet 引用（1346/1356-1357），若 pet 只存在于 party 而 `self.pet` 被删，恢复路径要先按 `kind=='pet'` 从 party 找回引用。

### auto_act 触发点
| 触发 | 行 | 机制 |
|---|---|---|
| `trigger=player_act` | `player_turn` 3022-3023 → `_companions_trigger("player_act")` 9172 | 玩家行动尾部扫 companions（召唤物普攻） |
| `trigger=interval` | `_TICK_HANDLERS["pet_act"]` = `_th_pet_act` 545-581 → `_companion_act(battle.pet)` 568 | pet_act tick 卡驱动，**直接传 battle.pet 引用**（不是从 companions 里取） |
| 执行 | `_companion_act` 9054 | 读 actor.auto_act.act.type，owner=`_last_player or self.player` |

→ **收编 party 影响**：`_th_pet_act` 568 行的 `battle._companion_act(battle.pet, ...)` 是「宠物动作不扫 companions、直取 self.pet」的特殊通道。party 化后应统一为「从 party 找 kind=='pet' 的 actor」或保留 self.pet 引用。而 9172 的 `_companions_trigger` 遍历从 companions 换成 party 时，**必须过滤掉玩家本体**（否则 party 里带 auto_act 的玩家成员会被误触发——虽然玩家无 auto_act 字段所以现状无碍，但语义必须显式）。

## 3. tick_effects / 时刻推进：player / allies / companions 各走什么容器

### 架构事实（决定性）
- **所有周期效果是「actor-agnostic 的通用 tick 卡」**（v179）：`add_tick_effect(kind, actor_dict, ...)` 3150，调度 `_process_until` 3246-3250 / `_advance_time` 8605-8610 → `_process_tick_effects` 3187。**actor 是引用，卡挂在 actor 身上，不关心 actor 在哪个容器**。
- 因此 tick 层几乎**没有** player/allies/companions 特判——DOT/治疗/regen 全看卡条目 `actor` 引用指向谁（指向 self.player → 焦点玩家；指向某怪 → 怪；宠物卡指向 self.pet）。
- 只有两处「player 兜底回落」：`_process_tick_effects` 3206 `_actor = eff.actor or player`；`_advance_time` 8607 `_pl_now = self.player or {}`。这两处是**当前单焦点假设**：整场只有 self.player 一人被周期治疗。

### 分容器状态流
| 效果 | 容器/落地 | 关键点 |
|---|---|---|
| 玩家 DOT | **player actor dict** `player["debuffs"]`（`_apply_dot` 7813 setdefault）→ actor_dot 卡 7834-7838 | `_is_focus_player(target)` 7824 路由 → 卡 uid `dot_p_<id>` |
| 玩家 regen/治疗 | handler 全走 `battle._heal_actor(actor, ...)`（137-452 族），actor=卡绑定的引用 | `_ensure_regen_effects(player)` 8280 只为 self.player 挂卡（8280-8367，输入即 player 参数） |
| 玩家 HOT | `player["hot"]` + `player["food_effects"]` + `tick_effects` 里 food_hot 卡（`_th_food_hot` 494） | 序列化走顶层 `p_hot/p_food_effects` 键（见 §4） |
| 宠物/召唤物周期 | 宠物=`self.pet` 引用 + pet_act 卡（545-581）；召唤物**无自己的周期卡**（只有 player_act 触发普攻，auto_act interval 仅宠物用） | 召唤物没有 DOT/regen 治疗来源——它们只吃挡刀扣血 |
| 治疗广播 | `_skill_heal` 5297 `target_ally` 参数（治疗指定队友）| 见下方「最关键一处」 |
| 时刻推进 buff 到期 | `_advance_time` 8524：**只扫 `self._p_buffs_bag()`（=self.player 的 buffs）+ `self.e_buffs`** | companions/宠物/其他成员 buffs **不在此到期**（靠各自 actor 化后无——宠物有 buffs 容器但没人给它挂带期 buff） |

### 最关键的断层（收编必须面对）
1. **`_advance_time` 只推进单焦点玩家 buffs**：allies 其他成员的 buffs 到期没人管（现状副本各成员 buffs 到期依赖各自 act 时 `_turn_start`？——实际 `_turn_start` 8400 只处理传入的行动玩家）。收编 party 后要么循环 party 全员到期，要么保持「buff 到期=行动玩家自结算」语义。
2. **`_heal_actor` 5297 治疗指定队友（target_ally）**在 `_skill_heal` 里走 allies 查找——allies 是唯一「可被指定治疗的玩家容器」。收编后查找逻辑从 `self.allies` 换 party 玩家子集即可，改动小但要动。
3. `_guard_check` 9279 的挡刀池扫 companions 换 party 时**必须排除玩家本体**（party 里玩家不配 guard 字段所以现状无碍，语义需显式）。

## 4. to_state (958-1049) / from_state (1209-1388) 序列化玩家侧

### 现状映射（全部存顶层键，玩家 actor dict 为值源）
| 键 | 值源 | 恢复 |
|---|---|---|
| 顶层焦点键 `p_buffs/resources/mech_stacks/eff_data/cooldown/combo_seq/hot/food_effects/shields/charging/p_defending/...`（980-1032） | 全部从 **self.player dict** 读（959-968） | **不直接回填** → 存 `b._restore_pstate`（1240-1263），命令层绑真实 player 后 `_apply_restore_pstate` 1131 灌入（player_turn 2798 自动触发） |
| `pet` | `self.pet` dict 原样（981） | 1213-1216 构造时 pet 参数回绑 |
| `summons`（996） | `self.summons` property（=companions 的 summon 子集） | 1266 `b.summons = st.get("summons")` → setter 937 保留非 summon + 追加 |
| `allies` | **不序列化**（从_state 无 allies 键，1236 恢复 `st.get("allies") or []`=空——instance 由调用方 2606 注入引用） | instance 命令层构造 state 时按 alive 注入存活成员引用 |
| `companions`（宠物 actor 化产物） | **间接经 `pet` + `summons` 两键**——宠物本身不序列化（靠 pet 键+from_state 末尾 `_pet_ensure_actor` 1380 重生成）；召唤物经 summons 键 |
| `tick_effects`（1036-1048） | **actor 存引用不存 dict**：`actor_ref = "player"（is self.player）/ "pet"（is self.pet）/ 敌人 uid` | 1349-1373 重绑：`"player"→b.player（此刻可能空 dict，命令层后绑生效）`、`"pet"→b.pet`、uid→enemies |
| `_last_player` | 1024 | 1292-1294（宠物 owner 恢复依赖） |

### 收编 party 后的序列化硬伤清单
| # | 问题 | 严重度 | 说明 |
|---|---|---|---|
| 1 | **party 玩家成员战斗状态不落档**（现有 allies 即如此，副本层靠 st players 引用持久化）。party 化后玩家状态若也存 party 里，to_state 必须整 party 序列化或继续旁路顶层键——当前顶层键 = 单焦点语义，多玩家 party 必然溢出 | 🔴 最麻烦 | 顶层 20+ 键是**单焦点扁平结构**（p_buffs/resources/cooldown/...），本质假设「一场=一个玩家状态」。party 后每成员都要一套，扁平键架构崩 |
| 2 | **宠物 actor_ref="pet" 依赖 self.pet 独立引用** | 🟡 中 | 若删 self.pet、宠物只进 party：tick_effects actor_ref 需新增 `"party:pet"` 或按 kind 查找；1346-1357 恢复逻辑要改 |
| 3 | **summons 键 = companions 子集视图** | 🟢 低 | party 化后 summons 视图改扫 party 即可（property 930-951 结构可保留）；旧档读兼容 |
| 4 | **`allies` 键恢复 = 空 + instance 注入**（1236） | 🟡 中 | 若 allies 概念并入 party，instance.py 2606 构造引用处 + from_state 恢复都要挪到 party 装配 |
| 5 | `_restore_pstate` 灌入机制（1131-1164）绑定「**唯一** self.player」 | 🔴 最麻烦 | 多玩家 party 需要每成员各自的 restore 快照（st 里按 qq_id 分键），或改为 party actor 直接携带状态后**废弃顶层键恢复** |
| 6 | pet 的 pet_buff_vals 等加在 pet/owner dict 上（9156） | 🟢 低 | actor dict 字段随 actor 走，party 序列化时自然带上 |
| 7 | tick 卡 actor_ref="player" 恢复时指向空 dict 占位、命令层后绑生效 | 🟡 中 | party 后要区分「哪个玩家」——多成员同场时单 `"player"` 引用不够 |

## 5. 判断：随从收编 party 后序列化格式要不要动？哪些最麻烦？

### 结论
**要动，且不是小动**。分两半看：

- **随从（宠物+召唤物）并入 party**：序列化格式**几乎不用动**，只需微调——现状 companions 本就只经 `summons` 键（召唤物）+ `pet` 键（宠物）两条路落档。party 化后可新增/改名一个 `party` 键承载全体，把 `summons` 降级为兼容 property（930 结构已有先例）。**真正的新增负担**：pet 的 actor 引用恢复、pet_act tick 卡的 actor_ref 定位，以及召唤物上限计数（9021/9929/9947 走 companions 的 3 处 + potion_effects.py 423）。
- **玩家（player+allies）并入 party**：序列化格式**必须动**——这是最麻烦的地方。理由：当前 `to_state`/`from_state` 的 20+ 顶层扁平键 + `_restore_pstate` + `tick_effects.actor_ref="player"` 全是**单焦点假设**的产物（959-968 从唯一的 self.player 读、1131 灌入唯一的 self.player）。party 收编多玩家后，这套「一台 Battle 一套玩家状态」的扁平架构没有自然延伸路径——要么每成员一份旁路键（爆炸），要么把状态全收进 party 成员 actor dict、顶层键废弃（v180-B 已铺路 80%：`_p_*` helper 都读 actor dict；但 `to_state` 仍把它们打平成顶层键输出，恢复再折回——这一步是整个架构里唯一还绑着单焦点的地方）。

### 最麻烦排序（收编 party 视角）
| 序 | 麻烦点 | 为何麻烦 |
|---|---|---|
| 1 | **to_state/from_state 顶层键 ↔ party 成员状态的往返**（958-1049 / 1240-1263 / 1131-1164） | 单焦点扁平结构是 v2 时代遗留；party 化要求按成员维度存取，等同把序列化重写。若只收编随从则绕开此雷 |
| 2 | **tick_effects 的 actor_ref 定位体系**（1036-1048 / 1349-1373：`"player"/"pet"/uid`） | 引用编码只有 3 种身份；party 里「第 N 个玩家 / 第 N 只随从」需要新编码（如 `"party:idx"` 或 qq_id/kind+序号），恢复期引用重绑逻辑全改 |
| 3 | **allies 玩家死亡压缩语义**（9258-9264：过滤+compact） | allies 当前=副本玩家存活引用阵列，compact 压缩站位；并入 party 后玩家+随从混排，compact 语义（站位/射程/阵型）要重新定义，且玩家死亡走 party 还是副本 st 两套账要合一 |
| 4 | **单焦点假设的散点**：`_advance_time` 8524 只到期焦点 buffs、`_guard_check` 9279 挡刀池扫 companions 需显式排除玩家、`_process_tick_effects` 3206 与 `_advance_time` 8607 的 player 回落 | 每处都是「默认只有一个玩家」的隐性依赖，party 化逐一显式化（尤其多人同场 buffs 各自到期） |
| 5 | **随从召唤上限/宠物身份计数**（9021 / potion_effects 423 读 `battle.summons`） | 兼容视图改扫 party 即可，属低危但易漏 |

**总体评价**：v180 系列（B=玩家状态收 actor dict、C=随从收 companions、E=宠物行为数据化）已经把引擎 80% 做成 actor 化；**随从并入 party 是平滑收口（序列化基本不动，动的是引用定位）**；**玩家并入 party 是真正的重构点，序列化是最大拦路虎**——顶层键体系 + `_restore_pstate` + tick actor_ref 三处必须一起重做，建议随从先并入 party、玩家保持 self.player+allies 双轨，或一次性把「状态全入成员 dict、顶层键只留旧档兼容读」落地为 party 序列化的新格式。