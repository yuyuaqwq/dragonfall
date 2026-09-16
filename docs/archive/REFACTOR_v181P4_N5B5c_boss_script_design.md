# REFACTOR_v181P4_N5B5c：副本 Boss 剧本"导演"设计（mech DSL 执行器 battle2 化）

> 状态：待鱼鱼审查（2026-09-09）
> 前置：R3 删除完成 + R4 验证网绿 + 5b G1/G2/收尾完成（HEAD 84f18d8+）
> 相关：docs/archive/REFACTOR_v181P4_N5B5_instance_gap_design.md §2 G3（本设计是其细化）
> 铁律：引擎零游戏知识——导演在命令层，只调引擎动词/事件/注入钩子；旧 battle_mech.py
> （2156 行，N10 删除对象）是**语义参考**，不是代码蓝本，不许搬结构。

---

## 0. 目标与范围

**目标**：副本/世界 Boss 的 Boss 剧本（v178 身份技）在 battle2 下完整可表达、可触发、可验证。
**范围**：27 张副本 Boss 机制卡（04 章二.5 机制分配表）+ 世界 Boss（外域 6 只）同导演通用。
**非目标**（标注依赖，不硬塞）：
- 普通怪多段 AI（ai.skill_chance/weights 概率轮换）→ 属上层"怪 AI 模块"，本批只做
  **确定性剧本**（阈值/时刻/条件触发），weights 轮换留接口不入实现。
- 数值/文案调整：27 张卡的机制数值、演出文案一字不动（纯内容翻译）。

## 1. 现状盘点：旧语义 → battle2 差距（数据权威 = 策划案 04 章二.5 + 27 章）

### 1.1 数据面（三层配置，**全部不动**）

| 层 | 文件 | 剧本内容 | 规模 |
|---|---|---|---|
| 怪定义 | game/data/monster_mods.py MONSTER_MODS | boss 条目 mech token + phases/opening/triggers/ai/on_interrupt/on_minion_died/chains/target_policy | 30 boss；27 带 phases、17 带 opening、21 带 ai、19 带 on_interrupt、8 带 triggers、7 带 on_minion_died、5 带 chains |
| 副本内联 | game/data/instances.py INSTANCES | inst 级 mech/phases/opening/chains（v178 E1/E2：与 MONSTER_MODS 合并去重，非覆盖） | 54 inst；22 mech、20 phases、1 opening、1 chains |
| 阶段模板 | game/data/boss_phases.py BOSS_PHASE_TEMPLATES | phase_id → merge_phase_config 模板（preserve_debuffs/ult_every/freq_mult/exit_turns/counter） | phase_id 条目（复用旧 merge 函数） |

**量级结论**：27 Boss phases 条目 = 67 条（2-5 条/Boss）；mech token 组合分布 =
phase×31、summon×20、enrage×10、phase_open×10、stacks×4、heal×4、player_low×3、
shield×2、reflect×1（含副本内联）。**内容翻译总量 ≈ 27 张 Boss 卡 + 6 世界 Boss**。

### 1.2 旧引擎消费点（语义参考，N10 删）

| 机制 | 旧消费 | 语义要点（battle_mech.py/battle.py） |
|---|---|---|
| phase 转阶段 | `_b_phase`（battle_mech:698） | 血量 < phases[pc].min（缺省 0.5^n）→ phase_count+1；演出 script.name/icon；add_skills 幂等 append；旧行为 atk/matk +20%；阶段演出刻不行动（battle._phase_skip_act）；阈值预告（pc>0 时接近下一阈值 +3% 内提前 warn once）；转阶段异常保留 50%（preserve_debuffs 默认 True）或净化 |
| stacks 叠层 | `_b_stacks`（:782） | 每 2 刻 +1 层（上限 5），atk 随层 |
| phase_open 开场技 | `_b_opening`（:800） | 战斗第一刻 once；opening{name,effect,power} → atk_up/atk_up_strong/mon_atk_down/mortal_wound |
| player_low | `_b_player_low`（:832） | 玩家 HP<30%（triggers.player_low.hp 可配）→ 杀意文案 + 本刻攻击加成；once 或 cooldown=N 刻 |
| pv_broken 反扑 | battle.py:7636 | 玩家本刻用过技能 → Boss 追加普攻 |
| summon 召唤 | `_b_summon`（:651） | CD 5 刻、单次 1 只、场上援军上限 3（含开怪爪牙）；v163：召唤物 = 该副本怪池同等级普通怪模板（build_monster），不从 Boss 比例缩放 |
| heal/shield/enrage/reflect | `_b_heal/_b_shield/_b_enrage` 等 | heal 每 4 刻 8%；shield 开场 20% 盾+受伤 -50%；enrage 血<30% atk+35%（一次）；reflect 血<25% 反弹 15% |
| chains 连招链 | battle.py 读 chains | seq 技能序列 + cd + break（血量阈值断链转阶段） |
| on_interrupt | battle.py | 读条被打断 → effect（freeze_self 等） |
| on_minion_died | battle.py | 爪牙死亡 → Boss 联动（stacks_clear/回血等） |
| 引擎原语九件套 | 04 章:119-121 | phases 四件套(ult_every/freq_mult/exit_turns/counter)、chains、on_interrupt、on_minion_died、element_immune/weak、defend_reduce、pdot |

