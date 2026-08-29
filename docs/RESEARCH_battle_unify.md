# 副本战斗状态机收编统一战斗引擎研究（RESEARCH_battle_unify）

> 版本：v1.0（2026-08-29）· 只读研究文档，**不含任何代码改动**
> 目标：把 `game/commands/instance.py` 中约 2500 行自写副本轮流回合 CTB 战斗状态机（ct 队列 / 仇恨 / 人数缩放 / 自动防御 / 敌我多对多）收编进统一战斗引擎 `game/battle.py`（`class Battle`，`btype=monster/worldboss/pvp`）。
> 原则：**最小改动**——战斗数值/机制（伤害公式、buff、dot、站位、蓄力、mech）一律不动，只移动"调度/时序/队列"层；不破坏现有 25+ 副本测试。
> 关联文档：`docs/CTB_REFACTOR.md`（v121 已立 CTB 统一目标，本节 1.4 明确"仇恨/嘲讽/目标选择、击杀奖励、切怪/分层/通关流程全部不变"）、`docs/INSTANCE_MAP_UNIFY_v137.md`。

---

## 0. 结论摘要（TL;DR）

| 维度 | 结论 |
|---|---|
| 现状 | 副本战斗 = **双层状态**：调度/队列/仇恨/超时在 `instance.py`（命令层），单次结算（伤害/buff/dot/蓄力/mech）在 `battle.py`（引擎，经 `Battle.from_state` 逐行动者构造单怪 Battle） |
| 关键语义差异 | instance 层 CTB 是 **v121 相对时钟**（ct=-spd 播种，行动者 +cost、其余 -cost）；battle.py 是 **v130.10 绝对时刻**（ct=+cost 起步，0 为行动点）——**两套时钟语义不等价**，是收编的第一技术障碍 |
| 引擎已有 | 多对多 `enemies` 阵列、`allies` 我方阵列、`_ct_cost`/`_after_actor_ct`/`_enemy_phase`（单玩家侧 CTB 敌方段）、`_resolve_player_target`（射程+编号）、`_resolve_ally_target`（治疗队友）、`_end_round` 等 |
| 引擎缺 | **多玩家侧 CTB 调度器**（下一行动者在"多个玩家 + 多个敌人"中取最小 ct）、玩家快照 ct 持久化通道、仇恨/嘲讽选择挂点、超时自动防御、人数缩放、动态加入（`allies` 追加）、旧 st 字段（`alive/p_defending/threat/taunt_*`）映射 |
| 收编方案 | 在 `battle.py` 新增 `btype="instance"` 分支 + 一组 `_inst_*` 方法（调度器 + 敌段循环 + 自动防御 + 仇恨/嘲讽），`instance.py` 保留**薄壳**（建 state / 展示 / 奖励 / 切怪分层 / 持久化） |
| 等价性验证 | 双实现对比测试：同一初始 state 分别跑旧 instance 逻辑与新引擎 instance 分支，断言每步 `(行动者, 目标, 伤害, ct 序列, hp)` 全等；先"函数级纯逻辑对比"，再"命令层整流程对比"（随机种子固定） |
| 最大风险 | 时钟语义迁移（v121 相对 vs v130.10 绝对）；`from_state` 单怪构造丢失阵列上下文（援军/多怪 mech）；动态 `allies` 追加与 `alive` 过滤；`round/dot_pending` 结算频次被引擎 `_end_round` 改变 |

---

## 1. 现状代码逐函数分析（instance.py）

### 1.1 副本战斗数据流总览（谁写 ct / 仇恨 / 缩放 / 自动防御，状态存哪）

```
开本 _instance_start / _enter_stage_combat / 切怪（instance.py）
  └─ _instance_build_state / _instance_build_enemy_array / _instance_reset_player_cts
       st["players"][qq] 快照: hp/mp/spd/ct(=-spd 播种) + rank/reach/uid/buffs/stacks/defending/charging
       st["enemies"]: Boss 单位 + 缩放爪牙（每单位自带 ct=-spd）
       st["alive"] / st["p_defending"] / st["threat"] / st["taunt_target"/"taunt_turns"]
       st["round_acted"] / st["dot_pending"] / st["mech_stacks"] / st["p_buffs"] ...
       （全量存 db.save_battle，battle_state JSON）

玩家行动 _instance_act（instance.py，async 命令入口）
  ├─ CTB 推进 while 循环：_instance_next_actor → 敌方段 _instance_enemy_ct_acts
  │    → 超时 _instance_auto_defend_player → 直到轮到请求玩家
  ├─ Battle.from_state({type:instance, enemies, p_buffs, e_buffs, round, p_ct, dot_pending, allies 存活快照...})
  │    b.player = snap  ← 关键：from_state 不设 player，_after_actor_ct("p") 需要行动者快照
  ├─ b.player_turn(action, skill_name, snap, enemy_act=False, target)
  │    → 引擎内: round+=1, _turn_start(dot), 技能/普攻, _after_actor_ct("p")（p_ct+=cost, 敌方 ct-=cost）
  ├─ 写回 st: snap["ct"]=b.p_ct; 其余存活玩家 ct -= p_cost（instance 层广播！引擎不管队友 ct）
  ├─ 仇恨: contribution/dealt/heal → threat[cur_key]; defend → threat 飙升; taunt → taunt_target
  └─ 死亡压缩 _instance_enemies_compact / 切怪重建阵列 / 分层推进 / 胜利失败

敌方行动 _instance_enemy_ct_acts（instance.py）
  └─ while 敌方最小 ct < 玩家最小 ct（且 <8 动）:
       _instance_enemy_one_act(st, gid, unit)
         ├─ 嘲讽判定(taunt_target/taunt_turns) → FM.select_target(unit, player_units, threat=threat_by_uid)
         ├─ Battle.from_state({enemy:unit, enemies:[unit], p_buffs[tkey]...})   ← 单怪构造
         ├─ b._enemy_turn(snap, unit) → 伤害/蓄力/mech
         ├─ _drain_pending_dmg / p_defending 减半(0.5) / hp 扣减 / alive 置 False
         └─ _sync_enemy_unit(st, unit) 写回 buffs/stacks/defending/charging/hp
       _instance_apply_enemy_act_ct(st, gid, unit)  ← 引擎 _after_actor_ct("e") 的 instance 复刻
         unit.ct += cost(基于 _enemy_stats buffed spd); 其余存活敌方 ct -= cost; 存活玩家 ct -= cost
```

