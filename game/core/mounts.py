# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - mounts（★ B13-L7 起 = 薄壳）

逻辑真源已进内容包：`content/mounts.py`（**逐字端口**；真源 = 本文件旧版 47 行）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()`，幂等；失败大声抛）
  2. 注入宿主句柄：`data`（`MOUNT_BY_KEY` / `MOUNT_DROP_BOSS` / `MOUNT_DROP_ELITE` ——
     包里**没有 mounts 域**，`editor/domains.json` 无此名）→ 按完整模块名注入自己那棵树
  3. 同名单 re-export（3 个符号；`random` 仍是包内 `content/mounts.py` 用的同一只系统 RNG，
     所以 `random.seed(...)` 之后的行为与改造前逐字相同）

消费点零改动：`game/core/__init__.py:115`、`tests/test_v104_shop_auction_mount.py:18`
（`from ...core import mounts as M`）。

缺口：`MOUNT_POOL / MOUNT_BY_KEY / MOUNT_DROP_ELITE / MOUNT_DROP_BOSS` 四张表仍未进包
（无同名域）→ 待 B14 建域后切包内读口。
"""
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                   # 包加载口（失败抛，不静默）
from content import mounts as _pkg                           # noqa: E402

_HERE_PKG = __package__.rsplit(".", 1)[0]
_pkg.bind_host(data=_pkg.lazy_host_module(_HERE_PKG + ".data"))

# ---- 同名单 re-export（真源符号名一字不变）----
make_mount_rein = _pkg.make_mount_rein
roll_mount_drop = _pkg.roll_mount_drop
mount_effects = _pkg.mount_effects
