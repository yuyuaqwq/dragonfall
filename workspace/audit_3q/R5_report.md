# R5 CTB 时刻制审查报告（战斗核心）

审查人：R5 subagent（时序模型专项）
日期：2026-08-30
范围：`game/battle.py`（5917 行）、`game/commands/combat.py`（3150 行）、`game/commands/instance.py`（3497 行）、`game/core/battle_modes.py`（458 行）、`game/data/battle_config.py`（647 行）、`game/data/skills.py`（4055 行）、`game/core/battle_mech.py`、`game/engine.py`、`game/data/pets.py`
只查未改；git status 无 tracked 改动（仅历史遗留 untracked 文件）。

## 覆盖范围
- `game/battle.py`：全文 5917 行，重点读 CT 调度（L212-220、L111-112、L404-406、L1389-1440）、player_turn（L1571-1720）、_enemy_phase（L1722-1759）、_end_round（L5118-5189）、_turn_start（L4954-5117）、_tick_dots（L4651-4849）、冷却（L1069-1098）、蓄力（L1518-1551、L4374-4390）、防御（L2193-2202）、Boss 机制（L4159-4218、L4912-4930）
- `game/commands/instance.py`：CTB 调度（L2056-2202）、_instance_next_actor（L2636-2662）、_instance_enemy_ct_acts（L2676-2727）、_instance_ct_queue（L2730+）、_instance_auto_defend_player、敌方段单动（L2795-2850）、round 字段（L442/883/1506/1583/2153/2202/2424-2425/2807/2826）、round_acted（L2187-2200）、taunt_turns（L2287/2777-2787）
- `game/commands/combat.py`：野外战斗路由（L870-897、L1095-1120、L1409-1429、L1452-1475）、PVP（L2894-2954）、世界 Boss（L2508-2574）、状态显示（L1256/1281/1385/1552-1582）
- `game/core/battle_modes.py`：dual_form/focus/vent 回合制状态机（L106/127/274 等）
- `game/data/battle_config.py`：turns 配置（L200-201/274/296/302/351/354/381/403）、DOT_DEFS（L50）
- `game/data/skills.py`：cd/持续字段（L66 等 30+ 处）
- `game/core/battle_mech.py`：BOSS_MECHS 每 N 回合机制（L524-560）、控制回合（L157-197）
- `game/engine.py`：skill_buff_turns（L773-776）
- `game/data/pets.py`：skill_interval（L22/27/33/38）

## 结论摘要

### 1. 现在是回合制还是时刻制？（先答）
**混合体：调度层已经是"时刻制"（绝对时刻 CTB），但结算层是"回合制"——所有效果持续/冷却/机制周期都挂在"回合"（=玩家行动周期）上。**

- **调度 = 绝对时刻**：v130.10 起玩家时钟从 0 起（`game/battle.py:404-406`），行动消耗 cost = BASE_DELAY/spd（`battle.py:111-112、1389-1395`），行动后行动者 ct += cost、其余单位 ct -= cost（时间流逝广播，`battle.py:1397-1440`），0 为行动点，敌方连动按 ct 判定（`battle.py:1722-1759`）。副本由命令层 `_instance_next_actor` 按最小 ct 选行动者（`instance.py:2636-2662`），并有行动队列预览 `_instance_ct_queue`（`instance.py:2730+`）。
- **"回合"仍无处不在**：`self.round` 每玩家行动 +1（`battle.py:234、1617`）；`_end_round`（`battle.py:5118-5189`）是全部 buff/冷却/护盾/增幅递减的唯一执行点；`_turn_start`（`battle.py:4954+`）是全部"每回合开始"结算钩子（DOT/套装回复/资源回复/模式状态机）。**"一回合" ≈ 一次玩家行动 + 其后敌方段**，与玩家行动次数严格 1:1。
- **玩家视角本质**：玩家每发一条行动指令 = 推进一个"回合"，回合内的敌人几次行动由 CT 时刻决定（可能 0~8 次连动）。所以对玩家体验而言，它更像是"回合制外壳 + CTB 内部节奏"。

