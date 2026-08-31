# v151 引擎差距侦察报告

> 侦察范围：`C:/Users/yuyu/qqbot/data/plugins/dragonfall`（只查不改）
> 依据：`docs/CLASS_MECHANICS_REDESIGN_v151_FULL.md`（§0.3/§7/§10）+ 任务卡
> 铁律：每条证据带 `文件:行号`；grep 定位，未整读大文件。

---

## 1. mech_stacks 现状（✅ 机制存在，泛化可用，但缺 v151 新键注册）

**结论：mech_stacks 是现成的玩家侧叠层容器，序列化/持久化/条件判定全链路已有，v151 的「战意/连段」可直接落，但 0-10 上限/白名单需要新注册。**

- 容器定义：`game/battle.py:303`（`self.mech_stacks: dict = {}`，v59 分支机制叠层，随战斗持久化）；property 读写 `game/battle.py:484-492`
- 序列化：to_state `game/battle.py:520` / from_state 恢复 `game/battle.py:577`
- 叠层封顶工具：`game/engine.py:138-141`（`mech_stack_gain`，上限查 `MECH_STACK_MAX`）；上限表 `game/engine.py:121-135`（burn/poison/rage/shadow/chi/judge/mark/wind/iron/shield/bless/arcane/spellblade——**没有 will/战意 键**，未注册键走默认 cap=99）
- 每层增伤查表：`game/data/battle_config.py:29-37`（MECH_STACK_BONUS：rage/shadow/chi/spellblade/dragon_might/zen）
- 增益技能叠层白名单：`game/data/battle_config.py:39-46`（MECH_STACK_WHITELIST 14 键）
- 条件判定：`game/core/battle_conds.py:203-206`（`player_mech_stacks`：自身任意 mech 键 ≥N，**战意≥N 可直接用**）
- 现用叠层键实例：echo（battle.py:989/1328-1338）、combo（battle.py:1155-1201）、arcane/spellblade 自动充能（battle.py:5168-5179）、dragon_mark（battle.py:3152 + affix_effects.py:217）、wind_mark/thunder_weave（battle.py:2371/2378）、novice_spark（battle.py:2506-2508）、iron 金身（battle.py:5952-5958）
- 副本按玩家持久化：`game/commands/instance.py:1533/1570/1601`（初始化）、`:2204`（恢复）、`:2235`（写回）、`:2479`（切怪清空）
- 旧档迁移兼容：from_state 把旧 mech_stacks 里的 poison/burn/mark 迁到 enemy debuffs（battle.py:610-623）

**v151 差距**：
- 战意（0-10）无专用键：`MECH_STACK_MAX` 无 `will`（engine.py:121-135），`MECH_STACK_WHITELIST` 无 will（battle_config.py:39-46）——需注册或靠默认 cap 99 手动 min
- 战意「持有即生效、不消耗」语义：现有 `_mech_stack_bonus`（battle.py:4043-4068）按持有层数动态结算，天然契合，但只查 `MECH_STACK_BONUS` 表——需给 will 加表项
- 连段 combo（0-10）：已有完整实现 `battle.py:1148-1201`（_combo_add/_combo_break/_combo_dmg_mult，COMBO_CFG cap 10 在 battle_config.py:169-176）——**v151 刺客连段可直接复用**；但 skills.py:2768 的 `combo_cond` 字段在 battle.py 无任何消费点（死字段，链刃 +10% 未实装）

---

## 2. enemy_buffs / 敌身挂账现状（⚠️ 双轨并存：e_buffs 旧轨 + enemy.debuffs 新轨；enemy_buffs 名字不存在）

**结论：没有叫 `enemy_buffs` 的东西。敌身状态实际分两轨：① `battle.e_buffs`（= enemy["buffs"]，回合计数 buff/控制/印记）；② `enemy["debuffs"]`（目标级层数型减益：毒/灼烧/标记/流血 + 元素印记）。v151 的「印记/破绽/标记挂敌身」两条轨都已有雏形，但破绽 shaken 只接了一半、curse/soul_mark 是纯死配置。**

