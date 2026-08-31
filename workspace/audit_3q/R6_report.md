## R6 CTB 时刻制审查报告（机制/数值层）

### 覆盖范围
- game/data/skills.py（4056 行，全量）
- game/data/items.py（3006 行，全量，含 v140 战斗机制道具）
- game/data/battle_config.py（648 行，全量）
- game/engine.py（962 行，重点 skill_buff_turns / core_resource）
- game/battle.py（5918 行，全量：回合主循环 / buff 递减 / CD / dot / hot / 护盾 / 宠物 / 召唤）
- game/core/battle_modes.py（459 行：dual_form/focus/vent 回合状态机）
- game/core/battle_bars.py（289 行：enemy_bar 回合衰减 + charge 蓄力）
- game/core/battle_conds.py（329 行：回合/状态条件）
- game/core/battle_mech.py（1045 行：MECH_EFFECTS / BOSS_MECHS / MON_BUFF_EFFECTS / SKILL_BUFF_EFFECTS）
- game/core/potion_effects.py（723 行：道具回合效果 handler）
- game/core/item_templates.py（1148 行：道具模板 payload）
- game/core/food_effects.py / affix_effects.py / weapon_effects.py（装备/食物回合钩子）
- game/core/constants.py（DOT 五律常量）
- game/commands/instance.py（3498 行：副本 CTB 调度/轮次闸门）
- game/commands/combat.py（3151 行：世界 Boss force dot / buff 显示）

### 结论摘要
1. **CTB 行动轴已经落地**（v121→v130.10 绝对时刻）：玩家/敌方/副本全部按 ct 行动，行动者 ct+=cost、其余单位 ct-=cost（battle.py:1397-1440；instance.py:2056-2103、2636-2700）。R5 负责看这条轴。
2. **但机制/数值层几乎全部仍是"回合制"单位**，且"回合"= 每次玩家行动（player_turn 开头 self.round += 1，battle.py:1617）。CTB 下敌方可以在一个 round 内多次行动（_enemy_phase while 循环上限 8 动，battle.py:1722-1759），所以**回合与行动/时刻不对等**：1 个"回合"内实际经过 1 次玩家行动 + 0~8 次敌方行动。所有按回合递减的 buff/CD/dot 都锚定在"回合"（_end_round，battle.py:5118-5189），与 CTB 的"时刻"（行动点）不是同一把尺。
3. 盘点结果：**没有用"时刻/行动点"计时的机制**；全部时长类机制 = 回合单位（buff 回合数、CD 回合数、dot 每回合结算、hot 每回合结算、护盾回合数、蓄力回合数、Boss 每 N 回合机制、宠物每 N 回合技能、被动每回合触发）。
4. 若严格"整个战斗不能有回合概念"，需把 9 大类机制全部改为行动点/时刻单位；若只做"CTB 语义对齐"，最小改动是让 `_end_round` 的递减与敌方行动次数解耦（每个"时刻"递减）——详见改造评估。

### 证据清单（回合单位机制全量清单）

#### A. 技能 CD/冷却（175 个技能带 cd 字段）
| 证据 | 内容 |
|---|---|
| skills.py:66,77,89,100,110,1240,1288,1326,1374,1393,1468…（共 111 处 `"cd": N`，N=1~6，分布 1:4/2:49/3:54/4:30/5:19/6:19） | cd 字段单位 = 回合 |
| battle.py:1068-1091 `_set_skill_cd`（注释"设置技能冷却(cd 回合…)"）+ `_skill_cd_left`（"剩余冷却回合数"） | CD 存 self.cooldown{技能名:回合数} |
| battle.py:1093-1099 `_tick_cooldowns`（"回合结束：所有冷却－1"） | **CD 递减点 = _end_round 每回合减 1** |
| battle.py:2186-2189（施放后 `self._set_skill_cd(skill_name, cd)`）、2140-2142（电荷制满阶才入 CD） | CD 写入点 |
| battle.py:1949-1952、2011-2014 `_skill_cast_blocked`/`_do_player_skill`（"还在冷却中(剩余 N 回合)"） | CD 消费点 |
| battle.py:5185 `self._tick_cooldowns()` | 递减挂点（_end_round 内） |

