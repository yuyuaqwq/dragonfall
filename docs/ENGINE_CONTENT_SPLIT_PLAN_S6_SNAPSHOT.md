# S6' 内容层重组 · 实施前快照（2026-09-11）

> 上游方案：`docs/ENGINE_CONTENT_SPLIT_PLAN.md`（含 §7.5 实施期修正）
> 本档是 **S6' 的重新盘点**（方案 §7.5 缺陷二：「S3/S5 已完成，S6 的起点与原文描述已不同，
> 实施前需重新盘点」）。**只读侦察**，未 `git mv` 任何目录、未 `git add/commit`。
>
> | 项 | 值 |
> |---|---|
> | 仓库 | `C:\Users\yuyu\qqbot\data\plugins\dragonfall` |
> | 基线 HEAD | `474eea3`（feat(editor): 配置编辑器 MVP（技能域）） |
> | 回归口径 | `scripts/run_all_tests.py` → **245/245 绿 / 104s**（S1 时 241 → 本步新增 `test_apply_game_content.py` 后 **245**） |
> | 回归命令 | `"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe" scripts/run_all_tests.py` |
> | 侦察工具 | 纯 Python（`os.walk` + `ast` + `re`），不依赖 grep；脚本见附录 |
> | 已知并行工作 | `docs/engine-wiki/`（另一 agent，untracked） |

---

## 1. 现状目录清单与三层分类（S3/S5 之后的新状态）

`game/` 顶层（按代码行数降序；数据由 `ast`/`os.walk` 实测，非估算）：

| 顶层模块/包 | py 文件 | 行数 | 三层判定 | 依据（本档 §3/§4） |
|---|---:|---:|---|---|
| `game/data/` | 86 | 74 526 | **内容** | 纯静态表；出边仅 3 条指向 `core.{class_sets,index,maps}`（`_assembly` 派生表装配） |
| `game/commands/` | 24 | 27 143 | **内容** | AstrBot 命令层；目录内有 1 个 3 节点环（§3.2） |
| `game/core/` | 55 | 13 274 | **内容**（灰色已消解） | S3 已把 4 个通用件迁出 → `battle2/support/`；剩余 55 个模块全部读游戏表 |
| `game/services/` | 22 | 10 959 | **内容** | 机制动作注册 + 装配层；出边 7 条指向 `battle2`（合法方向：内容 → 引擎） |
| `game/battle2/` | 19 | 5 202 | **引擎**（已纯化） | 0 条出边（`game.battle2` 出边目标 = 0，实测 §3.4）；`support/` 5 模块 |
| `game/store/` | 12 | 3 559 | **内容** | 目录内零环；出边 0 条 game.*（仅 4 个模块 `from .. import content`，见 §6.2） |
| `game/content_rules/` | 5 | 976 | **内容（S5 新落点）** | `skills/panel/gameplay/apply`；引用者仅 3 |
| `game/drop_engine.py` | 1 | 590 | **内容** | 掉落引擎，读 `data.drop_pools` |
| `game/reward.py` | 1 | 215 | **内容** | 奖励结算 |
| `game/bootstrap.py` | 1 | 207 | **内容（内容侧装配器）** | S1 落点；方案 §6.3 目标形态 `content/bootstrap.py` |
| `game/engine.py` | 1 | 110 | **灰色 → 已消解** | S5 后为**纯 shim**（re-export，零实现） |
| `game/content.py` | 1 | 19 | **内容（聚合层）** | 201 处引用 / 136 文件 → 迁移最高危单点（§6.1） |
| `game/db.py` | 1 | 8 | **内容（聚合层）** | `from .store import *` 薄转发 |

**v.s. 原方案 §2 的变化**（必须按新状态行事，不得照旧清单搬）：

