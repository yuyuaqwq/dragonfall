# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 `battle_cond_labels`（B13-L6 **薄壳**）。

真源（实现本体，逐字搬）已进内容包：`content/battle_cond_labels.py`。
本文件只剩三件事：**加载包**（幂等；失败大声抛）+ **同名单 re-export**（符号名/签名一字不变）
+ 数量：一行再导出 `COND_LABELS`。

消费者 1 处零改动：`game/commands/player.py:1523`（函数内 `from ..core.battle_cond_labels import COND_LABELS`）

逐字节等价证据：`overnight/w1213_l6_snap.py`（改前/改后同 sha256 + 字节数）；
差异面自检：`overnight/w1213_l6_diff.py`（只列「宿主取件」差异行）；本线报告 `overnight/W-B13-L6-stats-rules.md`。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（本进程唯一；幂等）

_bootstrap.package_apply()                                   # 失败抛，不静默留一个空实现
from content import battle_cond_labels as _pkg  # noqa: E402                 # ← 唯一实现

# ---------------------------------------------------------------- 同名单 re-export（真源 1 名）
COND_LABELS = _pkg.COND_LABELS
