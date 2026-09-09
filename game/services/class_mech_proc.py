# -*- coding: utf-8 -*-
"""battle2 职业机制装配层 class_mech_proc（v181.M）——技能 mech 兑现（声明驱动）。

蓝图：docs/REFACTOR_v181_CLASS_MECH_ASSEMBLY.md。声明表：data/battle2_rules.MECH_CASH。

设计（鱼鱼审 2026-09-09 v2 形态）：
- 机制差异全在 MECH_CASH 声明表（mech → 模式/消费层/每层系数/清层…）；
  新兑现机制 = 加一行声明（模式覆盖不了的真新语义才写新动作 ~15 行）。
- 动作只有几个"通用执行器"（怎么兑现），参数由装配时从声明读出填入效果 dict——
  引擎零知识、动作零 mech 字符串硬编码。
- 装配：扫 actor 技能集 mech → 查声明 → 参数化挂事件钩子（dmg_calc 乘区 /
  skill_hit 清层）。学什么挂什么，零噪音。

模式：
  dmg_mult_clear  → mech_cash_dmg_mult（dmg_calc）+ mech_cash_clear（skill_hit）
  bonus_clear/heal_clear → R1b/R1c 落地时各加一个执行器
"""

from __future__ import annotations

_registered = False


def install() -> None:
    """注册通用兑现执行器（幂等；模块 import 即注册，装配方无需再调）。"""
    global _registered
    if _registered:
        return
    from ..battle2.effects import register_action

    @register_action("mech_cash_dmg_mult")
    def mech_cash_dmg_mult(battle, caster, target, params, logs):
        """dmg_calc：按持有层数加成伤害乘区（模式 dmg_mult_clear 的伤害段）。

        参数（装配时从 MECH_CASH 声明读出填入效果 dict）：
          mech       判据：本次施放的技能 mech 必须等于它（触发绑定）
          key        消费的叠层条目（如 lian_duan）
          per_layer  每层伤害加成（技能 info.per_stack 可覆盖：链舞 finisher_up +6%）
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        info = ctx.get("info") or {}
        if info.get("mech") != params.get("mech"):
            return
        actor = ctx.get("actor") or caster
        ef = (actor.get("effects") or {}).get(params.get("key") or "")
        n = int(ef.get("stacks", 0) or 0) if isinstance(ef, dict) else 0
        per = float(params.get("per_layer") or 0)
        # 技能级覆盖：info.per_stack（链舞被动给后续终结技 +6%/段）优先于声明缺省
        per = float(info.get("per_stack") or per)
        mult = 1.0 + per * n
        ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * mult
        logs.append(f"🔪 终结技！连段 {n} 段，伤害 ×{mult:.2f}")

    @register_action("mech_cash_clear")
    def mech_cash_clear(battle, caster, target, params, logs):
        """skill_hit：兑现后清层（模式 dmg_mult_clear/bonus_clear 的清层段）。

        参数：mech 判据；key 消费层；info.keep_on_kill = 本次不清（技能级覆盖）。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        info = ctx.get("info") or {}
        if info.get("mech") != params.get("mech"):
            return
        if info.get("keep_on_kill"):
            return
        actor = ctx.get("actor") or caster
        ef = actor.get("effects") or {}
        entry = ef.get(params.get("key") or "")
        if isinstance(entry, dict):
            entry["stacks"] = 0
        logs.append(f"🔗 {params.get('key')} 归零")

    _registered = True


def _mech_cash_rules() -> dict:
    """当前挂载的兑现声明表（缺省空——装配层不崩）。"""
    try:
        from ..data.battle2_rules import MECH_CASH
        return MECH_CASH or {}
    except Exception:
        return {}


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


def apply_class_mech(actor: dict) -> None:
    """技能 mech 兑现装配（幂等；命令层开战仪式与 equip_proc 并列调用）。

    对 actor 技能集里每个"声明过兑现"的 mech，按声明参数化挂事件钩子：
    - dmg_calc（伤害前乘区修正）
    - skill_hit（命中后清层）
    """
    if not actor:
        return
    install()
    try:
        rules = _mech_cash_rules()
        if not rules:
            return
        trig = actor.setdefault("triggers", {})
        mechs = {info.get("mech") for _s, info in _learned_mech_skills(actor)}
        for mech in mechs:
            cash = rules.get(mech)
            if not cash:
                continue
            mode = cash.get("mode") or ""
            if mode == "dmg_mult_clear":
                trig.setdefault("dmg_calc", []).append({
                    "action": "mech_cash_dmg_mult",
                    "mech": mech, "key": cash.get("key") or mech,
                    "per_layer": cash.get("per_layer") or 0.0})
                if cash.get("clear"):
                    trig.setdefault("skill_hit", []).append({
                        "action": "mech_cash_clear",
                        "mech": mech, "key": cash.get("key") or mech})
    except Exception:
        pass  # 技能机制装配异常不阻断开战（容错铁律）


install()
