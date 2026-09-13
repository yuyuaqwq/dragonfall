# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - wild_king.py —— **B13-L2 薄壳**（2026-09-14）

真源（**唯一实现**）= 内容包 `content/wild_king.py`（709 行，逐字搬自本文件的 622 行；
搬运改动面只有「宿主取件」一类，逐行见包内头注）。本文件现在只剩两件事：

    加载包（`package_apply()`，幂等）· 把 `game.core.wild_king` 这个名字**指向**包内那份实现

为什么是「指向」而不是「从包内再导出 41 个名字」
------------------------------------------------
真源顶层名（41 个）与包内**逐名相同**（含私有名 `_load_global` / `_build_king` /
`_roll_chest_rewards` / `_party_members_of`，测试与命令层按名取用），且本模块的顶层名被
`game/core/__init__.py:121` / `game/commands/combat.py:43`（野王四函数经本模块属性解析，
`tests/test_v1307_zone_risk.py:65` / `test_v1308_lv_jitter.py:70` monkeypatch
`game.commands.combat.explore_king`）/ `game/services/player_event_subscribers.py:22` /
`game/commands/base.py:253` / `tests/test_numeric_drop_unify.py:151`
按**模块属性 + 模块身份**消费。指向后 `game.core.wild_king is content.wild_king`：
名字集合、对象身份、可变性全部与改造前逐名/逐对象相同，`import game.core.wild_king` 照旧。

薄壳零实现：本文件不含任何逻辑。消费者清单与证据见 `overnight/W-B13-L2-wild-worlds.md`。
"""
import sys as _sys

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）

from content import wild_king as _impl                       # noqa: E402

_sys.modules[__name__] = _impl
