# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - worlds.py —— **B13-L2 薄壳**（2026-09-14）

真源（**唯一实现**）= 内容包 `content/worlds.py`（356 行，逐字搬自本文件的 286 行；
搬运改动面只有「宿主取件」一类：`store.world` / `store.connection` / `data` 三张表 → 宿主句柄，
逐行见包内头注）。本文件现在只剩两件事：

    加载包（`package_apply()`，幂等）· 把 `game.core.worlds` 这个名字**指向**包内那份实现

为什么是「指向」而不是「从包内再导出 23 个名字」
------------------------------------------------
真源顶层名（23 个，含 `instance_worlds` 这个**可变内存态 dict**、`EVENT_STATE_PREFIX`、
`_restore_from_db` / `_persist` / `_json_ready`）与包内逐名相同；消费点按**模块属性 + 身份**取用：

    game/core/__init__.py:130      from .worlds import (…, instance_worlds)  → C.* 聚合面
    game/core/position.py:17/72/83 get_instance_world（副本图解析；:17 只在 TYPE_CHECKING 里）
    game/store/battle_state.py:119  destroy_instance_world（退本回收）
    game/commands/base.py:260       cleanup_stale_instances（任意指令惰性回收）
    main.py:271                     cleanup_stale_instances（启动兜底）
    tests/test_v141_instance_world.py / tests/test_v137_dungeon.py  经 C 聚合面调用

指向后 `game.core.worlds is content.worlds` ⇒ `instance_worlds` 是**同一份 dict**（进程内大陆
实例表只有一份，重启恢复/回收逻辑零改动），名字集合与身份逐名相同。

薄壳零实现：本文件不含任何逻辑。消费者清单与证据见 `overnight/W-B13-L2-wild-worlds.md`。
"""
import sys as _sys

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）

from content import worlds as _impl                          # noqa: E402

_sys.modules[__name__] = _impl
