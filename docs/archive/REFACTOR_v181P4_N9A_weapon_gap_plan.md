# battle2 N9A：weapon 缺口 6 key 完整方案（death_dance / randuin / ice_vein / dodge / combo 系）

> 2026-09-08 鱼鱼拍板流程：**缺口完整方案先列出来看，不做不行**；三个架构讨论点
> （enemy_act 阵营语义 / dodge 暂缓时机 / combo 归属）需鱼鱼拍板后再动工。
> 分支 wt_ebuffs（worktree df_wt_ebuffs/w1）。基线：battle2 全套 433/433 绿。

---

## 0. 缺口盘点修正（HANDOFF §3.A 的 10 key → 真缺口 6）

| key | HANDOFF 归类 | 实测结论 |
|---|---|---|
| vital_band / holy_radiance_mail / echo_band / novice_regen_heal | 缺口 | ❌ **非缺口**：proc_heal amp 4 key 走 `apply_to_actor` 被动装配（state.heal_amp_pct），实测 vital_band(0.15)+holy_radiance_mail(0.20) 叠算 = 0.32 ✓ 已生效 |
| death_dance | 缓伤池 | ✅ 可全做（引擎无缺口，扩展动作即可） |
| randuin_weary / ice_vein | enemy_act 事件 | ⚠️ 引擎加事件点，**需鱼鱼拍板阵营语义**（见 §2） |
| novice_first_turn_dodge | 闪避 | ⚠️ battle2 无命中 roll，**需拍板时机**（见 §3） |
| novice_hunt_combo / combo_end | 连击/连段 | ⚠️ 职业机制级，**需拍板归属**（见 §4） |

---

## 1. death_dance 缓伤池（✅ 可直接做）

### 1.1 旧语义（battle.py 10938-10961 + _we_executors 871-895，已逐句读）
```
battle_start  : eff[we_death_pool] = float(现值 or 0)     # 惰性建键（防缺键）
受击（_post_hp_lethal）: eff[we_death_pool] += dmg × 0.35   # 表 pool_pct 权威
turn_start    : pool>0 → pay = max(1, int(pool × 0.10))     # 表 pay_pct 权威
                hp = max(0, hp - pay); pool = max(0, pool - pay)
                日志 "💀 死亡之舞：缓伤池结算，损失 {pay} 点生命！（剩余 {pool:.0f}）"
```
数据：`{family: proc_special, pool_pct: 0.35, pay_pct: 0.10, max_turns: 10, pool_key: we_death_pool}`

### 1.2 battle2 落点（全走现成事件点，引擎零改动）
| 旧时机 | battle2 事件点 | ctx 可用 |
|---|---|---|
| battle_start | `battle_start`（已插桩 battle.py:318） | 无 dmg，只初始化池 |
| 受击收池 | `on_taken`（已插桩 landing.py:77，**dmg 实伤在 ctx**） | ctx.dmg = 承伤实值 |
| turn_start 扣池 | `turn_start`（已插桩 battle.py:243） | 行动者自己 |

- 装配层加翻译：`death_dance → {"battle_start": [初始化], "on_taken": [收池], "turn_start": [结算]}`，
  事件型 3 个都挂 battle2 事件名直通（map_event 同名）。
- 收池放**扩展动作 `we_death_pool_add`**（读 ctx.dmg × pool_pct，写 actor.eff 池）
  ——因为收池在 `on_taken` 的主体过滤语义下只有承伤者自己声明会执行，声明者=玩家自己=承伤者 ✓。
- 结算放**扩展动作 `we_death_pool_pay`**（turn_start 主体=行动者自己 ✓）。
- 池存哪：actor["eff"][pool_key]（actor.eff 是游戏侧自由扩展区，序列化随 actor 走，
  battle2 serialize 已保留任意 key？需确认——若 serialize 白名单化则补 key）。