#### B. 玩家/敌方 buff 持续（回合计数，p_buffs/e_buffs = {键:剩余回合}）
| 证据 | 内容 |
|---|---|
| battle.py:5118-5155 `_end_round`："回合结束：buff 剩余回合递减"——`for tbl in (self.p_buffs, self.e_buffs): tbl[k] -= 1` | **buff 递减 = 每回合一次**；stun/freeze（行动级控制）与 fire/ice/thunder_mark（元素印记）与 next_atk_up/buff_phys_next/stealth（一次性）与 reduce_all/shield（特殊类型）豁免 |
| battle.py:5157-5160 `_reduce_all_left -= 1` | 团队减伤回合数独立计时 |
| battle.py:107-108 BUFF_TURNS=3 / DEBUFF_TURNS=2 常量 | buff 默认回合 |
| battle.py:59-86 BUFF_MULT 24 键：atk_up/def_up/spd_up/crit_up/matk_up… | 属性 buff 全部按回合计数 |
| battle.py:3335-3353 `_skill_buff`：`base_turns = E.skill_buff_turns(lv)` → `p_buffs[key] = max(..., base_turns)` | 技能增益持续 = skill_buff_turns（回合） |
| engine.py:773-776 `skill_buff_turns`（"增益技能升级：每级持续回合＋1(Lv.1=3，Lv.5=7)"） | 持续回合按等级成长 |
| battle.py:3408（嘲讽 `e_buffs["mon_atk_down"] = skill_buff_turns(lv)`）、3926（破防 `def_down`）、3526（`p_buffs["def_down"]`） | 技能减益回合 |
| core/battle_mech.py:930-999 SKILL_BUFF_EFFECTS（mon_atk_down/element_shift/stealth/shadow_realm/mark/sleep/shield_all/reduce_all 均写 e_buffs/p_buffs 回合数） | effect 注册表 = 回合数写点 |
| core/battle_mech.py:769-826 MON_BUFF_EFFECTS（怪物增益 atk_up/def_up/spd_up = BUFF_TURNS=3 回合；shield 存护盾值不按回合） | 敌方 buff 回合 |
| battle.py:4447-4463 `_apply_buffs`（`for eff, turns in buffs.items()` 按回合数生效） | buff 消费点 |
| commands/combat.py:1552-1582 状态面板（"剩 N 回合"） | 展示消费 |

#### C. 控制类（眩晕/冻结/沉默/睡眠/减速）——行动级 vs 回合级混用
| 证据 | 内容 |
|---|---|
| core/battle_mech.py:180-197 `_m_stun`（`e_buffs["stun"]=1`）、`_m_freeze`（`e_buffs["freeze"]=1`）、`_m_silence`（`e_buffs["silence"]=2`） | 玩家施放控制写回合数（1/1/2） |
| core/battle_mech.py:835-894 MON_CTRL_EFFECTS（`p_buffs["freeze"]=1`/`["stun"]=1`/`["silence"]=2`/`["spd_down"]=2`） | 怪物控制写回合数 |
| core/battle_mech.py:166-176 `_m_spd_down`：`dur = max(mval, 1)` → `e_buffs["spd_down"]` | 减速回合 = mech_val |
| battle.py:1635-1646 player_turn（眩晕/冻结被控：pop + ct 照走） | 控制消费 = 行动级（被控浪费一次行动） |
| battle.py:4247-4262 `_enemy_turn`（freeze/stun/sleep 跳过敌方行动并 pop） | 控制消费 = 行动级 |
| battle.py:5122-5127 `_end_round`（stun/freeze 豁免回合递减，注释"控制类 buff 是行动级控制"） | **行动级语义已显式化** |
| battle.py:4040-4047 `_boss_ctrl_dur`（Boss 控制时长减半、至少 1 回合） | Boss 霸体 |
| core/battle_mech.py:353（`e_buffs["stun"]=1` 时停领域）、battle.py:5803（无敌后僵直 stun_after） | 其他控制写点 |

