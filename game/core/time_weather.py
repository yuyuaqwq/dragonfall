# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - time_weather.py —— **B13-L2 薄壳**（2026-09-14）

真源（**唯一实现**）= 内容包 `content/time_weather.py`（110 行，按本文件的 104 行**逐字原样**
搬入，零宿主取件、零改动）。本文件现在只剩两件事：

    加载包（`package_apply()`，幂等）· 把 `game.core.time_weather` 这个名字**指向**包内那份实现

为什么是「指向」而不是「从包内再导出 12 个名字」
------------------------------------------------
真源顶层名（12 个：`PERIODS` / `PERIOD_CN` / `SEASON_CN` / `WEATHER_CN` / `FOG_MAPS` /
`current_period` / `current_season` / `today_weather` / `time_weather_summary` / `_day_hash` /
`datetime` / `random`）与包内逐名相同。消费点：

    game/core/__init__.py:72   from .time_weather import (7 个名) → C.* 聚合面（『时间』面板）
    game/core/wild.py:22       current_period / current_season / today_weather（本线同名模块）
    game/core/events.py:10     current_season（B13-L3 线文件，本线不动）
    game/core/fishing.py:16    current_season
    tests/test_v95_30_npc_randomness.py:63  from game.core.time_weather import current_period
    tests/test_v184_loot_tiers.py:48        from …game.core.time_weather import current_season

指向后 `game.core.time_weather is content.time_weather`：名字集合与身份逐名相同
（`tests/test_commands_wild_npc.py:42` 会把 `TW.current_period` 取出来当 `current_period_orig`）。

薄壳零实现：本文件不含任何逻辑。消费者清单与证据见 `overnight/W-B13-L2-wild-worlds.md`。
"""
import sys as _sys

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）

from content import time_weather as _impl                    # noqa: E402

_sys.modules[__name__] = _impl
