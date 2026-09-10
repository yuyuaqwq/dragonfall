# 配置注入：引擎与游戏的边界

## 一句话

**方向只有一个：内容 → 引擎。** 引擎不 import 你的游戏；你把公式、面板、技能表
和规则表 `mount` 进引擎的 `config`。引擎需要什么就问 `config` 要，要不到就按
「零默认值」处理。

入口模块：`game/battle2/config.py`。

## 为什么必须这样

旧引擎的反向依赖问题被量化过：`game/battle2/` 里 **4 个文件（`actions`/`battle`/`stats`/`config`）
持有 15 条指向内容层的 import 边**（`docs/ENGINE_CONTENT_SPLIT_PLAN.md` §3.2）。
后果：

- 想把这个引擎做成可分发工具包 → 带不走，因为它 import 你的游戏表
- 想「换一套配置 = 新游戏」→ 做不到，因为公式和 `kind` 字面量写死在引擎里
- 引擎单测必须拉起整个游戏内容包

现在有一条机器可验的门禁盯着这件事：
`tests/test_engine_no_content.py`（AST 静态分析）断言 `game/battle2/**` 零
`game.content` / `game.data` / `game.engine` / `game.core` import 边，
且零 `importlib.import_module` / `__import__` 动态穿透。

> 门禁是**方向**的保证，不是「引擎绝对不用游戏东西」的保证。
> 引擎仍然读 `actor` 上的数据字段（那是运行期数据，不是 import）。

## 13 个 hook

`_HOOKS`（`config.py:33-64`）白名单，`mount(**hooks)` / `set_hook(name, value)` 写，
`get_hook(name)` 读。

| hook | 类型 | 引擎在哪里用 | 不装配的行为 |
|---|---|---|---|
| `formulas` | 对象 | `actions._skill_seg_damage`、`_settle_lifesteal`、`_do_heal`、`skill_pay_of` 等（`actions.py:116,355,492,500,602,630,739,769`） | 退回 `_NullFormulas`（全零效应，**静默**） |
| `formula_skeleton_fn` | `fn() -> dict` | `formulas.skill_power_mult / skill_buff_turns / skill_cond_mult / skill_mech_val / skill_lifesteal_pct / skill_learn_cost` | `{}` → 读 `["skill_growth"]` 时 **KeyError** |
| `skill_flat_fn` | `fn() -> dict` | `formulas.skill_flat_value` | `{}` → `float(None)` **TypeError** |
| `skill_up_fn` | `fn(info) -> dict` | `formulas._skill_up` | `{}` = 无成长配置 |
| `skill_level_of_fn` | `fn(player, name) -> int` | `formulas.skill_level_of` | 返回 `1`（未升级兜底） |
| `panel_fn` | `fn(class_name, level, equipment, tier, attributes, evolve_path, title_bonus, race) -> dict` | `stats._player_base_stats`（`stats.py:98-110`） | `{}`（空面板） |
| `skill_lookup` | 对象（需 `.skill_info(cls, key)` / `.skill_by_key(key)`） | `battle._index_one_actor`（`battle.py:134,137`） | 返回 `None` → 技能索引空 |
| `monster_skill_fn` | `fn(key) -> dict\|None` | `battle._index_one_actor`（`battle.py:142`） | `None` |
| `basic_skill_fn` | `fn(class_name) -> dict\|None` | `actions.resolve_basic_skill`（`actions.py:36`） | 回落 `basic_fallback` |
| `basic_fallback` | dict | 同上（`actions.py:42`） | 结构化兜底 `{"name": "", "kind": "", "exprs": ["atk*1.0"]}` |
| `kinds` | dict | `config.kind_of`（`config.py:254`）→ `actions._kind` | `""`（kind 比较全不成立） |
| `mech_cfg_fn` | `fn(name) -> dict` | `config.mech_cfg` → `support/battle_bars._battle_cfg` | `{}` |
| `bar_prefix_fn` | `fn() -> str` | `config.bar_prefix` → `support/battle_bars._state_prefix` | `""` |

**怎么记**：`formulas` 决定「数怎么算」，`f*_fn` 给它参数表，
`panel_fn` 决定「玩家面板怎么来」，`skill_lookup` / `monster_skill_fn` / `basic_skill_fn`
决定「技能 dict 从哪查」，`kinds` 决定「`kind` 字段的语义值是什么」，
`mech_cfg_fn` / `bar_prefix_fn` 是通用件（挂敌身条）的表读点。

> ⚠️ **未知名被静默忽略**：`set_hook`（`config.py:142`）里 `if name in _HOOKS`
> 没有 else。写错 hook 名不报错。开发期用 `strict=True`。

## 两张规则表：`set_config`

```python
config.set_config("effect_actions", EFFECT_ACTIONS)   # 名词 → 动词序列
config.set_config("effect_rules",   EFFECT_RULES)     # key → 行为规则
# 或者一次给一个模块（读它的 EFFECT_ACTIONS / EFFECT_RULES 属性）
config.load_game_rules(my_rules_module)               # config.py:89
```

