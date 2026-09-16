# RESEARCH：『加入战斗』指令的 CTB 支持性评估与设计

> 版本：v1（2026-08-29）｜关联：v137 副本彻底重构（docs/archive/INSTANCE_MAP_UNIFY_v137.md §3.4 / §六 风险表）
> 范围：只做研究与设计，**不改任何代码**。本文档是后续 Phase B4（『加入战斗』指令 + 野外组队同场战斗）的实现依据之一。
> 结论先行：**CTB 机制支持『加入战斗』，但存在三处结构性缺口必须改造**（战斗状态键、allies 持久化、ct 播种口径），否则并发下会数据错乱。

---

## 一、研究目标与场景

鱼鱼需求（v137 立项 §一 第 6/7 点）：

1. 副本内探索各自进行，一人遇怪进入战斗；
2. 队友可『加入战斗』并入同一场；
3. 野外组队打怪顺势升级为同场战斗（allies 多对多），『加入战斗』对野外同样适用（同队伍在附近时）。

『加入战斗』的语义：**战斗中任意时刻**，同队伍且未在战斗中的玩家，输入『加入战斗』并入目标战斗，成为我方阵列（allies）的一员，与原有玩家共享同一份敌方阵列、同一根 CTB 时间轴。

---

## 二、现状：battle state 结构与存储（侦察结论）

### 2.1 存储层：battle_state 表按「玩家」为键

```sql
CREATE TABLE IF NOT EXISTS battle_state (
    qq_id TEXT PRIMARY KEY,      -- 键 = 单个玩家 qq_id（全局维度，无 group_id 维度）
    monster TEXT NOT NULL,       -- 展示主目标名（I0-B8 多对多取 enemies[0]）
    state TEXT NOT NULL,         -- 完整战斗状态 JSON（Battle.to_state() / 命令层自拼）
    updated_at INTEGER
);
```

| 战斗类型 | 存谁名下 | 谁持有锁 | 备注 |
|---|---|---|---|
| 野外遇怪（探索/移动撞怪） | 玩家自己 | 玩家自己 | `BT.Battle("monster", ..., player=player, enemies=group)` |
| 世界 Boss | 玩家自己 | 玩家自己 | `BT.Battle("worldboss", ...)`；全局血量存 world_event |
| PVP | 攻击方+防守方**各一份**（同 state 双写） | 双方各自 | `db.save_battle(group_id, qq_id, state)` + `db.save_battle(group_id, target_qq, state)` |
| 副本（现状 v137 前） | **仅队长名下** | 全队各自 | `db.save_battle(group_id, st["leader"], st)`；队员经 `_instance_battle_for` 查队长行 |

**结论①：战斗状态没有『队伍级』键。** 副本用「队长名下 + party 表反查」绕开；PVP 用双写绕开。『加入战斗』需要多玩家共享同一份 state，两种绕法都不够——副本绕法依赖 party 表（队员退队即失效），双写绕法（野外）会导致**两行各自演化、互相覆盖**，直接不可用。

### 2.2 统一引擎 Battle 的状态结构（game/battle.py）

`Battle.__init__(btype, enemy, title_bonus, player, pet, dmg_mult, enemies, allies)`：

- `enemies`：敌方阵列，每单位 dict 含 `uid/rank/reach/buffs/stacks/defending/charging/ct/hp/max_hp/...`（v2 多对多）；`enemy` 属性为兼容主目标代理。
- `allies`：**我方阵列**（v122 治疗指定队友引入）。**副本传『存活玩家快照的引用』**（`[st["players"][m] for m in members if alive]`），Battle 内治疗改 hp 直接写回原快照；**单机/野外构造时传空**（`allies or []`）。
- `player`：本场行动者引用（`_player_stats`/`_monster_dodge_check` 读它）。
- `p_buffs/e_buffs/mech_stacks/resources/cooldown/combo_seq/p_ct/...`：战斗内状态。

`to_state()`（L426-473）序列化全部战斗状态——**但不含 allies**（野外单机 allies 恒空，故无此键）；`from_state()`（L476-550）`b.allies = st.get("allies") or []` 恢复。

