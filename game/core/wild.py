# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - wild.py —— **B13-L2 薄壳**（2026-09-14）

真源（**唯一实现**）= 内容包 `content/wild.py`（435 行，逐字搬自本文件的 333 行；
搬运改动面只有「宿主取件」一类，逐行见包内头注）。本文件现在只剩两件事：

    加载包（`package_apply()`，幂等）· 把 `game.core.wild` 这个名字**指向**包内那份实现

为什么必须「指向」（本线唯一硬要求）
------------------------------------
本模块的时间/天气三个名字被测试**直接赋新值**（monkeypatch 时钟），而包内实现按
模块全局读它们 —— 普通「从包内再导出」会让这些赋值打在壳上、实现读不到（= 测试假红）：

    tests/test_commands_wild_npc.py:39-41     W.current_period / current_season / today_weather
    tests/test_v1275_limited_wild.py:35-37    同上
    tests/test_v94_stamina.py:44              W.today_weather
    tests/test_v101_27_turn_in_period.py:41,52 W.current_period

指向后 `game.core.wild is content.wild`（同一模块对象）⇒ 赋值即改实现那份，测试语义逐字不变；
`W._get_meta` / `W._save_meta`（test_v1275_limited_wild.py:40-42 按名调用）等私有名同样在。

薄壳零实现：本文件不含任何逻辑。消费者清单与证据见 `overnight/W-B13-L2-wild-worlds.md`。
"""
import sys as _sys

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）

from content import wild as _impl                            # noqa: E402

_sys.modules[__name__] = _impl
