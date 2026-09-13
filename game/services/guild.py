# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - guild（★ B9-L3 起 = 薄壳）

逻辑真源已进内容包：`content/social_guild.py`（真源 = 本文件旧版 275 行全文件 +
原 `game/commands/social.py` 的公会面板/商店/技能编排）。本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身：`db`（存储层门面）+ `GUILD_CONFIG`（数值配置 = L7 配置面）+ `store.social`
     （公会原语 `guild_get_member` / `guild_set_role` / `guild_spend_contribute`——
     这三个在 `game/store/social.py` 里，但 `game/db.py` 聚合面没导出）
  3. **同名单 re-export** —— 保持模块路径与符号名不变，测试与 L3 订阅方零改动：
       测试            `tests/test_services_party_guild.py:28`（14 个函数）
       L3 订阅方       `game/services/player_event_subscribers.py:23`（`guild_kill_progress`）
       命令层          `game/commands/social.py`（公会 14 条命令 + 面板行构造）

宿主注入的必要性：包内模块**不 import 宿主**（方向只有 内容 → 引擎）；它按 `bind_host(...)`
或「已加载的宿主模块」解析存储层，见包内模块 docstring 的替身接口表。

⚠️ 未搬（见 B9-L3 报告 §缺口）：`GUILD_CONFIG`（数值配置，归 L7）与 `GUILD_EXP_BASE`
（宿主数值常量）——包内模块按注入/传参用，不在包侧另起一份。
"""

from __future__ import annotations

from .. import bootstrap as _bootstrap
from .. import db as _db
from ..data import guild as _G
from ..store import social as _store_social

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
from content import social_guild as _pkg            # noqa: E402

_pkg.bind_host(_db, config=_G.GUILD_CONFIG, store_social=_store_social)   # 宿主替身注入（幂等）

# ---- 同名单 re-export（逐字沿用真源符号名）----
ROLE_MAP = _pkg.ROLE_MAP
APPOINTABLE_ROLES = _pkg.APPOINTABLE_ROLES

guild_create_check = _pkg.guild_create_check
guild_create = _pkg.guild_create
guild_join = _pkg.guild_join
guild_leave_check = _pkg.guild_leave_check
guild_leave = _pkg.guild_leave
guild_disband = _pkg.guild_disband
guild_sign = _pkg.guild_sign
guild_task_view = _pkg.guild_task_view
guild_donate_inventory = _pkg.guild_donate_inventory
guild_donate_total = _pkg.guild_donate_total
guild_donate = _pkg.guild_donate
guild_rank_lines = _pkg.guild_rank_lines
guild_appoint_check_role = _pkg.guild_appoint_check_role
guild_appoint_level_ok = _pkg.guild_appoint_level_ok
guild_find_member = _pkg.guild_find_member
guild_appoint = _pkg.guild_appoint
guild_demote = _pkg.guild_demote
guild_kill_progress = _pkg.guild_kill_progress

# ---- B9-L3 新进包的三个命令级编排（公会面板 / 商店面板与购买 / 技能面板）----
guild_info_lines = _pkg.guild_info_lines
guild_exp_bonus_pct = _pkg.guild_exp_bonus_pct
guild_shop_lines = _pkg.guild_shop_lines
guild_shop_buy = _pkg.guild_shop_buy
guild_skill_lines = _pkg.guild_skill_lines