### 1.3 battle2 现状（可用能力盘点）

| 能力 | 现状 | 出处 |
|---|---|---|
| 注入钩子三件套 | Battle.__init__ 支持 target_picker/on_event/action_override（构造传参；from_state 后命令层重挂 _attach_instance_hooks） | battle2/battle.py:30-54 |
| 事件总线 | EVENTS 全集 22 事件；引擎自然插桩 act_* 系；**phase/player_low/pv_broken 已声明协议名但无插桩点**（5c 导演补触发） | effect_triggers.py:48 |
| 怪行动 | actor_auto 读 actor.auto_act（act.type/skill），缺省普攻；target_picker 可注入选目标 | battle.py:222 |
| 怪技能池 | monster_to_actor 透传 skills/learned_skills（actor.skills 可被 add_skills 扩展） | bridge.py:143 |
| 增益表达 | actor.effects + EFFECT_RULES（stat_scale 叠层/panel）；actor.stat_bonus 通用面板容器 | effects.py/stats.py |
| 承伤乘区 | target._dmg_taken_mult >1 生效（vulnerable） | landing.py:50 |
| sides 扩展 | 死亡 actor 不移除（只进 killed）；召唤 = 命令层 append actor 进 sides（st 同容器同步） | gap design §4 映射表 |
| 计数器 | CTB 绝对时刻 _now；无全局 round 号 → 剧本"每 N 刻"计数器需导演自建（st 持久化） | schedule.py |

## 2. 导演架构（game/commands/boss_script.py 新建，命令层）

### 2.1 职责边界（铁律）

```
┌─ 引擎（battle2）────────────────────────────┐
│  动词执行器 + EVENTS 插桩 + 注入钩子（三件套）    │
│  零游戏知识：不认识 phase/summon/enrage 名词      │
└──────────────▲───────────────────────────┘
               │ 注入：script_hook（构造参数，同 target_picker 同款）
┌──────────────┴───────────────────────────┐
│  导演 boss_script.py（命令层）                │
│  读配置（MONSTER_MODS/INSTANCES/模板 merge） │
│  查条件（血量%/刻计数/玩家状态）→ 决定触发       │
│  执行动作 = 只调引擎动词/事件/改 auto_act/append │
│  状态 st["boss_script"]（随 st 持久化）        │
└───────────────────────────────────────────┘
```

**核心取舍**：剧本触发检查放在**命令层导演**（每刻 IB.act 入口 + actor_auto 前），
不写进引擎。理由：剧本是"内容翻译"（gap design §2 原判）；导演状态（round 计数、
summon CD、phase_count、once 标记）存 st 顶层随副本持久化，actors 只留引擎效果。

### 2.2 挂点（复用现有注入模式，引擎改动 ≤ 一次性小扩展）

| 挂点 | 时机 | 用途 |
|---|---|---|
| A. IB.act 内 human_act **前**（命令层，零引擎改动） | 每刻玩家行动前 | phase 演出刻"跳过玩家？"不需要；此处做 round_no 维护 + 开战 opening once 判定 |
| B. script_hook（**引擎小扩展**，构造参数第 4 钩子） | actor_auto 怪行动前 | phase 演出刻拦截怪本刻行动（旧 _phase_skip_act 语义）+ 触发剧本动作（换招/增益/召唤/反扑在怪行动帧执行，演出顺序自然） |
| C. on_event 观察者（已有） | act_cast/act_done/on_death 等 | chains 推进（Boss 每出招后推 seq）、on_interrupt（玩家打断 Boss 读条）、on_minion_died（爪牙死亡联动）——这些是**响应型**剧本，走事件观察比轮询干净 |

