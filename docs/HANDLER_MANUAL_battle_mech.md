# Handler 改造手册（battle_mech.py 122 个）

> 配套 ENGINE_ARCHITECTURE_v181P4.md。鱼鱼拍板：handler 加显式 target/caster。
> 本手册精确到每个注册表：签名现状、缺什么、改造方式。

## 注册表签名现状（读代码确认）
| 注册表 | 现签名 | 已有 actor | 缺 |
|---|---|---|---|
| BOSS_MECHS | (battle, logs, **e**, r) | e=作用的 Boss ✓ | 无（已显式） |
| MON_CTRL_EFFECTS | (battle, **player**, logs, mval) | player=被打玩家 ✓ | 无（已显式，改名 target 即可） |
| MON_BUFF_EFFECTS | (battle, logs, sname) | ✗ 无 | **施法怪 actor**（自我 buff 作用者） |
| SKILL_BUFF_EFFECTS | (battle, skill_name, info, **player**, lv, logs) | player=施法者 | **target**（对敌效果如 sleep/mark） |
| MECH_EFFECTS | (battle, mval, p_mech, total, logs, skill_name, is_crit, info, **caster**) | caster=施法者 | **target**（对目标效果如 burn/mark/毒） |

## 各表 handler 细分

### MECH_EFFECTS（65 个）——玩家技能 mech 触发
**A 类：对目标效果（缺 target，作用=被打目标）**
burn/burn_burst/freeze/spd_down/stun/silence/slow/interrupt/mark/mark_burst/
poison/poison_burst/bleed/fire_mark/ice_mark/thunder_mark/element_multi_mark/
element_burst/element_burst_3/hunt_mark/soul_mark/curse/curse_refresh/
atk_down/def_down/all_down/corros/spellblade_meteor/bone_rush

**B 类：玩家自我/资源（作用=caster 自己，已有 caster 参数够了）**
rage/zhan_yi/lian_duan/chi/iron/shield/spellblade_surge/arcane_matrix/
shadow_dance/finisher/faith_unload/zhan_yi_cash/zhan_yi_fury/guard_core_burst

**C 类：混合/需要细看（~15 个）**
shield_burst/rage_burst/wind/wind_burst/arcane/arcane_burst/spellblade/
spellblade_storm/spellblade_burst/judge/judge_burst/shadow/shadow_burst/
chi_burst/iron_burst/bless_shield/melody/melody_chant/melody_finale/
element_burst_all/element_mark_current/sacrifice/poison_burst_finisher/cleanse

### SKILL_BUFF_EFFECTS（36 个）——增益技效果
**A 类：对敌 debuff（缺 target——增益技带对敌效果：睡眠/标记/降攻）**
mon_atk_down/mark/sleep/vuln/taunt/star_lock

**B 类：玩家自我/团队（player 参数已够，不改签名只改内部）**
shield/shield_all/reduce_all/reduce/spd_buff/dodge_buff/crit_hit_buff/cc_immune/
cleanse/cleanse_all/atk_matk_all/all_stat_cc/element_shift/element_switch/
shield_self/shield_block/block_reflect/protect/disengage_dodge/dodge_reduce_all/
hunt_team_dmg/reduce_shield_all/shield_all_reduce/shadow_dance/stealth_cc/
arcane_shield/arcane_matrix/arcane_field/stealth/shadow_realm

### MON_BUFF_EFFECTS（7 个）——怪自我增益（全缺 actor）
atk_up/atk_up_strong/def_up/heal_self/summon/shield/spd_up
→ 签名加 actor（施法怪自己），内部 battle._actor_buffs(actor)/actor[...] 写

### MON_CTRL_EFFECTS（5 个）——怪控制目标
freeze/stun/silence/interrupt/slow → 签名 player 改名 target（作用=被打玩家）

### BOSS_MECHS（9 个）——Boss 机制（已显式 e）
enrage/summon/heal/shield/phase/stacks/phase_open/player_low/pv_broken → 不改

## 待细分类（写代码时逐个确认）
mech_mixed 里 ~15 个 + skill_buff_self 需确认是否全用 player 参数（有的可能是
团队效果作用 allies）

## 改造顺序建议
1. MON_BUFF_EFFECTS（7 个，纯加 actor，最安全）
2. MON_CTRL_EFFECTS（5 个，player→target 改名）
3. MECH_EFFECTS A 类（对目标效果加 target）
4. SKILL_BUFF_EFFECTS A 类（对敌效果加 target）
5. 细看 mixed 类逐个定
