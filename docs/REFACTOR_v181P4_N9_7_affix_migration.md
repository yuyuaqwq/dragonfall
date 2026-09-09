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
| N9.7e（R4） | _见 R4 commit_ | 资源事件 gain 型 10（we_affix_res_gain + on 映射表 + crit_return tier 键修正）+ boiling_blood 怒气满减伤 + EFFECT_RULES 资源 cap 行补全（energy/faith/cp/element） | +tests/test_affix_res_gain.py 39 断言 |

## 4. 装配层架构速查（N9.7）
- `equipped_affix_ids(actor)`：装备 affixes 列表 → 去重保序
- `_AFFIX_TRANSLATORS`：aid → fn(aid, actor, eff) 返回 {old_event: [效果 dict]}
- `_affix_effect_final`：effect + tier 取档（tiers[quality] 覆盖主数值键）
- `affix_triggers(actor)`：全词条 → 事件映射展开；apply_to_actor 合并（武器 + 词条）
- 纯动词词条（无 chance）直走：shield/heal/buff 动词
- 带 chance/条件/附加伤害：we_affix_* 扩展动作（we_affix_dot/defdown/element/bonus/
  counter/tenacity + 乘区 we_dmg_mult_cond/we_taken_mult_cond）