### 1.3 对拍测试
- 同输入快照：装 death_dance → 受击 n 次 → 每轮到点扣 pay → 断言 pool/hp 数值与旧公式一致。
- 测试放 tests/test_battle_n9_equip.py（N9 验收文件，加 key 在此补用例）。

### 1.4 语义精度（实现前已核，2026-09-08）
- 旧 `_post_hp_lethal` 每次承伤后都调（battle.py:11330，非仅致死）→ 池每次受击收；
- 收池用 landing on_taken ctx 的 `dmg: real`（盾后实扣值）——与旧版进 _post_hp_lethal
  的 dmg（护盾吸收后剩值）口径一致 ✓；
- 池存 actor.eff（serialize 全量保留除 _skill_index 外所有键 ✓，恢复续战不丢池）。

---

## 2. randuin_weary / ice_vein：通用"行动完成"广播事件（鱼鱼 2026-09-08 拍板方向）

### 2.1 旧语义（weapon_effects.py:389 + _we_executors 134-143）
```
事件：enemy_act（敌方行动完成后，_hostile_phase 3506 行 player 侧 proc）
效果（mode=spd_down_stack）：当前目标敌人 e_buffs[sk] = min(max_stack, +1)
      e_buffs[_spd_down_pct] = max(现值, spd_down_pct × n)   # 乘算减速
日志：🛡️ 兰顿倦意：敌人速度 -X%（n/3 层）  /  ❄️ 冰脉寒流：...
数据：randuin {mode: spd_down_stack, max_stack: 3, spd_down_pct: 0.06, stack_key: _randuin_stack}
      ice_vein {mode: spd_down_stack, max_stack: 3, spd_down_pct: 0.08, stack_key: _ice_vein_stack}
```

### 2.2 鱼鱼拍板方向（2026-09-08）：「事件可以做，但更通用——所有阵营行动都触发，
自己 if 判断是不是敌对阵营就行」

### 2.3 设计定稿：通用广播事件 `act_done`（非专用 enemy_act）
- **事件名**：`act_done`（行动完成；与现有 act_begin/act_cast 命名族一致，语义中立）。
  旧装配映射 enemy_act → act_done 由装配层翻译，引擎不出现"敌人"名词。
- **fire 点**：`Battle.act()` 尾部——action 分发执行完成后、胜负判定前插 1 处
  （battle.py 285-287 区间：`_do_attack/_do_skill/_do_defend/_do_flee` 之后）。天然正确：
  - 所有阵营（玩家/怪/随从/PVP 对手）**真实行动完成**都触发；
  - 被控跳过（stun/freeze）早退 return 不触发 ✓（被控不算行动完成，旧 enemy_act 同）；
  - 玩家自己行动也触发 → 玩家若挂了"行动完成"监听，扩展动作 if 敌对判断自然不误伤自己。
- **ctx 形态**：`fire("act_done", {"acted": actor}, logs)` —— **不带 `actor` 键**！
  原因：fire 主体过滤看 ctx.actor，带 actor 键 = 只有行动者自己能响应（旁观者被拦截，
  正是 N9.6 修的事）。不带 actor 键 → subject=None → 走 battle_start 同款**全员广播**：
  每个存活 actor 查自己 `triggers["act_done"]`。刚行动的 actor 放 `ctx["acted"]`
  （暂存进 battle._fire_ctx，扩展动作读）。
- **敌我判断在效果侧**：randuin/ice_vein 装配成扩展动作 we_spd_down_stack 挂
  `triggers["act_done"]`；执行器内读 ctx["acted"] → `hostile_sides(battle, 自己.side)`
  包含 acted.side → 才给 acted 叠减速层。判断代码在装配层（游戏侧），引擎零知识。
- **事件全集**：EVENTS 加 "act_done"（21 → 22）。

