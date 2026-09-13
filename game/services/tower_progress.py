# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 服务层 - tower_progress（★ B8.2 线1 起 = 薄壳）

逻辑真源已进内容包：`content/flow/tower_progress.py`（逐字端口，真源 = 本文件旧版 110 行
+ 原 `game/commands/tower.py` 的 `build_tower_guard`）；塔表 = 包内 `content/flow/tower_data.py`
（真源 `game/data/trial_tower.py` 整文件逐字搬入）。

本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身：`db`（event_state / player 读写）
  3. **同名单 re-export** —— 保持模块路径与符号名不变，测试与 L3 订阅方零改动：
       测试           `tests/test_l3_player_events.py:21`（`_tower_state`）
       L3 订阅方      `game/services/player_event_subscribers.py:26`（`tower_guard_on_kill`）
"""

from __future__ import annotations

from .. import bootstrap as _bootstrap
from .. import db as _db

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
from content.flow import tower_progress as _pkg     # noqa: E402

_pkg.bind_host(_db)                                 # 宿主替身注入（幂等）

# ---- 同名单 re-export（逐字沿用真源符号名）----
_tower_key = _pkg._tower_key
_tower_state = _pkg._tower_state
_save_tower_state = _pkg._save_tower_state
_floor_def = _pkg._floor_def
tower_guard_on_kill = _pkg.tower_guard_on_kill
build_tower_guard = _pkg.build_tower_guard
TRIAL_FLOORS = _pkg.TRIAL_FLOORS
TRIAL_MIN_LV = _pkg.TRIAL_MIN_LV
TRIAL_MAX_FLOOR = _pkg.TRIAL_MAX_FLOOR
TRIAL_DAILY_LIMIT = _pkg.TRIAL_DAILY_LIMIT
