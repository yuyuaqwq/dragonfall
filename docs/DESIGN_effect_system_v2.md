# 效果系统 v2 设计（Effect System v2）——替换旧效果系统

> 2026-09-08 鱼鱼拍板：像战斗引擎 v2（battle2）一样，做**效果系统 v2**——
> 独立设计文档、独立实现、**整体替换旧效果系统**（battle_mech/weapon_effects/affix 三套并存）。
> 本文档是效果系统 v2 的主方案（对标 docs/REFACTOR_v181P4_FULL_PLAN.md 之于 battle2）。
>
> 关联文档：
> - `docs/REFACTOR_v181P4_FULL_PLAN.md` — battle2 引擎主方案（本效果系统是它的 Part 3 展开）
> - `docs/REFACTOR_v181P4_effect_time_system.md` — 效果时效收口（buffs 到期/盾 expire/消费规则）
> - `docs/REFACTOR_v181P4_class_mech_decouple.md` — 职业机制与引擎解耦（C 类机制留给上层）

---

## Part 1：现状诊断（为什么必须重建）

### 1.1 旧效果系统实测（四文件 5051 行、多注册表并存）

| 文件 | 行数 | 注册表 | handler 数 | 触发链 |
|---|---|---|---|---|
| `core/battle_mech.py` | 2156 | MECH_EFFECTS | 65 | 技能 mech 字段 |
| | | SKILL_BUFF_EFFECTS | 36 | 技能 effect 字段 |
| | | MON_BUFF_EFFECTS | 7 | 怪 buff 模板 |
| | | MON_CTRL_EFFECTS | 5 | 怪控制模板 |
| | | BOSS_MECHS | 9 | Boss 机制（enrage/summon/phase） |
| `core/weapon_effects.py` | 487 | WEAPON_EFFECTS（79 key 已族化 C2-C10） | 族执行器 | 装备特效事件 |
| `core/_we_executors.py` | 1034 | 族执行器 ~72 | 族 | 同上 |
| `core/affix_effects.py` | 1374 | HIT_EFFECTS / TAKEN_EFFECTS + 46 affix 内联 | 46+ | 命中/受击/词条触发 |
| **合计** | **5051** | **~10 注册表** | **240+** | **~19 事件时机** |

### 1.2 核心病灶（为什么必须替换而非修补）

**① 三套并存、语义分裂**
- battle_mech：技能 mech/effect 字段 → 散 handler（65+36）
- weapon_effects：装备特效 → proc 事件分发（79 key）
- affix_effects：词条 → HIT/TAKEN 注册表 + 46 内联
- 同一件事（如"上护盾"）在三个文件各写一遍 → 鱼鱼北极星"每个动作全项目只写一次"被破坏

**② 效果数值藏在名字表（BUFF_MULT 病）**
- 技能数据只有 effect 名（战吼 dict 无数值），倍率藏 BUFF_MULT 26 键名字表
- 靠枚举键名表达强度档（atk_up/small/big/strong/food_atk_up）→ 配置与效果耦合
- 换数值 = 改表 + 可能改键名；换配置 ≠ 新游戏

**③ 触发链硬编码**
- ~19 种事件时机散在 battle.py 各处手写 if/proc 调用（battle_start/on_skill/on_heal/
  on_taken/turn_start/enemy_act/on_attack/on_cast/on_crit/kill/threshold...）
- 新效果要接线 = 在 battle.py 找对时机手动插调用 → 漏插 = 效果静默失效

**④ 效果即状态，状态语义乱**
- buffs 值三种形态混存（expire_at/turns/int 剩余刻，v152 自认兼容）
- 控制/一次性/受击计数/永久 无统一消费规则表
- 护盾 v101.28d 起独立 shields dict（value/expire_at）但 battle2 没跟上

### 1.3 battle2 效果系统现状（已有雏形，但收敛度不足）
- `battle2/effects.py`：动词执行器 7 个（control/buff/shield/cleanse/cleanse_all/state_add/state_spend）
- `game/data/battle_rules.py`：STATE_EFFECTS（17 key）+ EFFECT_ACTIONS（23 名词映射）+ BUFF_STAT_KEYS（7 键，**要退役**）
- 实测：技能数据 187 effect 名词 + 13 mech 名词，battle2 rules 只映射 ~23 → **181 名词静默跳过**

