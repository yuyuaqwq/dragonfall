# v180-C 交接文档（随从 actor 化进行中 → 新会话开工用）

> 生成：2026-09-06 会话中断交接 | 代码仓 HEAD：aef825d（v180-C S1/S2），已推送 GitHub
> **更新：2026-09-06 深夜 S2 收尾完成（HEAD=f9f7dce）+ S3 方向重大调整（见文末 §七）**
> 用途：把 v180-C（召唤物/宠物 actor 化）当前进度 + 鱼鱼核心诉求 + 下一步交给新会话

## 〇、鱼鱼的态度（必须读，避免再被骂"太笨"）

1. **嫌我笨的根因**：我绕圈子说"宠物要复用效果表需要加 interval trigger 引擎扩展"——但 **v179 通用 tick 卡框架（鱼鱼亲手让做的）本身就是现成的周期触发机制**：
   `add_tick_effect(kind, actor, interval, data, uid)` 挂卡 → 到点调 handler → 返回 (logs, keep) 决定续排。
   宠物"每 N 刻做一次"直接挂卡就能跑。**我不该说"引擎不完善要加扩展"——是把现有框架没用起来。**
2. **鱼鱼方向**：
   - 召唤物/宠物 = **actor**（配数据被引擎认），不是单独一套代码
   - **不允许被攻击** → 加"不可被攻击"字段（untargetable）
   - **不在战场显示** → 加"不显示"字段（hidden）
   - **语义不固定全数据驱动**：宠物可能是 N 刻伤害 / 受击给效果 / 玩家行动后……触发时机和触发行为都是配置
   - 不要耦合进战斗引擎
3. **要求**：能优雅实现就用现有引擎机制（tick 卡）；不能优雅实现 = 引擎不完善（不是绕过）

## 一、已完成基线（全绿，勿重做）

代码仓 HEAD = aef825d（v180-C S1/S2），全部已推送 GitHub。
- **v180-B ① 状态容器统一（P10-P13）**：Battle 实例 22 个"玩家焦点字段"全删，战斗状态权威 = player actor dict（与怪同构）；引擎 actor 化完成；53 测试迁移；276/276 全绿
- **v180-B ② 挡刀配置化 + 控制免疫数据化 + side 化（P14）**：guard 数据化（召唤物/宠物实体带 guard 即挡刀）；霜狼套 '霜狼' 字符串特判 → class_sets bonus_5_ctrl_immune；_tgt_is_player/_m_slow/_m_interrupt 用 _is_focus_player
- **P15**：新增 test_numeric_actor_extensibility.py（随从 guard/宠物 guard/控制免疫/class_name actor 状态容器门禁，自动纳入数值门禁 → 45 文件全绿）；_monster_on_taken class_name 特判 → on_taken 字段驱动；_set_bonus_5_ctrl_immune 查表修复
- **v180-C S1/S2（aef825d）**：
  - `self.companions` 我方随从 actor 阵列（side/kind/buffs 就位）
  - `self.summons` 变 **property 兼容视图**（getter 过滤 companions 的 kind=="summon"；setter 整袋替换补 kind/side/buffs）
  - 召唤物实体生成带 actor 雏形：`side:"player", kind:"summon", buffs:{}` + `auto_act: {trigger:"player_act", act:{type:"basic_atk"}}`（atk>0 才有）
  - 三处召唤物生成点统一进 companions：_summon_entity（battle.py ~8920）/ potion_effects.eff_summon（L425）/ 测试
  - 通用触发点 `_companions_trigger(trigger, logs)`：扫 companions 带 auto_act.trigger==trigger 的逐个结算
  - `_companion_act(actor, logs)`：数据结算（现只支持 act.type=="basic_atk"；扩展分支留注释位）
  - player_turn 尾部改扫 companions（不再 self.summons 特判）
  - **`_summons_act` 保留为兼容壳**（转调 _companions_trigger("player_act")）——外部调用点/测试过渡用，**S2 收尾要删**
  - 实测：召唤物由 auto_act + 通用触发点正常出手/挡刀

## 二、进行中：v180-C S3 宠物 actor 化（刚被打断，还没写代码）

### 鱼鱼原话（2026-09-06）
> "语义不是固定的吧，看宠物技能的，有的宠物可能是玩家受击后给什么效果，有的宠物可能是N刻触发一次伤害"
> "这个宠物目前看应该做成buff貌似也可以，做成actor的话方便以后扩展，总之最好是数据驱动，不要耦合进战斗引擎"
> "召唤物就你看着来了，actor肯定要的"
> （打断时）"你等会" "总结你的任务，我要开新会话了"

