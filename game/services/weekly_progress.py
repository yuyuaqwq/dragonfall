# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 服务层 - weekly_progress（★ B8.2 线1 起 = 薄壳）

逻辑真源已进内容包：`content/flow/weekly_progress.py`（逐字端口，真源 = 本文件旧版 93 行）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身：`db`（event_state 读/写）+ `reward.grant_reward`（达标发奖）
  3. **同名单 re-export** —— 保持模块路径与符号名不变，测试与 L3 订阅方零改动：
       测试           `tests/test_texts_table.py:61`（`_week_state` / `_save_week_state`）
       L3 订阅方      `game/services/player_event_subscribers.py:27`（`weekly_bump_kill`）

宿主注入的必要性：包内模块**不 import 宿主**（方向只有 内容 → 引擎）；它按 `bind_host(...)`
或「已加载的宿主模块」解析存储层，见包内模块 docstring 的替身接口表。
"""

from __future__ import annotations

from .. import bootstrap as _bootstrap
from .. import db as _db
from ..reward import grant_reward as _host_grant_reward

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
from content.flow import weekly_progress as _pkg    # noqa: E402

_pkg.bind_host(_db, _host_grant_reward)             # 宿主替身注入（幂等）

# ---- 同名单 re-export（逐字沿用真源符号名）----
_week_key = _pkg._week_key
_week_state = _pkg._week_state
_save_week_state = _pkg._save_week_state
_grant_rewards = _pkg._grant_rewards
weekly_bump_kill = _pkg.weekly_bump_kill
_assign_week = _pkg._assign_week
weekly_pool = _pkg.weekly_pool
WEEKLY_PICK = _pkg.WEEKLY_PICK
WEEKLY_MIN_LV = _pkg.WEEKLY_MIN_LV