#### D. dot/持续伤害（目标级 enemy.debuffs，按层按回合）
| 证据 | 内容 |
|---|---|
| battle_config.py:50-61 DOT_DEFS（poison/burn/bleed/corros 混合公式 + 放血 + 适应回落） | dot 数值表 |
| battle.py:4651-4849 `_tick_dots`：**"每次结算（每层每回合混合公式）…结算后层数 n-1"** | dot 每回合跳一次、每回合 -1 层 |
| battle.py:4962-4965 `_turn_start`（monster/pvp：`_dot_pending=True` 复位 → `_tick_dots`） | **dot 结算频率 = 每玩家行动一次**（= 一回合） |
| commands/instance.py:2184-2201（副本：`dot_pending` 每轮（全员行动过）结算一次） | 副本 dot = 每轮一次 |
| commands/combat.py:2540-2547（世界 Boss：`_tick_dots(force=True)` 每次玩家行动强制结算） | 世界 Boss dot = 每行动一次 |
| core/battle_mech.py:95-130 `_m_burn` / 398-436 `_m_poison`（叠层写入 enemy.debuffs，`last_round` 记录叠层回合） | dot 叠层写点 |
| battle.py:4828-4834（poison/burn 最近 2 回合未叠层 → 适应 -4%） | "回合"被用作抗性回落判定 |
| core/battle_mech.py:229-258 `_m_mark` + battle.py:4841-4848（标记层每回合 -1） | 标记同 dot 生命周期（回合） |
| core/weapon_effects.py:130-138 `_apply_dot`（`cur["turns"]=max(…,turns)`）与 core/affix_effects.py:158（burn `cur["turns"]=3`）——**写 turns 字段但 _tick_dots 从不读 turns（只读 n）** | 冗余回合字段（死字段） |

#### E. hot/持续恢复（p_hot）
| 证据 | 内容 |
|---|---|
| battle.py:1795-1813 `_do_use_item` hot: 分支（`hot:hpct,mpct,turns`，turns 默认 3） | hot 回合数来源 |
| battle.py:1623-1625 player_turn（"正常回合开始结算 hot（每回合一次，含眩晕/冻结回合）"） | **hot 结算 = 每回合一次** |
| battle.py:1909-1932 `_apply_hot`（"每回合开始结算…回合数递减"） | hot 递减点 |
| core/item_templates.py:283-293 `tpl_food`（`turns = d.get("hot_turns") or 3`） | 食物 hot 模板 |
| items.py:2038-2046 等 150+ 食物条目（hot/hot_turns/hot_mana 字段，如黑面包 hot_turns=3） | hot 数据 |

#### F. 护盾（p_shields {value, turns}）
| 证据 | 内容 |
|---|---|
| battle.py:1761-1777 `_add_shield`（默认 turns=3，同源叠加取 max） | 护盾回合数 |
| battle.py:5161-5165 `_end_round`（"护盾回合递减：各来源独立计时"） | 护盾回合递减 |
| core/potion_effects.py:182-199（岩盾/圣盾 `_add_shield(..., turns)`） | 道具护盾回合 |
| core/battle_mech.py:981-986 `_sb_shield_all`（全队护盾 matk 20% 3 回合） | 技能护盾回合 |

#### G. 蓄力/电荷/专注/形态（回合状态机）
| 证据 | 内容 |
|---|---|
| skills.py:67,318,739（`"charge": 1/2/1`）+ battle.py:2166-2175（"需要 N 回合！"，`self.charging={"left": charge}`） | 旧蓄力 = 回合数 |
| battle.py:1518-1540 `_player_charge_release`（回合开始 left-1，归零释放） | 蓄力计时 = 回合 |
| battle.py:4374-4390 `_enemy_charge_tick`（敌方蓄力 left-1 回合） | 敌方蓄力回合 |
| core/battle_bars.py:206-237 `charge_tick`（每回合 +1 阶，`gain_per_turn` 配置） | 电荷制每回合 1 阶 |
| core/battle_modes.py:252-274 `focus_tick`（`fs["turns"] += 1`，max_turns=3 超时退出） | 专注回合计时 |
| core/battle_modes.py:96-133 `dual_form_enter/tick`（`turns_left` 递减，auto_duration=3） | 形态回合计时 |
| battle_config.py:295-314 FOCUS_CFG（enter_turn=1 / gain_per_turn / max_turns=3）、267-286 DUAL_FORM_CFG（auto_duration=3） | 配置回合单位 |
| skills.py:3455-3461 时间凝滞（`stasis.max_turns=3`，内联配置回合） | 时咒凝滞回合 |