> B 的实现成本：Battle.__init__ 加 `script_hook=None` 参数 + actor_auto 行动前
> `if self.script_hook: skip = self.script_hook(self, caster, logs); if skip: 推 ct 返回`
> ≈ 10 行 + from_state 透传（script_hook 不可序列化 → 命令层 _attach_instance_hooks
> 重挂，同 target_picker 先例）。**拒绝**把剧本判定写进引擎内部 if 分支。

### 2.3 导演状态（st["boss_script"]，随 st 持久化）

```python
st["boss_script"] = {
  "phase_count": 0,          # 当前阶段序号（0 = 阶段 1）
  "round_no": 0,             # 剧本刻计数（每次玩家/怪行动帧 +1；"每 N 刻"用）
  "summon_cd": 0,            # 召唤冷却计数（满员/未到不加）
  "summoned": [],            # 本场召唤 uid（上限 3 判定 + 死亡回收）
  "flags": {},               # once 标记：_open_played/_phase_warned/pv_broken_cd 等
  "chain_i": 0,              # chains seq 指针
  "chain_cd": 0,
  "cfg_snapshot": {...},     # 触发判定用只读快照（boss id/inst id → 已 merge 配置）
}
```

> 为什么不放 actor：导演状态是"整场剧本进度"（跨多 actor/爪牙联动），且命令层
> 每次 from_state 重建 Battle，actor 只承载引擎效果（V 系列铁律：actors 只留数据+纯读）。

### 2.4 配置解析（boss_script_cfg，移植 v178 E1/E2 语义）

- 输入：boss actor（uid/name/_inst_id）+ st
- 解析顺序：MONSTER_MODS[boss_id] 基准 → 若 _inst_id 命中 INSTANCES 副本条目 →
  phases/opening/triggers/chains 按副本覆盖/合并 → mech token 并集（v178 E2 去重合并）
- phase_id 条目：调 boss_phases.merge_phase_config（旧函数保留复用）得阶段四件套
- 输出：统一 cfg dict（含缺省 key，同 battle.py:7622-7624 缺省语义）

## 3. 剧本事件映射表（翻译目标 —— 每行 = 导演动作 → 引擎动词/命令层操作）

| 旧机制/字段 | 触发条件（导演查） | 导演动作序列（演出文案 + 引擎操作） |
|---|---|---|
| opening/phase_open | 开战第一帧（round_no==0 且未 _open_played） | 演出行 → actor effects 增益（EFFECT_ACTIONS atk_up 类）或 fire("phase_open") 装配层响应 |
| phase 转阶段 | Boss hp/max_hp < cfg.phases[pc].min（缺省 0.5^n）且 pc<3 | ① 阈值预告（pc>0 且 hp 在下一阈值 +3% 内 once）② phase_count+1 ③ 演出 script ④ add_skills → actor.skills append（幂等）+ **同步改 actor.auto_act 主技能** ⑤ atk 乘区（effects stat_scale 或 stat_bonus flat）⑥ preserve_debuffs 语义（转阶段前保留 50% 减益层——effects 容器 stacks 减半）⑦ 返回 skip = 本刻怪不行动（演出刻） |
| enrage | 血 <30%（一次，未 enraged） | 演出 + atk/matk 乘区（+35%，EFFECT_ACTIONS 或 stat_bonus） |
| stacks | round_no % 2 == 0 且 stacks<5 | stacks 叠层（effects 容器 stat_scale 声明，上限 5） |
| heal | round_no % 4 == 0 | landing.heal_actor（8% max_hp） |
| shield | 开战 once | effects shield（20% max）+ 受伤 -50%（dmg_taken_mult 或 shield 减伤声明） |
| reflect | 血 <25%（一次） | actor 挂 reflect 效果（landing 承伤反伤，同被动反伤 thorns 口径） |
| summon | round_no - summon_cd >= 5 且场上援军 <3（含开怪爪牙） | ① build_monster(该副本怪池同等级普通怪模板)（v163 口径）② BR.monster_to_actor → append 进 st["battle"]["sides"]["enemy"]（st 同容器）③ ct 播种（初始 ct = now + 小延迟，不插队当前行动）④ summon_cd = round_no ⑤ Boss atk +20%（短乘区） |
| player_low | 任一存活玩家 hp/max_hp < triggers.player_low.hp（0.3）且冷却到 | 演出 + 本刻 Boss atk 加成（导演帧内 effects 或 script_hook 返回增强标记） |
| pv_broken | 玩家本刻 act_cast（on_event 观察）且冷却到 | 追加一次普攻（导演调 Battle 动词/或怪 actor_auto 后补一帧） |
| chains | on_event act_done：Boss 每行动推 chain_i | seq 轮换：下刻 Boss auto_act.act.skill = seq[chain_i]；cd 刻冷却；break 条件（血量阈值/被打断）→ 退出链 |
| on_interrupt | on_event：玩家打断 Boss 读条动作 | 执行 effect（freeze_self 等，EFFECT_ACTIONS 查表） |
| on_minion_died | on_event on_death：死亡 actor 是 Boss 爪牙 | 执行联动 effect（stacks_clear/Boss 回血等） |
| element_immune/weak | 属"敌方元素克制"声明 | 装配层/技能落地已有元素判定 → 缺口盘点见 §5 P5 |
| defend_reduce / pdot / 形态轮换 | 见 §5 P5 盘点 | 引擎原语缺口 → 独立小批 |

