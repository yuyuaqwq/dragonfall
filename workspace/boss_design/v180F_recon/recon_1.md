审计完成。以下是结构化清单（行号以 battle.py 为准；涉及 zone 外的支撑函数会标注）。

---

# battle.py L2601–5200 玩家侧容器审计清单

## 0. 架构前提（决定一切的关键事实）

- **self.player = 单一焦点玩家 actor dict**（v180-B 权威容器）。引擎内所有 `_p_*` 状态袋 helper（`_p_buffs_bag/_p_res/_p_stacks/_p_shields_bag/_p_charging/_p_hot/...`，L1523–1618）**全部动态读 `self.player`**，换绑即跟随。
- **self.allies = 副本其他/全部存活成员快照引用数组**（含行动者本人，见 instance.py L2606-2608；野外/单人 = `[]`，battle.py L659、L2654 判空走单人语义）。
- **self.companions = 玩家侧非玩家 actor 阵列**（召唤物/宠物，side=player+kind，L700-703）。

---

## 1. Zone 内 self.player / self.allies / self.companions 字面量触点总表

| 行号 | 函数 | 容器 | 用途（一句话） |
|---|---|---|---|
| 2650–2669 | `_resolve_ally_target` | self.allies（2654/2660/2664） | 解析治疗指定队友：`b<N>` 站位编号/uid 精确/名字前缀，allies 空或找不到 → None（=奶自己） |
| 2789–2805 | `player_turn` | self.player（2796 兜底绑定、2801-2805 面板同步） | 焦点玩家 actor 化收口：self.player 权威、测试直调兜底绑定、浅拷贝模拟器同步 hp/mp |
| 3022–3023 | `player_turn` | self.companions | 玩家正常行动结束后触发随从自动行为（`_companions_trigger("player_act")`，v180-C S2） |
| 3374 | `_add_shield` | self.player | 读焦点玩家 shield_power 放大盾值；盾写入 `_p_shields_bag()`（即 self.player["shields"]） |
| 3742–3743 | `_do_player_skill` | self.allies | 治疗技带 target 且 allies 非空 → 校验队友存在，找不到拦截（不扣资源/不耗刻） |
| 4119 / 4127 / 4136–4137 | `_player_stats` | self.player | 武器特效数据查表走**焦点玩家**（风痕 wind_mark / 翠风 novice_wind_spd / 雷纹 thunder_weave 的 effect_data 读 self.player） |
| 4788–4792 | `_set_miracle_team_heal` | self.allies（4790） | 圣典·日冕 2 件：二档神迹先奶焦点 player（4788-4789）再循环 allies 全体回体力 |

**Zone 内全部 `_p_*` helper 调用（L2830/2860/2865/2884/2952/2967/2973/2993/3452/3521 等数十处）都间接经 self.player**——这些是语义上的"焦点读"，未逐行列字面量。

---

## 2. player_turn 的"焦点玩家"处理（L2778–3030）

### 2.1 焦点绑定
- L2789-2797：**行动者即焦点**。命令层先绑 `b.player = snap` 再调 `player_turn`（instance.py L2621-2626）；self.player 为空才用入参兜底。
- L2798 `_apply_restore_pstate()`：from_state 暂存的战斗状态单次灌入焦点 actor（L1131-1164）。
- L2801-2805：入参与 self.player 不同 dict（模拟器浅拷贝）→ 只同步 hp/mp/max_hp/max_mp 面板键。
- L2811-2815 / L2818-2827：焦点 max_hp/max_mp 实时刷新 + v139 模式配置注入。

### 2.2 单行动者管线（整个玩家行动全单焦点）
沉默拦截(2830) / O118 技能预检(2836) / 不动如山(2848) / 蓄力结算(2860) / `_turn_start`(2861, 内部 L8405-8409 记 `_last_player`=入参) / 食物 HOT 挂卡(2865-2876) / 战意免控(2884-2905) / 被控跳过(2906-2917) / 蓄力拦截(2920) / 目标解析(2926-2948) / defend/flee/item/skill/attack(2950-3010) —— **全部只作用于入参 player（=self.player）这一个 actor**。
- 行动后 `_after_actor_ct("p")` 写**单值 `self.p_ct`**（L2578）：battle 引擎只维护"当前行动者"一条玩家时间轴。

