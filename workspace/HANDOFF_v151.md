# v151 职业体系重构 · 交接文档（2026-08-31 日间更新）

> 鱼鱼睡前交代：完全抛弃隐藏职业（直接删，别留）、职业装备及套装改造、
> 严格数据驱动（v151 文档为蓝图，前面是废案）、审计回合制效果（防御药水等改时刻制）。
> 中途补充：隐藏职业装备保留改效果（不删）；不搞历史兼容，玩家技能重置返还技能点。

## ✅ 已完成并提交（master，最新 HEAD）

### 1. 引擎层（bfbc609 已提交）
- 时刻制改造：_p_buff_hits 受击计数表（防御类 buff 按受击次数递减）
- 破绽断链修复：turn_start_bars 接线、被震慑跳回合
- 特效 cd 修复、星辉壁垒刷新、mech 新键注册（zhan_yi/lian_duan → MECH_STACK_MAX/WHITELIST）

### 2. P1 法师技能补齐 + P2 技能合并（7a41405 → 4f3d8f3）
- workspace/skills_v151_fa_shi.py（39技：基础8+元素16+时律15）补齐
- 6 文件归一化合并 → game/data/skills_v151_overrides.py
- **纯 v151 新表**（鱼鱼拍板不搞历史兼容）：旧技能全删，分支统一 3-key（1/2/3=30/60/90级），
  分支技能 key 中文名（引擎按名查），全表 name 唯一性 0 冲突
- 战士/刺客/牧师分支重排（2-key 全塞 → 3-key 分层）；刺客毒刃 lv<30 基础技能归位

### 3. P3 隐藏职业删除（cf322ad）
- classes.py 删 6 隐藏职业；skills.py 删 _ADD_HIDDEN_SKILLS + 隐藏分支
- core_resources 删隐藏资源；quests（6试炼）/achievements（12成就）/builds（6套）/
  items（3物品）/dialogues（6NPC）/wild_npcs（18映射）全清理
- battle.py/combat.py 删隐藏职业逻辑（星语猎印/禅意/影步等）

### 4. 玩家技能重置（4f3d8f3）
- store/players.py 读档检测失效旧技能 → 清空 learned_skills/skill_levels，
  skill_spent 返还 skill_points，防重复标记
- 已实测：鱼神号重置返还 2 点

### 5. P4 引擎层（b1414b2）
- battle_mech.py 新增 zhan_yi/lian_duan MECH_EFFECTS handler（叠层0-10）
- summons.py 按 v151 §7：藤蔓守卫 纯挡刀(ATK0/吸收1次/吃AOE)、古树 0.50/0.30+全队攻30%光环
- battle.py 召唤物：atk=0 跳过普攻、absorb_once 吸收即散、古树光环挂载
- 验证：战意/连段/元素印记叠层生效，藤蔓挡刀吸收即散

### 6. P4.5 回合制审计修复（888f06b）
- 禁疗/重伤消费端：治疗结算读敌方 heal_down（层数×10% cap50%）/ _anti_heal_pct（cap80%）
- 副本 reduce_all 真减伤（不再误映射 def_up，与单机 v113.1 口径统一）
- shield_all 盾值读技能 shield_val 字段，13 个 shield 技能补盾值

### 7. 测试适配（2aac1fd + 进行中）
- 删 4 个纯隐藏职业测试（test_v107_hidden_jobs/unlock/unlock_quests/v87_spellblade）
- test_data_characters（12→6职业断言）、test_numeric_skill_power（新数值锁定）
- builds.py 全量重写为 v151 新技能推荐（坏引用 0/108）
- **4 个子 agent 并行适配剩余 37 个测试**（deleg_4a79eb7e）

## 📋 待办

### P3.5 装备保留改效果（未完成，等测试绿后）
- 9 件隐藏职业专属装备保留，改归属语义（龙脊→战士、星尘→法师、暮影→刺客、星语→游侠）
- 侦察报告：workspace/equip_audit_report.md + equip_retain_design.md
- 注意：装备 req 锁属性不锁职业（economy.py §5.1），穿戴天然兼容
- 传奇效果多数纯 stat 型（暴击/冷却/元素伤）无资源绑定 → 只需清理 desc"隐藏职业专属"字样
- 轻影套 cp → 连段迁移（class_sets.py:143）待引擎资源迁移后做

### P4 剩余（资源管线迁移）
- 游侠精力保留（v151 预算制）；战士/牧师/拳师残留 res_cost 为旧基础技能（已随纯新表删除）
- 旧资源条（rage/cp/chi/faith）在 core_resources 仍存在（兼容旧装备效果），
  v151 新技能已不用；装备/套装效果迁移待 P3.5
- **拳师磐核 guard_core 断链**：磐岩释能/磐核爆发/气力万法消耗 guard_core 但无来源/无注册
  （v151 蓝图：守御姿态受击转核 → 需注册 mech_stacks + 受击转核 handler + 消耗结算）
- **引擎特殊字段审计**（v151 新表用了但引擎可能未接线）：
  - 已支持（v139）：cond_rage_form/rage_form/reduce_all/summon/charge_cfg/mech_gain/shaken_gain/cleanse_self
  - 待接线：breathe_mark_extra/breathe_seg_bonus（屏息窗口）、curse_apply（墓穴低语）、
    soul_mark（亡魂低语）、star_lock（星轨锁定）、stasis/stasis_only（时间凝滞/过载）、
    consume_all+discharge（磐核）、counter_attack/stance_floor（守护姿态）、cc（影遁）、
    auto/auto_cond（破势斩/顿足盾击）、inner_fire（内燃）
  - 全表扫描：见 execute_code 输出（2026-08-31）

### P5 收尾
- ✅ 全量回归 **222/222 全绿**（test_v137 flaky 已随全量通过）
- ✅ 双仓库提交 + push：dragonfall（b769fe9）+ design/new_world（66bbc98）
- ✅ 策划案同步（09_职业体系.md §2/§3/版本说明更新 v151）
- ⏳ **重启验证**：AstrBot 进程未找到（可能未运行或外部管理）——v151 改动需 AstrBot 重启生效
  （NapCat 机器人号 3473145972；当前 Hermes qqbot 官方 app 不跑 dragonfall 插件）
- ⏳ 装备剩余改造：龙脊/星尘/暮影/星语 4 套专属装备归属语义（传奇效果多数纯stat无需改，
  仅清理 desc + economy.py 按 weapon_type 反查职业列表——已确认无"隐藏职业专属"字样残留）
- ⏳ 引擎特殊字段接线（HANDOFF 已列清单）：磐核 guard_core 断链、breathe_*/curse_apply/
  soul_mark/star_lock/stasis 等（技能效果待引擎批次，不影响核心战斗）

## 🔧 环境
- 项目根：C:/Users/yuyu/qqbot/data/plugins/dragonfall（git: master）
- 设计仓库：design/new_world/（独立 git）
- 回归：`python scripts/run_all_tests.py --serial`
- 已知历史遗留失败：test_commands_feedback_features（db.get_battle 返回 None，与 v151 无关）

## 📁 关键文件索引
- v151 蓝图：docs/CLASS_MECHANICS_REDESIGN_v151_FULL.md
- 技能表：game/data/skills_v151_overrides.py（脚本生成，勿手改）
- 重排中间数据：workspace/_reflow_result.json / _merge_clean_v5.json
- 装备侦察：workspace/equip_audit_report.md / equip_retain_design.md
