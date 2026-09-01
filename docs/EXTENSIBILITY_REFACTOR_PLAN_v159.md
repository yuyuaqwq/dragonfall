# EXTENSIBILITY_REFACTOR_PLAN_v159.md — 通用表达式数值公式（伤害/治疗/增益/装备效果）

> 日期：2026-09-01
> 触发：鱼鱼拍板「数值的公式可以任意自定义」「buff、装备效果等等都要支持用这个公式来配置数值」
> 范围：engine（表达式解释器）+ battle.py（治疗/增益/护盾结算）+ affix_effects（装备效果）+ 技能/装备数据
> 状态：🛠️ 进行中

## 1. 问题

v156 formula 是**固定模式**（每段 `{stat, mult, flat, type}` = 属性×mult+flat 加总），
公式结构本身不能自定义：
- 不能写 `atk×0.8 + 玩家等级×5`（无 player_lv 变量）
- 不能写 `(max_hp×0.05 + atk×0.3) × (1+技能等级×0.1)`（无括号/混合成长）
- 治疗/增益/护盾/装备效果更是写死数值（不走公式）

鱼鱼要求：**数值公式任意自定义**，伤害/治疗/增益/装备效果全部支持。

## 2. 目标架构：表达式字符串 + 预编译操作数栈

```
技能/装备数据：
  "formula": [{"expr": "(atk*0.8 + player_lv*5) * (1 + skill_lv*0.1)", "type": "phys", "skill_flat": true}]
  "heal_expr": "(matk*1.5 + 20) * (1 + skill_lv*0.08) + max_hp*0.02"
  "buff_expr": {"atk_up": "30 + player_lv*2 + skill_lv*3"}
  "shield_expr": "max_hp*0.08 + 15"

引擎：
  compile_expr(expr) → 操作数栈（加载时预编译一次，缓存）
  eval_expr(code, vars) → 数值（战斗时纯数字运算，无字符串解析）
  resolve_formula 段支持 "expr" 字段（替代 stat/mult/flat）
  _skill_heal / SKILL_BUFF_EFFECTS / 装备效果 统一接入 eval_expr
```

### 可用变量（白名单）

| 变量 | 含义 |
|---|---|
| atk / matk / def / mdef | 攻击/魔攻/防御/魔防 |
| max_hp / hp / spd / crit | 最大生命/当前生命/速度/暴击 |
| player_lv | 玩家等级 |
| skill_lv | 技能等级 |
| crit_mult | 暴击倍率（1.5） |
| target_max_hp | 目标最大生命（敌方） |
| base | 技能基础值（skill_flat 注入后） |

### 支持语法

- 四则运算 `+ - * /`
- 括号 `( )`
- 一元负号 `-x`
- 数字字面量、变量引用

## 3. 性能设计（鱼鱼关注点）

1. **解析一次**：技能/装备表加载时 compile_expr → 操作数栈（~294 技能 × 1 次）
2. **战斗纯数字求值**：eval_expr 跑操作数栈（微秒级，快过现在 dict 段循环）
3. **安全**：白名单 tokenizer，不 eval 用户输入

## 4. 迁移步骤

1. ✅ 引擎：compile_expr / eval_expr 表达式解释器（engine.py）
2. ⏳ resolve_formula 段支持 "expr"（伤害）
3. ⏳ _skill_heal 支持 heal_expr（治疗）
4. ⏳ SKILL_BUFF_EFFECTS 支持 buff_expr（增益）
5. ⏳ affix_effects 装备效果支持 expr
6. ⏳ 数据：技能/装备逐个配表达式
7. ⏳ 测试 + 全量回归

## 5. 一致性保证

- 未配 expr 的技能完全回退旧逻辑（行为不变）
- 已配的：表达式即唯一数值来源
- 每批独立 commit + 全量回归

## 6. 风险与回滚

- 风险：表达式解析器 bug → 单测兜底（加减乘除/括号/变量/优先级全覆盖）
- 回滚：git checkout 秒回