**结论②：allies 在引擎里是『可变列表』，不是静态引用。** 消费端（`_resolve_ally_target` L1416、`_skill_heal` L2951、团队 buff 遍历 L2677/L4508、`_remove_unit(side="ally")` L4846-4854）全部按 `self.allies` 运行时遍历/追加/移除——**引擎本身支持动态追加**。缺的是：①单机 `to_state` 不持久化 allies（野外同场战斗必须补）；②`from_state` 恢复 allies 后，各成员自己的 `p_buffs/mech_stacks/resources/cooldown` 仍按各自快照携带（副本命令层每次行动自拼 state dict 传入，见下）。

### 2.3 副本自写 CTB 调度（game/commands/instance.py，v137 前的现状）

副本不直接用 Battle 的 CTB 时间轴，而是**命令层自写**一套：

- `st["players"]`：{qq_id: 玩家快照}（快照含 `ct` 字段）；
- `st["enemies"]`：敌方阵列（单位含 `ct`）；
- `st["members"]`：开本成员列表（按 spd 降序排）；
- `st["alive"]`：{qq_id: bool}；
- `_instance_next_actor(st, group_id)`（L1824-1836）：取**存活玩家与存活敌方中 ct 最小者**；
- `_instance_enemy_ct_acts`（L1864-1893）：`while 敌方最小 ct < 玩家最小 ct → 敌方行动一次`（**相对比较**）；
- `_instance_apply_enemy_act_ct`（L1838-1862）/ `_instance_auto_defend_player`（L1895-1916）/ 玩家行动后的队友 ct 广播（L1506-1514）：行动者 ct += cost，**其余存活玩家与敌方 ct -= cost**（时间流逝对称）；
- `_instance_reset_player_cts`（L486-493）：新怪/换层时存活玩家 ct 重置为 **-spd**；
- 玩家快照构造（`_instance_start` L1203-1240）与敌方阵列构造（`_instance_build_enemy_array` L520-550）都播种 **ct = -spd**；
- 战斗持久化：**存队长名下**（`db.save_battle(group_id, st["leader"], st)`，15 处写回点）；
- 队伍构成实时过滤：`_instance_current_members`（L701-713）按 `db.party_members(group_id, st["leader"])` 过滤 `st["members"]`——**退队者即时从行动轴/结算剔除**（v104 P1 系列修复）。

### 2.4 单机 Battle 的 CTB 时间轴（v130.10 绝对时刻，与副本口径不同！）

- 常量：`BASE_DELAY = 100.0`、`SPD_CT_CAP = 80.0`；`_ct_cost(spd) = BASE_DELAY / max(1, min(spd, 80))`；
- **玩家 `p_ct` 开局 0.0**（L349），行动后 `_after_actor_ct("p")` → `p_ct += cost`、其余存活敌方 `ct -= cost`（L1330-1359）；
- **敌方单位 ct 开局 = `_ct_initial_wait(spd) = BASE_DELAY / spd`**（L209-217，v130.10 修复，阴阳师式速度条——**行动点 = ct ≤ 0**）；
- `_enemy_phase`（L1629-1660）：`while 敌方最小 ct > 0 → 行动`（**0 为行动点**）；
- `from_state` 兜底（L517-520）：`ct 缺失或 ≤ 0` 的敌方单位重置为 `_ct_initial_wait`；`p_ct < 0` 重置 0（L514-516）。

**结论③（关键发现）：单机 Battle 已迁到 v130.10 绝对时刻（0 为行动点），而副本命令层仍是 v121 相对时钟（-spd 播种 + me<mp 相对比较）——两套口径并存。** 『加入战斗』如果跨这两套（如副本战斗让野外玩家加入），必须先统一口径；即便只在单机野外同场战斗内做，也只需对齐单机口径。

### 2.5 玩家战斗锁

`_lock_battle/_unlock_battle`（combat.py L424-428）= 内存 set 按 qq_id 加锁；`_in_battle`（L404-422）= db 行 + 内存锁 + 副本队员反查（`_instance_battle_for`）。组队/拉人命令在战斗中一律拒绝（social.py L397-410 + store 层 `_in_battle_state`）。

