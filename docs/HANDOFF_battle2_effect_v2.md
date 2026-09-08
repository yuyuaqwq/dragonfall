# battle2 效果系统 v2 交接（N8/N9 阶段）——开新会话必读

> 2026-09-08 交接。主线 = 效果系统 v2 + 装备特效族化迁移（wt_ebuffs 分支）。
> 鱼鱼验收北极星：**最后清干净——N10 删旧 battle.py + 旧效果系统三套注册表，
> 不留兼容壳/开关/兜底参数**（鱼鱼原话："老的一定要确保删掉，最后不留东西"）。
> 会话重启口令：「继续 battle2，读 HANDOFF_battle2_effect_v2.md 接着 N9」

---

## 0. 分支/位置/跑法

- 分支：`wt_ebuffs`（worktree：`C:/Users/yuyu/AppData/Local/Temp/df_wt_ebuffs/w1`）
- HEAD：`7264425`（v181.N9.14，2026-09-08）
- 主仓（生产）：`C:/Users/yuyu/qqbot/data/plugins/dragonfall`（master 未动）
- Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`
- 全套测试：`for f in tests/test_battle2_*.py; do python "$f"; done`（当前 433/433 绿）
- 覆盖率门禁：`python tools/cov_func_battle2.py`（0 未调用）+ `cov_branch_battle2.py`
- 效果系统主方案：`docs/DESIGN_effect_system_v2.md`（Part 3.3/4 定稿 19 时机 + 管线）
- N9 施工方案：`docs/REFACTOR_v181P4_N9_migration.md`（盘点/批次/删除清单）
- 旧三套注册表数据权威：`game/data/weapon_effect_data.py`（79 key 13 族全参数化）、
  `game/data/affixes.py`（76 词条）

---

## 1. 已完成（16 commit，全部绿，工作区干净）

### N7 效果系统收口（568399f 前，8 commit）
buff 数值动作参数化 / 绝对到期 / on_hit 消费 / DOT interval / 187 名词分诊 /
heal/state_set/interrupt/damage 动词补齐。动词全集：`control / buff / shield /
cleanse / cleanse_all / state_add / state_spend / heal / state_set / interrupt /
damage`。

### N8 事件总线（b98dc99 + d6ca06a）
- `game/battle2/effect_triggers.py`：fire(battle, event, ctx, logs) 唯一入口 +
  **EVENTS 21 时机**（19 效果时机 + dmg_calc/taken_calc 数值修正钩子）
- 效果源 = `actor["triggers"] = {事件: [效果 dict]}`；owner 注入 params._owner
- **事件主体过滤（N9.6 引擎语义修正，重要）**：ctx.actor = 事件主体，只处理主体
  声明（旁观者不误触发）；无主体事件（battle_start）全体；on_death 允许死者自身
- ctx 语义：caster 缺省=声明者；taken/heal 的攻击/治疗方放 ctx.source；_fire_ctx
  存事件全量（扩展动作读 dmg/amount/overflow/source/mult/tags）

### N9 装备特效族化（13 commit → weapon 69/79）
装配层 `game/services/battle2_equip_proc.py`（battle2 包外，引擎零知识）：
- 旧事件 → battle2 事件映射表（hit→attack_hit+skill_hit；**缺省同名直通**）
- key 翻译器（纯动词声明 / 扩展动作 we_xxx / 被动常驻）
- `apply_to_actor(actor)`：装配事件型到 triggers + 被动型（heal amp → state）
- 族扩展动作 `game/services/battle2_we_procs.py`（register_action 注册进引擎
  ACTION_HANDLERS——引擎当扩展动词执行，不 import 装配层）

**已迁武器族**（69/79）：
proc_buff 全 7（含 abyss maxhp 加成）/ proc_shield 13 全 / proc_dot 4 全 /
proc_reflect 5 全 / proc_extra_dmg 11 全 / proc_control 7 / proc_next_atk_mark 4
（trinity thunder 段缺）/ proc_retort_mark 4 / proc_heal amp 4 + regen 3 /
novice_dawn_mana / wind_mark / undying_will / death_dance_armor(减伤段) /
passive_mult twilight/star_slayer/arcane_firmament / 叠层放大器
rune_amp·sage_amp·eternal_codex·time_staff·thunder_weave / 首刻守御。

**引擎机制完善（本阶段重要成果）**：
1. fire 事件主体过滤（N9.6）
2. 限时 DOT（dot.turns 跳够清层）+ curhp DOT + boss 档（N9.5）
3. heal_down 收编 state 容器 / heal_amp_pct 受疗增幅（N9.6/11）
4. **death_guard 濒死保护**（N9.12）：STATE_EFFECTS 声明 cap/guard_hp_pct/heal_pct，
   landing 致死分支保底 + 层-1（鱼鱼 chat 拍板方案：state+声明表 而非事件钩子）
5. **dmg_calc/taken_calc 数值修正钩子**（N9.13，鱼鱼 chat 拍板）：
   伤害算出后/承伤时 fire，扩展动作改 _fire_ctx.mult 累乘 + tags

---

## 2. 效果系统心智模型（鱼鱼 2026-09-08 认可——设计一切效果对着拆）

```
引擎表达力 = 三原语 + 组合器 + 有限机制本体：