---

## Part 2：目标架构（效果系统 v2 世界观）

### 2.1 一句话
> 效果 = **名词效果（数据声明）→ 动词动作（引擎执行）** 的翻译 + 统一注册 + 统一触发 + 统一生命周期。
> 引擎只认识动作（control/buff/shield/state/...）和通用规则；一切名词、数值、时长、强度都在配置。
> 换一套效果配置 = 换一套技能/装备手感 = 新游戏。

### 2.2 分层（与 battle2 北极星同构）
```
┌─────────────────────────────────────────────────┐
│ 游戏层（data/）：技能/装备/词条数据 + 规则表      │   ← 换这层 = 新游戏
│   SKILL_DEF  技能声明（含 effects 列表）          │
│   EFFECT_ACTIONS  名词效果 → 动词动作序列（含数值）│
│   BUFF_RULES      状态消费/到期规则               │
│   TRIGGER_RULES   触发时机 → 效果条件             │
├─────────────────────────────────────────────────┤
│ 效果系统 v2（game/core/effect_sys/ 或 battle2 内）│   ← 本方案新建，替换旧三套
│   registry   注册表（名词→动作翻译缓存）          │
│   trigger    事件总线（19 时机统一分发）           │
│   lifecycle  buffs/shields/state 生命周期         │
│   verbs      动词执行器（对 battle2 薄封装）       │
├─────────────────────────────────────────────────┤
│ 引擎 battle2：落地接口（landing/actions/schedule）│
└─────────────────────────────────────────────────┘
```

### 2.3 目标清单
| # | 目标 | 消灭的旧问题 |
|---|---|---|
| G1 | 每动作全项目只写一次 | 三套并存 |
| G2 | 数值在效果声明里（动作参数），不藏名字表 | BUFF_MULT 病 |
| G3 | 触发走事件总线，新效果接线 = 数据声明 | 触发链硬编码 |
| G4 | 生命周期统一（到期/行动/受击/永久 查规则表） | buffs 值混乱 |
| G5 | 兼容迁移：旧技能 effect/mech 字段自动翻译 | 187 名词静默跳过 |

---

## Part 3：数据模型（字段级定稿）

### 3.1 名词效果（技能数据里写什么）
技能 dict 从 `effect/mech` 双轨统一为 `effects` 列表（迁移期保留旧字段自动转）：
```python
skill = {
    "name": "战吼", "kind": "增益", ...,
    # 新：统一效果列表（v2 数据形态）
    "effects": [
        {"type": "atk_all", "turns": 10},          # 名词效果 + 时长
        {"type": "state_add", "key": "zhan_yi", "amount": 3},  # 可直接写动词
    ],
    # 旧字段迁移兼容（N7.5 分诊后逐步删）：
    "effect": "atk_all", "mech": "zhan_yi", "mech_val": 3,
}
```
**名词效果 type 的取值空间**（全部走 EFFECT_ACTIONS 翻译，不直接执行）：
- 属性增益：atk_up/matk_up/def_up/spd_up/crit_up/...（数值在动作参数 mult）
- 控制：stun/freeze/silence/sleep/slow/spd_down
- 状态叠层：zhan_yi/lian_duan/rage/chi/arcane/shield（圣盾）/hunt_mark/soul_mark
- DOT：burn/poison/bleed/corros
- 元素印记：fire_mark/ice_mark/thunder_mark
- 护盾：shield/shield_self
- 净化：cleanse/cleanse_all
- 一次性：next_atk_up/stealth/buff_phys_next/arcane_echo/oath_blade_next/we_oath
- 减伤：reduce/reduce_all
- 特殊（职业机制 C 类 → 上层，不进引擎）：旋律/血祭/卸负/骷髅祭仪/元素跃迁等

