# v180 战斗引擎审计汇总（4 子 agent 全量审计 + 修复清单）

> 2026-09-06 深夜~07 凌晨 | 4 并行子 agent 只读审计 battle.py/engine.py/core 各注册表
> 报告原文：`workspace/boss_design/audit_20260907/`（4 份）
> 代码仓 HEAD：e46bb8c（全量 279/279 + 数值 45/45 绿，已推 GitHub）

## 一、审计范围

| # | 子 agent | 报告文件 | 审计对象 |
|---|---|---|---|
| 0 | 伤害/身份 | audit_damage_identity.md | _damage_enemy 乘区/attacker/等级压制/class_name 残留/calc_damage 直调/治疗双轨 |
| 1 | 效果系统 | audit_effect_system.md | affix/food/potion/weapon/mech/poi 跨文件重复+handler 硬编码+数据断链 |
| 2 | 状态/序列化 | audit_state_serialization.md | 旧焦点字段残留/to_state-from_state/companions 一致性/tick actor_ref |
| 3 | 随从 actor | audit_companion_actor.md | kind/tid/名字特判残余/宠物技能双轨/挡刀双轨/字段未消费 |

## 二、✅ 已修复并提交（本轮）

| commit | 修复 | 来源 |
|---|---|---|
| 8bd86ea | 随从死亡清理跳过无 hp 宠物 actor（原每次玩家行动误删宠物）；死亡契约只牺牲 kind=summon | 审计2 问题1/2 |
| 2d91bc0 | 等级压制基准改 attacker 自身等级（宠物按宠物级，无 level 回落玩家）；_companion_act true 分支统一 calc_damage | 审计0 问题2/隐bug |
| 9a5cc06 | potion def_down 收敛到共享 action_def_down（消除第三份实现） | 审计1 §1.1 |
| e46bb8c | last_element 补序列化（元素连发跨行动记忆） | 审计2 问题4 |

## 三、🔴 P0 效果错误（需鱼鱼拍板后修，涉及数值设计）

审计1 §2.2 发现多个"数据声明 vs 代码行为"脱钩的真 bug：

1. **mortal_wound 致伤重击**：代码 `_anti_heal_pct=0.50`（50% 禁疗），数据 desc 说"受治疗-30%"——玩家吃 50% vs 宣称 30%。**哪个对？**（若 50 是 buff 过的数值，desc 该改）
2. **memory_tear 记忆撕裂**：数据想"沉默 1 刻"，代码却做"降攻 15%"（mon_atk_down+_weaken_val）——**效果类型错乱**。数据对还是代码对？
3. **arcane_echo 秘法回响 / sanctum_light 圣殿辉光**：写了状态但**全引擎 0 消费** → 装备效果白板（写了没人读）
4. **siphon 汲魂**：代码 5% 吸血 vs 数据 3%，且没做数据声明的"驱散 1 层增益"
5. **element_thunder 及 5 个词条附加伤害**：绕过 Boss 护盾过滤（与已修的 fire/ice 同款 bug）
6. **DOT 死字段**：所有 handler 写 `debuff.pct/turns` 但引擎 `_tick_actor_dots` 只读 DOT_DEFS 系数——pct/turns 全白写，desc 宣称数值不生效

## 四、🟠 结构性重构建议（建议立项，独立批次）

1. **`_heal_actor` 统一治疗核心**（审计0）：全引擎 20+ 处 `hp=min(max_hp,hp+heal)` 直写，无统一受疗/禁疗/溢出转盾钩子；怪治疗走玩家管线被玩家被动污染
2. **裸 calc_damage 收敛**（审计0）：~20 直调点不吃穿透/公式级封装；`_aoe_damage`/`_guard_redirect_check` 靠反推等效 atk 是 `_damage_enemy` 只收 dmg 的恶果
3. **宠物技能收编 companions auto_act**（审计3 P0）：宠物 8 skill_type 仍走 `_pet_skill_turn`/PET_SKILL_EFFECTS 专用注册表，与 `_companion_act`（只认 basic_atk）双轨
4. **挡刀双轨统一**（审计3 P0）：`_pet_block_check`(mode=absorb) vs `_guard_redirect_check`(mode=redirect) 并存，pet guard 对通用逻辑不可见
5. **weapon_effects 数值下沉数据行**（审计1 §2.3）：~80 武器特效数值全在代码，与鱼鱼数据驱动铁律冲突
6. **tick actor_ref 支持 companion**（审计2 问题3）：宠物卡序列化被丢靠兜底补挂，节奏重置

## 五、🟡 低危记录（可后置）

- 审计3：skeleton tid/"骷髅"名字关键词特判 4+ 处 → 建议 tags/undead 字段；`hidden`/`untargetable`/`eats_aoe` 字段零消费（前两者是"未来字段"，eats_aoe 语义静默失效）
- 审计2 问题5：from_state 恢复 tick 卡 actor 悬空（碰巧安全靠保险丝）
- 审计2 问题7：副本每行动重建 Battle，tick_effects 不跨行动（与野外不一致）
- 审计0：`_pvp_enemy_turn` 僵尸代码；`_res_gain` 用 class_name 区分玩家/怪资源链
- 审计1 §4 数据断链：3 件死 weapon_effect 键、铁壁药膏 30% 被首个命中规则吞成 15%、magic_resist 药剂空转、食物 shield/处决/精准数值硬编码

## 六、给鱼鱼的决策点（明天）

1. §三的 P0 效果错误：每个"数据 vs 代码"哪个是设计意图？（多数建议按**数据 desc** 对齐——那是策划声明，但需确认是否有意热修没改 desc）
2. §四的结构性重构做不做、先做哪个？（我建议优先级：heal_actor > 宠物收编 > 挡刀统一 > weapon 数值下沉 > calc_damage 收敛 > tick actor_ref）
3. 战斗引擎核心改动是否仍按"设计文档先行 + 分阶段全量回归"推进（铁律）
