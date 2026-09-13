# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - encounter.py —— **B13-L2 薄壳**（2026-09-14）

真源（**唯一实现**）= 内容包 `content/encounter.py`（35 行，按本文件的 29 行**逐字原样**搬入，
零宿主取件、零改动）。本文件现在只剩两件事：

    加载包（`package_apply()`，幂等）· 把 `game.core.encounter` 这个名字**指向**包内那份实现

为什么是「指向」而不是「从包内再导出 3 个名字」
------------------------------------------------
真源顶层名（3 个：`Optional` / `annotations` / `encounter_chance`）与包内逐名相同；
唯一消费点 `game/commands/instance.py:802` 是函数内
`from ..core.encounter import encounter_chance as _enc_chance`（副本遇怪概率，数据表驱动）。
指向后 `game.core.encounter is content.encounter`：名字集合与身份逐名相同。

薄壳零实现：本文件不含任何逻辑。消费者清单与证据见 `overnight/W-B13-L2-wild-worlds.md`。
"""
import sys as _sys

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）

from content import encounter as _impl                       # noqa: E402

_sys.modules[__name__] = _impl
