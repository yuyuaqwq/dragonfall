# 187 effect 名词分诊表（N7.5 产出）

> 2026-09-08 自动扫描 game/data/**/*.py 全库 effect/mech 字段 → 来源分类 → 落地分诊。
> 目的：效果系统 v2 收敛前，明确每个名词的去向——进 EFFECT_ACTIONS / 进事件总线 /
> 上层独占（不迁） / 生活效果（排除）。避免 battle2 静默跳过。
> 配套：docs/archive/DESIGN_effect_system_v2.md（效果系统 v2 主方案）

---

## 分诊原则（五类去向）

| 去向 | 含义 | 落点 |
|---|---|---|
| **A. 战斗动词直通** | 已在/应进 EFFECT_ACTIONS 名词映射，battle2 技能/怪直接执行 | `game/data/battle_rules.py` EFFECT_ACTIONS + STATE_EFFECTS |
| **B. 事件总线注册** | 触发时机才生效（命中/受击/battle_start/道具使用）→ N8 fire() 分发 | N8 完成后规则表注册 |
| **C. 上层独占（不迁）** | 套装/符文/词条/武器专属机制，引擎不认知名 | 上层 proc → 调动词（N9 族化后） |
| **D. 生活/非战斗** | 开箱/钓鱼/种植/改名等，不属战斗效果系统 | 命令层自理，不进引擎 |
| **E. 兼容层旧键** | 旧数据残留 effect 名（物品附加/策划表），无独立效果 | 迁移后随旧数据层清理 |

---

## 一、SKILL/MONSTER（12）——战斗核心，最高优先级

技能数据/怪物模板 effect 字段，**走技能链**（_do_buff 的 effect 分支）。

| 名词 | 来源 | 分诊 | battle2 现状 |
|---|---|---|---|
| atk_up | skills/monsters | **A** buff | ✅ EFFECT_ACTIONS atk_up（mult 快照） |
| def_up | skills/monsters | **A** buff | ✅ def_up（mult 快照） |
| spd_up | skills/monsters | **A** buff | ✅ spd_up |
| shield | skills/monsters | **A** shield | ✅ shield 动词（expire_at 收口 N7.2） |
| heal_pct | monster_mods | **A** heal | ⬜ heal 动词待补（怪按 max_hp% 自疗） |
| heal_self | monsters | **A** heal | ⬜ heal 动词待补 |
| summon | skills/monsters | **B** 事件（召唤实体） | ⬜ summon 动词/事件（N8） |
| vulnerable | skills/monsters | **A** 易伤（state_add 或 debuff_scale） | ⬜ hunt_mark 同族已有 state |
| mortal_wound | monster_mods | **A** 减疗（state/特殊） | ⬜ |
| stacks_clear | skills | **A** 清叠层（cleanse state） | ✅ cleanse 动词 |
| stacks_set | skills | **A** 设叠层（state_set） | ⬜ state_set 动词待补 |
| freeze_self | monster_mods | **B** 自控（模式切换副作用） | 上层怪机制 |

**行动**：补 heal / vulnerable / mortal_wound / stacks_set 4 个战斗动词或名词映射（N7.5a）。

---

## 二、ITEM（86）——物品/药水效果

物品使用效果（items.py effect 字段），分三子类：

### 2a. 战斗增益/一次性（~30，核心）——**B/A**
buff_atk/buff_matk/buff_crit/buff_def/buff_spd/buff_atk_big/small/def/big_def/food 系列、
crit_dmg_pot/pene_pot/pene_magi_pot/lifesteal_pot/block_pot/thorns_pot/dodge_pot/
heal_up/magic_resist/cc_immune/next_atk_up/buff_phys_next/shield_big/holy_shield/
rock_shield/steal_buff/vuln/execute_pot/armor_break_pot/full_tension/dot_amp/
battle_start_resource
→ 命令层道具使用走 `apply_effects`（同技能 effect 链）→ **A**（EFFECT_ACTIONS 补全）
  或 battle_start/命中注册 → **B**

### 2b. 生活/功能（~40，纯非战斗）——**D 排除**
bag_expand/garden_slot/harvest_boost/seed_planter/fish_net/collection/compass/
lantern/mail/morph/pet_rename/rename/re_roll_affix/reforge/return_vila/teleport_portal/
firework/toy_form/scout/trap/open_chest/open_rune_chest/reset_voucher/bait_*/
grapple/mana_restore/enhance_boost/lucky/recover/clear_red/refresh 等
→ 命令层物品使用逻辑处理，不进战斗效果系统

### 2c. 词条/附加（~15，旧物品附加机制）——**E 兼容层**
apply_mark/steal_buff 等 → 随 items 附加层清理

