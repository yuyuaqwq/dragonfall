# 奥兰迪亚 · 配置编辑器（MVP：技能域）

零第三方依赖的可视化配置编辑器：**stdlib Python 后端** + **原生 HTML/CSS/JS 前端**。
路线图阶段 2.2 的落地（技术方案见仓库根 `EDITOR_SPEC.md`）。

```bash
python editor/server.py            # 默认 http://127.0.0.1:8765
python editor/server.py --port 9000
python editor/server.py --host 0.0.0.0   # 局域网可访问（谨慎）
```

任何装了 Python 的机器都能直接跑，**不需要 Node / npm / pip install**。

## 目录

```
editor/
  server.py          # stdlib http.server：静态文件 + /api/domain/*
  data_io.py         # py → JSON 读取（ast 字面量抽取）+ 工作副本写入 + schema 校验
  selftest.py        # 只读自检（解析/校验/分组），不写任何文件
  web/
    index.html       # 单页壳
    app.js           # 域列表 / 技能列表 / 载入 / 保存 / 差异预览
    schema_form.js   # JSON Schema → 表单渲染器
    style.css
  .workdir/skills.json   # 写入目标（首次保存时自动创建）
```

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/domains` | 可编辑域列表 + 写入模式/数据来源信息 |
| GET | `/api/domain/skills` | 技能列表（按 表/职业/分支 分组 + 每条 key/name/kind/lv） |
| GET | `/api/domain/skills/<key>` | 单条完整 dict + skill schema + 该条校验结果 |
| POST | `/api/domain/skills/<key>` | 收 `{"data": {...}}`，**先过 schema 校验**，合法才写盘 |
| GET | `/api/schema/skills` | `schema/skill.schema.json` 原文 |

`<key>` 由 `~` 连接：`PLAYER_SKILLS~cls_zhan_shi~sk_hui_kan`、
`BRANCH_SKILLS~cls_zhan_shi~1~狂战士~怒斩`、`TUTOR_SKILLS~cls_fa_shi~sk_x`。

## 数据读写策略（重要）

* **读**：`data_io.parse_source_tables()` 用 `ast` 抽 `game/data/skills.py` 里的
  `PLAYER_SKILLS` / `BRANCH_SKILLS` / `TUTOR_SKILLS` 字面量。**不 import game 包**
  —— 避开循环导入与引擎副作用（`game/battle2` 正在并行重构）。
* **写**：MVP 只写 **JSON 工作副本** `editor/.workdir/skills.json`，
  **绝不触碰 `game/data/skills.py`**。整表回写源码会丢注释与手工排版
  （skills.py 里有大量 `# v162:` 之类注释），定点 AST 回写留待与主工程讨论后实施。
* 工作副本来由：首次保存时从 py 源码字面量种子化；之后列表/单条读取都走副本，
  UI 顶部会显示「数据来源：工作副本 / py 源文件」。
* **重置**：删掉 `editor/.workdir/`（或其中的 `skills.json`）即回到「以 py 源码为准」的只读态。
  注意：副本存在期间 py 源码的后续改动**不会**自动同步进编辑器。
* 校验复用 `schema/validate.py`（有 jsonschema 用它，没有则内置最小校验器）。

## 深链

`http://127.0.0.1:8765/#<urlencode(key)>` 直接打开某条技能，例如
`#PLAYER_SKILLS~cls_zhan_shi~sk_hui_kan`。

## 表单渲染（schema 驱动）

```
string + enum   → <select>
string          → <input type=text>
number/integer  → <input type=number>（min/max/step）
boolean         → <checkbox>
object          → 递归分组（properties）
object 仅 additionalProperties → 键值行编辑器（res_cost 这种）
array（标量项） → 可增删行；复杂项 → JSON 兜底
anyOf/const     → 联合输入框 / 常量显示
description     → 字段下方灰字帮助
```
另有「原始 JSON」视图（兜底，适合 `formula` 这类复杂嵌套）与「差异预览」。

## 新增一个域（后续）

1. `data_io.py` 加该表的 ast 读取 + 校验入口；
2. `server.py` 的 `DOMAINS` / `DOMAIN_LABELS` 加一项，`_api_get` 分流；
3. 前端 `app.js` 的域切换已通用（走同一套 API 形状）。

## 不做什么（MVP 边界）

* 不回写 py 源码；不提供删除条目接口；不做战斗模拟预览（P2）；
* 不引入任何第三方依赖（前端无构建、后端纯 stdlib）。