### S3 设计方向（已侦察确认，未实现）
宠物 8 种 PET_POOL skill_type 行为（battle.py _psk_* handler，L150-214）：
| skill_type | 行为 | 应转 auto_act 数据 |
|---|---|---|
| atk_pct | 主人 atk × value 打敌 | act:{type:"dmg_owner_atk", pct} |
| matk_pct | 主人 matk × value 打敌 | act:{type:"dmg_owner_matk", pct} |
| heal_pct | 回主人 max_hp × value | act:{type:"heal_owner", pct} |
| lifesteal | 打敌+回主人伤害50% | act:{type:"lifesteal", pct} |
| pierce | 打敌+破防2刻 | act:{type:"pierce", pct} |
| buff_atk | 主人 atk_up buff 2刻（数值实读 skill_value，_pet_buff_vals 覆盖常量） | act:{type:"buff_owner", buff:"atk_up", turns:2, val} |
| crit_up | 主人 crit_up buff 2刻 | act:{type:"buff_owner", buff:"crit_up", turns:2, val} |
| block | 挡刀 | **guard 已做（②）**，不占 auto_act |

S3 要做：
1. `_companion_act` 扩展 act.type 分支（heal_owner/buff_owner/lifesteal/pierce/dmg_owner_*），照 _psk_* 原逻辑写数据结算——**不是新引擎逻辑，是把专用行为数据化进通用结算**
2. `_pet_ensure_actor`（类似 _pet_ensure_guard）：宠物参战时补 actor 字段 + auto_act（PET_POOL skill_type/skill_value/skill_interval → auto_act 数据）+ **untargetable:true + hidden:true**（宠物不可挨打、不进战场显示）
3. pet_act tick handler（_th_pet_act，battle.py L652 区）从"调 _pet_skill_turn"改成"读宠物 auto_act → _companion_act"
4. 删 `_pet_skill_turn` + PET_SKILL_EFFECTS 注册表 + 8 个 _psk_* handler（行为已数据化）
5. 鱼鱼说的"受击后给效果"宠物 → 未来配 trigger:"on_taken" + act.buff（引擎要加受击后扫 companions 的触发点——_damage_actor 玩家受击后）

⚠️ **关键提醒（鱼鱼点过的）**：tick 卡框架 v179 已有，宠物 interval 周期直接 add_tick_effect 挂卡就行。**别再说"引擎不完善需要加 interval trigger 扩展"——那是错的，框架现成。**

## 三、关键代码位置（S3 用）

| 位置 | 说明 |
|---|---|
| PET_POOL | game/data/pets.py（skill_type/skill_value/skill_interval/spd 定义源） |
| 8 个 _psk_* handler | battle.py L150-214（行为参照，S3 数据化后删） |
| _pet_skill_turn | battle.py ~7665（专用分发，S3 删） |
| _th_pet_act | battle.py ~651（pet_act 卡 handler，S3 改读 auto_act） |
| _pet_ensure_guard | battle.py ~7670（②加的，S3 扩展成 _pet_ensure_actor） |
| _pet_interval_sec | battle.py ~7711（skill_interval → 秒，interval 卡周期） |
| _companion_act | battle.py ~8985（S2 加的通用行为结算，S3 扩展分支） |
| _companions_trigger | battle.py ~9020（通用触发点） |
| _pet_block_check | battle.py ~7730（guard absorb 挡刀，②已数据化） |

## 四、S2 收尾遗留（召唤物侧）
- `_summons_act` 兼容壳要删：外部 2 调用点（player_turn 已改通用触发；另 1 处在哪需 grep `_summons_act`）改成直接 _companions_trigger
- `_pick_summon_target` 被 _companion_act 用（保留作通用选目标或收敛 formation）
- **测试迁移坑**：所有 `b.summons.append(...)` 测试代码已失效（summons 是 property 只读视图）——要改 `b.companions.append`（test_v107_summon L110 已改样板；v107_mech/v107_skills/v113/v114 读 `b.summons[0]` 是引用实体改字段，能生效不用改）