#### H. 战斗道具（全部回合制，3 回合默认）
| 证据 | 内容 |
|---|---|
| battle.py:1855-1875 `_do_use_item` buff: 分支（"战斗药水：effect → p_buffs 增益 3 回合"，`p_buffs[k]=max(...,3)` 硬编码 3） | 战斗药水 = 3 回合（硬编码！） |
| core/item_templates.py:351-433 `_BUFF_KEYS`（effect→buff 键映射，含 special: 分发） | 道具→buff 映射 |
| core/potion_effects.py:64-199（next_atk_up=1 次、heal_up/magic_resist/thorns/dodge/cc_immune/execute/pene/lifesteal/crit_dmg/block 全部 `turns` 默认 3） | 特殊药水 = 回合 |
| core/potion_effects.py:316-326（mana_cost_down `turns=3`）、329-339（buff_phys_next 一次性）、342-352（full_tension `turns`） | v130.2 资源药水回合 |
| core/potion_effects.py:404-439 `eff_summon`（turns 用于 thorns/hot/heal_up buff；**召唤物实体本身无 turns 字段 → 召唤物无时间限制，存活到死**） | 召唤物时间单位缺失 |
| core/potion_effects.py:442-485 `eff_trap`（ctrl turns=1；Boss 降级）、549-561 `eff_buff_extend`（+extend_turns 回合）、564-578 phoenix（turns=3 减伤）、581-596 purify_immune（turns=3 免疫）、599-611 morph（turns=3）、614-624 invuln（turns=1 无敌 + stun_after）、648-667 dot_amp（turns=2）、697-721 vuln（turns=3） | v140 战斗机制道具全部回合单位 |
| items.py:2967-2986（烬灵香炉 turns=3 / 霜寒捕兽夹 turns=1 / 圣光净水 turns=3 / 龙血变身 turns=3 / 次元门扉 turns=1 / 连携增幅墨 turns=2 / 弱点击破石 turns=3…） | 道具 effect_data turns 字段 |
| battle.py:5166-5177（p_eff amps `turns_left` 回合衰减 / hits_left 命中消耗）、5178-5184（vuln/dot_amp `turns_left` 回合衰减） | p_eff 回合递减 |

#### I. 被动/每回合触发类
| 证据 | 内容 |
|---|---|
| skills.py:1138（气力调和 `passive.proc="turn_heal" pct=0.02`）+ battle.py:5009-5015（"每回合回血 2%"） | **每回合触发被动** |
| skills.py:2403（生命之泉 team_regen）+ battle.py:5016-5022（全队每回合回血 5%） | 每回合被动 |
| skills.py:1672（奥术直觉 arcane_regen）+ battle.py:5023-5031（每回合充能 +1） | 每回合被动 |
| battle.py:5039-5056（核心资源自然回：`rd.get("regen")` 每回合）+ battle_config.py:243-247（regen=1 注释） | 每回合资源回复 |
| battle.py:4988-5002（圣光/永恒套每回合回血、星尘套夜间每回合回蓝） | 套装每回合 |
| battle.py:4966-4968 `_affix_turn_start`/`_food_turn_start`（词条/食物回合开始回春/冥想） | 回合开始钩子 |
| core/weapon_effects.py:845-911（铁卫意志/晨曦微光/不灭微光每回合回血、死亡之舞每回合结算缓伤、岁月流转每回合叠层） | 特效装备回合开始/结束 |
| game/data/pets.py:9-16,22-52（`skill_interval`: 3/4/5 回合）+ battle.py:4599-4626 `_pet_skill_turn`（`self.round % interval != 0` 跳过） | **宠物技能 = 每 N 回合** |
| battle.py:4628-4649 `_pet_block_check`（影袭 `round % interval`） | 宠物挡刀 = 每 N 回合 |
| skills.py:1304（`stance_floor: {res_gain:1, per_turn:1}` 守护姿态回合末回怒）——**全库唯一写点，引擎零消费（死配置）** | 姿态回合末 |
| battle_config.py:600-608 STANCE_COUNTER（guard_counter_flat 回合末保底回怒 1）——**battle.py 无消费点（同 dead）** | 姿态回合末（未接线） |
| battle_config.py:373-408 ENEMY_BAR_CFG（shaken `decay_per_turn=4`、curse turns=3）+ core/battle_bars.py:133-147 `bar_tick`（每回合免疫递减+衰减） | 敌身条回合衰减 |
| battle_config.py:636 IDLE_FLOOR_TURNS=2 —— **全库无消费（死常量）** | 保底律回合（未接线） |

#### J. Boss 回合机制（按 round 计数）
| 证据 | 内容 |
|---|---|
| core/battle_mech.py:533-542 `_b_summon`（`r % 3 == 0` 每 3 回合召唤；每 6 回合 2 只） | Boss 回合机制 |
| core/battle_mech.py:545-552 `_b_heal`（`r % 4 == 0` 每 4 回合回血 8%） | Boss 回合机制 |
| core/battle_mech.py:555-560 `_b_shield`（`r == 1` 首回合护盾） | Boss 回合机制 |
| core/battle_mech.py:659-665 `_b_stacks`（`r % 2 == 0` 每 2 回合叠层 +1） | Boss 回合机制 |
| core/battle_mech.py:676-705 `_b_opening`（`r != 1` 跳过；mortal_wound 写 p_buffs 回合数，monster_mods.py:214-222 power=2） | 开场技首回合 + 回合 buff |
| core/battle_mech.py:708-739 `_b_player_low`（`_low_hp_cd` 每回合递减的 cooldown） | 反制 cooldown 回合 |
| battle.py:4172 `r = self.round` → BOSS_MECHS handler 传 round | round 来源 |