- e_buffs 是 enemy["buffs"] 的兼容代理：`game/battle.py:466-472`；序列化 `battle.py:516`
- 目标级 debuffs：`game/core/battle_mech.py:97-151`（burn 叠层/读取/清）、`:232-256`（mark 叠层/爆发，e_buffs["mark"]=DEBUFF_TURNS 计时保留）、`:203-223`（净化）、`:400-464`（poison）
- DOT 五律结算：`game/battle.py:4745-4920`（阈值递增/每场上限/跨阶段保留/真伤/饱和收敛）；`_tick_dots` 在 `_turn_start` 调用 `battle.py:5064-5075`
- 跨阶段保留：`battle.py:4961-4986`（_preserve_debuffs 50% 层数）；调用点 battle_mech.py:619-631（_b_phase）
- 标记易伤消费：`battle.py:4678-4692`（_apply_mark，每层 +20%）；普攻 battle.py:2525、技能 battle.py:3809
- 标记判定放宽（词条追猎）：battle.py:3119-3125（e_buffs["mark"] 或 debuffs.mark 任一）
- 状态栏展示：`game/commands/combat.py:1540-1610`（_DEBUFF_NAMES 毒/灼烧/标记/流血 + e_buffs 表 1523-1537）

**破绽 shaken（挂敌身条，v139 已有）**：
- 通用挂敌身条纯函数：`game/core/battle_bars.py:56-158`（bar_def/bar_state/bar_gain/bar_should_trigger/bar_trigger/bar_tick/bar_preserve）
- 配置：`game/data/battle_config.py:373-388`（ENEMY_BAR_CFG.shaken：max 50/衰减 4/阈值 50×1.35 递增/免疫 1 回合/trigger_effect skip_turn）
- 注入点：`game/battle.py:3980-3994`（技能 info.shaken_gain → bar_gain + bar_trigger，触发后「破绽值满！敌人被震慑」）
- 技能数据：skills.py:1091（三连击破 +15）、:2978（旋风踢 +5）、:2991（碎颅势 +15）、:3261（无影连打 +3）
- 条件：`game/core/battle_conds.py:91-99`（enemy_shaken_gt 破绽/震慑中）

**v151 差距（关键）**：
- **bar_tick / turn_start_bars 从未被 battle.py 调用**：`game/core/battle_bars.py:276-288`（turn_start_bars）全库唯一引用是注释 `battle.py:5292`——破绽的「每回合衰减 4/免疫期递减」实际不跑，`_end_round` 只对 int 值 -1 且跳过 dict（battle.py:5287-5296）；shaken 的 immune_turns/decay 形同虚设
- **「被震慑跳回合」无消费端**：trigger_effect=skip_turn 只在注释/配置里（battle_config.py:383），battle.py `_enemy_turn`（4307-4360）只有 freeze/stun/sleep 跳过分支，**没有读 shaken.immune_turns 跳过敌方回合**
- curse/soul_mark（暗影神谕）是死配置：classes.py:581-591 + battle_config.py:391-404 有定义，但 `curse_apply`/`soul_mark_on_summon`/`soul_mark_per_skeleton`/`bone_tide`/`consume_skeletons`/`curse_dmg_mult`/`curse_bonus` 这些技能字段（skills.py:3649/3661/3677/3689/3732-3733）在 battle.py/battle_mech.py/battle_conds.py **零消费**（全库 grep 命中仅在 data/ 三个文件）——v151 若沿用幽祷线需补消费端
- v151 破绽 0-50 推满跳回合：bar 机制方向对，但 max=50 且阈值=50 意味着「推满即触发」与 v151 一致，需修上两条断链

---

## 3. core_resources 消费点清单（要废弃资源条需改的全部触点）

**结论：CORE_RESOURCES 资源条深度耦合战斗主流程，v151「废弃 12 资源条」不是删一个文件，而是要动 battle.py 资源管线 + engine 工具 + 数据表 + 命令层展示。逐项列出：**

### 3.1 数据层
- `game/data/core_resources.py:28-254`：CORE_RESOURCES 表本体（cls_zhan_shi rage / cls_fa_shi element / cls_you_xia energy / cls_mu_shi faith / cls_ci_ke cp / cls_wu_seng chi / 隐藏线 dragon_oath/chronomancer/wild_hunter/hymn/shadow_blade/wu_sheng + 副资源 resonance/echo/vow）
- `game/data/battle_config.py:212-219`：BRANCH_RESOURCE_OVERRIDE（分支资源覆盖：法师 element、歌者 resonance+echo）
- `game/data/__init__.py:204`：导出 CORE_RESOURCES

