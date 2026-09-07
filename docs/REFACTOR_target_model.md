# 战斗引擎重构：作用对象（Target）模型设计文档

> 状态：迭代中（鱼鱼 2026-09-07：边分析边写文档，确认无误再改代码）
> 触发：P4 移除 battle.enemy 时发现引擎"作用对象"语义混乱——handler 无脑
> 替换 battle.enemy → battle._hit_tgt() 导致增益/治疗/AOE 目标错位。

## 1. 现状诊断（读引擎后的发现）

### 1.1 引擎已存在的 actor/目标访问器
| 访问器 | 语义 | 读什么 |
|---|---|---|
| `_tgt()` | 技能管线目标 | `_target_ctx` 优先，无→当前敌 |
| `_hit_tgt()` | 受击/被作用目标 | `_active_target` 优先，无→首个存活敌 |
| `_cast_buffs/_res/_stats` | **施法者**状态袋 | `_cast_ctx`（怪施法=怪）/ 玩家 |
| `_cast_is_side_player()` | 施法者是否 player side | _cast_ctx 是否为玩家 |
| `_pick_hostile_target(unit)` | unit 的敌对目标（AI 用） | sides 敌对阵营 |
| `_resolve_target(player,target)` | 玩家行动目标解析 | 玩家输入/自动 |
| `_resolve_ally_target(target)` | 治疗队友目标解析 | allies |
| `_actor_stats_of(actor)` | 任意 actor 面板 | 按 actor 数据路由 |
| `side_of(actor)` | actor 所属阵营 | actor.side / sides |
| `hostile_sides(side)` | side 的敌对阵营 | sides 关系 |

### 1.2 核心错误（我犯的）
core handler 原用 `battle.enemy`，我全替换成 `battle._hit_tgt()`——但 handler 语义分几类，目标各不相同：
- **怪物自我增益**（mon_atk_up/def_up/自疗/自盾/spd_up）：作用对象 = 施法者自己（怪 A 给自己加攻，却可能写到玩家正打的怪 B 上）❌
- **对目标 debuff**（mon_atk_down/mark/sleep/stun/降防）：作用对象 = 技能目标（玩家施法=被打怪）✓（_hit_tgt 碰巧对）
- **对玩家 buff**（shield/stealth/crit_buff）：作用对象 = 玩家（施法者 player）→ 走 _cast_* ✓
- 单怪 1v1 时"施法者怪"和"被打目标"是同一只，原代码靠这个重合没炸

### 1.3 引擎设计现实
- `_actor_skill` 按 kind 分派：K_HEAL→治疗队友/自己；K_BUFF→增益（写 _cast_buffs 施法者自己）；攻击→伤害管线
- 怪自动行动 `_actor_auto_turn`（原 _enemy_turn）→ `_actor_skill_cast`（设 _cast_ctx=怪、_target_ctx=目标）
- 玩家行动 `actor_turn` → `_do_actor_skill` → `_actor_skill`（_cast_ctx=None=玩家、_target_ctx=选中目标）

**技能管线目标其实由 `_target_ctx` 承载，施法者由 `_cast_ctx` 承载**——两个上下文在技能结算期间是有效的。

## 2. 目标模型（Target State）

### 2.1 作用对象分两类，都由"当前动作上下文"决定
1. **施法者（caster）**：`_cast_ctx`（怪施法=怪 dict；玩家施法=None=玩家 self._focus）
2. **技能目标（target）**：`_target_ctx`（玩家施法=选中的怪；怪施法=玩家/被打目标）

### 2.2 handler 作用对象映射规则（按语义）
| handler 类型 | 作用对象 | 正确写法 |
|---|---|---|
| 自我增益/自疗/自盾（怪用技能强化自己） | 施法者 | `battle._cast_ctx or battle._focus` 或显式 actor 参数 |
| 对目标 debuff/控制/标记（给被打者上负面） | 技能目标 | `battle._target_ctx or battle._tgt()` |
| 对玩家 buff（玩家的增益技） | 施法者=玩家 | `battle._cast_buffs()`（已是施法者袋） |
| 治疗 | 显式 target_ally | `_resolve_ally_target` 已处理 |
| AOE | 多目标集合 | 调用方逐目标循环（_aoe_damage 已显式传 target） |
| 伤害 | 显式 target | `_deal_damage(target=...)` 已显式 |

### 2.3 结论
- **handler 不应该自己猜目标**——它应接收显式传入的"作用对象 actor"参数
- 或至少：区分"自我"（_cast_ctx）与"对目标"（_target_ctx），替换成正确的访问器
- 单怪重合是历史侥幸；多怪/怪施法场景必须显式

## 3. 分批改造计划（待细化确认）
### D1: 读引擎全部 handler 调用链，产出手册（哪个 handler 在什么上下文被调、应作用谁）
### D2: 定义统一访问约定：handler 加 caster/target 参数 or 文档化的上下文读取规则
### D3: 逐模块替换（battle_mech/affix_effects/conds/we/food/effect）
### D4: 全量回归验证（重点多怪/怪施法/自我增益场景）

## 4. 待确认问题（问鱼鱼）
- handler 用显式参数（侵入大但彻底）还是上下文访问器（_cast_ctx/_target_ctx）？
- 怪物自我 buff 的 handler 语义确认：mon_atk_up 是"怪给自己加攻"（应写自己）？
