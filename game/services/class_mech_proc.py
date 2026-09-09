# -*- coding: utf-8 -*-
"""battle2 职业机制装配层 class_mech_proc（v181.M R1a 起）——技能 mech 兑现动作。

蓝图：docs/REFACTOR_v181_CLASS_MECH_ASSEMBLY.md（40 mech 分派矩阵；引擎零职业知识）。

技能 mech 三层现状：
- 叠层写入（命中攒层 zhan_yi/lian_duan/arcane...）✅ effects._mech_to_effect 已通
- 兑现/消费（终结技/引爆/倾泻）⬜ 本模块补（双通道，全部装配层）：
    通道 1 dmg_calc 乘区（伤害前修正）——actor.triggers 挂 dmg_calc 效果
    通道 2 命中后清层/附加——actor.triggers 挂 skill_hit 效果
- 渠道喂养（on_* 攒层）→ R2

R1a 样板 = finisher（刺客终结技族）：
  终结·割喉/终结·处刑/暗影绞杀 desc 共性「连段越高伤害越高（每段 +10%），结算后
  连段归零」（旧 battle_mech._m_finisher：mult = 1+0.10×连段；info.per_stack 覆盖
  系数——链舞被动 finisher_up +6%；keep_on_kill 不清层）。
  特例待接：终结·处刑「连段 ≥4 必定暴击」（crit roll 早于 dmg_calc，需更早钩子，R1a 记缺口）。

装配点：命令层开战仪式（combat._open_battle2/PVP/tower）与 equip_proc.apply_to_actor
并列调用 apply_class_mech(actor)。
"""

from __future__ import annotations

_registered = False


def install() -> None:
    """注册兑现动作（幂等；模块被装配方 import 后调用，或底部自动执行）。"""
    global _registered
    if _registered:
        return
    from ..battle2.effects import register_action

    @register_action("mech_finisher_mult")
    def mech_finisher_mult(battle, caster, target, params, logs):
        """dmg_calc 乘区：技能 mech=finisher → 伤害 ×(1 + per×连段层)。"""
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        info = ctx.get("info") or {}
        if info.get("mech") != "finisher":
            return
        actor = ctx.get("actor") or caster
        ef = (actor.get("effects") or {}).get("lian_duan")
        n = int(ef.get("stacks", 0) or 0) if isinstance(ef, dict) else 0
        per = float(info.get("per_stack") or 0.10)  # 链舞被动 finisher_up 由技能 info 覆盖
        mult = 1.0 + per * n
        ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * mult
        logs.append(f"🔪 终结技！连段 {n} 段，伤害 ×{mult:.2f}")

    @register_action("mech_finisher_clear")
    def mech_finisher_clear(battle, caster, target, params, logs):
        """skill_hit 命中后：终结技结算 → 连段归零（keep_on_kill 技能保留）。"""
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        info = ctx.get("info") or {}
        if info.get("mech") != "finisher":
            return
        if info.get("keep_on_kill"):
            return
        actor = ctx.get("actor") or caster
        ef = actor.get("effects") or {}
        entry = ef.get("lian_duan")
        if isinstance(entry, dict):
            entry["stacks"] = 0
        logs.append("🔗 连段归零")

    _registered = True


def _learned_mech_skills(actor: dict) -> list:
    """actor 已学技能中含 mech 的技能 [(中文名, info)]（查技能定义表）。"""
    cn = actor.get("class_name") or ""
    names = actor.get("learned_skills") or []
    if not cn or not names:
        return []
    from .. import engine as E
    out = []
    for s in names:
        try:
            info = E.skill_info(cn, s)
        except Exception:
            info = None
        if info and info.get("mech"):
            out.append((s, info))
    return out


def _has_mech(actor: dict, mech: str) -> bool:
    return any(info.get("mech") == mech for _s, info in _learned_mech_skills(actor))


def apply_class_mech(actor: dict) -> None:
    """技能 mech 兑现装配（幂等；命令层开战仪式与 equip_proc 并列调用）。

    学有对应兑现型技能的 actor → actor.triggers 挂双通道效果：
    - dmg_calc（伤害前乘区修正）
    - skill_hit（命中后清层/附加）
    """
    if not actor:
        return
    install()
    try:
        if not _has_mech(actor, "finisher"):
            return
        trig = actor.setdefault("triggers", {})
        trig.setdefault("dmg_calc", []).append({"action": "mech_finisher_mult"})
        trig.setdefault("skill_hit", []).append({"action": "mech_finisher_clear"})
    except Exception:
        pass  # 技能机制装配异常不阻断开战（容错铁律）


install()
