# battle2 效果系统 v2 交接（N8/N9 阶段）——开新会话必读

> 2026-09-08 交接。主线 = 效果系统 v2 + 装备特效族化迁移（wt_ebuffs 分支）。
> 鱼鱼验收北极星：**最后清干净——N10 删旧 battle.py + 旧效果系统三套注册表，
> 不留兼容壳/开关/兜底参数**（鱼鱼原话："老的一定要确保删掉，最后不留东西"）。
> 会话重启口令：「继续 battle2，读 HANDOFF_battle2_effect_v2.md 接着 N9」

---

## 0. 分支/位置/跑法

- 分支：`wt_ebuffs`（worktree：`C:/Users/yuyu/AppData/Local/Temp/df_wt_ebuffs/w1`）
- HEAD：`413c276`（v181.N9.8 trinity thunder 段，2026-09-08）
- 主仓（生产）：`C:/Users/yuyu/qqbot/data/plugins/dragonfall`（master 未动）
- Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`
- 全套测试：`for f in tests/test_battle2_*.py; do python "$f"; done`（当前 12 文件 486 断言全绿）
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

## 3. 剩余工作（按优先级）

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

### C. N5b-4 命令层切换（🔴 **下一步主工程**——详细设计已备好）
- **详细设计文档**：`docs/REFACTOR_v181P4_N5B4_command_switch.md`（字段/函数级，
  2026-09-08 鱼鱼要求出详细方案再动工）
- 内容：9 文件改造总账 + 开战统一改法（prepare+build_sides+EP_apply）+ 玩家回写
  sync_player_from_actor（battle2 actor 是副本！）+ 世界Boss meta 外壳 + _status_line
  逐字段改造 + db.save_battle monster 列 sides 兼容 + PVP/instance 难点 + 8 批计划
- 关键已核实事实：死亡 actor 不从 sides 移除（只进 killed_actors，展示要过滤
  actor_alive）；db.save_battle 的 monster 列读旧 state["enemies"] 需兼容 sides
- 鱼鱼约定：**核心战斗文件 diff 出后鱼鱼过目再提交**
- 批次：展示纯读函数先切 → 探索战斗 → 世界Boss → PVP → instance → 轻文件 → 全量回归

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
读本文档 → `git log --oneline -8` 确认 HEAD → 剩余：B affix purify 设计 /
C（N5b-4 需鱼鱼把关 diff）等。每批 commit 后汇报鱼鱼。✂️
