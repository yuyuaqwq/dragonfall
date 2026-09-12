# REFACTOR v183 —— 地图形状 → 引擎（路线图 #6，字段级设计）

> 目标：把「派生 / 邻接 / 出口匹配」从**具体地图数据**里剥出来，做成引擎形状。
> 判据（roadmap §一）：把常量、枚举、名词全拿掉，逻辑还成立吗？成立 = 形状。
> 本轮：**框架侧新建 `saintess_engine/space/`** · **内容侧 `game/core/maps.py` 改调用** ·
> **编辑器 `maps` 域 + 拓扑视图**。

---

## 一、现状：一份形状，四个副本

| # | 位置 | 内容 |
|---|---|---|
| 1 | `game/core/maps.py:72-127` `subarea_links` | 邻接：显式网状 → 否则「城镇星形 / 野外线性」 |
| 2 | `game/core/maps.py:182-204` `subarea_depth` | 深度：显式网状 BFS / 否则声明序 |
| 3 | `game/core/maps.py:130-166` `map_exit_subarea` + `map_entry_subarea` | **两份逐字相同的实现**（城镇取出口子区域，否则首个子区域） |
| 4 | `game/services/travel.py:158-170` · `game/commands/world.py:933-940` | 各自又抄了一遍「星形链首必经」判断（文本提示用） |

问题不在行数，在于：**这四条都是形状，却写在内容侧、且互相不共享**。
数据侧稍一改（新增一种子区域角色、改星形规则），要同时改 4 处 —— 典型的双源。

## 二、剥出来的形状：`saintess_engine/space/`

一个空间 = **有序节点表 + 拓扑名 + 角色映射**，其余全是派生。

```python
from saintess_engine.space import Space, register_topology

sp = Space(
    nodes=[{"id": "a", "role": "hub"}, {"id": "b"}, {"id": "c", "role": "exit"}],
    topology="star",                       # chain | star | mesh |（第三方注册）
    roles={"hub": "hub", "through": "through", "exit": "exit"},
    links=None,                            # 显式连通表 {id: [id…]}；给了就优先（拓扑让位）
    label_key="name",                      # 可选：视图里带出的显示字段
)
sp.links("a")        # → ["b", "c"]   邻接（显式表优先，否则按拓扑派生）
sp.adjacency()       # → {id: [id…]}  全图（画图 / 审计用）
sp.depth("c")        # → 2            深度
sp.gate()            # → "c"          跨图落点 / 出图点（★ 老的 entry/exit 两个名字合一）
sp.route("a", "c")   # → ["a", "c"]   必经路径；不可达 → []
sp.audit()           # → {ok, dangling, asymmetric, isolated, unreachable, no_gate}
sp.to_view()         # → dict（编辑器 / 序列化用；纯 JSON）
```

| 概念 | 语义 | 谁给 |
|---|---|---|
| `nodes` | 有序节点表；**顺序有意义**（链状/星形的「深度」= 声明序） | 内容侧 |
| `role` / `roles` | 节点角色 + 「哪个值算 hub/through/exit」的映射表 | 内容侧 |
| `topology` | 形状名：`star` / `chain` / `mesh` | 内容侧（或显式连通表） |
| `links` | 显式连通表（非 None → 优先，拓扑不参与） | 内容侧 |
| `gate` | 出入口节点（星形=外围出口节点，链/网状=入口节点） | 拓扑声明 |
| `route` / `depth` / `audit` / `to_view` | 派生 | **引擎** |

### 2.1 形状名与规则（原样搬，逐格等价）

**`chain`（链状 / 线性）** —— 按声明序相邻：`i ↔ i+1`；`gate = 首节点`。

**`star`（星形）** —— 枢纽在外、辐条在内、经「通道」出图：

```text
枢纽(hub)  → 全部非 exit 节点；★ 若无 through 节点，则枢纽**额外**直连 exit（防断链）
通道(through) → 全部 exit 节点 + 枢纽
出口(exit)  → 全部 through 节点；若无 through，则直连枢纽
其余角色    → 枢纽
gate        → 第一个 exit 角色节点；没有则首节点
```
（这三条防断链分支是原实现在真实数据上踩出来的：白鹿城 / 铁港城缺街道链，
不补就是「广场→出口 先经过自己」的死循环。）