### 2.3 副本多人：队友（allies）怎么参与 → **只有焦点玩家能行动，队友不行动**
- **引擎内无轮转**：battle 不选"下一个玩家"。副本轮转在命令层：instance.py `_instance_next_actor`(L3167-3179，存活玩家/敌方 ct 最小者) → `_instance_act`(L2511-2538，非请求玩家超时自动防御否则等待) → 每刻**重建 Battle + `b.player = snap`**（instance.py L2621-2626）后才调 player_turn。每玩家独立 `snap["ct"]`，写回 b.p_ct（instance.py L2665-2677）。
- 队友在 battle 引擎内**仅三种被动角色**：
  1. **敌方目标池**（见 §3）——会被怪打；
  2. **治疗目标池**（`b<N>` 编号，见 §4）——会被焦点奶；
  3. **团队效果接收者**（heal_all/buff 广播）——但**不在引擎内落地**：`_skill_buff`/`_skill_heal` 只把 `team_effects` 记入列表（L5570-5574/L5491-5493），逐人上 buff/回血由命令层 `_apply_team_effect`（instance.py L3069+）完成。
- 随从（companions）只在焦点玩家行动后触发（L3022），打敌人、奶 owner（`_last_player or self.player`，L9102），不碰队友。

---

## 3. 敌方行动选目标（_pick_enemy_target 在 L1166，zone 外；zone 内驱动链）

调用链：`_enemy_phase`(L3032) → `_process_until` enemy_act 分支(L3258-3289，**L3272 `_enemy_turn(player, unit)` 的 player=焦点玩家入参**) → `_enemy_turn`(L7055) **L7076-7086**：
- 若 `self._st and self.allies and player`（副本）→ 默认 `_enemy_pick_target=True` → `_pick_enemy_target(e)` 从 **self.allies（全存活玩家快照，含焦点本人）**重选；
- 野外/单人（无 _st/allies）→ player 入参原样为目标。

`_pick_enemy_target`(L1166-1206) 选择逻辑：
| 步骤 | 行号 | 说明 |
|---|---|---|
| 候选池 | 1176-1179 | `self.allies` 中 st.alive=True 者 |
| 嘲讽强制 | 1181-1186 | taunt_target 存活 → 必选 + `_load_player_state` |
| 仇恨表 | 1188-1191 | threat[uid→qq_id]，boss 默认 hate_top、其余 front（1199-1201） |
| 策略选人 | 1201 | `FM.pick_by_policy`（monster_mods.target_policy 数据驱动） |
| **切焦点** | 1202-1203 | 选中后 `_load_player_state(qq_id)` → **self.player 重新指向被打者**（L1070 换绑 + L1091-1122 st 顶层 per-player 旁路键合并 + L1126 记 `_last_focused_qid`） |

⚠️ 关键发现：**敌方行动事件在焦点玩家自己的回合里会中途把 self.player 换绑成被打的队友**（_process_until 在 player_turn 尾部推进）。当前安全仅因为敌方段是 player_turn 最后一步（L3030 后无焦点读）；且 instance 侧下一行动者 act 前会重新 `b.player = snap`。这是"单焦点假设"最脆弱的点。

---

## 4. 治疗/增益技能目标选择——player 与 allies **分开处理**

### 治疗（K_HEAL）
| 环节 | 行号 | 行为 |
|---|---|---|
| player_turn 目标分流 | 2929-2934 | 治疗技 → 不解析敌人目标，`_active_target=None` |
| 目标校验 | 3742-3745 | `target and self.allies` → `_resolve_ally_target` 找不到即拦截（不耗刻）；**allies 空（单人）= 忽略 target 按奶自己** |
| 目标解析 | 2650-2669 | 只查 self.allies：`b<N>`(2660)/uid/名字前缀(2664)；allies 空或未命中 → None |
| 分支落地 | 5297-5300（zone 外） | `target_unit = target_ally if target_ally is not None else player` —— **指定队友走 ally 分支，None/单人走 player 分支（奶自己）** |
| 溢出护盾分叉 | 5436-5446 / 5467-5478 | 奶队友 → 盾写 `target_unit["p_shields"]`；奶自己 → `self._add_shield`（焦点 shields） |

→ 治疗是唯一"指定队友"已打通的口子，但**只能单目标**（b1/b2…），无群奶引擎内实现。

### 增益（K_BUFF）
- `_skill_buff`(L5510-5580) **严格 self**：效果写 `self._cast_buffs()`（=焦点玩家 buffs，L5555），**没有任何"给指定队友上 buff"的入口/目标参数**。
- `team` 字段只进 `team_effects` 广播列表（L5569-5574），命令层逐人上身（instance.py L3069+）。技能管线内不存在"buff 队友"语义。

---