### 3.2 动词动作（引擎执行什么）
动作 = 引擎唯一认识的执行单元，全部带显式参数：
```python
# 动作序列（EFFECT_ACTIONS 翻译产物；每个动作就是一个执行指令）
[
    {"action": "buff",   "key": "atk_up", "stat": "atk", "op": "mul", "mult": 1.30, "on": "caster"},
    {"action": "state",  "key": "zhan_yi", "amount": 3, "on": "caster"},
]
```
动作清单（引擎 verb 全集，对应 battle2/effects.py + landing + state 容器）：
| action | 参数 | 落点 | 说明 |
|---|---|---|---|
| `buff` | key/stat/op/mult\|value/on/turns | actor.buffs[key] = {expire, stat, op, mult} | 增益快照（N7.1 定稿） |
| `control` | tag/turns/on | actor.buffs[tag] = {expire, rule:on_act} | 控制（行动级消费） |
| `shield` | value/pct/on/turns/halve | actor.shields[key] = {value, expire_at, halve} | 护盾 |
| `cleanse` / `cleanse_all` | — | 查 CLEANSE_TAGS 清减益 | 净化 |
| `state_add` / `state_spend` | key/amount/on | actor.state[key] | 叠层/资源 |
| `heal` | expr/value/on | landing.heal_actor | 治疗落地 |
| `damage` | expr/value/on/kind | landing.deal_damage | 直接伤害 |
| `summon` | mon_id/on | sides 添加 actor | 召唤（引擎新 verb，N7.5） |
| `interrupt` | — | 打断读条 | 打断（N7.5） |
| `vuln` / `debuff_scale` | key/amount/on | state 声明表折算 | 易伤标记 |

### 3.3 触发时机（事件总线事件全集）
效果系统 v2 提供**统一触发总线**，所有效果声明"何时触发"：
```python
# TRIGGER_EVENTS（battle.py/actions/schedule 唯一插桩点，一次插齐）
EVENTS = [
    "battle_start",    # 开战（词条/套装/仪式）
    "turn_start",      # actor 回合开始
    "act_begin",       # 行动前（读条前）
    "act_cast",        # 行动施放瞬间（耗蓝/读条）
    "skill_hit",       # 技能命中后（伤害结算后）
    "attack_hit",      # 普攻命中后
    "crit",            # 暴击命中（skill_hit 子集）
    "on_taken",        # 受击（承伤后）
    "on_heal",         # 治疗生效
    "on_kill",         # 击杀敌人
    "on_death",        # 死亡
    "dot_tick",        # DOT 每跳
    "on_act_consume",  # 行动级消费点（控制跳过）
    "on_hit_consume",  # 出手消费点（一次性）
    "buff_expire",     # buff 到期钩子（后续扩展）
    "threshold",       # 状态阈值（战意满 10 → 狂暴）
    "phase",           # Boss 阶段转换
    "player_low",      # Boss 机制：玩家低血量
    "pv_broken",       # Boss 机制：破防
]
```
**引擎只在这 19 个点各插一次 `fire(event, ctx)` 调用**（battle.py 对应位置），
不再允许 battle.py 手写某个具体效果的 if 分支。

---

## Part 4：触发 → 翻译 → 执行管线

```python
# fire(event, ctx)：事件总线唯一入口（引擎 battle/actions/schedule 调）
def fire(battle, event, ctx):
    # 1. 遍历"该事件感兴趣"的已激活效果源：
    #    - 技能 effects（施放时一次性触发）
    #    - 装备特效（battle_start 注册，事件匹配触发）
    #    - 词条/套装（同装备特效）
    #    - actor 自身状态钩子（threshold 类）
    # 2. 每个源：名词 → EFFECT_ACTIONS 翻译成动词序列
    # 3. 动词序列逐条执行（apply_effects 已有骨架）
    # 4. 生命周期副作用（on_hit/on_act 消费）由 lifecycle 统一处理
```
### 4.1 效果源分类（谁声明效果）
| 源 | 效果从哪来 | 生命周期 | 触发方式 |
|---|---|---|---|
| 技能效果 | 技能 dict effects 列表 | 施放时即时 | 一次性（施放即执行） |
| 状态持久效果 | actor.buffs 条目（挂上后持续） | buff 存活期 | 面板折算/到期/行动消费 |
| 装备特效 | 装备词条 → weapon effect id | 装备期 | 事件匹配（battle_start 等） |
| 词条/套装 | affix/套装数据 | 装备期 | 事件匹配 |
| 被动 | 职业被动表 | 常驻 | 事件匹配（阈值/条件） |
| Boss 机制 | Boss 数据表 | 战斗期 | 阶段/条件触发 |

