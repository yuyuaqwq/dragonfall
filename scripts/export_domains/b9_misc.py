# -*- coding: utf-8 -*-
"""B9 L9（misc 线）域插件 —— **本线不新增任何域**（`DOMAINS = {}`，显式留白 + 理由留档）。

为什么留白（逐条核实，2026-09-13）
----------------------------------
契约见本目录 `README.md`：一个域 = 「真源表 → 包内 JSON」。misc 线（宿主
`game/commands/misc.py` 的 5 个命令：帮助 / 游戏提示 / 签到 / 成就 / 意见）**没有任何一张
属于自己的真源表**，它的数据面 100% 已被既有域覆盖，文案与规则都是内容侧字面量：

1. **数据读口全部已有域**
   - 签到幸运符 / 成就奖励物品名 → `items` 域（`content/data/items.json`，900 条；宿主
     `C.ITEMS`/`C.MATERIALS`/`C.resolve("materials", …)` 的等价读口 = 包内
     `content/misc_cmds.py:item_name()` / `material_key()`，对拍见 `overnight/b9_l9_verify.py`）。
   - 成就表 → `achievements` 域（119 条，既有）。
2. **文案是内容侧文本字面量**：帮助面板 11 份 + 新手指引 1 份（共 12 份、约 12.5 KB）过去是
   `commands/misc.py` 的类属性字面量；本批**逐字节搬进包内模块** `content/misc_cmds.py`
   （`HELP_PANELS` / `GAME_TIP`），源码字面量 → 包内模块，没有 JSON 形态的真源表可导出。
   ⚠️ 它们**不能**进 `texts` 域：`tests/test_texts_table.py:651` 把文案表的 category 取值
   钉死为 6 个已知分类 + `WIRED` 只认 9 个已迁移接线文件 —— 加一域会当场报红（不是本线能改的
   测试）。**登记为缺口**：帮助/指引文案的「域化」归属文案表批次（texts），不属本线。
3. **数值配置不属本线**：`SIGNIN_CONFIG`（`game/data/signin_config.py`）是 `*_config.py` 常量
   模块 —— 按 B9 域归属铁律归 **L7**（本线只以参数注入，不复制、不建域）。
4. **频控/长度规则**（30 秒、≤200 字）与 4 条回执文案：内容规则字面量，进包内模块
   （`content/misc_cmds.py:FEEDBACK_CD_SECONDS/FEEDBACK_MAX_LEN/MSG_*`）—— 若建域会与包内常量
   形成**第二份真源**（本项目最忌的双源），故不建。

若父任务要求本线必须落一个域，最小、正当的候选（**本批不做，理由见下**）
--------------------------------------------------------------------
- `achievement_order`：`achievements` 域落盘按字典序（`sort_table`），**丢了源列表序**
  （`game/data/achievements.py:25 ACHIEVEMENTS` 是 list）—— 而『成就 <分类>』面板的逐条渲染序
  就是源序（逐字节等价硬指标）。
  **本批不建域**的原因：① 该缺口属成就域的导出器（`export_domains/shop_econ.py:derive_achievements`
  = 别人线的文件，禁改）；② 再建一个「id → 序号」的域 = 同一批 id 出现两份（新增双源面）；
  ③ 现状以「宿主把 `C.ACHIEVEMENTS`（源序）作为参数交给包」解决，零复制（与 B8.2 线2
  `commands/collection.py` 的「宿主给集合、包内判定」同款）。长期解在报告 §缺口②已写。

本文件保留为空插件而非删除：域插件目录是「本线声明面」，空声明 = 显式留档「本线无域」，
比一个缺席的文件更难被误读成「漏了」；且插件加载器对 `DOMAINS = {}` 零副作用
（`scripts/export_game_package.py:load_domain_plugins` 只并入键值，不校验非空）。
"""
from _helpers import import_game_data, sort_table, as_table  # noqa: F401  （留作本线后续域备用）

DOMAINS = {}
