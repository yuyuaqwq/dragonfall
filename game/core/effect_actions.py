# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 `effect_actions`（B13-L6 **薄壳**）。

真源（实现本体，逐字搬）已进内容包：`content/effect_actions.py`。
本文件只剩三件事：**加载包**（幂等；失败大声抛）+ **同名单 re-export**（符号名/签名一字不变）
+ 数量：全名单再导出。

消费者 1 处零改动：`game/core/potion_effects.py:136`（函数内 `from .effect_actions import action_def_down`）

逐字节等价证据：`overnight/w1213_l6_snap.py`（改前/改后同 sha256 + 字节数）；
差异面自检：`overnight/w1213_l6_diff.py`（只列「宿主取件」差异行）；本线报告 `overnight/W-B13-L6-stats-rules.md`。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（本进程唯一；幂等）

_bootstrap.package_apply()                                   # 失败抛，不静默留一个空实现
from content import effect_actions as _pkg  # noqa: E402                 # ← 唯一实现

# ---------------------------------------------------------------- 同名单 re-export（真源 12 名）
_ea_tgt = _pkg._ea_tgt
action_regen_hp = _pkg.action_regen_hp
action_regen_mp = _pkg.action_regen_mp
action_dot = _pkg.action_dot
action_def_down = _pkg.action_def_down
action_mark = _pkg.action_mark
_bonus_dmg_apply = _pkg._bonus_dmg_apply
action_bonus_pct = _pkg.action_bonus_pct
action_element_dmg = _pkg.action_element_dmg
action_pierce_dmg = _pkg.action_pierce_dmg
action_counter = _pkg.action_counter
action_lifesteal = _pkg.action_lifesteal
