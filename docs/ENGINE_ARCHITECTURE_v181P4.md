# 战斗引擎架构文档（v181.P4 重构目标）

> 鱼鱼 2026-09-07 迭代确认中
> 本文档是引擎重构的权威蓝图——先写清楚再改代码。

## 1. 引擎世界观

Battle = 一组 actor 按 sides（阵营）分组，任意 actor 可以执行动作，动作作用到目标。
**引擎没有"玩家/怪物"身份逻辑，只有 actor、side、action、target。**

actor 带 `side` 字段（属于哪个阵营）、`kind` 字段（数据标签：player/monster/summon/pet）、
`human_controlled`（是否真人操作——决定谁等输入、谁按配置自动行动）。

### 核心概念
| 概念 | 说明 |
|---|---|
| **side** | 阵营，sides = {side名: [actor,...]}。任意多个 |
| **actor** | 战斗单位，全同构 dict（buffs/stacks/hp/atk/side/...） |
| **action** | 一次行动 = caster 执行 action（普攻/技能/防御/道具/逃跑） |
| **target** | action 的作用对象：单 actor / side 范围(AOE) / None（无对象技/自我技） |
| **auto_act** | actor 的自动行为配置（怪/随从用它行动；行为树/状态机是外部实现） |

## 2. 行动流程（完整）

### 2.1 人类驱动（玩家回合）
```
命令层: b.actor_act(action, skill_name, actor, target)   # actor=真人操作的玩家
   └→ actor_turn(action, skill, actor, target)
        ├─ defend → _do_defend(actor, ...)
        ├─ flee   → _do_flee(actor, ...)
        ├─ use_item → _do_use_item(payload, actor)
        ├─ skill  → _do_actor_skill(skill_name, actor, target)
        │             └→ _actor_skill(st, skill_name, info, actor, target)
        │                   ├─ K_HEAL → _skill_heal(..., target_ally)   # 治疗队友/自己
        │                   ├─ K_BUFF → _skill_buff(...)                # 增益（写 caster 自己）
        │                   └─ 攻击   → 伤害管线 → _deal_hit/_aoe_damage(target)
        └─ attack → _actor_attack(st, actor) → basic_skill → _actor_skill
```

### 2.2 自动驱动（怪/随从按配置行动）
```
调度: _actor_auto_turn(actor, target)        # actor=要行动的怪/随从
   └→ 控制状态检查(冻结/眩晕/睡眠/破绽) → 蓄力 → AI 决策(读 actor 配置)
        └→ 选技能 → _actor_skill_cast(caster=actor, skill, target)
              ├─ 设 _cast_ctx=actor(施法者)、_target_ctx=target
              └→ _actor_skill(统一管线)
```

### 2.3 关键：技能管线上下文
`_actor_skill` 内部用两个上下文决定"谁在施法、作用谁"：
| 上下文 | 值 | 语义 |
|---|---|---|
| `_cast_ctx` | 施法者 actor（玩家施法=None→_focus；怪施法=怪） | 增益/自我效果的归属 |
| `_target_ctx` | 技能目标（玩家施法=选中的怪；怪施法=target 参数） | 伤害/对敌效果的目标 |

**`_actor_skill_cast` 是唯一正确设这两个上下文的地方**（L7691-7694 保存/设置/恢复）。
玩家路径 actor_turn→_do_actor_skill 也应设（或复用同机制）。

## 3. 作用对象模型（handler 的核心问题）

### 3.1 现状
core handler（词条/mech/效果）无 target 参数，从 battle 猜作用对象：
`battle.enemy`(已删)/`_hit_tgt()`/`_cast_*` 混用 → 单怪碰巧对，多怪/怪施法错。

### 3.2 正确模型（鱼鱼拍板：handler 全部加显式 target 参数）
每个 handler 接收**显式作用对象 actor**，不再自己猜。调用方按语义传：
| handler 类型 | 作用对象 | 调用方传什么 |
|---|---|---|
| 伤害/对敌 debuff/标记/控制 | 被打目标 | `target`（_target_ctx） |
| 自我增益/自疗/自盾（怪 buff 自己） | 施法者 | `caster`（_cast_ctx） |
| 玩家增益技 | 施法者=玩家 | caster（_focus） |
| 治疗 | 被奶的人 | target_ally |
| AOE | 逐目标 | 循环里每目标 |

### 3.3 handler 签名改造
```
旧: def _m_xxx(battle, mval, p_mech, total, logs, ...)
新: def _m_xxx(battle, caster, target, mval, p_mech, total, logs, ...)
    # caster=施法者 actor、target=技能目标 actor（作用对象）
```
- 注册表 dict 值 = handler，调用点 battle.py 传 caster/target
- 但**不是所有 handler 都要两个参数**——按语义：纯自我增益可只加 caster；纯对敌可只加 target
- 先产出手册（每个 handler 归类）再批量改