## 5. 判断：单焦点假设 vs 已多队友化

### A. 强"单焦点/单行动者"假设（v180F 重构重点）
| # | 现象 | 证据 |
|---|---|---|
| 1 | **玩家行动入口 = 单 actor + 单 p_ct**；副本多玩家轮转完全在命令层（instance.py），引擎内无"下一玩家"概念 | player_turn L2778-3030；`_after_actor_ct` L2578 单值 p_ct |
| 2 | 全部 `_p_*` 状态袋只读 self.player；任何队友行动前必须先 `_load_player_state`/`b.player=snap` 换焦点 | L1523-1618 |
| 3 | 增益/团队效果无"对任意队友生效"的引擎内路径（team_effects 只是广播，落地在外层） | L5569-5574 + instance.py L3069 |
| 4 | **敌方事件队列中途换绑 self.player**（被打队友变焦点）后无显式切回；目前靠"敌方段在 turn 尾部"才安全 | L1202-1203 + L3030 |
| 5 | `_player_stats(入参)` 混读焦点状态：buff/poi/武器特效段(3987/4115-4141)读的是 self.player 焦点袋——**对非焦点 allies 成员调 `_player_stats` 会拿错 buffs**。当前靠"结算前必切焦点"维持正确 | 4119/4127/4136-4137 |
| 6 | 护盾键不一致：队友溢出盾写 `target["p_shields"]`（5437/5468），引擎吸收走 `actor["shields"]`（10213）——engine 内没有直接对 allies 结算伤害吸收盾的主路径（都靠 instance 侧独立 Battle + 切焦点） | 5436-5478 vs 10211-10227 |
| 7 | `_player_attacker` uid 硬编码 `"player"`（2598），与 allies 的 `p_{qq_id}`(646) 口径不一 | L2596-2598 |
| 8 | 蓄力/防御/逃跑/道具全落在焦点上，队友无对应行为状态机（各自快照有 charging/defending 键但引擎只在焦点上驱动） | 2950-2968、_do_defend 3912 |

### B. 已经能处理多队友/已 actor 化
| # | 能力 | 证据 |
|---|---|---|
| 1 | **敌方选目标已全 allies 多目标化**（policy/仇恨/嘲讽/点名，选谁打谁） | `_pick_enemy_target` L1166-1206；`_enemy_turn` L7076-7086 |
| 2 | **治疗指定队友已打通**（b<N>/uid/名前，含奶队友日志/溢出盾分叉） | 2650-2669、3742-3745、_skill_heal 5297+ |
| 3 | 团队回血/套装/回声 tick 已"焦点 + allies 循环"两段式（hp<max 守卫防双奶，因焦点也在 allies 里） | 4788-4792；模块级 `_th_echo_heal` L410-415 |
| 4 | 统一承伤/治疗落地核心 actor-agnostic（玩家/怪/随从/队友快照同一套） | `_damage_actor` L10138+、`_heal_actor` L5228、`_apply_heal_mods` L5251 |
| 5 | `_is_focus_player` 按 side/引用/allies 成员/enemies 排除识别任意我方 actor | L10055-10080 |
| 6 | 随从阵列通用化（召唤物/宠物/挡刀 guard/auto_act 数据驱动），玩家侧非玩家实体已收编 companions | L9172-9196、L9267-9345；触发点 L3022 |
| 7 | tick 效果 actor 化（eff["actor"] 任意 dict，含 allies 成员被打的 DOT） | L3150-3223 |
| 8 | 副本玩家 ct 各自独立绝对时刻，命令层按 min-ct 多玩家轮转 | instance.py L3167-3179 |

### C. 对 v180F（player+allies+companions → 统一 party actor 数组）的核心提示
1. **真正的单焦点瓶颈不在数据容器（已 actor 化），而在"行动调度/管线入口"**：player_turn 整体是"一个 actor 的回合"；统一 party 后仍需保留"每刻一个行动者 + 引擎外轮转"或引入引擎内多行动者队列。
2. allies 里**混着焦点本人**（instance.py 传全存活成员）→ 统一数组时注意去重/rank 归属，勿把焦点算两份（现状靠 hp<max 守卫掩盖）。
3. `_load_player_state` 式"换焦点"应退化为"显式 actor 参数"——目前所有隐式焦点读（_p_*、_player_stats 内 4115-4141、_add_shield 3374）是重构时最易漏改的暗雷。

---

**交付物**：仅本审计报告，未改动任何文件（只读侦察）。无遗留问题；所有结论均基于实际代码行验证。