读取端（**S2 公开 API**）：

| 函数 | 位置 | 语义 |
|---|---|---|
| `get_effect_actions()` | `config.py:119` | 默认 `{}` |
| `get_effect_rules()` | `config.py:124` | 默认 `{}` |
| `state_def(key)` | `config.py:129`（`state_effects.py:13` 的实体） | `get_effect_rules().get(key) or {}` |

## 三档行为：零装配 / 部分装配 / strict

这是接引擎时最容易踩的坑，实测结果：

| 情况 | 结果 |
|---|---|
| **什么 hook 都没装** | 一切「静默降级为 0」。`human_act` 返回 `[]`，双方 hp 不变，**不抛异常** |
| **装了 `formulas` 但没装 `formula_skeleton_fn` / `skill_flat_fn`** | 伤害链内部抛 `KeyError: 'skill_growth'` / `TypeError: float() ... NoneType` —— **硬崩**，而且栈不指向 hook 名 |
| **`config.strict = True`** | `get_hook` 对未装配 hook 抛 `EngineNotConfigured`（`config.py:165`），错误信息直接点名缺哪个 hook |

```python
config.strict = True    # 开发/测试环境建议打开（config.py:71）
```

原文说明（`config.py:66-70`）：`False`（默认）与历史行为一致——未装配给中性兜底不炸；
`True` 防测试假绿 / 线上静默失效。**生产接入点必须显式装配**，否则你会得到一场
「谁都不掉血的战斗」。

⚠️ **`strict=True` 的已知副作用**：它拦不住「装了 A 没装 B」这类**部分装配**
（只会在链深处第一次访问 B 时抛），也拦不住 `formulas` 已装但骨架表缺键的情况。
彻底的检查要么在自己启动时逐个 `get_hook(name) is not None` 断言，要么等引擎提供。

## 装配的三种写法

### ① 直接赋值（最省事，但绕过名单检查）

```python
from game.battle2 import config
config._HOOKS["formulas"] = my_formulas     # ⚠️ 私有字段，不推荐
```

### ② `mount` / `set_hook`（推荐）

```python
config.mount(
    formulas=my_formulas,
    kinds={"phys": "phys", "magi": "magi", "true": "true", "heal": "heal", "buff": "buff"},
    panel_fn=my_panel.player_final_stats,
    skill_lookup=my_skills,                 # 需有 .skill_info / .skill_by_key
    monster_skill_fn=my_monster_skills,
    basic_skill_fn=my_basic_skill,
    basic_fallback={"name": "普攻", "kind": "phys", "exprs": ["atk*1.0"]},
    formula_skeleton_fn=lambda: FORMULA_SKELETON,
    skill_flat_fn=lambda: {"SKILL_FLAT_BASE": 12, ...},
    skill_up_fn=my_skill_up,
    skill_level_of_fn=my_skill_level_of,
)
config.load_game_rules(my_rules_module)
```

### ③ 惰性装配（`register_hook_provider`）

```python
config.register_hook_provider(my_lazy_mount)   # config.py:101
```

引擎首次访问某个未装配 hook 时调用一次（`_lazy_bootstrap`，`config.py:171`，带防重入）。
本仓库的《奥兰迪亚》内容侧就是这么接的：`game/bootstrap.py:203` 注册
`_lazy_mount`，它 `from . import content` 后 `mount_engine_hooks()`。

⚠️ **副作用（实测）**：在同时存在 `game/` 包的项目里，`import game.battle2` 之后
**第一次读 hook** 就会把整份游戏内容 import 进来（`game.content` 与 `game.data`
进入 `sys.modules`）。这就是
[../getting-started/installation.md](../getting-started/installation.md) 里
「第三方项目请用独立拷贝、别依赖 `game` 包的 `__init__`」的原因。

还有 `register_defaults_loader(fn)`（`config.py:95`）——它只被 `load_game_defaults()`
（兼容 shim，`config.py:107`）调用，用于「52 个测试调用点」的旧 API 兼容。

## 引擎侧的通用件也会走 config

`support/battle_bars.py`（挂敌身条 + 蓄力三律）和 `formulas.py` 都不是「纯函数库」——
它们的表读点也走 config：

```python
def _battle_cfg(name):                  # support/battle_bars.py:42
    return _cfg.mech_cfg(name)

def _skeleton():                        # formulas.py:33
    fn = _cfg.get_hook("formula_skeleton_fn")
    return (fn() if fn is not None else None) or {}
```

所以第三方要用挂敌身条，必须装 `mech_cfg_fn` 与 `bar_prefix_fn`；
要用引擎自带的 `formulas` 模块，必须装 `formula_skeleton_fn` 与 `skill_flat_fn`。

## 相关

- 13 个 hook 的逐项签名与未装配行为 → [../reference/api.md](../reference/api.md)
- 两张规则表的字段级 schema → [../reference/effect-rules.md](../reference/effect-rules.md) ·
  [../reference/effect-actions.md](../reference/effect-actions.md)
- 边界的物理形态与迁移方案 → [../architecture/boundaries.md](../architecture/boundaries.md)
