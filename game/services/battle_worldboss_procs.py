# -*- coding: utf-8 -*-
"""世界 Boss 内容装配层 battle_worldboss_procs（2026-09-11 接线修复）。

## 修的是什么

`gm_伤害 <倍率>` 指令（`game/commands/gm.py::gm_boss_dmg`）把倍率写进
`event_state["boss_dmg_{qq}"]`，讨伐世界 Boss 时由 `combat.py` 读出并作为
`Battle(..., dmg_mult=<倍率>, pet=...)` 构造参数传给引擎。

**battle2 引擎的 `Battle.__init__` 只把 `dmg_mult` 存成 `self.dmg_mult`、从不读取**
（旧引擎 battle.py `_boss_dmg_filter` 里那段 `if btype == "worldboss" and self.dmg_mult != 1.0:
dmg = int(dmg * self.dmg_mult)` 没跟着迁过来）——于是 GM 设置的世界 Boss 伤害倍率
**静默失效**，面板还说「『讨伐』时生效」。

同一行传的 `pet=db.pet_get(qq)` 同理：引擎只存不读，宠物在世界 Boss 战里从未参战
（属「随从 actor 工厂」缺口，见 docs/REFACTOR_v181_GAP_CLOSURE_PLAN.md；那条线单独做）。

## 怎么修的

**零引擎改动**——走引擎既有的 `taken_calc` 承伤乘区事件（`landing.deal_damage` 里
fire，读 `battle._fire_ctx["mult"]`）。语义与旧 `_boss_dmg_filter` 一致：
乘在「玩家打 Boss」这一侧的伤害上（倍率 >1 = 更疼，<1 = 更肉）。

挂载形态：在 Boss actor 上声明 `triggers["taken_calc"] = [{"action": "wb_gm_dmg_mult",
"factor": N}]`（乘区动作族与 `passive_taken_reduce` 同构）。倍率 = 1.0 时不挂（零噪音）。
"""
from __future__ import annotations

from saintess_engine.battle.effects import register_action


@register_action("wb_gm_dmg_mult")
def wb_gm_dmg_mult(battle, caster, target, params, logs):
    """taken_calc 承伤乘区 ×factor（worldboss GM 伤害倍率）。

    引擎零知识：只读 params 的数字，不认「世界 Boss」这个概念。
    factor 缺省/无效/等于 1.0 → 无此行为（不写 ctx.mult）。
    """
    ctx = getattr(battle, "_fire_ctx", None)
    if ctx is None:
        return
    try:
        f = float(params.get("factor", 1.0) or 1.0)
    except (TypeError, ValueError):
        return
    if f == 1.0:
        return
    ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * f


def apply_gm_dmg_mult(actor: dict, mult: float) -> bool:
    """把 GM 世界 Boss 伤害倍率挂到 actor 的 taken_calc 乘区。

    幂等（同 actor 重复调用只保留一条声明，值就地更新）；mult 无效或 =1.0 → 不挂并
    返回 False。返回是否挂上。
    """
    if not isinstance(actor, dict):
        return False
    try:
        m = float(mult or 1.0)
    except (TypeError, ValueError):
        return False
    trig = actor.setdefault("triggers", {})
    lst = trig.setdefault("taken_calc", [])
    for e in lst:
        if isinstance(e, dict) and e.get("action") == "wb_gm_dmg_mult":
            if m == 1.0:
                lst.remove(e)          # 倍率被 GM 改回 1 → 撤掉声明
                return False
            e["factor"] = m
            return True
    if m == 1.0:
        return False
    lst.append({"action": "wb_gm_dmg_mult", "factor": m})
    return True
