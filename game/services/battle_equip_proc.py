# -*- coding: utf-8 -*-
"""saintess_engine 装备特效/词条装配层（game/services/battle_equip_proc.py）—— B10-L1 **薄壳**。

唯一实现（真源）= 内容包 `content/mech/equip.py`：事件映射 / 数据读口 / 词条分档 /
武器特效与传说特效翻译器 / `weapon_triggers` / `affix_triggers` / `legendary_triggers` /
`apply_to_actor` / `install_ext_actions`（全部逐字在包内；与宿主旧版差异仅在「取件层」：
数据表读写口 `..data.*` → 包内 `content/data/*.json` + `we_data`，已实测逐值相同）。

本文件只做：包加载口 + 全量再导出 + 两个装配入口一行委托 + `__getattr__` 兜底。
`game/services/__init__.py` / `battle_bridge.py` / `battle_food_proc.py` / `tests/*` 的
import 点与名字零变化（`install_ext_actions()` / `apply_to_actor(actor)` 签名一字不变）。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                  # 唯一包加载口（幂等，失败抛）

from content.mech import equip as _E                        # noqa: E402  包内唯一实现

_PKG_MOD = "equip"


# ------------------------------------------------------------
# 装配入口（名字/签名**一字不变**，一行委托）——`battle_bridge.py:244`
# `from .battle_equip_proc import apply_to_actor`、`battle_food_proc.py:220`
# `install_ext_actions`、以及门禁 `test_package_mech_ports` 都按名取。
# ------------------------------------------------------------
def install_ext_actions() -> None:
    """注册族扩展动作（形态 2）——委托包内（幂等；包内实现与真源逐字一致）。"""
    return _E.install_ext_actions()


def apply_to_actor(actor: dict) -> None:
    """把装备特效+词条装配进 actor（幂等）——委托包内（实现逐字在 `content/mech/equip.py`）。"""
    return _E.apply_to_actor(actor)


# ---- 模块级名字全量再导出（常量 / 数据字典 / 翻译器 / 清单提取 …）----
_EVENT_MAP = _E._EVENT_MAP
_UNKNOWN_EVENTS = _E._UNKNOWN_EVENTS
_UNSUPPORTED_LEGENDARY = _E._UNSUPPORTED_LEGENDARY
_JUDGE_ARCANE = _E._JUDGE_ARCANE
_AFFIX_TIER_KEY = _E._AFFIX_TIER_KEY
_AFFIX_TRANSLATORS = _E._AFFIX_TRANSLATORS
_AFFIX_RES_GAIN_ON = _E._AFFIX_RES_GAIN_ON
_AFFIX_RES_GAIN_IDS = _E._AFFIX_RES_GAIN_IDS
_HEAL_AMP_KEYS = _E._HEAL_AMP_KEYS
_START_TRANSLATORS = _E._START_TRANSLATORS
_LEGENDARY_TRANSLATORS = _E._LEGENDARY_TRANSLATORS
_known_engine_events = _E._known_engine_events
map_event = _E.map_event
_we_data = _E._we_data
_we_config = _E._we_config
equipped_weapon_keys = _E.equipped_weapon_keys
_affix_data = _E._affix_data
equipped_affix_ids = _E.equipped_affix_ids
_apply_cap_bonus = _E._apply_cap_bonus
_apply_cost_bonus = _E._apply_cost_bonus
_apply_bonus_domains = _E._apply_bonus_domains
_tier_value = _E._tier_value
_affix_effect_final = _E._affix_effect_final
_register_affix = _E._register_affix
_affix_chance_of = _E._affix_chance_of
_affix_hit_ev = _E._affix_hit_ev
_af_shield = _E._af_shield
_af_regen = _E._af_regen
_af_meditate = _E._af_meditate
_af_bleed = _E._af_bleed
_af_armor_break = _E._af_armor_break
_af_element_fire = _E._af_element_fire
_af_element_ice = _E._af_element_ice
_af_element_thunder = _E._af_element_thunder
_af_combo = _E._af_combo
_af_charge = _E._af_charge
_af_pierce = _E._af_pierce
_af_counter = _E._af_counter
_af_tenacity_cc = _E._af_tenacity_cc
_af_dmg_reduce = _E._af_dmg_reduce
_af_execute = _E._af_execute
_af_hunt = _E._af_hunt
_af_break_magic = _E._af_break_magic
_af_dragon_aw = _E._af_dragon_aw
_translate_affix_res_gain = _E._translate_affix_res_gain
_af_boiling_blood = _E._af_boiling_blood
_af_energy_tide = _E._af_energy_tide
_af_swift_tailwind = _E._af_swift_tailwind
_af_purify = _E._af_purify
_af_finisher = _E._af_finisher
_af_ember_brand = _E._af_ember_brand
_af_combo_ward = _E._af_combo_ward
affix_triggers_for_key = _E.affix_triggers_for_key
_translate_shield_start = _E._translate_shield_start
_translate_buff_start = _E._translate_buff_start
_translate_shield_abyss = _E._translate_shield_abyss
_translate_regen_turn_start = _E._translate_regen_turn_start
_translate_stack_hit = _E._translate_stack_hit
_translate_we = _E._translate_we
_translate_dot_hit = _E._translate_dot_hit
_translate_reflect_taken = _E._translate_reflect_taken
_translate_buff_hit_self = _E._translate_buff_hit_self
_translate_next_atk_mark = _E._translate_next_atk_mark
_translate_trinity = _E._translate_trinity
_translate_retort_mark = _E._translate_retort_mark
_translate_shield_taken_cd = _E._translate_shield_taken_cd
_translate_shield_cond = _E._translate_shield_cond
_translate_control = _E._translate_control
_translate_death_dance = _E._translate_death_dance
_translate_act_done_slow = _E._translate_act_done_slow
_translate_extra_dmg = _E._translate_extra_dmg
_translate_dusk_blade = _E._translate_dusk_blade
_translate_legend_mult = _E._translate_legend_mult
_translate_first_turn_dodge = _E._translate_first_turn_dodge
_cond_mult = _E._cond_mult
_star_slayer = _E._star_slayer
_arcane_firmament = _E._arcane_firmament
_stack_pair = _E._stack_pair
triggers_for_key = _E.triggers_for_key
_legendary_data = _E._legendary_data
equipped_legendary_ids = _E.equipped_legendary_ids
_note_unsupported_legendary = _E._note_unsupported_legendary
legendary_triggers_for_key = _E.legendary_triggers_for_key
legendary_triggers = _E.legendary_triggers
weapon_triggers = _E.weapon_triggers
affix_triggers = _E.affix_triggers


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