---

## 三、SET（64）——套装效果（最高优先级 B/C 分界）

套装 2/4/6 件效果（set_bonus_data/sets.py 数据 effect 名），分四子类：

### 3a. battle_start 起手（~15）——**B**（battle_start 事件）
battle_start_cp/battle_start_res/qi_shi_charge/cloth_regen_battle/first_hit_immune/
hu_xiao_barrier/holy_halo_shield/night_mp_regen/full_rage_pursuit/pan_shi_steady
→ N8 fire("battle_start") 注册

### 3b. 命中/暴击/击杀触发（~25）——**B**（skill_hit/crit/kill 事件）
anvil_parry/burn/crit_on_marked/dot_amp 族/divine_grace_burst/eagle_vision/execute/
finisher_crit/frost/gale_double/hei_zhao_erode/holy_field_heal/hunter_mark_bonus/
iron_execute_rampage/jing_tie_refine/judge_purify_heal/lei_ting_chain/li_ming_dawnbreak/
lifesteal_set/mi_fa_arcane_bolt/midnight_assassinate/night_backstab/phantom_echo/pierce/
proc_flat_dmg/proc_lifesteal/reflect/regen/silver_knight_lance/sky_chain/shadow_combo_double/
thunder/xing_chen_starstrike/xing_jie_starfall/xue_tu_spark
→ N8 事件注册（hit/crit/taken/kill）或上层族化

### 3c. 条件触发（阈值/形态）——**B/C**
crit_up_set/dodge_set/mdef_up_set/lifesteal_set（面板型套装）/heal_team_on_miracle_t2plus/
bless_chant_mp/chi_skill_phys/combo_finisher_per_layer/tie_pi_bulwark/
ultimate_cost_reduce/res_cost_reduce/fu_wen_glyph_bolt/shou_wang_ward/xing_zhe_hunt
→ 状态阈值事件/上层被动族

### 3d. 词条级特殊——**C 上层**
shadow_etch_vuln/tie_shou_blood/travel_mark 等 → 职业/套装上层

---

## 四、RUNE（14）——符文效果

| 名词 | 分诊 | 说明 |
|---|---|---|
| barrier/ironwall/regen | **B** 护盾/减伤/回复（受击/时刻） | 引擎动词 shield/heal 已有 |
| armor_pierce/magic_break/weaken | **B** 破甲/减益 | state debuff_scale |
| brutal/swift/thorns/lifesteal/exp_bless/mana_flow/scavenger | **B/C** 命中/击杀/资源触发 | 事件总线或上层 |
| freeze | **A** 控制 | ✅ EFFECT_ACTIONS freeze |
| chain | **B** 连招 | 上层 |

---

## 五、POI/OUT（11）——探索点/世界效果，全部 **D 排除**

buff（POI 祝福→poi_buff 已处理）/fish/herb/loot/merchant/note/recover/refresh/rune/
sight/wish → 探索/世界逻辑自理，非战斗效果系统

---

## 六、技能 mech 名词（13）——分诊

| mech | 分诊 | 说明 |
|---|---|---|
| slow/stun/silence/freeze/spd_down | **A** ✅ 已有 control 动词 | rules 已映射 |
| poison/burn | **A** ✅ state DOT | STATE_EFFECTS 已有 |
| zhan_yi/lian_duan/arcane | **A** ✅ state 叠层 | STATE_EFFECTS 已有 |
| heal（mech=heal） | **A** heal 动词待补 | |
| thunder | **A** 元素技能（mech 语义） | 上层/伤害类型 |
| enrage | **C** 怪狂暴机制 | BOSS_MECHS 上层 |
| summon | **B** 召唤 | N8 |
| interrupt | **A** 打断（control 变体） | 待补动词 |

---

## 七、实施批次建议

| 批次 | 内容 | 范围 |
|---|---|---|
| N7.5a | 战斗核心动词补全：heal / vulnerable / mortal_wound / stacks_set / interrupt | SKILL/MONSTER 12 + mech 13 |
| N7.5b | ITEM 2a 战斗增益名词 → EFFECT_ACTIONS 补全（药水链） | ITEM ~30 |
| N7.5c | SET/RUNE 触发类整理事件注册表（N8 前置清单） | SET/RUNE ~70 |
| N8 | 事件总线 19 时机 fire() → 触发类效果接入 | battle_start/hit/crit/kill... |
| N9 | 上层族化迁移（C 类不迁引擎，族执行器薄封装） | 套装/符文/词条 |
| 收尾 | D/E 类确认排除清单落文档 + 静默日志防漏 | 全库 |

---
*本表由全库扫描自动生成初稿 + 人工分诊，来源文件清单可重跑脚本复现。*