---

## 三、动态 allies 追加可行性分析

### 3.1 引擎侧：可行（几乎零改动）

allies 的全部消费端都是运行时遍历：

| 消费点 | 行为 | 动态追加影响 |
|---|---|---|
| `_resolve_ally_target`（L1416-1433） | `numbered_units(self.allies)` + uid/名前缀匹配，返回存活队友快照 | 新快照入列表即被解析到（b1/b2 编号顺延） |
| `_skill_heal`（L2951+） | `target_ally` 引用快照改 `hp` | 引用语义 → 直接写 st 原快照 |
| 团队 buff / 神迹余晖 / 回声余韵（L2677/L4508） | 遍历 allies 补血/上 buff | 遍历到即生效 |
| `_remove_unit(side="ally")`（L4846-4854） | hp≤0 移除 + compact | 死亡自动剔除，无需手动 |
| `player_turn` / `_enemy_phase` | 只动 `self.player` 与 `self.enemies` | **不碰 allies 的 ct**（allies 只做治疗目标/站位展示） |

**结论④：引擎 allies 是『活列表』，动态追加 = `b.allies.append(新快照)` 即完成引擎侧接入。** 但注意引擎对 allies 不做 ct 推进（ct 由命令层管理），所以『加入战斗』的 ct 播种必须由命令层完成。

### 3.2 命令层（副本）侧：状态结构支持，但有三处必须处理

副本 `st["players"]` 是 {qq_id: 快照}，**天然支持动态加入**：

```python
# 加入流程（伪代码）：
st["players"][str(new_q)] = build_snapshot(new_player)   # 与 _instance_start 同构
st["members"].append(str(new_q))                          # 或按 spd 重排
st["alive"][str(new_q)] = True
st["p_buffs"][str(new_q)] = {}
st["p_hot"][str(new_q)] = {}
st["p_food_effects"][str(new_q)] = []
st["mech_stacks"][str(new_q)] = {}
st["p_defending"][str(new_q)] = False
st["contribution"][str(new_q)] = 0
st["threat"][str(new_q)] = 0
st["players"][str(new_q)]["ct"] = 播种值              # 见 §四
db.save_battle(group_id, st["leader"], st)               # 队长的行
self._lock_battle(group_id, new_q)                       # 给新人上锁
```

现有代码自动兼容点：
- `_instance_current_members`（按 party 表过滤）→ 新人入队后自动纳入；
- `_instance_living_player_cts` / `_instance_next_actor` / `_instance_enemy_ct_acts` / `_instance_auto_defend_player` / 队友 ct 广播 → 全部遍历 `st["players"]` + 存活 + 在场过滤，**新成员自动进入行动轴**；
- `_instance_kill_reward` / `_instance_victory` / `_instance_defeat` 结算按 `_instance_current_members` → 自动含新人；
- `_sync_players_db`（L1303-1317）按 `st["members"]` 写回 DB → 自动含新人。

**三处必须处理：**
1. **人数上限**：队伍上限 4 人（party_add max_size=4），但战斗内 `members` 是开本快照——『加入战斗』需校验 `len(当前战斗 members) < 4`，且新人必须已在 party 表（同队伍）。
2. **入队时机**：队伍操作与战斗互斥（social.py L397-410 战斗中禁止组队/拉人）——『加入战斗』**不能改变队伍关系**，只能把已在队且未入战的队友拉进当前战斗。
3. **快照新鲜度**：开本时快照是当时属性；新人入场应取**当前 DB 属性**构造新快照（`_instance_start` 同款 `player_final_stats` 实时算），否则换装/升级后属性失真。

### 3.3 单机（野外）侧：需要新增 allies 持久化 + 战斗键

野外 `BT.Battle` 的 state 是**单玩家自持**（to_state 无 allies、battle_state 按 qq_id 存）。野外同场战斗的『加入战斗』，需要：

1. `to_state` 增加 `allies` 键（序列化我方阵列）；
2. battle_state 需要支持**多玩家共享同一行 state**（见 §六 方案 B：队长键）或**双写**（PVP 先例）；
3. 命令层需要管理各成员的 ct（引擎对 allies 不推进 ct）。

