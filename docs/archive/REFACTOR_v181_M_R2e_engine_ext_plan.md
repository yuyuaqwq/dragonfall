# v181.M 引擎扩展方案（affix 动态 cap + 牧师信仰负载制闭环）

> 2026-09-09 鱼鱼拍板：要动核心引擎的给方案审批；纯配置/装配层直接做。
> 审批结果（鱼鱼 2026-09-09）：方案 A ✅ / B2 ✅ / B3 改为 effects float 通用层 ✅
> （鱼鱼拍板：小数层是通用能力，非 0.7 单点——内部 float + 展示 floor 取整）。
> 状态：已批，实施中（M-R2e）。

---

## 方案 A：affix 资源上限词条（动态 cap）

**问题**：EFFECT_RULES cap 是静态 int（怒气 10/连击点 5…），effects.py 叠层
clamp 到静态 cap（`n = max(0, min(cap, cur + amount))`）。7 条上限型 affix
（rage_forge/divine_radiance/holy_heart/rhythm_badge/chi_limit/full_pack/
energy_blade）要求「资源上限 +N」→ 现网无法生效（cap 动态机制缺口，R4 留记）。

**设计（最小侵入，stat_bonus 同哲学）**：

1. **actor 侧 cap 修正容器**：`actor["cap_bonus"] = {资源key: 增量int}`——纯 flat 增幅，
   零引擎语义（对齐 stat_bonus 09-08 拍板容器哲学）。开战装配时由装备/词条写入。
2. **clamp 查 cap 改动态**：effects.py 叠层 clamp 处与 EFFECT_RULES cap 查询处
   （引擎内 cap 读取收敛为一个小函数）→ `cap = 基础cap(EFFECT_RULES) + actor.cap_bonus.get(key, 0)`。
   涉及点：effects op=add/set clamp、schedule period gain clamp、R4 affix gain clamp
   （同一收敛函数）。
3. **装配**：affix 翻译器（battle_equip_proc _START_TRANSLATORS）新增 cap_bonus 词条族
   7 条 → 装配时写 `actor.setdefault("cap_bonus", {})[key] += N`。数值取词条数据
   （affixes.py/词条表旧值，迁移前抄录）。

**验收**：装备 rage_forge → 怒气 cap 12（10+2）→ 叠层能到 12 → 卸下恢复 10；
叠层超新 cap 时 clamp 生效不溢出。测试覆盖。

**量级**：中（引擎 cap 读取收敛小改 + 翻译器 7 词条 + 测试）。

---

## 方案 B：牧师信仰负载制闭环（faith 攒→兑现→档位→衰减全链路）

现状（M-R2d 后）：faith 已能攒（治疗施放 +2/受击 +1，cap 10）。但消费端与
机制端全断：
- 卸负技能（mech=faith_unload「卸 3 点信念自身回血 80% 魔攻」）**无兑现执行器**
- 负载四档（0-3 清醒 / 4-7 专注 治疗×1.25 / 8-9 透支 ×1.5 / 10 过载 清零+全队回复）
  **无乘区无数据**（load_tiers 随 core_resources R2c 退役删除，旧 passive_procs
  tick_faith 为无引用残留）
- 每刻 -0.7 衰减**无载体**（battle2 effects 层 int stacks + schedule period gain 只认正数）

### B1 faith_unload 兑现（装配层——直接做，不等批）

**不改引擎**。MECH_CASH 声明表加 `faith_unload` 行（R1c heal_clear 同族先例：
施放时查 faith ≥ 3 → 扣 3 层 → 自身回血 80% 魔攻+成长）。执行器复用 heal 动作。

### B2 负载档位治疗乘区（动引擎：heal 乘区钩子）

**问题**：battle2 heal 动作（actions._do_heal）乘区链只有技能公式 × cond_mult ×
(1+面板 heal_power)，**无装配层乘区钩子**（dmg 侧有 dmg_calc 钩子链可挂词条）。

**设计**：
1. **数据（纯配置，先做）**：EFFECT_RULES faith 条目扩展 `load_tiers` 字段
   （逐字迁 v130 设计）：
   ```python
   "load_tiers": [
       {"max": 3, "heal_mult": 1.00, "label": "清醒"},
       {"max": 7, "heal_mult": 1.25, "label": "专注"},
       {"max": 9, "heal_mult": 1.50, "label": "透支"},
       {"max": 10, "heal_mult": 1.00, "overload": True},  # 过载：清零+全队回复
   ],
   ```
2. **引擎钩子**：actions._do_heal 乘区链加装配点（heal_calc 钩子，对齐 dmg_calc
   现成模式：装配层查 actor faith 层 → load_tiers 表 → 返回 heal_mult 乘入）。
   装配器（class_mech_proc）为牧师挂 heal_calc 钩子。
3. **过载**：faith 满 10 时的清零+全队回复（旧 overload_heal_pct 0.015 × max_hp）——
   由档位钩子同点处理（叠层到 10 触发清零+全队回复，防每刻重复 = 过载帧标记）。

**量级**：中小（heal 动作加钩子点小改 + 装配查表 + 测试）。

### B3 每刻 -0.7 衰减（动引擎 or 数值口径，三选项拍板）

| 选项 | 做法 | 改动面 | 语义 |
|---|---|---|---|
| **i（彻底）** | effects stacks 支持 float（含消费端取整策略） | 大（effects 层 + 所有叠层消费点审计） | 精确 0.7/刻 |
| **ii（引擎小扩）** | schedule period dir=gain 支持负 amount（int 整数刻度：如 amount=-7 interval=10 刻 = 每 10 刻 -7，均值 0.7） | 小（schedule gain 分支放开负值 + clamp 0） | 0.7 均值、10 刻一跳 |
| **iii（改口径）** | 衰减改整数（如每刻 -1 或每 3 刻 -2） | 无引擎改动（纯数值） | 需改 v130 数值权威（0.7 → 新值），策划拍板 |

> 备注：设计意图是「慢衰减」——0.7/刻 ≈ 14 刻从满归 3（清醒档）。选项 ii 保持均值
> 语义最接近原设计且改动小。选项 iii 若改每刻 -1 = 10 刻清零，手感明显更快（档位
> 停留时间缩短），需重校平衡。

---

## 附：已裁定不加（记录锁定，防后人误解）

1. **牧师攻击系攒信念**：不加。v130 旧表 on_attack:0（攻击不攒）+ 审判之矛 desc
   「（单体输出，不增信念）」明示——攻击系不攒是设计语义（M-R2d 缺口注释中
   「反证攻击系默认攒点」的解读有误，以本裁定为准）。
2. **普攻攒战意/连段**：不加。v151 语义战意/连段由技能 mech 命中攒（技能 desc 明写），
   普攻不攒是有意设计（防普攻无限攒→冷静/终结永动机）。
3. **v139 形态层 / 元素反应 / melody**：独立立项，非本批。

---

## 批次建议

| 批 | 内容 | 依赖 | 类型 |
|---|---|---|---|
| M-R2e-1 | B1 faith_unload 兑现 + load_tiers 数据重建 + faith 条目扩展 | 无 | 直接做 |
| M-R2e-2 | 方案 A affix 动态 cap（引擎收敛 + 7 词条） | 方案 A 批 | 等批 |
| M-R2e-3 | B2 heal_calc 钩子 + 档位乘区 + 过载 | B2 批 | 等批 |
| M-R2e-4 | B3 衰减（i/ii/iii 选一） | B3 拍板 | 等批 |
