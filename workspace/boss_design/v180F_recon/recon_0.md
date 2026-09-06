审计完成。以下为 `game/battle.py` 第 1–2600 行玩家侧容器使用模式的结构化清单。

---

# battle.py L1–2600 玩家侧容器审计清单（v180F 前置侦察）

## 1️⃣ 全量触点清单（行号 · 函数 · 用途）

### A. `self.player`（焦点玩家 actor dict，权威容器）

| 行号 | 函数 | 用途一句话 |
|---|---|---|
| 660 | `__init__` | `self.player = player or {}`——焦点玩家 actor 初始化 |
| 667–689 | `__init__` | `_seed` 兜底播种 player 全部战斗可变键（resources/stacks/eff/shields/cooldown/combo_seq/hot/food_effects/poi_buff/buff_hits/reduce_*/last_element/tailwind/v139_*/overflow/stealth/buffs/defending/charging） |
| 707–762 | `__init__` | player 存在时：刷 max_hp/max_mp、注入 dual_form/focus/vent 配置、echo_bless/poi_buff 祝福、`_init_resources(player)` |
| 765–800 | `__init__` | player 词条/套装 battle_start 链（护盾、wolf_howl/surge_ready、资源、`_we_proc(self, player, "battle_start")`） |
| 849–851 | `__init__` | `_pl0 = self.player or {}` → `_ensure_regen_effects(_pl0)` 挂 regen tick 卡 |
| 959–968 | `to_state` | `_pl = self.player or {}`——序列化时从 player dict 读全状态袋 |
| 1042 | `to_state` | tick_effects `actor_ref`: `"player" if e.get("actor") is self.player`（引用相等判定） |
| 1069–1070 | `_load_player_state` | **切焦点 = `self.player = snap` 换绑**（副本核心机制） |
| 1137/1142 | `_apply_restore_pstate` | 读当前 `self.player`，把 from_state 暂存状态灌入 |
| 1424–1428 | `_is_path` | v139 桥接：把 `_p_v139_modes()/_v139_charge()` 值写挂到传入 player dict 上 |
| 1446–1447 | `_elem_charge` | 读 `self.player` 的 resources.element_charge |
| 1513 | `_cast_stats` | `_player_stats(self.player)`（cast_ctx 为空 = 玩家施法） |
| 1523–1618 | 全部 `_p_*` helper | 见 §3 表格——动态读 `self.player` 的状态袋/标量访问器 |
| 1780–1781 | `_res_gain_class` | `_pl = self.player or {}` 守卫：词条/套装上限加成归 0 |
| 2152 | `_set_skill_cd` | `_player_stats(self.player)` 读 cdr |
| 2160–2161 | `_set_skill_cd` | `_pl_sd = self.player or {}` → `_proc_pm(_pl_sd)` 影舞冷却 |
| 2189 | `_tick_cooldowns` | `_we_proc(self, self.player, "battle_start")` 星辉壁垒刷新 |
| 2371 | `_elem_mark_max` | `pl = player or self.player or {}` 兜底取焦点 |
| 2576–2578 | `_after_actor_ct` | `_p = player or self.player or {}`（side="p" 时推进 `self.p_ct`，仅此处 p_ct 与 self.player 同现） |
| 2796–2805 | `player_turn`（>2600 边界，收口参考） | player 空则绑传入、非同一引用则同步 hp/mp/max_* 面板字段 |

### B. `self.allies`（副本存活玩家快照阵列）

| 行号 | 函数 | 用途一句话 |
|---|---|---|
| 636–639 | `__init__`（instance 分支） | allies = 显式传入 或 `st["players"].values()` 按 `st["alive"]` 过滤的**存活快照引用**（非拷贝） |
| 641–651 | `__init__` | 对 allies 每个快照**播种站位/战斗键**：rank/reach/uid/buffs/stacks/defending/charging/ct（`setdefault`）——与 player seed 类似但不含 resources/cooldown 等袋 |
| 659 | `__init__` | 非 instance：`self.allies = allies or []`（注释：v122 我方阵列=治疗指定队友用） |
| 1173–1177 | `_pick_enemy_target` | allies 空→None；alive 过滤后按 formation 选敌方目标 |
| 1203 | `_pick_enemy_target` | 选中后 `_load_player_state(qq_id)` → 换绑 self.player 做结算焦点 |
| 1236 | `from_state` | `b.allies = st.get("allies") or []` 恢复 |
| 2654–2668 | `_resolve_ally_target` | b<N> 编号/uid/名字前缀在 allies 中找治疗目标（`formation.numbered_units`） |

### C. `self.companions` / `self.summons`（我方随从阵列）

