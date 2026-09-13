# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - achievements.py（★ B13-L4（2026-09-14）起 = **薄壳**）

真源已进内容包：`framework/games/orlandia/content/achievements.py`（**逐字端口**，本文件旧版
305 行是它的搬运前身 —— 替换表与断言见 `overnight/w1213_b13l4_port.py`，
逐字节等价证据 = `overnight/w1213_b13l4_snap.py`，改前/改后同 sha256）。

本壳只做两件事：

  1. **加载包**（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
     —— 包内模块 import 期即跑完 `COND_CHECKS` / `CONDITIONS` 注册（含
     `content/achievements.py` 的 3 个 v140 条件类型），与真源「import 本文件即注册」逐字等价；
  2. **同名单 re-export**（真源 12 个顶层名一个不少，符号名 / 签名一字不变）——
     消费者（`game/core/__init__.py:86`（4 个名字）· `game/services/player_event_subscribers.py:20` · `tests/test_v104_achievements.py` · `tests/test_v116_faction_camp.py`）的 import 点零改动。

宿主替身（`db` / `C`）由包内模块按 `sys.modules` 惰性解析（`_HostMod`），本壳不注入。
"""

from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（失败抛）

_bootstrap.package_apply()
from content import achievements as _pkg                            # noqa: E402  ← 唯一实现

# ---------------------------------------------------------------- 同名单 re-export（真源顶层名）
_COND_CHECKS = _pkg._COND_CHECKS
_register_cond = _pkg._register_cond
_c_blueprints_learned = _pkg._c_blueprints_learned
_c_quests_done = _pkg._c_quests_done
_c_chests_opened = _pkg._c_chests_opened
_bestiary_kills = _pkg._bestiary_kills
_monster_total = _pkg._monster_total
cond_met = _pkg.cond_met
achievement_titles = _pkg.achievement_titles
achievement_points = _pkg.achievement_points
check_achievements = _pkg.check_achievements
claim_achievement_rewards = _pkg.claim_achievement_rewards
