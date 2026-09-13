# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心 - shop_stock.py（v166 商店限购）—— B13-L5 **薄壳**（2026-09-14）

两层限购（店内共享库存 + 每人每日限购）+ 惰性补货的实现正文（228 行，含 `get_limit` /
`stock_state` / `check_and_consume` / `limit_label` / `_is_restock_due` / `_consume_shared` /
`_day_*` 与私有 `_now_ts` / `_today`）已**逐字搬进内容包** `content/shop_stock.py`，
配置表改读包内 `shop_stock` 域（35 条，= 真源 `game/data/shop_limit.py:39 SHOP_LIMIT`）。
本文件只剩三件事：**加载包** · **模块别名**（`sys.modules[__name__] = 包内模块`） · 说明。

为什么用「模块别名」而不是「一行转发桩」
----------------------------------------
`tests/test_v166_shop_limit.py:97` 用 `mock.patch.object(SS, "_now_ts", …)` 把时钟推到 7 小时后
验证补货 —— 转发桩会让补丁**静默失效**（补丁打在壳上，实现读自己的模块全局）。
别名之后 `game.core.shop_stock` 与 `content.shop_stock` **是同一个模块对象**：
`from .shop_stock import get_limit, stock_state, check_and_consume, limit_label`
（`game/core/__init__.py:67-70`）与 `from ..core import shop_stock as _sshop`
（`commands/economy.py:21`、`services/shop.py:12`、包内 `content/economy_cmds.py` 的 `_sshop` 宿主面）
取到的都是包内实现本体，名字/签名/语义零变化。
"""
import sys as _sys

from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                  # 本进程唯一包加载口（幂等）

from content import shop_stock as _impl                      # noqa: E402  包内实现（真源）

_sys.modules[__name__] = _impl                               # 模块别名：壳与实现同体
