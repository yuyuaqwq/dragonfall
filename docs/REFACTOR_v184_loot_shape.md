# REFACTOR v184 —— 物品形状 → 引擎（路线图 #7，字段级设计）

> 目标：**掉落 / 档位(品质) / 词条挂载**三件形状搬进引擎，与具体物品表解耦。
> 判据（roadmap §一）：把常量、枚举、名词全拿掉，逻辑还成立吗？成立 = 形状。
> 本轮：**框架侧新建 `saintess_engine/loot/`** · **内容侧 `drop_engine` / `affix` / 四处档位调用改调用** ·
> **编辑器新增 `drop_pools` 域**。

---

## 一、现状：一份形状，五个副本 + 两处内联抄写

| # | 位置 | 内容 |
|---|---|---|
| 1 | `game/drop_engine.py:37` `_weighted_pick` | 加权抽取（权重和 → 随机点 → 累加命中 → 兜底末项） |
| 2 | `game/drop_engine.py:415` `POOL_STRATEGIES` + 四策略 | 池 + 策略注册表 + `roll()` / `expand_pool()` / `audit_all()` |
| 3 | `game/drop_engine.py:203` `_quality_weights_inline` | ★ **`core/fishing._quality_weights` 的内联副本**（注释自称"防循环 import"） |
| 4 | `game/core/fishing.py:80` / `smith_stock.py:124` / `commands/misc.py:308` / `core/event_templates.py:340` | 四处各自 `random.choices(..., weights=...)`，**档位与权重就地写死** |
| 5 | `game/core/affix.py:78` `roll_affixes` + `data/equipment.py` `AFFIX_COUNT` | 档位 → 词条条数（定值 / `[3,4]`+20%）+ 池过滤 + 不可重复抽样 |
| 6 | `game/data/equipment.py` `QUALITY` / `QUALITY_ORDER` / `QUALITY_CN` | 档位阶梯（顺序 / 倍率 / 颜色 / 名 / 中文别名）——垂钓、坐骑、宠物、签到**各自再抄一遍顺序** |

问题不是行数：`drop_engine` 里那套（池 / 策略 / 展开 / 审计）**完全不含游戏名词**，
换一套池数据照样跑 —— 它是形状，却长在内容仓里，且与外层四处档位逻辑互不相认。

## 二、剥出来的形状：`saintess_engine/loot/`

四件事：**加权抽取** · **池与策略** · **档位阶梯** · **槽位挂载**。

```python
from saintess_engine.loot import LootTable, TierTable, pick_weighted, pick_many, draw_slots

# ① 加权抽取（最小原语；rng 注入 = 可复现）
pick_weighted(entries, weight_key="w", rng=None)      # → entry | None（空/全零→None；末项兜底）
pick_many(entries, n, weighted=False, replace=False, where=None, rng=None)   # 等概率或带权

# ② 池 + 策略（内容侧把「池数据 + 引用解析 + 自定义策略」挂进来）
t = LootTable(pools, resolver=my_resolver, strategies={"fish": my_fish}, inline_prefixes=("gold:", ...))
t.roll("gather:oak_plain", ctx, qty=2)   # 唯一入口；池不存在/抽空 → []（不抛错）
t.expand("chest:wild_low")               # 带权展开候选
t.audit()                                # 结构审计：断链 / 空池 / 权重和 / 子池缺失

# ③ 档位阶梯（品质那一类「有序档位 + 每档倍率 + 按等级插值的权重表」）
T = TierTable(["white", "green", "blue", "purple", "orange"],
              info={"white": {"mult": 1.0, "name": "普通"}, ...},
              weights_by_level={1: [...], 3: [...], 5: [...], 7: [...], 9: [...]},
              aliases={"white": "白", ...})
T.index("blue"); T.next_tier("blue"); T.info_of("green")
T.weights_at(4)                          # 等级 → 权重行（线性插值）
T.pick(level=4, exclude=("orange",), rng=rng)     # 按权重抽一档
T.pick_weights([45, 40, 15], rng=rng)             # 就地给权重行也行
T.upgrade("blue", chance=0.05, steps=1, rng=rng)  # 概率升档（封顶）

# ④ 槽位挂载（词条那一类「固定前缀 + 随机补足到档位条数 + 不可重复」）
count_for({"white": 0, "orange": [3, 4]}, "orange", extra_chance=0.20, rng=rng)   # 条数规则
draw_slots(pool, count, fixed=("series_affix",), no_dup=True, rng=rng)            # 先固定后随机补足
```

