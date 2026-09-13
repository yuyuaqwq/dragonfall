# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - timed_events.py —— **B13-L2 薄壳**（2026-09-14）

真源（**唯一实现**）= 内容包 `content/timed_events.py`（210 行，逐字搬自本文件的 143 行；
搬运改动面只有「宿主取件」一类：3 处函数内 `from .. import db` → 模块级 `db` 替身，
逐行见包内头注）。本文件现在只剩两件事：

    加载包（`package_apply()`，幂等）· 把 `game.core.timed_events` 这个名字**指向**包内那份实现

为什么是「指向」而不是「从包内再导出 13 个名字」
------------------------------------------------
真源顶层名（13 个，含模块级状态 `_timers`（`LazyTimers` 实例，注册表 + 惰性过期缓存）
与 `_PLAYER_KEY` / `_load` / `_save` / `_remove_whole`）与包内逐名相同；消费点：

    game/core/__init__.py:83        from .timed_events import (6 个公开名) → C.* 聚合面
    game/commands/base.py:245       from ..core import timed_events as _te → _te.refresh_timed
    game/services/profession.py:38  同上（挂机倒计时）
    tests/test_v1275_timed_engine.py / test_v1275_limited_wild.py / test_v1275_prof_wait(_expire)
    game/core/wild.py:23            register_timed / set_timed（本线同名模块；包内 wild 已直取包内）

指向后 `game.core.timed_events is content.timed_events` ⇒ `_timers`（事件类型注册表）全局
**只有一份**：`wild.py` 注册的 `wild_npc` 类型与命令层 `refresh_timed` 看到的是同一个实例
（若各自持一份副本，过期回调会静默丢失）。名字集合与身份逐名相同。

薄壳零实现：本文件不含任何逻辑。消费者清单与证据见 `overnight/W-B13-L2-wild-worlds.md`。
"""
import sys as _sys

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）

from content import timed_events as _impl                    # noqa: E402

_sys.modules[__name__] = _impl
