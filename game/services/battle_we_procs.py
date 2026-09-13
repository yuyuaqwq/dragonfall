# -*- coding: utf-8 -*-
"""saintess_engine 装备特效族扩展动作（game/services/battle_we_procs.py）—— B10-L1 **薄壳**。

唯一实现（真源）= 内容包 `content/mech/we_procs.py`：27 个 `@register_action` 动作 +
模块级助手 + 数据字典 + `ensure_registered()`（全部逐字在包内）。

本文件只做三件事：
1. 包加载口（`game.bootstrap.package_apply()`，幂等；把包根插进 sys.path）；
2. `import` 包内族模块 —— **动作注册发生在这一步**（引擎 `register_action` 是模块级
   装饰器，import 即注册；它是**覆盖式**注册，本文件若再声明一遍就是第二个副本）；
3. 全量再导出 + `__getattr__` 兜底 —— `game/services/__init__.py` /
   `battle_equip_proc` / `tests/*` 的 import 点与名字零变化（签名一字不变）。

⚠️ 已知红：`tests/test_package_mech_ports.py` 的 we_procs 条目拿**本文件源码里的
   `@register_action` 名字集合**当「真源」，收口后本文件不再有装饰器声明 → 该条报红
   （动作名集合 0 vs 27）。这不是行为回归（快照逐字节等价，见
   `overnight/B10-L1-we-equip.md`）：双源已收口，该门禁的「宿主真源」前提消失，
   需收口方把该族改成「比包内自证」或删条目。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                  # 唯一包加载口（幂等，失败抛）

from content.mech import we_procs as _E                     # noqa: E402  ← import 即注册 27 动作

_PKG_MOD = "we_procs"

# ---- 模块级名字全量再导出（对象同一：`_roll` / `_DOT_LOG` / 27 个 we_* 动作 …）----
_DOT_LOG = _E._DOT_LOG
_REFLECT_LOG = _E._REFLECT_LOG
_SHIELD_TAKEN_LOG = _E._SHIELD_TAKEN_LOG
_SHIELD_COND_LOG = _E._SHIELD_COND_LOG
_EXTRA_LOG = _E._EXTRA_LOG
_CONTROL_LOG = _E._CONTROL_LOG
_MULT_TAG = _E._MULT_TAG
_ACT_DONE_SLOW_LOG = _E._ACT_DONE_SLOW_LOG
_AFFIX_HIT_LOG = _E._AFFIX_HIT_LOG
_AFFIX_TAKEN_LOG = _E._AFFIX_TAKEN_LOG
_roll = _E._roll
_hit_target = _E._hit_target
_is_boss = _E._is_boss
_add_stacks = _E._add_stacks
we_dot = _E.we_dot
we_reflect = _E.we_reflect
we_hit_slow = _E.we_hit_slow
we_shield_taken = _E.we_shield_taken
we_guardian_will = _E.we_guardian_will
_add_owner_shield = _E._add_owner_shield
we_shield_cond = _E.we_shield_cond
_crit_flag = _E._crit_flag
we_abyss = _E.we_abyss
_owner_stats = _E._owner_stats
_target_def_stats = _E._target_def_stats
_calc = _E._calc
we_extra_dmg = _E.we_extra_dmg
we_mana_once = _E.we_mana_once
_control_target = _E._control_target
_freeze = _E._freeze
_slow = _E._slow
we_control = _E.we_control
_bump_control_state = _E._bump_control_state
we_dmg_mult_cond = _E.we_dmg_mult_cond
we_taken_mult_cond = _E.we_taken_mult_cond
_state_cap = _E._state_cap
we_stack_prod = _E.we_stack_prod
we_amp_consume = _E.we_amp_consume
we_combo_stack = _E.we_combo_stack
we_combo_end = _E.we_combo_end
we_death_pool_add = _E.we_death_pool_add
we_death_pool_pay = _E.we_death_pool_pay
we_act_done_slow = _E.we_act_done_slow
we_affix_dot = _E.we_affix_dot
we_affix_defdown = _E.we_affix_defdown
we_affix_element = _E.we_affix_element
we_affix_bonus = _E.we_affix_bonus
we_affix_counter = _E.we_affix_counter
we_affix_tenacity = _E.we_affix_tenacity
we_affix_res_gain = _E.we_affix_res_gain
_target_gain_keys = _E._target_gain_keys
we_affix_purify = _E.we_affix_purify
ensure_registered = _E.ensure_registered


# ------------------------------------------------------------
# 兜底转发：任何**未静态再导出**的名字（含 `_EXT_LOADED` / `_WE_TABLE` /
# `_AFFIX_TABLE` / `_LEGENDARY_TABLE` 这类会被重新绑定的名字）实时取包内那份 ——
# 静态别名对「可变量」会拿到导入瞬间的旧值（None / False），实时取才与改造前等价。
# ------------------------------------------------------------
def __getattr__(name):
    """模块属性兜底 → 包内唯一实现（PEP 562）。"""
    try:
        return getattr(_E, name)
    except AttributeError:
        raise AttributeError(
            "module %r has no attribute %r（包内 content/mech/%s.py 也没有；"
            "B10-L1 后本文件只是薄壳）" % (__name__, name, _PKG_MOD)) from None


def __dir__():
    return sorted(set(globals()) | set(dir(_E)))