| 形状 | 语义 | 谁给 |
|---|---|---|
| `pick_weighted` / `pick_many` | 权重和 → 随机点 → 累加命中；等概率或带权、可放回/不放回 | 引擎 |
| `LootTable` | 池集合 + 策略注册表 + `roll/expand/audit`；**池 key / 引用 / 上下文是内容侧的事** | 引擎（绑定由内容给） |
| 策略 `weighted`/`fixed`/`table`/`table_choice` | 内置于引擎（不含游戏词）；`fish` 这类专属策略内容侧 `register_strategy` 挂进来 | 内置 + 内容扩展 |
| `resolver(ref, ctx)` | **引用怎么解析成实物**（`equip:` / `gold:` / 物品 ID…）——引擎只调它，不认识前缀 | 内容侧 |
| `inline_prefixes` | 哪些前缀算「内联引用」（审计时需要，属内容词汇表） | 内容侧 |
| `TierTable` | 有序档位 + 每档信息 + 按等级插值的权重表 + 抽档 / 升档 / 比较 | 引擎 |
| `count_for` / `draw_slots` | 档位→条数（定值或区间+命中概率）；固定前缀 + 随机补足、不可重复 | 引擎 |

**零知识**：引擎不知道「品质」「词条」「掉落」这些词，只认 `tier` / `pool` / `entry` / `ref` / `count`。
**rng 注入**：所有随机走传入的 `rng`（默认 stdlib `random`）——这是「可复现 + 可逐格比对」的前提。

## 三、内容侧适配

| 旧 | 新 |
|---|---|
| `drop_engine._weighted_pick` | `loot.pick_weighted` |
| `drop_engine.POOL_STRATEGIES`（全局 dict） | `LootTable(strategies={...})` 实例绑定；**对外名字 `POOL_STRATEGIES` 保留**（转发到实例表） |
| `drop_engine.roll/expand_pool/audit_all` | `_TABLE.roll(...)` / `.expand(...)` / `.audit()`（签名与返回不变） |
| `drop_engine._quality_weights_inline`（内联副本） | `TierTable.weights_at(lv)` —— **副本删除，`core/fishing` 与 `drop_engine` 同源** |
| `_resolve_item_ref` | **留在内容侧**，作为 `LootTable(resolver=...)` 传入 |
| `affix.roll_affixes` 的条数/抽样/过滤 | `count_for` + `draw_slots`；池过滤（武器/防具）留内容 |
| 四处 `random.choices(weights=...)` | `TierTable.pick/pick_weights`（档位顺序与权重仍由内容数据给） |

### 3.1 唯一真相源：`game/core/quality_tiers.py`

档位表**只建一份**（本轮新建）：

```python
QUALITY_TIERS = TierTable(QUALITY_ORDER, info=QUALITY, aliases=QUALITY_CN)
FISH_TIERS    = TierTable(QUALITY_ORDER, info=QUALITY, aliases=QUALITY_CN,
                          weights_by_level=FISH_QUALITY_WEIGHTS, clamp=(1, 9))
quality_of(word)                                     # 玩家输入（含中文别名）→ 档位 key
quality_up(quality, *, chance, steps, rng)           # 概率升档
```

顺序/倍率/颜色/中文名继续以 `data/equipment.py` 的 `QUALITY`/`QUALITY_ORDER`/`QUALITY_CN` 为准，
垂钓权重继续以 `data/fishing.py` 的 `FISH_QUALITY_WEIGHTS` 为准 —— **数据不动，只是读法收口到一处**。

实测（2026-09-12）：`FISH_TIERS.weights_at(lv)` 与旧 `core/fishing._quality_weights(lv)` 在 lv=0..11
**逐级位级一致**（含浮点尾数）。

**对外函数名与返回全部不变**（调用方零改动），逐格一致由回归证明（§五）。

## 四、编辑器 `drop_pools` 域

- `schemas/drop_pools.schema.json`：一条 = 一个池 `{type, entries[{item,w,n,min_lv,max_lv,…}], rolls[{pool,chance,cutoff,n,fallback}], fallback, desc}`；
  **零 enum**（策略名是内容侧注册的，不设枚举）。
- `editor/packages.py` 一行 + `glossary` 词典与分组。
- **池预览 API**：`GET /api/package/<id>/d/drop_pools/<key>/preview` —— 用引擎 **`expand()`**
  展开候选（带权重），非程序员能当场看见「这个池会出什么、权重多少」；
  展开失败（断链/空池）如实报错，不假装有内容。

## 五、验收（全部要实跑）

