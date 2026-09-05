# v180 怪物技能管线化重构（完成版 2026-09-06）

## 状态：✅ 完成（P1-P10，见 git log 5a551b6..8ee75d8）

## 一、目标达成
怪物技能（MONSTER_SKILLS 329 个）全量收编玩家技能管线 `_player_skill`：
- 伤害（231）/ 治疗 heal_self（13）/ 召唤 summon（55）/ 增益 atk_up·def_up·spd_up·shield（29）
- 控制 mech slow·interrupt·stun·silence·freeze（36）
- `_enemy_cast_done` 192 行简化结算删除；`_enemy_release_charge`（蓄力 35 技能）收编；
  `_enemy_turn` 增益/治疗即时分支收编
- 一套 actor 无关技能执行器：施法者=玩家或怪走同一管线

## 二、过程中修复的潜伏 bug（P1-P9）
1. **v177 方向 bug**：管线攻击段 est 硬编码 `self._enemy_stats()`=主怪面板当目标面板 →
   怪打玩家错误用怪自己 def/mdef/韧性 → 伤害虚高 20%。P1 修：`_tgt_is_player` 用玩家面板
2. **默认成长兜底 ×1.4**（鱼鱼指出）：skill_power_mult 没配 p 默认每级+10%，无 SKILL_UP 的
   怪技能按折算等级白吃。P4 删默认（没配=不成长），审计确认零玩家伤害损失
3. **撞名污染**：14 个怪技能 name 撞玩家 SKILL_UP（圣光弹/雷击/龙爪等）→ 误吃玩家成长配置。
   P5 `_skill_up` 按 lv 字段隔离怪技能
4. **58 个无 formula 怪技能**：管线 power 自动分支注入玩家 skill_flat 保底 → 虚高 5 倍。
   P5 批量补等效 formula 段（实测 56/57 ratio=1.00）
5. **MECH_EFFECTS 控制写错目标**：stun/freeze/silence 写 battle.e_buffs（主怪容器）——
   怪打玩家会晕自己。P2 actor 化写 `_tgt_buffs()`；P3 补 slow/interrupt 注册

## 三、效果类收编细节（P6-P8）
- heal_self 13：kind=增益→治疗 + hp_pct:0.15（管线 _skill_heal hp_pct 分支精确等价旧 15%）
- summon 55：加 summon:1 字段（_player_skill 召唤分支 kind 分流前触发，怪施法→_summon_minions）
- 增益即时分支：_enemy_turn kind=增益/治疗 → _monster_cast_playerskill（原 MON_BUFF/SKILL_BUFF
  双表分派废弃）
- buff 刻数：怪施法固定 info.buff_turns 缺省 3（对齐旧 BUFF_TURNS，怪无养成概念不叠折算成长）
- shield 6：SKILL_BUFF_EFFECTS 注册 effect=shield（actor 化写施法者 shields halve=True，
  盾值 max_hp×20%）
- pdot：_skill_hit_settle 命中后统一挂（原只在 _enemy_cast_done 简化段）
- _enemy_mitigate 补鲁莽之心（mr<0 增伤）+ 魔法免伤文案

## 四、门禁
- 新测试 tests/test_numeric_monster_skill_pipeline.py（329 技能不崩 + 效果落地）✅
- run_numeric_tests.py 43 文件全绿 ✅
- 全量 run_all_tests.py --jobs=16：257 过/17 存量红（基线 256/18，零新增还修好 1 个）✅

## 五、遗留（B 层，待新会话）
怪 actor 化（配 class_name/装备/被动/资源当职业 actor）——最大障碍是玩家可变战斗状态
（resources/mech_stacks/p_eff/p_shields/charging）不在 actor dict 而在 Battle 焦点字段，
统一需迁移 + 存档序列化兼容。侦察报告见 workspace/boss_design/v180_actor_gap_report.md
（含身份 if 全量清单 ~60 处 + 改造依赖序）。