### 2. 回合计数与字段分布
| 字段/概念 | 位置 | 说明 |
|---|---|---|
| `self.round` | battle.py:234(0)/1617(+1)/486(序列化)/551(恢复)/4172(_boss_mech)/4616,4643(宠物)/4831-4832(dot 适应) | 玩家行动次数计数 |
| `st["round"]`（副本） | instance.py:442/883/1506/1583(初始=1)/2153(透传)/2202,2826(写回 b.round)/1211(第 N 轮显示)/2424-2425(换层重置=1) | 副本轮次显示+Boss 机制 |
| `round_acted`（副本） | instance.py:2187-2200/2424 | "全员行动过→新一轮"轮次闸门 |
| `p_ct`/单位 `ct` | battle.py:406/574-580；instance.py:189-200(播种)/2161(透传)/2208(写回) | 时刻（行动点） |
| `turn`/`turn_time`（副本） | instance.py:449-450/1505/1582/1985-1989/2091-2100/2126 | 谁行动/超时（与 CT 无关的真人轮转计时） |

**重要**：副本有两套 round 并存——命令层 `st["round"]`（显示/Boss 机制基准，换层重置 1）与 Battle 内 `b.round`（每行动+1，写回 st）；DOT 适应消退按 b.round 差判定（`battle.py:4831-4832`）。

### 3. 所有"回合"单位的机制清单（改时刻制影响面）
以下全部以"回合"为时间单位，改时刻制全部要动：

**A. buff/增益/减益持续时间（最大面）**
- `p_buffs`/`e_buffs` = `{effect: 剩余回合}`，`_end_round` 每回合 -1（battle.py:290-291、5120-5155）
- 默认 3/2 回合：BUFF_TURNS/DEBUFF_TURNS（battle.py:107-108）
- 技能增益持续 = skill_buff_turns：每级 +1 回合（engine.py:773-776）；消费点 battle.py:3349-3353（含回声延长 battle_config.py:201）、3408、3926；battle_mech.py:86-89/932-996
- 技能数据描述"持续 X 回合"：skills.py:66/80/91/102/112/255/274/284/297/452/465/489/501/674/696/706/740/868/878 等 30+ 处
- 药水/料理 3 回合：battle.py:1856/1873/1875/1891、matk_up_pot 本回合（battle.py:65）
- 一次性 buff 豁免递减（next_atk_up/buff_phys_next/stealth）：battle.py:5134-5142

**B. 技能冷却 CD**
- `self.cooldown = {技能名: 剩余回合}`（battle.py:307/512/568），`_set_skill_cd`（1075-1091，cdr 削减+时停领域套装 -1）、`_tick_cooldowns` 回合结束 -1（1093-1098）
- 技能数据 cd 字段：skills.py:66/77/89/100/112/253/273/283/292/317/332/450/461/485/498/524/672/682/694/705/715/738/751/866/877/898/909/1065 等
- 文案"冷却 X 回合"：combat.py:1385、battle.py:1951/2013

**C. DOT 持续伤害（每回合结算）**
- 毒/灼烧/流血/腐蚀"每层每回合"公式：battle.py:101-105、4651-4849（_tick_dots）
- 结算闸门 = 每玩家行动 1 次（_dot_pending，battle.py:416-418/4962-4963/527/595）；副本每轮 1 次（instance.py:2163-2165/2186-2200）；世界 Boss 每 4 次玩家行动 force 结算（combat.py:33/2539-2547）
- 适应消退"最近 2 回合"（battle.py:4831-4832）、层数每回合 -1（4841-4848）
- 阈值递增/饱和免疫回合：battle_config.py:60、battle.py:4664-4676

**D. HOT/食物持续恢复**：`p_hot {turns}`（battle.py:293/1795-1812/1909-1932），每回合开始结算

**E. 护盾**：`p_shields {turns}`（battle.py:295/1761-1777/5161-5165），回合递减；词条护盾 3 回合（377-383）

**F. 防御/架势**
- 玩家防御 = 本回合行动 + 本回合敌方伤害减半（battle.py:298/2193-2202/1722-1745）
- 副本防御持续到该玩家下次行动开始（instance.py:2115-2117）
- PVP 防御持续到对方行动（combat.py:2936-2941）；敌方 defending 减半（battle.py:5323-5324）

**G. 蓄力（玩家/敌方）**：`charging {left: 回合数}`，回合开始 -1（battle.py:299/1518-1540、2166-2175、4264-4284、4374-4390）；"需要 X 回合"

**H. 控制效果**：冻结 1 回合/眩晕/沉默 2 回合/减速 dur 回合（battle.py:4247-4262、5122-5127 行动级控制不回合递减；battle_mech.py:157-197）；睡眠按回合（battle.py:4257-4262）

**I. Boss 机制按回合计数**：召唤每 3 回合/回血每 4 回合/护盾首回合/狂暴（battle_mech.py:524-560）；阶段"每 N 回合大招"`_phase_ult_every`（battle.py:4912）、`exit_turns`（4915-4918）、`entered_at=round`（4918）；_boss_mech 全程传 round（battle.py:4172）

