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

## Part 5：实施路线（鱼鱼拍板：新建独立实现，替换旧引擎）

> 2026-09-07 鱼鱼决策：按本文档**新建 battle 实现**（不是原地改造旧 battle.py）。
> 旧引擎保留可跑，新引擎实现完切换 + 删旧。顺带把 P3（玩家状态容器收尾）
> P5（battle 拆类）做进新设计。

### Phase 0：文档定稿（本稿）→ 鱼鱼审 → 确认后动代码

### Phase N1：新引擎骨架（game/battle2/ 包，见 Part 7）
- 模型层 actors.py：Actor/Sides/ActCtx + 序列化（纯数据，无逻辑）
- 先跑通：构造 sides → act(ctx) 普攻 → 伤害落地 → hp 变化
- 验收：新引擎能完成"玩家普攻打怪扣血"最小闭环（对照旧引擎同场景数值）

### Phase N2：行动链（actions.py）
- human_act / actor_auto / _do_skill / _deal_hit / _damage_actor / AOE
- 技能管线：多段/暴击/元素/吸血/冷却（读旧 engine.py 数值函数，不重写公式）
- 验收：技能/治疗/增益三类 kind 全通 + 数值与旧引擎一致（同场景对拍）

### Phase N3：效果系统（effects.py + 数据迁移）
- EFFECT_HANDLERS 单表 + handler 从旧 MECH_EFFECTS/SKILL_BUFF_EFFECTS 迁入
  （统一 fn(battle, caster, target, params, logs)）
- 死表 MON_BUFF/MON_CTRL 不迁（删）
- 技能数据 mech/effect → effects 列表（脚本化迁移）
- 验收：dot/控制/buff/元素反应 效果全通

### Phase N4：CTB 调度 + 状态收尾（schedule.py + P3 内容）
- 事件队列/时刻推进/自动行动调度
- 玩家战斗状态全进 actor dict（P3：p_meta 收纳，无 Battle 残留字段）
- 验收：完整战斗能从头打到结束（胜利/失败/逃跑）

### Phase N5：序列化 + 命令层切换
- to_state/from_state sides-only（Part 4.2）
- 命令层 combat/instance/world/tower import 切到 battle2
- 旧 battle.py 冻结（不再改）
- 验收：野外/副本/PVP/世界Boss 全场景能玩

### Phase N6：全量回归 + 删旧
- 全部测试切新引擎跑绿（含 numeric 52 门禁）
- 删 game/battle.py + 旧 core 效果表（MECH_EFFECTS 等残留清干净）
- 验收：run_all_tests 全绿、numeric 52/52

## Part 6：必做收尾承诺（不可跳过）
- [ ] mech/effect 合并（N3 的 EFFECT_HANDLERS）完成前不许认为重构结束
- [ ] enemy 过渡属性删除（新引擎天然无，旧引擎删）
- [ ] 旧档迁移一次性脚本 + 删除持续兼容
- [ ] 旧 battle.py 最终删除（N6）

---

## Part 7：新引擎落地细节（game/battle2/ 包）

### 7.1 目录结构与模块职责
```
game/battle2/
├── __init__.py        # 导出 Battle（对外唯一入口：from game.battle2 import Battle）
├── actors.py          # Actor 模型/工厂 + Sides 容器 + ActCtx + actor 序列化
├── battle.py          # Battle 主类：构造、act/human_act/actor_auto、结果判定
├── actions.py         # 行动结算：技能/普攻/防御/道具/伤害落地/承伤链/AOE
├── effects.py         # EFFECT_HANDLERS 单表 + 注册 + 效果执行入口
├── stats.py           # 面板计算（薄封装 engine.py 数值函数，不重写公式）
├── schedule.py        # CTB 时间轴：事件队列/时刻推进/行动点/自动调度
├── serialize.py       # to_state/from_state（sides-only JSON 结构）
└── data_bridge.py     # 读旧数据层（技能表/词条/怪物模板）的适配层
```

### 7.2 依赖关系（新引擎只向下依赖，不反向）
```
battle2/ 依赖：
  → game/engine.py      （数值公式：calc_damage/player_final_stats/skill_info…只读）
  → game/data/          （技能/词条/怪物/套装数据，只读）
  → game/core/formation.py（站位/AOE 选目标——纯函数，可复用）
  → game/core/constants.py（数值常量）
不依赖：
  → game/battle.py      （旧引擎——绝不 import）
  → game/core/battle_mech.py 的 handler（迁到 effects.py 后断开）
```

### 7.3 关键模块接口签名

#### actors.py
```python
class ActCtx:
    caster: dict
    action: str                 # attack|skill|defend|flee|use_item|auto
    skill_name: str|None
    info: dict|None             # 技能配置
    target: dict|None           # 单目标
    target_side: str|None       # AOE 范围目标（side 名或 "all"/"front"）
    scope: str = "single"       # single|all|front|self

def make_actor(uid, name, side, kind, human_controlled=False, **stats) -> dict
    # 播种全部战斗状态键（buffs/debuffs/stacks/resources/shields/...）

def actor_buffs(actor) -> dict       # 替代旧 _actor_buffs
def actor_debuffs(actor) -> dict
def actor_alive(actor) -> bool
def actor_side_of(battle, actor) -> str|None
```