| 原方案描述 | 现状（S3/S5 后） |
|---|---|
| `game/battle2/` 13 文件 / 3 572 行 | **19 文件 / 5 202 行**（+`formulas.py` +`support/` ×5） |
| `core/formula_expr·formation·skill_kinds·battle_bars` 需迁引擎 | **已迁** → `game/battle2/support/`；`game/core/` 同名文件已是 shim |
| `game/engine.py` 1 212 行需一拆为二 | **已拆** → `battle2/formulas.py` + `content_rules/{skills,panel,gameplay}.py`；`engine.py` = 110 行 shim |
| `content/core/` 收灰色模块 | 灰色已消解：`core/` 剩余全部为内容（读表）；引擎不需要它们 |
| S6 = `data → core → store → services → commands` | 该顺序**建议调整**，见 §5（store 前置） |

---

## 2. 内容层真实边界

### 2.1 应进 `game/content/`（内容）—— 五包 + 三个顶层单文件

`data/` · `core/` · `store/` · `services/` · `commands/` · `content_rules/`（→`rules/`）
+ `bootstrap.py` + `drop_engine.py` + `reward.py`

### 2.2 引擎（不进 content）

`game/battle2/`（19 模块）+ `game/battle2/support/`（5 模块：`formula_expr` / `formation` /
`skill_kinds` / `battle_bars`）。
实测**出边 0 条** → 引擎单向依赖已达成（门禁 `tests/test_engine_no_content.py` 在跑）。

### 2.3 灰色（本轮判定 + 处置建议）

| 模块 | 现状 | 处置 |
|---|---|---|
| `game/content.py`（19 行聚合） | 聚合 `data *` + `core *` + 触发 `bootstrap.mount_engine_hooks()` | **进 content，且必须是 S6' 第 1 步**：内容 → `game/content/__init__.py`（§6.1） |
| `game/db.py`（8 行） | `from .store import *` 转发 | 随 store 一起（store 迁完即改指向） |
| `game/engine.py`（110 行 shim） | re-export 全部旧符号，93 处引用 / 26 文件 | **不迁**；S9 收口删 |
| `game/bootstrap.py`（207 行） | 内容侧引擎装配器（`mount_engine_hooks` / `load_engine_config`） | 进 content（`game/content/bootstrap.py`），引用者 1（`game/__init__.py`） |
| `game/battle2/{__init__,actions,...}` | 引擎 | 引擎本身也有 8 节点环（§3.3），**本阶段一行不碰** |

---

## 3. 内部循环导入环（前置风险 · 逐条给路径）

方法：`ast` 抽取**模块级（eager）** import 边 → Tarjan 强连通分量；函数体内 import 单列
为「惰性断点」（它们才是让这些环不炸的原因）。

### 3.1 ★ 环 R1（唯一跨目录真实环，5 节点，全 eager）

```
game.data  →  game.data._assembly  →  game.core.class_sets  →  game.core.index  →  game.data
                                   ↘  game.core.maps  →  game.data
```

逐边证据（**全部模块级，非惰性**）：

| 边 | 位置 | 形态 |
|---|---|---|
| `game.data → game.data._assembly` | `game/data/__init__.py:242` | EAGER `from . import _assembly` |
| `game.data._assembly → game.core.index` | `game/data/_assembly.py:9` | EAGER `from ..core.index import build_index, …` |
| `game.data._assembly → game.core.maps` | `game/data/_assembly.py:90` | EAGER |
| `game.data._assembly → game.core.class_sets` | `game/data/_assembly.py:91` | EAGER |
| `game.core.index → game.data` | `game/core/index.py:5` | EAGER `from ..data import _INDEXES` |
| `game.core.maps → game.data` | `game/core/maps.py:3` | EAGER `from ..data import MAPS, SUBAREAS, …` |
| `game.core.class_sets → game.data` | `game/core/class_sets.py:20` | EAGER |
| `game.core.class_sets → game.core.index` | `game/core/class_sets.py:22` | EAGER |

**当前靠 import 顺序侥幸闭合**：`game.content` 先 `from .data import *` → `data/__init__`
从第 1 行起顺跑完整条链（含 `_assembly`）→ 环在 `content.py` 内部安全闭合。
`game/bootstrap.py` 的 docstring 已记录了这条（「⚠️ 装载顺序：先引内容包，再取 battle_rules」）。
→ **迁移时不得改变 `game.data.__init__` 与 `game.core.*` 的相对装载顺序**；
子包重排后先跑 `python -c "import game.content"` 冷启动冒烟（比全量快 ~20×）。

