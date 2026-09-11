# -*- coding: utf-8 -*-
"""battle2 技能条件倍率装配层 battle2_cond_procs（v181 cond 接线）。

背景：技能数据 `cond={"type":…,"mult":…}` 的在战判定原走 `core/battle_conds.py`
的 `COND_CHECKS` 注册表（旧 battle.py `_cond_mult` 消费）。battle2 里该注册表**零消费方**
（`battle2_bridge.py` 明确标注「battle_modes/battle_conds 为 v139 遗留空壳」），且条件
函数读的是旧引擎 API（`battle._hit_tgt()` / `battle._melody`，battle2 均无）——结果是
技能条件倍率静默失效（`actions.py` 里 `cond_mult = 1.0  # N2b 补，恒 1.0 起步`）。
数据受影响：5 条技能（先手/敌方减益/敌方破防/旋律增益系/旋律强度）。

本模块把条件倍率接回 battle2 乘区钩子（**引擎零改动**，走既有装配层扩展动作模式，
对齐 `we_dmg_mult_cond`）：
- `skill_cond_mult` 挂 dmg_calc / heal_calc：读事件技能 `info["cond"]` → 查谓词表 →
  命中则 `battle._fire_ctx["mult"] *= E.skill_cond_mult(cond, lv, info)`（与面板
  「条件 ×N」显示同源；未注册 type / 无 cond = 静默不生效，同旧引擎未知 type 语义）
- 谓词表 `COND_PREDICATES`：type → fn(battle, actor, target, cond) -> bool
  （加条件类型 = 加一行注册，技能数据直接可用）

装配：`apply_cond_procs(actor)` 扫已学技能——有带 cond 的技能才挂（学什么挂什么，零噪音）。
"""
from __future__ import annotations

from battle2.effects import register_action

# 敌方减益键（控制/属性降）；DOT/印记类走 effects 层数判定
_DEBUFF_KEYS = ("def_down", "spd_down", "mon_atk_down", "atk_down",
                "stun", "freeze", "silence")
_DOT_KEYS = ("poison", "burn", "bleed", "mark")
# 旋律增益系（咏叹调 desc「当前旋律为增益系时 ×1.3」）
_MELODY_BUFF_KINDS = ("atk", "def", "spd", "atk_matk", "all")

COND_PREDICATES: dict = {}


def register_cond(key):
    """条件类型注册（加类型 = 加一行；未注册 type 静默不生效）。"""
    def deco(fn):
        COND_PREDICATES[key] = fn
        return fn
    return deco


def _spd_of(battle, actor) -> float:
    if not isinstance(actor, dict):
        return 0.0
    try:
        from battle2 import stats as S
        st = S.actor_stats(battle, actor) or {}
        return float(st.get("spd", 0) or 0)
    except Exception:
        return float(actor.get("spd", 0) or 0)


@register_cond("player_first")
def _p_player_first(battle, actor, target, cond) -> bool:
    """先手：速度高于目标（v2.0）。"""
    return _spd_of(battle, actor) > _spd_of(battle, target)


@register_cond("enemy_debuff")
def _p_enemy_debuff(battle, actor, target, cond) -> bool:
    """敌方有减益（控制/属性降 + 目标级 DOT/印记层）。"""
    if not isinstance(target, dict):
        return False
    ef = target.get("effects") or {}
    if any(k in ef for k in _DEBUFF_KEYS):
        return True
    for k in _DOT_KEYS:
        e = ef.get(k)
        if isinstance(e, dict) and int(e.get("stacks", 0) or 0) > 0:
            return True
        if e:  # 无 stacks 结构的条目存在即算减益（控制型）
            return True
    deb = target.get("debuffs") or {}
    return any(int((deb.get(k) or {}).get("n", 0) or 0) > 0 for k in _DOT_KEYS)


