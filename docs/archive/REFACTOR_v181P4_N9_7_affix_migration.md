# battle2 N9.7 affix 76 词条迁移方案（分档 + 批次）——进度更新 2026-09-09

> affix 迁移完成度：A1 26 零代码 ✓ + 通用战斗词条 16 已迁 ✓ + 条件乘区 4 ✓。
> R4（N9.7e，2026-09-09）：资源型落地一批——事件 gain 型 10 词条已装配
> （war_spirit/warcry_echo/blood_bath/arcana_flux/crit_charge/holy_echo/crit_return/
> pious_charm/rock_rest/opening_stance）+ boiling_blood 怒气满减伤。
> 剩余 = 上限型/cost_reduce/cond 修正/regen 型 11（cap 动态机制待引擎层，R4 未实施）
> + 职业机制 12 + purify 特殊（缺"增益 key 语义"设计）。

## 1. 分档矩阵（76 词条实测分类）

### A1 面板 stat 型 26（✅ 零代码——生成时折算进 item.stats，battle2 面板自动含）
```
lifesteal crit_up crit_dmg precise pene_phys pene_magi pene_flat pene_mflat
block thorns phys_ward magic_ward thirst_phys thirst_magi dodge swift
elem_resist abyss_resist hp_up tenacity luck cdr exp_bonus gold_bonus
heal_power shield_power
```
（N9.7a 已验证：stat_affix_stats 折算 + 不产生 triggers + 面板含 ✓）

### A2 stat 未折算 15
| 词条 | 去向 |
|---|---|
| dmg_reduce（全减伤 3%） | ✅ N9.7c 已迁（taken_calc 乘区） |
| rage_forge/divine_radiance/holy_heart/rhythm_badge/chi_limit/full_pack/energy_blade | 职业资源上限 → **缺口** |
| arcane_focus/sigil_* /reaction_catalyst/burst_break/momentum_mastery/combo_edge | 职业机制（法师/拳师/攻线）→ **缺口** |

### B 事件型 21（通用 14 全迁 + 资源 6 缺口）
| 已迁（12+2） | 批次 | 缺口（资源 6） |
|---|---|---|
| bleed armor_break combo charge pierce | N9.7b | blood_bath pious_charm rock_rest |
| element_fire element_ice element_thunder | N9.7b | opening_stance energy_tide swift_tailwind |
| shield regen meditate | N9.7a | |
| counter tenacity_cc | N9.7c | |
| purify | ⚠️ 未迁——需"敌方增益 key"语义设计（旧 mon_ 前缀） | |

### C passive 14（条件乘区 4 迁 + 资源 8 缺口 + boiling_blood/finisher 依赖职业）
| 已迁 | 缺口 |
|---|---|
| execute hunt break_magic dragon_aw（dmg_calc 钩子，N9.7d） | war_spirit warcry_echo ember_brand arcana_flux crit_charge holy_echo crit_return combo_recover（资源回） |
| | boiling_blood（rage_full 职业资源判定）finisher（终结技职业机制） |

## 2. 迁移统计
- ✅ 已完成：A1 26（零代码）+ 通用战斗 16 = **42 词条 battle2 路径覆盖**
- 📋 缺口清单（等上层职业模块）：资源型 20 + 职业机制 12 = 32 词条
- ⚠️ purify：已注册翻译器设计，需"敌方增益 key 语义"定稿（battle2 buffs 无 mon_ 前缀概念，
  增益判定应 = 有 stat 折算 + op mul>1/add>0 的条目；待 N10 前补齐或记录缺口）

## 3. 批次完成记录
| 批 | commit | 内容 | n9_equip 断言 |
|---|---|---|---|
| N9.7a | 6db4cce | 骨架（affix_triggers/翻译器注册/tier）+ shield/regen/meditate + stat 验证 | 105→113 |
| N9.7b | c1b6ed7 | on_hit 族 8（bleed/armor_break/element_*/combo/charge/pierce）+ 4 扩展动作 | 113→121 |
| N9.7c | 67558d6 | on_taken 族 2 + dmg_reduce（we_affix_counter/tenacity） | 121→126 |
| N9.7d | 1b0943c | 条件乘区 4（execute/hunt/break_magic/dragon_aw）+ 4 新谓词 | 126→133 |
| N9.7e（R4） | e46cf05 | 资源事件 gain 型 10（we_affix_res_gain + on 映射表 + crit_return tier 键修正）+ boiling_blood 怒气满减伤 + EFFECT_RULES 资源 cap 行补全（energy/faith/cp/element） | +tests/test_affix_res_gain.py 39 断言 |

## 4. 装配层架构速查（N9.7）
- `equipped_affix_ids(actor)`：装备 affixes 列表 → 去重保序
- `_AFFIX_TRANSLATORS`：aid → fn(aid, actor, eff) 返回 {old_event: [效果 dict]}
- `_affix_effect_final`：effect + tier 取档（tiers[quality] 覆盖主数值键）
- `affix_triggers(actor)`：全词条 → 事件映射展开；apply_to_actor 合并（武器 + 词条）
- 纯动词词条（无 chance）直走：shield/heal/buff 动词
- 带 chance/条件/附加伤害：we_affix_* 扩展动作（we_affix_dot/defdown/element/bonus/
  counter/tenacity + 乘区 we_dmg_mult_cond/we_taken_mult_cond）

## 5. affix 收尾批（v181.M-affixtail，2026-09-09）——76 词条真实剩余缺口精确盘点

