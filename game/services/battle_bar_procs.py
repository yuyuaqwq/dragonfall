# -*- coding: utf-8 -*-
"""saintess_engine 挂敌身条装配层 battle_bar_procs（★ B10-L3 起 = 薄壳）。

真源已进内容包：`framework/games/orlandia/content/mech/bar_procs.py`（265 行，**逐字端口**；
D2 `bar_procs` 批搬运，B10-L3 收口本文件）。本文件旧版 244 行是它的搬运前身 —— 两版差异
只有 2 类（逐函数对拍见 `overnight/B10-L3-class-mech.md`）：

  1. `apply_bar_procs` 的两个取件口：`..data.battle_rules.BAR_INJECT_FIELDS` →
     包内单源 `..element_data`（再导出 `params.py`）；`..content_rules.skills.skill_info` →
     `..apply._SKILL_LOOKUP`（包内 `content/skills.py`）
  2. 包侧 `__all__`（4 个动作名）

其余 9 个函数（`_now_of` / `_host_of` / `_bar_keys_of` / `_ensure_tick` / `_settle` /
`bar_gain_act` / `bar_time_settle_act` / `bar_phase_preserve_act` / `passive_reflect_bar_act`）
**AST 逐字相同**；4 个动作在真源是模块级 `@register_action`（import 即注册），包内同款。

本壳只做两件事：

  1. **加载包**（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）——
     包内模块 import 期即注册 4 个动作（`bar_gain` / `bar_time_settle` / `bar_phase_preserve` /
     `passive_reflect_bar`），与真源「import 本文件即注册」逐字等价
  2. **同名单 re-export**（真源 10 个顶层名一个不少，符号名 / 签名一字不变）

✅ 零消费者判定（步骤 A 实测，2026-09-13）：
  · 生产 1 处（收口前）：`game/services/class_mech_proc.py:2364`
    （`from .battle_bar_procs import apply_bar_procs`）—— 随 L3 同批变薄壳后，该处由**包内**
    `class_mech.py` 的 `from .bar_procs import apply_bar_procs` 承接，本壳仅供 import 点保名
  · 测试 2 处：`tests/test_apply_game_content.py:38`（`as BAR`）·
    `tests/test_v181_gap_tail.py:39`（`from game.services.battle_bar_procs import _ensure_tick`）
  · `game/services/__init__.py` **未导出**本模块；文档/脚本引用均为注释路径

逐字节等价证据：`overnight/b10_l3_snap.py`（`bar/apply_bar_procs` + `bar/_ensure_tick` +
真实战斗「命中注入 → 阈值触发 → 时钟衰减」三段 · 与 `battle/*` 用例同源）。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（失败抛）

_bootstrap.package_apply()
from content.mech import bar_procs as _pkg                   # noqa: E402  ← 唯一实现（import 即注册 4 动作）

# ---------------------------------------------------------------- 同名单 re-export（真源 10 名）
_now_of = _pkg._now_of
_host_of = _pkg._host_of
_bar_keys_of = _pkg._bar_keys_of
_ensure_tick = _pkg._ensure_tick
_settle = _pkg._settle
bar_gain_act = _pkg.bar_gain_act
bar_time_settle_act = _pkg.bar_time_settle_act
bar_phase_preserve_act = _pkg.bar_phase_preserve_act
passive_reflect_bar_act = _pkg.passive_reflect_bar_act
apply_bar_procs = _pkg.apply_bar_procs