**数据归属表（谁写/读什么）**

| 状态字段 | 位置 | 写入者 | 读方 |
|---|---|---|---|
| 玩家 `ct` | `st["players"][qq]["ct"]` | instance：播种、行动后写回、队友广播 -cost、自动防御 +cost | instance 调度器；`battle.p_ct` 仅临时 |
| 敌方单位 `ct` | `st["enemies"][i]["ct"]` | instance：播种、`_apply_enemy_act_ct` | instance 调度器；`battle` 内 `_after_actor_ct("e")` 只在单怪 Battle 内部生效 |
| `alive` | `st["alive"][qq]` | instance（扣血/倒下） | instance 调度器、目标选择、奖励 |
| `p_defending` | `st["p_defending"][qq]` | instance（防御/自动防御/行动开始重置） | instance `_instance_enemy_one_act` 减伤 |
| `threat` | `st["threat"][qq]` | instance（dealt/heal/defend/taunt） | instance `_instance_enemy_one_act` → `FM.select_target` |
| `taunt_target/taunt_turns` | `st` | instance（团队技 taunt） | instance 嘲讽强制选目标 |
| `enemies` | `st["enemies"]` | instance（构建/切怪/压缩） | instance 调度器；`battle.from_state` 拷贝 |
| `round_acted/dot_pending` | `st` | instance（δ副本层 dot 闸门） | instance 写回；`battle._dot_pending` 透传 |
| `contribution/mech_stacks/p_buffs/e_buffs/resources/cooldown/combo_seq/charging/player_hit` | `st` | instance 透传 ↔ `battle` 实例 | 双向 |

**关键洞察**：副本的"战斗状态"实际是一棵 `st`（dict，JSON 持久化），battle 引擎每次只被"借用"做**单行动者的瞬时结算**，从不持有整场战斗生命周期。收编 = 让 battle 引擎持有这场战斗（含玩家侧多快照），instance 只做 I/O 与展示。

### 1.2 逐函数分析（按收编相关度排序）

#### A. CTB 调度核心（必须搬）

| 函数 | 行号 | 职责 | 现状依赖 |
|---|---|---|---|
| `_instance_next_actor` | 1824 | 下一行动者 = 存活玩家与存活敌方中 ct 最小者；同 ct 玩家先 | `_instance_min_player_ct` / `_instance_min_enemy_ct` / `_instance_living_player_cts` |
| `_instance_living_player_cts` | 1803 | 在场（`_instance_current_members` 过滤退队者）且 `alive` 的玩家 `{key: ct}` | `_instance_current_members`（DB party 查询） |
| `_instance_min_player_ct` / `_instance_min_enemy_ct` | 1814 / 1819 | 存活最小 ct（None=无存活） | 同上 |
| `_instance_enemy_ct_acts` | 1864 | 敌方行动段：while 敌方最小 ct < 玩家最小 ct → `_instance_enemy_one_act` → `_instance_apply_enemy_act_ct`；上限 8 动；玩家全灭提前终止；返回 `(logs, ok)` | `_instance_min_enemy_ct` / `_instance_min_player_ct` / `_instance_enemy_units` |
| `_instance_apply_enemy_act_ct` | 1838 | 敌方行动后 ct 结算（= `battle._after_actor_ct("e")` 的 instance 复刻）：行动者 +cost（buffed spd）、其余存活敌方 -cost、存活玩家 -cost | `BT.Battle()._ct_cost` / `_enemy_stats` / `_sync_enemy_unit` |
| `_instance_auto_defend_player` | 1895 | 超时自动防御：置 `p_defending[key]=True` + 结算 defend 行动的 ct（自身 +cost、队友与敌方 -cost） | `BT.Battle()._ct_cost` / `_player_stats` |

#### B. 敌方单单位行动（必须搬/半搬）

| 函数 | 行号 | 职责 | 现状依赖 |
|---|---|---|---|
| `_instance_enemy_one_act` | 1942 | 敌方单单位行动一次：目标 = 嘲讽/仇恨/射程（`FM.select_target`）→ 单怪 `Battle.from_state` → `_enemy_turn` → 防御减半 → 扣血 → alive 标记 → `_sync_enemy_unit` 写回 | `FM.select_target` / `BT.Battle.from_state` / `_sync_enemy_unit` |
| `_sync_enemy_unit` | 2053 | 单怪 Battle 结算后单位状态写回 `st["enemies"]`（hp/max_hp/buffs/stacks/defending/charging） | 无 |

#### C. 阵列构建 / 缩放 / 初始化（搬进引擎构造或保留薄壳）