### 3.2 环 R2（commands 目录内，3 节点）

```
game.commands  →  game.commands.instance  →  game.commands.instance_router  →  game.commands
```

`game/commands/__init__.py → instance`（EAGER）、`instance.py → instance_router`（EAGER）、
`instance_router.py → game.commands`（EAGER）。
→ 该目录**整体搬迁**时三条边的相对层级同时 +1，环结构不变；单独搬其中任一文件会破环。

### 3.3 环 R3（引擎内部，8 节点 —— 本阶段不碰，仅登记）

```
game.battle2 ↔ actions ↔ battle ↔ effects ↔ schedule ↔ serialize ↔ state_effects ↔ stats
```

### 3.4 惰性断点清单（迁移必须原样保留的延迟导入点）

实测：函数体内 `game.*` import 共 **840 条 / 89 文件**（其中 225 条是 `from .. import <顶层包>` 形态）。

| 分组 | 条数 | 文件数 |
|---|---:|---:|
| `game/commands` | 268 | 17 |
| `game/services` | 259 | 17 |
| `game/core` | 183 | 32 |
| `game/battle2` | 72 | 10 |
| `game/store` | 15 | 5 |
| `game/bootstrap` | 13 | 1 |
| `game/content_rules` | 8 | 2 |
| `game/data` | 7 | 2 |
| `game/drop_engine` / `game/reward` | 7 / 7 | 1 / 1 |
| `game/engine` | 1 | 1 |

**与 R1/store 链直接相关的断点**（改目录时最容易踩）：

| 位置 | 目标 | 作用 |
|---|---|---|
| `game/core/maps.py:19` | `game.data`（`SUBAREA_LINKS_INDEX`） | 防 `_assembly` 装配期环（函数 docstring 明写） |
| `game/core/smith_stock.py:281` / `:371` | `game`（=`from .. import db`） | 断 `core → db → store → content` 链（注释「惰性导入（防 core 层循环导入）」） |
| `game/core/smith_stock.py:31` | `game.data` | 货架表读取 |
| `game/store/players.py:226` / `:253` | `game.engine` | store → 内容 |
| `game/store/players.py:231` / `:93` | `game.core.stat_bonus` / `game.core.constants` | 同上 |
| `game/store/battle_state.py:119` | `game.core.worlds` | 同上 |
| `game/core/__init__.py:62` 附近 | 头部注释记录 `smith_stock → db → store.connection → content` 环 | **注释即契约**，勿删 |

### 3.5 目录内环结论（迁移粒度）

| 目录 | 目录内环 | 结论 |
|---|---|---|
| `game/data` | ✅ 无 | 可整目录搬 |
| `game/core` | ✅ 无 | 可整目录搬（但与 data 组成 R1） |
| `game/store` | ✅ 无 | 可整目录搬（叶子） |
| `game/services` | ✅ 无 | 可整目录搬 |
| `game/content_rules` | ✅ 无 | 可整目录搬 |
| `game/commands` | ⚠ R2（3 节点） | **必须整目录搬**（拆开则破环） |
| `game/battle2` | ⚠ R3（8 节点） | 引擎，不碰 |

---

## 4. 外部引用者数表（决定 shim 范围）

计数口径：**import 目标解析为模块名**（含相对导入按包展开、含惰性 import；包式
`data.plugins.dragonfall.game.X` 同一模块树另计）。单位 = **不同模块数**。

