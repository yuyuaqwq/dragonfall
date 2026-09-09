# battle2 效果系统 v2 交接（N8/N9 阶段）——开新会话必读

> 2026-09-08 交接。主线 = 效果系统 v2 + 装备特效族化迁移（wt_ebuffs 分支）。
> 🔴 **队列最新状态（2026-09-08 会话尾）**：效果容器统一（V 系列）拍板插队，
> 排在 I3-I7 之前。方案 `docs/REFACTOR_v181P4_EFFECTS_UNIFY_design.md`。
> 鱼鱼验收北极星：**最后清干净——N10 删旧 battle.py + 旧效果系统三套注册表，
> 不留兼容壳/开关/兜底参数**（鱼鱼原话："老的一定要确保删掉，最后不留东西"）。
> 会话重启口令：「继续 effects 统一，读 docs/REFACTOR_v181P4_EFFECTS_UNIFY_design.md
> 从 V1 开始」

---

## 0. 分支/位置/跑法

- 分支：`wt_ebuffs`（worktree：`C:/Users/yuyu/AppData/Local/Temp/df_wt_ebuffs/w1`）
- HEAD：`（N5b4-4 PVP 切 battle2 后）`（v181.N5b4.4，2026-09-08）
- 主仓（生产）：`C:/Users/yuyu/qqbot/data/plugins/dragonfall`（master 未动）
- Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`
- 全套测试：`for f in tests/test_battle2_*.py; do python "$f"; done`（当前 16 文件 541 断言全绿）
- 覆盖率门禁：`python tools/cov_func_battle2.py`（0 未调用）+ `cov_branch_battle2.py`
- 效果系统主方案：`docs/DESIGN_effect_system_v2.md`（Part 3.3/4 定稿 19 时机 + 管线）
- N9 施工方案：`docs/REFACTOR_v181P4_N9_migration.md`（盘点/批次/删除清单）
- N9A 缺口方案：`docs/REFACTOR_v181P4_N9A_weapon_gap_plan.md`（weapon 缺口设计）
- N9.7 affix 方案：`docs/REFACTOR_v181P4_N9_7_affix_migration.md`（分档 + 进度）
- **N5b-4 命令层切换详细设计（下一步主工程，字段/函数级施工图）**：
  `docs/REFACTOR_v181P4_N5B4_command_switch.md`
- 旧三套注册表数据权威：`game/data/weapon_effect_data.py`（79 key）、
  `game/data/affixes.py`（76 词条）

---

## 0.5 鱼鱼 2026-09-08 拍板记录（本会话新增）

1. **enemy_act → 通用 act_done 广播事件**（鱼鱼拍板"事件可以做，但更通用——
   所有阵营行动都触发，自己 if 判断敌我"）：EVENTS +act_done、Battle.act() 尾部
   fire({"acted": actor}) 全员广播、randuin/ice_vein 效果侧 hostile_sides 判敌我。
   语义差异：旧"整轮后叠给锁定目标"→ 新"谁行动叠谁"（多怪更合理，绕 e_buffs bug）。
2. **weapon 缺口清单"肯定不能放着不做"**：先出方案文档再实施（非闷头做）。
3. **affix 76 分档**：不是全迁——资源型 20 + 职业机制 12 归上层职业模块缺口。
4. **N5b-4 命令层切换**：鱼鱼要看详细设计文档（字段/函数级）再动工；
   核心战斗文件 diff 鱼鱼过目再提交。
5. **（2026-09-08 后续会话）trinity thunder 段补齐 + death_dance_armor 复活段复核**：
   - trinity thunder：文案承诺"附雷 15% atk"旧引擎置标空转永不消费（ctx.attack 门
     恒 False bug）→ battle2 按文案兑现：hit 子键 bonus_atk_pct（引擎 actions.py
     N9.8 通用附伤参数）+ 装配翻译器 _translate_trinity 双段。weapon 73/79。
   - death_dance_armor 复活段：**复核结论 = 旧引擎从未实现**（全 battle.py 复活链族
     只有 phoenix/death_pact/berserk/stance 4 条，无 death_dance_armor 消费点；
     revive_hp_pct 0.12 是数据孤儿，装备文案比实现多写了复活）→ battle2 现状
     （taken_calc 减伤 8%）已与旧引擎行为等价，不算丢能力。复活段**不单开引擎原语**
     （单 key 造半套"死后复活"违背北极星，同闪避体系判断），记 N10 文案清单：
     玩家可见 special 文案含复活承诺但旧引擎从未生效，N10 前改文案或确认不要。
6. **（2026-09-08 N5b4 批）命令层切 battle2 进度：N5b4-1/2/3 完成（0c1a5c6/fe0b3a8/207e741）**
   - N5b4-1 展示层：_status_line/_resource_line/_battle_formation_panel 改读
     player dict + b.sides（双引擎通用，纯读先切）+ _buff_left_ticks 双形态折算
   - N5b4-2 野外/野王/普通遇怪构造 + attack/skill/defend/flee 行动切 battle2
     （_open_battle2 四步仪式 / _restore_battle2 / _sync_battle_player；旧档清档重开）
   - N5b4-3 世界Boss 切 battle2：构造 sides+auto_act；**退役全局 debuffs/adapt 共享 +
     每4次强制 DOT 结算补丁**（鱼鱼拍板按新引擎语义：本地 actor.state DOT + schedule
     自动跳）；_monster_display_name 兼容 sides
   - 🔴 **未决设计点（鱼鱼 2026-09-08 会话尾提出，先保留现状待拍板）**：
     世界Boss DOT 挂载语义——battle2 毒挂在**玩家各自本地副本的 enemy actor**（私有），
     不跟 Boss 真身（gboss.enemies）共享；旧引擎是 gboss.debuffs 全局单份 + 每 N 次
     行动统一结算。鱼鱼原话质疑："DOT 应该是挂在目标 actor 身上的吧？为什么会跟玩家
     强关联"。两条路：A 毒层回全局共享（对齐旧玩法语义，需防多玩家轮流刷毒伤）、
     B 接受"Boss 独立镜像"语义（当前实现，血量共享/贡献独立/DOT 个人输出）。
     **鱼鱼拍板：先保留现状（路线 B），新会话再议。**
7. **（2026-09-08 N5b4-4）PVP 切 battle2（本 commit）**
   - 实现见 §3C；测试 tests/test_battle2_n5b4_pvp.py（29 断言：发起/轮流/胜负/防御/
     skill/超时/旧档清档）。全套 battle2 16 文件 541 断言绿。
   - 🔴 ~~新缺口（待鱼鱼拍板）PVP title_bonus 对称置空~~ → **✅ 鱼鱼拍板方案 A 已实施
     （2026-09-08）**：battle2/stats.py `_player_base_stats` 改 actor 自带 stat_bonus
     优先、缺省回落 battle.title_bonus（野外零变化）；PVP 双方各自增幅塞 actor 随盘。
   - ✅ **再拍板：通用容器正名 stat_bonus（新增纯数值增幅系统不改引擎）**：
     `core/title_bonus.py → core/stat_bonus.py`，聚合函数 `stat_bonus()` = 外部面板
     数值增幅聚合器（称号 TITLES + 成就 ACHIEVEMENTS + 收藏册 + 未来挂件/时装等纯
     flat 来源只在这里加一路）。actor 容器字段 `title_bonus → stat_bonus`；全开战
     路径（_open_battle2 野外/约战/塔、世界Boss 玩家侧、PVP）都塞 actor["stat_bonus"]，
     battle.title_bonus 仅兜底（N10 收）。机制型效果不走这（走装配层 triggers）。
     冻结区保留：命令层 _title_bonus 方法名 / rule hooks 键 / engine.player_final_stats
     第 7 参数名（N10 删旧引擎时收敛）。
   - 附注（引擎行为确认，命令层已兜底不崩）：battle2 的 DOT/时间结算路径（schedule
     _advance_time/_settle_time_effects）致死**不触发 _check_side_end**（result 不置位），
     只在 act() 尾部/actor_auto 后置——PVP 命令层胜负判定已改为**按 actor 存活**（不依赖
     result，防守方视角 result 本身要翻转），慢杀/毒跳死场景正常收尾。
   8. **（2026-09-08 N5b4-5 重写路线拍板）** 鱼鱼两次纠正："别在老引擎上改动、重新写"
   → 副本战斗 = battle2 原生**行动命令层全重写**：新 InstanceBattle 层接管副本行动
   入口（战斗执行/轮转/结算全新代码），instance.py 战斗路由停用不手术、纯玩法壳
   保留。已落地：5a v2 施工图（49def5d）+ 控制器骨架 instance_battle.py（e8e62e8，
   build_battle/act/sync_views/next_actor_key，17 断言）。**v3 执行蓝图（本会话最后
   产出）**：docs/REFACTOR_v181P4_N5B5a_instance_mainline.md——命令注册约束（同名
   『攻击』无法共存→CombatCmds 仅 4 处接线点改调用目标）、instance_router 新文件
   职责、instance.py 删除清单、R1-R5 分步。**新会话口令：「继续 N5b4-5a v3，读
   docs/REFACTOR_v181P4_N5B5a_instance_mainline.md（v3）+ 本节，从 R1 开始」**

9. **（2026-09-08 N5b4-5a 执行会话：R1/R2 完成 + use_item 链设计文档）**
   - **R1 完成（db70ce1）**：新 `game/commands/instance_router.py`
     （InstanceCmds 继承挂载，v3 §4.1-4.5 全逻辑）——入口守卫（大陆权威
     st/肃清引导/轮转+超时自动防御）/行动（IB.act+sync_views）/账务薄壳/
     结算全重写（守卫宝箱/rooms Boss 通关/切怪 build_battle 重构造/层清/
     victory/失败同归）/死亡账 diff→_last_killed。**顺手修骨架 bug**：
     instance_battle.act 行动者要从 from_state 副本 sides 找（原 st 旧 dict
     → 引擎修改不落回，ct/defending 全丢）。测试 28 断言。
   - **R2 完成（aa7384e）**：CombatCmds attack/skill/defend 3 处 instance
     分流 → `_instance_router`（flee 保留锁场不可逃）；instance_battle.act
     补目标解析（None/actor dict/字符串敌名/aN 编号——battle2 引擎只吃
     actor dict）。接线冒烟测试（db 行真实写入）33 断言。
   - **引擎 action_override（f0199d6）**：鱼鱼拍板"通用行动驱动回调——
     告诉引擎做一次行动+耗时，回调写功能"。Battle 加 `action_override`
     注入点（同 target_picker/on_event 先例）：非内置 action（use_item）
     → 回调 (battle, action, actor, payload, target)->(logs, cast)；
     cast=str 内置基准或数字秒；consumed 才推 ct+advance。引擎零名词。
   - 🔴 **use_item 道具链设计（新会话执行蓝图）**：
     docs/REFACTOR_v181P4_N5B5a_use_item_design.md——economy use_item
     （副本 5895 / 普通 5909）在 R2/N5b4-2 后**已静默坏**（state battle2 化
     但走旧 BT.from_state→enemy={}），R3 删 `_instance_act` 前必须处理。
     方案：翻译器 battle2_item_use（payload→actor）+ schedule hot 周期恢复
     基建 + economy 分流切 router + purify 改翻译器；机制型 special
     （summon/trap/phoenix/morph/invuln 等）明确提示不扣道具列缺口。
     **新会话口令：「读 docs/REFACTOR_v181P4_N5B5a_use_item_design.md，
     从 I1 开始（先做 hot 基建）→ I2-I5 → 回 R3」**
   - 未做：R3 删除清单 / footer、world.py 两处 CT helpers 残留（依赖
     _instance_ct_queue/_instance_next_player_name，删 helpers 前要改读
     battle state）/ R4 端到端 / R5 HANDOFF。

10. **（2026-09-08 会话尾）🔴 效果容器统一（V 系列）拍板——插队排期**：
  鱼鱼连续质疑 I1 hot 设计：「DOT/HOT 本质同构能否合并 / state 是否不够通用 /
  能不能基于 buff/state 实现」。深挖结论：**引擎现状 4 个效果容器
  （state 29 key / buffs / hot(I1 新做) / debuffs 死键）各带一半能力，分裂是
  历史演化非第一性设计**——state 无到期（dot.turns hack）、buff 无叠层、
  hot 无归宿、debuffs 零消费。鱼鱼拍板**做干净**：统一为单容器
  `actor["effects"]` + 单规则表 `EFFECT_RULES`。
  - **方案文档（完整字段级+排期）**：`docs/REFACTOR_v181P4_EFFECTS_UNIFY_design.md`
  - **排期决策**：V 系列插在 **I2 之后、I3 之前**（现在做）——引擎还在重写早期，
    命令层盖楼前先浇地基；I1 hot 容器段（V3 删）+ I2 翻译器（V6 改）被 V 吸收，
    不做独立回滚；V 完成后 I3-I7 用新 API 写（工作量反而减少）。
  - **V1-V7 分阶段**：V1 容器地基（串行前置）→ V2 stats/V4 动词可并行 →
    V3 schedule 统一结算 → V5 数据表 29 key 迁移 → V6 命令层/桥适配 →
    V7 全套回归。约 23h（子 agent 并行压 ~2 工作日）。
  - **完成顺序（更新后总队列）**：~~I1/I2（已做，被 V 吸收）~~ → **V1-V7** →
    I3-I7（命令层用新 API）→ R3-R5 → N5b4-6/7 → 剩余 weapon/affix 缺口 → N10 删旧。
  - 未决点随附：世界Boss DOT 语义（记录 6 路线 B）在 V 统一 period damage 后
    语义不变，顺手一起收口。

## 1. 已完成（全部绿，工作区干净）

### N7 效果系统收口（8 commit）
buff 数值动作参数化 / 绝对到期 / on_hit 消费 / DOT interval / 187 名词分诊 /
heal/state_set/interrupt/damage 动词补齐。

### N8 事件总线（2 commit）
- `game/battle2/effect_triggers.py`：fire() 唯一入口 + **EVENTS 22 时机**
  （19 效果时机 + dmg_calc/taken_calc + act_done）
- 效果源 = `actor["triggers"]`；owner 注入 params._owner；事件主体过滤（N9.6）

### N9 装备特效族化（→ weapon 72/79 + affix 42/76 覆盖）
装配层 `game/services/battle2_equip_proc.py` + 族扩展动作 `battle2_we_procs.py`。

**N9A-1 death_dance 缓伤池**（04bb334）：we_death_pool_add/pay 扩展动作。
**N9A-2 act_done 通用广播 + randuin/ice_vein**（0906c30）：EVENTS +act_done（全员
广播、效果侧判敌我）；randuin/ice_vein = STATE_EFFECTS 层声明 + stat_scale 负值。

**N9.7 affix 76 分档迁移**（6db4cce→b9f0d50 四批）：
- A1 stat 型 26：生成时折算 → 面板自动含（零代码验证）
- N9.7a shield/regen/meditate + 装配骨架（affix_triggers/翻译器/tier）
- N9.7b on_hit 族 8：bleed/armor_break/element_*/combo/charge/pierce（4 扩展动作）
- N9.7c on_taken 族 2 + dmg_reduce：counter/tenacity_cc（反击/清负回血/减伤）
- N9.7d 条件乘区 4：execute/hunt/break_magic/dragon_aw（we_dmg_mult_cond 补 4 谓词）

---

## 2. 效果系统心智模型（鱼鱼 2026-09-08 认可——设计一切效果对着拆）

```
引擎表达力 = 三原语 + 组合器 + 有限机制本体：
1. state + 声明表   → 数值状态/层数/资源/DOT/濒死保护（cap/stat_scale/dot/guard 全配置）
2. buff + 效果动词   → 带时限临时状态（到期时刻/数值快照；control/buff/shield/heal/damage...）
3. 事件钩子         → "何时触发"（fire 22 时机 → actor 声明执行）
4. 扩展动作（组合器）→ 条件/概率/多段逻辑放游戏侧注册进 ACTION_HANDLERS，
                     内部只调引擎 API（动词/landing/state）——引擎零名词知识