**`mesh`（显式网状）** —— `links` 直接给全图邻接；`gate = 首节点`。
（副本房间连通表就是这个形状；副本「无出口」是内容侧的事，引擎不管。）

**深度**：显式连通表 → **从首节点 BFS**；派生拓扑 → **声明序**（作者按由近及远排）。
两条口径不同是**故意的**：网状图没有天然顺序，链/星形的顺序本身就是数据。

**`audit()`**：`dangling`（连到不存在的 id）/ `asymmetric`（a→b 但 b↛a）/ `isolated`（零邻接）/
`unreachable`（从首节点不可达）/ `no_gate`（星形但无 exit 角色）。**只报不改** —— 由内容侧决定处置。

**可拔插**：`register_topology(name, fn)`；`fn(nodes, *, roles, role_key, root) -> {"links": {...}, "gate": id}`。
第三方要做环形 / 网格 / 房间迷宫，注册一个函数即可，引擎不预设形状集合。

**零知识**：`hub/through/exit` 只是**角色名**（引擎不认含义），角色**取值**由内容侧给
（本游戏是「城镇 / 城镇街道 / 城镇出口」）。引擎不 import 宿主、不认地图、不认玩家。

## 三、内容侧适配（`game/core/maps.py`）

```python
_ROLE_BY_TYPE = {SUB_TYPE_TOWN: "hub", SUB_TYPE_STREET: "through", SUB_TYPE_GATE: "exit"}

def _space(map_id):                      # 无缓存（SUBAREAS 运行期可被副本克隆增补）
    sas = SUBAREAS.get(map_id, [])
    nodes = [{"id": s["id"], "role": _ROLE_BY_TYPE.get(s.get("type"))} for s in sas]
    topo = "star" if (nodes and nodes[0]["role"] == "hub") else "chain"
    mesh = SUBAREA_LINKS_INDEX.get(map_id)
    return Space(nodes=nodes, topology=topo, roles=_ROLES, links=mesh)
```

对外**函数名与返回全部不变**（`subarea_links` / `map_exit_subarea` / `map_entry_subarea` /
`subarea_depth`），只是实现改为「建 Space → 问引擎」：

| 旧实现 | 新实现 |
|---|---|
| 星形/线性 40 行 + 网状 8 行 | `_space(map_id).links(sa_id)` |
| `map_exit_subarea` / `map_entry_subarea` 两份逐字相同 | 两者都 = `_space(map_id).gate()`（保留函数名，注释写明同义） |

**提示文本处的两个副本**一并收口：

| 位置 | 旧 | 新 |
|---|---|---|
| `travel.py move_blocked_msg` | 广场→链上目标特判「先经过链首」+ 非城镇按 links 拼名 | `route(cur, tgt)` 的**中间站名**拼串（无可达路径 → 原兜底） |
| `world.py _subarea_body` 出城提示 | 广场时 `chain[0]`，否则出口名 | `route(cur, gate)` 的**第一个中间站**名 |

**行为等价性**由回归证明（见 §五），不靠读代码。

### 3.1 性能（实测，不是估计）
每次 `subarea_links` 调用现在要构造一个 `Space`（O(节点数)），旧的星形分支是 O(1) 扫描：

| 场景 | 旧 | 新 |
|---|---|---|
| 单次查询（7 子区域的城镇） | 4.1 µs | 34.4 µs |
| 整图遍历（7 子区域 × 200 轮） | — | 42 ms → **0.2 ms/次** |

绝对值可忽略（命令路径上一只手数得过来的调用），因此**不加缓存**：`SUBAREAS` 运行期会被
副本克隆增补，缓存键做不干净就会读到半成品 —— 宁可慢 30 微秒，不要一个偶发的幽灵地图。

## 四、编辑器 `maps` 域