**auto_act 换招细节**：actor_auto 每刻读 actor.auto_act.act（固定技能）。阶段换招 =
导演改写 actor.auto_act = {"act": {"type": "skill", "skill": <新主技能>}}——演员本刻
或下刻生效（script_hook 帧内改 → actor_auto 已读旧值则下刻生效；演出刻 skip 后
下刻自然用新招）。链条轮换同此机制。**这是"怪 AI weights 轮换"缺口的最小确定性子集**。

## 4. 批切方案（每批独立验证 + commit，沿用 N5b 纪律）

| 批 | 内容 | 引擎改动 | 覆盖 | 验证 |
|---|---|---|---|---|
| **P1 导演框架 + phases** | boss_script.py 骨架 + cfg 解析 + script_hook 引擎小扩展 + phase 转阶段（阈值/演出/换招/演出刻 skip/阈值预告） | 小（script_hook ≈10 行 + from_state 透传） | 27 Boss 的 phases 全量可触发（67 条） | 古王（3 阶段）/咕噜（低血酒疯）端到端 + battle2 全套回归 |
| **P2 开场/条件反制** | opening once + player_low + pv_broken + enrage/stacks/heal/shield/reflect 简单机制（EFFECT_ACTIONS 翻译） | 无（导演内部） | 17 opening / 8 triggers / 简单机制 token | 咕噜（掠夺号令+酒疯）完整剧本端到端 |
| **P3 召唤系** | summon sides append（CD/上限/小怪模板/v163 口径）+ Boss atk 联动 | 无 | summon×20 token 覆盖 | 摩罗/哥布林（召唤身份技）端到端：援军上限 3/死亡回收/清场 |
| **P4 链/打断/联动** | chains seq 轮换 + on_interrupt + on_minion_died（on_event 观察者实现） | 无 | chains×5 / on_interrupt×19 / on_minion_died×7 | 试炼骑士长（4 招连招链）/马尔库斯（处刑读条断）端到端 |
| **P5 场景原语盘点** | element_immune/weak、defend_reduce、pdot、形态轮换、phases 四件套（ult_every/freq_mult/exit_turns/counter）逐项盘点：battle2 能表达的走配置翻译；真缺的原语列**独立小批**（引擎小扩展或装配层声明） | 视盘点（预计 ≤2 项小扩展） | 烛影主教（双态轮替）/蚀夜（三形态）等场地/形态族 | 对应 Boss 端到端 |

> 预计顺序 P1→P4 是主线（27 卡绝大多数 = phases/opening/summon/chains 组合），
> P5 是少数身份技（烛影/蚀夜/云中圣者等）的收尾。**建议 P1 先做**（骨架 + 最大
> 覆盖），P1 落地即"导演可用了"，后续批都是内容翻译增量。

## 5. 引擎改动清单（目标：≤2 处小扩展，全部可回落）

| 改动 | 内容 | 位置 | 回落 |
|---|---|---|---|
| script_hook | Battle.__init__ 参数 + actor_auto 行动前调用（返回 True 拦截本刻） | battle2/battle.py | 无参数 → 不调用（默认 None）✓ |
| （待 P5 盘点） | element 免疫/defend_reduce 等若有真缺口 → 独立评估 | 待定 | — |

**明确不做**：剧本判定不进引擎内部；不新增 EVENTS 插桩点（phase/player_low/
pv_broken 协议名已留，导演负责 fire 或直接动作）；actor 不加 game 字段。

## 6. 验证策略

1. **Boss 剧本端到端测试**（test_boss_script_p1.py 起，每批新增）：真实副本数据
   （INSTANCES/MONSTER_MODS 原样）→ build_battle → 按 next_actor_key 轮流驱动 →
   断言：阈值触发阶段（hp 压线检查 phase_count/演出文案/auto_act 换招）、召唤上限、
   链条轮换、on_interrupt 联动。**伤害随机性断言**沿用波动区间/乘区直调先例。
