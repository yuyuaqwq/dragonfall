# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年内容库 —— 薄聚合层（重构后）

数据层 → game/data/（纯静态表）
核心层 → game/core/（生成逻辑）
本文件保留 `import game.content as C` 兼容路径，全部符号聚合自上下两层。
"""
from .data import *  # noqa: F401,F403
from .core import *  # noqa: F401,F403
from .data import _INDEXES  # noqa: F401
from .core import pinyin_id, build_index, resolve, display  # noqa: F401

# ---- S1 引擎装配（docs/ENGINE_CONTENT_SPLIT_PLAN.md §7）：内容装载即装配引擎 ----
# battle2 引擎零内容 import；内容侧把数值公式/面板/技能查询/kind 常量 mount 进
# 引擎 config 注入面（方向：内容 → 引擎）。凡 import 内容者即完成 hook 装配，
# 与 S1 前（引擎直接 import 内容函数）等价；规则表仍由 load_game_defaults() 装载。
from . import bootstrap as _engine_bootstrap  # noqa: E402

_engine_bootstrap.mount_engine_hooks()