| 目标目录 | 内部模块 | game/ 内活引用者 | main | tests/活 | tests/归档 | scripts/活 | scripts/归档 | 其他 | **合计** | 引用点行数 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `game.data` | 86 | **53** | 0 | 22 | 14 | 27 | 7 | 87 | 210 | 420 |
| `game.core` | 55 | **28** | 1 | 19 | 32 | 25 | 1 | 44 | 150 | 365 |
| `game.store` | 12 | **8** | 1 | 16 | 20 | 2 | 1 | 0 | 48 | 58 |
| `game.services` | 22 | **10** | 0 | 43 | 2 | 0 | 0 | 0 | 55 | 78 |
| `game.commands` | 24 | **0** | 1 | 24 | 4 | 5 | 0 | 3 | 37 | 120 |
| `game.content_rules` | 5 | **2** | 0 | 1 | 0 | 0 | 0 | 0 | 3 | 1 |
| `game.battle2` | 19 | **21** | 0 | 71 | 5 | 0 | 0 | 0 | 97 | 377 |

> 「其他」列 = 根目录脚本 / `editor/` / `audit/` / `schema/` / `gen_drop_pools` 等
> （`game.data` 的 87 主要来自 `schema/` 与根目录生成脚本）。

**game/ 内部活引用者明细**（shim 必须遮罩的相对导入点）：

- `game.data`（53）：`core/*` **34** 个、`commands/*` 8、`services/*` 5、`content_rules/{gameplay,panel}` 2、
  `bootstrap`、`content`、`engine`、`drop_engine`
- `game.core`（28）：`commands/*` 10、`services/*` 10、`store/{battle_state,players}` 2、
  `data._assembly`、`content`、`content_rules.panel`、`bootstrap`、`engine`、`reward`
- `game.store`（8）：`commands/{_identity,economy,social}`、`content_rules.gameplay`、`core.worlds`、
  `db`、`reward`、`services.guild`
- `game.services`（10）：`commands/*` 9、`content_rules.apply`（本次 S7 新增）
- `game.commands`（0）：仅 `main.py` + scripts/tests
- `game.content_rules`（2）：`bootstrap`、`engine`(shim)
- `game.battle2`（21）：`services/*` 5、`commands/*` 8、`core/{battle_bars,formation,formula_expr,skill_kinds}`（4 个 **shim**）、
  `content_rules/{panel,skills}` 2、`bootstrap`、`engine`(shim)

**shim 结论**：`game/store`（8）与 `game/content_rules`（2）的 game/ 内引用面最小 →
**最适合作 shim 方案的样板**；`game.data`（53）/`game.core`（28）的 shim 面大，
且其引用者大量使用 `from ..data import <符号>` 形态（shim 需 `import *` + `sys.modules` 子模块别名）。

---

## 5. S6' 子步序列（自底向上 · 每子步可单独 245 绿 + 单独 revert）

> ⚠️ **本档不改任何目录**（任务铁律 2）。以下为待父 agent 审批后执行的序列。
> 每一步都是「`git mv` 一批 + 新路径 shim + 旧路径 shim」的原子提交。

### S6'-1【最高结构风险，但引用面最小】`game/content.py` → `game/content/__init__.py` + `store` 迁入

| 项 | 内容 |
|---|---|
| 动作 | ① 新建 `game/content/__init__.py` = `game/content.py` 逐字 + `from . import bootstrap` 改 `from .. import bootstrap`；② 删 `game/content.py`；③ `git mv game/store game/content/store`；④ `game/content/store/*` 内 `from .. import content as C`（4 处）改 `from ... import content as C`；⑤ 新 `game/store/__init__.py` = shim（`from game.content.store import *` + `sys.modules` 别名 12 个子模块）；⑥ `game/db.py` 的 `from .store import *` 保留（走 shim）或改直连 |
| 为何第一步 | `game/content/` 包名**会遮蔽** `game/content.py`（§6.1 实测）→ 必须一次性完成；而 store 是唯一「目录内零环 + game/ 内引用者仅 8」的叶子，把它绑在这一步使「新包 + 首个子包」一次成型 |
| 验证 | `python -c "import game.content"` 冷启动 → 全量 245 绿 |
| 回滚 | `git revert`（mv 可逆） |
| 风险 | `game/content/store/connection.py:9` 等 4 处 `from .. import content` 的层级语义变化（§6.2） |

