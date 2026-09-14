# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年内容库 —— 薄聚合层（★ B14 开关版 · 2026-09-14）

**数据层 `game/data/` 已删**（74,707 行 / 87 个 `.py`；只留 `command_specs.json` / `text_specs.json` /
`tlogs.json` / `t2i_templates/` 四项资产）。全部内容（域 JSON + 逻辑实现 + 聚合门面）现在住在内容包
`framework/games/orlandia/`（框架仓 `games/orlandia`，提交 `03affc2`）。

本文件只剩三件事（`C.<名>` 语义与改造前**逐名相同**）：
  ① 聚合宿主核心层：`from .core import *`（`game/core/*` 全是薄壳 → 包内 `content/*` 实现）
  ② 聚合**包内门面**替代原 `from .data import *`：`content/catalog_legacy`（丢名再导出面）
     + `content/catalog_{b143,core,items,life,quests,rules,space}`（66+6 域 + 长尾门面）
  ③ 装载引擎 hook 与名字索引：`bootstrap.mount_engine_hooks()` · `_INDEXES`（包内自建的那只 dict）

等价性证据（真源级/开关演习）：
  * `overnight/b14_catalog_gate.py` —— 门面逐名 vs 宿主旧表：值 / 类型 / **dict 键序** 全等（不等 0）
  * `overnight/w11d_switch_drill.py` —— 沙盒「删 87 个 .py + 本文件的接法」：宿主模块 import 23/23 ·
    宿主代码引用的 51 个 `C.<大写名>` **缺 0**
  * 开关后复跑：`test_v87_command_matrix 242/0` · `test_v104_commands_system 314/0` ·
    `run_numeric_tests ✅18 ❌0` · `verify_package_coverage --check 失败 0`
"""
from .core import *  # noqa: F401,F403
from .core import pinyin_id, build_index, resolve, display  # noqa: F401

# ---- 包内门面聚合（替代原 `from .data import *`）----
from content.catalog_legacy import *  # noqa: F401,F403
from content import (catalog_b143, catalog_core, catalog_items, catalog_life,  # noqa: F401
                     catalog_quests, catalog_rules, catalog_space, index as _idx)

for _m in (catalog_b143, catalog_core, catalog_items, catalog_life, catalog_quests,
           catalog_rules, catalog_space):
    for _n in dir(_m):
        if _n.startswith("__"):
            continue
        if _n.isupper() or callable(getattr(_m, _n)):
            # 与改造前同序：`.core` 先落、门面后落 → 同名时 core 胜（setdefault 保这一点）
            globals().setdefault(_n, getattr(_m, _n))
del _m, _n

# 名字索引：改造前 `from .data import _INDEXES`（宿主运行期建的那只 dict）→ 现在 = 包内自建同一只
_INDEXES = _idx._indexes()  # noqa: F841

from . import bootstrap as _engine_bootstrap  # noqa: E402

_engine_bootstrap.mount_engine_hooks()
