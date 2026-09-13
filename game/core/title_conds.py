# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - title_conds.py（★ B13-L4（2026-09-14）起 = **薄壳**）

真源已进内容包：`framework/games/orlandia/content/title_conds.py`（**逐字端口**，本文件旧版
350 行是它的搬运前身 —— 替换表与断言见 `overnight/w1213_b13l4_port.py`，
逐字节等价证据 = `overnight/w1213_b13l4_snap.py`，改前/改后同 sha256）。

本壳只做两件事：

  1. **加载包**（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
     —— 包内模块 import 期即跑完 `COND_CHECKS` / `CONDITIONS` 注册（含
     `content/achievements.py` 的 3 个 v140 条件类型），与真源「import 本文件即注册」逐字等价；
  2. **同名单 re-export**（真源 56 个顶层名一个不少，符号名 / 签名一字不变）——
     消费者（`game/commands/economy.py:26` · `game/core/stat_bonus.py:87` · `tests/test_v98_03_registry.py` · `tests/test_v1242_audit_fix.py` · 游戏仓导出器 `scripts/export_domains/shop_econ.py:derive_title_conds`）的 import 点零改动。

宿主替身（`db` / `C`）由包内模块按 `sys.modules` 惰性解析（`_HostMod`），本壳不注入。
"""

from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（失败抛）

_bootstrap.package_apply()
from content import title_conds as _pkg                            # noqa: E402  ← 唯一实现

# ---------------------------------------------------------------- 同名单 re-export（真源顶层名）
CONDITIONS = _pkg.CONDITIONS
register = _pkg.register
TitleCtx = _pkg.TitleCtx
_t_novice = _pkg._t_novice
_t_lv10 = _pkg._t_lv10
_t_lv20 = _pkg._t_lv20
_t_lv30 = _pkg._t_lv30
_t_kill10 = _pkg._t_kill10
_t_kill100 = _pkg._t_kill100
_t_kill500 = _pkg._t_kill500
_t_elite5 = _pkg._t_elite5
_t_boss1 = _pkg._t_boss1
_t_boss3 = _pkg._t_boss3
_t_rep_honor = _pkg._t_rep_honor
_t_rep_legend = _pkg._t_rep_legend
_t_quest10 = _pkg._t_quest10
_t_wealthy = _pkg._t_wealthy
_t_explorer = _pkg._t_explorer
_t_fish10 = _pkg._t_fish10
_t_enhance5 = _pkg._t_enhance5
_t_enhance9 = _pkg._t_enhance9
_t_hidden = _pkg._t_hidden
_t_final = _pkg._t_final
_t_iron_adventurer = _pkg._t_iron_adventurer
_t_fish_king = _pkg._t_fish_king
_t_pvp_hero = _pkg._t_pvp_hero
_side_done = _pkg._side_done
_has_flag = _pkg._has_flag
_t_north_benefactor = _pkg._t_north_benefactor
_t_nightwalker = _pkg._t_nightwalker
_t_guifan_seal = _pkg._t_guifan_seal
_t_dragon_warden = _pkg._t_dragon_warden
_t_gourmet = _pkg._t_gourmet
_t_herb_friend = _pkg._t_herb_friend
_t_treasure_hunter = _pkg._t_treasure_hunter
_t_furry_friend = _pkg._t_furry_friend
_t_merchant_friend = _pkg._t_merchant_friend
_t_just_enforcer = _pkg._t_just_enforcer
_t_shadow_friend = _pkg._t_shadow_friend
_t_dusk_detective = _pkg._t_dusk_detective
_t_peacemaker = _pkg._t_peacemaker
_t_guide = _pkg._t_guide
_t_night_rain = _pkg._t_night_rain
_t_goose_messenger = _pkg._t_goose_messenger
_t_forge_son = _pkg._t_forge_son
_t_graveyard_warden = _pkg._t_graveyard_warden
_t_fishing_legend = _pkg._t_fishing_legend
_t_late_messenger = _pkg._t_late_messenger
_t_season_gardener = _pkg._t_season_gardener
check_pro_title = _pkg.check_pro_title
_t_res_forge_master = _pkg._t_res_forge_master
_t_res_gather_expert = _pkg._t_res_gather_expert
_t_res_treasure_hunter = _pkg._t_res_treasure_hunter
_t_res_fishing_legend = _pkg._t_res_fishing_legend
_t_res_alchemy_master = _pkg._t_res_alchemy_master
_t_res_food_king = _pkg._t_res_food_king