### S6'-2 `content_rules/` → `game/content/rules/` + `bootstrap.py` → `game/content/bootstrap.py`

| 项 | 内容 |
|---|---|
| 动作 | `git mv game/content_rules game/content/rules`；`git mv game/bootstrap.py game/content/bootstrap.py`（内部 `from .battle2` → `from ..battle2`、`from .data` → `from ..data` 等 13 条惰性导入层级 +1）；`game/__init__.py` 改 `from .content import bootstrap`；`game/engine.py` shim 改 `from .content.rules import …`；旧路径 `game/content_rules/__init__.py` 留 shim |
| 验证 | 245 绿 |
| 风险 | `game/content.py` 末尾 `from . import bootstrap as _engine_bootstrap` 与 `game/__init__.py` 的 `install()` 双侧登记（R2：两套模块树各自 config 实例）——两只树都要能闭合 |

### S6'-3 `core/` → `game/content/core/`

| 项 | 内容 |
|---|---|
| 动作 | `git mv game/core game/content/core`；模块内相对导入整体 +1（`from ..data` → `from ...data`；`from ..battle2.support` → `from ...battle2.support`）；旧路径 shim |
| 联动（高危） | `game/data/_assembly.py` 的 3 条 `from ..core.*`（`:9/:90/:91`）→ `from ..content.core.*`，**与 S6'-4 必须协同**（先 core 后 data 时，`data` 仍在旧位，`..core` = `game.core` shim → 可走 shim，故可单独 revert） |
| 必须保留 | `core/maps.py:19`、`core/smith_stock.py:281/371`、`core/__init__.py:59-63` 注释所记的延迟导入点原样（§3.4） |
| 验证 | 冷启动 `import game.content` + 245 绿 |

### S6'-4 `data/` → `game/content/data/`

| 项 | 内容 |
|---|---|
| 动作 | `git mv game/data game/content/data`；86 个文件内相对导入 +1；`game/content/__init__.py` 的 `from .data import *` **文本不变**（相对包解析自动指向新位置）；旧路径 shim（需 `import *` + 子模块 `sys.modules` 别名，引用者 53） |
| 验证 | 245 绿 + `tests/_battle_settlement_snapshot.baseline.json` 数值对拍 |
| 风险 | 最大体量（74.5k 行）；`data/__init__.py` 245 行聚合的装载顺序契约（§3.1） |

### S6'-5 `commands/` → `game/content/commands/`

| 项 | 内容 |
|---|---|
| 动作 | `git mv game/commands game/content/commands`；环 R2 的三条边同时 +1；`main.py` 的 `from .game.commands import (...)` ×2 与 `from .game.commands._platform import` 改路径；旧路径 shim（引用者仅 main + scripts 7 + tests 24） |
| 验证 | 245 绿 |
| 风险 | R2 环必须整目录搬 |

### S6'-6 收口（→ 交 S9）

删 `game/content.py` 遗留死文件（S6'-1 已删）、`game/{data,core,store,services,commands,content_rules}`
旧路径 shim 留到 S9；更新 `ARCHITECTURE.md`。

**建议顺序理由**：原方案 `data → core → store → services → commands` 把**体量最大 + 环最多**的
data 放第一位。改为 **store 前置**：① store 是唯一「目录内零环」叶子；② 它的搬迁顺带完成
`content.py → content/` 这一**结构性突变**，此刻受影响面最小；③ `core`/`data` 互成 R1，放中段
（此时两侧 shim 均已在位，可逐条改边）。

---

## 6. ⛔ 阻塞项（必须先解决，否则 S6' 无法开工）

### 6.1 `game/content/` 包会**静默遮蔽** `game/content.py` —— 实测复现

复现（沙箱，非仓库内）：

```
$ mkdir -p game/content && echo "X='mod'" > game/content.py && echo "X='pkg'" > game/content/__init__.py
$ python -c "from game import content; print(content.X)"
取到: pkg
content.__file__ = …/game/content/__init__.py
```

