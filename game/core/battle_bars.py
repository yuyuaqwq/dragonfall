# -*- coding: utf-8 -*-
"""兼容 shim（S3 通用件归位）：本体已迁 `game/battle2/support/battle_bars.py`。

旧路径 import 保持可用（docs/ENGINE_CONTENT_SPLIT_PLAN.md §7-S3）：
`from ..core.battle_bars import bar_gain, …` / `from game.core.battle_bars import X`。
下划线名 `_state_prefix` 不随 `import *` 导出（commands/combat、services/
battle2_bar_procs、tests/test_numeric_bar_decay 直接用），故显式再导出。

S9 收口时删（§7-S9）。
"""
try:
    from ..battle2.support.battle_bars import *  # noqa: F401,F403
    from ..battle2.support.battle_bars import _state_prefix  # noqa: F401
except ImportError:  # 独立文件加载（无包上下文）
    import importlib.util as _ilu
    import os as _os

    _p = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
        "battle2", "support", "battle_bars.py")
    _spec = _ilu.spec_from_file_location("_b2support_battle_bars", _p)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})
    del _ilu, _os, _p, _spec, _mod