2. **router 端到端**：真人副本（如 v137 哥布林营地）完整 Boss 战走剧本，验证
   footer/轮转/死亡同步与剧本共存（5b test_15 扩展场景）。
3. **全量回归**：335 = 310/25 基线逐条对照，零新增（每批跑）。
4. **数值门禁**：scripts/run_numeric_tests.py 全绿才能提交（atk_mult/召唤涉及数值）。
5. 纪律：每批 commit + push origin/wt_ebuffs；HANDOFF §9.x 逐批记录。

## 7. 风险与边界（动手前必知）

- **演出刻 skip 语义**：battle2 无全局"本刻"概念——script_hook 返回 skip 时
  actor_auto 内推 ct 但不执行动作（行动浪费），与旧 _phase_skip_act 对齐。
- **召唤 append 与 to_state**：append 后 to_state 序列化全量 sides ✓；CT 播种须
  > 当前 _now（防插队）；死亡援军不移除（引擎 killed 账）→ 导演按 uid 判存活计数。
- **preserve_debuffs 50%**：V 系列 effects 容器 stacks 减半（先例：v138.2 律三
  进度遗产）。全清变体 = 移除 effects 负面条目。**语义坑**：旧"debuffs 键"在
  V 系列 = effects 容器声明条目，盘点时逐条对 EFFECT_RULES cleanse 语义。
- **阶段换招与技能索引**：actor.skills append 新技能后，Battle._index_skills 只在
  构造时跑 → 导演帧内改 skills/auto_act 需同步刷新技能索引（或 actor.auto_act 直接
  引用技能名由 act 时查表——验证 P1 时定，倾向后者零引擎改动）。
- **世界 Boss 共存**：外域世界 Boss（全局血量同步）走同导演——验证 P4 后补 1 例；
  与"世界Boss DOT 语义未决点（路线 B）"正交，不受影响。
- **怪 AI weights 缺口**：ai.skill_chance/weights（21 Boss 带 ai）不在本批——
  导演先做确定性剧本；weights 轮换标注"上层怪 AI 模块"依赖（与 weapon/affix 同列）。
- **文案/数值冻结**：翻译过程不改 27 卡机制数值与文案；若发现数据与代码脱钩
  （如 2026-09-07 audit 的 P0 类），单独列问题给鱼鱼，不顺手改。

## 8. 内容翻译工作量粗估

| 族 | 代表 Boss | 导演复杂度 |
|---|---|---|
| 打断博弈 | 咕噜/杰克/赫尔嘉/马尔库斯/歌澜/赫尔加/黑渊/云怒 | P1+P2+P4（召唤/低血/读条断） |
| 叠层管理 | 轰鸣/克罗/冰霜/黑渊/摩罗/奥姆 | P1+P2+P3（stacks/phase） |
| 转火优先级 | 古王/蓝歌/石炉/月神守卫 | P1+P3（多目标 phases/召唤） |
| 场地时间轴 | 磐涡/晨曦/澜歌/敖澜/摩罗 | P1+P5（pdot/周期） |
| 形态轮换 | 烛影/蚀夜/云中圣者/蓝歌 | P1+P5（element/defend_reduce） |
| 读招防反 | 骑士长/马尔库斯/黑渊 | P4（chains/on_interrupt） |

→ P1-P4 估覆盖 ~24/27 卡；P5 收 3-4 张场地/形态卡 + 引擎原语盘点。

---

## 附：本设计已核实的事实（侦查记录）

- EVENTS 协议名 phase/player_low/pv_broken 已在 effect_triggers.py:48 声明但无引擎
  插桩 → 5c 导演是它们的首个触发方（fire 或直接动作，P1 定）。
- Battle.__init__ 三件套注入模式（target_picker/on_event/action_override）已有
  （battle.py:30-54）；script_hook 照此加第 4 钩子。
- 副本 Boss 携带 _inst_id（v178 E1，instance.py:938）供 cfg 按副本解析；mech 合并
  去重语义（E2，instance.py:939-950）移植进 boss_script_cfg。
- MONSTER_MODS 30 boss 统计：27 phases / 17 opening / 21 ai / 19 on_interrupt /
  8 triggers / 7 on_minion_died / 5 chains / 3 target_policy。
- instances.py 内联：54 inst、22 mech、20 phases、1 opening、1 chains。
- battle2 无全局 round 号（CTB 绝对时刻）→ 导演 round_no 自维护（st 持久化）。