**J. 宠物技能每 N 回合**：`self.round % skill_interval`（battle.py:4616/4643；pets.py:22/27/33/38）

**K. 回合开始/结束钩子（大量机制）**：_turn_start 全套——套装每回合回复（battle.py:4988-5002）、被动 turn_heal/team_regen（5009-5022）、核心资源每回合回复（5039-5048）、疾风余韵上回合精力（4937-4944/5186-5187）、满溢转盾每回合限 1 次（718-743/5188-5189）、词条回合开始（3170-3201、3203+）、召唤物每回合攻击（1711-1717）、宠物回合开始技能（1626-1631）

**L. 副本轮次与杂项**：round_acted 全员轮（instance.py:2187-2200）、嘲讽 taunt_turns=2（2287/2777-2787）、破绽免疫期 1 回合（battle_config.py:381）、骨噬 3 回合（battle_config.py:403）、模式状态机回合（battle_modes.py:106/127/274；battle_config.py:274/296/302/351/354）、p_eff turns_left 衰减（battle.py:5166-5184）

**M. 状态显示文案**：combat.py:1552-1582"剩 X 回合"、1256/1281"持续 X 回合"

## 影响面评估（改时刻制）

### 可行性与本质
- **调度层已经时刻制，无需改**。CT 时间轴（BASE_DELAY=100/spd，行动点 0）就是"时刻"：单位在时间轴上按 cost 前进，"谁到 0 谁行动"。朋友说的"基于时刻"在调度层已成立（v130.10 绝对时刻，battle.py:212-220 注释直说"阴阳师式速度条"）。
- **"回合"不是多余概念，而是节拍器**：回合 = 玩家两次行动之间的时间（= 玩家一个 cost 周期 = 100/spd_p 时刻单位）。正统 CTB/ATB 同样有 round 概念。**不必也不该全删**；技术等价性：turns 换成"行动点/时刻刻度"只是数值换标。
- 真正的改造诉求若是"效果时长按真实 CT 时间流逝（敌我行动都推进效果计时）而非按玩家行动次数"，那影响面 = 本报告第 3 节全部清单。

### 改造分级
| 级别 | 内容 | 工作量 |
|---|---|---|
| **核心引擎（高）** | 新增"时间流逝结算器"：把 `_end_round`（battle.py:5118-5189）的递减、`_turn_start`（4954+）的结算、`_tick_dots` 闸门（4651+）从"每玩家行动一次"迁移到"每单位行动/每 N 时刻滴答一次"；`_after_actor_ct`（1397-1440）需发出时间流逝事件 | 重写结算挂点，风险最高 |
| **数据层（中）** | skills.py 全部 cd/持续字段、battle_config.py turns 族、battle_mech.py 每 N 回合、pets.py skill_interval、词条 turns_left、buff 表结构（p_buffs 值型→struct 型） | 全量数据迁移 |
| **命令层（中）** | instance.py round_acted/超时轮转（2187-2200）与 CT 调度关系重审；worldboss dot_act 计数（combat.py:2543-2547）；PVP defending_qq（2936-2941） | 中等 |
| **展示/文案（低）** | combat.py"剩 X 回合"（1552-1582）→"剩 X 时刻/行动点" | 纯文案 |

### 高风险点
1. **数值平衡全变**：buff 时长从"固定玩家行动数"变"时间轴刻度"后，速度堆叠会放大/缩短所有效果窗口，需全量数值标定（battle.py:111 注释"待 Agent D 模拟标定"即此风险）
2. **存档兼容**：`round`、`p_buffs` 值型、`turns_left`、`cooldown`、`p_hot`、`p_shields` 随战斗序列化（battle.py:484-533），字段语义变更需迁移脚本
3. **DOT 闸门三方不一致**已存在（单机/副本/世界 Boss 三种结算频率，battle.py:4958-4963、instance.py:2186-2200、combat.py:2543-2547），改时刻制需统一
4. **控制类"行动级"语义**（stun/freeze 不回合递减，battle.py:5122-5127）与时刻制天然契合，是少数不需改的

### 对鱼鱼问题的直接回答
- 现在是**时刻制调度 + 回合制结算**的混合；调度已"基于时刻"。
- 不是所有技能/buff/道具都要"重构成时刻"才叫 CTB——调度层已经是；只有想让持续效果按真实时间流逝时才需要迁移（第 3 节清单，量大但机械）。
- 战斗中不必消灭"回合"概念；保留"回合=玩家行动周期"作为节奏单位是 CTB 惯例，行动顺序由时刻决定即可。