| 函数 | 行号 | 职责 | 现状依赖 |
|---|---|---|---|
| `_instance_build_enemy_array` | 520 | 由 `st["boss"]` 构建敌方阵列：Boss 主单位 + 配置 minions 展开（`_scale_enemy_copy` ×0.5、rank1、reach 按 role、is_minion）；每单位 ct=-spd 播种 | `_scale_enemy_copy` / `C.INSTANCES` |
| `_scale_enemy_copy` | 495 | 按倍率复制主怪属性派生爪牙（确定性强，无随机） | 无 |
| `_instance_elite_scale` | 409 | 精英按人数缩放（超出 min_players 每人 +50% 血/攻/魔攻） | `C.INSTANCES[inst_id].min_players` |
| `_instance_reset_player_cts` | 486 | 新敌人入场时重置存活玩家 ct = -spd（与敌方播种对称） | `_instance_ensure_player_fields` |
| `_instance_ensure_player_fields` | 583 | 玩家快照补站位字段（rank/reach/uid/buffs/stacks/defending/charging/ct=-spd 兜底） | `C.CLASSES` |
| `_enter_stage_combat` | 422 | 层内怪物投入战斗：build_monster → Boss 缩放（`hp_mult + 0.65/人`）→ 风神铭文 → 建阵列 → 重置 ct | `_instance_build_enemy_array` / `_instance_elite_scale` / `_instance_reset_player_cts` |
| `_instance_build_state` | 945 | st 初始 dict（stages 分层 / 地图模式判定） | — |
| `_instance_enemies_alive` / `_instance_enemy_units` / `_instance_enemies_compact` | 552 / 556 / 560 | 存活判定 / 存活列表 / 死亡压缩（`FM.compact` + `st["boss"]` 兼容键维护 + `_last_killed`） | `FM.compact` |
| `_instance_player_units` | 599 | 我方存活玩家单位列表（供目标选择参考） | `_instance_ensure_player_fields` |

#### D. 命令层薄壳（留 instance.py，不搬）

`_instance_act`（1320，行动入口 + CTB 推进循环 + 仇恨结算 + 写回 + 分层/切怪/通关分发）、`_instance_extract_target`（605）、`_instance_current_members`（701，DB party 过滤）、`_instance_status`（744）/`_instance_map_view`（868）/`_instance_ct_queue` 展示（1918）、`_instance_next_player_name`（1932）、`_instance_kill_reward`（2065）/`_instance_main_kill_progress`（2190）/`_instance_loot_pile`（2228）/`_instance_secret_*`（2251/2290）、`_instance_victory`（2348）/`_instance_defeat`（2493）、`_instance_battle_for`/`_instance_retreated_row`/`_instance_expired_hint`（662/675/682）、`_instance_list`（715）。

---

## 2. BT.Battle 已有能力的差距清单（battle.py 现状 vs 副本需要）

### 2.1 battle.py 已有（可直接复用）

| 能力 | 位置 | 说明 |
|---|---|---|
| 多对多敌方阵列 `enemies` | `__init__` 229-246 | `[dict(u) for u in enemies]` 拷贝；补 ct/uid/rank/reach/buffs/stacks/defending/charging |
| 我方阵列 `allies` | `__init__` 253、`from_state` 492 | v122 治疗指定队友（副本传存活玩家快照**引用**，改 hp 直接反映到 st） |
| `_ct_cost(spd)` | 1322 | `BASE_DELAY / max(1, min(spd, 80))`，副本 `_apply_enemy_act_ct`/`_auto_defend_player` 已在调用 |
| `_after_actor_ct("p"/"e")` | 1330 | 行动者 +cost、其余存活 -cost（v130.10 语义）；`side="p"` 必须传 player 否则 spd=0 卡死 |
| `_enemy_phase` | 1629 | 单玩家侧敌方行动段：while 敌方最小 ct > 0 → `_enemy_turn` → `_after_actor_ct("e")`；8 动上限；defend 减半 |
| `player_turn` | 1490 | 完整玩家行动（技能/普攻/防御/道具/蓄力/被控），enemy_act=False 支持 PVP/副本式真人操作 |
| `_enemy_turn(player, unit)` | 3857 | 敌方单单位行动（蓄力/技能/普攻/mech/被控），unit 参数化已支持多怪 |
| `_resolve_player_target` / `_resolve_ally_target` | 1366 / 1416 | 射程 + 编号（a1/a2）+ 名字前缀选敌；b1/b2 选友（治疗） |
| `_turn_start` / `_end_round` | 4398 / 4513 | dot 闸门（`_dot_pending` 已支持 instance 透传）、buff/护盾/冷却递减 |
| `from_state` / `to_state` | 476 / 426 | `type`→btype、`allies` 恢复、`p_ct`/单位 ct 兜底（v130.10 重置为初始等待） |
| `_boss_mech` | 3796 | unit 参数化，多怪逐单位触发 |

### 2.2 差距清单（GAP-*，收编必须补的）

