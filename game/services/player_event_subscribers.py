# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 L3 玩家事件订阅方注册（★ B12-L4 起 = 薄壳）

逻辑真源已进内容包：`content/player_events.py`（逐字端口，真源 = 本文件旧版 170 行
+ `player_event_bus.py` 旧版 71 行 —— 订阅方与总线同处一个包内模块）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身：
       `db` / `c`      —— 存储层 + 内容聚合层（真源模块级 `from .. import db` / `from .. import content as C`）
       `log`           —— `log_setup.LOG`（总线 logger）
     ⚠️ 订阅方体内那 8 个宿主函数（`check_player_level_up` / `check_achievements` / `stat_bonus` /
     `wild_king_on_kill` / `guild_kill_progress` / `quest_kill_progress` / `tower_guard_on_kill` /
     `weekly_bump_kill`）属**别线正在并行搬的模块** ⇒ 包内一律按「宿主句柄 + 调用时解析」接入
     （见包内 docstring 缺口节），本文件无需注入。
  3. **注册时机 + 同名单 re-export**：
       `ensure_registered()` 在**本模块 import 时**调用一次 —— 与真源「模块末尾自动注册」逐字同义
       （原调用点：`game/commands/instance.py:2521/2999`、`content/combat_cmds.py:2297/2616`、
       `tests/test_l3_player_events.py:19`；幂等，重复 import 不重复注册）。
       订阅方名字 `/ _sub_levelup`（`tests/test_l3_player_events.py:100` 点名）逐字沿用。
"""

from __future__ import annotations

import importlib

from .. import bootstrap as _bootstrap
from .. import content as _host_content
from .. import db as _db
from ..log_setup import LOG as _LOG

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
_pkg = importlib.import_module("content.player_events")

_pkg.bind_host(db=_db, c=_host_content, log=_LOG)   # 宿主替身注入（幂等）
_pkg.ensure_registered()                            # 注册 6 个 battle_victory 订阅方（幂等）

# ---- 同名单 re-export（逐字沿用真源符号名）----
_sub_guild_daily = _pkg._sub_guild_daily
_sub_levelup = _pkg._sub_levelup
_sub_quests = _pkg._sub_quests
_sub_wild_king = _pkg._sub_wild_king
_sub_tower_guard = _pkg._sub_tower_guard
_ach_lines = _pkg._ach_lines
_sub_achievements = _pkg._sub_achievements
ensure_registered = _pkg.ensure_registered

# 真源模块级标志 `_registered` 现由包内模块持有（生产无消费者）→ 按 PEP 562 转发，保持 import 兼容
_LAZY = ("_registered",)


def __getattr__(name):
    if name in _LAZY:
        return getattr(_pkg, name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))
