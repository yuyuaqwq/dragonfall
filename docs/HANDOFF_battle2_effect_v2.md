# battle2 效果系统 v2 交接（N8/N9 阶段）——开新会话必读

> 2026-09-08 交接。主线 = 效果系统 v2 + 装备特效族化迁移（wt_ebuffs 分支）。
> 鱼鱼验收北极星：**最后清干净——N10 删旧 battle.py + 旧效果系统三套注册表，
> 不留兼容壳/开关/兜底参数**（鱼鱼原话："老的一定要确保删掉，最后不留东西"）。
> 会话重启口令：「继续 battle2，读 HANDOFF_battle2_effect_v2.md 接着 N9」

---

## 0. 分支/位置/跑法

- 分支：`wt_ebuffs`（worktree：`C:/Users/yuyu/AppData/Local/Temp/df_wt_ebuffs/w1`）
- HEAD：`0906c30`（v181.N9A.2，2026-09-08）
- 主仓（生产）：`C:/Users/yuyu/qqbot/data/plugins/dragonfall`（master 未动）
- Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`
- 全套测试：`for f in tests/test_battle2_*.py; do python "$f"; done`（当前 12 文件全绿）
- 覆盖率门禁：`python tools/cov_func_battle2.py`（0 未调用）+ `cov_branch_battle2.py`
- 效果系统主方案：`docs/DESIGN_effect_system_v2.md`（Part 3.3/4 定稿 19 时机 + 管线）
- N9 施工方案：`docs/REFACTOR_v181P4_N9_migration.md`（盘点/批次/删除清单）
- **N9A 缺口方案（2026-09-08 新增）**：`docs/REFACTOR_v181P4_N9A_weapon_gap_plan.md`
  ——weapon 6 真缺口完整设计 + 鱼鱼拍板记录（act_done 通用广播定稿 §2）
- 旧三套注册表数据权威：`game/data/weapon_effect_data.py`（79 key 13 族全参数化）、
  `game/data/affixes.py`（76 词条）

---

## 1. 已完成（全部绿，工作区干净）

### N7 效果系统收口（8 commit）
buff 数值动作参数化 / 绝对到期 / on_hit 消费 / DOT interval / 187 名词分诊 /
heal/state_set/interrupt/damage 动词补齐。动词全集：`control / buff / shield /
cleanse / cleanse_all / state_add / state_spend / heal / state_set / interrupt /
damage`。

### N8 事件总线（2 commit）
- `game/battle2/effect_triggers.py`：fire(battle, event, ctx, logs) 唯一入口 +
  **EVENTS 22 时机**（19 效果时机 + dmg_calc/taken_calc + act_done）
- 效果源 = `actor["triggers"] = {事件: [效果 dict]}`；owner 注入 params._owner
- 事件主体过滤（N9.6）：ctx.actor = 事件主体，只处理主体声明（旁观者不误触发）；
  无主体事件（battle_start）全体；on_death 允许死者自身

### N9 装备特效族化（→ weapon 72/79）
装配层 `game/services/battle2_equip_proc.py` + 族扩展动作 `battle2_we_procs.py`。

**N9A-1 death_dance 缓伤池**（04bb334，weapon 70/79）：
- we_death_pool_add（on_taken 收池 dmg×pool_pct 0.35）+ we_death_pool_pay
  （turn_start 结算 pay=pool×pay_pct 0.10 扣血）
- 池存 owner.ext.we_proc[pool_key]（serialize 保留续战不丢）

**N9A-2 act_done 通用广播 + randuin/ice_vein**（0906c30，weapon 72/79）：
- 鱼鱼拍板：不做专用 enemy_act，做**通用 act_done**——任何阵营行动完成都 fire
  （不带 ctx.actor 键 → subject=None 全员广播，刚行动的 actor 放 ctx["acted"]），
  效果侧自己 if 敌我判断（hostile_sides）。引擎零身份。
- randuin/ice_vein：STATE_EFFECTS 层 cap 3 + stat_scale spd 负值（-6%/-8% 乘算），
  we_act_done_slow 扩展动作叠层（自己/友方不叠，PVP 对手叠——按 side 判敌我）。

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

### A. weapon 缺口（还剩 7 个，N9A 方案已列）
| key | 缺的机制 | 状态/方案 |
|---|---|---|
| novice_first_turn_dodge | 闪避（battle2 无命中 roll） | N9A-3 战斗系统批（等命令层 N5b-4 后，N10 前） |
| novice_hunt_combo / combo_end | 连击/连段（拳师/刺客职业机制） | 记缺口等上层职业模块（勿半迁） |
| trinity_rhythm thunder 段 | 附雷附加伤害（atk_pct 段已迁，thunder_pct 未做） | N9A 方案未含，补译（damage 附加） |
| death_dance_armor 复活段 | 致死复活链（减伤段已迁 N9.13） | 复核 undying_will N9.12 是否覆盖同链 |
| vital_band 等 4 heal_amp | — | ✅ 非缺口（apply_to_actor 已装配） |

### B. affix 76 词条迁移（N9.7 批，未开始）
- stat 型 41（面板键）battle2 面板自动含，无需装配
- 事件型 ~35 走同管线（装配层加 affix_triggers：读 item["affixes"] → AFFIXES 表）
- 职业深度绑定词条（拳师气/牧师信仰/游侠精力/连段/攻线）→ 上层职业模块缺口清单

### C. N5b-4 命令层切换（施工图 docs/N5B_调用映射表.md 已备）
- combat.py 等 import 切换 + battle2_bridge.build_sides + EP.apply_to_actor(开战前装配)
- 之前约定"核心战斗文件等鱼鱼把关"——建议主 agent 出 diff 后鱼鱼过目再提交

### D. N10 删旧（最终验收"清干净"）
- 删除清单见 `docs/REFACTOR_v181P4_N9_migration.md` §4
- **前提**：weapon/affix 全部能力由 battle2 路径覆盖 + 命令层真实玩家跑通

---

## 4. 施工纪律（鱼鱼铁律，务必遵守）

1. 替换/大改前 `git status` 确认干净；出事先 `git checkout` 秒回，别在坏文件上硬修
2. 每块改完跑测试 + commit（v181.N9A.X 格式）再动下一块；全套绿是底线
3. 引擎零游戏知识：名词/条件/数值全在数据（weapon_effect_data/affixes/battle2_rules）
   与扩展动作——引擎只留动词执行器 + landing + config 查表 + 事件总线
4. 新效果接线 = 数据声明（triggers/STATE_EFFECTS/EFFECT_ACTIONS），不改引擎
5. 读表零默认值：缺字段 = 无此行为；数值权威 = 数据表 + we_data 覆盖
6. 不陪葬旧 bug：语义以 battle2 v2 定稿为准
7. 写生产库前必先 cp 备份 + dry-run（本阶段主要测测试库，无生产写）

---

## 5. 关键文件速查

| 文件 | 角色 |
|---|---|
| game/battle2/effect_triggers.py | 事件总线（EVENTS 22/fire/subject 过滤/_owner） |
| game/battle2/effects.py | 动词执行器 ACTION_HANDLERS（引擎 + 扩展共用注册表） |
| game/battle2/landing.py | 落地收口（death_guard/taken_calc/heal amp/on_taken dmg） |
| game/battle2/battle.py | Battle 主类（act() 尾部 act_done fire） |
| game/battle2/schedule.py | CTB 推进（限时 DOT/buff 到期） |
| game/data/battle2_rules.py | STATE_EFFECTS/EFFECT_ACTIONS（randuin/ice_vein 层声明在这） |
| game/services/battle2_equip_proc.py | 装配层（事件映射/翻译器/apply_to_actor） |
| game/services/battle2_we_procs.py | 族扩展动作注册中心（we_death_pool/we_act_done_slow/...） |
| tests/test_battle2_n9_equip.py | N9/N9A 验收（105 断言——加新 key 在此补用例） |

## 6. 会话重启第一步
读本文档 → `git log --oneline -8` 确认 HEAD → 剩余队列：B（affix）可自主开工 /
A 剩余记缺口 / C（N5b-4 需鱼鱼把关 diff）。每批 commit 后汇报鱼鱼。✂️