---

## 四、CTB 播种规则设计（核心）

### 4.1 问题背景：两套时钟

- **单机（v130.10 绝对时刻）**：玩家 `p_ct` 0 起、行动 +cost、敌方行动 -cost；敌方 ct 从 `BASE_DELAY/spd` 起、行动 +cost、其余 -cost。**所有 ct 围绕 0 波动，行动点 = ct ≤ 0（玩家）/ ct ≤ 0（敌方，同义）**。
- **副本（v121 相对时钟残留）**：玩家/敌方 ct 均从 **-spd** 起（快者更负先手），行动 +cost、其余 -cost；`_instance_next_actor` 取最小 ct、`_instance_enemy_ct_acts` 用 `me < mp` 相对比较。

**『加入战斗』播种必须与目标战斗的时钟口径一致**，否则：
- 给 v130.10 战斗播种 -spd → 负 ct 立即行动 + `from_state` 兜底把负 ct 重置为 0（行为漂移）；
- 给 v121 副本战斗播种 0/最小 ct → 语义错位。

### 4.2 推荐规则（单机/统一引擎口径，v130.10 绝对时刻）

**新入场玩家 ct = 当前战斗时间轴上『敌方最小 ct』与『现有玩家最小 ct』的最小值（即 `min(存活敌方 ct, 存活玩家 ct)` 的当前最小者），同时叠加一次『入场等待』= 该玩家自身 cost。**

理由：
1. 绝对时刻下所有存活单位 ct 围绕行动点波动，取当前最小 ct 作为参考点，新玩家**不会立即抢走本回合行动权**（参考点 ≈ 最近行动者位置）；
2. 叠加自身 cost 保证**入场有代价**（不能白嫖当前行动窗口），且 cost 随 spd 缩放——快者入场等待短、慢者长，符合 CTB 频率线性；
3. 数学上不会『永远轮不到』：绝对时刻下时间流逝对所有单位对称（他人行动 → 新玩家 ct -= cost），新玩家 ct 会随他人行动自然回落，spd 低只是频率低、不是零频率。

```python
def seed_join_ct(battle_or_st, new_snap) -> float:
    """加入战斗 ct 播种（v130.10 绝对时刻口径）"""
    ref = min(存活敌方 ct 最小者, 存活玩家 ct 最小者)  # 当前时间轴参考点
    return ref + BT.Battle()._ct_cost(new_snap.get("spd", 0))  # 参考点 + 自身行动 cost
```

**边界**：
- 目标战斗是 v121 相对时钟（现状副本）→ 先统一时钟口径（§七 改造 1），再播种；
- 目标战斗开局未行动（全部 ct = 初始值）→ 参考点 = 初始最小 ct，新玩家 = 初始最小 ct + cost，排最后合理；
- 目标战斗已接近结束（敌方全灭/玩家全灭）→ 直接拒绝加入（§五）。

### 4.3 反对方案

| 方案 | 问题 |
|---|---|
| `-spd`（v137 原案） | 相对时钟残留；负 ct 在 v130.10 下立即行动（抢行动权）+ from_state 兜底重置 0 → 行为漂移；且『入场即行动』破坏公平 |
| 播种 0 | 等同『刚行动完』——若战斗正有玩家在行动窗口，新玩家会在同窗口插队，仍是白嫖 |
| 播种当前最小 ct（不叠 cost） | 与 0 同窗口问题；且无入场代价 |
| 播种当前最大 ct | spd 慢者 cost 大 → 被持续拉开，近似『永远轮不到』（虽然绝对时刻下不绝对，但体验差） |

### 4.4 入场后行动顺序重排

无需显式重排——`_instance_next_actor` / `_enemy_phase` 本来就按 ct 最小者选行动者，**新玩家播种后自动进入队列**。要做的只是：加入动作本身**不触发任何行动推进**（不调用 `_enemy_phase` / `_instance_enemy_ct_acts`），只改状态 + 保存 + 广播，让下一个自然行动者按新 ct 顺序行动。若加入发生在『轮到某人行动、正在等待』的窗口，保持原行动者不变（不抢行动权）。