### 2.4 通用性收益（为什么比专用 enemy_act 好）
| 场景 | 专用 enemy_act | act_done 通用广播 |
|---|---|---|
| randuin/ice_vein 敌行动减速 | 支持 | 支持（效果侧 if hostile） |
| 未来"友方行动后我加 buff" | 不支持（需再加事件） | 支持（if ally） |
| 未来"任何人行动计数/层数" | 不支持 | 支持 |
| 引擎改动 | 事件 + 特判广播规则 | 一个通用广播事件 + 插桩 1 处 |
| 北极星"引擎零身份" | 事件名带敌意倾向 | 事件名中立 ✓ |

### 2.5 语义差异说明（vs 旧版，需鱼鱼知晓）
- 旧版：敌方**整轮**行动完 → 叠给"当前锁定目标"（_hit_tgt，e_buffs 共享单怪遗留）。
- 新版：**每个敌对 actor 各自行动完** → 叠给"行动的那只"（actor 自己的 buffs）。
  单体怪战斗零差异；多怪战斗更合理（谁动谁被叠，且绕开 e_buffs 共享串扰 bug——
  该 bug 本就是 P3 要收口的古王内战根因）。按 battle2 actor 语义这是正确行为，非陪葬旧 bug。

### 2.6 引擎改动清单
1. `effect_triggers.py` EVENTS 加 "act_done"（22 个，单行定义保 cov 行 trace）；
2. `battle.py act()` action 分发后插 `fire("act_done", {"acted": actor}, logs)` 1 处；
   （被控 skip 早退路径不触发；行动结束已含攻击/技能/防御/逃跑）
3. 无 fire 过滤逻辑改动——复用 battle_start 无主体广播语义（subject=None 全员查声明）。
4. 装配层：map_event 加 "enemy_act" → ("act_done",)；randuin/ice_vein 翻译器挂
   act_done + we_spd_down_stack 扩展动作（mode 分派已有骨架，新注册一个敌对判断执行器）。

---

## 3. novice_first_turn_dodge：闪避体系时机（⚠️ 鱼鱼拍板点 2）

### 3.1 旧语义
```
battle_start : eff[novice_dodge_active]=True（每场首刻标记）
受击闪避判定（_roll_dodge battle.py:10341-10372 全链）：
  dodge = min(面板dodge, 0.40) × 乘算合并（dodge_up buff 0.40 / 无声被动 0.30 /
           影步药剂 0.15 / 远行首刻 0.05）→ ×(1-精准) → roll → 命中/闪避
```
数据：`{family: proc_special, dodge_pct: 0.05, mark_key: novice_dodge_active}`

### 3.2 为什么 battle2 不能只做这一个 key
battle2 **整个命中/闪避判定不存在**：landing.deal_damage 直接结算，无 miss roll。
闪避不是单 key 效果，是战斗系统级能力（面板 dodge 折算、精准削减、40% cap、多源乘算
合并、命中日志二选一）。只给 novice_first_turn_dodge 开洞 = 引擎为单 key 造半套系统。

### 3.3 建议时机（回答"暂缓到什么时候"）
**建议：N10 删旧前最后一个战斗系统批次做，与命令层 N5b-4 切换后真实玩家回归同批。**
理由：
1. 闪避牵动 landing 全伤害路径，晚做一次性插桩最干净（不必为兼容返工）；
2. 旧引擎闪避全链语义（含 dodge_up/无声被动/药水多源合并 + 精准削减）要整批搬，
   需要 behavior snapshot 对拍——现在 N9 weapon 都还没收完，对拍样本不足；
3. 命令层切完（N5b-4）才有真实玩家路径，可对照"被打不闪避"的实感差异。
前提：dodge stat 已在 battle2 面板（actors.py:98 stats.dodge 已折算），无需数据层改动。
若鱼鱼想更早：可在 N9A 收尾后单独开一个"N9B 战斗判定补全（命中/闪避/精准）"批次。

---

## 4. novice_hunt_combo / combo_end：连击系统归属（⚠️ 鱼鱼拍板点 3）

