# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - achievement_conds.py（★ B13-L4（2026-09-14）起 = **薄壳**）

真源已进内容包：`framework/games/orlandia/content/achievement_conds.py`（**逐字端口**，本文件旧版
497 行是它的搬运前身 —— 替换表与断言见 `overnight/w1213_b13l4_port.py`，
逐字节等价证据 = `overnight/w1213_b13l4_snap.py`，改前/改后同 sha256）。

本壳只做两件事：

  1. **加载包**（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
     —— 包内模块 import 期即跑完 `COND_CHECKS` / `CONDITIONS` 注册（含
     `content/achievements.py` 的 3 个 v140 条件类型），与真源「import 本文件即注册」逐字等价；
  2. **同名单 re-export**（真源 48 个顶层名一个不少，符号名 / 签名一字不变）——
     消费者（`content/achievements.py`（`COND_CHECKS`）· `tests/test_v99_05_achievement_conds.py` · 游戏仓导出器 `scripts/export_domains/shop_econ.py:derive_achievement_conds`）的 import 点零改动。

宿主替身（`db` / `C`）由包内模块按 `sys.modules` 惰性解析（`_HostMod`），本壳不注入。
"""

from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（失败抛）

_bootstrap.package_apply()
from content import achievement_conds as _pkg                            # noqa: E402  ← 唯一实现

# ---------------------------------------------------------------- 同名单 re-export（真源顶层名）
COND_CHECKS = _pkg.COND_CHECKS
register = _pkg.register
_value = _pkg._value
_c_registered = _pkg._c_registered
_c_level = _pkg._c_level
_c_evolve = _pkg._c_evolve
_c_learned = _pkg._c_learned
_c_learned_all = _pkg._c_learned_all
_c_skill_has = _pkg._c_skill_has
_c_branch_skills = _pkg._c_branch_skills
_c_hidden_class = _pkg._c_hidden_class
_c_hidden_class_lv = _pkg._c_hidden_class_lv
_c_kills = _pkg._c_kills
_c_elite = _pkg._c_elite
_c_boss = _pkg._c_boss
_c_kills_type = _pkg._c_kills_type
_c_prof_lv = _pkg._c_prof_lv
_c_prof_any10 = _pkg._c_prof_any10
_c_prof_count = _pkg._c_prof_count
_c_apprentice = _pkg._c_apprentice
_c_set_has = _pkg._c_set_has
_c_visited = _pkg._c_visited
_c_hidden_area = _pkg._c_hidden_area
_c_inst_clear = _pkg._c_inst_clear
_c_inst_id = _pkg._c_inst_id
_c_inst_all8 = _pkg._c_inst_all8
_c_flawless = _pkg._c_flawless
_c_bestiary = _pkg._c_bestiary
_c_bestiary_all = _pkg._c_bestiary_all
_c_item_has = _pkg._c_item_has
_c_hidden_monsters_all = _pkg._c_hidden_monsters_all
_c_party = _pkg._c_party
_c_guild = _pkg._c_guild
_c_guild_lv = _pkg._c_guild_lv
_c_faction = _pkg._c_faction
_faction_contribute = _pkg._faction_contribute
_c_faction_top = _pkg._c_faction_top
_c_faction_rank1 = _pkg._c_faction_rank1
_c_world_event = _pkg._c_world_event
_c_event_all = _pkg._c_event_all
_c_fish_king = _pkg._c_fish_king
_c_collect_fish = _pkg._c_collect_fish
_c_wish_met = _pkg._c_wish_met
_c_worldboss = _pkg._c_worldboss
_c_quest_done = _pkg._c_quest_done
_c_main_done = _pkg._c_main_done
_c_main_quest_done = _pkg._c_main_quest_done
_c_flag = _pkg._c_flag