| # | 差距 | 说明 | 严重度 |
|---|---|---|---|
| GAP-1 | **多玩家侧 CTB 调度器缺失** | `_enemy_phase` 只处理"单玩家 vs 多敌"；副本需要"多玩家 + 多敌"统一取最小 ct 行动者（`_instance_next_actor` 语义），引擎没有对应入口 | 🔴 核心 |
| GAP-2 | **玩家快照 ct 无持久化通道** | 引擎只有单个 `self.p_ct`；副本需要每个玩家快照 `snap["ct"]` 独立持久化、行动后写回、队友广播 -cost（instance 现在手写这段广播，引擎不感知队友） | 🔴 核心 |
| GAP-3 | **v121 相对时钟 vs v130.10 绝对时刻语义不一致** | instance：ct=-spd 播种、行动者 +cost、其余 -cost，最小者行动；battle：ct=初始等待(+cost)、0 为行动点、最小者行动。**两套公式计算出的行动序列/频率不同**（v130.10 修复了 v121 追赶死锁）。直接搬函数会改变副本行动节奏 → 必须统一到 v130.10 | 🔴 核心 |
| GAP-4 | **仇恨/嘲讽无引擎挂点** | `FM.select_target` 支持 threat 表，但 battle 的 `_enemy_turn`/`_enemy_phase` 不接受 threat/taunt 参数；副本的 `threat_by_uid` 与 `taunt_target/taunt_turns` 处理全在 instance | 🔴 |
| GAP-5 | **超时自动防御无引擎入口** | `_instance_auto_defend_player`（含 defend 行动 ct 结算 + 文案）是命令层概念（60s 超时），引擎不该知道 QQ 超时，但"defend 行动的 ct 结算"引擎已有（`_do_defend` 路径）；需拆：引擎收"自动防御结算"，命令层收"超时判定" | 🟡 |
| GAP-6 | **人数缩放不在引擎** | Boss `hp_mult + 0.65/人`、精英 `+0.5/人`、爪牙 `×0.5` 都是 instance 在 build 时做；引擎 `__init__` 无 `member_count` 概念。收编时缩放在**构造前**由命令层算好传入即可（不必进引擎） | 🟢 |
| GAP-7 | **`from_state` 单怪构造丢失阵列上下文** | `_instance_enemy_one_act` 每次构造 `enemies=[unit]` 单怪 Battle——引擎 `_enemy_turn` 内 `_boss_mech` 按该单位自身 mech 触发（多怪场景"逐单位各自 mech"实际正确）；但**援军**（summon）只会进 `b.enemies`，instance 靠"比对 uid 追加"补回 `st["enemies"]`；且单怪构造时 `_enemy_stats()` 用 `_active_target=unit` 解析属性 OK。收编后整阵列常驻引擎，summon 自然入阵列 | 🟡 |
| GAP-8 | **`alive`/`p_defending`/`threat`/`taunt_*` 等 st 字段无映射** | 引擎 `_player_dead` 用 hp≤0 判定，副本用 `st["alive"]` 显式标记（退队者不参与）；`p_defending` 是**每玩家** dict，引擎是单布尔。收编需把 players 快照的存活/防御/仇恨内聚进 allies 单位或 battle 实例字段 | 🔴 |
| GAP-9 | **动态加入（allies 追加）未验证** | v122 `allies` 是静态列表（构造时传存活快照）；副本"中途加入战斗"（`_instance_start` 的 members 追加/恢复）会新增玩家快照——引擎没有"战斗中追加 allies/玩家"入口，且新玩家 ct 播种语义未定义 | 🟡 |
| GAP-10 | **回合结算频次可能漂移** | 引擎 `_end_round` 在每次 `player_turn`/`_enemy_phase` 后调用（副本现状每行动者一次 buff 递减、dot 闸门一轮一次）；收编后若调度器每行动者都触发 `_end_round`，buff/冷却递减频次与现状一致；但**dot_pending/round_acted 轮次推进**（全队行动过→新一轮）目前是 instance 手写，引擎无"轮"概念 | 🟡 |
| GAP-11 | **`e_buffs` 单位级 vs 共享** | 副本 `st["e_buffs"]` 是共享 dict（老兼容键），v2 后敌方 buffs 已单位级（`u["buffs"]`）；`_instance_enemy_one_act` 里 `"e_buffs": unit.get("buffs")` 透传、写回 `st["e_buffs"]=unit.get("buffs")`——收编后统一走单位 `u["buffs"]`，兼容键仅序列化保留 | 🟢 |
| GAP-12 | **无"整场 Battle 生命周期"入口** | 现状每次行动重新 `from_state`（构造成本 + 引用断裂）；收编后需要一个 `btype="instance"` 的**常驻 Battle**（含 `st` 内聚），`player_turn`/`enemy_turn` 直接在同一实例上连续调用 | 🔴 架构 |

---

## 3. 收编改造点（每个函数搬到哪、怎么改）

### 3.1 总体架构：常驻 InstanceBattle + 命令层薄壳

```
game/battle.py (class Battle)
  ├─ __init__(btype="instance", ...): 新增 instance 分支
  │    · 内聚 st 引用: self._st = st（含 players/alive/p_defending/threat/taunt_*）
  │    · allies = 存活玩家快照（引用）；players = 全量快照（含退队者，供 alive 过滤）
  │    · enemies = st["enemies"]（引用，不再拷贝——写回零成本）
  │    · p_cts: {qq_key: ct} 由快照 dict 兼任（snap["ct"] 即权威）
  ├─ 新增 _inst_* 方法（见 3.2）
  └─ 扩展 player_turn/_enemy_phase 的 instance 分支（见 3.3）

game/commands/instance.py (InstanceCmds 薄壳)
  ├─ _instance_start/_enter_stage_combat/_instance_build_state: 保留（建 st + 缩放，传给引擎构造）
  ├─ _instance_act: 精简为"调引擎一次行动 + 写回 + 展示/奖励/分层/通关"
  ├─ 展示/奖励/切怪/分层/持久化: 全部保留
  └─ 删除: 1803-2051 段 CTB 调度函数（逻辑搬引擎）
```

### 3.2 函数级搬迁映射（必须搬 vs 可以留）

#### 🔴 必须搬（引擎新增 `_inst_*`，语义对齐 battle CTB）

