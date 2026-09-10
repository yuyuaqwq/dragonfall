# -*- coding: utf-8 -*-
"""兼容 shim（S3 通用件归位）：本体已迁 `game/battle2/support/formation.py`。

旧路径 import 保持可用（docs/ENGINE_CONTENT_SPLIT_PLAN.md §7-S3）：
`from ..core import formation as FM` / `from game.core.formation import X`。

S9 收口时删（§7-S9）。
"""
try:
    from ..battle2.support.formation import *  # noqa: F401,F403
except ImportError:  # 独立文件加载（无包上下文）
    import importlib.util as _ilu
    import os as _os

    _p = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
        "battle2", "support", "formation.py")
    _spec = _ilu.spec_from_file_location("_b2support_formation", _p)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})
    del _ilu, _os, _p, _spec, _mod
