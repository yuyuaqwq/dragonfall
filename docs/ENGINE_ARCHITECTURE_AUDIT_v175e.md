# 引擎代码分离/数据驱动架构审计（v175e）

> 触发：鱼鱼"职业效果是不是硬编码进引擎，不应该数据驱动/代码分离吗"
> 日期：2026-09-05 ｜ 审计对象：game/battle.py(8105行) engine.py(1210) core/battle_mech.py(2038) core/battle_conds.py(534) data/skills.py(4152) data/battle_config.py(651)

## 一、现状：混合架构（骨架数据驱动 + 局部硬编码）

### ✅ 已经是数据驱动的（好消息）
1. **技能数据**：game/data/skills.py（4152 行纯数据：技能名/lv/mp/power/cd/cast/hits/exprs/desc）
   - 伤害公式 exprs（如 `atk*1.6 + 16 + player_lv*5.4 + skill_lv*12.8`）→ 引擎解释执行，加技能不改码
   - 技能等级/解锁/CD/MP/段数/机制字段全数据
2. **机制注册表**：core/battle_mech.py `@register(MECH_EFFECTS, "zhan_yi_fury")` 63 个注册
   - 攒怒/狂暴/毒层/元素印等机制 → 数据键触发，注册表分发，加机制不改主流程
3. **条件注册表**：core/battle_conds.py `@register(...)` 44 个（player_mech_stacks/enemy_hunt_mark 等）
4. **战斗常量**：data/battle_config.py（SKILL_PMULT_CAP/DUAL_FORM_CFG/FOCUS_CFG 等）
5. **职业核心资源**：data/core_resources.py（每职业 rage/energy/cp/chi/faith + dual_form 形态）

### ❌ 硬编码问题点（battle.py 8105 行大杂烩）
1. **职业特判硬编码**（~20+ 处）：
   - `cls == "cls_fa_shi" and not (path and tier)` (873)
   - `kind == "物理" and player.class_name == "cls_wu_seng"` (1194 拳师)
   - `cls == "cls_fa_shi"` 元素法师转职特判 (1568/1594/1672/5006/5009/5156 共 6+ 处)
   - `cls_you_xia` 能量特判 (1227/1525)
2. **技能名硬编码**：
   - `skill_name == "时停领域"` (1356)
   - `skill_name in ("安魂曲", "献祭暗焰")` (3744)
   - 各版本注释显示"原硬编码技能名，改名即失效"→ 已部分修复（v109.2 数据驱动化）
3. **版本号分层注释**：v1.x ~ v175 累计 40+ 个版本补丁逻辑交错在 battle.py
   → 每版本加"特判"导致函数越来越长、难以测试

### 本质问题
- **数据驱动已做 70%**（技能/机制/条件/常量），新内容尽量走数据 ✓
- **但 battle.py 主流程仍是 8000 行单体**：职业特判/历史补丁/边缘分支混在一起
- 每加新职业/新技能若涉及"独特交互"→ 开发者倾向在 battle.py 加 if（因为注册表没覆盖）

## 二、建议方向（按优先级）

### P0：审计清单化（低风险高收益）
把 battle.py 里的职业/技能特判 grep 出来列清单（约 30-40 处），逐条标注：
- 能否下沉到数据（effect/mech/cond 字段）？
- 能否移到 battle_mech/battle_conds 注册表（v2 数据化）？
- 属于临时补丁 → 可否删除/收敛？

### P1：机制注册表扩容
battle_mech 已有 63 注册，把常见职业特判转成新 mech effect：
- cls_fa_shi 元素法师 → 数据 effect（element_mage 已有 cond，扩展消费端）
- 拳师物理特判 → mech 层加成注册
- 时停领域 → 注册成 cond/effect 数据键

### P2：技能效果 DSL/表驱动（大工程，需策划案）
理想态：技能效果 = 数据表（{effect: x, params: {...}}），引擎只做通用解释器
- 现状 desc 是给人看的文案，机制分散在代码
- 目标：desc 语义 = 数据字段（charge/consume/summon/empower...）自动生成，引擎读数据执行

### P3：battle.py 拆分（长期）
8105 行按域拆：伤害结算/承伤/资源/被动/词条/宠物/AOE...

## 三、风险
- P2/P3 是大重构，动引擎核心 → 必须 35 门禁全绿 + 真引擎矩阵回归
- 数据驱动改造要防"过度抽象"：机制注册表已经证明可行（63 个 mech 数据化后平衡工作大幅简化）
- 铁律：改造每步 commit + 策划案同步（参照 v175e 副本重构流程）
