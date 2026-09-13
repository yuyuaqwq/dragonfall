# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 `race_talent_display`（B13-L6 **薄壳**）。

真源（实现本体，逐字搬）已进内容包：`content/race_talent_display.py`。
本文件只剩三件事：**加载包**（幂等；失败大声抛）+ **同名单 re-export**（符号名/签名一字不变）
+ 数量：全名单再导出。

消费者 2 处零改动：`game/commands/player.py:417/697`（函数内 `from ..core.race_talent_display import format_talent`）；
  测试 `tests/test_v98_03_registry.py:36`（`from ...game.core import race_talent_display as RTD`）

逐字节等价证据：`overnight/w1213_l6_snap.py`（改前/改后同 sha256 + 字节数）；
差异面自检：`overnight/w1213_l6_diff.py`（只列「宿主取件」差异行）；本线报告 `overnight/W-B13-L6-stats-rules.md`。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（本进程唯一；幂等）

_bootstrap.package_apply()                                   # 失败抛，不静默留一个空实现
from content import race_talent_display as _pkg  # noqa: E402                 # ← 唯一实现

# ---------------------------------------------------------------- 同名单 re-export（真源 27 名）
DISPLAY = _pkg.DISPLAY
register = _pkg.register
format_talent = _pkg.format_talent
_d_hp_mult = _pkg._d_hp_mult
_d_growth_mult = _pkg._d_growth_mult
_d_spd_mult = _pkg._d_spd_mult
_d_crit_add = _pkg._d_crit_add
_d_phys_reduce = _pkg._d_phys_reduce
_d_magic_reduce = _pkg._d_magic_reduce
_d_heal_received = _pkg._d_heal_received
_d_berserk_hp = _pkg._d_berserk_hp
_d_timid_hp = _pkg._d_timid_hp
_d_first_hit = _pkg._d_first_hit
_d_learn_discount = _pkg._d_learn_discount
_d_first_upgrade_refund = _pkg._d_first_upgrade_refund
_d_prof_bonus = _pkg._d_prof_bonus
_d_exp_bonus = _pkg._d_exp_bonus
_d_crit_dmg = _pkg._d_crit_dmg
_d_block = _pkg._d_block
_d_lifesteal = _pkg._d_lifesteal
_d_luck = _pkg._d_luck
_d_item_effect = _pkg._d_item_effect
_d_craft_bonus = _pkg._d_craft_bonus
_d_explore_item = _pkg._d_explore_item
_d_berserk_tag = _pkg._d_berserk_tag
_d_timid_tag = _pkg._d_timid_tag
_d_first_hit_tag = _pkg._d_first_hit_tag