@register_cond("enemy_broken")
def _p_enemy_broken(battle, actor, target, cond) -> bool:
    """敌方被破防/震慑中（破绽条触发态）——与 bar_trigger 后状态同源。

    条状态载体 = 目标 effects[BAR_STATE_PREFIX+shaken]；读取前先结算到当刻
    （衰减时间制：不结算会读到过期值）。
    """
    if not isinstance(target, dict):
        return False
    from ..core.battle_bars import bar_settle, bar_effect_key
    _now = float(getattr(battle, "_now", 0.0) or 0.0)
    bar_settle(target, "shaken", _now)
    bs = (target.get("effects") or {}).get(bar_effect_key("shaken"))
    if not isinstance(bs, dict):
        return False
    return (int(bs.get("trigger_count", 0) or 0) > 0
            and float(bs.get("immune_until", 0.0) or 0.0) > _now)


@register_cond("melody_buff")
def _p_melody_buff(battle, actor, target, cond) -> bool:
    """施法者当前旋律为增益系（读 effects.melody_state.kind）。

    注意：旧 battle_conds 读 `battle._melody["kind"]`（旧引擎载体，battle2 无写入方）；
    battle2 真实载体 = 施法者 `effects["melody_state"]`（class_mech_proc.class_melody_act 写）。
    """
    if not isinstance(actor, dict):
        return False
    st = (actor.get("effects") or {}).get("melody_state") or {}
    return st.get("kind") in _MELODY_BUFF_KINDS


@register_cond("melody_stacks")
def _p_melody_stacks(battle, actor, target, cond) -> bool:
    """施法者旋律强度 ≥ stacks（旧读 `_melody["stack"]`，battle2 实键为 `stacks`）。"""
    if not isinstance(actor, dict):
        return False
    st = (actor.get("effects") or {}).get("melody_state") or {}
    need = int(cond.get("stacks", 4) or 4)
    return int(st.get("stacks", 0) or 0) >= need


@register_action("skill_cond_mult")
def skill_cond_mult_act(battle, caster, target, params, logs):
    """dmg_calc / heal_calc：技能 cond 条件倍率 → 累乘 battle._fire_ctx["mult"]。"""
    ctx = getattr(battle, "_fire_ctx", None)
    if not isinstance(ctx, dict):
        return
    info = ctx.get("info") or {}
    cond = info.get("cond")
    if not isinstance(cond, dict):
        return  # 无字段 = 不启用
    fn = COND_PREDICATES.get(cond.get("type"))
    if fn is None:
        return  # 未注册类型：静默不生效（不给断言/不崩）
    actor = ctx.get("actor") or caster
    tgt = ctx.get("target")
    if tgt is None:
        tgt = target
    try:
        if not fn(battle, actor, tgt, cond):
            return
    except Exception:
        return  # 判定异常不阻断战斗
    try:
        from .. import engine as E
        name = info.get("name") or ""
        lv = E.skill_level_of(actor, name) if (actor or {}).get("class_name") else 1
        mult = float(E.skill_cond_mult(cond, max(1, int(lv or 1)), info) or 1.0)
    except Exception:
        mult = float(cond.get("mult", 1.0) or 1.0)
    if mult == 1.0:
        return
    ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * mult
    logs.append(f"✨ 条件达成【{cond.get('type')}】×{mult:g}")


def apply_cond_procs(actor: dict) -> None:
    """装配：扫已学技能 → 存在带 cond 的技能才挂 dmg_calc/heal_calc 条件乘区。"""
    cn = actor.get("class_name") or ""
    names = actor.get("learned_skills") or []
    if not cn or not names:
        return
    from .. import engine as E
    has_cond = False
    for s in names:
        try:
            info = E.skill_info(cn, s)
        except Exception:
            info = None
        if info and isinstance(info.get("cond"), dict):
            has_cond = True
            break
    if not has_cond:
        return
    trig = actor.setdefault("triggers", {})
    for ev in ("dmg_calc", "heal_calc"):
        lst = trig.setdefault(ev, [])
        if not any(isinstance(e, dict) and e.get("action") == "skill_cond_mult"
                   for e in lst):
            lst.append({"action": "skill_cond_mult"})
