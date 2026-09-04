# 引擎硬编码审计 → 执行批次（v176 深夜推进）

> 三份审计报告（资源连段域/伤害结算域/战斗编排域）汇总，全部问题点按批次归类
> 审计报告原文：cache/delegation/subagent-summary-{0,1,2}-*.txt

## 审计总量
- 职业/线特判：~20 处（集中 1174-1620 与受击尾部 8053-8084）
- 技能名特判：时停领域(已删✓)/安魂曲献祭暗焰(已删✓)/SHADOW_STEALTH_DMG_MULT(数据但用中文key)
- 魔法数字/重复/结构问题：~40 处
- 死代码：~8 处（_reschedule_* 3个/1516 注释/_pvp_enemy_turn/SPD_CT_CAP/BASE_DELAY 常量/_active_keys）
- 架构不合理（F 级）：F1 事件队列不序列化 / F2 单类职责爆炸 / F3 单怪多怪双轨 / F4 instance 模式摇摆 / F5 四份序列化清单手写 / F6 目标隐式传递
- 敌方 AI：全局 0.3 概率无差异化 → 应数据化

## 已完成批次
- ✅ B0：时停领域死代码删除（v153 退役）
- ✅ B0：献祭暗焰死引用移除（v151 退役）
- ✅ B1：SkillKind 类型域（去 kind 中文魔法字符串，battle 34+engine 2+combat 8）

## 后续批次（按风险排序，鱼鱼批准后执行）
### 批次 2（低风险纯清理，行为等价）
- [ ] 删死代码：_reschedule_dot/_reschedule_mech/_reschedule_pet（3函数）、1516 禅意死代码、_pvp_enemy_turn、SPD_CT_CAP/BASE_DELAY 常量、_active_keys、327/332 allies 重复赋值
- [ ] ACT_TICK or 2.0 16 处 → ACT_TICK（常量=1.0 纯噪音）
- [ ] 3739 elegy_dmg 孤儿套装分支（sets 数据无此 effect → 死分支）删除或按数据匹配
- [ ] BUFF_MULT/TEAM_BUFF_KEYS 表 → battle_config.py 数据下沉

### 批次 3（低风险数据字段化）
- [ ] 873 基础法师无资源 → BRANCH_RESOURCE_OVERRIDE 数据加 base 配置
- [ ] 1220-1227 游侠开局满精力 → core_resources 加 start_full 字段
- [ ] 984 满溢转盾 ×5 → core_resources overflow_shield 加 ratio 字段
- [ ] 1555/1634 元素枚举魔法字面量 → E.ELEMENT_MARKS keys 校验

### 批次 4（中风险·词条 cond 消费）
- [ ] 1174/1568/1672/5151 法师元素使守卫 → 词条 cond=element_mage 数据消费
- [ ] 1194/3743 拳师气力判定 → is_chi_skill(info) 公共谓词（读 res_cost/consume_all）
- [ ] 8062 战士血债怒火 → core_resource on_hit 加 scale_by_missing_hp
- [ ] 8077 刺客影舞受击扣连击 → core_resource on_taken_penalty

### 批次 5（中风险·架构单点化）
- [ ] 抽 _is_element_mage(player) 单点 helper（5006/5009/5156 三处统一）
- [ ] 元素法师 _last_element 与职业解耦（5004：只要带 element 即维护）
- [ ] 1516 满弦阈值/职业 → core_resource 数据
- [ ] combo 机制（刺客连段）注册表 cond 化

### 批次 6（较大·敌方 AI 数据化）
- [ ] monsters.py 每怪加 ai 字段（skill_chance/weights/first_move），引擎读数据缺省回落全局 0.3

### 批次 7（大·F 级架构，单独立项）
- [ ] F5 声明式状态字段表（STATE_FIELDS 驱动 to_state/from_state/__init__）
- [ ] F1 事件队列序列化 + 删补排补丁
- [ ] F2/F4 Battle 拆类（InstanceBattle 子类 + 事件总线）
- [ ] heal 乘区装配器 / 暴击装配点 / pmult 对象化（伤害域 2 大重构）

## 红线
- 行为等价迁移，最后统一跑 36 门禁 + refactor_regression（4fab93c9433b）+ git commit

## 深夜推进记录（v176 实际执行）
- ✅ B2 纯清理：删死函数×3/_zen/allies冗余/elegy死分支 + ACT_TICK噪音 + BUFF_MULT下沉
- ✅ B3 数据字段化：基础法师无资源(override 0)/游侠start_full/overflow_ratio/元素枚举keys
- ✅ B4a 元素法师收口：_is_element_mage/_is_element_skill helper 收口 7 处 cls_fa_shi + 元素技能解耦
- ⏸️ B4b 拳师气力判定(1172/3700)暂缓：实测拳师技能数据无 res_cost.chi/consume_all 标记，
      "气力技"在数据层无区分字段，is_chi_skill(info) 方案不成立——
      需先给拳师物理技能加 chi 标记(skills 数据改造)才能解耦，留待独立批次
- ⏸️ B6 敌方 AI 数据化：未开始（怪物 ai 字段）
- ⏸️ B7 F级架构拆分：未开始（事件序列化/声明式状态/拆类）