| 现状函数 | 搬入位置（battle.py） | 改造点 |
|---|---|---|
| `_instance_next_actor` | 新增 `Battle._inst_next_actor()` | 改为 v130.10 语义：下一行动者 = `min(存活玩家 snap["ct"], 存活敌方 u["ct"])`（**玩家 ct 由快照读，不再是 -spd 相对值**；同 ct 玩家先保底不变） |
| `_instance_min_player_ct` / `_instance_min_enemy_ct` / `_instance_living_player_cts` | 新增 `Battle._inst_min_player_ct()` / `_inst_min_enemy_ct()` / `_inst_living_cts()` | 玩家侧改用 `self.allies` 存活过滤（`alive` 与 hp>0 双判）+ 在场过滤改为命令层注入 `active_keys`（退队判定是 QQ 业务，不搬引擎） |
| `_instance_apply_enemy_act_ct` | **直接删除** → 用引擎 `_after_actor_ct("e", unit, player=行动者快照)` | 引擎方法已实现同语义（行动者 +cost(buffed)、其余敌方 -cost）；**唯一差异**：引擎不广播"队友玩家 ct -cost"——需扩展 `_after_actor_ct`：当 `self.allies` 非空时，对 allies 中非行动者存活成员 `snap["ct"] -= e_cost`（v121 对称性保留） |
| `_instance_auto_defend_player` | 拆两半：超时判定留命令层；"防御结算"→ 引擎 `Battle._inst_auto_defend(player)` | 引擎方法 = `p_defending[qq]=True` + 该玩家 `ct += cost(_player_stats buffed)` + 队友/敌方 -cost（复用 `_after_actor_ct("p", player=...)` 扩展的队友广播） |
| `_instance_enemy_ct_acts` | 新增 `Battle._inst_enemy_phase(logs)` | 改 v130.10 判定：while `min(enemy ct) <= 0`（行动点）且 `< min(player ct)` → `_enemy_turn(player=目标玩家快照, unit)` → `_after_actor_ct("e", unit)`；8 动上限、全灭提前终止保留；**目标选择**在 `_enemy_turn` 前用 `_inst_pick_target(unit)`（见下） |
| `_instance_enemy_one_act` | 合并进 `Battle._inst_enemy_phase`（或保留 `_inst_enemy_one_act`） | 目标 = `_inst_pick_target(unit)`（嘲讽 → 仇恨/射程 `select_target(unit, allies, threat=threat_by_uid)`，同现状）；防御减半走 `_damage_player` 的 defend 参数或现状 0.5 折；hp 扣减直接改快照（allies 引用）；`alive[qq]=False` 同步 |
| `_sync_enemy_unit` | 删除（enemies 已是引用，`_enemy_turn` 原地改 `u["buffs"]/["stacks"]` 即写回） | 无 |
| `_instance_reset_player_cts` | 保留在命令层（换怪/切层时调用）或引擎 `_inst_reset_cts()` | v130.10 语义：重置为 `ct = _ct_initial_wait(spd)`（不再是 -spd！否则与引擎时钟混用出 bug） |

#### 🟡 半搬（数据进引擎构造，逻辑留命令层）

| 现状函数 | 去向 | 改造点 |
|---|---|---|
| `_instance_build_enemy_array` | 保留命令层（构造期纯数据，无状态），把"ct 播种"改为 `_ct_initial_wait(spd)` | 命令层 `st["enemies"]` 构造完 → 一次性传给 `Battle(btype="instance", enemies=...)` |
| `_scale_enemy_copy` | 保留命令层 | 无改动 |
| `_instance_elite_scale` / `_enter_stage_combat` 的 Boss 缩放 | 保留命令层 | 缩放在引擎构造**前**完成，引擎不感知人数（GAP-6 结论） |
| `_instance_ensure_player_fields` | 保留命令层 | 构造前补字段；引擎 `__init__` 的 instance 分支兜底 `setdefault` 一次即可 |
| `_instance_enemies_compact` | 保留命令层（或引擎 `_inst_compact()`） | 引擎 `_remove_unit` 已做死亡压缩+`killed_enemies` 记录；命令层仍需 `st["boss"]` 兼容键维护与 `_last_killed`。**建议**：引擎实例持有 `killed_enemies`，命令层读它发奖励（消除双份压缩逻辑） |

#### 🟢 可以留（薄壳，不搬）

`_instance_act` 的调度 while 循环 → 改为"一次 `engine.player_turn(...)` 调用 + 一次 `engine._inst_enemy_phase()` 调用"，但**行动者判定/超时轮转**仍可留在命令层（它需要 QQ 业务上下文：谁是请求者、谁超时）；`_instance_extract_target`、`_instance_current_members`、展示（status/map_view/ct_queue/next_player_name）、奖励、分层、通关、`_instance_victory/_defeat`、`_instance_list`、`_instance_battle_for` 等——全部保留。

### 3.3 引擎侧扩展点（battle.py 具体改法草案）

