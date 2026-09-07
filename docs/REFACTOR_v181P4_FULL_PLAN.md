# 战斗引擎重构完整方案（v181.P4 详细设计稿）

> 鱼鱼 2026-09-07 要求：详细方案文档，仔细到每个函数每个字段如何定义、DB 结构如何存储。
> 本文档 = 可实施蓝图。写完给你审，确认后按它改代码。

---

## Part 1：目标架构总览

### 1.1 引擎世界观
战斗 = **actor 组（sides）** 上的行动序列。无"玩家/怪物"身份逻辑。

```
Battle
├── sides: dict[str, list[actor]]     # 阵营 → actor 组（唯一容器）
├── actor: dict                        # 全同构战斗单位
├── act_ctx: {caster, target, scope}   # 当前行动上下文（每 action 新建）
├── events: 时刻事件队列               # CTB 调度
└── result: 战斗结果
```

### 1.2 actor dict 字段定义（全同构，无身份）
```python
actor = {
    # —— 身份/数据标签（不参与逻辑分支）——
    "uid": str,              # 唯一 id（e_0 / p_qqid / summon_x）
    "name": str,
    "side": str,             # 阵营名（"player"/"enemy"/任意自定义）
    "kind": str,             # 数据标签：player|monster|summon|pet
    "human_controlled": bool,# True=真人操作，False=按 auto_act 配置行动

    # —— 基础属性（战斗面板，由 _actor_stats_of 计算/聚合）——
    "hp": int, "max_hp": int, "mp": int, "max_mp": int,
    "atk": int, "matk": int, "def": int, "mdef": int, "spd": int,
    "crit": float, "dodge": float, ...（面板字段）

    # —— 战斗可变状态（玩家/怪同构）——
    "buffs": dict,       # {buff_key: 刻数/值} 如 {"atk_up": 3, "shield": {...}}
    "debuffs": dict,     # {dot_key: {n, mult, threshold, atk, ...}} 持续减益
    "stacks": dict,      # 职业叠层（气/怒/战意）
    "resources": dict,   # 核心资源（法力/能量/元素充能）
    "shields": dict,     # 护盾 {key: {value, halve, expire...}}
    "charging": dict|None, # 蓄力中 {skill, left, ...}
    "defending": bool,
    "ct": float,         # CTB 行动时钟
    "equipment": dict,   # 装备（玩家有，怪空）
    "class_name": str,   # 职业（玩家/扮职业怪）
    "level": int,
    "auto_act": dict|None,  # 自动行为配置（怪/随从）
    "skills": list,      # 可用技能 key
    "cooldown": dict,    # 技能冷却
}

# sides 组织
sides = {
    "player": [玩家actor, 队友actor...],   # side 名由数据定，引擎不预设
    "enemy": [怪actor...],
    # 任意更多阵营（怪vs怪/混战）
}
```

### 1.3 行动上下文（act_ctx）
每次行动建一个上下文对象，贯穿结算，**消灭隐式全局目标**：
```python
@dataclass
class ActCtx:
    caster: dict          # 施法者 actor（谁在行动）
    action: str           # action 类型：attack|skill|defend|flee|use_item|auto
    skill_name: str|None  # 技能名
    info: dict|None       # 技能/动作配置
    target: dict|None     # 单目标 actor（伤害/debuff 对象）
    target_side: str|None # 范围目标（AOE 打哪个 side）
    scope: str            # "single"|"all"|"front"|"side:<name>"|"self"
```
引擎结算方法从 ctx 读 target，不再从 self.enemy/self._focus 猜。
命令层/AI 先决定 ctx（选目标），再交给引擎执行。

---

## Part 2：行动入口函数（签名定稿）

### 2.1 统一行动入口
```python
class Battle:
    # —— 唯一行动入口（人类/AI/随从都走这里）——
    def act(self, ctx: ActCtx) -> tuple[list[str], bool]:
        """执行一次行动。ctx 含 caster/action/target。返回 (logs, ended)。"""

    # —— 人类驱动包装（命令层用；ctx.caster = 玩家 actor）——
    def human_act(self, action: str, skill_name: str|None,
                  actor: dict, target=None, target_side=None) -> tuple[list, bool, dict|None]:
        """命令层唯一入口。构造 ctx 后调 self.act()。
        target_side: 技能配 aoe 时传 side 名（"all"=敌对全阵营）
        返回 (logs, ended, next_who)。"""

    # —— actor 自动行动（怪/随从按 auto_act 配置；行为树外部实现）——
    def actor_auto(self, actor: dict, ctx_target=None) -> tuple[list, bool]:
        """读 actor.auto_act / actor.skills 配置决定动作，构造 ctx 调 self.act()。
        替代原 _actor_auto_turn（原 _enemy_turn）。"""
```

### 2.2 内部结算链（全部显式 ctx/caster/target，不摸 self.enemy）
```python
    def _do_skill(self, ctx: ActCtx) -> list:      # 技能（原 _actor_skill 泛化）
    def _do_attack(self, ctx: ActCtx) -> list:     # 普攻 = basic_skill
    def _do_defend(self, ctx: ActCtx) -> list
    def _do_flee(self, ctx: ActCtx) -> list
    def _do_use_item(self, ctx: ActCtx) -> list

    # 技能内按 info.kind 分派（无身份，只看 kind）
    #   kind=heal   → _skill_heal(ctx, target_ally)
    #   kind=buff   → _skill_buff(ctx)          # 增益写 ctx.caster
    #   kind=attack → _skill_damage(ctx)        # 伤害打 ctx.target / ctx 范围

    def _skill_damage(self, ctx: ActCtx):        # 原伤害管线（多段/暴击/元素）
    def _deal_hit(self, ctx: ActCtx, dmg):       # 命中落地（单目标）
    def _deal_aoe(self, ctx: ActCtx, dmg, scope):# AOE 逐目标（已显式 target）
    def _damage_actor(self, target, dmg, source):# 承伤链（免伤/格挡/护盾/反伤）
```