### 4.1 旧语义（_we_executors 388-395 + 440-441 + battle.py 2586-2631）
```
novice_hunt_combo（猎影之牙，武器）：暴击命中 → stacks[novice_combo]+1（cap 5）
     每层连击率 +8%——消费点在 battle 连击判定（直读 stacks，非本执行器）
combo_end（夜枭双匕，武器）：hit 命中且 _combo_active(player)=真（影舞者攻线判定）
     → eff[we_combo_end]=crit_dmg 0.4 标记；被动暴击消费 crit_dmg 加法并清标
_combo_active = class_name==刺客 && path==攻线（职业机制，数据化 _MC['assassin_combo']）
```

### 4.2 判断：职业机制级，但武器效果本体可分两半
- 一半（**叠层/标记生产**）：hunt_combo = 暴击叠层（crit 事件 state_add，引擎可做）；
  combo_end = "连段活跃时命中置标记" —— 依赖 **连段活跃状态**，battle2 无连段系统。
- 一半（**消费**）：连击率（追加普攻概率）/ 连段判定 —— 属职业机制（刺客攻线/拳师），
  北极星红线"职业机制不进引擎" → 上层职业模块（现状未建）。

### 4.3 方案选项
**方案 A（推荐）：等上层职业模块（影舞者攻线重建）时一起做，本轮记缺口**
- 引擎不为"连段活跃"造概念；battle2 现无刺客职业模块 → 装配了也没消费端，等于半迁。
- 缺口的触发条件写清楚，职业模块方案（N5b-4 后）直接引用本清单。
- 武器数据侧无改动（等职业模块建时再挂）。

**方案 B：本轮先做 hunt_combo 的"暴击叠层"生产段（state_add），combo_end 记缺口**
- 好处：hunt_combo 半套先通（叠层可见，未来消费段接职业模块）。
- 坏处：北极星"不留半迁/不留兼容壳"——叠了没消费 = 玩家看到层数但无效果，违背铁律。

**方案 C：battle2 直接建连击系统**（引擎级 combo count/break/消费）
- 违背"职业机制不进引擎"（连击是职业分支玩法不是引擎动词）→ 不推荐。

### 4.4 建议
选 A。这 2 key 挂"上层职业模块依赖"清单，和 §2 randuin/ice_vein 的"引擎事件缺失"
分开记（一个是等引擎事件，一个是等职业模块）。N10 删旧前核对清单：凡能力未覆盖的
key 一律**先不删对应旧族执行器**（death_dance_armor 复活段同理——注意它 N9.12 已迁
undying_will 但 death_dance_armor 的"致死复活"段是否已覆盖需复核）。

---

## 5. 开工顺序（拍板后）

| 序 | 批次 | 内容 | 前置 |
|---|---|---|---|
| 1 | N9A-1 | death_dance 缓伤池（方案 §1） | 无，可直接做 |
| 2 | N9A-2 | act_done 广播事件 + randuin/ice_vein（方案 §2 定稿） | 鱼鱼确认设计 |
| 3 | N9A-3 | 闪避体系批次（方案 §3 时机） | 鱼鱼拍板时机 |
| 4 | — | hunt_combo/combo_end 记缺口等职业模块（方案 §4 选 A 时） | 鱼鱼拍板归属 |
| 5 | N9.7 | affix 76 迁移（stat 41 面板已含 + 事件型 ~35） | N9A 或并行 |

**2026-09-08 鱼鱼拍板记录：**
- enemy_act 事件：✅ 可做，但**改通用 act_done 广播**（全员触发，效果侧 if 敌我判断）——已定稿 §2
- death_dance：✅ 做（"肯定不能放着不做"）
- 待拍板：dodge 时机（§3 建议命令层切换后同批）、combo 归属（§4 建议等职业模块）

每批：改前 git status 干净 → 实现 + 测试补用例 → 全套 433 绿 → commit v181.N9A.X → 汇报鱼鱼。