#### K. 战斗回合本身（"回合"定义）
| 证据 | 内容 |
|---|---|
| battle.py:1617 `self.round += 1`（player_turn 正常回合开始） | **回合 = 每次玩家行动** |
| battle.py:1722-1759 `_enemy_phase`（while 敌方最小 ct>0 行动，硬上限 8 动） | 一回合内敌方可多动 |
| battle.py:5118 `_end_round`（buff/CD/护盾/amp 递减统一出口，由 _enemy_phase 末尾调用） | 回合结束 = 递减时刻 |
| commands/instance.py:2198-2201（`round_acted` 全存活成员行动过 → 新一轮） | 副本"轮" = 全员各行动一次 |
| commands/combat.py:2540-2547（世界 Boss 每玩家行动 force dot 一次） | 世界 Boss 行动即回合 |
| battle.py:417 `_dot_pending`（"副本由 instance 层 set False；世界 Boss 由 combat 层 force=True 触发"） | dot 结算闸门 = 回合锚 |

### 影响面评估（若改时刻制）
数据层（skills.py/items.py/battle_config.py）：
- skills.py：111 处 `cd`（1-6 回合）+ 87 处 desc 含"回合" + 44 处"持续 N 回合" + charge 3 处 —— 需换算或改单位（粗糙估 200+ 行）
- items.py：约 150 条食物 hot_turns + 40+ 药水 turns/effect_data + 20 件 v140 机制道具 turns —— 200+ 行
- battle_config.py：FOCUS/DUAL_FORM/CHARGE/ENEMY_BAR/VENT/STAR_LOCK/SHADOW_DANCE/CURSE/DIRGE/STANCE/IDLE_FLOOR 等含回合字段 —— 30+ 字段

引擎/战斗层（battle.py 为主）：
- `_end_round`（battle.py:5118-5189）：buff/CD/护盾/amp/reduce_all 递减入口 —— 若改为"每个行动时刻递减"需在 `_after_actor_ct` 或敌方单动结算点挂新递减；若保留回合概念则不动
- `_turn_start`（4954-5116）：hot/dot/被动/资源回复/形态 tick —— 全部回合锚
- `_tick_cooldowns`（1093-1099）：CD 递减
- `_tick_dots`（4651-4849）：dot 每回合跳
- `_apply_hot`（1909-1932）、`_add_shield`/`_end_round` 护盾段
- `_pet_skill_turn`/`_pet_block_check`（`round % interval`）
- `_boss_mech`（BOSS_MECHS 全部 `r % N`）
- `_player_charge_release`（charging.left 回合）、core/battle_modes（focus.turns / dual_form.turns_left）、core/battle_bars（charge stages / bar 衰减）
- 状态序列化字段：`round`/`cooldown`/`p_buffs`/`e_buffs`/`p_hot`/`p_shields`/`dot_pending`/`round_acted`/`taunt_turns`/`_reduce_all_left`/`amps.turns_left`/`vuln.turns_left`/`dot_amp.turns_left`/`charging`/`v139_charge`/focus/dual_form state —— 存档兼容也涉及
- 命令层：instance.py `round_acted`/`dot_pending` 轮次闸门；combat.py force dot 与 buff 显示"剩 N 回合"

粗估：数据层 ~450-500 行字段/注释、引擎层 ~20 个函数/挂点、存档结构 15+ 字段。**工作量中等到大**。关键设计决策：CTB 时刻制下"1 回合 = 1 玩家行动"的现有等价（monster/worldboss 每次行动结算一次 dot/递减）其实已经接近"时刻"语义；真正对不齐的是**敌方多动（CTB 连动）不触发递减**——若接受"回合 = 玩家行动"作为等效时刻，则现有实现语义自洽，只需把文案从"回合"改为"行动/时刻"并补敌方行动后递减（如需严格对齐）。

### 收尾验证
- git status：无 tracked 改动（仅 untracked 历史文件与 workspace 产物），无临时脚本残留。
