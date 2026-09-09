# -*- coding: utf-8 -*-
"""battle2 职业机制装配层 class_mech_proc（v181.M）——技能 mech 兑现（声明驱动）。

蓝图：docs/REFACTOR_v181_CLASS_MECH_ASSEMBLY.md。声明表：data/battle2_rules.MECH_CASH。

设计（鱼鱼审 2026-09-09 v2 形态 + R1b owner 方向扩展）：
- 机制差异全在 MECH_CASH 声明表（mech → 模式/消费层/每层系数/清层…）；
  新兑现机制 = 加一行声明（模式覆盖不了的真新语义才写新动作 ~15 行）。
- 动作只有几个"通用执行器"（怎么兑现），参数由装配时从声明读出填入效果 dict——
  引擎零知识、动作零 mech 字符串硬编码。
- 装配：扫 actor 技能集 mech → 查声明 → 参数化挂事件钩子（dmg_calc 乘区 /
  skill_hit 清层）。学什么挂什么，零噪音。

模式（mode，owner 方向由 mode 推断，装配时写入效果 dict 参数 owner）：
  dmg_mult_clear         → owner=caster（缺省，finisher 行为不变）：读/清 caster effects
  dmg_mult_clear_target  → owner=target（R1b B2 burst 引爆族）：读/清 fire ctx 的
                           target effects（元素印记/毒层全在 target 身上）

效果 dict 参数（装配时从声明读出填入）：
  mech        判据：本次施放的技能 mech 必须等于它（触发绑定）
  owner       caster(缺省)/target：读/清谁的 effects（mode 装配时推断写入）
  key         消费的叠层条目；str 或 [k1, k2…] 多印记 key 列表（层数 = 各 key 之和；
              清层清全部）
  per_layer   每层伤害加成（技能 info.per_stack 可覆盖：链舞 finisher_up +6%）
  clear_extra 主清之外的并列清层 [{"owner": …, "key": …}, …]
              （poison_burst_finisher：引爆 target 毒层同时清 caster 连段）
  label/layer_label/unit/icon  文案 flavor（声明表出文案，动作零硬编码）
"""

from __future__ import annotations

_registered = False


