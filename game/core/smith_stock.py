# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心 - smith_stock.py（v135 铁匠铺全服共享货架）—— B13-L5 **薄壳**（2026-09-14）

实现正文（438 行）已**逐字搬进内容包** `content/smith_stock.py`（含常量 `QUALITY_WEIGHTS` /
`STOCK_COUNT` / `STOCK_WINDOW` / `RESTOCK_HOURS` / `_QTY_BY_QUALITY` / `SMITH_NPC_NAMES` /
`_SMITH_TOWN_LEVELS` 与 `town_level` / `roll_stock` / `get_smith_stock` / `buy_stock_item` /
`smith_stock_price` / `_static_shop_rids` / `_pick_weighted_quality` / `_smith_equip_price`）。
本文件只剩三件事：**加载包**（`bootstrap.package_apply()`，本进程唯一包加载口）·
**模块别名**（`sys.modules[__name__] = 包内模块`）· **源码探针**（见下）。

为什么用「模块别名」而不是「一行转发桩」
----------------------------------------
宿主/测试对本模块有两类**打补丁**用法，转发桩会让它们**静默失效**（补丁打在壳上，
实现读自己的模块全局）：

    tests/test_v135_smith_stock.py:112/137  mock.patch.object(ss, "_now_ts", …)
    tests/test_v184_loot_tiers.py:541/569   SS._pick_weighted_quality()

别名之后 `game.core.smith_stock` 与 `content.smith_stock` **是同一个模块对象**：
`from .smith_stock import town_level, roll_stock, …`（`game/core/__init__.py:62-65`）、
`from ..core import smith_stock as _ss`（`commands/economy.py:21`、`services/shop.py:12`、
包内 `content/economy_cmds.py` 经 `_ss` 宿主面）取到的都是包内实现本体，名字/签名/语义零变化。

宿主源码级门禁（**判据只加强**）
--------------------------------
`tests/test_v184_loot_tiers.py:695-696` 按**本文件源码**查字符串：必须含
`QUALITY_TIERS.pick_weights(QUALITY_WEIGHTS, rng=random)`、不得含旧的手写累加抽法
（`random` + `.randint` 手写累加抽法，故本文件里该字面量**不出现在一处**，免得自己把自己扫红）。
本文件保留同字面量指针，并在 import 期**断言它确实还长在包内实现里** —— 指针指向的实现若漂移，
直接 import 失败（比「扫到壳上一句注释就过」强）。
"""
import inspect as _inspect
import sys as _sys

from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                  # 本进程唯一包加载口（幂等）

from content import smith_stock as _impl                     # noqa: E402  包内实现（真源）

# ---- 宿主源码级门禁指针（tests/test_v184_loot_tiers.py:695）----
_SRC_PROBE = "QUALITY_TIERS.pick_weights(QUALITY_WEIGHTS, rng=random)"       # noqa: F841
try:
    _IMPL_SRC = _inspect.getsource(_impl)
except OSError as _exc:                                      # pragma: no cover
    raise RuntimeError("smith_stock 薄壳：取不到包内实现源码，唯一真相源指针无法核验（%r）" % (_exc,))
if _SRC_PROBE not in _IMPL_SRC:
    raise RuntimeError("smith_stock 薄壳：包内实现已漂移（源码里查不到 %r）" % (_SRC_PROBE,))

_sys.modules[__name__] = _impl                               # 模块别名：壳与实现同体