### 4.2 名词翻译缓存
```python
# registry：名词 → 动作序列 一次性翻译缓存（skill 数据加载时预热）
#   translate("atk_all") → [{"action": "buff", "key": "atk_up", "stat": "atk",
#                            "op": "mul", "mult": 1.30}]   （数值来自 EFFECT_ACTIONS 动作参数）
# 找不到名词 → 按"本身就是动词"直通（resolve_actions 已有逻辑）
# 找不到也非动词 → 记 missing 日志（N7.5 分诊驱动，不再静默跳过）
```

### 4.3 动作参数合并优先级（定稿）
`技能数据显式参数 > EFFECT_ACTIONS 动作参数 > 动词默认值`
（_merge_params 已实现：调用方显式参数优先于映射默认）

---

## Part 5：生命周期统一（效果系统 v2 的心脏）

### 5.1 状态容器字段（actor 全同构）
| 容器 | 条目形态 | 管理 |
|---|---|---|
| `actor.buffs[key]` | `{expire: float, stat: str\|None, op: "mul"\|"add", mult: float}`（增益）<br>`{expire, rule: "on_act"\|"on_hit", tag}`（控制/一次性）<br>`{expire, v: float, hits: int}`（value 型） | lifecycle.buff_tick |
| `actor.shields[key]` | `{value: int, expire_at: float\|None, halve: bool}` | lifecycle.shield_tick |
| `actor.state[key]` | `int` 层数（cap 声明） | 声明表 cap/stat_scale |

### 5.2 生命周期规则（BUFF_RULES 全表）
```python
BUFF_RULES = {
    # key: {"expire": "time"|"on_act"|"on_hit"|"forever"|"count",
    #       "value_type": bool, "wake_on_hit": bool, "skip_skill_only": bool, ...}
    "atk_up":       {"expire": "time"},          # 默认：绝对时刻到期
    "stun":         {"expire": "on_act"},         # 轮到行动 → 跳过 + 删
    "freeze":       {"expire": "on_act"},
    "silence":      {"expire": "on_act", "skip_skill_only": True},
    "sleep":        {"expire": "on_act", "wake_on_hit": True},
    "next_atk_up":  {"expire": "on_hit"},         # 出手命中 → 消费
    "stealth":      {"expire": "on_hit"},
    "echo_bless":   {"expire": "forever"},        # 整场
    "stance_guard": {"expire": "forever"},
    "reduce":       {"expire": "time", "value_type": True},  # 百分比 + reduce_left 计时
}
```
**缺省 = time（绝对到期）**；引擎不认识具体 key，只执行规则。

### 5.3 到期/消费扫（schedule 统一做）
```python
# schedule._settle_time_effects 每推进执行（全部 actor）：
#   1. buffs：expire <= now → 删（time 型）；on_act/on_hit/forever 型不在此删
#   2. shields：expire_at <= now → 删（None=永久不删）
#   3. state dot：interval 到点 → 跳伤
# advance 决策前：查决策 actor buffs 的 on_act 键 → 跳过行动 + 删 + 日志
# actions 出手命中后：查 caster on_hit 键 → 应用效果 + 删
```

---

## Part 6：与旧效果系统的映射（迁移路径）

