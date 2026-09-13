# 《剑与魔法》项目开发规范（DEVELOPMENT.md）

> 本文件是项目的**开发总纲**——给所有参与本项目的开发者/AI 助手读的第一份文档。
> 详细操作手册见 Hermes 技能 `dragonfall-game`（SKILL.md + references/），本文件是规范层，技能是操作层。
> 最后更新：2026-08-10（v103 系列 B1-B3 完成后定稿）

---

## 0. 项目是什么

AstrBot QQ 机器人文字 RPG《剑与魔法》（dragonfall 插件）。玩家通过 QQ 群/私聊指令游玩。
插件路径：`C:\Users\yuyu\qqbot\data\plugins\dragonfall\`。
数据文件：主库 `game/game_data.db`（根目录 `game_data.db` 是 0 字节残壳勿用）；测试库 `test_game_data.db`。

---

## 1. 架构铁律（v47 重构定稿，不可回退）

```
data（纯数据 dict） ← core（纯逻辑，无 IO 不碰 DB/QQ） ← store（Repository，唯一碰 SQLite）
← commands（Mixin 命令层，只管 QQ 交互） ← main.py（装配）
```

- **依赖单向**：data ← core ← store ← commands ← main，禁止反向 import
- **core 层不要 import db**（循环 import 先炸）；core 模块若被 data/_assembly 触达，db 必须函数内延迟导入
- `content.py` 是薄聚合层（`from .data import *` + `from .core import *`），**core/__init__.py 新增常量/函数必须显式加入导出列表**（v103.3 踩过：漏导出 → AttributeError）
- store 层引用常量用 `from .. import content as C`（players.py 先例）

## 2. 数据与 ID 规范（v46/v48 定稿）

- **存档只存 ID，内存用中文名，落库转 ID**：`C.resolve(table, 中文或ID)` → ID；`C.display(table, id)` → 中文
- 数据表 key 一律 ID（`mat_`/`sk_`/`cls_`/`rec_`/`set_`），值带 `name` 字段做显示名
- **改任何"名字"（物品名/地图名/职业名）前先 `grep name` 全项目**——改名断引用是最高频事故
- 派生表（MAP_BY_ID/MAP_CONNECTIONS 等）在 `data/_assembly.py` 构建，**加新数据必须同步检查派生表**（MINE_SPOTS/CAMP_SPOTS/PORTALS/ENHANCE_SMITH_MAPS/PROPERTIES/create_player 默认地图/回城点清单）

## 3. 可扩展性规范（v98-v103 系列成果，新代码必须遵守）

### 3.1 魔法字符串/数字一律进 `core/constants.py`
- 字符串比较用 key/常量：地图 type（`C.MAP_TYPE_TOWN`）、职业 ID（`C.CLASS_NOVICE`）、物品 type（`C.ITEM_TYPE_*`）
- 概率、等级阈值、容量、奖励量抽常量（`FLEE_CHANCE`/`EVOLVE_LEVELS`/`DEFAULT_MAX_MP`/`PVP_TIMEOUT_SEC`…）
- **加常量后必须同步 core/__init__.py 导出**（v103.3 教训）
- 判据：改数值/文案 = 只动 data 或 constants，不碰逻辑代码

### 3.2 加内容 = 加数据，加行为 = 注册表
- 新物品/怪物/地图/配方/技能 = data 层加 dict，零代码
- 新"类型/机制"（新事件类型/新效果/新条件）= `TYPE_REGISTRY` 注册一个函数（~20 行），**禁止新增 if-elif 分发链**
- 已有注册表：battle_mech/battle_conds/affix_effects/achievement_conds/title_templates/race_traits/dialogue_conds/world_event_templates/item_detail_renderers…

### 3.3 动态 SQL 必须过白名单（v103.1）
- `update_player`/`pet_update`/`bump_stats`/`add_prof_exp` 的字段名必须 ∈ 表列白名单（PLAYER_FIELDS/PET_FIELDS/STAT_FIELDS/PROF_FIELDS）
- **加新列（含 ALTER 补列）必须同步加进白名单**，否则运行时 ValueError
- 注销清理表名只能来自 DELETE_TABLES 常量

### 3.4 超大函数拆分原则（v103.5-103.7 定稿）
- **拆**：巨型 if-elif 分发（kind 分支）、纯数据构建段（stages/state dict）、建表 SQL
- **不拆**：async generator yield 流程（命令层）、线性结算（10+ 变量互传）、回合状态机——硬拆需 async for 转发或巨型签名，可读性不升反降
- 判据：提取后参数 ≤6 且无 yield 转发，才值得拆

## 4. 重构铁律（v98 起零例外）

1. **行为零变化**：重构不改数值/文案/概率（明确 bug 修复除外，必须标注"正向修复"）
2. **先 commit 再验证**：每阶段独立 commit，信息标注 `vXX.Y`
3. **单测先行，全量最后后台跑**：改完 → py_compile + 相关单测全绿 → commit；**所有阶段弄完才跑全量**（鱼鱼嫌慢，别每个阶段都跑）
4. **全量跑时绝不动源文件**（中间态误判），全量/单测不并发（共用 test_game_data.db 互相污染）
5. 数据表下沉后必须**全局 grep 旧引用（含 tests/）**再提交（v102.4/102.6/102.7 教训）
6. 批量删行永远**从后往前删**（v102.4 del 行号偏移教训）

## 5. 测试规范

- 单测：`"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe" tests/test_xxx.py`（AstrBot uv python，系统 python 无 pypinyin）
- 全量：`python scripts/run_all_tests.py`（v117.5 起默认并行 + shim astrbot 替身：按核数自适应 4~16 路、每文件独立私有库 `tests/.run_all_workers/`、注入 `tests/shim_astrbot/` 行为等价替身；实测 149 文件 **~27s**，详见 `docs/TEST_SPEEDUP.md`）；`--serial` 恢复旧的纯串行共享库行为；`--skip=test_xxx.py` 跳过已知坏测试（重构过渡期用）；`--real-astrbot`/`GWEN_NO_SHIMMED_ASTRBOT=1` 退回真实 astrbot（对照验证 shim 用）；**不要用 pytest 跑**（旧式脚本 sys.exit 会 INTERNALERROR）
- 硬编码共享 `test_game_data.db` 的文件（如 test_v101_28_food_hot.py）自动进「串行槽」先跑，新测试**禁止直接赋值 `GWEN_GAME_DB` 指向共享库**（要用隔离库就 setdefault 自己的私有库，或直接用 conftest 默认）
- **测试必须确定性**：
  - 概率/随机逻辑必须 `random.seed()` 固定（撞怪/彩蛋/掉落）
  - **禁止真实时钟依赖**：规则引擎 `_is_time` 会读真实时间（v103.2 教训：深夜跑全量触发 deep_night 幽灵彩蛋 → 误判失败）——测试里 patch 固定时段
  - 玩家等级要提到威慑线（`_travel_ambush` diff≤-5 永不撞怪），否则跨图 move 18% 概率撞怪随机失败（v103.4 教训）
- 断言数字（成就数/NPC 数/表数）改数据后必须同步 grep 检查硬编码计数

### 5.5 平台解耦架构（v117.5 起，新增代码必须遵守）

游戏核心已独立于 astrbot（详见 `docs/TEST_SPEEDUP.md` §2.5）：

- **命令装饰器一律从 `game/commands/_platform.py` import**（`from ._platform import filter`，
  语法仍是 `@filter.regex(...)`）——**禁止** `from astrbot.api.event import filter`。
  `_platform` 装饰器自动双注册（核心注册表 + 真实 astrbot 注册表），生产行为不变。
- **回复构造用核心数据类**：`MessageChain / Plain / Node / Nodes` 从 `._platform` import；
  生产环境由 `main.py` 的 `AstrMain` 壳 context 翻译代理转成 astrbot 类型。
- **只有 `main.py` 允许 import astrbot**（壳 `AstrMain(star.Star, Main)`，astrbot 固定
  入口模块）；game/ 与 tests/ 禁止 import astrbot（测试命中 `tests/shim_astrbot/` 替身）。
- **迁移到其他平台** = 把 `game/` + `main.Main` 搬走，照 `AstrMain` 写目标平台薄壳：
  提供事件协议（get_message_str/sender_id/group_id/plain_result/stop_event/send）、
  把核心注册表（`_platform.star_handlers_registry`）翻译成目标平台命令系统。

## 6. Git 规范

- 提交信息格式：`vXX.Y 内容描述（做了什么+验证结果）`
- 大改打版本号（v101/v102/v103…），测试文件 `test_vXX_*.py` 或 `test_<功能域>.py`
- 迁移函数放 main.py + event_state 标记幂等；**改表结构检查 5 处**（CREATE/ALTER/update_player 白名单/get_player 解析/迁移 defaults）
- 不要提交 playtest 产物、临时脚本输出（`.bak_*` 用完即删）

### ⚠️ 策划案同步铁律（2026-08-12 拍板；**2026-09-13 因清场变更**）

**原状（2026-08-12 起）**：任何涉及设计/数值/新内容的代码改动，提交 git 之前必须先同步 `design/new_world/` 对应章节（独立 git 仓库，位于插件目录 `....\dragonfall\design\new_world`，代码仓 .gitignore 已排除），与 git commit 同级必做，禁止只提交代码。

**★ 2026-09-13 变更（B1 清场，鱼鱼拍板 A 案）**：整个 `design/new_world/`（849 文件 / 10.0 MB，其中嵌套独立 `.git` 独占 7.2 MB）已**移出仓**（移出 ≠ 删除）。
- 原因：嵌套独立 `.git` 混进插件目录会让代码仓状态混乱（`docs/ENGINE_CONTENT_SPLIT_PLAN.md` R10）
- **新家（2026-09-13 定案）**：`C:\Users\yuyu\dragonfall-designer\` —— 与 `framework-engine` 同级的**外挂兄弟仓**，保留它自己的 git 历史与远端 `git@github.com:yuyuaqwq/dragonfall-designer.git`；设计稿今后在那里维护、独立提交（提交信息照旧写设计依据）
- B1 移出时的中转站 `...\workspace\_retired\20260913\design\new_world\` 已迁空，只留 `design/MOVED_TO.txt` 指针；`_retired\20260913\MANIFEST.json` 仍是这次移出的逐文件 sha256 凭据
- 仓内留了跳转指针 `design/README.md`：源码注释里所有 `design/new_world/...` 写法都按它跳（~10 处注释沿用旧写法，未逐条改）
- **「强制双仓分别提交」不再适用**（本铁律退掉的就是这一步）。改数值/新内容/机制时：**可选**去 `dragonfall-designer` 更新设计稿，但**必须在代码提交说明里写清设计依据并知会鱼鱼**；纯 bug 修复 / 纯文案错别字 / 纯重构不涉及。
- 宿主旧编辑器 `editor/`（技能/词条 2 域 MVP）同批退役 → `_retired\20260913\editor\`；现行编辑器 = `framework-engine/editor`（24 域，端口 8766）。

**判定（沿用）**：改到数值·新内容·机制 → 必同步；纯 bug 修复、纯文案错别字、纯重构不动设计 → 可不同步但拿不准就同步。
**历史教训（沿用）**：v101.25h3 只更新 `docs/NUMERIC_DESIGN.md` 被鱼鱼抓包（"这种策划设计类的文档要放在策划案里，不要在代码文档里"）；`docs/NUMERIC_DESIGN.md` 只是实现记录，不承载设计意图。
**本铁律四处常驻**：本文件 §6 / `dragonfall-game` SKILL.md / Hermes MEMORY.md / playtest cron prompt —— **变更后四处都要跟着改**（2026-09-13 已同步）。

## 7. 高频工具坑（全部实战踩过）

| 坑 | 规避 |
|---|---|
| patch 工具 fuzzy match 吞相邻函数/改缩进/匹配相似代码块 | 改完 `grep -c "def 函数名"` 必须==1；大段代码用 python read-replace-write 脚本（带替换计数验证） |
| patch 写 markdown 把引号写成 `\"` 字面转义 | new_string 直接写普通引号；改完扫反斜杠 |
| patch 改含正则文件（_registry.py）反斜杠双写 | 用 python raw 字符串精确替换，patch 后 cat -A 验证 |
| bash heredoc 含 `&` 被误判后台符 / 引号转义层级 | 脚本写成 .py 文件再跑 |
| 生成器反复运行读到自己产物（数据翻倍） | 从 .bak 干净结构读，或原子替换 |
| Windows 路径给 patch/write_file 必须原生 `C:\...` | 别用 MSYS `/c/...` |
| `sk_` 前缀被 Hermes 安全过滤器打码成 `***` | 写入文件再 cat 验证 |
| 测试库路径不能用 `/tmp` | 用 `os.path.abspath()` 相对插件目录 |
| 全量跑着时跑单测 = 库污染随机失败 | 严格串行 |