与本仓库相关的事实（实测）：

| 项 | 值 |
|---|---|
| `game/content.py` | **19 行**，被 **201 处引用 / 136 个文件**（含 `game.content` 裸式 22 处、`from data.plugins.dragonfall.game import content` 包式 99 处、`from .. import content as C` 相对式等） |
| 包式引用（`data.plugins.dragonfall.game.*`，同一模块树） | `tests/**` 中 **389** 处 |
| 影响 | 一旦创建 `game/content/` 而不同时把聚合逻辑放进 `__init__.py`，**所有内容消费者会静默拿到空包/错对象**，不报错 |

→ **S6'-1 必须先做**：`game/content/__init__.py` 必须是 `game/content.py` 的等价聚合体，
`git mv`/`rm` 原 `.py` 与该创建**同一次提交**。
（这正是方案 §7.5 缺陷一在 `engine` 上踩过的同一类陷阱，`content` 是第二个实例。）

### 6.2 `store` 的 `from .. import content` 语义在搬迁后变化

`game/store/{connection,inventory,players,professions}.py` 各有 1 条模块级 `from .. import content as C`
（`connection.py:9` / `inventory.py:5` / `players.py:5` / `professions.py:11`）。

- 现状：pkg = `game.store` → `..` = `game` → 取到**聚合模块** `game/content.py`
- 搬迁后：pkg = `game.content.store` → `..` = `game.content`（**新包**）→ 取到包的 `__init__`
  （语义上仍应等于聚合体，故**在 S6'-1 原子完成后依然正确**；但若 store 先单独搬而
  `content/__init__.py` 尚未就位 → `ImportError`/错对象）

→ 两条路径**必须在同一步**处理（这也是 §5 把 store 与 content/`__init__` 绑在一起的原因）。

### 6.3 双模块树（`game.*` 与 `data.plugins.dragonfall.game.*`）

`tests/conftest.py:35` 同时 `sys.path.insert(0, QQBOT_DIR)` 与 `(0, PLUGIN_DIR)`，
仓库并存两种 import 风格：
- 包式 `from data.plugins.dragonfall.game import content as C, db, engine as E`（conftest）
- 裸式 `from game import content`（多数测试内联模板）

实测：`tests/**` 中 `data.plugins.dragonfall.game` 出现 **389** 处。
两棵树各自的 `battle2.config` 实例独立（`game/__init__.py` docstring 已说明），
**shim 必须让两条路径同时可用**（否则 245 里的某一半会红）。

---

## 7. `sys.path` / 目录推导痛点（实测）

| 位置 | 现状 | 迁移影响 |
|---|---|---|
| `scripts/run_all_tests.py:46-48` | `PLUGIN_DIR = dirname(dirname(__file__))` → `TESTS_DIR` → `QQBOT_DIR = dirname^3` | 不动 `tests/` 位置则无需改；若 `tests/` 移动则三段推导全断 |
| `scripts/run_all_tests.py:49` | `PYTHON` **硬编码** `C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe` | 与目录无关，忽略 |
| `scripts/run_all_tests.py:52` | `SHIM_DIR = TESTS_DIR/shim_astrbot` | 同上 |
| `scripts/run_all_tests.py:85-90`（**第 89 行**） | `_TPL_INIT` 硬编码 `from data.plugins.dragonfall.game.store import init_db`（**包式 + 具体到 store**） | ⚠️ **`store` 一旦搬迁，此模板立即失效**（每个并行 worker 建库都会炸）→ S6'-1 必须同步改这一行 |
| `scripts/run_all_tests.py:78-80` | `_SHARED_DB_RE` 正则扫 `os.environ["GWEN_GAME_DB"] = …test_game_data.db` | 与目录无关 |
| `scripts/run_all_tests.py:58+` | `SERIAL_SLOT` 硬编码 2 个测试文件名 + 私有库路径 | 与目录无关 |
| `tests/conftest.py:29-30` | `sys.path.insert(0, QQBOT_DIR)` / `(0, PLUGIN_DIR)`（38 行插 shim） | shim 双路径依赖它 |
| `tests/conftest.py:40` | `from data.plugins.dragonfall.game import content as C, db, engine as E` | **包式**；`engine` 为 shim，`content` 为聚合体 |
| 测试文件内联模板 | `tests/**` 中 **420** 个文件含 `sys.path.insert`（**581** 次）；`scripts/` 144 文件 185 次 | 只改 path 计算、不改 import 名（R3） |
| `main.py` | `from .game.commands import (`（16、338 行）、`from .game.commands._registry import COMMAND_REGEX`（68、418 行）、`from .game.store.world import …`（264）、`from .game.core.worlds import …`（271）；`os.path.dirname(__file__)` 仅用于定位 `scripts/playthrough_*.txt`（110-112 行） | `commands` 搬迁需改 4 处；`store`/`core` 各 1 处 |
| `game/game_data.db` + 4 个 `.bak_*` | 被 `.gitignore` 覆盖，不参与迁移（`.py` 扫描已排除） | — |