### 3.2 engine 工具（game/engine.py）
- `core_resource_def` :57-61 / `core_resource_def_by_key` :63-69 / `core_resource_gain_key` :71-79 / `core_resource_gain` :81-90 / `core_resource_spend` :93-103 / `core_resource_regen` :106-115

### 3.3 battle.py 资源管线（主战场，~40 处）
- 容器：`self.resources` battle.py:306；序列化 :521/:578
- 读写工具：`_res_read` :673-677 / `_res_gain` :679-709 / `_res_spend` :712-724 / `_res_gain_class` :726-758 / `_res_max` :871-874 / `_res_affix_max_bonus` :847 / `_set_res_max_bonus` :2918
- 初始化：`_init_resources` :974-1008（按 _branch_keys 预充，element→element_charge 双槽、energy 满 100、echo→mech_stacks）
- 展示：`_resource_label` :1051-1089（战况条显示资源）；`_rage_full` :877-878
- 获取渠道：`_resource_on_attack` :2623-2650（on_attack/on_hit/暴击）/ `_resource_on_skill` :2655-2731（on_skill/res_gain dict 副资源/on_heal）/ 受击 :6086-6095 / 闪避 on_dodge_success :5719 / 回合自然回 :5186-5196 / 战前预充 :1010-1040 / 套装/词条 res_gain :2895-2912 / 受击被动 :5850-5863 / 反击 :5930-5934
- 消耗/校验：`_do_player_skill` 预检 :1973-1998、`_pre_cost_res` 快照 :2040、扣费 :2076-2094、consume_all 动态威力 :2046-2075、电荷制蓄力扣 charge_cost :2123-2146、治疗脱战校验 `game/commands/combat.py:1002-1009`
- 条件/倍率联动：`_cond_mult` 读 COND_CHECKS（battle.py:4092-4106）、`_mech_stack_bonus` res_cost 每层加成 :4053-4068、终结技判定 :2932-2968、神迹档位 :2964-2975、满弦精力 :1251-1257、连击点返还 :2769-2781
- v139 模式机：dual_form 维持扣资源 :5229-5231 / vent 排气 :5240-5244 / focus 额外资源 :5250-5255
- 杂项：元素切换字符串槽 resources["element"] :984-986/:3561/:3932、combo_ready 标记 :3702/:3945、受击清空 :6094-6096

### 3.4 条件层
- `game/core/battle_conds.py:181-200`：`player_res_stacks`（读 battle.resources——**这是资源条语义的条件**，v151 废弃后此 cond 及 skills.py 里 8 处使用点（55/662/1460/2463/2941/3253/3421/3509）都要迁到 player_mech_stacks）
- `game/core/battle_conds.py:287-290`：被动条件 `rage>=5`（读 resources）

### 3.5 命令层（展示/技能面板）
- `game/commands/combat.py:1617-1624`：`_resource_line` 战况资源条显示
- `game/commands/player.py:31-32`：`_RES_CN` 资源名映射；`:1288-1295` 技能详情 res_cost 行
- `game/commands/job_guide.py:17/:102-105`：职业指南读 CORE_RESOURCES desc
- `game/commands/_registry.py:101`：job_guide 数据源依赖
- `game/commands/instance.py:214/:2211/:2260/:2865/:2891`：副本按玩家持久化 resources

### 3.6 其他 core 模块
- `game/core/battle_mech.py:940-943`：元素跃迁改 resources["element"]
- `game/core/battle_modes.py:54-407`：dual_form/focus/vent 状态机（资源值由调用方 battle.py 传入，见注释 :144「实际扣资源由调用方执行」——**纯函数层可保留，改 battle.py 调用点即可**）

**v151 影响面评估**：废弃资源条 = ① skills.py 全部 res_gain/res_cost（97+122 处，见 grep 统计）改 mech_stacks/enemy_buffs 语义；② battle.py 上述 ~40 触点改读叠层；③ player_res_stacks/rage>=5 条件改道；④ 命令层 4 处展示改道。**其中 energy（游侠精力）是最大耦合点**（电荷制 battle.py:2123-2146、满弦 :1251、自然回 :5186 全挂它）。

---

## 4. cond 条件清单（v151 需要的有没有）

**结论：28 个注册条件（battle_conds.py:34-243）。v151 的「战意≥N」「印记层数」「连段≥N」全都有通用/现成实现；缺的是「敌身印记层数」读新轨（现读旧轨 e_buffs）与「敌身条数值条件」（如破绽值≥N）。**

