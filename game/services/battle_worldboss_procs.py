# -*- coding: utf-8 -*-
"""世界 Boss 内容装配层 battle_worldboss_procs —— ★ B10-L4 起 = **委托薄壳**。

## 修的是什么（历史；保留原文，实现已迁包内）

`gm_伤害 <倍率>` 指令（`game/commands/gm.py::gm_boss_dmg`）把倍率写进
`event_state["boss_dmg_{qq}"]`，讨伐世界 Boss 时由 `combat.py` 读出并作为
`Battle(..., dmg_mult=<倍率>, pet=...)` 构造参数传给引擎。

**battle2 引擎的 `Battle.__init__` 只把 `dmg_mult` 存成 `self.dmg_mult`、从不读取**
（旧引擎 battle.py `_boss_dmg_filter` 里那段 `if btype == "worldboss" and self.dmg_mult != 1.0:
dmg = int(dmg * self.dmg_mult)` 没跟着迁过来）——于是 GM 设置的世界 Boss 伤害倍率
**静默失效**，面板还说「『讨伐』时生效」。

修法 = **零引擎改动**：走引擎既有的 `taken_calc` 承伤乘区事件（`landing.deal_damage`
里 fire，读 `battle._fire_ctx["mult"]`）。挂载形态：Boss actor 上声明
`triggers["taken_calc"] = [{"action": "wb_gm_dmg_mult", "factor": N}]`；倍率 1.0 时不挂。

## ★ B10-L4 收口（2026-09-13）

实现真源（动作 `wb_gm_dmg_mult` **+** 装配入口 `apply_gm_dmg_mult`）= 包内
`games/orlandia/content/mech/worldboss.py`（同处一个模块）。本文件只「再导出 + 一行委托」，
名字 / 签名 / 语义 / 返回一字不变 —— 调用点零改动：

    commands/combat.py:2392               WBP.apply_gm_dmg_mult(actor, mult)   （生产）
    tests/test_v181_worldboss_gm_dmg.py   WBP.apply_gm_dmg_mult / WBP.wb_gm_dmg_mult

**唯一形态差异**：本模块不再 `@register_action("wb_gm_dmg_mult")`（动作注册真源 = 包内那份，
由 `content/apply.py` import 即注册；宿主进程的包加载口 = `game.bootstrap.package_apply()`）。
包加载**惰性**（首调才加载）——不在 import 期改变宿主 import 顺序副作用。

等价证据：`overnight/b10_l4_snap.py`（改造前后逐字节快照，含 wb 全分支）·
          `overnight/_b10_l4_recon.py`（宿主 vs 包内逐函数对拍）·
          `overnight/B10-L4-cond-food-wb-bridge.md`。
"""
from __future__ import annotations

_PKG = None          # 包内 `content.mech.worldboss` 模块缓存（惰性——import 期不碰包）


def _pkg():
    """包内 `content.mech.worldboss`（世界 Boss 乘区+装配唯一实现源）：首调加载，之后走缓存。

    包装载口 = `game/bootstrap.package_apply()`（本进程唯一，幂等）。失败**抛**、不静默降级
    （静默降级 = GM 倍率又回到「面板承诺、实机失效」的老毛病，比报错难查得多）。
    """
    global _PKG
    if _PKG is None:
        from .. import bootstrap as _bootstrap
        _bootstrap.package_apply()
        from content.mech import worldboss as _m
        _PKG = _m
    return _PKG


def wb_gm_dmg_mult(battle, caster, target, params, logs):
    """taken_calc 承伤乘区 ×factor（worldboss GM 伤害倍率）—— 委托薄壳，实现见包内。"""
    return _pkg().wb_gm_dmg_mult(battle, caster, target, params, logs)


def apply_gm_dmg_mult(actor: dict, mult: float) -> bool:
    """把 GM 世界 Boss 伤害倍率挂到 actor 的 taken_calc 乘区 —— 委托薄壳，实现见包内。

    幂等（同 actor 重复调用只保留一条声明，值就地更新）；mult 无效或 =1.0 → 不挂并返回 False。
    """
    return _pkg().apply_gm_dmg_mult(actor, mult)


__all__ = ["wb_gm_dmg_mult", "apply_gm_dmg_mult"]
