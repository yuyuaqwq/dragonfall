# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - _identity：平台身份映射（openid ↔ QQ 号）—— **B2-W2 薄壳指向**

真源（**唯一实现**）= 内容包 `content/_identity.py`（B2-C4 新建：宿主原 120 行逐字搬入，
存储句柄改走**包内** `content/persistence/handles`；搬运边界见那边的头注）。本文件只剩两件事
（照**已有先例** `game/core/wild_king.py` 的写法）：

    加载包（`bootstrap.package_apply()`，幂等）· 把 `game.commands._identity` 这个名字**指向**包内实现

`_sys.modules[__name__] = _impl` ⇒ 8 个模块级名（`is_openid` / `is_qq_id` / `bind` /
`unbind_openid` / `openid_to_qq` / `qq_to_openid` / `resolve_uid` / `query_all`）逐名逐对象不变，
宿主消费者零改动：

    game/commands/base.py:100-101  `resolve_uid`
    game/commands/gm.py:169        `qq_to_openid`
    game/commands/gm.py:328-329    `qq_to_openid` / `query_all`
    tests/test_v62_delete_account.py 等（`resolve_uid` / `bind`）

实测：宿主壳顶层名 − 包内顶层名 = **空**（`out/evidence/probe_w2.txt`）⇒ 无 host-only 残留。
接口表第 1 行冻结的「注入句柄 `db`」在 C4 落地时被**更强的等价物**取代：包内直接 import
`content/persistence/handles`（B1 的包内存储层，与宿主 `game/store/connection.py` **同一只库、
同一批函数对象**；`tests` 的身份对拍 `out/evidence/identity_parity.txt` 同 0 差异）——
故本壳**不需要**再 bind_host，指向即等价（宿主侧零行为变化）。
"""
import sys as _sys

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）

from content import _identity as _impl                       # noqa: E402

_sys.modules[__name__] = _impl