def install() -> None:
    """注册通用兑现执行器（幂等；模块 import 即注册，装配方无需再调）。"""
    global _registered
    if _registered:
        return
    from ..battle2.effects import register_action

    def _key_list(key):
        """声明 key 归一为列表（str → [str]；None → []）。"""
        if isinstance(key, (list, tuple)):
            return list(key)
        return [key] if key else []

    def _stacks_of(effects, key) -> int:
        """effects 层数：key 为 str 或多印记 key 列表（语义 = 各 key stacks 之和）。"""
        total = 0
        for k in _key_list(key):
            ef = (effects or {}).get(k)
            total += int(ef.get("stacks", 0) or 0) if isinstance(ef, dict) else 0
        return total

    def _holder(owner, ctx, caster, target):
        """owner 方向选 actor：owner=target → ctx.target（fire ctx 优先）；缺省 caster。"""
        if (owner or "caster") == "target":
            return ctx.get("target") or target
        return ctx.get("actor") or caster

    def _clear_actor(actor, key, logs):
        """把 actor.effects 的 key（str/列表）stacks 置 0。"""
        for k in _key_list(key):
            entry = (actor.get("effects") or {}).get(k)
            if isinstance(entry, dict):
                entry["stacks"] = 0
        logs.append(f"🔗 {'、'.join(_key_list(key))} 归零")

    @register_action("mech_cash_dmg_mult")
    def mech_cash_dmg_mult(battle, caster, target, params, logs):
        """dmg_calc：按持有层数加成伤害乘区（模式 dmg_mult_clear* 的伤害段）。

        参数见模块 docstring；mult = 1 + per_layer × 层数（多印记 key = 各 key 之和）。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        info = ctx.get("info") or {}
        if info.get("mech") != params.get("mech"):
            return
        actor = _holder(params.get("owner"), ctx, caster, target)
        n = _stacks_of(actor.get("effects"), params.get("key"))
        per = float(params.get("per_layer") or 0)
        # 技能级覆盖：info.per_stack（链舞被动给后续终结技 +6%/段）优先于声明缺省
        per = float(info.get("per_stack") or per)
        mult = 1.0 + per * n
        ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * mult
        label = params.get("label") or params.get("mech") or ""
        icon = params.get("icon") or "💥"
        layer_label = params.get("layer_label") or "、".join(_key_list(params.get("key")))
        unit = params.get("unit") or "层"
        logs.append(f"{icon} {label}！{layer_label} {n} {unit}，伤害 ×{mult:.2f}")

    @register_action("mech_cash_clear")
    def mech_cash_clear(battle, caster, target, params, logs):
        """skill_hit：兑现后清层（模式 dmg_mult_clear* 的清层段）。

        主清 params.key（owner 方向 actor）；clear_extra 并列清层（可另一 owner）；
        info.keep_on_kill = 本次不清（技能级覆盖，主清与 extra 一并跳过）。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        info = ctx.get("info") or {}
        if info.get("mech") != params.get("mech"):
            return
        if info.get("keep_on_kill"):
            return
        actor = _holder(params.get("owner"), ctx, caster, target)
        _clear_actor(actor, params.get("key"), logs)
        for ex in params.get("clear_extra") or []:
            if not isinstance(ex, dict):
                continue
            xactor = _holder(ex.get("owner"), ctx, caster, target)
            _clear_actor(xactor, ex.get("key"), logs)

    @register_action("mech_cash_per_system_mult")
    def mech_cash_per_system_mult(battle, caster, target, params, logs):
        """dmg_calc：每系独立乘区（模式 per_system_clear——element_burst_3 元素裁决）。

        对 key 列表里每个 stacks≥1 的系各 ×(1+per_system)（层数不累加，有层就乘）：
        desc 元素裁决：结算三系印记，每系 ×1.2（火/冰/雷各挂过印才触发对应系）。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        info = ctx.get("info") or {}
        if info.get("mech") != params.get("mech"):
            return
        actor = _holder(params.get("owner"), ctx, caster, target)
        effects = actor.get("effects") or {}
        ps = float(params.get("per_system") or 0)
        factor = 1.0
        hit_systems = []
        for k in _key_list(params.get("key")):
            ef = effects.get(k)
            n = int(ef.get("stacks", 0) or 0) if isinstance(ef, dict) else 0
            if n > 0:
                factor *= 1.0 + ps
                hit_systems.append(k)
        if not hit_systems:
            return
        ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * factor
        label = params.get("label") or params.get("mech") or ""
        icon = params.get("icon") or "💥"
        logs.append(f"{icon} {label}！结算 {'、'.join(hit_systems)}，伤害 ×{factor:.2f}")

    _registered = True


def _mech_cash_rules() -> dict:
    """当前挂载的兑现声明表（缺省空——装配层不崩）。"""
    try:
        from ..data.battle2_rules import MECH_CASH
        return MECH_CASH or {}
    except Exception:
        return {}


def _effect_rules() -> dict:
    """当前 EFFECT_RULES（缺省空）。"""
    try:
        from ..battle2.config import get_effect_rules
        return get_effect_rules() or {}
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
    mode=dmg_mult_clear_target 的条目装配时向效果 dict 写 owner=target（读/清
    fire ctx 的 target effects）；dmg_mult_clear 缺省 owner=caster（finisher 兼容）。
    """
    if not actor:
        return
    install()
    try:
        rules = _mech_cash_rules()
        if not rules:
            return
        trig = actor.setdefault("triggers", {})
        # v181.M-R2：start_full 资源开局满额（读 EFFECT_RULES 条目 start_full 声明，
        # 源 core_resources.cls_you_xia v176（原表随 v181.M-R2c 退役，现单源 EFFECT_RULES energy.start_full）
        # 游侠精力开局满——装配层初始化 effects 条目）
        try:
            _full_rules = _effect_rules()
            _cn = actor.get("class_name") or ""
            for _rk, _rc in (_full_rules or {}).items():
                if not (isinstance(_rc, dict) and _rc.get("start_full")):
                    continue
                # 开局满额归属职业（start_classes 声明，空 = 不装配）——防非游侠白拿 energy
                _sc = _rc.get("start_classes") or []
                if _sc and _cn not in _sc:
                    continue
                _cap = int(_rc.get("cap", 0) or 0)
                if _cap > 0:
                    actor.setdefault("effects", {})[_rk] = {
                        "stacks": _cap, "expire": 999999.0}
        except Exception:
            pass
        mechs = {info.get("mech") for _s, info in _learned_mech_skills(actor)}
        for mech in mechs:
            cash = rules.get(mech)
            if not cash:
                continue
            mode = cash.get("mode") or ""
            # owner 方向由 mode 推断（*_target → target，其余 caster）
            owner = "target" if mode.endswith("_target") else "caster"
            if mode.startswith("per_system_clear"):
                # element_burst_3 元素裁决：每系独立乘区（per_system）
                dm = {"action": "mech_cash_per_system_mult", "mech": mech,
                      "key": cash.get("key") or mech,
                      "per_system": cash.get("per_system") or 0.0,
                      "label": cash.get("name") or mech}
                for _k in ("layer_label", "unit", "icon"):
                    if cash.get(_k):
                        dm[_k] = cash[_k]
                if owner == "target":
                    dm["owner"] = "target"
                trig.setdefault("dmg_calc", []).append(dm)
                if cash.get("clear"):
                    cl = {"action": "mech_cash_clear", "mech": mech,
                          "key": cash.get("key") or mech}
                    if owner == "target":
                        cl["owner"] = "target"
                    trig.setdefault("skill_hit", []).append(cl)
                continue
            if mode not in ("dmg_mult_clear", "dmg_mult_clear_target"):
                continue
            key = cash.get("key") or mech
            dm = {"action": "mech_cash_dmg_mult", "mech": mech, "key": key,
                  "per_layer": cash.get("per_layer") or 0.0,
                  "label": cash.get("name") or mech}
            for _k in ("layer_label", "unit", "icon"):
                if cash.get(_k):
                    dm[_k] = cash[_k]
            if owner == "target":
                dm["owner"] = "target"
            trig.setdefault("dmg_calc", []).append(dm)
            if cash.get("clear"):
                cl = {"action": "mech_cash_clear", "mech": mech, "key": key}
                if owner == "target":
                    cl["owner"] = "target"
                if cash.get("clear_extra"):
                    cl["clear_extra"] = cash["clear_extra"]
                trig.setdefault("skill_hit", []).append(cl)
    except Exception:
        pass  # 技能机制装配异常不阻断开战（容错铁律）


install()