---

## 五、玩家入场时机

| 场景 | 允许？ | 设计 |
|---|---|---|
| 战斗进行中任意时刻（副本） | ✅ | 状态只改（append + 播种 + 保存），不推进行动轴；下个行动者由 ct 最小者自然决定 |
| 战斗进行中任意时刻（野外单机） | ✅ | 同上（需先有队伍同场战斗能力，§六） |
| 目标战斗处于『敌方行动段』（单机 _enemy_phase 正在 while） | ⚠️ 可 | 加入是同步指令，不会插入正在执行的行动段；在段间（消息间隙）进入即安全。建议文案提示『敌方正在行动，稍后入场』不必要——消息间隙天然安全 |
| 目标战斗已结束（胜利/失败/逃跑结算完成） | ❌ | 拒绝：『战斗已结束』 |
| 目标战斗是 PVP | ❌ | PVP 是双人快照对决，无 allies 概念，拒绝 |
| 目标战斗是世界 Boss | ⚠️ 特例 | 世界 Boss 是全局共享血量、按玩家各自 battle 行结算贡献——『加入战斗』应指『同一场世界 Boss 讨伐』（已有机制：`_worldboss_act` 全局血量同步），**无需 allies 改造**，文案提示走『攻击』即可；若要做成同场组队则属二期 |
| 目标战斗在副本、加入者在野外 | ❌ | 地理不符（副本是封闭地图），拒绝 |
| 加入者在战斗中（任何类型） | ❌ | 已在战斗，拒绝 |
| 加入者不在队伍中 | ❌ | 先『组队』 |

**『加入时机 = 消息间隙』**：QQ 异步交互下，战斗是『一条消息一次行动』的回合制外壳，玩家行动之间天然有间隙；『加入战斗』作为一条独立指令，只在间隙被处理，不会与行动推进并发冲突。真正要防的是**两个玩家同时行动/同时加入的写入竞争**——这靠 SQLite `_lock`（battle_state.py 全局写锁）+ 战斗锁（`_lock_battle`）已覆盖（现状 PVP/副本同款）。

---

## 六、战斗状态共享：按键设计

### 方案 A：副本现方案——『队长键』（零新增表）

- 战斗 state 存队长名下（现状副本即如此）；队员查询走 `_instance_battle_for`（party 表反查队长）。
- 『加入战斗』= 新成员直接并入队长行 state。
- **缺陷**：①野外没有『队长战斗行』概念（各打各的）；②队长退队/换队长时 party 表结构变化 → 行归属漂移；③battle_state 表无 group 维度，跨群同名玩家会撞键（现状靠 qq_id 全局唯一规避）。

### 方案 B：野外/统一——『队长键 + state 内 members』（推荐，改动最小）

- 野外遇怪时，若玩家在队伍中 → battle 存**队长名下**（与副本同构），`state` 内记录 `"members"`/`"leader"`；
- 队员输入『攻击/技能/防御』→ `_instance_battle_for` 同款反查（复用 party 表）；
- 『加入战斗』= 并入队长行 state（同方案 A）。
- **代价**：野外遇怪路径（explore L276/345、world 移动撞怪 L1491）构造 Battle 时需判断 `db.party_members` 非空 → 改存队长键 + `allies=[队长快照]` + 锁全队。这是**单点改造**（两个构造点）。

### 方案 C：PVP 双写——（不推荐用于野外同场）

PVP 是双人各自双写同一 state；3-4 人同场时双写 ×N 互相覆盖，不可扩展。

**推荐：方案 B（野外与副本统一走『队长键 + members 字段』）。** 其本质是把副本的战斗归属模式泛化到野外，一套 `_instance_battle_for`-like 反查即可。

---

## 七、对现有战斗的影响（改造清单）

### 7.1 必须改造（结构性）