| # | 项 | 判据 |
|---|---|---|
| 1 | 框架门禁 | `tests/test_loot.py` **89 断言**（抽取原语随机流与末项兜底 / 策略注册表与元数据 / 四种内置策略 / 兜底钩子 / 展开与审计 / 档位插值与升档 / 挂载 / 零知识静态扫描 / rng 注入可复现） |
| 2 | 框架全量 | **28 文件 28 绿**（纯度 / 中立性 / wiki 行号 / JS 调度器） |
| 3 | ★ 内容侧逐格一致·池 | `tests/test_v184_loot_pools.py` **96 断言 / 34413 条逐项比对**：v174 原文逐字冻结（sha256 自检）+ 596 池全量 × 13 ctx × 4 种子 = 30 992 组合严格全等；`expand_pool` 596 池逐项；audit 判定逐项 + 真实数据 0 问题 |
| 4 | ★ 内容侧逐格一致·档位 | `tests/test_v184_loot_tiers.py` **3047 断言 / 4641 条逐项比对**：`roll_affixes` 7 部位×5 档×30 次（含橙装 20% 四词条分支）；垂钓权重 lv −3..12 **位级相等**；`generate_roster_equip` 55 件×20 次；锻造货架/签到/流浪商人各 300 种子（另含 2 万次分布校验）；源码级断言「全仓只有一处 `TierTable`」 |
| 5 | 真实库回归 | 游戏仓全量 **267/267**（265 + 2 门禁）/ 数值门禁 **18/18** / `compileall` 零错 |
| 6 | 编辑器 | `tests/test_editor_loot.py` **107 断言** + 真 HTTP 实测（四种内置策略各验一遍：share_pct / cutoff / 递归展开 / warnings；未知池 422、未知域 404；`/api/glossary` 含 drop_pools 14 字段 4 分组） |

### 5.1 已登记的 7 处有意差异（真实池数据 0 命中）

门禁 §7 逐条钉住「新行为」并写明旧行为：

| # | 差异 | 性质 |
|---|---|---|
| D1 | `gold:` 子引用带 `n` → 新按 `roll_range(n)` 乘 count（旧忽略） | 统一语义 |
| D2 | `weighted:` 前缀子池 → 新剥前缀正常抽（旧当内联引用，抽出垃圾） | 修 bug |
| D3 | 裸名册 id 当**条目** ref → 新放行（旧报断链）。引擎只给**一个** `resolvable` 回调，而旧实现条目侧/roll 侧判定不同；此处选忠实 roll 侧（`INSTANCE_BOSS_EQUIP_DROP` 老数据就是裸名册 id）。真实池数据 0/1435 | 二选一，登记 |
| D4 | `fixed` 池空 entries → 新报「空池」（旧不报） | 只多不少 |
| D5 | `table_choice` 的 rolls → 新按 `uses=rolls` 审（旧不审） | 只多不少 |
| D6 | `table` 池 roll 行的 `fallback` → 新应用（旧忽略，抽空就空） | 修 bug |
| D7 | **引擎自己那两条结构消息的措辞**：`条目无 item:` → `条目缺 item 字段:`；空 ref 的 `table 子池未知:` → `roll 无 pool`（判定不变）。引用类措辞由内容侧 `_resolvable` 逐字保留旧说法 | 措辞更直白 |

### 5.2 落地的过程中改掉的一个设计（否则会留兼容壳）

内容侧原先要保留自己更具体的审计措辞（「物品缺失 / 名册缺失 / 子池缺失」），而引擎的第一版
只给 `resolvable(resolvable) -> True/False/None` → 内容侧只能**事后按字符串前缀把引擎文案改回旧文案**
（一个脆的兼容壳：引擎一改措辞就静默失配）。

改法（框架 `ad34bad`）：回调签名扩为 `resolvable(ref, pool)`，返回值四态 ——
`True` 解得开 / `False` 断链（引擎通用措辞）/ **字符串 = 断链且用这句措辞**（内容侧用自己的词汇表说话）/
`None` 不判。于是**判定与措辞都在内容侧**，壳不需要了。

## 六、自己拍板的四项

| 项 | 决定 | 理由 |
|---|---|---|
| 模块名 | `loot` | 通用名词；比 `drop` 宽（含档位/挂载），比 `item` 窄（不认识物品表） |
| 策略注册表放哪 | `LootTable` **实例绑定**（保留模块级 `register_strategy` 给第三方） | 旧的全局 dict 改一次全局污染；实例绑定让内容侧"一张自己的表" |
| 参数名 | 沿用旧数据字段 `w` / `n` / `item` / `qty` | 改字段名要动全部池数据 —— 超出"搬形状"，属数据迁移 |
| `fish` 策略 | **留内容侧**（注册进表） | 季节/水域/鱼饵/血饵是这款游戏的内容，不是形状 |

## 七、不做（本轮明确排除）

- 不改池数据（`data/drop_pools.py` 零改动）、不改 `items.py`
- 不动 `generate_equip` / `generate_roster_equip` 的**取名**与套装逻辑（内容）
- 不动 `stat_affix_stats` 的折算表（`_STAT_AFFIX_FX` 是数值配置，属内容）
- 宝石/符文/附魔的**数值**不动（只把它们用到的档位顺序接到 `TierTable`）
