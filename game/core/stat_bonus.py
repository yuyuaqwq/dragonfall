# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 `stat_bonus`（B13-L6 **薄壳**）。

真源（实现本体，逐字搬）已进内容包：`content/stat_bonus.py`。
本文件只剩三件事：**加载包**（幂等；失败大声抛）+ **同名单 re-export**（符号名/签名一字不变）
+ 数量：全名单再导出。

消费者 9 处，零改动：`commands/base.py:523` · `core/achievements.py:234` · `reward.py:166` ·
  `services/battle_settlement.py:37` · `services/player_event_subscribers.py:21` · `services/quests.py:66` ·
  `services/quests_flow.py:35` · `store/players.py:231` · 测试 `tests/test_m_bonus.py:42` / `test_numeric_reward_unify.py:97`

逐字节等价证据：`overnight/w1213_l6_snap.py`（改前/改后同 sha256 + 字节数）；
差异面自检：`overnight/w1213_l6_diff.py`（只列「宿主取件」差异行）；本线报告 `overnight/W-B13-L6-stats-rules.md`。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（本进程唯一；幂等）

_bootstrap.package_apply()                                   # 失败抛，不静默留一个空实现
from content import stat_bonus as _pkg  # noqa: E402                 # ← 唯一实现

# ---------------------------------------------------------------- 同名单 re-export（真源 9 名）
C = _pkg.C
LOG = _pkg.LOG
_visited_maps = _pkg._visited_maps
_has_enhanced = _pkg._has_enhanced
stat_bonus = _pkg.stat_bonus
_collection_completed_bonus = _pkg._collection_completed_bonus
BONUS_DOMAINS = _pkg.BONUS_DOMAINS
bonus_seed = _pkg.bonus_seed
bonus_domain = _pkg.bonus_domain