---

## 8. 阶段 B 决策：**未实施搬迁**（原因）

任务铁律 2 明令「**不许 `git mv` 搬目录** —— S6' 改为方案产出，实际搬迁经父 agent 审批后再做」，
且上述盘点显示**没有任何候选满足「风险极低」三条件（无环 + 引用者少 + 可用 shim 完全遮罩）**：

| 候选 | 目录内环 | game/ 内引用者 | 阻塞项 | 判定 |
|---|---|---:|---|---|
| `store` | 无 | 8 | 必须先完成 `content/` 包化（§6.1/6.2）+ 改 `run_all_tests.py:83` 模板 | ❌ 非「极低」 |
| `content_rules` | 无 | 2 | 引用面最小，但 `bootstrap`/`engine` shim 双侧联动 + 仍是 S6'-2 | ❌ 需审批批次 |
| `data` / `core` | 无（但互成 R1） | 53 / 28 | R1 环 + shim 面最大 | ❌ 高危 |
| `commands` | ⚠ 3 节点环 | 0(game)/24(tests) | R2 环 + main.py 改路径 | ❌ 非「极低」 |
| `battle2` | ⚠ 8 节点环 | 21 | **引擎，铁律 1 禁改** | ❌ 绝对不动 |

→ **阶段 B 产出 = 本档 §5 的子步序列**（可单独 245 绿 + 单独 revert），等父 agent 审批。
**唯一未做但零风险可做的替代动作**（本轮已做）：把 S7 装配入口落在
`game/content_rules/apply.py` —— 该目录本就存在且是 S6'-2 的搬迁对象，无需搬目录即可验证接口。

---

## 9. 附录：本轮侦察命令与产出

| 用途 | 命令 |
|---|---|
| 基线回归 | `"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe" scripts/run_all_tests.py` |
| 三层分类 / 分组边矩阵 | `python recon_s6.py <REPO>` |
| 目录内受限 SCC / 出边 | `python recon_s6e.py <REPO>` |
| 引用者分类表 | `python recon_refs2.py <REPO>` |
| 惰性 import 清单（840 条） | `python recon_lazy.py <REPO>` |
| `content` 遮蔽复现 | 沙箱 `mkdir game/content` + `content.py` vs `content/__init__.py`（§6.1） |

侦察脚本落在工作区（**不在仓库内**，避免污染）：
`C:\Users\yuyu\AppData\Local\hermes\workspace\recon_s6{,b,c,d,e}.py`、`recon_refs{,2}.py`、
`recon_lazy.py`、`lazy_imports2.txt`（840 条惰性 import 明细）。

**本轮仓库内改动（仅 2 个新文件，均 untracked、无 `git add/commit`）**

| 文件 | 说明 |
|---|---|
| `game/content_rules/apply.py` | S7 单一装配入口（`apply_game_content` / `ensure_engine_configured`） |
| `tests/test_apply_game_content.py` | S7 验收（顺序契约 / 幂等 / 新旧等价 / 数值抽样，35 断言全绿） |
