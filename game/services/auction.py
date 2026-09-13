# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - auction（★ B12 L5 起 = 薄壳）

逻辑真源已进内容包：`content/auction.py`（逐字端口，真源 = 本文件旧版 103 行；
生成器 `overnight/w1213_l5_gen.py` 可按「删 4 行宿主取件」重算出包内正文）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身：
       `db`      —— 存储层（真源 函数体内 `from .. import db`）
       `content` —— 内容聚合层（真源 函数体内 `from .. import content as C`，
                    本模块只用它的 `C.generate_equip`）
  3. **同名单 re-export** —— 保持模块路径与符号名不变（含 P4-5 兼容别名 `_settle_auction`）：
       `game/commands/social.py:19`（`settle_expired_auction`）· `:862`（`settle_auction`）
       `game/services/__init__.py:37`（3 个名字）· `tests/test_services_auction.py`

逐字节等价证据：`overnight/w1213_l5_snap.py`（20 例 · 私有库全表 dump · sha256 对拍）。

⚠️ 缺口（见包内模块头注）：`C.generate_equip`（宿主 `game/core/drops.py`）**无同名域**
→ 走宿主句柄 + 缺口登记，B14 切读点/裁缺口时统一处置；本线不建第二份读口。
"""

from __future__ import annotations

from .. import bootstrap as _bootstrap
from .. import content as _host_content
from .. import db as _db

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
from content import auction as _pkg                 # noqa: E402

_pkg.bind_host(db=_db, content=_host_content)       # 宿主替身注入（幂等）

# ---- 同名单 re-export（逐字沿用真源符号名）----
settle_auction = _pkg.settle_auction
_settle_auction = _pkg._settle_auction
settle_expired_auction = _pkg.settle_expired_auction
save_auction_state = _pkg.save_auction_state