```python
# ---- __init__ 新增 instance 分支 ----
def __init__(self, btype="monster", ..., enemies=None, allies=None, st=None, active_keys=None):
    ...
    if btype == "instance":
        # 内聚副本状态：enemies/allies 直接引用 st 对象（非拷贝）
        self._st = st or {}
        self.allies = allies or []          # 存活玩家快照引用（含 ct/rank/reach/buffs...）
        self._players_all = (st or {}).get("players") or {}   # 全量快照（退队者保留）
        self._active_keys = active_keys or [str(p.get("qq_id")) for p in self.allies]
        self.p_cts = None                   # 弃用：玩家 ct 权威 = snap["ct"]

# ---- _after_actor_ct 扩展（队友广播，v121 对称性） ----
def _after_actor_ct(self, side, unit=None, player=None):
    ...原逻辑...
    if self.allies and side == "e":
        for a in self.allies:
            if a is not player and a.get("hp", 0) > 0:
                a["ct"] = float(a.get("ct", 0) or 0) - e_cost
    elif self.allies and side == "p":
        for a in self.allies:
            if a is not player and a.get("hp", 0) > 0:
                a["ct"] = float(a.get("ct", 0) or 0) - p_cost

# ---- 新增：敌方段（instance 多对多版） ----
def _inst_enemy_phase(self, logs, target_player=None):
    """while min(enemy ct) <= 0 and min(enemy ct) < min(player ct): 行动一次"""
    from .core.formation import alive_units, select_target
    _guard = 0
    while _guard < 8:
        alive = alive_units(self.enemies)
        players = [a for a in self.allies if a.get("hp", 0) > 0]
        if not alive or not players:
            break
        me = min(float(u.get("ct", 0) or 0) for u in alive)
        mp = min(float(a.get("ct", 0) or 0) for a in players)
        if me > 0.0 or me >= mp:          # v130.10：0 为行动点
            break
        unit = min(alive, key=lambda u: float(u.get("ct", 0) or 0))
        tgt = self._inst_pick_target(unit)   # 嘲讽 → select_target(threat)
        if tgt is None:
            self._after_actor_ct("e", unit)  # 无目标也结算（与现状一致：return 前不扣血但 ct 照走）
            _guard += 1
            continue
        mlogs, dmg = self._enemy_turn(tgt, unit)   # 目标玩家快照作为 player 参数
        logs += mlogs
        ...防御减半/扣血/alive 标记（同 _instance_enemy_one_act 现逻辑，快照引用直接改）...
        self._after_actor_ct("e", unit, player=tgt)
        _guard += 1
    return logs

# ---- 新增：仇恨/嘲讽目标 ----
def _inst_pick_target(self, unit):
    taunt = self._st.get("taunt_target")
    if taunt and self._st.get("taunt_turns", 0) > 0:
        for a in self.allies:
            if str(a.get("qq_id")) == str(taunt) and int(a.get("rank", 1) or 1) <= int(unit.get("reach", 1) or 1):
                self._st["taunt_turns"] = max(0, int(self._st.get("taunt_turns", 0)) - 1)
                ...日志...
                return a
        self._st.pop("taunt_target", None)
    threat_by_uid = {str(a.get("uid")): float(self._st.get("threat", {}).get(str(a.get("qq_id")), 0)) for a in self.allies}
    return select_target(unit, self.allies, threat=threat_by_uid)

# ---- 新增：自动防御（引擎只收"结算"，超时判定在命令层） ----
def _inst_auto_defend(self, player):
    self._st.setdefault("p_defending", {})[str(player.get("qq_id"))] = True
    self._after_actor_ct("p", player=player)   # 自身 +cost + 队友/敌方 -cost（扩展后自动广播）
    return [f"⏰ {player.get('name', '')} 迟迟没有行动，自动进入防御姿态！"]

# ---- player_turn 的 instance 分支 ----
def player_turn(self, action, skill_name, player, enemy_act=False, target=None):
    # 现有逻辑不变（round+=1, _turn_start, 行动, _after_actor_ct("p")）
    # instance 下 enemy_act=False 时敌方段不在此结算（由命令层/调度器调 _inst_enemy_phase）
    ...
```

### 3.4 数据格式对齐（st ↔ battle state 字段映射）

| st 字段（instance） | battle state 键（现有） | 收编后去向 |
|---|---|---|
| `st["players"][qq]["ct"]` | `"p_ct"`（单值） | **保留 `snap["ct"]` 为权威**；`b.p_cts` 弃用；`from_state` 的 `p_ct` 仅兼容单机 |
| `st["enemies"]` | `"enemies"` | 引用同一列表（引擎构造 `enemies=[dict(u) for u in ...]` 的拷贝要改为 `enemies=st["enemies"]` 直传，或用 `b.enemies = st["enemies"]` 覆盖） |
| `st["alive"]` | —（引擎用 hp≤0） | `Battle._inst` 内 `alive_keys`（命令层注入 `_instance_current_members` 结果） |
| `st["p_defending"][qq]` | `"p_defending"`（单布尔） | 保留 `st["p_defending"]` dict；引擎实例侧 `_st` 引用 |
| `st["threat"]` / `st["taunt_target"/"taunt_turns"]` | — | 保留 `_st` 引用（引擎只读/改写，命令层初始化） |
| `st["round_acted"]` / `st["dot_pending"]` | `"dot_pending"`（已透传） | 保留命令层管理（轮次语义是副本业务）；`b._dot_pending` 继续透传 |
| `st["p_buffs"/"p_hot"/"p_food_effects"/"mech_stacks"/"resources"/"cooldown"/"combo_seq"/"charging"/"player_hit"]` | 已有对应键 | 每玩家行动前把 `st[...][qq]` 拷入 b 实例、行动后拷回（现状机制，收编后仍需要——除非引擎改为"每玩家一份 buff 表"，那是更大重构，**不做**） |

**关键决定**：收编**不改** `battle.to_state/from_state` 的单机结构（25+ 测试依赖），只新增 instance 分支的 `st` 内聚路径。

---

## 4. 等价性验证方案（新旧输出对比测试）

### 4.1 总体思路

同一初始 state + 同一行动序列 + 固定随机种子 → 旧实现（现 instance.py 逻辑）与新实现（battle.py instance 分支）各跑一遍 → 逐行动对比。

### 4.2 测试分层

#### 层 1：函数级纯逻辑对比（核心，无 I/O）

直接 import 两个实现，喂同一 state，断言每一步输出全等：

