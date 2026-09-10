# -*- coding: utf-8 -*-
"""奥兰迪亚内容包（game/）。

S1（docs/ENGINE_CONTENT_SPLIT_PLAN.md §7）：本 `__init__` 只做一件事 —— 引入内容侧
引擎装配器 `game/bootstrap.py` 并调用 `install()`：

  * 登记 battle2 引擎的「默认配置装载器」（旧 `load_game_defaults()` 委托目标，R7）
  * 登记「hook 惰性装配器」（引擎首次访问未装配 hook 时自举内容装配）

必要性：本仓库并存 `game.*` 与 `data.plugins.dragonfall.game.*` 两套 import 路径
（同一份文件的两个模块树，plan §8-R2）——两棵树各自的 config 实例在各自包 init
时登记，互不串味。

方向：内容 → 引擎（合法）。引擎（`game/battle2/`）自身零内容 import，
门禁见 `tests/test_engine_no_content.py`。
"""
from . import bootstrap as _engine_bootstrap  # noqa: F401

_engine_bootstrap.install()