注册表（`game/core/battle_conds.py`，register 装饰器 :21-27，COND_CHECKS :17）：
- 血量类：enemy_hp_low :34 / player_hp_low :40 / enemy_hp_high :46 / player_hp_high :52 / enemy_full_hp :58
- 敌方状态类：enemy_frozen :66 / enemy_stunned :72 / enemy_silenced :78 / enemy_poison_stacks :84 / enemy_shaken_gt :91 / enemy_marked :123 / enemy_debuff :129 / enemy_slowed :141
- 元素印记：`element_marks` :147-159（**读 battle.e_buffs 的 fire_mark/ice_mark/thunder_mark——旧轨**；v151 印记落 enemy["element_marks"] 后此 cond 需改读 _elem_marks）
- 自身类：player_rage_form :104 / player_stance :111 / player_shield :161 / player_spd_up :169 / player_chi_stacks :175 / **player_res_stacks** :181（资源条语义，见 §3.4）/ **player_mech_stacks** :203（通用「自身 mech 键 ≥N」——战意≥N 直接用）/ player_buffed :209 / player_untouched :215 / player_combo（上一招）:222 / player_first :235 / speed_ratio :243
- 连段：**player_combo_stacks** :117-121（链值 combo ≥N——v151 连段≥N 现成）
- 被动条件表：PASSIVE_COND_CHECKS :260-268（rage>=5 :287-290 / hp_low_50 / hp_high_70 等）

**v151 差距**：
- 「战意≥N」→ 用 `player_mech_stacks`{mech:"will"} 即可（battle_conds.py:203），但需先注册 will 键进 MECH_STACK_MAX/WHITELIST
- 「印记层数≥N」→ `element_marks` 已有（:147），但读旧轨 e_buffs；需加读 `enemy["element_marks"]`（battle.py:1263-1272 的 _elem_marks 存储轨）的分支
- 「连段≥N」→ `player_combo_stacks` 现成（:117）
- 「破绽≥N」（v151 拳师推条场景）→ 无现成 cond 读 shaken bar 的 val 数值（enemy_shaken_gt :91 只判触发态 trigger_count/immune_turns）；需新增读 `buffs["shaken"]["val"]` 的条件
- cond 消费点：`_cond_mult` battle.py:4092-4106 / `_cond_active` :4108-4116，均走 COND_CHECKS 注册表，**新增条件零改动 battle.py**

---

## 5. 元素反应现状（✅ 反应表+双轨印记全实现，引爆技 cond 未接线）

**结论：蒸发/超载/冻结/感电反应表完整落地，且已有「目标侧 element_marks（0..3）+ 反应表」的新轨实现——v151 法师元素印记基本可直接用，缺的是技能数据侧接入引爆技（cond type='reaction' 目前零技能使用）。**

- 反应表：`game/data/battle_config.py:135-143`（REACTION_TABLE：(fire,ice)蒸发 1.30 / (fire,thunder)超载 aoe / (ice,thunder)冻结 freeze / (thunder,ice)感电 chain；clear 规则齐全）
- 印记上限：`game/data/battle_config.py:128-131`（ELEMENT_MARKS_MAX=3 / ELEMENT_MARK_GAIN_PER_HIT=1）
- 旧轨（e_buffs 印记）：engine.py:25（ELEMENT_MARKS 映射）/ :34-46（element_reaction 判定）/ :48-53（element_mark_apply）；battle.py:3630-3658（技能命中按当前系×e_buffs 印记查反应，超载 AOE/冻结/感电连击/清印）
- **新轨（目标侧 element_marks，v151 同构）**：battle.py:1262-1307（_elem_marks 读 enemy["element_marks"] / _elem_mark_apply 上限 3 / _elem_mark_max 词条 +1 / _elem_marks_total）；命中登记 battle.py:3917-3918；引爆结算 `_reaction_table_resolve` battle.py:1351-1390（按引爆系×目标印记查 REACTION_TABLE，返回 mult/日志/chain_flag）
- 引爆技挂点：battle.py:3659-3669（info.cond.type=="reaction" 时调 _reaction_table_resolve）——**但全库无技能带 cond reaction**（grep 仅 skills.py:378 passive proc "reaction"（元素共鸣 +15% 被动）与 items_add_v140.py:89 元素共鸣石药水 effect=reaction，后者经 potion_effects.py:672 eff_reaction 消费）
- 反应催化：battle.py:1393-1402（_reaction_catalyst_mult 词条 +15%）；元素共鸣石：potion_effects.py:672-690
- 印记生命周期：`_end_round` 豁免递减 battle.py:5270-5274（fire/ice/thunder_mark 不清回合，由反应 clear 或战斗结束清除）
- 同系连发：battle.py:1310-1322（_last_element_set，第二次同系 +1 充能）
- 印记词条消费（雷印条件等）：affix_effects.py:409-436（cond_thunder_mark/cond_thunder_ge2/consume_thunder）