---

## Part 3：效果系统（mech/effect 合并 + handler 显式化）

### 3.1 合并后单一注册表
```python
# game/core/effects.py（新文件，替代 battle_mech 的 MECH_EFFECTS/SKILL_BUFF_EFFECTS
# 及死表 MON_BUFF_EFFECTS/MON_CTRL_EFFECTS）
EFFECT_HANDLERS: dict[str, EffectHandler] = {}

@dataclass
class EffectParams:      # 技能数据里 effect 的参数字段（原 mech_val/层数/时长）
    stacks: int = 0      # 层数（毒/灼烧/标记）
    turns: int = 0       # 持续刻数（buff/控制）
    pct: float = 0.0     # 百分比（dot 强度/降防幅度）
    value: int = 0       # 数值（护盾量/治疗量）
    ...  # 按 effect 类型扩展

EffectHandler = Callable[[Battle, dict, dict|None, dict, list], None]
# 签名：fn(battle, caster, target, params, logs) -> None
#   caster = 施法者（自我增益作用对象）
#   target = 作用目标（对敌效果；治疗目标；None=无对象）
#   params = effect 参数字典
```

### 3.2 技能数据 effect 字段（统一，mech 并入）
技能 dict 增加标准字段：
```python
skill = {
    ...,
    "kind": "攻击|增益|治疗|召唤",   # 已有
    "effects": [                       # 统一效果列表（替代 mech/effect 双轨）
        {"type": "bleed", "stacks": 2, "turns": 0},   # 攻击命中附带
        {"type": "def_up", "turns": 3, "pct": 0.45},  # buff
        {"type": "heal", "value": "0.15*max_hp"},     # 治疗
    ],
}
# 兼容层（迁移期）：读 effect/mech 字段自动转 effects，迁移完删
```

### 3.3 handler 作用对象归类（写进手册的最终版）
| effect type 类 | 作用对象 | handler 参数 |
|---|---|---|
| 对敌附加（bleed/burn/poison/mark/sleep/stun/降攻/降防/印记） | ctx.target | target |
| 自我增益/自疗/自盾 | ctx.caster | caster |
| 治疗 | ctx.target（=被奶的 ally） | target |
| 团队 buff（副本广播） | side 内全体 | 遍历 side |
| AOE | 逐目标循环调 | 每目标各传 |

---

## Part 4：DB 存储设计

### 4.1 现状
- `battle_state` 表：`state TEXT` 存整个 battle.to_state() JSON（含 sides/actors）
- 玩家持久数据在 `players` 表（hp/mp/等级/装备/技能），战斗状态不落 DB

### 4.2 战斗状态存储（to_state/from_state 结构定稿）
```python
# to_state() 输出（JSON 存 battle_state.state）
state = {
    "type": "monster|worldboss|pvp|instance",
    "now": float,               # CTB 绝对时刻
    "p_acts": int,
    "sides": {                  # 唯一容器（替代旧 enemies/allies/enemy 键）
        "player": [actor_serialized...],
        "enemy":  [actor_serialized...],
    },
    "focus_uid": str,           # 命令层焦点 actor 的 uid
    "focus_state": {...},       # 玩家战斗状态（buffs/stacks/resources/cooldown）
    "tick_effects": [...],      # 事件队列序列化
    "killed": [...],            # 击杀记录（结算用）
    "battle_flags": {...},      # 战斗级一次性标记（death_pact_used 等）
    "title_bonus": {...},
    "pet": {...},
}
# from_state(state) 反序列化：重建 sides + actors（含全部战斗状态字段）

# 旧存档兼容：v181 前的 state（enemy/enemies 键）→ 迁移函数一次性转 sides（不做持续兼容）
```

### 4.3 actor 序列化字段白名单
actor dict 含 owner 循环引用（召唤物）→ 序列化转 uid 字符串，恢复后按 uid 重连
（_strip_actor_refs/_summons_serializable 已有，保留）。

---

## Part 5：分阶段实施计划

### Phase 0：文档定稿（本稿）→ 鱼鱼审 → 确认
### Phase A：handler 显式 caster/target
  A1: battle.py 结算链改造（act_ctx 引入，_do_skill/_deal_hit 显式 target）
  A2: MECH_EFFECTS/SKILL_BUFF_EFFECTS handler 加 caster/target（按手册归类）
  A3: 删死表 MON_BUFF_EFFECTS/MON_CTRL_EFFECTS + 测试直调点改
### Phase B：效果表合一
  B1: 建 game/core/effects.py EFFECT_HANDLERS
  B2: 两表 handler 迁入（统一签名 fn(battle, caster, target, params, logs)）
  B3: 技能数据 mech/effect → effects 列表迁移（脚本化 145 处）
### Phase C：容器收口
  C1: 删 self.enemies/self.allies 实体容器（sides 派生）
  C2: 删 battle.enemy 过渡属性（命令层/测试改 sides 读）
  C3: to_state/from_state 换 sides-only（Part 4.2）
### Phase D：验证
  D1: 单怪/多怪/副本/PVP/世界Boss/随从 场景测试
  D2: 全量回归 + numeric 门禁

## Part 6：必做收尾承诺（不可跳过）
- [ ] mech/effect 合并（Phase B）完成前不许认为重构结束
- [ ] enemy 过渡属性删除（Phase C2）
- [ ] 旧档迁移一次性脚本 + 删除持续兼容