```python
# tests/test_battle_unify_eq.py（草案）
import random
from game import battle as BT
from game.commands import instance as INST

def run_old(st, actions, seed=42):
    """旧：逐行动调 instance 的 CTB 函数（_instance_next_actor → _instance_enemy_ct_acts → ...）"""
    ic = INST.InstanceCmds()
    logs_all, trace = [], []
    for act in actions:
        nxt = ic._instance_next_actor(st, GID)
        trace.append(("actor", nxt))
        if nxt[0] == "e":
            elogs, ok = ic._instance_enemy_ct_acts(st, GID)
            logs_all += elogs
        else:
            b = BT.Battle.from_state({...构造同 _instance_act 1434...})
            b.player = st["players"][nxt[1]]
            al, _ = b.player_turn(act, None, st["players"][nxt[1]], enemy_act=False)
            st["players"][nxt[1]]["ct"] = b.p_ct
            ...写回（同 _instance_act 1469-1539）...
            logs_all += al
        trace.append(("snapshot", snap_state(st)))   # ct 全表/enemies hp/players hp/alive/p_defending/threat
    return trace

def run_new(st, actions, seed=42):
    """新：常驻 Battle(btype="instance")，player_turn + _inst_enemy_phase 交替"""
    eng = BT.Battle("instance", enemies=st["enemies"], allies=存活快照, st=st)
    trace = []
    for act in actions:
        nxt = eng._inst_next_actor()
        trace.append(("actor", nxt))
        if nxt[0] == "e":
            eng._inst_enemy_phase(logs, target_player=...)
        else:
            eng.player_turn(act, None, st["players"][nxt[1]], enemy_act=False)
        trace.append(("snapshot", snap_state(st)))
    return trace

def snap_state(st):
    """可比对快照：ct 全表 + hp 全表 + alive + p_defending + threat + enemies(uid,hp,ct,buffs)"""
    return json.dumps({...}, sort_keys=True)

# 用例矩阵：
#  ① 单人副本 vs 单怪（最简）
#  ② 3 人队 vs Boss+2 爪牙（多对多，混合配速：快玩家/慢玩家/快怪/慢怪）
#  ③ 嘲讽触发（团队技 taunt → 强制目标 2 回合）
#  ④ 超时自动防御（turn_time 拨旧 60s+ → 自动防御路径）
#  ⑤ 玩家死亡/同归于尽（alive 全 False → 敌段提前终止）
#  ⑥ 切怪（kill → 重建阵列 → reset ct）
#  ⑦ 援军召唤（Boss mech summon → 阵列追加）
# 每用例：随机种子固定；行动序列固定；断言 trace 逐条全等
```

**断言粒度**（逐行动）：
- `actor`：`("p", key)` / `("e", uid)` 必须一致（**行动者序列是等价性的第一硬指标**——它由 ct 序列唯一决定）
- 每行动后的 `snapshot`：所有存活单位 `ct`、所有 `hp`、`alive`、`p_defending`、`threat`、敌方 `buffs/stacks` 全等
- 伤害值隐含在 hp 快照差异中（比"伤害数字"更可靠，避免文案差异干扰）

#### 层 2：命令层整流程对比（端到端，回归网）

```python
# 草案：复用 conftest 的 FakeEvent/run
async def eq_flow(gid, qid, inst_name, seed=42):
    random.seed(seed)
    out_old = await run_full_old_flow(...)   # 现有 test_commands_instance.py 风格：开本→探索→行动循环
    random.seed(seed)
    out_new = await run_full_new_flow(...)   # 同一流程走新引擎（开关：env DRAGONFALL_BATTLE_UNIFY=1 切 instance._act 内部实现）
    assert normalize(out_old) == normalize(out_new)   # 归一化（去随机文案/时间戳）后全等
```

- **落地方式**：给 `instance.py` 加一个模块级开关（`_USE_UNIFIED_ENGINE` 环境变量/常量），`_instance_act` 内二选一：旧调度循环 / 新引擎调用。同一测试文件用开关跑两遍对比——**不用改任何现有 25+ 测试**，它们照常跑旧路径回归；新对比测试专测开关切换。
- 归一化：去掉 `⏳` 时间戳、随机命中文案、`剩余 X/Y` 中的动态数字（或保留数字但固定 seed 后应全等——优先保留，更严格）。
- 回归门槛：**现有 test_commands_instance.py 全部通过 = 新旧等价的最低门槛**（先切开关跑全量，再逐步删旧路径）。

#### 层 3：长程统计对比（节奏/胜率不漂移）

```
固定队伍 vs 固定副本配置 → 新引擎跑 N=200 场（不同 seed）→ 统计：
  胜率 / 平均回合数 / 玩家平均受击次数 / 敌方行动次数分布
旧实现跑同样 N 场 → 对比分布差异 < 容差（如胜率 ±3pp）
```
（v121 历史教训：CTB 时钟改版曾让 Boss 站桩/玩家暴毙，长程分布是防回归的保险丝。见 docs/NUMERIC_TEST.md）

### 4.3 测试放置与运行

- 新文件：`tests/test_battle_unify_eq.py`（层 1 + 层 2 开关）、`tests/sim_battle_unify_stats.py`（层 3，可选）
- 运行：`python tests/test_battle_unify_eq.py`（与现有测试同风格：`check()` + `if __name__ == "__main__"`）
- 现有 `tests/test_commands_instance.py`（25+ 断言）**不改**，作为旧路径回归基准

---