### 6.1 迁移矩阵（旧 → v2）
| 旧注册表 | handler 数 | v2 去向 |
|---|---|---|
| MECH_EFFECTS（技能 mech） | 65 | 按效果归类：通用状态→verbs / 职业专属→上层模块（不迁） |
| SKILL_BUFF_EFFECTS（技能 effect） | 36 | → EFFECT_ACTIONS 名词映射（数值进动作参数） |
| MON_BUFF_EFFECTS / MON_CTRL_EFFECTS | 12 | 死表（memory：MON_BUFF+MON_CTRL 删）→ 不迁 |
| BOSS_MECHS | 9 | → Boss 机制表（phase/条件触发事件） |
| WEAPON_EFFECTS（79 key 族化） | 72 族 | → 事件总线注册（族执行器薄封装成动作序列） |
| HIT_EFFECTS / TAKEN_EFFECTS（affix） | 46+ | → 同上：命中/受击事件注册 |
| BUFF_MULT 26 键 | — | 数值摊进 EFFECT_ACTIONS 动作参数 → **表退役** |
| BUFF_STAT_KEYS 7 键 | — | 删（面板折算读 buff 条目快照） |
| 187 技能 effect 名词 | — | 分诊：A 战斗→EFFECT_ACTIONS / B 生活→排除 / C 词条→上层 |

### 6.2 迁移顺序（跟 N7 配合）
```
N7.1  数值动作参数化（BUFF_MULT → EFFECT_ACTIONS mult）
N7.2  生命周期收口（到期/盾 expire/控制 on_act）
N7.3  一次性 on_hit 消费
N7.4  DOT interval
N7.5  187 名词分诊 → EFFECT_ACTIONS 补全（产出 docs/EFFECT_TRIAGE_v181P4.md）
N8    事件总线（19 时机插桩 fire）——本效果系统 v2 主干
N9    三套旧注册表 → v2 迁移（battle_mech/weapon/affix 逐批族化）
N10   删旧（battle_mech/weapon_effects/affix 死代码删除 + 全量回归）
```

---

## Part 7：文件布局（效果系统 v2 落点）

方案 A（推荐）：效果系统 v2 放 **battle2 包内独立模块**（引擎原生能力）：
```
game/battle2/
├── effects.py       # 动词执行器（已有，扩展 heal/damage/summon/interrupt）
├── effect_registry.py  # 名词翻译缓存 + 分诊日志（新）
├── effect_triggers.py  # 事件总线 fire()（新）
└── lifecycle.py     # buffs/shields/state 到期/消费扫（新，schedule 调）
```
方案 B：放 game/core/effect_sys/（旧核心库旁，独立新目录）。
**决策建议 A**——效果系统是战斗引擎的一部分，紧邻 battle2 语义一致；
旧游戏数据仍从 game/data 读，不进引擎。

---

## Part 8：验收里程碑（每 Phase）
| Phase | 验收 |
|---|---|
| N7 系列 | 效果全通对拍（buff/盾/控制/DOT/一次性 数值一致）+ 全套测试绿 |
| N8 事件总线 | 19 时机插桩后，battle_start/on_skill/on_taken 效果与旧引擎对拍一致 |
| N9 迁移 | weapon 79 key + affix 46 与旧实现同输入同输出（行为快照测试） |
| N10 删除 | battle_mech/weapon_effects/affix 删后全量回归绿 + numeric 52/52 |

---

## Part 9：架构决策记录
| # | 决策 | 理由 |
|---|---|---|
| E1 | 效果 = 名词（数据）→ 动作（引擎）翻译；数值在动作参数 | 引擎零游戏知识；换配置=新游戏 |
| E2 | 旧 BUFF_MULT/名字表退役，数值摊进 EFFECT_ACTIONS | "固定×1.3 不对"——数值不藏名字表 |
| E3 | 统一事件总线 19 时机，引擎单点插桩 | 消灭触发链硬编码 |
| E4 | 生命周期查 BUFF_RULES（time/on_act/on_hit/forever） | buffs 值唯一形态 + 消费统一 |
| E5 | 职业专属机制（C 类）不进效果系统，上层事件总线接入 | 沿用 battle2 class_mech_decouple |
| E6 | MON_BUFF/MON_CTRL 死表不迁（删） | battle2 收口已定 |
| E7 | 三套旧注册表逐批族化迁移（快照对拍），最后整体删除 | 不陪葬旧 bug、不半迁 |
| E8 | 效果系统 v2 落 battle2 包内（方案 A） | 紧邻引擎语义一致 |
