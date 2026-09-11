# -*- coding: utf-8 -*-
"""奥兰迪亚内容包（game/）。

S1（docs/ENGINE_CONTENT_SPLIT_PLAN.md §7）：本 `__init__` 只做一件事 —— 引入内容侧
引擎装配器 `game/bootstrap.py` 并调用 `install()`：

  * 登记 battle2 引擎的「默认配置装载器」（旧 `load_game_defaults()` 委托目标，R7）
  * 登记「hook 惰性装配器」（引擎首次访问未装配 hook 时自举内容装配）

必要性：本仓库并存 `game.*` 与 `data.plugins.dragonfall.game.*` 两套 import 路径
（同一份文件的两个模块树，plan §8-R2）——两棵树各自的 config 实例在各自包 init
时登记，互不串味。

方向：内容 → 引擎（合法）。引擎（`framework/battle2/`）自身零内容 import，
门禁见 `tests/test_engine_no_content.py`。
"""
import os as _os
import sys as _sys

# 引擎框架包接线（S8 物理分离）：引擎已迁独立仓库，本仓以 git submodule 接入
# `framework/`（内含包 `battle2/`）。必须在任何 `import battle2` 之前把框架根
# 加进 sys.path —— 本包 `__init__` 是最靠前的可靠执行点（游戏运行时 `from .game
# import …` 必经此处；测试侧另有 tests/conftest.py 同款接线）。
# 方向铁律：内容 → 引擎；框架侧零游戏知识（门禁：framework/tests/test_engine_purity.py）。
_FRAMEWORK_DIR = _os.path.normpath(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "framework"))
if _os.path.isdir(_FRAMEWORK_DIR) and _FRAMEWORK_DIR not in _sys.path:
    _sys.path.insert(0, _FRAMEWORK_DIR)

from . import bootstrap as _engine_bootstrap  # noqa: E402,F401

_engine_bootstrap.install()