**v151 差距**：
- 无任何技能数据接 cond type='reaction'（引爆技入口 battle.py:3661 空转）——v151 法师引爆技需在 skills.py 数据侧挂 cond
- 旧轨 e_buffs 印记（battle.py:3917 仍在写）+ 新轨 element_marks（:3918 同时写）双写并存，v151 废弃资源条时建议收敛到新轨
- `element_marks` cond（battle_conds.py:147）只读旧轨 e_buffs，见 §4

---

## 6. 召唤物现状（⚠️ 系统完整，但 v151 §7 属性表对不上 + 缺「纯挡刀/吃AOE」语义）

**结论：召唤物系统 v107 已全链路（模板→生成→自动攻击→挡刀→死亡契约→序列化），v151 §7 的骷髅/藤蔓/古树三类都已有模板，但数值比例与行为语义需按 v151 改。**

- 模板表：`game/data/summons.py:17-39`（skeleton 骷髅 / vine_guard 藤蔓守卫 / treant 古树守卫；字段 atk_ratio/hp_ratio/def_ratio/dmg_type/limit/bodyguard/rank/reach）
- 生成：`game/battle.py:5519-5544`（_summon_entity：按玩家实时属性比例缩放 ×(1+summon_power)，limit 上限拦截）
- 自动攻击：`game/battle.py:5546-5573`（_summons_act：玩家行动后每只打一次，按 dmg_type 走 calc_damage，真伤绕过减伤；死亡清理）
- 选目标：`game/battle.py:5575-5577`（_pick_summon_target → formation.select_target :34-67，按 reach 射程内最前排）
- 挡刀：`game/battle.py:5622-5652`（_summon_block_check：bodyguard 概率 ×(1+sp) 上限 85%，按召唤物自身 def 结算，挡刀后死亡移除）；调用点 `_damage_player` :5684
- 死亡契约：`game/battle.py:6062-6067`（death_pact 被动，致死时牺牲 1 召唤物 20% HP 存活，每场 1 次）
- 技能挂载：skills.py:1930（召唤藤蔓守卫）、:2162（召唤古树守卫）、:3646/:3674/:3685（召唤骷髅/墓穴低语/骷髅海）；召唤在技能结算前执行 battle.py:3468-3470
- 强化属性 summon_power：engine.py:226/:258/:321/:358（属性通道 + 面板显示「召唤强化」）
- 序列化：to_state :515 / from_state :573（summons 随战斗持久化）
- 亡灵计数（联动悼咏/灵魂标记）：battle.py:2879-2889（_undead_count 数存活骷髅）

**v151 §7 差距（对照 docs/CLASS_MECHANICS_REDESIGN_v151_FULL.md:686-704）**：
- 骷髅：v151 = 主人 HP×0.30 / ATK×0.40 / 上限3；现状 = hp_ratio 0.35 / atk_ratio 0.50（summons.py:21）——比例需改
- 藤蔓守卫：v151 = HP×0.25 / **ATK 0（纯挡刀，替队友吸收 1 次单体后消失）** / 上限2；现状 = atk_ratio 0.45 会普攻（summons.py:28）+ bodyguard 概率挡刀（非「吸收 1 次即消失」）——**行为语义需新增「纯挡刀+单次吸收」类型**
- 古树守卫：v151 = HP×0.50 / ATK×0.30 / 上限1 / 挡刀+全队攻+30% 光环；现状 = hp_ratio 0.55 / atk_ratio 0.75 / limit 1（summons.py:35-36）——比例需改；光环需新增（现有古树靠技能 effect=atk_up 施放当回合给，非常驻光环）
- 三条铁律：① 召唤物死亡不清主人状态 → 现状天然满足（召唤物是独立实体 battle.py:5538-5540）；② 继承主人减伤、不继承暴击/暴伤 → 现状挡刀按召唤物 def 自结算（:5640-5644），自动攻击走 E.calc_damage（:5563-5567），**未实现继承主人减伤乘区**；③ Boss AOE 清场骷髅/单点杀只耗一次出手 → 现状召唤物不吃 AOE（无 AOE 清召唤物逻辑），**需新增**