| # | 位置 | 改动 | 影响面 |
|---|---|---|---|
| 1 | `battle.py to_state/from_state` | `to_state` 增加 `allies` 序列化（野外同场必需）；`from_state` 已恢复 allies（L492 已读 `st.get("allies")`） | 单机战斗 state 体积略增；旧档无 allies 键 → `or []` 兜底已存在，**零破坏** |
| 2 | 野外战斗存储键 | 遇怪构造点（combat.py explore L276/345、world.py 移动撞怪 L1491）判断队伍 → 存队长名下 + state 记 `leader/members` | 只影响**在队玩家的遇怪**；单人不组队行为不变 |
| 3 | 副本 CTB 时钟统一 | `instance.py` 玩家/敌方 ct 播种 -spd → `_ct_initial_wait`（绝对时刻）；`_instance_enemy_ct_acts` 的 `me<mp` → 与单机 `>0 行动点` 对齐 | 影响副本行动节奏（需数值回归：v121→v130.10 的失衡修复文档 docs/NUMERIC_TEST.md 已证明绝对时刻是正确口径）；**若不做，『加入战斗』跨时钟播种会错乱** |
| 4 | `_in_battle`/锁 | 队员持有战斗锁（现状副本已锁全队）；野外同场后，队员的 db battle 行不存在（存队长）→ 复用副本的 `_instance_battle_for`-like 反查 + 自愈保留锁逻辑（combat.py L413-421 已有先例） | 队员探索/移动在战斗中会被拦（现状副本已如此） |
| 5 | 指令注册 | `_registry.py` 增加 `join_battle: '^(?:\\[At:\\d+\\]\\s*)?加入战斗(?:\\s*|$)'` + 命令实现（base.py 派发） | 新增指令，不影响存量 |

> **2026-08-30 审计更新（v141 后）**：上表**均未落地**。现状口径：**播种与调度比较仍为 v121 相对时钟**（`-spd` 播种，`me<mp` 相对比较，instance.py 905/942 播种、1945/2031 调度），**行动后结算走引擎 v130.10 绝对时钟**（`b.p_ct` 写回 snap["ct"]）——播种/调度用相对、行动后用绝对，**口径未完全统一**（join_battle 播种 180-190 混用同源），列为已知项（v141 审计 P1-2）。『加入战斗』指令本身亦**未实现**（见头部结论）。

### 7.2 建议配套（非阻塞）

- **人数上限**：`len(members) < 4` 才可加入（与队伍上限对齐）；
- **满员/重复加入**：已在 `st["players"]` → 『你已在战斗中』；人数满 → 『战斗满员（4 人）』；
- **加入时快照新鲜度**：新快照按 `_instance_start` 同款 `player_final_stats` 实时构造；
- **加入不触发行动推进**：只改状态 + `db.save_battle` + `_lock_battle(new)`，不调 `_enemy_phase`/`_instance_enemy_ct_acts`；
- **敌方仇恨/贡献**：`threat`/`contribution` 按 `setdefault` 初始化 0，新人自然累积；
- **团队 buff 覆盖**：新人入场不继承已生效的团队 buff（如 boss_buff_next 风神铭文是开本时全队），文案提示『你加入了战斗』即可；若要继承，需在加入点遍历 `st["p_buffs"]` 各源快照拷贝——**二期**；
- **撤退/离开副本**：战斗中不能撤退/离开（现状 instance_retreat/leave 已拦 mode != "map"），新人入场后同样受约束，无需新逻辑。

### 7.3 对现有战斗的回归风险

| 风险 | 影响 | 对策 |
|---|---|---|
| 野外遇怪改存队长键 | 单人不组队行为不变；在队玩家遇怪从『自己行』变『队长行』 | 只改 `party_members 非空` 分支；单人行路径零改动 |
| allies 序列化 | 旧档无 allies → 兜底 `[]`，治疗指定队友在旧档单机战斗不可用（现状即不可用，无回归） | 无需迁移 |
| 副本时钟统一 | 行动顺序/频率变化 | 先跑 v121→v130.10 等价性测试（v137 Phase 2 B1 已规划），数值门禁 |
| 世界 Boss | 不受影响（全局血量机制独立） | 无 |
| PVP | 不受影响（无 allies，双写保持） | 无 |

