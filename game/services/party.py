# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - party（★ B12-L4 起 = 薄壳）

逻辑真源已进内容包：`content/party.py`（逐字端口，真源 = 本文件旧版 225 行）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身：
       `db`            —— 存储层（真源函数体内 `from .. import db`：party_* 原语 / bump_stats /
                          update_player / clear_battle / get_battle / get_group_players）
       `c`             —— 内容聚合层 `game.content`（只喂未进包的符号：`display` / `CLASS_NOVICE` /
                          `check_achievements`）
       `panel_stats`   —— `content_rules.panel.player_final_stats`（面板速度值，真源函数体内惰性 import）
  3. **同名单 re-export** —— 保持模块路径与符号名不变，命令层 / 聚合导出 / 测试零改动：
       命令层       `game/commands/social.py:301`（5 名）· `:366`（3 名）
       聚合导出     `game/services/__init__.py:40`（8 个名字，逐字沿用）
       测试         `tests/test_services_party_guild.py:24`

宿主注入的必要性：包内模块**不 import 宿主**（方向只有 内容 → 引擎）；它按 `bind_host(...)`
或「已加载的宿主模块」解析存储层，见包内模块 docstring 的替身接口表。

⚠️ 未搬（见 B12-L4 报告 §缺口）：`db.party_*` 等**存档层原语**（`game/store/social.py`）
按接人层铁律留宿主；`C.display` / `C.check_achievements` 包内无等价读口，不建第二份。
"""

from __future__ import annotations

import importlib

from .. import bootstrap as _bootstrap
from .. import content as _host_content
from .. import db as _db
from ..content_rules.panel import player_final_stats as _panel_stats

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
_pkg = importlib.import_module("content.party")

_pkg.bind_host(db=_db, c=_host_content, panel_stats=_panel_stats)   # 宿主替身注入（幂等）

# ---- 同名单 re-export（逐字沿用真源符号名）----
resolve_party_target = _pkg.resolve_party_target
party_in_battle = _pkg.party_in_battle
target_in_battle = _pkg.target_in_battle
party_view_lines = _pkg.party_view_lines
party_join = _pkg.party_join
party_leave_check = _pkg.party_leave_check
party_leave_inst_member = _pkg.party_leave_inst_member
party_leave_execute = _pkg.party_leave_execute
