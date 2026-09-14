# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - factions 声望 tier（★ B13-L7 起 = 薄壳）

逻辑真源已进内容包：`content/factions.py`（**逐字端口**；真源 = 本文件旧版 14 行）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()`，幂等；失败大声抛）
  2. 注入宿主句柄：`data`（`REPUTATION_TIERS`，`game/data/factions.py:20`）——
     包里**没有 factions 域**（`editor/domains.json` 无此名）→ 按完整模块名注入自己那棵树
  3. 同名单 re-export（1 个符号）

消费点零改动：`game/core/__init__.py:58`、`tests/test_daily_events.py:23`。

缺口：`REPUTATION_TIERS`（连带 `FACTIONS` / `FACTION_ORDER` / `AREA_FACTION` / `CHRONICLES`）
仍未进包 → 待 B14 建域后切包内读口。
"""
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                   # 包加载口（失败抛，不静默）
from content import factions as _pkg                         # noqa: E402

_HERE_PKG = __package__.rsplit(".", 1)[0]
_pkg.bind_host(data=_pkg.lazy_module(_HERE_PKG + ".data"))

# ---- 同名单 re-export（真源符号名一字不变）----
faction_reputation_tier = _pkg.faction_reputation_tier