---

## 八、最小实现路径（推荐顺序）

```
Phase 0（本设计文档）✅
Phase 1：时钟统一（§七 3）——副本 ct 播种 -spd → _ct_initial_wait；_instance_enemy_ct_acts 对齐行动点语义
         （先做！否则加入战斗的播种跨时钟错乱）
Phase 2：引擎 allies 持久化（§七 1）——to_state 增加 allies；回归单机治疗指定队友
Phase 3：野外队长键（§七 2/4）——遇怪构造点判断队伍 → 存队长行 + 锁全队 + 队员反查
Phase 4：『加入战斗』指令（§七 5）——
         a. 路由：找目标战斗（同队伍成员的 battle 行 / 副本队长行）
         b. 校验：同队伍 / 不在战斗中 / 战斗未结束 / 非 PVP / 人数 < 4 / 地理位置（副本封闭）
         c. 并入：st["players"] 追加新快照 + members/alive/各 per-player 状态初始化 + ct 播种（§四.2）
         d. 保存 + 上锁 + 广播
Phase 5：野外组队同场战斗（顺带完成——Phase 3 后野外战斗天然 allies=[队长]；
         遇怪时若队伍 2-4 人 → 全员并入同一场）
Phase 6：测试（25+ 副本测试回归 + 新增：加入战斗后行动顺序断言 / 重复加入 / 满员 / 退队后加入 / 战斗结束加入）
```

**最小路径 = Phase 1 → 2 → 3 → 4**（野外同场战斗是 Phase 3 的自然产物，不另计工作量）。

---

## 九、边界情况总表

| 场景 | 处理 |
|---|---|
| 战斗中玩家退队 | 副本现状：`_instance_current_members` 按 party 表过滤 → 退队者即时退出行动轴/结算/仇恨/奖励（v104 P1 已实现）；退队者自己的锁被清（social.py party_leave L466-469）。野外同场后需同款过滤（方案 B 的 members 过滤点） |
| 战斗中玩家掉线/不行动 | 副本现状：`INSTANCE_TIMEOUT=60s` 自动防御 + ct 结算（`_instance_auto_defend_player`），不卡死全队；单机无超时（单人在等自己） |
| 重复加入 | 已在 `st["players"]` → 『你已在战斗中』（幂等拒绝） |
| 满员 | `len(members) >= 4` → 『战斗满员（4 人）』 |
| 战斗结束（胜利/失败/逃跑）后加入 | battle 行已清（`clear_battle`）→ 找不到目标战斗 → 『附近没有可加入的战斗』 |
| 0 血玩家加入 | 拒绝（快照 hp>0 校验；与副本恢复进本同规则） |
| 加入者已在其他战斗 | `_in_battle` 拦截 → 『你正在战斗中』 |
| 目标战斗是 PVP | 拒绝（无 allies 概念） |
| 目标战斗是世界 Boss | 特例：世界 Boss 已是全局共享，提示走『攻击』即可（无需 allies） |
| 副本战斗让野外玩家加入 | 拒绝（封闭地图，地理不符；且副本有入本校验） |
| 队长退队 | 副本现状：队长战斗中禁止退队（social.py L453-455 拦）。野外同场后同样拦截（队伍解散 = 战斗行孤儿 → 需在 party_leave 加同款拦截或战斗行清理） |
| 全队死亡 | 副本：`_instance_defeat` 结算（按当前成员，退队者不误杀）；野外同场：胜利/失败结算按存活成员各自写回（`_handle_victory` 每成员） |
| 敌人全灭 | 结算胜利；在场成员各自解锁/清行（副本现状；野外同场需批量） |
| 敌方单位 ct 缺失/≤0 | `from_state` 兜底重置 `_ct_initial_wait`（单机已有）；副本 `_instance_ensure_player_fields` 兜底 -spd（需随时钟统一改） |

---

## 十、数据流图

