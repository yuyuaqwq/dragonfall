# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年存储层 - props_use：**委托薄壳**（B17 存档层归包）。

实现（表结构 + CRUD 逐字）已归内容包：`framework/games/orlandia/content/persistence/props_use.py`。
本文件只做一件事：把包内实现**同名同签名**转发出来 —— 全宿主 `from .. import store as db` /
`db.<fn>` / `from ..store.props_use import <名>` 的调用点**一行未改**。

判据：`overnight/check_host_boundary.py --check`（宿主零逻辑边界）；行为证据：`overnight/W-B17.md`
（存档快照 before/after 逐字节相同 + 每步全库 dump）。
"""
from content.persistence.props_use import *  # noqa: F401,F403
from content.persistence.props_use import __all__ as __all__  # noqa: F401
from .connection import _lock  # noqa: F401  （保持与改造前同一实例：真 RLock，非句柄代理）