## 4. 访问器语义定稿（不再混淆）
| 访问器 | 语义 | 何时用 |
|---|---|---|
| `_cast_ctx` | 当前施法者 | 管线内（增益归属） |
| `_target_ctx` | 当前技能目标 | 管线内（伤害/debuff 目标） |
| `_focus` | 命令层焦点 actor（=玩家） | 展示/命令层；玩家即 actor |
| `sides[side]` | 某阵营 actor 组 | 遍历/选目标 |
| `side_of(actor)` | actor 阵营 | 判定 |
| `hostile_sides(side)` | 敌对阵营 | AI 选目标 |
| `_actor_buffs(actor)` | 任意 actor 的 buffs | 读写 buff |

## 5. 移除清单（最终态）
- [ ] battle.enemy property（过渡读取口，测试/命令层改完删）
- [ ] self.enemies 容器（改 sides 派生）
- [ ] _hit_tgt()（过渡——被显式 target 取代）
- [ ] core handler 全部无 target 签名
- [ ] 测试里的 b.enemy 断言改显式

## 6. 验证
- 引擎重构完再跑测试（鱼鱼：先重构完引擎，测试是引擎正确性的验证不是开发拐杖）
- 每模块改完 py_compile + 定向场景（单怪/多怪/怪施法自我增益/AOE/治疗）

## 7. mech/effect 合并（鱼鱼 2026-09-07 拍板：一并改，统一成基于 effect）

### 7.1 现状（数据调研）
- **mech 字段**（skills.py 87 处）：攻击技能的机制标签，如 `'mech': 'bleed', 'mech_val': 2`
  → 命中后对目标附加效果（流血/灼烧/毒/标记/眩晕/降攻）
  → 引擎 MECH_EFFECTS 表（65 handler）分派
- **effect 字段**（skills.py 58 处）：增益/治疗技能效果，如 `"effect": "def_up"`
  → buff 类型（def_up/盾/治疗/免疫）
  → 引擎 SKILL_BUFF_EFFECTS 表（36 handler）分派
- 两者职责：攻击技能用 mech（对敌附加）、增益技用 effect（buff）——但能力重叠（
  如 mark/毒/sleep 在两边都有）

### 7.2 合并目标
统一为 **effect 一条效果管线**：
- 技能数据：攻击技的 `mech` 字段改名/并入 `effect`（或保留 mech 名但引擎统一处理）
- 引擎：MECH_EFFECTS + SKILL_BUFF_EFFECTS + MON_BUFF_EFFECTS 合并成一个 EFFECT_HANDLERS 表
- handler 统一签名：`fn(battle, caster, target, params, logs)`（caster+target 显式）
- effect 参数（mech_val/层数/时长）统一为 params dict

### 7.3 合并后的 handler 分类（作用对象语义不变）
| effect 类型 | 作用对象 |
|---|---|
| 对敌附加（灼烧/毒/标记/睡眠/降攻/控制） | target |
| 自我增益/自疗（怪/玩家强化自己） | caster |
| 治疗 | target_ally |

### 7.4 改造阶段（并入整体重构）
- Phase A: handler 全部显式 caster/target（先做，本手册）
- Phase B: 三表合一 EFFECT_HANDLERS + 统一签名
- Phase C: 技能数据 mech→effect 字段归一

> ⚠️ **收尾承诺（鱼鱼 2026-09-07）**：mech/effect 合并是**必须收尾**的阶段——
> 先完成当前主线（handler 显式 target/caster + enemy 移除），引擎恢复全绿后，
> 回来做 Phase B/C 合并，不许遗忘。Phase A 的 handler 签名改造要为 Phase B
> 预留统一签名（fn(battle, caster, target, params, logs)）方向，避免二次返工。

### 7.5 死代码发现（2026-09-07 读代码确认）
- **MON_BUFF_EFFECTS 整张表（7 handler）引擎零读取**——只有定义 + register +
  测试直调（test_v98_04/v1252）。v180 起怪增益统一走 `_actor_skill_cast` 管线
  （battle.py 注释自证"原 MON_BUFF_EFFECTS/SKILL_BUFF_EFFECTS 双表分派为两套
  代码残余，已废弃"）。→ Phase B 合并时**直接删**，不并入新表。
- **MON_CTRL_EFFECTS（5 handler）引擎也零读取**（只有测试直调）→ 同上删。
- **SKILL_BUFF_EFFECTS（36 handler）只有 battle.py L6228 一处活读取**
  （_skill_buff 内 `SKILL_BUFF_EFFECTS.get(eff)`）→ 活代码，并入新表。
- **MECH_EFFECTS（65 handler）** 由 battle.py `_apply_mech_effect` 查表调用
  （活代码）→ 并入新表。
- 测试直调死表 handler 的点（v98_04/v1252/v101_28f）需在删除时同步改/删。

### 7.6 合并后的真实规模修正
- 死表（MON_BUFF/MON_CTRL）删除：-12 handler
- 活表合并：MECH_EFFECTS(65) + SKILL_BUFF_EFFECTS(36) = 101 handler → EFFECT_HANDLERS
- handler 统一签名 fn(battle, caster, target, params, logs)，按作用对象归类