| 行号 | 函数 | 用途一句话 |
|---|---|---|
| 703 | `__init__` | `self.companions: list = []`——v180-C S1 我方非玩家实体统一容器 |
| 930–934 | `summons`(property getter) | 兼容视图：`companions` 中 `kind=="summon"` 子集（纯读） |
| 936–951 | `summons`(setter) | 整袋替换：保留非 summon 随从 + 追加 summon（补 kind/side/buffs 字段） |
| 996 | `to_state` | `"summons": self.summons` 序列化（只存召唤物视图，非 companions 全量） |
| 1123 | `_load_player_state` | 副本切焦点时 `self.summons = st["summons"][key]`——**按玩家分桶** |
| 1266 | `from_state` | `b.summons = st.get("summons") or []` 恢复 |

### D. 玩家快照/状态存取（序列化桥）

| 行号 | 函数 | 用途一句话 |
|---|---|---|
| 958–1049 | `to_state` | 玩家战斗状态从 player dict 读出，**沿用旧顶层键结构**（p_buffs/p_hot/p_food_effects/p_shields/mech_stacks/resources/cooldown/combo_seq/charging/p_defending/...）输出——老档兼容 |
| 1051–1129 | `_load_player_state` | 副本反向合并：st 顶层 per-player 旁路键（`p_buffs[key]/resources[key]/...`）→ snap dict（P3 前双轨兼容，快照键优先） |
| 1091–1122 | 同上 | 逐键 merge：buffs/buff_hits/reduce_all/reduce/poi_buff/hot/food/shields/charging/defending/stacks/resources/cooldown/combo_seq |
| 1131–1164 | `_apply_restore_pstate` | from_state 暂存的**单玩家**状态 → 当前绑定 player dict（merge 或覆盖） |
| 1240–1263 | `from_state` | 顶层键 → `b._restore_pstate` 暂存（单份 dict，非 per-player 分桶） |
| 1010 | `to_state` | `"p_ct": self.p_ct`（注意：p_ct 仍是 Battle 级实例槽，不在 player dict） |
| 804 | `__init__` | `self.p_ct: float = 0.0`——**唯一残留的玩家侧 Battle 级标量槽** |

---

## 2️⃣ 重点：初始化 / 序列化模式

**`__init__`（L584–703，instance 分支 L629–652 + 单机 L659–703）**

| 容器 | 初始化方式 | 拷贝/引用 |
|---|---|---|
| `self.enemies` | `[dict(u) for u in enemies]`（L610）**instance 则直传引用**（L631） | 单机拷贝 / 副本引用 |
| `self.allies` | instance：`st["players"]` 存活**快照引用** + setdefault 站位键（L638–651）；非 instance：`allies or []`（L659） | 引用 |
| `self.player` | `player or {}`（L660）；随后 L667–689 用 `_seed` **对同一 dict 播种全部战斗状态键**（setdefault，不动已有值） | 引用（外部玩家 dict / 副本快照） |
| `self.companions` | `[]`（L703），宠物由 `_pet_ensure_actor()`（L834，>2600）惰性加入 | — |
| `self.summons` | 无实例槽——property 兼容视图（L930） | 视图 |

**关键不对称**：`allies` 快照播种（L641–651）只有站位键 + buffs/stacks/defending/charging/ct **7 键**；`player` 播种（L667–689）有完整 **23 键**含 resources/eff/shields/cooldown/hot/food_effects/v139 等。副本快照切焦点后靠 `_load_player_state` 二次补播+合并 st 顶层旁路键才补齐——**两套播种代码，键集合不同步**。

**`to_state`/`from_state`（L958–1049 / L1208–1388）**

- to_state：玩家状态**全部从 `self.player` dict 读**，但**以旧 Battle 顶层键名平铺输出**（`p_buffs`/`resources`/`mech_stacks`/`cooldown`/...），不是 "players" 分桶。单机字段级；副本的 per-player 分桶由**命令层 instance.py** 写回 st 顶层（L2638+：`st["p_buffs"][cur_key] = b.player.get("buffs")`...每行动后写回）。
- from_state：构造时 `player` 未绑（空 dict）→ 顶层键先暂存 `b._restore_pstate`（L1240–1263，**单份**，只够一个玩家）→ 命令层绑 `b.player = snap` 后由 `player_turn` 入口调 `_apply_restore_pstate()`（L2796–2798）一次性灌入。副本每行动者重建 Battle + 换绑 player + 从 st 顶层键逐 key 合并（`_load_player_state`）。
- 序列化中玩家身份线索：`tick_effects.actor_ref = "player"`（引用相等 `is self.player`，L1042）；`summons` 走 property 视图。

---

