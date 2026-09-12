# 指令表迁移（路线图 #9）—— 现状 / 做法 / 门禁

> 2026-09-12。目标：命令正则从「两处来源」收敛到**声明表唯一真源**。
> 相关：框架 `saintess_engine.command.CommandRegistry`、`docs/engine-wiki/reference/declarative-commands-and-texts.md`。

## 一、为什么迁

命令正则原先有两处来源：

```text
① 各文件 @filter.regex(<字面量>)           ← 真实注册（AstrBot）
② game/commands/_registry.py _LITERAL_REGEX ← 手工维护的镜像表
   （供 停服 gate / 快捷转发回退 / 测试 用）
```

两处互相同步 → **一定会漂移**，只能再配一个「表与装饰器 1:1」测试盯着（`test_v87_command_matrix.py`）。
迁移把 ① 换成 `@declared("key")`（正则从 `game/data/command_specs.json` 取），并删掉 ② 的同名条目
→ 声明表成为唯一真源；`COMMAND_REGEX = {**声明派生, **尚未迁的字面量}` 对外名字与形状不变。

## 二、现状（2026-09-12 收工口径）

| 项 | 值 |
|---|---|
| 有效指令表 `COMMAND_REGEX` | **194 条**（冻结快照 `tests/_command_table_freeze.json`，sha256 双锁） |
| 已迁（声明表 `game/data/command_specs.json`） | **186 条** |
| 未迁（`_registry._LITERAL_REGEX`） | **8 条 = `instance.py` 全族**（副本/深入/副本地图/调查/撤退/确认撤退/离开副本/加入战斗） |
| `_registry.py` 体量 | 324 → **106 行**（只剩表头纪律注释 + 8 条字面量 + 派生/合并逻辑） |

未迁那 8 条**有意留到最后**：`instance.py` 是另一会话「副本进度/名单」的改动目标文件，
同仓并发改同一文件撞车成本高。收尾时按 §三 同一套做法迁即可。

## 三、迁一条的做法（三步，可停、可增量）

```text
1. game/data/command_specs.json 加声明：
     {"<key>": {"patterns": ["<正则，逐字来自字面表>"], "desc": ..., "category": ...,
                "usage": ..., "guards": ["player"], "order": N, ["visible": false, ]
                ["page_size": N, ] ["extra": {"note": "设计来历/坑"}]}}
2. 该方法的 @filter.regex(r"…"[, priority=…])  →  @declared("<key>"[, priority=…])
3. 从 _registry.py 的 _LITERAL_REGEX 删掉同名条目（连同上方的 key 专属注释；
   表头注释块永不删）
```

批量工具（**已入库 scripts/**）：

```bash
# 1) 看某个模块还有哪些指令没迁（导出上下文：装饰器链 / 字面表值 / 表注释 / docstring）
python scripts/command_decl_context.py instance.py
# 2) 写 batch.json（形如 {"file": "instance.py", "items": {"<key>": {desc/category/usage/order/note…}}}）
# 3) 先 dry-run 看要改什么，再实跑
python scripts/migrate_command_decl.py _batch.json --dry-run
python scripts/migrate_command_decl.py _batch.json
# 4) 冻结快照校验（跑完应打印 差异: 0）
python scripts/command_table_freeze.py
```

`migrate_command_decl.py` 的自检项：

* 装饰器字面量 **==** 字面表同 key 的值（不等直接抛，不做「差不多」）
* `guards` 由**装饰器链**派生（`require_player`→`player`、`require_battle`→`battle`），不手填
* 正则**逐字**搬到声明（禁止顺手「规范化」——那会改命令面）
* 全部迁完的模块顺带摘掉不再使用的 `filter` 导入（只看代码，注释里的提及不算）

## 四、门禁

| 门禁 | 断言 | 作用 |
|---|---|---|
| `tests/test_v185_command_migration.py` | 12 断言：当前有效表 **== 冻结快照**（键集合 + 每条正则逐字 + sha256）；无双源（`OVERLAP_KEYS` 空）；无 key 丢失/凭空多出；比较器反证（改/删/加一格必报红） | ★ **搬家只能搬家**：迁移每一批后命令面一个字都不能变 |
| `tests/test_v87_command_matrix.py` | 表与装饰器 1:1（逐字）+ 互斥矩阵 232 样本 + 停服 gate 覆盖 | 防漂移与双触发 |
| `tests/test_v181_command_declaration.py` | 派生保真 / combine 同语义 / 漂移双向干净 / 声明表过编辑器 schema / catalog 有消费者 | 声明驱动本身的不变量 |
| `tests/test_command_parse.py` | 命令词无跨 handler 冲突 + 历史 bug 回归 + 200 次 fuzz 无双触发 | 解析层回归（扫描走 `tests/_cmd_registry.py` 共享 helper） |

冻结快照的生成/校验：`python scripts/command_table_freeze.py`（`--write` 只在**迁移开始前**用；
日后新增指令须显式更新快照，否则门禁按「凭空多出来的 key」报红）。

## 五、本轮踩到的两个坑（都已修）

1. **扫描实现残留**：`test_command_parse.py` 自带一份「只认 `@filter.regex` 字面量」的正则扫描
   → 迁到声明表的指令**整体掉出正则池**，当场 3 例变红（宠物改名小黑/公会签到5/公会任务 命中 `[]`）。
   修法：改用共享 helper `tests/_cmd_registry.py`（2026-09-11 建它正是为了避免三处重复扫描），
   并按 v87 口径剔除停服全局 gate `_maint_gate`。
2. **表头注释块被误删**：批处理把「上一个 key 迁走后」错挂到下一个 key 上的**表头纪律注释**
   当成了「key 专属注释」删掉（第五批实测触发）。修法：按结构定位表头（紧跟 `_LITERAL_REGEX = {`
   的注释行）设为**永不删除**；表头文案同步更新为迁移期口径。

## 六、收尾 checklist（迁完 instance.py 后）

- [ ] 迁移后 `_LITERAL_REGEX` 为空 → `_registry.py` 可再瘦身（只剩「读声明 → 派生 → 合并」）
- [ ] 把快照里的注释/文档口径改成「声明表是唯一真源，字面量表已退役」
- [ ] 路线图 §二 #9 标记完成；`docs/engine-wiki/reference/declarative-commands-and-texts.md` 同步
- [ ] 帮助/目录可考虑改由 `catalog()` 生成（声明里的 desc/category/usage/order 已在表里就位）
