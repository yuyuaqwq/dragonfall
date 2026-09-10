# 奥兰迪亚 · 配置编辑器（技能 / 词条域）

零第三方依赖的可视化配置编辑器：**stdlib Python 后端** + **原生 HTML/CSS/JS 前端**。
路线图阶段 2.2（MVP：技能域）+ 2.3（战斗模拟预览 / 按 kind 定制表单 / 域扩展）的落地
（技术方案见仓库根 `EDITOR_SPEC.md`）。

```bash
python editor/server.py            # 默认 http://127.0.0.1:8765
python editor/server.py --port 9000
python editor/server.py --host 0.0.0.0   # 局域网可访问（谨慎）
```

任何装了 Python 的机器都能直接跑，**不需要 Node / npm / pip install**。

## 目录

```
editor/
  server.py           # stdlib http.server：静态文件 + /api/domain/* + /api/simulate
  data_io.py          # 多域：py→JSON 读取（ast 字面量）+ 工作副本写入 + schema 校验
  simulate.py         # 战斗模拟父进程侧：只起子进程，绝不 import game
  simulate_worker.py  # 战斗模拟子进程侧：在子进程里装配引擎、跑一场最小战斗
  selftest.py         # 只读自检（解析/校验/分组/key 往返），不写任何文件
  web/
    index.html        # 单页壳（含模拟预览抽屉）
    app.js            # 域切换 / 条目列表 / 按 kind 定制表单 / 保存 / 模拟预览
    schema_form.js    # JSON Schema → 表单渲染器
    style.css
  .workdir/<域>.json   # 写入目标（首次保存时自动创建）
```

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/domains` | 可编辑域列表（id/label/primary/flat/capabilities）+ 写入模式/数据来源 |
| GET | `/api/domain/<域>` | 条目列表（按 表/职业/分支 或 kind 分组 + 每条 key/id/name/kind） |
| GET | `/api/domain/<域>/<key>` | 单条完整 dict + 主 schema + 该条校验结果 + capabilities |
| POST | `/api/domain/<域>/<key>` | 收 `{"data": {...}}`，**先过 schema 校验**，合法才写工作副本 |
| GET | `/api/schema/<域>` | `<域>.schema.json` 原文（含 `primary` 指向的主 def） |
| POST | `/api/simulate` | **战斗模拟预览**：子进程跑引擎，返回伤害/日志/事件 |

域：`skills`（技能）/ `affixes`（词条）。

`<key>` 由 `~` 连接：

| 域 | key 形态 | 例子 |
|---|---|---|
| skills | `表~职业~技能` | `PLAYER_SKILLS~cls_zhan_shi~sk_hui_kan` |
| skills | `表~职业~lv~分支~技能` | `BRANCH_SKILLS~cls_zhan_shi~1~狂战士~怒斩` |
| affixes | `表~id` | `AFFIXES~bleed` |

## 战斗模拟预览（`POST /api/simulate`）

**入参**

```json
{
  "skill":    { "name": "挥砍", "kind": "物理", "lv": 1, "mp": 6,
                "exprs": ["atk*1 + 20 + player_lv*5.0 + skill_lv*12"], "desc": "…" },
  "attacker": { "class_name": "战士", "level": 20, "panel": {}, "effects": {} },
  "defender": { "def": 80, "mdef": 80, "level": 20, "hp": 10000000 },
  "skill_lv": 1,
  "seed": 1
}
```

* `skill` 必填，是**完整技能 dict**（可以是编辑器里还没保存的改动 —— 纯内存注入，不落盘）；
* `attacker` / `defender` 可省略：施法者默认按「职业面板 × 等级」聚合
  （`player_final_stats`，与命令层同口径），目标默认是一根不还手、不闪避的木桩；
* `skill_lv` 技能等级（决定取 `exprs` 第几条）；`seed` 随机种子（默认 1，让预览可复现）。

**出参**（成功）

```json
{"ok": true, "damage": 167, "self_heal": 0, "mp_used": 6,
 "hp": {"target_before": 10000000, "target_after": 9999833, ...},
 "logs": ["💥 木桩 受到 167 点伤害！", "✦ zhan_yi 1/10（+1）"],
 "events": [{"event": "skill_hit", "ctx": {"actor": "模拟者", "target": "木桩", "dmg": 167}}, ...],
 "attacker": {...}, "defender": {...}, "seed": 1, "warnings": []}
