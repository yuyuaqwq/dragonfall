# -*- coding: utf-8 -*-
"""saintess_engine 技能条件倍率装配层 battle_cond_procs（v181 cond 接线）。

背景：技能数据 `cond={"type":…,"mult":…}` 的在战判定原走 `core/battle_conds.py`
的 `COND_CHECKS` 注册表（旧 battle.py `_cond_mult` 消费）。saintess_engine 里该注册表**零消费方**
（`battle_bridge.py` 明确标注「battle_modes/battle_conds 为 v139 遗留空壳」），且条件
函数读的是旧引擎 API（`battle._hit_tgt()` / `battle._melody`，saintess_engine 均无）——结果是
技能条件倍率静默失效（`actions.py` 里 `cond_mult = 1.0  # N2b 补，恒 1.0 起步`）。
数据受影响：5 条技能（先手/敌方减益/敌方破防/旋律增益系/旋律强度）。

本模块把条件倍率接回 saintess_engine 乘区钩子（**引擎零改动**，走既有装配层扩展动作模式，
对齐 `we_dmg_mult_cond`）：
- `skill_cond_mult` 挂 dmg_calc / heal_calc：读事件技能 `info["cond"]` → 查谓词表 →
  命中则 `battle._fire_ctx["mult"] *= skill_cond_mult(cond, lv, info)`（与面板
  「条件 ×N」显示同源；未注册 type / 无 cond = 静默不生效，同旧引擎未知 type 语义）
- 谓词表 `COND_PREDICATES`：type → fn(battle, actor, target, cond) -> bool
  （加条件类型 = 加一行注册，技能数据直接可用）

装配：`apply_cond_procs(actor)` 扫已学技能——有带 cond 的技能才挂（学什么挂什么，零噪音）。

★ B10-L4 收口（2026-09-13）：本文件 = **委托薄壳**
--------------------------------------------------------
原实现（3 张常量元组 + `COND_PREDICATES` + `register_cond` + `_spd_of` + 5 个谓词 +
`skill_cond_mult` 动作 + `apply_cond_procs` 装配）已逐字在包内
`games/orlandia/content/mech/cond_procs.py`（P4-D2 搬入；`apply_cond_procs` 为 P4-D2b 追加）。
逐函数对拍结论（`overnight/_b10_l4_recon.py`）：9 个同名函数里 7 个「去 docstring 后逐行相同」，
2 个（`skill_cond_mult_act` / `apply_cond_procs`）**只差 1 行**技能表 import 路径
（宿主 `..content_rules.skills` → 包内 `..apply._SKILL_LOOKUP`），行为对拍 139/139 相等
（`overnight/_b10_l4_probe_BEFORE.txt`）⇒ 宿主那份是**纯冗余副本**。

本文件只「再导出 + 一行委托」，名字 / 签名一字不变 —— 调用点零改动：

    services/class_mech_proc.py:2370    from .battle_cond_procs import apply_cond_procs
    tests/test_battle_cond_procs.py     CP.COND_PREDICATES
    tests/test_apply_game_content.py    COND（⑤ 条件乘区）

**唯一形态差异**：本模块不再 `@register_action("skill_cond_mult")`（动作注册真源 = 包内
`content/mech/cond_procs.py`，由 `content/apply.py` import 即注册）。模块级常量 / 谓词表 /
私有谓词函数走 PEP 562 惰性再导出（import 期不碰包、不改宿主 import 顺序副作用）。

等价证据：`overnight/b10_l4_snap.py`（改造前后逐字节快照）·
          `overnight/B10-L4-cond-food-wb-bridge.md`。
"""
from __future__ import annotations

_PKG = None          # 包内 `content.mech.cond_procs` 模块缓存（惰性——import 期不碰包）


def _pkg():
    """包内 `content.mech.cond_procs`（条件乘区唯一实现源）：首调加载包，之后走缓存。

    包装载口 = `game/bootstrap.package_apply()`（本进程唯一，幂等）。失败**抛**、不静默降级
    （条件乘区静默缺失 = 技能面板承诺「条件 ×N」实机不生效，比报错难查得多）。
    """
    global _PKG
    if _PKG is None:
        from .. import bootstrap as _bootstrap
        _bootstrap.package_apply()
        from content.mech import cond_procs as _m
        _PKG = _m
    return _PKG


def apply_cond_procs(actor: dict) -> None:
    """装配：扫已学技能 → 存在带 cond 的技能才挂 dmg_calc/heal_calc 条件乘区。

    ★ B10-L4：委托薄壳，实现（逐字）在包内 `content/mech/cond_procs.apply_cond_procs`。
    """
    return _pkg().apply_cond_procs(actor)


def skill_cond_mult_act(battle, caster, target, params, logs):
    """dmg_calc / heal_calc：技能 cond 条件倍率 → 累乘 `battle._fire_ctx["mult"]`。

    ★ B10-L4：委托薄壳，实现（逐字）在包内 `content/mech/cond_procs.skill_cond_mult_act`。
    """
    return _pkg().skill_cond_mult_act(battle, caster, target, params, logs)


def register_cond(key):
    """条件类型注册（加类型 = 加一行；未注册 type 静默不生效）。

    ★ B10-L4：委托薄壳 → 包内 `COND_PREDICATES` 唯一真源（本函数与包内那份同写一个表）。
    """
    return _pkg().register_cond(key)


# 模块级常量 / 谓词表 / 私有谓词函数：PEP 562 惰性再导出（import 期不碰包）
_LAZY = (
    "_DEBUFF_KEYS", "_DOT_KEYS", "_MELODY_BUFF_KINDS", "COND_PREDICATES",
    "_spd_of", "_p_player_first", "_p_enemy_debuff", "_p_enemy_broken",
    "_p_melody_buff", "_p_melody_stacks",
)


def __getattr__(name):
    """PEP 562：把上面那批名字转发到包内那份（同一对象/同一表 —— 双源已收口）。"""
    if name in _LAZY:
        return getattr(_pkg(), name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


__all__ = ["apply_cond_procs", "skill_cond_mult_act", "register_cond", "COND_PREDICATES"]
