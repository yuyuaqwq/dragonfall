# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - player_event_bus（★ B12-L4 起 = 薄壳）

逻辑真源已进内容包：`content/player_events.py`（逐字端口，真源 = 本文件旧版 71 行
+ `player_event_subscribers.py` 旧版 170 行 —— 总线与订阅方同处一个包内模块）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身 `log` —— 真源 `from ..log_setup import LOG`（总线 logger；包内惰性建总线，
     注入先于首次使用 ⇒ 日志仍走宿主 `astrbot` 管线）
  3. **同名单 re-export** —— 保持模块路径与符号名不变，命令层 / 包内战斗层 / 测试零改动：
       命令层     `game/commands/instance.py:2520/2998`（`fire`）
       包内       `content/combat_cmds.py:2296-2304/2615-2628`（`_host_attr("services.player_event_bus","fire")`）
       测试       `tests/test_player_event_bus.py:16`（EVENTS / register / fire / clear_registry）·
                  `tests/test_l3_player_events.py:18`（fire）

总线机制（注册表 / 注册序执行 / 段落空行 / 未知事件策略 / 异常容忍）来自框架
`saintess_engine.events.EventBus`；本模块只留**本游戏的内容**：事件集 `EVENTS`、对外 API 名、日志器
—— 这三样随本次一起进包（`content/player_events.py`），宿主不再持有第二份。
"""

from __future__ import annotations

import importlib

from .. import bootstrap as _bootstrap
from ..log_setup import LOG as _LOG

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
_pkg = importlib.import_module("content.player_events")

_pkg.bind_host(log=_LOG)                            # 宿主替身注入（幂等）

# ---- 同名单 re-export（逐字沿用真源符号名）----
EVENTS = _pkg.EVENTS
register = _pkg.register
fire = _pkg.fire
clear_registry = _pkg.clear_registry
