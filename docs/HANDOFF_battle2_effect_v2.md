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
