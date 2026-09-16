# 指令表单源化（路线图 #9）—— 现状 / 做法 / 门禁

> 2026-09-12 完成。相关：框架 `saintess_engine.command.CommandRegistry`、
> `docs/engine-wiki/reference/declarative-commands-and-texts.md`。

> ⚠️ **2026-09-17 现状订正（Gwen，实测）**：本文写于「宿主仍是真源」的时期，此后**真源已归包**，
> 三处口径按现状读：
> 1. **声明表真源 = 包内** `content/data/commands.json`（引擎走 `Package.command_declarations()` 读它）；
>    文中提到的 `game/data/command_specs.json` **已无任何运行期读者**（全仓 grep：只剩本文档与
>    `scripts/gate_fast.py` 的 glob 模式），内容与包内那份 **JSON 级完全相同**（196 键 / 0 键差异 / 0 值差异，
>    仅序列化字节不同）⇒ 它是**待删的历史镜像**（删时需同步 `scripts/gate_fast.py` 的 glob 与 NO_GATE 表）。
>    （对照：`game/data/tlogs.json` 是**合法部署期镜像**，有 `scripts/mirror_tlogs.py` 单向同步 + 唯一读者
>    `host/tlog_setup.py`，不要与前者混为一谈。）
> 2. **条数 194 → 196**（V2 重铸新增 `reroll` + S4/S2 补登记两个域）；冻结快照
>    `tests/_command_table_freeze.json`（**在包仓**）`count = 196`、`sha256 = 5d16c8e4f629bddd…`。
> 3. 改一条指令的姿势同理：改**包内** `content/data/commands.json`，不再改宿主那份。

## 一、结果一句话

**194 条指令 100% 来自声明表**（`game/data/command_specs.json`）；原先手工维护的镜像表
（`_registry._LITERAL_REGEX`）**已删除**；命令层源码里**零 `@filter.regex` 装饰器**；
**命令面逐字未变**（冻结比对门禁全程绿）。

## 二、为什么（历史问题）

命令正则原先有两处来源：

```text
① 各文件 @filter.regex(<字面量>)             ← 真实注册（AstrBot）
② game/commands/_registry.py _LITERAL_REGEX  ← 手工维护的镜像表
   （供 停服 gate / 快捷转发回退 / 测试 用）
```

两处互相同步 → **一定会漂移**，只能再配一个「表与装饰器 1:1」测试盯着（`test_v87_command_matrix.py`）。
迁移把 ① 换成 `@declared("key")`（正则从声明表取），删掉 ② → **声明表是唯一真源**。

## 三、现状（2026-09-12 收工口径）—— ⚠️ **以下数字是历史值，现行口径见本文顶部「2026-09-17 现状订正」**

| 项 | 值 |
|---|---|
| 有效指令表 `COMMAND_REGEX` | **194 条**（= 声明表派生） |
| 声明表 `game/data/command_specs.json` | **194 条**（含 desc/分类/用法/守卫/排序；73 条带 `extra.note` 记设计来历） |
| `_LITERAL_REGEX` / `OVERLAP_KEYS` | **已删除**（结构上不可能再漂移） |
| 命令层 `@filter.regex` 装饰器 | **0**（AST 扫描断言） |
| `_registry.py` | 324 → **78 行**（只剩「读声明 → 派生 → 合并别名」） |
| 冻结快照 `tests/_command_table_freeze.json` | 194 条 + sha256 `7fe285c7…` |

## 四、新增 / 修改 / 删除一条指令（**现在的唯一姿势**）

```text
1. 改 game/data/command_specs.json：
     {"<key>": {"patterns": ["^…$"], "desc": …, "category": …, "usage": …,
                "guards": ["player"], "order": N, ["visible": false, ] ["page_size": N, ]
                ["extra": {"note": "设计来历 / 坑"}]}}
   · guards 名 = 装饰器链语义（require_player→"player"、require_battle→"battle"、
     no_prof_waiting→"no_prof_waiting"）
2. 命令层方法上写 @declared("<key>")（key **就是**方法名惯例）+ 守卫装饰器链
   → 正则、帮助/目录元数据全部从声明表来；不要写 @filter.regex 字面量
3. 显式更新冻结快照（**只有有意变更命令面时才做**）：
     python scripts/command_table_freeze.py --write
   否则 tests/test_v185_command_migration.py 会按「凭空多出来的 key / 正则变了」报红 —— 这是设计如此
4. 跑门禁 + 全量回归（下节）
```

## 五、门禁

| 门禁 | 断言 | 作用 |
|---|---|---|
| `tests/test_v185_command_migration.py` | 12 断言：有效表 **== 冻结快照**（键集 + 每条正则逐字 + sha256）；单源结构（有效表键集 == 声明表键集 / 无镜像表残留 / AST 扫描零 `@filter.regex`）；无 key 丢失或凭空多出；比较器反证（改/删/加一格必报红） | ★ **命令面冻结** + 单源结构 |
| `tests/test_v87_command_matrix.py` | 有效表键集 == 装饰器集（逐字）+ 互斥矩阵 232 样本（一条消息恰好命中 1 条）+ 停服 gate 覆盖 | 防漂移 / 防双触发 |
| `tests/test_v181_command_declaration.py` | 单源 / 派生保真 / `_combine_patterns` ≡ 框架实现 / 漂移双向干净（死声明·漏登记）/ 声明表过编辑器 schema / `catalog()` 可用 | 声明驱动自身的不变量 |
| `tests/test_command_parse.py` | 命令词无跨 handler 冲突 + 历史 bug 回归 + 200 次 fuzz 无双触发 | 解析层回归 |

扫描实现**只此一处**：`tests/_cmd_registry.py`（`@filter.regex` 与 `@declared` 两种写法都认）。

## 六、迁移踩到过的坑（已修，供后人避免）

1. **「读源码找正则」的测试是迁移的绊脚石**（踩了 3 次）：`test_command_parse.py` 只认
   `@filter.regex` 字面量 → 迁走的指令整体掉出正则池（3 例当场红）；`test_commands_skills.py`
   / `test_v1302g_job_guide.py` 断言源码里有正则串。修法一律是**改成对有效表/声明表断言**
   （更强：证的是真正注册的那个值，而不是某处的文本）。
2. **表头注释块被误删**：批处理把「上一个 key 迁走后」错挂到下一个 key 上的表级纪律注释
   当成了 key 专属注释（实测触发）。修法：按结构定位表头（紧跟 `_LITERAL_REGEX = {`）并保护。
3. **声明表 JSON 是 indent=2 且保留键序**（不是 `sort_keys`）——脚本自作主张排序会把整文件重排。
4. **`filter` 导入摘除要看代码不看注释**（`world.py` 有一条注释提到 `@filter.regex`；
   `base.py` 仍需要 `filter`，因为它还用 `@filter.custom_filter`）。

## 七、迁移过程存档（历史，2019 行 diff 都在 git 历史里）

```text
第一批 social.py 33      第二批 player.py 22        第三/四批 combat.py 15 + gm.py 21
第五批 economy.py 45     第六批 world.py 37         第七批 单条域 6
第八批 instance.py 8     —— 194/194 完成
每一批都跑：冻结比对 + v87 矩阵 + v181 声明 + 解析回归 + 全量
本文件所在提交链：8b7af65 → 7dd64cb →（第八批/收尾）
```

迁移用的批处理工具（`@filter.regex` → `@declared`，含「装饰器值 == 镜像表值」等自检）
随迁移收尾一并移除 —— 已无待迁对象；需要时从 git 历史取。