## 3️⃣ 玩家"焦点状态"读写分布（player dict vs Battle 级旁路）

### 已迁入 player actor dict 的状态（L1523–1618 `_p_*` helper 全量，动态读 `self.player`）

| 状态袋 | helper（行号） | 存放键 | 调用量(全文件) |
|---|---|---|---|
| 资源 | `_p_res`(1523) | `player["resources"]` | 65+ |
| 叠层 | `_p_stacks`(1526) | `player["stacks"]`（含 combo/echo） | 23+ |
| 特效/物品 | `_p_eff`(1529) | `player["eff"]`（amps/we_*_cd/phys_up...） | 33+ |
| 护盾 | `_p_shields_bag`(1532) | `player["shields"]` | 5+ |
| buff | `_p_buffs_bag`(1535) | `player["buffs"]` | 72+ |
| charging | `_p_charging`/`_p_set_charging`(1539/1542) | `player["charging"]` | 15+ |
| cooldown | `_p_cooldown`(1545) | `player["cooldown"]` | 6+ |
| combo_seq/last_tag | `_p_combo_seq`/`_p_last_combo_tag`(1548/1551) | `player["combo_seq"]`/`["last_combo_tag"]` | 5+ |
| hot/food | `_p_hot`/`_p_food_effects`(1557/1560) | `player["hot"]`/`["food_effects"]` | 9+ |
| defending | `_p_defending`/`_p_set_defending`(1563/1566) | `player["defending"]` | — |
| buff_hits | `_p_buff_hits`(1569) | `player["buff_hits"]` | 4+ |
| reduce 刻数 | `_p_reduce_*_left`(1572–1582) | `player["reduce_*_left"]` | — |
| 杂项标量 | poi_buff/last_element/tailwind/overflow_shield_cd/stealth_atk（1584–1618） | `player` 直接键 | — |
| v139 模式 | `_p_v139_modes`/`_p_v139_charge`(1602/1605) | `player["v139_modes"]`/`["v139_charge"]` | — |

### 仍走 Battle 级旁路 / 非 player-dict 的状态

| 状态 | 位置 | 存放处 | 说明 |
|---|---|---|---|
| **玩家 CT（p_ct）** | L804 init / L1010 to_state / L2578 `_after_actor_ct` | `self.p_ct` 实例槽 | 副本注释明言"snap["ct"] 权威，self.p_ct 弃用勿用于调度"（L652），但玩家行动后仍写它再由命令层回写 snap（instance.py L2680 `snap["ct"]=b.p_ct`）——**双轨** |
| **玩家侧瞬态标记** | L805–817 | `self._player_hit/first_attack_done/_death_pact_used/_set_immune_used/_pending_dmg_lines/_player_casting/_pending_player_cast/_last_hitter` | 随 to_state 顶层键序列化（L1011–1033），非 actor dict——每场一次性/瞬态，未 actor 化 |
| **胜利结算专用** | L1024–1025 | `self._last_player/_shifted_element` | 已注释收进顶层，仍实例槽 |
| **玩家被击结算** | L10156–10164 `_damage_actor` | **直接读 actor dict**（B/EFF/RES/MS/CH/HITS/SH/RL_ALL/RL 全从参数 actor 取） | v180-B 后分叉退化——这是**收编后的目标形态样板**（>2600 行，已全 actor 化） |
| 蓄力打断清理 | L10180–10183 | `_is_focus_player` 分叉：玩家走 `_p_set_charging(None)`，怪走 `actor["charging"]=None` | 唯一残留的玩家/怪双通道写点 |
| 治疗队友护盾 | L5437/5468 `_skill_heal` | **队友快照 `target_unit.setdefault("p_shields",{})` 手写 `{"value","turns"}` 旧格式** | 与 `_p_shields_bag` 的 `{"value","expire_at"}` 新格式**不一致**——写玩家自己走 `_add_shield`（L3367 内 `_p_shields_bag`），写队友走旁路旧格式 |
| 敌方侧 | L971–999 to_state | e_buffs/e_defending/e_minions/enemy | 敌方本来就 actor 化，无旁路 |

**结论**：本区（L1–2600）玩家焦点状态**已 100% 收进 player dict**，无 Battle 级焦点字段残留（唯一例外 `p_ct`）。`_p_*` helper 只是"读当前 self.player 的语义口"，已是纯旁路化读取而非独立状态存储。真正的**双轨残留**在副本 st 层：状态权威在 `st["players"][key]` 快照 dict，但每行动后命令层仍向 st 顶层 per-player 键回写一份兼容拷贝（instance.py L2638–2662），再由下次 `_load_player_state` 合并回去——P3 未折叠前的双向搬运。

---

