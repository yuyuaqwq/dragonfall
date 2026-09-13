# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 `rule_engine`（B13-L6 **薄壳**）。

真源（实现本体，逐字搬）已进内容包：`content/rule_engine.py`。
本文件只剩三件事：**加载包**（幂等；失败大声抛）+ **同名单 re-export**（符号名/签名一字不变）
+ 数量：全名单再导出。

消费者 2 处零改动：`game/commands/base.py:511`（函数内 `from ..core.rule_engine import fire as _fire`）·
  `game/services/battle_settlement.py:36`（顶层 `from ..core.rule_engine import fire as rule_fire`）；
  测试 `tests/test_v97_05_rule_engine.py:29/34`（`fire, _get_counter` + `RE._is_time = …` 覆盖宿主模块属性 —— 该覆盖
  由包内 `_time_check()` 取件承接，见包内头注 ④）

逐字节等价证据：`overnight/w1213_l6_snap.py`（改前/改后同 sha256 + 字节数）；
差异面自检：`overnight/w1213_l6_diff.py`（只列「宿主取件」差异行）；本线报告 `overnight/W-B13-L6-stats-rules.md`。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（本进程唯一；幂等）

_bootstrap.package_apply()                                   # 失败抛，不静默留一个空实现
from content import rule_engine as _pkg  # noqa: E402                 # ← 唯一实现

# ---------------------------------------------------------------- 同名单 re-export（真源 9 名）
RULES = _pkg.RULES
_rules = _pkg._rules
_db = _pkg._db
_counter_key = _pkg._counter_key
_get_counter = _pkg._get_counter
_set_counter = _pkg._set_counter
_is_time = _pkg._is_time
_match_cond = _pkg._match_cond
fire = _pkg.fire