## 五、坑/注意（铁律）
1. 改引擎前 git status 确认 tracked 干净；每块改完跑测试+提交
2. 全量回归必须 `run_all_tests.py --jobs=16`（现 277 文件基线），0 红底线；数值门禁 45 文件全绿
3. **test_v116 偶发 flaky**（多次跑 0 失败，非引擎 bug，重跑确认即可）
4. `self.summons` 已是 property——**任何 `x.summons.append` 都会静默无效**（append 到副本），必须操作 companions
5. 身份判定不用 class_name 判玩家/怪 → _is_focus_player/side
6. 测试直接调引擎方法（不经 player_turn）from_state 产物需 b.player=测试player + _apply_restore_pstate()
7. 工作区大量 ?? 未跟踪是历史遗留（tests/auto_tune*.py、scripts/_tmp_*.py 等），别提交
8. 双仓：代码仓 git@github.com:yuyuaqwq/dragonfall.git 已推送 aef825d；策划案仓 design/new_world 未推

## 六、设计文档存档（workspace/boss_design/）
- v180C_companion_actor_design.md：随从 actor 类型化设计（S1-S5 分步，auto_act 数据驱动格式已定稿）
- v180B_stage2_design.md / v180B_stage2_feasibility.md / v180B_focus_fields_reference.md：B 层文档
- v180B_test_migration_guide.md：测试迁移规则

## 七、【深夜更新】S2 收尾完成 + S3 方向重大调整（2026-09-06 深夜）

### 已完成（HEAD=f9f7dce，全量 278/278 绿 + 数值门禁 45/45 绿）
1. **S2 收尾·删 `_summons_act` 兼容壳**（39e7132）：player_turn 已走通用触发点，测试迁移 `_companions_trigger`
2. **S2 收尾·装配统一**（f9f7dce）：
   - 新增 `_spawn_companion(cfg, player, logs)` 单一装配函数（技能/药水召唤共用）
   - 药水召唤 bodyguard → guard（修复 P14 后烬灵不挡刀回归，现按 0.30 精确挡刀）
   - 召唤药水 effect_data 显式补 hp/def（辅助型不普攻，配置驱动零隐藏默认——鱼鱼铁律）
   - 新测试 `tests/test_v180c_summon_unify.py`（29 断言行为等价锚）

### S3 方向重大调整（鱼鱼 2026-09-06 深夜新拍板）
> 鱼鱼原话方向：宠物需要**新增不在战场显示的 actor**（hidden+untargetable），继承部分属性，
> 目的是**伤害隔离**——宠物打伤害不该吃玩家吸血/暴击/命中触发效果。

**格温深夜实证发现 bug（需鱼鱼醒来决策，勿擅自动刀）**：
- 宠物伤害走 `_damage_enemy` 被玩家被动乘区污染：敌挂猎印 5 层 → 宠物撕咬 197→254（+29%）
- 根因：`_damage_enemy`（battle.py ~8754）v169.7 乘区无条件读 `self.player` 被动（猎印/魂标/破绽/挽歌），不看攻击者 source
- **召唤物同样吃玩家乘区**（非玩家主体伤害归属是通用问题，不止宠物）

**⚠️ 待鱼鱼决策（详见 `workspace/boss_design/v180C_S3_decision_brief.md`）**：
- 决策 A：非玩家主体（宠物/召唤物）伤害该不该吃玩家被动乘区？（格温倾向 A1 不该吃）
- 决策 B：宠物 actor 化怎么做？（格温建议 B2 先修身份判定，未来要被打再 actor 化）
- 决策 C：归属判定机制（source 参数 vs actor 身份字段）

### v180-D 效果系统统一（新立项，鱼鱼拍板）
- 设计文档：`workspace/boss_design/v180D_effect_system_unify_design.md`（v2）
- 核心：效果 = 执行器（代码唯一）+ 声明（来源数据各自写）；数值权威留各来源
- P1 效果执行器 + 宠物试点（**与 S3 决策耦合，先定再动**）→ P2 affix/food 同语义 8 效果合并 → P3 推广
- affix/food 重复实测：bleed/armor_break/combo/pierce/element_fire/ice/charge/dragon_tongue 相似度 0.28-0.73

### 复现实证脚本
`workspace/_diag/_diag_pet_isolation.py`——跑：宠物撕咬 敌挂猎印5层 197→254

### 【深夜续更】S3 伤害隔离已修（HEAD=db309f9，勿重做）
**鱼鱼拍板方向**：宠物需 hidden actor 隔离伤害（不吃玩家吸血/暴击/命中触发效果）。

