# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心 - portals.py —— B13-L5 **薄壳**（2026-09-14）

`portal_cost`（传送费用，纯函数）的实现正文已**逐字搬进内容包** `content/portals.py`
（包内零宿主依赖、零数据读口 —— 真源本来就只用传进来的 dict）。
本文件只剩两件事：**加载包** · **模块别名**（`sys.modules[__name__] = 包内模块`）。

别名之后 `game.core.portals` 与 `content.portals` **是同一个模块对象**：
`from .portals import portal_cost`（`game/core/__init__.py:103`）与聚合层 `C.portal_cost`
（`tests/test_core_world.py:31` 用 `getattr(C, "portal_cost")`）取到的都是包内实现本体。
"""
import sys as _sys

from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                  # 本进程唯一包加载口（幂等）

from content import portals as _impl                         # noqa: E402  包内实现（真源）

_sys.modules[__name__] = _impl                               # 模块别名：壳与实现同体