## 5. 风险点

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| R1 | **时钟语义迁移（v121 相对 → v130.10 绝对）** | 行动序列/频率改变——副本玩家行动节奏、敌方连动次数全变；若 instance 仍按 -spd 播种而引擎按 +cost 播种，同一 st 读出的行动者不同 | 收编时**统一播种**：`_instance_reset_player_cts` 与 `_instance_build_enemy_array` 的 ct 初始化改为 `_ct_initial_wait(spd)`；等价性测试层 1 的用例 ①-② 专测播种后的首行动者 |
| R2 | **队友 ct 广播遗漏** | 引擎 `_after_actor_ct` 只动 `p_ct`（单值）与 enemies；若收编时忘记扩展"allies 非行动者 -cost"，多玩家下时间流逝不对称，敌方相对未行动玩家行动偏快（v121 审计已修过一次，勿回退） | 扩展 `_after_actor_ct` 的 allies 广播；层 1 用例 ② 专测 3 人队 ct 全表全等 |
| R3 | **`_enemy_turn` 的 player 参数语义** | 副本敌方行动目标是**具体玩家快照**；引擎 `_enemy_turn(player, unit)` 的 player 决定 `_player_stats`/闪避/减伤。若传错（如传行动者而非目标），防御减半/闪避/装备词条全错 | `_inst_enemy_phase` 明确 `player=目标快照`；层 1 用例 ③（嘲讽/仇恨目标）断言伤害作用于正确目标 |
| R4 | **单怪构造 vs 整阵列构造的 mech/援军差异** | 现状 `_instance_enemy_one_act` 单怪 Battle：`_boss_mech` 逐单位正确，但 **summon 援军**只能靠"uid 比对追加"回写；整阵列常驻后 summon 自然进 `b.enemies`——`e_minions` 兼容键、`st["enemies"]` 追加逻辑要保留命令层读 `b.enemies` 的通道 | 层 1 用例 ⑦ 专测援军；`_sync_enemy_unit` 删除后确认 `b.enemies` 与 `st["enemies"]` 同一引用 |
| R5 | **`p_defending` 作用域** | 引擎单布尔 vs 副本每玩家 dict；防御过期点 = 该玩家下次行动开始（现状 `_instance_act` 行动前重置）。收编后若引擎在 `player_turn` 内统一重置，会破坏"防御覆盖到下次行动前" | 重置逻辑留在命令层行动入口（现状 1415 行），引擎只读写 `_st["p_defending"]` |
| R6 | **`round`/dot 结算频次漂移** | 引擎 `player_turn` 每次 `round += 1` + `_turn_start`（dot）；副本现状每行动者一次、dot 由 `dot_pending` 闸门每轮一次。收编后若引擎自动 `_end_round` 而命令层又手动推进 `round_acted`，会出现 buff 双递减或 dot 漏结算 | 明确"谁推进轮次"：**引擎只管行动者级结算**（round+=1/_turn_start/_end_round），`round_acted`/`dot_pending` 轮次推进仍由命令层在行动后写回（现状 1480-1494 保留） |
| R7 | **动态加入（allies 追加）** | 中途加入玩家：新快照 ct 播种、`alive`/`p_defending`/`threat` 补键、`_instance_current_members` 过滤变化；引擎常驻实例的 `allies` 列表需支持追加 | 命令层在加入时：补 `st` 键 + `eng.allies.append(snap)` + `_inst_reset_cts`（或按 v121 语义 -spd 播种后由时钟自然追赶）；层 1 用例 ⑧ 专测 |
| R8 | **退队成员（`_instance_current_members`）** | 引擎不感知 QQ 队伍业务；收编后调度器若用全量 `st["players"]` 会把退队者当行动者 | 命令层每次行动前注入 `active_keys`（`_instance_current_members` 结果）；引擎 `_inst_living_cts` 严格按 active_keys 过滤 |
| R9 | **`from_state` 引用拷贝断裂** | 现状 `Battle.from_state` 对 enemies 做 `dict(u)` 浅拷贝；若收编沿用拷贝，引擎内改 buffs 不回写 st | instance 分支用**引用直传**（`enemies=st["enemies"]` 或构造后 `b.enemies = st["enemies"]` 覆盖），并加注释防回归 |
| R10 | **随机性引入** | `select_target` 同层平局 `random.choice`、敌方技能 `random.random()`；新旧实现若 random 调用顺序不同 → 序列全等断言失败 | 固定 seed + **对比测试内同时喂同一 RNG 流**（`random.setstate` 同步）或允许"归一化后"比较；文案类差异归一化 |
| R11 | **现有 25+ 测试回归** | 收编误伤 instance 路径（切怪/分层/通关/奖励依赖 st 结构） | 全程开关隔离（`_USE_UNIFIED_ENGINE`），现有测试默认旧路径；收编完成、层 1/层 2 全等后，再切新路径跑全量回归，最后删旧代码 |
| R12 | **`e_buffs` 兼容键分裂** | 现状 `st["e_buffs"]` 与单位 `u["buffs"]` 并存；整阵列常驻后以单位级为准，老代码若仍读写 `st["e_buffs"]` 会不同步 | 收编后 `st["e_buffs"]` 仅作序列化兼容输出（= 主目标 buffs），引擎一律读写 `u["buffs"]` |

---

## 6. 实施顺序建议（最小改动路径）

1. **Phase 0（不动代码）**：本文档定稿；补层 1 测试骨架（`tests/test_battle_unify_eq.py` 先写"旧实现快照"基线，跑通）。
2. **Phase 1**：battle.py 加 `btype="instance"` 构造分支 + `_after_actor_ct` allies 广播 + `_inst_*` 方法族（纯新增，不影响 monster/worldboss/pvp 路径）。
3. **Phase 2**：instance.py 加 `_USE_UNIFIED_ENGINE` 开关，`_instance_act`/`_instance_enemy_one_act` 双路径；层 1 对比测试全绿（逐行动 trace 全等）。
4. **Phase 3**：层 2 端到端对比（现有 test_commands_instance.py 在新路径下全绿）。
5. **Phase 4**：层 3 长程统计对比（胜率/节奏分布不漂移）。
6. **Phase 5**：删旧 CTB 调度函数（1803-2051 段），命令层转薄壳；全量回归；更新 `docs/CTB_REFACTOR.md` 与 `ARCHITECTURE.md` 的副本章节。

---

## 7. 参考

- `game/battle.py`：`__init__` 221-361、`_ct_cost` 1322、`_after_actor_ct` 1330、`player_turn` 1490、`_enemy_phase` 1629、`_enemy_turn` 3857、`_turn_start` 4398、`_end_round` 4513、`from_state` 476、`to_state` 426
- `game/commands/instance.py`：CTB 段 1802-2051、`_instance_act` 1320、`_instance_build_state` 945、`_enter_stage_combat` 422、阵列 486-604
- `game/core/formation.py`：`select_target` 34（threat 参数）、`compact` 110、`numbered_units` 140
- `docs/CTB_REFACTOR.md`（v121 规格，§1.4 副本调度）、`docs/NUMERIC_TEST.md`（v130.10 绝对时刻改版背景）
- `tests/test_commands_instance.py`（25+ 断言，含 CTB 语义校验 `_next_player_key`）