## 8. 文档规范

- **一系统一文档**：新系统落地 = 独立文档记录（策划案 → 实现 → 坑），放 docs/ 或 references/
- **版本计划文档**：每轮重构写 `docs/EXTENSIBILITY_REFACTOR_PLAN_vXX.md`（问题清单/方案/验收/踩坑），**做完必须更新**（v102 没写文档被鱼鱼抓包）
- **踩坑记录必写**：行号偏移/旧引用残留/时间依赖这类教训，写进版本文档或技能 references，后人必读
- 升级/迁移要写文档再动代码（鱼鱼："一系统一文档、同功能不分散"）

## 9. 遗留清单（2026-08-10 审计后）

- 🔴 **D 维度重复语句块**（审计重跑发现，未处理）：`world.py:453 map_view()` 重复块 ×2（12 行）、`core/rule_engine.py:78 _match_cond()` 重复块 ×2（16 行）
- 🟡 命令层 145 个 `@filter.regex` 分散注册 + misc.py 帮助手写（**明确不改**：AstrBot 框架惯例）
- 🟢 未来可做：帮助面板/命令表自动同步（P6 远期）

## 10. 上线流程（简短版）

1. 相关单测全绿 + git commit
2. 全量后台跑（`run_all_tests.py`，notify_on_complete），期间不动源文件
3. 重启 AstrBot：`netstat -ano | grep 6199` 找实际 PID → `taskkill //PID <pid> //F` → `rm astrbot.lock` → uv 环境 `python -m astrbot.cli run`（background）
4. 等日志 `Loading plugin dragonfall` + 适配器连接