---

## 7. 结论：v151 落地需要的引擎改动清单（按文件分组）

### game/core/battle_bars.py（破绽条断链修复）
1. `turn_start_bars`（:276-288）需在 battle.py `_turn_start`（:5064）或 `_enemy_turn`（:4307）接线——当前全库零调用，bar_tick 衰减/免疫期递减不生效
2. 触发效果消费端：`_enemy_turn` 需新增 shaken.immune_turns>0 时跳过敌方回合分支（对齐 freeze :4336/stun :4341 分支）；trigger_effect=skip_turn 目前只是配置注释（battle_config.py:383）

### game/battle.py（核心改动）
3. 资源管线迁移：§3.3 的 ~40 处 resources 触点（_res_gain/_res_spend/_res_gain_class/_resource_label/_init_resources/_resource_on_attack/_resource_on_skill/预检扣费/consume_all/电荷制/dual_form 维护/vent/focus/自然回/受击回）改为读 mech_stacks/enemy_buffs
4. mech_stacks 注册：will（战意）键进 `MECH_STACK_MAX`（engine.py:121）与 `MECH_STACK_WHITELIST`（battle_config.py:39）、`MECH_STACK_BONUS`（battle_config.py:29）——战意「持有即生效」走 _mech_stack_bonus（:4043）自动成立
5. combo_cond 消费：skills.py:2768 的 combo_cond（链刃 +10%）在 _player_skill/_do_player_skill 无消费端——v151 连段若保留需补（或并入 _combo_dmg_mult :1193）
6. 召唤物：_summon_entity（:5519）支持 v151 比例（读模板即可改数据）+ 新增「纯挡刀单次吸收」类型（藤蔓）+ AOE 清召唤物分支（铁律③）+ 召唤物继承主人减伤（铁律②）
7. 旧轨印记收敛：battle.py:3917（写 e_buffs 印记）与 :3918（写 element_marks）双写，v151 建议只保留新轨

### game/data/（数据层）
8. `summons.py:17-39`：三模板数值按 v151 §7 表改（骷髅 0.30/0.40、藤蔓 0.25/0、古树 0.50/0.30 + 光环字段）
9. `battle_config.py`：MECH_STACK_MAX/WHITELIST/BONUS 加 will；ENEMY_BAR_CFG.shaken（:373-388）阈值对齐 v151 0-50 推满跳回合；curse/soul_mark 配置（:391-404）要么删除要么补消费端
10. `core_resources.py`：废弃后 CORE_RESOURCES 表（:28-254）+ BRANCH_RESOURCE_OVERRIDE（battle_config.py:212-219）移除/瘦身——**注意 job_guide/player.py 依赖 desc 文案，需同步迁移**

### game/core/battle_conds.py（条件层）
11. `element_marks`（:147-159）加读 `enemy["element_marks"]` 新轨分支
12. 新增「破绽值 ≥N」cond（读 buffs["shaken"]["val"]）；战意≥N/连段≥N 用现有 player_mech_stacks（:203）/player_combo_stacks（:117）即可
13. `player_res_stacks`（:181-200）+ 被动 `rage>=5`（:287-290）随资源条废弃改道 player_mech_stacks

### game/commands/（展示层）
14. combat.py:1617-1624（_resource_line）、player.py:31-32/:1288-1295（_RES_CN/res_cost 行）、job_guide.py:17/:102-105（CORE_RESOURCES desc）——随资源条废弃改为叠层/挂账展示
15. instance.py 副本持久化：resources（:214/:2211/:2260/:2865/:2891）随资源条废弃移除；mech_stacks 持久化（:2204/:2235）保留即 v151 玩家叠层跨回合所需

### 技能数据 game/data/skills.py
16. 法师引爆技：cond type="reaction" 接线（battle.py:3661 入口已备，skills.py 侧挂 cond）
17. 全表 res_gain/res_cost（97+122 处）语义迁移——**这是体量最大的机械性改动**

---

*侦察方式：grep 定位 + 关键段 sed 读上下文；未跑全量回归；未改任何文件。*