- `schemas/maps.schema.json`：一条 = 一张图 `{name, topology, roles, nodes[{id,name,role,…}], links, desc}`；
  **不含 enum**（门禁：schema 枚举值不得含非 ASCII；角色取值由内容侧自定）。
- `editor/packages.py` 加一行 `"maps"`；`editor/glossary.py` 加 `_MAPS` 词典 + `GROUPS["maps"]` 分组。
- **拓扑视图**：`GET /api/package/<id>/d/maps/<key>/graph` → 用引擎 `Space.to_view()`
  （**同一份派生代码**，不在 JS 里重写第二遍）→ 前端 `app.js` 加 `graph` 模式：
  按深度分层画节点、连边，角色配色，`audit` 问题图上明示（悬空红虚线 + 虚影节点 / 不对称琥珀虚线 /
  不可达·孤立置灰）。
- 落地：`editor/space_view.py`（适配层）+ `editor/packages.py` 一行 + 词典 `_MAPS` + 分组 3 组 +
  `editor/web/{index.html,app.css,app.js}`（第四档「拓扑」，仅 maps 域出现；布局是**纯函数**
  `graphLayout()`，由 `tests/js/graph_layout_test.js` 抠出来用 Node 真跑）+ 示例包
  `games/my_game/content/data/maps.json`（星形 / 链状 / 显式连通表各一张）。
- 主进程 import `saintess_engine.space` 的说明：`space` 是**纯计算模块**（零挂载、零全局副作用），
  与 `version` 同性质；`packages.py` 原有「编辑器主进程不 import 引擎」的纪律针对的是**会挂 hook 的
  战斗域**，此处不违背 —— 且换来「派生只有一份」。

## 五、验收（全部要实跑）

| # | 项 | 判据 |
|---|---|---|
| 1 | 框架门禁 | `tests/test_space.py`：拓扑规则 / 防断链三分支 / 深度两口径 / gate / route / audit / 注册表 / 零知识（不出现角色取值） |
| 2 | 框架全量 | 23 → 24 文件全绿（纯度 / 中立性 / wiki 行号） |
| 3 | ★ 内容侧逐格一致 | 新门禁 `tests/test_v183_space_shape.py`：**全 47 图 × 全子区域**逐条比对（旧实现快照 vs 新实现）—— 邻接 / 深度 / 出入口 |
| 4 | 真实库回归 | 游戏仓全量 264/264 + 数值门禁 18/18 + `compileall` |
| 5 | 编辑器 | 门禁 `tests/test_editor_space.py` **51 断言** + JS 单测 34 断言 + 框架全量 **25/25**；**真浏览器 + 真 HTTP 实测**：星形图 5 列按声明序 / 8 边 / `▶` 在入口 / 外环在出口、坏图虚影节点 + 2 节点置灰 + 悬空边红虚线（computedStyle 实测） |
| 6 | 性能 | 单次查询 4.1µs → 34.4µs（整图遍历 0.2ms/次），**不加缓存**（理由见 §3.1） |

## 六、自己拍板的三个待定项

| 项 | 决定 | 理由 |
|---|---|---|
| 模块名 | `space`（不叫 `map`/`graph`） | `map` 与内建/内容侧 `MAPS` 撞；`graph` 偏数据结构名；`space` 是「空间形状」语义位 |
| `entry` / `exit` 两名 | 引擎只留 **`gate()`** 一个 | 内容侧那两份逐字相同的实现是纯双源；合一后由函数名兼容层承担 |
| 深度两口径 | **保留**（显式→BFS，派生→声明序） | 强行统一会改数值（星形图 gate 深度 3→2），属改行为，不在「搬形状」范围内 |

## 七、不做（本轮明确排除）

- 不改任何地图数据（`data/maps.py` / `data/subareas.py` / `dungeon_links.py` 零改动）
- 副本 `instance.py` 直读数据表的路径不动（它读的是原始连通表，不是派生）
- 不把 `MAP_CONNECTIONS`（跨图连边）纳入本模块 —— 那是「图与图之间」，属下一步（#8 副本形状）的邻接
