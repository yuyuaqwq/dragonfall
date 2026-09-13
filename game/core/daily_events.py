# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - daily_events.py —— **B13-L2 薄壳**（2026-09-14）

真源（**唯一实现**）= 内容包 `content/daily_events.py`（134 行，逐字搬自本文件的 52 行；
搬运改动面只有「宿主取件」一类：模块级 `from ..data.daily_events import DAILY_MAP_EVENTS`
→ 宿主句柄 `_host_attr("data.daily_events", "DAILY_MAP_EVENTS")`（域未进包），逐行见包内头注）。
本文件现在只剩两件事：

    加载包（`package_apply()`，幂等）· 把 `game.core.daily_events` 这个名字**指向**包内那份实现

为什么是「指向」而不是「从包内再导出 5 个名字」
------------------------------------------------
真源顶层名（5 个：`datetime` / `DAILY_MAP_EVENTS` / `_day_hash` / `today_map_event` /
`today_event_effects`）与包内逐名相同；`tests/test_daily_events.py:20` 直接
`from …game.core.daily_events import (today_map_event, today_event_effects, _day_hash)`
（**连私有名一起**），消费点还有 `game/core/__init__.py:113`（→ `C.today_map_event`，
被 `commands/combat.py explore()` / `commands/world.py map_view()` 消费）。
指向后 `game.core.daily_events is content.daily_events`：名字集合与身份逐名相同。

薄壳零实现：本文件不含任何逻辑。消费者清单与证据见 `overnight/W-B13-L2-wild-worlds.md`。
"""
import sys as _sys

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）

from content import daily_events as _impl                    # noqa: E402

_sys.modules[__name__] = _impl
