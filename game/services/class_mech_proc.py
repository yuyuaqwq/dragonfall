# -*- coding: utf-8 -*-
"""saintess_engine 职业机制装配层 class_mech_proc（★ B10-L3 起 = 薄壳）。

真源已进内容包：`framework/games/orlandia/content/mech/class_mech.py`（2676 行，**逐字端口** +
`@register_action` 化；D2 `class_mech` 批搬运，B10-L3 收口本文件）。本文件旧版 2446 行是它的
搬运前身 —— 两版差异只有 4 类，逐函数对拍见 `overnight/B10-L3-class-mech.md`：

  1. 取件口：`..data.battle_rules`(MECH_CASH/PASSIVE_PROC/BAR_INJECT_FIELDS) / `..content_rules.skills`
     → 包内单源 `class_data.py` / `..apply._SKILL_LOOKUP`
  2. 动作注册：真源 `install()` 里的闭包 + `register_action(...)` 调用 → 包内模块级函数 +
     `@register_action("<原名>")` 装饰器（**import 即注册**，39 个动作）
  3. `apply_class_passives` / `apply_class_mech` 里那两行 `install()` → 包内 `LAST_ERRORS.clear()`
     （「最近一次装配的失败步」排障语义，不写 actor、不进存档）+ bar/cond 缺件记 `LAST_ERRORS`
  4. 包侧新增 `LAST_ERRORS` / `_note_error`（真源无，见上）与 `__all__`

本壳只做三件事：

  1. **加载包**（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）——
     包内模块 import 期即注册 39 个动作，与真源「import 本文件即注册」逐字等价
  2. **同名单 re-export**（真源 14 个顶层名一个不少；符号名 / 签名 / 默认值一字不变，
     生产消费者 `services/battle_bridge.py:249` 与 33 处测试 import 点零改动）
  3. `install()` 保名：真源语义 = 幂等注册动作；包内注册已由 import 完成 → 本壳 `install()`
     是幂等空委托（`tests/test_v181_channel_when.py:116` 直调它）

⚠️ 真源独有名 `install()` / `_registered`：`install` 由本壳保名（上），`_registered` 随注册机制
一并消失（零外部读取点 —— 全仓 grep 无 `class_mech_proc._registered`）。

✅ 零消费者判定（步骤 A 实测，2026-09-13）：
  · 生产 1 处：`game/services/battle_bridge.py:249`（`from .class_mech_proc import apply_class_mech`）
  · 测试 33 处（`from game.services[.class_mech_proc] import …`；`CM.`/`CMP.` 属性面 =
    `apply_class_mech`(57) · `apply_class_channels`(2) · `install`(2)）→ 全部由本壳保名
  · `game/services/__init__.py` **未导出**本模块
  · 文档/脚本 12+ 处引用均为**注释路径**（`docs/*.md` / `data/battle_rules.py` 注释 /
    `scripts/export_game_package.py` 说明文字），非 import

逐字节等价证据：`overnight/b10_l3_snap.py`（27 例 · actor 全量 dump · 真实战斗渲染文本 ·
引擎动作注册表 · 私有库行数/内容 sha）—— 改前/改后同 sha256 + 字节数。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（失败抛）

_bootstrap.package_apply()
from content.mech import class_mech as _pkg                  # noqa: E402  ← 唯一实现（import 即注册 39 动作）

# ---------------------------------------------------------------- 同名单 re-export（真源 14 名）
_registered = True          # 真源模块级状态位（注册已由包 import 完成；本壳仅为保形）
_mech_cash_rules = _pkg._mech_cash_rules
_effect_rules = _pkg._effect_rules
_CHANNEL_EVENTS = _pkg._CHANNEL_EVENTS
apply_class_channels = _pkg.apply_class_channels
_learned_mech_skills = _pkg._learned_mech_skills
_learned_proc = _pkg._learned_proc
_learned_proc_param = _pkg._learned_proc_param
_passive_proc_rules = _pkg._passive_proc_rules
apply_class_passives = _pkg.apply_class_passives
_res_ge_ok = _pkg._res_ge_ok
_has_effect_ok = _pkg._has_effect_ok
_when_ok = _pkg._when_ok
_merge_agg_entry = _pkg._merge_agg_entry
apply_class_mech = _pkg.apply_class_mech


def install() -> None:
    """注册通用兑现执行器（真源语义：幂等；模块 import 即注册）。

    ★ B10-L3：注册实体 = 包内 `content/mech/class_mech.py` 的 39 个 `@register_action`
    装饰器（上面 `_bootstrap.package_apply()` → 包 import 时已完成，幂等）。
    本函数保留为**空委托**：真源 import 期那次 `install()` 的等价物就是「包已加载」。
    """
    return None