#### battle.py
```python
class Battle:
    def __init__(self, btype="monster", sides=None, title_bonus=None,
                 dmg_mult=1.0, pet=None, st=None):
        # sides: dict[str, list[actor]] —— 唯一入口，无 player/enemy 参数
        # 玩家只是 sides["player"] 里的一个 actor（human_controlled=True）

    # —— 行动入口 ——
    def human_act(self, action, skill_name, actor, target=None,
                  target_side=None) -> (logs, ended, who)
    def actor_auto(self, actor, forced_target=None) -> (logs, ended)
    def act(self, ctx: ActCtx) -> (logs, ended)      # 内部统一执行

    # —— 查询 ——
    def sides_of(self, side) -> list          # 某阵营 actor 组
    def hostile_of(self, side) -> list        # 敌对阵营 actors（AI 选目标用）
    def focus(self) -> dict|None              # human_controlled actor（命令层用）
    def alive_actors(self) -> list
```

#### stats.py（复用旧公式，不重写）
```python
def actor_stats(battle, actor) -> dict
    # 内部：actor 有 class_name → engine.player_final_stats(...)
    #       纯怪（无 class_name）→ 读 actor 字段 + buffs 修正（对齐旧 _enemy_stats）
def actor_max_hp(actor) / actor_spd(actor) / ...  # 便捷访问
```

#### effects.py
```python
EFFECT_HANDLERS: dict[str, EffectHandler] = {}
EffectHandler = Callable[[Battle, dict, dict|None, dict, list], None]
# 签名：fn(battle, caster, target, params, logs)
#   params = {"stacks": n, "turns": n, "pct": f, "value": n, ...}

def register_effect(key): ...           # 装饰器
def apply_effects(battle, caster, target, effects, logs):
    # effects = [{"type": "bleed", "stacks": 2}, ...] 技能数据里的列表
    # 按 type 查 EFFECT_HANDLERS 执行

# 迁移自旧表（N3 做）：
#   MECH_EFFECTS 的 A 类（burn/mark/poison/控制/印记）→ target 效果
#   MECH_EFFECTS 的 B 类（rage/资源）→ caster 效果
#   SKILL_BUFF_EFFECTS 全部 → caster/target 按语义
```

#### serialize.py
```python
def to_state(battle) -> dict      # Part 4.2 结构（sides-only）
def from_state(state) -> Battle   # 重建 sides+actors
def migrate_old_state(state) -> dict  # 旧档（enemy/enemies 键）一次性迁移
```

### 7.4 数值一致性策略（关键风险）
- **公式不重写**：所有伤害/面板/技能数值函数从旧 engine.py 复用（import + 薄封装）
- **对拍测试**：每个 Phase 用"同场景双引擎跑"对比 hp/logs（旧 vs 新），数值差=0
- **行为快照**：P3/P5 需要的白盒黑盒化——新引擎每 Phase 产出快照对比
- 命令层逻辑（掉落/经验/胜负结算）在旧 battle.py 外部（combat.py），切引擎时这些不动

### 7.5 切换与删除
- import 切换：命令层 `from game import battle as BT` → `from game.battle2 import Battle as BT`
- 切换点：combat/instance/world/tower/economy 用 BT.Battle 的地方
- 切换前旧引擎冻结；切换后全量回归；绿了才删 game/battle.py
- 删除清单：game/battle.py、core/battle_mech.py 死表、_we_executors 旧 handler 链

### 7.6 验收里程碑（每 Phase 明确）
| Phase | 验收 |
|---|---|
| N1 | 普攻闭环：同场景新旧引擎伤害一致 |
| N2 | 技能/治疗/增益/AOE 全通 + 数值一致 |
| N3 | 效果（dot/控制/buff/元素）全通 + 数值一致 |
| N4 | 完整战斗可打完（含 CTB 调度/自动行动/胜负） |
| N5 | 命令层切新引擎，野外/副本/PVP 能玩 |
| N6 | run_all_tests 全绿 + numeric 52/52 + 旧引擎删除 |

## Part 8：风险与对策
| 风险 | 对策 |
|---|---|
| 数值不一致（新引擎伤害/效果偏差） | 公式全复用 engine.py + 每 Phase 对拍测试 |
| 技能数据迁移漏（mech/effect 145 处） | 脚本化迁移 + 数据完整性断言（全技能 effects 可解析） |
| 命令层依赖旧引擎内部方法 | 切换前盘点命令层调用面（b.xxx 方法清单），battle2 提供同语义 API |
| 大工程周期长 | 每 Phase 独立可用+可验证，不阻塞游戏运行（旧引擎保留） |