做效果 = 三个问题：什么时候？（事件钩子） 持续还是数值？（buff/state）
                有条件/概率/复杂链？（扩展动作）
⚠️ 做不了的是机制本体不在引擎的（闪避命中 roll / 连击入口 / 复活时序）——
   本体一旦有钩子，效果表达依然用三原语。
```

---

## 3. 剩余工作（按优先级）🔴 队列已因 V 系列插队更新（见 §0.5 记录 10）

### A0. 🔴 效果容器统一（V 系列）——当前第一优先（I2 之后、I3 之前）
- 方案：`docs/REFACTOR_v181P4_EFFECTS_UNIFY_design.md`（完整字段级 + V1-V7 排期）
- 4 容器（state/buffs/hot/debuffs）→ 单 `actor["effects"]` + 单表 `EFFECT_RULES`
- V1 容器地基 → V2 stats/V4 动词（并行）→ V3 schedule 统一结算 → V5 数据表
  → V6 命令层/桥适配 → V7 回归；每阶段全绿 commit
- 开工口令：「继续 effects 统一，读 docs/REFACTOR_v181P4_EFFECTS_UNIFY_design.md
  从 V1 开始」

### A. weapon 缺口（剩 2 实现缺口）
| key | 缺的机制 | 状态 |
|---|---|---|
| novice_first_turn_dodge | 闪避（battle2 无命中 roll） | 等命令层 N5b-4 后做（N9A-3 战斗系统批） |
| novice_hunt_combo / combo_end | 连击/连段（拳师/刺客职业机制） | 缺口等上层职业模块 |
| ~~trinity_rhythm thunder 段~~ | ~~附雷附加~~ | ✅ N9.8 已补（hit 子键 bonus_atk_pct + _translate_trinity） |
| ~~death_dance_armor 复活段~~ | ~~致死复活链~~ | ✅ 复核 = 旧引擎从未实现，battle2 行为已等价；文案虚标记 N10 清单 |

### B. affix 缺口（剩 34）
- purify：需"敌方增益 key 语义"设计（battle2 buffs 无 mon_ 前缀概念）
- 资源型 20（rage/faith/chi/cp/energy 受击/暴击/施法回）→ 上层职业模块
- 职业机制 12（法印/反应/攻线/终结技）→ 上层职业模块
- boiling_blood（rage_full 判定）/ finisher（终结技）→ 上层

### C. N5b4 命令层切换（进度：1/2/3/4 完成，剩 5/6/7）🔴 下一步主工程
- **详细设计文档**：`docs/REFACTOR_v181P4_N5B4_command_switch.md`（字段/函数级施工图）
- **已完成**（0c1a5c6/fe0b3a8/207e741 + N5b4-4，每批全绿）：
  - N5b4-1 展示纯读（player dict + b.sides 双引擎通用）
  - N5b4-2 野外/野王/普通遇怪 + 4 行动（attack/skill/defend/flee）切 battle2
  - N5b4-3 世界Boss 切 battle2（DOT 语义未决点见 §0.5 记录 6）
  - N5b4-4 **PVP 切 battle2**：_pvp_start 构造 battle2 sides（player=攻击方/enemy=防守方
    双 human_controlled）+ meta{attacker_qq, actor} 外壳；_pvp_act 从 state 恢复、按
    my_side 显式定位行动者、meta.actor 驱动轮流、defending 随 actor 持久化（defend 覆盖/
    非 defend 消耗）、heal/buff 技能 target=None（防奶对手）、胜负按 actor 存活判定
    （battle2 result 视角固定 player side，防守方翻转）；flee/超时/旧档清档兼容。
    测试 tests/test_battle2_n5b4_pvp.py 29 断言。title_bonus 缺口见 §0.5 记录 7。
- **剩余**：N5b4-5 instance.py 副本
  （增援/DOT 自动/killed）、N5b4-6 economy/player/tower 轻文件 + 删 import、
  N5b4-7 全命令层回归 + 汇报鱼鱼过目 diff
- **N5b4-5 进度**：侦查发现副本深度定制旧引擎（仇恨/团队广播/剧本/内聚引用），
  切 battle2 需先补缺口 → 设计文档 `docs/REFACTOR_v181P4_N5B5_instance_gap_design.md`
  （鱼鱼 2026-09-08 审查后拍板"先做"）。引擎批 5E 完成：Battle +target_picker
  （自动 actor 目标注入）/ +on_event（事件总线外部观察者），引擎零游戏知识；
  测试 test_battle2_n5b4e_hooks.py 13 断言。剩 5a 主流程 / 5b 账务 / 5c 剧本。
- **已核实事实**：死亡 actor 不从 sides 移除（只进 killed_actors，展示要过滤
  actor_alive）；db.save_battle 的 monster 列已兼容 sides（N5b4-3 改）
- 鱼鱼约定：**核心战斗文件 diff 出后鱼鱼过目再提交**
- 引擎零改动铁律至今保持（N5b4 三个 commit 均未碰 game/battle2/）
- ⏸️ **N5b4-5a I3-I7 道具链后续暂停**（V 系列统一容器先行，见 §0.5 记录 10；
  I1/I2 已 commit 的 hot 容器/翻译器被 V 吸收，V 完成后用新 API 续做 I3-I7）

### D. N10 删旧（最终验收"清干净"）
- 删除清单见 `docs/REFACTOR_v181P4_N9_migration.md` §4：battle.py（11000+ 行）/
  battle_mech.py / weapon_effects.py / _we_executors.py / affix_effects.py / BUFF_MULT
- **前提**：weapon/affix 全部能力由 battle2 路径覆盖 + 命令层真实玩家跑通（N5b-4 完成后）
- 顺序建议：weapon 小缺口（trinity thunder 段等）→ N5b-4 → N10

---

## 4. 施工纪律（鱼鱼铁律，务必遵守）

1. 替换/大改前 `git status` 确认干净；出事先 `git checkout` 秒回，别在坏文件上硬修
2. 每块改完跑测试 + commit（v181.N9.X 格式）再动下一块；全套绿是底线
3. 引擎零游戏知识：名词/条件/数值全在数据与扩展动作——引擎只留动词执行器 +
   landing + config 查表 + 事件总线
4. 新效果接线 = 数据声明（triggers/STATE_EFFECTS/EFFECT_ACTIONS），不改引擎
5. 读表零默认值：缺字段 = 无此行为；数值权威 = 数据表 + we_data 覆盖
6. 不陪葬旧 bug：语义以 battle2 v2 定稿为准
7. 写生产库前必先 cp 备份 + dry-run

---

## 5. 关键文件速查

| 文件 | 角色 |
|---|---|
| game/battle2/effect_triggers.py | 事件总线（EVENTS 22/fire/subject 过滤/_owner） |
| game/battle2/effects.py | 动词执行器 ACTION_HANDLERS |
| game/battle2/landing.py | 落地收口（death_guard/taken_calc/heal amp） |
| game/battle2/battle.py | Battle 主类（act() 尾部 act_done fire） |
| game/data/battle2_rules.py | STATE_EFFECTS/EFFECT_ACTIONS（含 affix_bleed/randuin 声明） |
| game/services/battle2_equip_proc.py | 装配层（weapon + affix 翻译器/apply_to_actor） |
| game/services/battle2_we_procs.py | 族扩展动作注册中心（we_* 全部） |
| tests/test_battle2_n9_equip.py | N9/N9A/N9.7 验收（133 断言） |

## 6. 会话重启第一步
读本文档 → `git log --oneline -8` 确认 HEAD → 剩余：C 的 N5b4-4 PVP / N5b4-5 instance
（N5b4-7 前核心 diff 给鱼鱼过目）+ §0.5 记录 6 的**世界Boss DOT 语义未决点**（先保留
现状路线 B，鱼鱼说"先保留吧，我开新会话了"）。每批 commit 后汇报鱼鱼。✂️

## 7. V 系列更新（2026-09-08 V4+V5 完成后追加；09-09 V5 收尾补齐）

### V1 原子切换（bf6c590）+ V1b 显示适配（15a8ba0）→ V4 动词收敛（fe1350b）→ V5 面板入表（ba04288）

- **V4 动词收敛**：control/buff/state_add/state_set/state_spend 五动词 → apply/consume 二动词。
  effects.py 注册 apply（mode=控制 / op=add|set=叠层 / value=值型 / stat=增益快照 /
  hit=出手消费 / 纯状态 参数分流，cap 查 EFFECT_RULES，threshold 事件保留）+ consume（扣叠层）。
  effects_from_skill mech 分派发 apply+op=add。EFFECT_ACTIONS 33 buff→apply + 6 control→apply
  （补 key/on/mode 显式——slow/spd_down 原 mode 缺省 skip 已显式化）+ stacks_set→apply op=set。
  装配层 equip_proc 9buff+2state_add、we_procs 4buff+2control+内部直调 act_buff/act_control→act_apply、
  item_use 反查兼容 apply。测试 4 文件 type 机械替换 + coverage 控制用例显式 mode。
  ⚠️ 与旧记录「动词名勿删」的关系：那是 V1 阶段为避免破坏装配层的临时约束；V4 同步改完全调用面后
  删旧注册名是干净终态（鱼鱼拍板 A 确认）。V4 后装配层只发 apply/consume + shield/cleanse/heal/
  damage/interrupt。battle2 21 文件全绿，run_all 335 零新增回归（v137_dungeon 基线红已证 15a8ba0
  同 19/1；v85_pvp_honor run_all 库互清偶发单跑 25/0 绿）。
- **V5 面板入表（ba04288 半程）**：EFFECT_RULES 加 19 buff key panel{stat,op,mult} 声明（atk_up/def_up/spd_up/
  crit_up/matk_up/food_* 等），act_apply 增益分支参数缺省查表（动态装配层参数直传仍优先），
  stats._apply_effects 折算单源查表能力就绪。
- **V5 收尾（09-09 手工补齐，本次 commit）**——数据表迁移四大块一次做完：
  1. **EFFECT_ACTIONS 静态 buff 瘦身**：27 名词/28 动作的 stat/op/mult 参数删除 → key-only
     （数值单源查 EFFECT_RULES[key].panel；改前逐条核验 0 误差）。
  2. **控制 tag 入表**：stun/freeze/sleep/silence 进 EFFECT_RULES 带 consume{mode}（sleep 额外
     wake_on_hit 声明，不可净化）；act_apply 控制分支 mode 参数缺省查表回落；EFFECT_ACTIONS
     控制条目瘦身（stun/freeze/sleep/silence 去 mode 参数）。⚠️ **mech 分派防劫持**：
     _mech_to_effect 判据改为 _is_stack_resource()（有 stat_scale/debuff_scale/period/dot/
     on_threshold/guard_hp_pct 或 cap>1 纯计数 = 叠层资源走 apply op=add；仅 consume/panel/
     tag/cleanse 效果声明 = 名词路径走 EFFECT_ACTIONS）——否则技能 mech=stun（mech_val=2 刻晕）
     会被当叠层 2 层，行为破坏。spd_down 双语义（装配层 _slow 减速 stat + 控制 skip）不入
     consume，仅作净化标记（动作参数优先，协议 §7 判据）。
  3. **DOT dot → period 统一**：EFFECT_RULES 8 DOT key（burn/bleed/poison/corros/blaze/ember/
     blood_trace/affix_bleed）改 period{dir:damage, interval:1.0, 原数值}；schedule 读点删
     旧 dot 回落折算，直接读表 period；act_cleanse 读点同步（dot → period）。
  4. **cleanse 表化**：CLEANSE_TAGS 硬清单删除 → EFFECT_RULES 内 cleanse/negative 声明
     （stun/freeze/silence/spd_down/reduce cleanse=True；sleep 不可净化）；act_cleanse 遍历
     effects 查表（period / on==target / cleanse）；config.py cleanse_tags 挂载/接口删除。
  battle2 21 文件全绿；run_all 335 沙盒对照：V5 29 失败 = 基线(c1154d8) 29 失败 完全一致，
  **零新增回归**（既有基线含 v137_dungeon 等，非本次引入）。
- **剩余**：V6 命令层复查（V1 已切大部分）；V7 最终回归 + 文档 diff 给鱼鱼。V 系列后 →
  I3-I7 道具链续做（用新 API apply/consume）。

## 8. 会话重启第一步（V 系列后更新）
读本文档 → `git log --oneline -6` 确认 HEAD → V 系列已完成（V1/V1b/V4/V5），剩余主线：
I3-I7 道具链续做（apply/consume API）+ N5b4-6/7 + 世界Boss DOT 语义未决点（记录 6 路线 B）。
每批 commit 后汇报鱼鱼。✂️

## 9. V6/V7 + I3-I5 + N5b4-6/7 自主推进记录（2026-09-09 鱼鱼睡觉批）

### V6 命令层/桥复查（b116e4f）——修 2 个真实断链 bug
- **echo_bless（神龛祝福 v97.4）断链**：prepare_player_for_battle 消费 event_state 后写
  player.buffs 旧键，player_to_actor 又剔除 buffs → 祝福效果 battle2 从不生效。
  修：仪式消费读 event_state pct（5/6/8% 动态）→ 落 `player["_battle_boons"]` 标记 →
  player_to_actor 尾部 `_battle_boons_to_effects` 翻译进 actor.effects 面板快照
  （{stacks,stat,op,mult}，无 expire=整场；stats._apply_effects 折算）。
- **poi_buff（神龛祝福 v104 M23）断链**：仪式写 player.poi_buff 仅透传 actor 字段，
  battle2 stats 从不折算。修：同落 _battle_boons → effects（stat/mult 动态）。
- player dict 不再透传 poi_buff 冗余 actor 字段；combat.py 两处开战 bless_note 改读
  _battle_boons + 动态 pct 文案（原来写死 +5%/+10%，雷淬之池实际 pct=8%）。
- 测试：test_battle2_bridge 断言同步新语义 + boons→effects 翻译断言（64/64）。

### V7 全量回归（沙盒对照）
- 沙盒：Temp/df_wt_v7sbx/data/plugins/dragonfall（data/plugins 父链必需）。
- run_all 335：306 通过 / 29 失败 = V5 HEAD(ecdca3f) 对照逐条一致（v5check 沙盒），
  **零新增回归**。失败名单全部是旧引擎线测试（N10 删旧前基线红）。

### I3-I5 道具链 battle2 化（65886cc）
- I3：instance_battle.act from_state 后注入 make_override（action_override 不可序列化，
  恢复必重挂）；economy 副本 use_item 分流改 _instance_router（不再调旧 _instance_act——
  其对 battle2 state 静默失效）。
- I4：economy 普通野外 use_item 段改 battle2（_restore_battle2 + override + human_act +
  sync_player_from_actor 回写；胜负按 sides actor 存活判定）。
- I5：purify 改翻译器——item_templates tpl_purify 只做净化对象判定（读 battle2 视图/
  sides actors effects + EFFECT_RULES period/on=target/cleanse 声明）→ payload=purify:1；
  翻译器新增 purify 分支清玩家侧负面（sleep 不可净化保留）；purify_immune 映射 cc_immune
  （规则表 + 分诊键）。机制型缺口（summon/trap/phoenix 等）：can_translate 纯判定 +
  economy 两处 remove_item 前拦截 → 提示不扣道具不占刻（原状态=白扣+静默失效）。
- 测试：router test_12 use_item 端到端（heal 生效/缺口不占刻）；item_use test_purify；
  battle2 21 文件全绿。

### N5b4-6 轻文件切 battle2（34b5608）+ N5b4-7 回归
- player.py 属性面板战斗内实时值：BT.Battle.from_state+_player_stats → battle2
  from_state+actor_stats（state 无 sides 回落静态）。
- tower.py 爬塔开战 / world.py 跨图撞怪伏击：旧 BT.Battle 构造 → battle2 四步仪式
  （prepare/sides/装配/B2，同 _open_battle2 语义）。
- economy/world/player/tower 四处 BT import 清零（N10 前置）。
- world.py 副本行动提示改 battle2 轮转（_instance_turn_player_name 读 IB.next_actor_key，
  4b193ba 前置 commit）。
- 测试适配：v97_07/v1252 use 段旧格式 state fixture → battle2 to_state（9b36ed7）。
- run_all 335：306 通过 / 29 失败 = V5 基线逐条一致（v7c 沙盒确认）。

### 卡点（无法自主安全推进，待鱼鱼）
- **I6/R3 instance.py 删除清单**：_instance_act 零调用可删，但 CT helpers
  （_instance_next_player_name/_instance_ct_queue/_instance_next_actor/_instance_reset_player_cts 等）
  仍被玩法壳引用（instance_advance/_instance_explore/_instance_start/_instance_battle_footer/
  _instance_secret_crack 等 8+ 调用点），删除前需逐点改读 battle2 或删段；副本流程测试
  （v141/v137/v178 等）在基线红 → 删除无兜底验证网。建议先写 R4 端到端（拟真 DB 2 人
  开本完整流程）再删。
- **N5b4-5b/5c**：账务深化（target_picker/team 广播 on_event 翻译器）+ Boss 剧本
  mech DSL 导演——开放内容翻译工程（每剧本一个命令层动作，量=副本内容翻译），
  范围需鱼鱼拍板。
- **N10 删旧**：前置 = N5b4 全切 + weapon/affix 覆盖 + R4 验证；当前 battle.py 1.1万行
  仍被旧路径测试引用（29 基线红大半是它）。
- 世界Boss DOT 语义未决点（记录 6 路线 B）：未动，保留现状。

## 9.2 R3 + 5b 推进记录（2026-09-09 追问后继续推进）
### R3 instance.py 删除清单（63ada06 + 80d2632 + 117626a）
- 删除 803 行：_instance_act（633 行战斗主体）/ _instance_battle_cb / _apply_team_effect
  / _instance_auto_defend_player / _sync_enemy_unit / _instance_next_player_name
- CT helpers 保留链：living/min/min_enemy/next_actor（_instance_start 开本首动展示用）、
  ct_queue（footer 行动队列）——均无 BT 依赖
- instance.py BT 依赖清零：ct 播种 _ct_cost/_ct_initial_wait → battle2 schedule
  action_time/initial_ct（公式同款：CAST_ATK×√(SPD_REF/spd)）；BT import 删除
- 命令层 BT import 清零：base/combat/misc/social 残留 import 删除（N10 前置）
- 先修 2 个旧测试：ctb_audit（auto_defend→IB.act defend 语义 + reset 断言对齐）
### 抓到的真 bug（v137 暴露）：副本切房/新怪入场只更新 st.enemies 视图，
- st.battle 残留上一房 sides → router 懒构建条件仅查'有无 sides'不重建 → 玩家打旧
  死亡 actor 死循环（真人在副本换房会遇到）。修：4.1b 按敌人 uid 集合一致性强制
  重建（7ec4631）。
### R4 验证网测试 battle2 化（7ec4631/ddc6b56/80d2632）
- v137_dungeon 23/0（开本→清怪→移房→Boss→通关端到端）+ v141_instance_world 101/0
  （失败回城/大陆销毁）+ v94_stamina 22/0 + v95_25 27/0 + ctb_audit 13/0
  —— 均为旧格式 state fixture → battle2 to_state + 大陆权威 st（C.get_instance_st）
  适配。全量 335：310 过 / 25 失败 = R3 前基线逐条一致，零新增回归。
### 5b 副本账务：G1 仇恨 + G2 团队广播（4680f83 + be073a2）
- G1 target_picker：_instance_target_picker(st) 闭包（嘲讽强制 → MONSTER_MODS
  target_policy（boss 缺省 hate_top/其他 front）+ st.threat 表 → FM.pick_by_policy）；
  _attach_instance_hooks(b, st) 统一重挂 target_picker + action_override + on_event
  （build_battle 构造时 + act from_state 后）——构造参数不可序列化必重挂
- G2 on_event 团队广播：_instance_team_event 监听 act_cast + info.team==heal_all →
  除施放者外全队治疗（_heal_amount 同引擎口径 + landing.heal_actor）。数据现状
  team 值仅 heal_all（救赎之光）——按声明做无 if-elif 扩散
- router test_13（hate_top/嘲讽/front/无存活）+ test_14（双人 heal_all 广播/单人
  不崩）46/0；battle2 全套 + v137/v141 零回归
### 剩余（需鱼鱼）
- 5b 死亡/击杀 on_death → alive 同步：router 死亡账已齐（_router_advance_killed），
  玩家倒地 sync_views 已写 alive——待端到端验证
- 5c Boss 剧本 mech DSL 导演（25 phases × 副本，内容翻译工程）
- N10 删旧（battle.py 1.1万行）：命令层 import 已清零，剩 weapon/affix 上层缺口 +
  numeric/stage/v1xx 旧引擎直测 25 红的迁移

## 9.3 5b 收尾 + I7 道具链收口记录（2026-09-09 上午，84f18d8）
### 5b 收尾：多人死亡 alive 同步端到端验证（test_15，+13 断言，router 59/0）
- 覆盖：一死一活副本战 → actor/视图/DB 三路 hp 同步 0 + alive=False
  （sync_views 倒地标记 O105 语义落地验证）；
  死者请求行动 → 轮转到活人等待提示，不崩不占轮；
  next_actor_key 跳过死者（hp<=0 过滤）；活人单刷通关；
  通关奖励隔离：阵亡者 💀 未获奖励（gold 不变），活人得奖；
  失败回城/全灭已有 test_8 单人覆盖，v4 探针确认多人同链路。
- 探针教训（多人 router 测试）：无 party 行必须 _patch_current_members；
  压血要视图+DB 双写（build_battle 读视图、sync_views 写 DB）；
  多人 CTB 推进 = 按 next_actor_key 轮流驱动（engine 停在真人行动点，
  敌 ct 未到不插队）——真人轮流操作的自然行为，非 bug。
- 生产代码零改动（账务层 5b G1/G2 已齐，纯补验证网）。

## 9.4 5c P1 完成记录（2026-09-09 上午，导演框架 + phases 转阶段）
### 交付（引擎改动 ≤15 行，命令层新模块）
- **battle2/battle.py script_hook**：Battle.__init__ 第 4 注入钩子（target_picker/
  on_event/action_override 同款）+ actor_auto 行动帧前置调用——返回 True = 演出刻
  拦截本刻行动（照推 ct）；hook 日志并入 actor_auto 返回（_hook_logs 前置）。
  默认 None → 零回归（全量 336 = 311/25 与基线一致，+test_boss_script_p1）。
- **game/commands/boss_script.py 导演**：boss_script_cfg（MONSTER_MODS 基准 +
  INSTANCES 副本覆盖 v178 E1 + mech token 并集 E2；无 phases → None 不挂）+
  make_script_hook（导演帧：round_no 计数 + _check_phases 血量阈值转阶段）+ 状态
  st["boss_script"]（随副本持久化，actors 只留引擎效果——V 系列铁律）。
- **instance_battle._attach_instance_hooks**：敌方阵容有剧本 Boss 才挂 script_hook
  （build_battle 构造 + act from_state 重挂统一走它）。
### phases 转阶段语义（对齐旧 _b_phase，battle_mech.py:698 + v116 测试）
- 阈值链：pc 从 0，target = phases[pc].min（缺省 0.5^n）；pc<3 且 ratio < target → 进
  下一阶段；min=0 末条永不触发（古王 rampage 同理，无害）
- 演出：phases[npc-1].script name/icon；阈值预告（pc>0 下一阈值 +3% once）
- 换招：add_skills 幂等 append actor.skills + auto_act 切阶段主技能（actor_auto 读）
- atk 乘区：phase_id → boss_phases.merge_phase_config 模板 atk_mult（覆盖式）；
  无 phase_id/atk_mult → 旧行为 1+0.2×npc；落 actor.effects boss_phase_atk/matk
  （面板快照型 stat/op/mult 内嵌，无需 EFFECT_RULES 注册——stats._apply_effects 折算）
- 演出刻：返回 True → 引擎拦截本刻行动（对齐 _phase_skip_act）
- preserve_debuffs：默认全保留（P1 简化为不清除，防误清 Boss 自身状态；
  模板显式 False 的清负面留给 P2 盘点 EFFECT_RULES 后细化）
### 测试（test_boss_script_p1.py 22/0）
cfg 解析（inst 3 条覆盖）/ 40%→阶段2（王冠威临换招 ×1.2）/ 25%→阶段3（enrage
模板 ×1.25）/ rampage min0 不触发 / 演出刻无伤害 / 序列化 st["boss_script"] 跨
from_state 保留 + 重挂继续。
### 教训/记录
- actor_auto 无 logs 参数——hook 用局部 _hook_logs，正常行动时前置合并进返回日志
  （初版引用不存在 logs 变量被 except 吞，导演静默失效——探针抓到）
- monster_to_actor 剥 _inst_id（白名单透传）→ cfg 靠 st.inst_id 兜底（副本内
  inst_id 恒在，可靠）

## 9.5 5c P2 完成记录（2026-09-09 上午，opening/player_low/简单机制）
### 交付（boss_script.py 导演扩展，引擎零改动）
- **_check_opening**（mech phase_open）：第一帧 once——演出 + effect 翻译
  （数值 battle_config BUFF_STATS 同源零新数值）：atk_up/strong → Boss atk/matk
  ×1.30/×1.70 时效 power 秒；mon_atk_down → 玩家 atk ×0.70；mortal_wound → 玩家
  effects 落条目（**battle2 吸血装配未落地——条目预留，吸血批消费**；3 boss 用）
- **_check_player_low**（mech player_low/triggers）：任一存活玩家 hp<阈值
  （triggers.hp 缺省 0.30）→ 演出 + 本刻 atk/matk ×1.25（旧 _b_player_low 25%）；
  once 或 cooldown=N 重复（_low_hp_cd 计数）
- **_check_simple_mech**（简单 token，04 章机制表数值）：
  stacks 每 2 刻 +1 cap5 ×(1+0.08n) / heal 每 4 刻回 8%（landing.heal_actor）/
  enrage 血<30% once ×1.35（**phases 含 enrage phase 则跳过**——P1 phases 管）/
  shield 开战 once 20% 盾 halve（effects.act_shield turns=999 永久盾）
- hook 帧顺序：round_no++ → opening → player_low → simple_mech → phases（skip）
- **pv_broken 不做**：当前数据零消费（无 token/triggers 配置）——不做死代码
- **临时乘区 = effects 面板快照型 + expire=now+短秒**（0.1s：下次时刻推进即过期，
  仅本帧行动吃到——对齐旧"本刻加成"语义）
### 测试（test_boss_script_p2.py 26/0）
opening atk_up/mortal_wound/once / player_low 低血触发+满血不触发+无配置不触发 /
stacks cap5 累计 / heal 4 刻节奏 / enrage 补漏 + phases 覆盖跳过 / shield 20% halve /
简单机制不拦截。P1 22/0 仍绿；全量 337 = 312/25 与基线一致零新增。
### 待 P3-P5
- summon 召唤系（P3）/ chains/on_interrupt/on_minion_died（P4，含"插一帧行动"基建
  给 pv_broken 反扑预留）/ element/defend_reduce/pdot/reflect 反弹/形态轮换（P5 盘点）
- mortal_wound 消费端 = battle2 吸血装配落地批

## 9.6 5c P3 完成记录（2026-09-09 上午，召唤援军）
### 交付（boss_script.py _check_summon，引擎零改动）
- mech summon：CD 5 刻（对齐旧 r%5==0：round_no 5/10 触发）、单次 1 只、
  场上援军上限 3（含开怪自带爪牙——enemy side 存活 is_minion 计数，死亡不占位）
- 召唤物模板（v163 口径）：INSTANCES[inst_id].minions[0].monster →
  C.build_monster（同图小怪模板，不从 Boss 缩放）；非 instance/无 minions 回落
  Boss×0.2（旧兜底路径保留）
- 召唤物字段：uid e_min_seq（bs.summon_seq 递增）、名字 "{Boss}的{模板名}"、
  rank1/reach1、is_minion=True、is_boss/is_elite False、mech=""（防递归剧本）、
  auto_act 缺省普攻、ct=now+2（站场不插队）
- 成功召唤 → Boss 攻击联动 atk×1.30 时效 2 秒（旧 mon_atk_up 线上行为；
  ⚠️ 策划案文字"自身攻击+20%"为概数——记录差异，行为跟旧代码）
- append 写 battle.sides["enemy"] 容器（⚠️ sides_of 返回拷贝——初版 append 到
  拷贝白做，测试 n=0 抓到）
### 测试（test_boss_script_p3.py 18/0）
CD 节奏 5/10 / v163 模板（哥布林营地 → 哥布林守卫）/ 回落 Boss×0.2 / 上限 3
（预置 2+召 1；满员不召）/ 死亡爪牙不占位 / 无 token 不召。P1 22/0 P2 26/0 仍绿；
全量 338 = 313/25 与基线一致零新增。
### 待 P4-P5
- P4 chains/on_interrupt/on_minion_died（含"插一帧行动"基建给 pv_broken 预留）
- P5 reflect 反弹/element_immune/weak/defend_reduce/pdot/形态轮换盘点

## 9.7 5c P4 完成记录（2026-09-09 上午，chains / on_minion_died）
### 交付（boss_script.py，引擎零改动）
- **_check_chains**（导演帧，非演出刻才推进）：seq 顺序轮换改 actor.auto_act
  （本帧 actor_auto 读它出招）；chain_pos 推进到头回绕 + chain_idx 多链轮换；
  cd 整链冷却（until = 帧 + cd + 1：cd=0 无缝 / cd=1 隔 1 帧）；break>0 概率断链
  回随机池；charging 读条中不出链
- **make_script_event**（剧本事件观察者，组合进 instance_battle on_event 链：
  团队广播 + 剧本联动并存）：on_death + is_minion → 找剧本 Boss（非爪牙存活）
  → on_minion_died 联动执行 _minion_death_link：
  heal_pct（Boss 回 pct max）/ stacks_clear（清 stacks_n + effects）/
  atk_up（×1.30 时效 turns）
- **boss_script_cfg 门槛放宽**（P1 只认 phases → P2-P4 任一剧本要素即可挂导演/
  观察者：phases/opening/chains/on_interrupt/on_minion_died/简单 token）——
  on_minion_died 独立于 phases 的 Boss（如 b_moro）也能被观察者识别
- **on_interrupt 未做**：需引擎 interrupt 事件扩展（act_interrupt/landing 清
  charging 处 fire）+ 玩家打断技能链路确认——P5 或独立小批，19 boss 带配置
### 测试（test_boss_script_p4.py 14/0）
chains 4 招轮换回绕 / cd=1 隔帧冷却 / charging 不出链 / heal_pct（b_moro 真实
cfg 经观察者端到端）/ stacks_clear / atk_up（直调分支）/ 非爪牙死亡不触发。
P1-P3 22/26/18 仍绿；全量 339 = 314/25 与基线一致零新增。
### 5c 批进度小结
P1 导演框架+phases ✅ / P2 opening+低血+简单机制 ✅ / P3 召唤 ✅ / P4 chains+
爪牙联动 ✅ → 27 卡绝大多数机制族已可表达（打断族 on_interrupt 例外待 P5/独立批）
剩余：on_interrupt（引擎 interrupt 事件）、P5 场景原语盘点（reflect 反弹/
element_immune/weak/defend_reduce/pdot/形态轮换）

## 9.8 5c 端到端验收完成记录（2026-09-09，真实副本 Boss 战）
### test_boss_script_e2e.py 15/0（真实命令层链路，非单测）
- 流程：开本（哥布林营地）→ 清房 → 移动 Boss 房 → Boss 战（真实玩家操作）
- 断言：咕噜登场（+开怪 2 爪牙 minions 展开）→ opening 首帧触发（掠夺号令
  演出 + flags._open_played）→ Boss 压血 <60% 触发阶段 2（抄起酒桌演出 +
  sides actor auto_act 换招 ms_lve_jie_huan_zhua）→ <40% 酒疯（merge normal
  模板 atk ×1.7 落 sides actor effects）→ 导演状态 st["boss_script"] 全程
  在真实副本大陆权威 st 持久化
- 教训：导演改动落在 **sides actors**（st["boss"] 视图键不同步 auto_act/effects）
  ——断言必须读 sides actor；压血 helper 只压存活单位（死爪牙别"复活"）；
  副本开本按 DB max_hp 钳制玩家血（测试提血要连 max_hp 一起）
### 5c 状态：P1-P4 + e2e 全部完成
27 卡机制族：打断博弈/叠层/转火/读招防反/召唤 全部可表达（phases+opening+
player_low+summon+chains+on_minion_died+简单 token）；剩 on_interrupt（引擎
interrupt 事件扩展）+ P5 原语盘点（element/reflect/defend_reduce/形态轮换）。
全量 340 = 315/25 与基线一致零新增（5c 系列测试 P1 22 + P2 26 + P3 18 + P4 14
+ e2e 15 = 95 断言全绿）。

## 9.9 5c P5 完成记录（2026-09-09，on_interrupt + 原语盘点结论）
### 交付：on_interrupt 读条打断联动（引擎 +4 行事件 + 导演观察者）
- EVENTS 全集加 "interrupt"（23 个；n8_events 断言 22→23 同步）
- 引擎打断点 fire：landing.py 伤害打断 charging 处 + effects.act_interrupt 动词处
  （ctx {actor=被打断者, source=攻击方}）
- 导演 make_script_event 加 interrupt 分支：被打断者是剧本 Boss（cfg.on_interrupt）
  → _interrupt_link：
    freeze_self（咕噜等）→ effects boss_frozen {mode=skip, expire=now+turns}
    （引擎 act 控制消费：冻结帧不行动）
    vulnerable（19 处配置多数）→ boss._dmg_taken_mult=value + bs.flags._vuln_until
    =round_no+turns；导演帧 _check_vuln_expire 到点清（landing 承伤乘区消费）
- 测试 test_boss_script_p5.py 14/0（观察者 freeze_self 真实咕噜 cfg / vulnerable
  时效清理 / 引擎链路伤害打断→联动 / 非剧本 Boss 不联动）
### P5 原语盘点结论（能做的做了，其余标注缺口待上层批）
| 原语 | 现状 | 处置 |
|---|---|---|
| on_interrupt ×19 | ✅ 本次完成 | 全链可用 |
| pdot（给玩家 DOT） | battle2 effects period 已表达（on target） | ✅ 无需专门原语 |
| element_immune/weak | 数据透传但 **battle2 无元素伤害系统**（landing/effects 无 elem 消费） | ⏳ 元素伤害批（未来） |
| reflect（血<25% 反弹 15%，×1 boss） | 反伤装配未迁 battle2（_we_executors 旧引擎） | ⏳ 装配层 on_taken 声明批 |
| defend_reduce（方向性防御 v178 E6） | battle2 defending 减伤固定 0.5（landing:58），无按技能覆盖 | ⏳ 防御技能批 |
| 形态轮换（烛影/蚀夜双态） | phases + element 组合可表达；element 未落地前形态无伤害差异 | ⏳ 随 element 批 |
| mortal_wound（3 opening 用） | 玩家 effects 条目已落（P2）；**battle2 吸血装配未落地**→无消费 | ⏳ 吸血装配批 |
- v15 flaky 记录：numeric_actor_class run_all 并行偶红（单测 3 次全过；
  清 .run_all_workers 后 v16 回绿）——既有随机脆弱测试，非本次改动引入
### 5c 终态：P1-P5 + e2e 全完成，测试 109 断言全绿
P1 22 + P2 26 + P3 18 + P4 14 + P5 14 + e2e 15。全量 341 = 316/25（基线一致零新增）。

## 9.10 N5B 怪 AI P1 完成记录（2026-09-09，通用 AI 决策器 + 怪技能索引 bug）
### 交付
- **game/battle2/ai.py 新模块**：normalize_ai（旧 {skill_chance,weights} → weighted
  moves，幂等写回）+ eval_when（谓词 v1：self_hp_lt/gt、hostile_lowest_hp_lt、
  round_mod（actor.act_count）、cd_ok、恒真——未知谓词不命中防拼写漂移）+
  resolve_ai_move（priority 条件表 / weighted 权重随机 + skill_chance 概率回落）
- **actor_auto 决策 4 层**：导演演出刻 skip → auto_act 显式（导演换招/连招链压 AI）
  → ai 决策器（本批）→ 普攻；act_count 个体行动计数随 actor 序列化
- **🚨 修深层 bug：battle2 怪技能索引缺 MONSTER_SKILLS 源**（battle.py _index_skills
  只查玩家技能表 → ms_* 怪技能索引空 → ActCtx.info={} → do_skill 静默空放——
  怪从头到尾放不出技能，5c 导演换招后 Boss 实际打普攻）。修：查 C.MONSTER_SKILLS
  （旧引擎 7666 同款：先怪表后玩家表）
### 测试（test_monster_ai_p1.py 22/0）
normalize 幂等 / priority 命中顺序+AND+未知谓词 / round_mod 节奏 /
hostile 残血追击 / cd_ok 冷却（id→name 经 actor._skill_index）/ weighted 分布
+chance 回落 / 真实咕噜 ai.weights 20 帧自选技能（技能真实打出伤害）
### ⚠️ 已知小瑕疵（记录待修）
- P3 召唤物 append enemy side 尾部 = 后排不挡刀；旧语义 rank1 前排。真实 Boss
  召唤应插前排（e2e 咕噜无 summon token 未暴露）。修法：append 前插到敌方
  sides 前排位置（rank1 层），后续批处理。
- battle2 无射程限制（玩家可指定打后排，无"够不到"规则）——旧 v114.2 站位
  射程语义未迁，记录上层站位批。
### 全量
342 = 317/25（AI 测试计入）基线一致零新增。

## 9.11 N5B P2/P3 + target_hint + 仇恨配置完成（2026-09-09 下午）
### N5B P2/P3（test_monster_ai_p2.py 12/0）
- P2 覆盖验证：21+ boss ai.weights 全可 normalize + 技能 key 怪表/玩家表双查无悬空
- P3 导演共存：auto_act 显式招真实结算压过 AI（物理技能日志无技能名前缀——
  用玩家掉血验证）；无 auto_act 时 AI 生效；导演演出刻 skip 优先于 AI
### target_hint（鱼鱼拍板加——AI 战术目标，可扩展位）
- ai move 可带 "target_hint"：actor_auto 挂瞬态 actor["_target_hint"] →
  命令层 target_picker 消费（v1：lowest_hp 残血收割——与仇恨不冲突时优先；
  一次性 pop；未知 hint 回落仇恨；无 picker 引擎尾部清理防残留）
- 语义分层：仇恨（target_picker）= 默认公道规则；AI hint = 战术意图仅覆盖不冲突场景
### 🚨 仇恨配置接入（v173.5 模型——鱼鱼问"不同行为仇恨可配置吗"）
- 发现脱钩：技能数据 hate_mult/hate_taunt_mult（v173.5 数值模型）已配但消费端
  在 R3 删旧 _instance_act 时丢失（_find_skill_cfg 变死代码零调用）
- 修：router 3.5 账务读本次技能 cfg（_find_skill_cfg 复活）：
  伤害仇恨 = dealt × hate_mult（缺省 1，贡献仍按实际伤害）
  嘲讽（effect=taunt）= 仇恨当前最高×hate_taunt_mult+100 + st.taunt_target 强制
  lock 帧（hate_lock_turns 缺省 3）+ 每玩家行动帧递减 taunt_left 到 0 清强制
  治疗仇恨 ×0.8（v49 保留）
- 测试 test_instance_hate.py 11/0：普攻×1 / 盾击·誓×4 / 嘲讽最高×3+100 +
  强制锁 3 帧递减清除
- 测试教训：class_name 存职业 ID（cls_zhan_shi）不是中文——查表必须用 ID
### 全量
344 = 319/25 基线一致零新增（router 59 + 仇恨 11 + AI 34 + 5c 109 全绿）

## 10. 会话重启口令（2026-09-10 更新：N10-C 删旧完成 🎉）
- **N10-C 删旧完成**（379a792 + ce87914 + 4ad2a41）：旧战斗引擎 game/battle.py(11000行) +
  battle_mech/weapon_effects/_we_executors/affix_effects/food_effects 五注册表**全删**，
  累计 **-16965 行**；退役 160+ 守护旧引擎路径的测试 → tests/_retired_old_engine/（run_all 自动跳过）。
  现存验证网 = 205 绿 / 2 红（feedback_features+services_quests = 既有遗留，非删旧引入）。
  HEAD=4ad2a41。
- **N10 剩余**：D 测试处置的收尾只剩 2 个既有红（副本仇恨路径/任务断言过时，独立于删旧）；
  numeric 数值门禁族退役（鱼鱼拍板"重做数值时重建"，numeric_lib 模拟引擎依赖旧 battle 已归档）。
- 🔴 **L3 玩家事件层已排期**（2026-09-09 拍板，N10 删旧合并 master 后开工）：
  设计+排期 = docs/DESIGN_v181_L3_player_event_bus.md。L1 战斗内效果总线(N8) ✅ 已落地、
  L2 战斗级观察者(on_event) ✅ 已落地、L3 玩家级事件总线 ⬜ 缺位——victory_settle 手动
  接线任务/成就/公会/野王/塔卫要收敛成订阅。方案 = DDD 同步领域事件（非 QFramework 全家桶）。
- ✅ **master 合并完成**（2026-09-10，fast-forward 154 commit，9b73e2d）+ **2 个遗留红已清**：
  feedback_features #6 仇恨段退役（旧防御嘲讽语义被 v173.5 router 仇恨 + test_instance_hate 覆盖）+
  services_quests 测试日期改动态当天（写死旧日期被跨天重置误判）。**全量 207 = 207/0 全绿**。
- **N10 整批收官**：B 缺口补完 → C 删旧（battle.py + 五注册表 -16965 行）→ D 收尾（遗留红清零）。
  下一步 = L3 玩家事件层开工（排期文档已就绪，P0 任务书先行）。
- 🔴 **L3 玩家事件层 P0-P3 完成（2026-09-09 午后会话，master HEAD 0f722cd）**：
  - P0 字段级任务书 docs/REFACTOR_v181_L3_P0_task.md（339e90f）——侦察修订：手动接线在
    combat._handle_victory 壳 L2034-2118 非 victory_settle；胜利入口 4 类；公会=每场+1 订阅 battle_victory。
  - P1 总线核心 game/services/player_event_bus.py（e26f92a，EVENTS/register/fire/blank 空行/容错）。
  - P2a 下沉 tower/weekly 状态族 services（b7f509c，re-export 零行为变化）。
  - P2 field 试点（ee19c45）：6 订阅方 game/services/player_event_subscribers.py，combat 壳 → fire 单点；
    升级建模订阅方保行序；删 _update_quests。
  - P3 instance+worldboss 收编（0f722cd）：鱼鱼语义决策"任何击杀都算数"（老配置漏接非设计）；
    levelup kind 守卫仅 field（副本不升级回血防破坏节奏——有意设计保留）；删 _instance_main_kill_progress；
    战斗入口成就调用 3→0。全量 **208/208 绿**。
  - 剩 L3-P4：settlement 瘦身（可选）+ 新订阅方接入文档 + 回写。**新玩法加战斗反应 = services 注册一行**
    `register("battle_victory", handler, blank_line=...)`，不改结算函数。
- 续做口令：读本 HANDOFF §10 → git log 确认 HEAD → L3-P4 或下个排期项。