```

失败（如技能未过 schema）→ HTTP 422 + `{"ok": false, "message": "...", "validation": {...}}`；
引擎异常/超时 → HTTP 200 + `{"ok": false, "stage": "engine|timeout|crash", "message": "...", "traceback"/"stderr": "..."}`。

### 为什么必须用子进程（重要，别改成直接 import）

1. **循环导入陷阱**：`game.data ↔ game.core` 互相 import，编辑器主进程里 import game 会在
   错误时机拿到半初始化模块（`game/bootstrap.py` 装载顺序注释有详解）。
2. **装配有副作用**：`battle2.config.load_game_defaults()` 会把公式/面板/kind 常量 mount 进
   引擎**进程级全局** hook 面 —— 跑一次就污染编辑器进程。
3. **隔离与兜底**：引擎异常、死循环都能被子进程超时（默认 30s，可用 `DF_SIM_TIMEOUT` 调）
   掐死，编辑器本身永不崩。
4. **纪律一致**：`data_io` 只读 py 源码字面量、**绝不 import game**；模拟把「唯一碰 game 的
   地方」隔离到子进程 —— 主进程只做 `subprocess`。

实现要点：父进程（`simulate.py`）把 payload 从 stdin 喂给 `simulate_worker.py`，只认子进程
stdout 里的 `__DF_SIM_RESULT__<json>` marker 行（引擎/内容的零星 print 不会污染结果）；
子进程照 `tests/` 的 `sys.path` 补丁写法（qqbot 根 + 插件根 + astrbot shim），把
`GWEN_GAME_DB` 指到一个临时路径并 `GWEN_TEST_MODE=1` —— **模拟全程零 DB 访问**（实测不创建任何文件），
只是保险栓。

技能怎么被引擎用上：`Battle` 构造后把传入的技能 dict 直接挂进施法者的
`_skill_index`（`ActCtx.__post_init__` 在 `action=skill` 时从这里取 `info`），
所以**不需要改任何技能表**，`game/` 零改动。

## 按 kind 定制的表单（只改前端，不动 schema）

`app.js` 里的 `SKILL_PROFILES` / `AFFIX_PROFILES` 按 `kind`（技能）/ `trigger`（词条）
把表单字段分成两档：

* **高亮**（`.kind-hl`）：该 kind 最关心的字段（如 `物理` 高亮 `power/exprs/hits/mech…`）；
* **精简时隐藏**（`.kind-dim`，由「精简显示」勾选控制）：与该 kind 无关的字段（如 `被动` 隐藏 `mp/cast/cd`）。

档位条显示在表单顶部，可随时关掉「精简显示」回到完整表单。枚举取值本身仍来自 schema，
**没有在前端硬编码任何 schema 字段**（只是给已有字段加 class）。

## 数据读写策略（重要）

* **读**：`data_io.parse_source_tables()` 用 `ast` 抽 `game/data/<域>.py` 里的顶层表字面量。
  **不 import game 包** —— 避开循环导入与引擎副作用。
* **写**：只写 **JSON 工作副本** `editor/.workdir/<域>.json`，**绝不触碰 `game/data/*.py`**。
  整表回写源码会丢注释与手工排版（skills.py 里有大量 `# v162:` 之类注释），
  定点 AST 回写留待与主工程讨论后实施。
* 工作副本来由：首次保存时从 py 源码字面量种子化；之后列表/单条读取都走副本，
  UI 顶部会显示「数据来源：工作副本 / py 源文件」。
* **重置**：删掉 `editor/.workdir/`（或其中的某个域 json）即回到「以 py 源码为准」的只读态。
* 校验复用 `schema/validate.py`（有 jsonschema 用它，没有则内置最小校验器）。

## 深链

`http://127.0.0.1:8765/#<urlencode(key)>` 直接打开某条，例如
`#PLAYER_SKILLS~cls_zhan_shi~sk_hui_kan`。

## 新增一个域（零依赖，约 15 分钟）

以「物品域 items」为例，**只需两处改动 + 一次验证**：

1. **`editor/data_io.py` 的 `DOMAIN_DEFS` 加一条**（唯一的「域注册表」）：
   ```python
   "items": {
       "label":  "物品（items.py）",
       "schema": "item.schema.json",        # schema/ 下已有的文件
       "primary": "item",                   # schema $defs 里「一条数据」的 def 名
       "source":  "game/data/items.py",     # py 源文件（只读）
       "tables":  ("ITEMS",),               # 顶层表名（整表读写的单位）
       "copy":    "items.json",             # 工作副本文件名
       "flat":    True,                     # 扁平表（id → 条目）；三层嵌套表填 False
       "group":   "kind",                   # 列表分组策略："class"（表/职业/分支，技能域用）
                                            #              / "kind"（按条目 kind 字段分两组）
   },
   ```
   列表/单条读写、key 解析、schema 校验、`/api/schema/<域>` 全部由这张表驱动，
   **函数一行都不用改**（`server.py` 的 `DOMAINS` 也是从它派生的）。
2. **（可选）前端档位**：若想让表单按某字段高亮，在 `app.js` 的
   `SKILL_PROFILES`/`AFFIX_PROFILES` 旁加一组同构 profile（纯前端增强，不加也能用）。
3. **验证**：
   ```bash
   python editor/selftest.py                       # 全域网 py 字面量能解析、能过 schema
   python tests/test_editor_simulate.py            # 域泛化 + 模拟回归
   ```
   浏览器打开 → 新域应出现在顶部按钮里，列表/表单/保存/差异预览立即可用
   （保存只写 `editor/.workdir/<域>.json`，不改 py）。

> 目前只有**技能域**支持战斗模拟（`server.py` 的 `_simulate_supported`）；词条/物品等域若要
> 模拟，需要先想清楚「它怎么起一场战斗」，属后续迭代。

## 不做什么（边界）

* 不回写 py 源码；不提供删除条目接口；模拟为纯内存、不改盘；
* 不引入任何第三方依赖（前端无构建、后端纯 stdlib；模拟的子进程也只用 stdlib）。