```
『加入战斗』指令（新命令 join_battle）
   │
   ├─ 1. 路由/定位目标战斗
   │      ├─ db.party_members(group_id, qq_id)  → 同队伍成员列表（无队 → 拒绝）
   │      ├─ 逐成员查 db.get_battle / _instance_battle_for 找队长行（battle 存队长名下）
   │      └─ 无目标战斗 / 战斗已结束(clear_battle) / PVP → 拒绝
   │
   ├─ 2. 校验
   │      ├─ _in_battle(new) → 已在战斗中 → 拒绝
   │      ├─ 已在 st["players"] → 重复加入 → 拒绝
   │      ├─ len(st["members"]) >= 4 → 满员 → 拒绝
   │      ├─ st["over"]/result 非空 → 战斗结束 → 拒绝
   │      ├─ hp <= 0 → 拒绝
   │      └─ 地理位置（副本封闭 / 世界 Boss 特例）→ 校验
   │
   ├─ 3. 并入（只改状态，不推进行动轴）
   │      ├─ 构造新快照（_instance_start 同款 player_final_stats 实时属性）
   │      ├─ st["players"][new] = 快照（含 uid=p_{qq}、rank/reach、buffs/stacks/defending/charging）
   │      ├─ st["members"].append(new)（或按 spd 重排）
   │      ├─ st["alive"][new] = True
   │      ├─ st["p_buffs"/"p_hot"/"p_food_effects"/"mech_stacks"/"p_defending"][new] = 初始
   │      ├─ st["contribution"][new] = 0；st["threat"][new] = 0
   │      ├─ 快照["ct"] = min(存活敌方 ct, 存活玩家 ct) + _ct_cost(新快照 spd)   ← 播种（§四.2）
   │      └─ （野外同场）battle state 的 allies 追加新快照（to_state 已持久化 allies）
   │
   ├─ 4. 持久化 + 锁
   │      ├─ db.save_battle(group_id, st["leader"], st)（副本/野外统一队长行）
   │      ├─ self._lock_battle(group_id, new)
   │      └─ 广播：『XXX 加入了战斗！』（群内所有参战者可见）
   │
   └─ 5. 下个行动者（不在此处推进）
          ├─ _instance_next_actor（副本）/ 玩家消息触发（单机）→ 按 ct 最小者
          └─ 新玩家 ct 已含入场等待 → 不会立即抢占当前行动窗口

行动轴（战斗内，既有逻辑不变）：
  玩家行动（攻击/技能/防御/道具）→ _after_actor_ct("p") / 副本队友 ct 广播
  敌方段（单机 _enemy_phase / 副本 _instance_enemy_ct_acts）→ 单位 ct += cost，其余 -= cost
  新成员被 `_instance_living_player_cts` / `_instance_next_actor` 自动纳入（遍历 st["players"]）
```

---

## 十一、结论

1. **CTB 支持『加入战斗』**：引擎 allies 是运行时遍历的活列表（治疗/团队 buff/死亡剔除全部兼容动态追加），命令层 st 结构（players/members/alive 分 key）天然支持并入，行动轴（ct 最小者）自动纳入新成员——**机制上成立**。
2. **必须的三处改造**（否则并发/口径错乱）：
   - ① 副本 CTB 时钟统一到 v130.10 绝对时刻（现状 -spd 相对时钟是 v121 残留）；
   - ② 单机 `to_state` 持久化 allies（野外同场战斗必需）；
   - ③ 野外战斗存储改『队长键 + members』（与副本同构，队员反查）。
3. **ct 播种规则**：`min(存活敌方 ct, 存活玩家 ct) + 新玩家 _ct_cost(spd)`——入场有代价、不抢行动权、不会永远轮不到。`-spd` 方案（v137 原案）在 v130.10 下会产生『入场即行动』漂移，弃用。
4. **加入时机**：消息间隙（指令级同步），任意时刻可加；不推进行动轴；结束/PVP/满员/重复/0 血/异地拒绝。
5. **边界**：退队/掉线沿用副本既有守卫（party 过滤 + 60s 自动防御）；满员 4 人；重复加入幂等拒绝。
6. **最小路径**：Phase 1（时钟统一）→ 2（allies 持久化）→ 3（野外队长键）→ 4（加入战斗指令），野外组队同场战斗是 Phase 3 的自然产物。