1. state + 声明表   → 数值状态/层数/资源/DOT/濒死保护（cap/stat_scale/dot/guard 全配置）
2. buff + 效果动词   → 带时限临时状态（到期时刻/数值快照；control/buff/shield/heal/damage...）
3. 事件钩子         → "何时触发"（fire 21 时机 → actor 声明执行）
4. 扩展动作（组合器）→ 条件/概率/多段逻辑放游戏侧注册进 ACTION_HANDLERS，
                     内部只调引擎 API（动词/landing/state）——引擎零名词知识

做效果 = 三个问题：什么时候？（事件钩子） 持续还是数值？（buff/state）
                有条件/概率/复杂链？（扩展动作）

⚠️ 做不了的是机制本体不在引擎的（闪避命中 roll / 连击入口 / 复活时序）——
   本体一旦有钩子，效果表达依然用三原语。
```

---

## 3. 剩余工作（按优先级）

### A. weapon 缺口机制（10 key，需设计后做——勿闷头拍，鱼鱼参与设计）
| key | 缺的机制 | 建议 |
|---|---|---|
| death_dance | 缓伤池 | 读旧 `game/battle.py _post_hp_lethal` 精确语义 → 扩展动作（on_taken 收池 ext + turn_start 扣池）大概率可全做 |
| novice_first_turn_dodge | 闪避（battle2 无命中 roll） | 战斗系统级：需先决定要不要给 landing 加 miss 判定 |
| novice_hunt_combo / combo_end | 连击/连段（追加攻击概率/连段活跃） | 职业机制级（拳师/刺客），可并入上层职业模块 |
| randuin_weary / ice_vein | enemy_act（敌人行动后事件点） | 引擎加事件 or 放弃（减速叠层） |
| trinity_rhythm thunder 段 | 附雷附加伤害 | hit 子键扩展 or damage 附加 |
| novice_first_turn_dodge / 闪避 | — | 同上 |

### B. affix 76 词条迁移（N9 施工方案 N9.7 批，未开始）
- 侦察结论：`E.player_final_stats` 已把词条 stat 属性折进面板（engine.py:417）→
  **stat 型（41 中面板键类）battle2 面板自动含，无需装配**
- 事件型 ~35 可走同管线（装配层加 affix_triggers：读 item["affixes"] 列表 → AFFIXES 表）
- ⚠️ 职业深度绑定词条（拳师气/牧师信仰/游侠精力上限、连段阈值、终结技、攻线限定）
  属**上层职业模块**（现状未建）→ 缺口清单记录，勿硬塞引擎
- 复用的现成能力：hit 事件 DOT/破甲/连击/元素附加；taken 回资源；turn_start 回复
  （regen 已迁示例）；battle_start 盾（shield 族示例）；dmg_calc 条件乘区（execute/破魔）

### C. N5b-4 命令层切换（施工图 docs/N5B_调用映射表.md 已备）
- combat.py 等 import 切换 + battle2_bridge.build_sides + EP.apply_to_actor(开战前装配)
- 之前约定"核心战斗文件等鱼鱼把关"——建议主 agent 出 diff 后鱼鱼过目再提交

### D. N10 删旧（最终验收"清干净"）
- 删除清单见 `docs/REFACTOR_v181P4_N9_migration.md` §4：battle.py /
  battle_mech.py / weapon_effects.py / _we_executors.py / affix_effects.py /
  BUFF_MULT 等；每删一块跑全量回归 + numeric 52
- **前提**：weapon/affix 全部能力由 battle2 路径覆盖 + 命令层真实玩家跑通

---

## 4. 施工纪律（鱼鱼铁律，务必遵守）

1. 替换/大改前 `git status` 确认干净；出事先 `git checkout` 秒回，别在坏文件上硬修
2. 每块改完跑测试 + commit（v181.N9.X 格式）再动下一块；全套 433 绿是底线
3. 引擎零游戏知识：名词/条件/数值全在数据（weapon_effect_data/affixes/battle2_rules）
   与扩展动作——引擎只留动词执行器 + landing + config 查表 + 事件总线
4. 新效果接线 = 数据声明（triggers/STATE_EFFECTS/EFFECT_ACTIONS），不改引擎
5. 读表零默认值：缺字段 = 无此行为；数值权威 = 数据表 + we_data 覆盖
6. 不陪葬旧 bug：语义以 battle2 v2 定稿为准（如 Boss 控制减半替代旧免疫退化）
7. 写生产库前必先 cp 备份 + dry-run（本阶段主要测测试库，无生产写）

---

## 5. 关键文件速查

| 文件 | 角色 |
|---|---|
| game/battle2/effect_triggers.py | 事件总线（EVENTS 21/fire/subject 过滤/_owner） |
| game/battle2/effects.py | 动词执行器 ACTION_HANDLERS（引擎 + 扩展共用注册表） |
| game/battle2/landing.py | 落地收口（death_guard/taken_calc/heal amp） |
| game/battle2/schedule.py | CTB 推进（限时 DOT/buff 到期） |
| game/data/battle2_rules.py | STATE_EFFECTS/EFFECT_ACTIONS（引擎 config 挂载） |
| game/services/battle2_equip_proc.py | 装配层（事件映射/翻译器/apply_to_actor） |
| game/services/battle2_we_procs.py | 族扩展动作注册中心（we_dot/reflect/extra_dmg/...） |
| tests/test_battle2_n9_equip.py | N9 验收（86 断言——加新 key 在此补用例） |

## 6. 会话重启第一步
读本文档 → `git log --oneline -15` 确认 HEAD → 选 A（weapon 缺口设计）或 B（affix）
开工。每批 commit 后汇报鱼鱼。✂️