## 4️⃣ 收编 party 数组的主要障碍点（player=单个 dict 的假设）

| # | 障碍 | 证据行 | 说明 |
|---|---|---|---|
| 1 | **焦点单例语义贯穿全局**：`self.player` 是"当前行动/结算玩家"的**单指针**，收编后必须变成"聚焦索引"。切焦点 = 换绑引用（L1070），80+ 处 `_p_*` helper 都动态读它——改造成"读 party[idx]"，helper 层可一次收口（L1523–1618 全量重定向即可），这是**最小阻力路径** | 660, 1070, 1523–1618 | 需把 `self.player` 变 property 或统一改 `_focus()` |
| 2 | **`_restore_pstate` 是单份暂存**（L1240–1263）：from_state 只恢复一个玩家状态。收编 party 后多玩家恢复需 per-uid 分桶——涉及 `_load_player_state`（L1091–1122 逐 key 合并逻辑）与 instance 层写回格式双改 | 1240, 1091, 1137 | |
| 3 | **to_state 平铺单玩家键**（L958–1049）：`p_buffs/resources/cooldown/...` 顶层键只有一套。玩家侧多成员时无法表达"每成员各一套"——要么切分桶要么放弃旧档兼容 | 980–1009 | 老档兼容 vs 多玩家序列化不可兼得 |
| 4 | **`summons`/companions 按玩家归属分桶但 to_state 只存视图**（L996）：`st["summons"][key]` 是 per-player 的（L1123），companions 却是 Battle 级平铺数组——收编 party 后随从归属（跟随哪个玩家/快照主人）没有显式 owner 字段，仅靠"切焦点时整袋换" | 930, 1123, 996 | |
| 5 | **`self.p_ct` Battle 级单槽 + `allies` 快照 ct 双轨**（L804/1010/2578 vs L652）：玩家 ct 权威注释已说在 `snap["ct"]`，但调度仍写 Battle 槽再由命令层搬运。party 化应彻底改读 `unit["ct"]`（敌方已同构，玩家侧照抄即可） | 652, 2578, 1010 | |
| 6 | **玩家 vs 随从承伤无统一入口**：`_damage_actor` 已 actor 化（>2600，读 actor dict），但 `_guard_check`（L9267）挡刀检查、`_resolve_ally_target`（L2650）治疗目标、`_is_focus_player`（L10055，引用相等 + allies 遍历判定玩家身份）都隐含"我方=allies 玩家快照 + 焦点单玩家"的旧心智模型 | 10055–10086, 2650, 9267 | `_is_focus_player` 是收编后最需要重写的身份判定 |
| 7 | **玩家侧站位字段仅 allies 快照播种，player 播种缺 rank/reach/uid**（L641–651 有 vs L667–689 无）：`_player_attacker`（L2596）读 `player.get("reach")` 兜底 2。收编后 party 数组内每 actor 必须统一有 rank/reach/uid，现在两份播种代码键集不一致 | 641–651, 667–689, 2596–2598 | |
| 8 | **`tick_effects.actor_ref` 只有 "player/pet/enemy-uid" 三种枚举**（L1042–1045）：多玩家/随从时代 actor 定位需扩展（"player:<uid>" 或 party 索引），否则 tick 卡无法绑到非焦点成员 | 1042, 1354–1362 | |
| 9 | **治疗队友路径绕过统一状态袋**：`_skill_heal` 对队友手写 `p_shields` 旧格式 `{"value","turns"}`（L5437/5468），与 actor 标准 `{"value","expire_at"}` 冲突——证明"非焦点玩家"尚未享受 actor 同构待遇，是 party 化后第一个会爆的格式坑 | 5437, 5468 vs 3367–3390 | |
| 10 | **命令层耦合**（battle.py 外）：instance.py 每行动后 `b.player.get("buffs")/...` 写 st 顶层 per-player 键 + 重建 Battle 换绑（L2568–2680）——party 收编必须连带改命令层读写契约 | instance.py 2638–2662 | 引擎内再干净，写回契约不折叠双轨即白改 |

**总评**：L1–2600 内玩家侧"状态存储"已高度 actor 化（v180-B 完成度高，`_p_*` 全读 `self.player`），真正的障碍不在状态在**焦点单例**——`self.player` 单指针 + 单份 `_restore_pstate` + 平铺 to_state + allies/companions 无 owner 归属。收编 party 的改造顺序建议：①`self.player` → 焦点 property/索引（helper 层一次收口）；②to_state/from_state/restore 分桶；③companions 补 owner 字段；④治疗/挡刀/身份判定改走统一数组。

---
*注：本次为只读侦察，未修改任何文件。行号以 battle.py 现文件为准（10255 行）。*