# 回合制效果审计报告（v151 配套 · 2026-08-31 子agent侦察，主agent落盘）

> 子agent撞迭代上限未落盘，主agent从 subagent-summary 提取恢复。

## 核心机制（CTB）
- CTB = battle.py:111 (BASE_DELAY) / 1406-1412 (_ct_cost) / 1634 (round+=1 每玩家行动1次) / 1739-1776 (_enemy_phase 敌方ct≤0连动，单次玩家行动敌方最多8动)
- 全部回合 buff 在 _end_round (battle.py:5260-5331) 按玩家行动递减
- 已豁免：stun/freeze(5268 行动级)、next_atk_up/stealth/buff_phys_next(5283 一次性)、reduce_all/shield(5289 特殊)

## 失真项（必须改时刻制）—— P0
| 效果 | 位置 | 问题 |
| --- | --- | --- |
| def_up 铁壁药剂 45%×3回 | alchemy.py:188 / items.py:2053 / skills.py:88-91 | 敌快多招赚/敌慢少招亏，主要失真 |
| reduce_all 团队减伤 | battle.py:5743-5755 / potion_effects.py:276-279 | 同失真；副本侧 instance.py:2626 仍映射 def_up 口径分裂 |
| 敌方减攻 mon_atk_down / _weaken_val | battle.py:4613-4616 / weapon_effects.py:685 | 作用目标行动，按玩家回合计时失真 |
| 敌方 mon_def_up | battle_mech.py:785-790 | 同上 |
| 敌方减速 spd_down | battle.py:4606-4611 | 同上 |
| magic_resist 龙鳞 3回法免 | potion_effects.py:86 / items.py:2061 | 受击消费失真 |
| dodge_pot 影步 3回 / block_pot 岩壁 3回 / thorns_pot 荆棘 3回 | 药水 | 被击/受击消费失真 |
| 护盾 p_shields | battle.py:1778-1794, 5303-5307 | 盾值按受击扣+回合到期双计时，敌快盾秒破/敌慢白嫖 |

## 合理保留（回合制）—— P2
- 玩家输出类（atk_up/crit_up/matk_up/pene_pot/execute_pot/lifesteal_pot/crit_dmg_pot/heal_up/mana_cost_down/full_tension/phys_up）：玩家每回合仅1动，回合数≈出手次数，合理
- DOT 毒/灼/流血/暗蚀：每回合掉血本就是回合语义，合理
- 控制类 stun/freeze/sleep：已是行动级，CTB 正确范式，应推广
- 标记 mark / 印记 fire/ice/thunder_mark：已豁免，对
- 敌方护盾 e_buffs shield 存 HP 值：按伤害扣减，对

## 顺带发现 4 处真 bug（非失真但回合计时损坏）—— P1
1. 特效装备冷却 we_everfrost_cd/we_radiance_cd/we_sentinel_cd/we_deeprock_cd 只写不递减（weapon_effects.py:525/571/633/695），_tick_cooldowns(battle.py:1110-1116) 只 tick self.cooldown → 奥拉圣剑等"冷却3回合"实际永久一次
2. 星辉壁垒 we_starlight_next=5 每5回合刷新从未消费（weapon_effects.py:217）→ 刷新机制死代码
3. 禁疗/重伤 heal_down/_anti_heal_pct 写入但消费缺失（weapon_effects.py:394,721 / affix_effects.py:617）
4. 副本 reduce_all→def_up 误映射（instance.py:2626）

## 推荐方案
**P0（必改）**：防御/减伤/受击消费类改为"受击计数/敌方行动次数"计时
- p_buffs/e_buffs 增加 hits_left 字段，由 _damage_player 与 _enemy_turn 消费递减，回合递减豁免
- 文案同步"3次受击"
- 护盾 p_shields 同理改 hit_left 或纯到期

**P1**：修复 4 处真 bug（特效cd递减、星辉壁垒刷新、禁疗消费、副本reduce_all误映射）

**P2**：保持回合制不动——玩家输出buff、DOT、行动级控制、标记、一次性、敌方HP型护盾
- 将 stun/freeze 的"行动级豁免"模式推广为 CTB 统一计时规范