> 方法：AFFIXES 76 逐条对照装配分派路径（A1 stat_affix_stats 折算 26 / cap_bonus
> 上限 6 / _AFFIX_TRANSLATORS 翻译器 29）→ **覆盖 61**；剩余 **15 真没效果**
> （带词条 → battle2 战斗内零效果）。R4/R2e 后遗留的 15 条明细与收口状态：

| 词条 | trigger/effect | 卡点 | 状态 |
|---|---|---|---|
| purify | on_hit {purge 1, holy_weaken 0.10} | 增益 key 语义（旧 mon_ 前缀） | ✅ 已装（we_affix_purify 命中驱散，判定 = EFFECT_RULES 面板 mul>1/add>0 / stat_scale 正层 / 自愈回能 period；成功 → holy_weaken atk×0.90 1 刻） |
| energy_tide | turn_start {res energy, regen 5, tiers 5/10} | — | ✅ 已装（turn_start → we_affix_res_gain，tier 取档，battle2「每刻」= 每行动） |
| swift_tailwind | turn_start {res energy, regen 10, cond energy_ge_80} | 跨刻状态无 1:1 点位 | ✅ 已装（turn_start 判当前精力 ≥80 → +10；持续维持线 ≈ 旧「上刻末≥80 下刻+10」口径，适配近似见注释） |
| energy_blade | stat {res energy, cost_reduce 0.05, tiers} | 消耗修正无装配层通道 | ⛔ 记缺口（下详） |
| arcane_focus | stat {mp_cost_reduce 0.10} | 同上 | ⛔ 记缺口（下详） |
| sigil_blessing | stat {mp_cost_reduce 5, on miracle, tiers 5/10} | 同上 | ⛔ 记缺口（下详） |
| ember_brand | passive {res rage, gain 1, cond hp_lt_30}（无 on） | 「怒气获取时额外 +1」需资源获取事件钩子 | ⛔ 记缺口（R4 判定维持） |
| combo_recover | passive {res chi, gain 1, on combo_skill} | 连招技无技能标记事件判据 | ⛔ 记缺口（R4 判定维持） |
| finisher | passive {finisher_dmg 0.10 tiers} | 终结技（res_cost/consume_all 技能）dmg_calc 乘区——**数据可判，潜在可装**，留主 agent 定（与 MECH_CASH finisher mech 乘区并存口径） | ⛔ 记缺口 |
| burst_break | stat {chi_skill_phys 0.10} | 拳师 chi 资源所有权 + kind=物理 技能乘区（职业判定） | ⛔ 记缺口 |
| sigil_engrave | stat {max_sigil 1, cond element_mage} | 元素法师印记上限（职业机制，battle.py 旧接线已随 N10-C 删） | ⛔ 记缺口 |
| reaction_catalyst | stat {reaction_dmg 0.15, cond element_mage} | 元素反应伤害（职业机制） | ⛔ 记缺口 |
| combo_ward / combo_edge | {combo_keep_chance / combo_threshold_reduce} cond 攻线限定 | 拳师攻线连段系统（职业机制） | ⛔ 记缺口 |
| momentum_mastery | stat {momentum_per_chi, cond 攻线蓄势} | 攻线蓄势 Momentum 机制（职业机制） | ⛔ 记缺口 |

**cost_reduce 三词条（energy_blade/arcane_focus/sigil_blessing）卡点侦察结论**
- 技能消耗结算点：battle2 引擎 `actions._skill_usable`（前置足额拦截）+
  `actions._spend_skill_cost`（扣费，mp 平字段直扣 / res_cost 扣 effects stacks）——
  **单点结算在引擎内、先于一切事件（act_cast 在扣费后 fire），装配层无消耗修正通道**。
- 先例核查：faith_unload/zhan_yi_cash = 技能数据 res_cost 通道（技能内声明，非装备词条
  折扣面）；旧 potion mana_cost_down / 套装 res_cost_reduce 消费端均随旧 battle.py 退役，
  battle2 无同族通道。
- 引擎方案建议（类 M-R2e cap_bonus，等主 agent 批）：装配层写 actor["cost_reduce"]
  容器（energy_blade → {res: energy, pct: tier}；arcane_focus → {mp_pct: 0.10,
  element/奥术技能判据 = info.element 字段}；sigil_blessing → {mp_flat: 5/10,
  miracle 判据 = res_cost/consume_all key∈faith/canticle}），引擎消耗点折算
  `实际扣费 = f(声明费, actor.cost_reduce)`（预检与扣费同源，旧语义保底 1 点）。

**we_affix_res_gain cap 收敛（同批）**：R4 附赠通道 `_add_stacks` 缺省 cap 静态读
state_def（上限词条抬 cap 后仍封旧 cap——divine_radiance 后 faith 卡 10/11、
full_pack 后 energy 卡 100/110）→ 缺省 cap 收敛引擎 `_cap_of`（EFFECT_RULES 基准 +
cap_bonus 动态；无 cap_bonus 时与旧读等价 = 行为零变化）；日志 cap 展示同源。

## 6. 批次完成记录（续）
| 批 | commit | 内容 | 断言 |
|---|---|---|---|
| m_affixtail | （见 git log） | 收尾：we_affix_res_gain cap 收敛 _cap_of + regen 型 2（energy_tide/swift_tailwind turn_start 回能）+ purify 命中驱散（we_affix_purify + holy_weaken 声明）；cost_reduce 3 / ember_brand / combo_recover / 职业机制 8 记缺口 | test_affix_res_gain 39→54；test_battle_n9_equip 157→171；test_class_mech_r2e 53 保持绿 |
