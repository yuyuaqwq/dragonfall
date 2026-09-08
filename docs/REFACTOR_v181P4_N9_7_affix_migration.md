# battle2 N9.7 affix 76 词条迁移方案（分档 + 批次）

> 2026-09-08 开工侦察结论。affix 迁移不能 76 全做——按效果本质分四档，
> 只把"引擎/装配层该管的"迁进 battle2，职业资源/机制向记缺口等上层职业模块。

## 1. 分档矩阵（76 词条实测分类）

### A1 面板 stat 型 26（✅ 零代码——装备生成时已折算进 item.stats）
```
lifesteal crit_up crit_dmg precise pene_phys pene_magi pene_flat pene_mflat
block thorns phys_ward magic_ward thirst_phys thirst_magi dodge swift
elem_resist abyss_resist hp_up tenacity luck cdr exp_bonus gold_bonus
heal_power shield_power
```
- 折算点：`affix.stat_affix_stats` → drops.generate_* 生成时并入 stats
- battle2 面板走 E.player_final_stats → 自动含 ✓ **什么都不用做**
- （测试验证一件带 crit_up 词条的装备在 battle2 面板有 +5% crit 即可）

### A2 stat 未折算 15（→ 拆两半）
| 词条 | 去向 |
|---|---|
| dmg_reduce（全减伤 3%） | ⚠️ 触发型常驻减伤（TAKEN_EFFECTS reduce 段）——迁装配层 taken_calc 乘区（见 §3 批次） |
| rage_forge / divine_radiance / holy_heart / rhythm_badge / chi_limit / full_pack / energy_blade（资源上限） | 职业核心资源模块（未建）→ **缺口** |
| arcane_focus / sigil_engrave / sigil_blessing / reaction_catalyst / burst_break / momentum_mastery / combo_edge（法印/反应/攻线机制） | 职业机制（元素法师/拳师/攻线）→ **缺口** |

### B 事件型 21
| 类别 | 词条 | 去向 |
|---|---|---|
| 通用战斗 14 | bleed armor_break combo element_fire element_ice element_thunder pierce charge counter purify shield tenacity_cc regen meditate | 装配层翻译（§3）——bleed/dot、combo(命中追加=extra_dmg 同语义)、counter(受击反击)、element_*(命中附元素)、pierce/charge(无视防御/追加) 均可迁 |
| 职业资源 6 | blood_bath(passive资源?) pious_charm rock_rest opening_stance energy_tide swift_tailwind（受击/回合回资源） | 职业核心资源模块 → **缺口** |

### C passive 14
| 类别 | 词条 | 去向 |
|---|---|---|
| 条件乘区 6 | execute hunt break_magic dragon_aw boiling_blood finisher | dmg_calc/taken_calc 钩子（we_dmg_mult_cond 已有 execute 谓词；boiling_blood 需 rage_full 职业依赖→缺口） |
| 职业资源 8 | war_spirit warcry_echo ember_brand arcana_flux crit_charge holy_echo crit_return combo_recover（暴击/治疗/施法回资源） | 职业核心资源模块 → **缺口** |

## 2. 结论：本期实际迁移量
- 面板 stat 26：零代码（验证即可）
- 装配层新迁 ≈ **13 词条**：bleed armor_break element_fire element_ice element_thunder
  pierce charge counter purify shield tenacity_cc regen meditate + dmg_reduce（taken_calc）
  + execute/hunt/break_magic/dragon_aw（条件乘区 4，已有谓词扩展）
- 记缺口等上层职业模块 ≈ 37：资源词条 20（A2 8 + B 6 + C 8 资源型）+ 职业机制 15 +
  combo/counter/finisher/boiling_blood 职业依赖复核
- legendary 传说专属（93 key）不在本期（N9.7 是 AFFIXES 76）

## 3. 装配层实现（battle2_equip_proc.py 扩展）
```python
def affix_triggers(actor) -> dict:
    """读装备 affixes 列表 → AFFIXES 表 → {battle2事件: [效果 dict]}。"""
    # item["affixes"] = ["bleed", ...]
    # trigger 映射：on_hit→hit(展开 attack_hit+skill_hit), on_taken→on_taken,
    #   battle_start→battle_start, turn_start→turn_start, passive→dmg_calc/taken_calc
```
- apply_to_actor 末尾合并 affix_triggers（与 weapon_triggers 并集进 actor["triggers"]）
- stat 型 affix 已折算 → 装配层跳过（不产生 triggers）
- 每个词条翻译器 ~5-15 行（大部分复用：dot 用 we_dot / shield 用 shield 动词 /
  regen 用 heal / execute 用 we_dmg_mult_cond）

## 4. 批次计划
| 批 | 内容 | 复用 |
|---|---|---|
| N9.7a | 装配骨架：affix_triggers + trigger 映射 + stat 验证测试 | EP 既有 |
| N9.7b | on_hit 族：bleed armor_break element_* pierce charge purify | we_dot + 新扩展（元素附加/破甲） |
| N9.7c | on_taken/turn_start/battle_start 族：counter tenacity_cc shield regen meditate | shield/heal 动词 |
| N9.7d | 条件乘区：execute hunt break_magic dragon_aw + dmg_reduce | we_dmg_mult_cond 谓词补 |
| 缺口清单 | 资源 20 + 职业机制 15 + combo/counter/finisher 职业依赖 | docs/EFFECT_TRIAGE 追加 |

每批：git status 干净 → 实现 + 测试 → 全套绿 → commit v181.N9.7X → 汇报。