**格温实现**：`_damage_enemy` 加 `player_atk` 参数（默认 True）；宠物 `_pet_skill_dmg`
传 `player_atk=False` → 跳过 v169.7 玩家被动乘区段（猎印/魂标/破绽/挽歌）。
- 实证修复前：敌挂猎印5层宠物撕咬 +29% 白嫖；修复后多轮均值 diff 0.0%
- 对照：玩家本人攻击仍吃乘区（+39.8%）——未误伤
- 门禁：`tests/test_v180c_pet_isolation.py`（4 断言）；全量 279/279 + 数值 45/45 绿
- **召唤物暂未改**（v169.7 后一直吃玩家乘区，可能是召唤流平衡一部分——待鱼鱼定）

**格温判断（待鱼鱼确认）**：player_atk 已达成隔离，**宠物完整 actor 化（hidden companion）
暂缓**——宠物 16 种/序列化/命令层大改只换来"将来可被打"（而 untargetable 明确不要被打），
属过度工程。若鱼鱼仍要 actor，再按 S3 设计收编 companions。召唤物是否也隔离待定。

### 【深夜续更 2】S3 宠物 actor 化完成（HEAD=9c01d2c，勿重做）
鱼鱼明确 actor 化不能缩水。已做：
- `_pet_ensure_actor()`：宠物参战补 side/kind/buffs + hidden/untargetable 进 companions（3 挂点幂等）
- `_damage_enemy` 加 `attacker` 参数（谁攻击吃谁的被动）——宠物传自己 → 乘区读宠物自身被动
  （无被动=无加成），玩家传自己照吃。语义实证：宠物吃标记基础+40% 不吃自然之眼+0%；
  玩家吃标记+40% + 吃自然之眼+21.5%
- Lv10 解锁收敛 `PET_SKILL_UNLOCK_LV` 数据常量（pets.py，原 6 处硬编码全清）
- 门禁 `tests/test_v180c_pet_isolation.py` 10 断言；全量 279/279 + 数值 45/45 绿

### 【深夜续更 3】v180-D P2 affix/food 效果合并完成（HEAD=518ee95，勿重做）
- 新建 `game/core/effect_actions.py`：11 个共享效果动作（dot/def_down/bonus_pct/
  element_dmg/pierce_dmg/counter/mark/regen_hp/regen_mp/lifesteal）
- affix_effects.py + food_effects.py 的 11 个重叠 handler 全改薄（只留触发判断+数值）
- 修 bug：affix combo/charge/element 附加伤害原本绕过 Boss 护盾（food 有过滤 affix 漏了）
  → 统一走 _boss_dmg_filter
- 文案规范化：affix "ice属性附加"半英文 → "冰霜附加"（测试断言同步）
- 全量 279/279 + 数值 45/45 绿

### 下一步（等鱼鱼醒来/审计结果）
- P3：宠物 8 skill_type 效果是否收编 companions actor 通用路径（_pet_skill_turn 还在用
  PET_SKILL_EFFECTS 注册表，与 actor 化并存——审计子 agent 查残余专用路径）
- P4：审计出的硬编码/设计不良清理

### 【深夜续更 4】战斗引擎 4 子 agent 审计完成 + P0/P1 修复（HEAD=e46bb8c）
**4 并行子 agent 只读审计完成**，报告存 `workspace/boss_design/audit_20260907/`：
- audit_damage_identity.md（伤害/身份/治疗双轨）
- audit_effect_system.md（效果重复/硬编码/数据断链）
- audit_state_serialization.md（序列化/容器一致性）
- audit_companion_actor.md（随从 actor 残余专用路径）
- AUDIT_SUMMARY.md（汇总 + 修复清单 + 待决策）

**已修复提交**：宠物被误删/误牺牲(8bd86ea)、等级压制 attacker 化+true 分支统一(2d91bc0)、
potion def_down 收敛(9a5cc06)、last_element 序列化(e46bb8c)。全量 279/279 + 数值 45/45 绿。

**🔴 待鱼鱼拍板的 P0 效果错误**（审计1 §2.2，数据声明 vs 代码行为脱钩）：
1. mortal_wound 代码 50% 禁疗 vs desc 30%
2. memory_tear 数据"沉默"vs 代码"降攻"
3. arcane_echo/sanctum_light 写了没人读（白板装备）
4. element_thunder 等词条附加伤害绕 Boss 护盾
5. DOT 死字段（handler 写 pct/turns 引擎不读）

**🟠 结构性重构建议**（见 AUDIT_SUMMARY §四）：_heal_actor 统一治疗核心 / 宠物技能收编
auto_act / 挡刀双轨统一 / weapon_effects 数值下沉 / calc_damage 收敛 / tick actor_ref
