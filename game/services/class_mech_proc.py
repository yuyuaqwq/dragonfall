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

    def _add_mark(tgt: dict, mech: str, n: int) -> None:
        """target effects 印记层 +n（挂印增强用——基础段 apply 前先加，总 = 1+n）。"""
        if tgt is None or n <= 0:
            return
        ef = tgt.setdefault("effects", {})
        en = ef.get(mech)
        if not isinstance(en, dict):
            en = ef[mech] = {}
        en["stacks"] = int(en.get("stacks", 0) or 0) + n

    def _act_target(battle, ctx, actor, target):
        """act_cast 动作目标解析：act_cast fire 在 do_skill 目标解析之前（ctx.target=None）
        → 回落敌对存活首目标（同 actions._default_target 语义）。"""
        tgt = ctx.get("target") or target
        if tgt is not None:
            return tgt
        try:
            from ..battle2.actors import hostile_sides, actor_alive as _alive
            for _sn in hostile_sides(battle, actor.get("side", "")):
                for _a in (battle.sides.get(_sn) or []):
                    if _alive(_a):
                        return _a
        except Exception:
            pass
        return None

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

    @register_action("class_res_channel_gain")
    def class_res_channel_gain(battle, caster, target, params, logs):
        """职业资源渠道 gain（v181.M-R2d）：owner.effects[res].stacks += gain。

        装配层从 EFFECT_RULES 条目 channels 声明生成（归属职业 start_classes 已过滤）：
        - res/gain/label 全由声明写入，动作零资源 key 硬编码
        - kind / not_basic 事件过滤（heal_cast 时机只认 kind=治疗 行动——普攻/攻击技能
          施放不触发，防误攒；参数由装配时从渠道时机映射写入）
        - cap clamp 查 _cap_of（v181.M-R2e 方案 A 收敛：EFFECT_RULES 基础 + actor
          bonus.cap 动态（v181.M-bonus 分域）——faith 上限词条 divine_radiance/holy_heart 生效）；
          stacks float 读/写归一（B3——衰减后 3.9 +2 → 5.9 精度保真）
        - 写后广播 threshold（v181.M-R2e B2：渠道攒到满 cap 的当次触发——过载钩子
          依赖；对齐 effects.apply op=add 的 threshold 广播口径）
        """
        from ..battle2.actors import actor_alive
        from ..battle2.effects import _cap_of as _cap_fn, _norm_stack as _ns
        owner = params.get("_owner") or caster
        if owner is None or not actor_alive(owner):
            return
        ctx = getattr(battle, "_fire_ctx", None) or {}
        info = ctx.get("info") or {}
        kind = params.get("kind")
        if kind and (info.get("kind") or "") != kind:
            return
        if params.get("not_basic") and info.get("_basic"):
            return
        res = params.get("res") or ""
        gain = float(params.get("gain") or 0)
        if not res or gain <= 0:
            return
        cap = _cap_fn(owner, res)
        ef = owner.setdefault("effects", {})
        entry = ef.get(res)
        cur = float(entry.get("stacks", 0) or 0) if isinstance(entry, dict) else 0.0
        if cur >= cap:
            return
        n = max(0.0, min(float(cap), cur + gain))
        if abs(n - cur) < 1e-9:
            return
        if not isinstance(entry, dict):
            entry = ef[res] = {}
        entry["stacks"] = _ns(n)
        cap_txt = f"/{cap}" if cap < 999999 else ""
        logs.append(f"{params.get('icon') or '✦'} {params.get('label') or res} "
                    f"+{_ns(gain):g}（{_ns(n)}{cap_txt}）")
        # v181.M-R2e B2：叠层变化后广播 threshold（过载/阈值机制同一口径）
        try:
            from ..battle2.effect_triggers import fire as _fire
            _fire(battle, "threshold", {"actor": owner, "key": res, "value": n}, logs)
        except Exception:
            pass

    # ---- v181.M-R2e B2：牧师信仰负载制（档位乘区 + 过载）两个装配动作 ----
    # 数据源 = EFFECT_RULES faith 条目 load_tiers/overload_heal_pct（声明驱动，
    # 动作零职业知识——只有装配层按 start_classes 给牧师挂钩，防白拿）。

    def _faith_tiers() -> list:
        """EFFECT_RULES faith 条目 load_tiers 档位表（缺省 []——零默认值铁律）。"""
        try:
            from ..battle2.state_effects import state_def
            _t = (state_def("faith") or {}).get("load_tiers")
            return _t if isinstance(_t, list) else []
        except Exception:
            return []

    @register_action("class_faith_load_tier")
    def class_faith_load_tier(battle, caster, target, params, logs):
        """heal_calc：牧师信仰负载档位治疗乘区（v181.M-R2e B2）。

        施法者（_owner）查自身 effects[faith].stacks（float 保真——衰减 9.3 也准）→
        load_tiers 档位（max 升序，取首个 stacks<=max 的档：0-3 清醒 / 4-7 专注 ×1.25 /
        8-9 透支 ×1.5 / 10 过载 ×1.0）→ heal_mult 累乘进 ctx.mult。无条目/0 层 →
        清醒档 ×1.0（零行为）；超过末档 max（bonus.cap 抬 cap 超高瞬态）→ 末档兜底。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        owner = params.get("_owner") or caster
        if owner is None:
            return
        tiers = _faith_tiers()
        if not tiers:
            return
        entry = (owner.get("effects") or {}).get("faith")
        cur = float(entry.get("stacks", 0) or 0) if isinstance(entry, dict) else 0.0
        mult = 1.0
        label = ""
        for t in tiers:
            if not isinstance(t, dict):
                continue
            mx = float(t.get("max", 0) or 0)
            if mx < 0:
                continue
            if cur <= mx:
                mult = float(t.get("heal_mult", 1.0) or 1.0)
                label = str(t.get("label") or "")
                break
        else:
            # 超过末档 max（bonus.cap 抬 cap 后 10+ 层瞬态）：取最后一档声明
            _last = tiers[-1] if tiers else {}
            if isinstance(_last, dict):
                mult = float(_last.get("heal_mult", 1.0) or 1.0)
                label = str(_last.get("label") or "")
        if mult != 1.0:
            ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * mult
            logs.append(f"✨ 信仰{label or '专注'}！治疗 ×{mult:.2f}（{cur:g} 层）")

    @register_action("class_faith_overload")
    def class_faith_overload(battle, caster, target, params, logs):
        """threshold：信仰叠到满 cap 的当次 → 过载（v181.M-R2e B2）。

        - 触发点 = 叠层 clamp 后 threshold 事件（effects.apply op=add/set 与渠道
          gain 均广播，subject=叠层者自己——只处理自己声明）
        - 判据：ctx.key==faith 且 ctx.value 达 _cap_of 满额（叠到 cap 当次）
        - 效果：faith 清零 + 我方全员回复 max_hp × overload_heal_pct（v130 旧值
          0.015；圣化被动 faith_overload_heal 属旧被动域，battle2 未接——不乘）
        - 防重复：满层后的再次 clamp（已满 +n 仍广播 value=cap）不再触发——过载帧
          标记 _faith_overload_at（近 0.5 刻内只一次）；触发即清零自然离开满层，
          下次重新攒满才再次过载。
        """
        ctx = getattr(battle, "_fire_ctx", None) or {}
        if ctx.get("key") != "faith":
            return
        owner = params.get("_owner") or caster
        if owner is None:
            return
        try:
            from ..battle2.effects import _cap_of as _cap_fn
            cap = _cap_fn(owner, "faith")
        except Exception:
            return
        val = float(ctx.get("value", 0) or 0)
        if val + 1e-9 < cap:
            return  # 未满 cap 不触发（threshold 每层变化都广播）
        now = float(getattr(battle, "_now", 0.0) or 0.0)
        last = float(owner.get("_faith_overload_at", -99.0) or -99.0)
        if now - last < 0.5:
            return  # 过载帧标记：同刻/近帧已过载（满后再次 clamp 广播不重复触发）
        owner["_faith_overload_at"] = now
        # 清零 + 全队回复（同 side 存活成员）
        ef = owner.setdefault("effects", {})
        fentry = ef.get("faith")
        if isinstance(fentry, dict):
            fentry["stacks"] = 0
        pct = 0.015
        try:
            from ..battle2.state_effects import state_def
            pct = float((state_def("faith") or {}).get("overload_heal_pct", 0.015) or 0.015)
        except Exception:
            pct = 0.015
        # 信念·圣化（faith_overload_heal：过载回血 ×(1+heal_up)——R2e 原注释待接，
        # 现被动装配就绪：学过圣化的牧师过载回血提升 heal_up（desc「过载时不再力竭，
        # 改为全队回血+30%」→ 全队回血量 ×1.3；数值读技能 passive dict 零硬编码）
        if _learned_proc(owner, "faith_overload_heal"):
            try:
                from .. import engine as E
                for _s in (owner.get("learned_skills") or []):
                    _i = E.skill_info(owner.get("class_name") or "", _s) or {}
                    if isinstance(_i.get("passive"), dict) \
                            and (_i.get("passive") or {}).get("proc") == "faith_overload_heal":
                        _up = float((_i.get("passive") or {}).get("heal_up", 0) or 0)
                        if _up > 0:
                            pct = pct * (1.0 + _up)
                        break
            except Exception:
                pass  # 圣化增强异常不阻断过载（容错铁律）
        from ..battle2.actors import actor_alive
        from ..battle2.landing import heal_actor
        healed = 0
        side = owner.get("side") or "player"
        for _a in (getattr(battle, "sides", None) or {}).get(side, []) or []:
            if not actor_alive(_a):
                continue
            _val = max(1, int((_a.get("max_hp", 1) or 1) * pct))
            _real = heal_actor(battle, _a, _val, logs)
            if _real > 0:
                healed += _real
        logs.append(f"⚡ 信仰过载！圣光迸发，全员回复 {healed} 点生命！"
                    if healed > 0 else "⚡ 信仰过载！信念归零（全员生命已满）！")

    # ---- v181.M-melody：诗人旋律驻留（唱新歌/吟唱叠层/满层终章 + 全队光环广播）----
    # 数据源 = 技能 dict：melody 字段（kind: atk/def/spd/atk_matk）+ melody_pct（基础%）
    # + finale（终章 kind: crit/atk）+ melody_fin_pct/buff_turns。状态存施法者
    # effects["melody_state"]（无 EFFECT_RULES 声明 → 零折算纯状态，随 actor 序列化）；
    # 光环广播全员 effects["melody_<kind>"]（stat_scale per=0.01，stacks=目标%）。
    # 数值公式：效果% = pct × (1 + 0.25×(stacks-1))（1 层=desc 值，5 层=×2=+100%；
    # 公式与分支 e_ 减益系/终章触发细节标待 v153 重做确认——本次目的=机制载体）。
    _MELODY_AURA_MAP = {
        "atk": "melody_atk", "def": "melody_def",
        "spd": "melody_spd", "atk_matk": "melody_atk_matk",
    }
    _MELODY_FIN_MAP = {"atk": "melody_finale_atk", "crit": "melody_finale_crit"}

    def _melody_pct_of(state) -> float:
        pct = float(state.get("pct") or 0)
        stack = int(state.get("stacks") or 1)
        return pct * (1.0 + 0.25 * max(0, stack - 1))

    def _melody_write_aura(battle, actor, logs):
        """按施法者 melody_state 写全员驻留光环（先清旧驻留条目，finale buff 不清）。"""
        state = ((actor.get("effects") or {}).get("melody_state") or {})
        key = _MELODY_AURA_MAP.get(state.get("kind") or "")
        side = actor.get("side") or "player"
        for _a in (getattr(battle, "sides", None) or {}).get(side, []) or []:
            ef = _a.setdefault("effects", {})
            for _k in list(ef):
                if _k in _MELODY_AURA_MAP.values():
                    ef.pop(_k, None)  # 旧驻留全清（换歌/叠层重写）
            if key:
                ef[key] = {"stacks": _melody_pct_of(state), "expire": None}

    def _melody_finale(battle, actor, state, logs):
        """终章：全员 finale 爆发 buff（expire 后消散，叠加在驻留上），强度归 1。"""
        fin = state.get("fin_kind") or ""
        fkey = _MELODY_FIN_MAP.get(fin)
        if not fkey:
            return
        try:
            _now = float(getattr(battle, "_now", 0) or 0)
        except Exception:
            _now = 0.0
        _turns = max(1, int(state.get("fin_turns") or 8))
        side = actor.get("side") or "player"
        for _a in (getattr(battle, "sides", None) or {}).get(side, []) or []:
            _a.setdefault("effects", {})[fkey] = {
                "stacks": float(state.get("fin_pct") or 0), "expire": _now + _turns}
        logs.append(f"💥 终章！全队获得爆发增益（{_turns} 刻）！")

    @register_action("class_melody_act")
    def class_melody_act(battle, caster, target, params, logs):
        """act_cast：mech=melody（唱新歌/换歌）| mech=melody_chant（吟唱叠层）。"""
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        actor = ctx.get("actor") or caster
        info = ctx.get("info") or {}
        mech = info.get("mech")
        if mech not in ("melody", "melody_chant"):
            return
        ef = actor.setdefault("effects", {})
        if mech == "melody":
            kind = info.get("melody") or ""
            if kind not in _MELODY_AURA_MAP:
                logs.append("🎵 这首曲式（" + str(kind) + "）尚未谱成……")
                return
            ef["melody_state"] = {
                "stacks": 1, "kind": kind,
                "pct": float(info.get("melody_pct") or 0),
                "name": info.get("name") or "",
                "fin_kind": info.get("finale") or "",
                "fin_pct": float(info.get("melody_fin_pct") or 0),
                "fin_turns": int(info.get("buff_turns") or 8),
            }
            _melody_write_aura(battle, actor, logs)
            logs.append(f"🎵 奏响【{ef['melody_state']['name']}】！旋律驻留，全队获得光环！")
            return
        state = ef.get("melody_state")
        if not isinstance(state, dict) or not state.get("kind"):
            logs.append("🎵 尚无旋律奏响——先唱一首歌吧！（战歌/守歌/疾歌）")
            return
        stack = int(state.get("stacks") or 1)
        if stack >= 5:
            if state.get("fin_kind") and state.get("fin_kind") in _MELODY_FIN_MAP:
                _melody_finale(battle, actor, state, logs)
                state["stacks"] = 1
                _melody_write_aura(battle, actor, logs)
            else:
                logs.append("🎵 旋律已至巅峰（5 层）——此曲无终章，保持最强音吧")
            return
        state["stacks"] = stack + 1
        _melody_write_aura(battle, actor, logs)
        logs.append(f"🎵 吟唱回旋，【{state.get('name')}】强度 +1（{state['stacks']}/5）！")

    # ---- v181.M-passive P1：被动 proc 通用动作（插件样板——动作零 proc 硬编码）----
    # 语义源 = 技能 desc + passive dict；声明表 PASSIVE_PROC（battle2_rules）给
    # event/action/judge 模板；装配器把被动参数并入 params（mult 归一 mult/dmg_add）。
    # P1 先落 dmg_calc 乘区 + on_kill 回能两样板（零引擎改动通道），其余族 P2 续。

    @register_action("passive_dmg_mult")
    def passive_dmg_mult(battle, caster, target, params, logs):
        """dmg_calc 条件乘区：judge 命中 → ctx.mult ×(1+mult)（对齐 N9.7d 词条乘区）。

        judge kind（谓词扩展 P2）：
        - mech_eq          本次技能 mech == judge.mech → mult 参数
        - mech_prefix      本次技能 mech 以 judge.mech 开头（poison_burst 覆盖毒爆两种技）
        - target_marks_all_ge  目标多印记都 ≥layers → mult 参数
        - target_mark_any  目标带标记（层数>0）→ mult = per_layer × 层数（标记额外增伤，
                          旧挂点14 增量并入语义——基础段 EFFECT_RULES debuff_scale 天然处理）
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        judge = params.get("judge") or {}
        kind = judge.get("kind") or ""
        actor = ctx.get("actor") or caster
        tg = ctx.get("target") or target
        info = ctx.get("info") or {}
        mult = 0.0
        ok = False
        if kind == "mech_eq":
            ok = (info.get("mech") or "") == judge.get("mech")
            if ok:
                mult = float(params.get("mult") or params.get("dmg_add") or 0)
        elif kind == "mech_prefix":
            _pre = judge.get("mech") or ""
            ok = bool(_pre) and (info.get("mech") or "").startswith(str(_pre))
            if ok:
                mult = float(params.get("mult") or params.get("dmg_add") or 0)
        elif kind == "target_marks_all_ge":
            layers = float(params.get("layers") or judge.get("layers") or 1)
            if tg is not None:
                ef = tg.get("effects") or {}
                ok = all(
                    float((ef.get(m) or {}).get("stacks", 0) or 0) >= layers
                    for m in (judge.get("marks") or []))
                if ok:
                    mult = float(params.get("mult") or 0)
        elif kind == "target_mark_any":
            # 标记额外增伤：目标带标记（层>0）→ ×(1 + per_layer×层)
            mark = judge.get("mark") or ""
            if tg is not None and mark:
                _entry = (tg.get("effects") or {}).get(mark)
                _n = int(_entry.get("stacks", 0) or 0) if isinstance(_entry, dict) else 0
                if _n > 0:
                    ok = True
                    mult = float(params.get("per_layer") or 0) * _n
        elif kind == "speed_ratio_ge":
            # 速度比 ≥ ratio_field → ×(1+dmg_add)（疾风·极；旧挂点4 语义：
            # 敌方无速度按 0 防御性跳过——速度比恒 ≥2 不触发）
            try:
                from ..battle2.stats import actor_stats as _as
                _spd_a = float((_as(battle, actor) or {}).get("spd", 0) or 0)
                _spd_t = float((_as(battle, tg) or {}).get("spd", 0) or 0) if tg is not None else 0.0
            except Exception:
                _spd_a = _spd_t = 0.0
            _ratio = float(params.get("ratio") or judge.get("ratio") or 0)
            if _ratio > 0 and _spd_t > 0 and _spd_a >= _ratio * _spd_t:
                ok = True
                mult = float(params.get("dmg_add") or params.get("mult") or 0)
        if not ok or mult <= 0:
            return
        ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * (1.0 + mult)
        logs.append(f"✨ 被动生效：伤害 ×{1.0 + mult:.2f}！")

    @register_action("passive_kill_gain")
    def passive_kill_gain(battle, caster, target, params, logs):
        """on_kill 资源回满：击杀者 effects[key] 置 cap（追风：专注回满）。"""
        ctx = getattr(battle, "_fire_ctx", None) or {}
        actor = ctx.get("actor") or caster
        if actor is None:
            return
        key = params.get("key") or "energy"
        from ..battle2.effects import _cap_of as _cap_fn
        cap = _cap_fn(actor, key)
        if cap <= 0:
            return
        ef = actor.setdefault("effects", {})
        if not isinstance(ef.get(key), dict):
            ef[key] = {}
        ef[key]["stacks"] = float(cap)
        ef[key]["expire"] = None
        logs.append(f"✨ {params.get('label') or '被动'}:{'资源回满！'}")

    @register_action("passive_counter")
    def passive_counter(battle, caster, target, params, logs):
        """on_taken 受击反击（聚合族装配后终值单条）：roll chance → atk×atk_pct 反打攻击方。

        语义 = 旧挂点13 聚合收口 + we_affix_counter 落地动作（反击方向=攻击方，
        on_taken ctx.source；伤害 = 攻击者面板 atk × atk_pct 直伤打防御）。
        """
        owner = params.get("_owner") or caster
        if owner is None:
            return
        ctx = getattr(battle, "_fire_ctx", None) or {}
        attacker = ctx.get("source")  # on_taken 攻击方
        from ..battle2.actors import actor_alive
        if attacker is None or not actor_alive(attacker):
            return
        import random as _r
        chance = float(params.get("chance") or 0)
        if chance <= 0 or _r.random() >= chance:
            return
        try:
            from ..battle2.landing import deal_damage
            from ..battle2.stats import actor_stats as _as
            st = _as(battle, owner) or {}
            dmg = max(1, int(float(st.get("atk", 0) or 0)
                               * float(params.get("atk_pct") or 0.80)))
            deal_damage(battle, owner, attacker, dmg, logs)
            logs.append(f"⚔️ 反击！对【{attacker.get('name', '敌人')}】造成 {dmg} 点伤害！")
        except Exception:
            pass  # 反击异常不阻断受击落地

    @register_action("passive_cond_crit")
    def passive_cond_crit(battle, caster, target, params, logs):
        """act_cast 条件暴击：资源 ≥ 阈值（+技能系/非普攻门槛）→ 本次行动暴击加算 buff。

        语义 = 旧挂点1 _passive_crit_bonus（crit_cond_add）逐字：资源层数（战意/奥术/精力）
        ≥ 阈值 → 暴击率 +add（绝对点）。实现 = effects buff 快照型条目
        {stat: crit, mult: add, op: add}（stats._apply_effects 兼容路径，无需 EFFECT_RULES
        声明）——act_cast 在 crit 判定前 fire（扣费后、伤害管线前），buff 覆盖整个行动；
        下次行动动作重写/清除，无残留。
        judge 参数：res（资源 key）/ ge_field（passive dict 阈值字段名）/ mech（可选技能系
        过滤）/ not_basic（普攻不吃）。add 来自 passive dict。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        actor = ctx.get("actor") or caster
        if actor is None:
            return
        info = ctx.get("info") or {}
        judge = params.get("judge") or {}
        buff_key = params.get("buff_key") or ""
        if not buff_key:
            return
        ef = actor.setdefault("effects", {})
        # 普攻排除（desc「下次技能暴击」）：basic 行动直接清旧残留并跳过
        if judge.get("not_basic") and info.get("_basic"):
            ef.pop(buff_key, None)
            return
        # 技能系过滤（desc「奥术暴击」）：info.mech 不匹配 → 清残留跳过
        mech = judge.get("mech")
        if mech and (info.get("mech") or "") != mech:
            ef.pop(buff_key, None)
            return
        res = judge.get("res") or ""
        ge_field = judge.get("ge_field") or ""
        need = float(params.get(ge_field) or 0)
        add = float(params.get("add") or 0)
        if not res or need <= 0 or add <= 0:
            ef.pop(buff_key, None)  # 缺字段 = 无此行为
            return
        _entry = ef.get(res)
        cur = float(_entry.get("stacks", 0) or 0) if isinstance(_entry, dict) else 0.0
        # 施放前快照还原（旧挂点 _pre_cost_res 语义）：act_cast 在 _spend_skill_cost
        # 之后 fire——若本技能 res_cost 扣了该资源，施放前结余 = 当前 + 已扣额
        # （疾风之心 desc「结余 ≥40」= 施放前判定，非扣费后）
        _rc = (info.get("res_cost") or {})
        if isinstance(_rc, dict) and res in _rc:
            try:
                cur += float(_rc.get(res, 0) or 0)
            except Exception:
                pass
        if cur >= need:
            # 命中 → 重写 buff（防多次行动叠加/陈旧值）
            ef[buff_key] = {"stacks": 1, "stat": "crit", "mult": add,
                            "op": "add", "expire": None}
            logs.append(f"✨ 被动生效：暴击 +{int(add * 100)}%！")
        else:
            ef.pop(buff_key, None)

    @register_action("passive_taken_reduce")
    def passive_taken_reduce(battle, caster, target, params, logs):
        """taken_calc 条件减伤：资源 ≥ 阈值 → ctx.mult ×(1-reduce)（承伤者视角）。

        语义 = 旧挂点11 dr_cond（zy_full 段）逐字：战意 ≥stacks → 减伤 reduce
        （乘区模式对齐 we_taken_mult_cond：mult <1 = 减免）。reduce 来自 passive dict。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        owner = params.get("_owner") or ctx.get("actor") or caster
        if owner is None:
            return
        reduce_v = float(params.get("reduce") or 0)
        if reduce_v <= 0:
            return  # 缺字段 = 无此行为
        if not _res_ge_ok(owner, params.get("judge") or {}, params):
            return
        ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * (1.0 - min(reduce_v, 0.9))
        logs.append(f"🛡️ {params.get('label') or '被动'}：减伤 {int(reduce_v * 100)}% 生效！")

    @register_action("passive_cc_clear")
    def passive_cc_clear(battle, caster, target, params, logs):
        """turn_start 免控清除：资源 ≥ 阈值 → 移除指定控制条目（免疫眩晕等）。

        语义 = 旧挂点10 stun_clear 段逐字（战意满 → 移除 stun——回合开始检查早于
        控制消费，等效免疫；被晕时下回合开始即被清，控制不生效）。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        owner = params.get("_owner") or ctx.get("actor") or caster
        if owner is None:
            return
        if not _res_ge_ok(owner, params.get("judge") or {}, params):
            return
        ctrl = params.get("ctrl") or ""
        if not ctrl:
            return
        ef = owner.get("effects") or {}
        entry = ef.get(ctrl)
        if isinstance(entry, dict) and entry.get("mode") == "skip":
            ef.pop(ctrl, None)
            logs.append(f"🛡️ {params.get('label') or '被动'}：免疫【{ctrl}】！")

    @register_action("passive_cc_break")
    def passive_cc_break(battle, caster, target, params, logs):
        """turn_start 消耗挣脱：被控（mode=skip）→ 资源 ≥cost + 次数余 → 扣资源挣脱。

        语义 = 旧 _tenacity_try_break 逐字：战意 ≥cost（默认2）且剩余次数>0 → 扣
        战意 + 次数-1（effects[left_key]，装配时 init=3 每场重置）→ 移除控制照常行动。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        owner = params.get("_owner") or ctx.get("actor") or caster
        if owner is None:
            return
        ef = owner.get("effects") or {}
        # 找 skip 控制（stun/freeze/sleep…mode=skip 一律可挣脱）
        hit_ctrl = None
        for _k, _e in ef.items():
            if isinstance(_e, dict) and _e.get("mode") == "skip":
                hit_ctrl = _k
                break
        if hit_ctrl is None:
            return
        res = params.get("res") or ""
        cost = float(params.get(params.get("cost_field") or "cost") or 0)
        if not res or cost <= 0:
            return  # 缺字段 = 无此行为
        _entry = ef.get(res)
        cur = float(_entry.get("stacks", 0) or 0) if isinstance(_entry, dict) else 0.0
        left_key = params.get("left_key") or ""
        _le = ef.get(left_key) if left_key else None
        left = float(_le.get("stacks", 0) or 0) if isinstance(_le, dict) else 0.0
        if cur < cost or left <= 0:
            return
        # 扣战意 + 次数-1 + 移除控制（旧 _tenacity_try_break 顺序）
        _entry["stacks"] = max(0, cur - cost)
        if left_key and isinstance(_le, dict):
            _le["stacks"] = left - 1
        ef.pop(hit_ctrl, None)
        logs.append(f"🛡️ {params.get('label') or '被动'}：消耗 {int(cost)} 层战意挣脱控制！")

    @register_action("passive_lifesteal_buff")
    def passive_lifesteal_buff(battle, caster, target, params, logs):
        """act_cast 吸血 buff：每层资源 → 面板 lifesteal 加算（淬血 1.5%/层战意）。

        语义 = 旧挂点5 _settle_lifesteal 吸血率加算（每层战意 +per_layer，cap 30% 引擎保留）
        ——buff 快照条 {stat: lifesteal, mult: per_layer×层, op: add}，行动内 _settle_lifesteal
        读面板吃到；下次行动重写/清除。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        actor = ctx.get("actor") or caster
        if actor is None:
            return
        res = params.get("res") or "zhan_yi"
        per = float(params.get("per_layer") or 0)
        buff_key = params.get("buff_key") or ""
        if per <= 0 or not buff_key:
            return  # 缺字段 = 无此行为
        ef = actor.setdefault("effects", {})
        _entry = ef.get(res)
        cur = float(_entry.get("stacks", 0) or 0) if isinstance(_entry, dict) else 0.0
        value = per * cur
        if value > 0:
            ef[buff_key] = {"stacks": 1, "stat": "lifesteal", "mult": value,
                            "op": "add", "expire": None}
        else:
            ef.pop(buff_key, None)

    @register_action("passive_heal_overflow_shield")
    def passive_heal_overflow_shield(battle, caster, target, params, logs):
        """heal_calc 治疗溢出转盾：计划治疗超出目标缺口部分 ×pct → 护盾（给被治疗者）。

        语义（NO_OLD，desc 权威）：圣光回响「治疗溢出量的 50% 转为护盾」——heal_calc
        在落地前（缺口未填充），溢出 = heal - 当前缺口。护盾结构对齐引擎 shield 动词
        （shields[key]={value, expire_at, halve}；转盾默认 3 刻）。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        owner = ctx.get("actor") or caster
        if owner is None:
            return
        tgt = ctx.get("target") or target
        if tgt is None:
            return
        heal = float(ctx.get("heal") or 0)
        pct = float(params.get("pct") or 0)
        if heal <= 0 or pct <= 0:
            return
        _mx = int(tgt.get("max_hp", 1) or 1)
        _cur_hp = int(tgt.get("hp", 0) or 0)
        gap = max(0, _mx - _cur_hp)
        overflow = max(0, int(heal) - gap)
        if overflow <= 0:
            return
        val = max(1, int(overflow * pct))
        try:
            from ..battle2.battle import _now_of
            now = _now_of(battle)
        except Exception:
            now = 0.0
        sh = tgt.setdefault("shields", {})
        key = "heal_overflow"
        expire = now + 3  # 转盾默认 3 刻（shield 动词缺省 turns=3）
        cur = sh.get(key)
        if isinstance(cur, dict):
            cur["value"] = int(cur.get("value", 0) or 0) + val
            if cur.get("expire_at") is not None:
                cur["expire_at"] = max(float(cur.get("expire_at", 0) or 0), expire)
        else:
            sh[key] = {"value": val, "expire_at": expire, "halve": False}
        logs.append(f"🛡️ {params.get('label') or '被动'}：治疗溢出 {overflow}，转化护盾 {val} 点！")

    @register_action("mech_cash_fury_enter")
    def mech_cash_fury_enter(battle, caster, target, params, logs):
        """act_cast 狂暴进入（血祭 zhan_yi_fury 兑现）：花 res 层战意 → effects[fury]。

        语义（v153 CLASS_MECHANICS_v153 战士血怒线）：血祭花 4 层战意（无视 10 层
        门槛）立即进入狂暴。fury 条目声明 EFFECT_RULES stat_scale atk +20%。
        战意不足 → 不进入（技能无 res_cost 前置，兑现兜底判）。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        owner = params.get("_owner") or ctx.get("actor") or caster
        if owner is None:
            return
        info = ctx.get("info") or {}
        mech = info.get("mech") or ""
        if mech != "zhan_yi_fury":
            return
        res = params.get("res") or "zhan_yi"
        cost = int(info.get(params.get("mech_val_field") or "mech_val") or 0)
        if cost <= 0:
            return  # 缺字段 = 无此行为
        ef = owner.get("effects") or {}
        _entry = ef.get(res)
        cur = float(_entry.get("stacks", 0) or 0) if isinstance(_entry, dict) else 0.0
        if cur < cost:
            logs.append(f"🔥 战意不足（{int(cur)}/{cost}），无法进入狂暴！")
            return
        _entry["stacks"] = max(0, cur - cost)
        owner.setdefault("effects", {})["fury"] = {"stacks": 1, "expire": None}
        logs.append(f"🔥 {params.get('label') or '狂暴'}！战士进入狂暴状态，攻击 +20%！")

    @register_action("passive_dot_mult")
    def passive_dot_mult(battle, caster, target, params, logs):
        """dot_calc DOT 乘区：dot_key 匹配 → ctx.mult ×(1+mult)（施毒者被动万毒归宗）。

        语义 = 旧挂点 DOT 伤害结算处毒伤乘区（所有毒层伤害 +mult）。dot_calc 是
        broadcast 事件（施毒者在施放方、承伤者在 target——subject 过滤会挡住），
        owner=_owner（fire 注入声明者）自查归属；dot_key 过滤只加成指定 DOT。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        owner = params.get("_owner") or caster
        if owner is None:
            return
        dot_key = ctx.get("dot_key") or ""
        judge = params.get("judge") or {}
        allow = judge.get("dot_key") or ""
        if allow and dot_key != allow:
            return
        mult = float(params.get("mult") or params.get("dmg_add") or 0)
        if mult <= 0:
            return  # 缺字段 = 无此行为
        ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * (1.0 + mult)
        logs.append(f"☠️ {params.get('label') or '被动'}：DOT 伤害 ×{1.0 + mult:.2f}！")

    @register_action("passive_poison_weaken")
    def passive_poison_weaken(battle, caster, target, params, logs):
        """dot_calc 毒层条件 debuff：目标毒 ≥layers → 减速降防（剧毒之触，desc 权威）。

        语义（NO_OLD desc）：目标毒层 ≥5 时减速 30%、降防 20%——dot_calc 每跳广播时
        检查承伤者毒层（效果持续 = 每跳续期 hold 刻，毒止跳后 debuff 自然到期消散）。
        effects 快照条目折算对齐现网 we_ 减速/降防（stat spd/def op mul）。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        owner = params.get("_owner") or caster
        if owner is None:
            return
        dot_key = ctx.get("dot_key") or ""
        judge = params.get("judge") or {}
        if judge.get("dot_key") and dot_key != judge.get("dot_key"):
            return
        tgt = ctx.get("target")
        if tgt is None:
            return
        _pe = (tgt.get("effects") or {}).get("poison")
        n = int(_pe.get("stacks", 0) or 0) if isinstance(_pe, dict) else 0
        layers_field = judge.get("layers_field") or ""
        need = float(params.get(layers_field) or 0)
        if need <= 0 or n < need:
            return  # 毒层不足 = 无此行为
        spd_pct = float(params.get("spd_pct") or 0)
        def_pct = float(params.get("def_pct") or 0)
        if spd_pct <= 0 and def_pct <= 0:
            return
        try:
            from ..battle2.battle import _now_of
            exp = _now_of(battle) + float(params.get("hold") or 2.0)
        except Exception:
            exp = None
        ef = tgt.setdefault("effects", {})
        if spd_pct > 0:
            ef["spd_down"] = {"stat": "spd", "op": "mul", "mult": 1.0 - spd_pct,
                              "expire": exp}
        if def_pct > 0:
            ef["def_down"] = {"stat": "def", "op": "mul", "mult": 1.0 - def_pct,
                              "expire": exp}
        logs.append(f"🐍 {params.get('label') or '被动'}：剧毒缠身，目标减速降防！")

    @register_action("class_shadow_dance_enter")
    def class_shadow_dance_enter(battle, caster, target, params, logs):
        """增益技 effect=shadow_dance（暗影步）：连段 ≥5 → 进入影舞态。

        语义（v153 影舞者线）：暗影步「连段满 5 → 进入影舞态」——effects[shadow_dance]
        1 层（cd_mult 0.8 态内 CD−20% 引擎通用修正）。连段不足 → 提示不进入。
        """
        actor = caster if caster is not None else target
        if actor is None:
            return
        ef = actor.get("effects") or {}
        _le = ef.get("lian_duan")
        n = float(_le.get("stacks", 0) or 0) if isinstance(_le, dict) else 0.0
        if n < 5:
            logs.append(f"🌫️ 连段不足（{int(n)}/5），无法进入影舞态！")
            return
        actor.setdefault("effects", {})["shadow_dance"] = {"stacks": 1, "expire": None}
        logs.append("🌫️ 踏入影舞之境！技能 CD −20%，如影随形！")

    @register_action("class_stance_guard_enter")
    def class_stance_guard_enter(battle, caster, target, params, logs):
        """增益技 effect=stance_guard（守护姿态 v153 铁誓线）：写守护姿态态 + 挂反击。

        语义：守护姿态「受击反击 40%、每刻积攒 0.2 战意」——effects[stance_guard]
        持续 turns 刻（技能 buff_turns）；反击 = on_taken trigger（class_stance_counter，
        态在才反击 40%，防重复挂）；每刻 +0.2 战意需 tick 装配点标缺口。
        """
        actor = caster if caster is not None else target
        if actor is None:
            return
        try:
            from ..battle2.battle import _now_of
            now = _now_of(battle)
        except Exception:
            now = 0.0
        turns = max(1, int(params.get("turns") or 0) or 8)
        actor.setdefault("effects", {})["stance_guard"] = {
            "stacks": 1, "expire": now + turns}
        # 挂受击反击 trigger（幂等——同 key 不重复挂）
        trig = actor.setdefault("triggers", {})
        lst = trig.setdefault("on_taken", [])
        if not any(isinstance(t, dict) and t.get("type") == "class_stance_counter"
                   for t in lst):
            lst.append({"type": "class_stance_counter", "chance": 0.40,
                        "atk_pct": 1.0, "label": "守护姿态"})
        logs.append(f"🛡️ 进入守护姿态：受击反击 40%（{turns} 刻）！")

    @register_action("class_stance_counter")
    def class_stance_counter(battle, caster, target, params, logs):
        """on_taken 守护姿态反击：态在 → 40% 反打攻击者 atk×100%（普攻全额）。"""
        ctx = getattr(battle, "_fire_ctx", None) or {}
        owner = params.get("_owner") or ctx.get("actor") or caster
        if owner is None:
            return
        if not isinstance((owner.get("effects") or {}).get("stance_guard"), dict):
            return  # 姿态已过期 → 不反击
        attacker = ctx.get("source")
        from ..battle2.actors import actor_alive
        if attacker is None or not actor_alive(attacker):
            return
        import random as _r
        chance = float(params.get("chance") or 0)
        if chance <= 0 or _r.random() >= chance:
            return
        try:
            from ..battle2.landing import deal_damage
            from ..battle2.stats import actor_stats as _as
            st = _as(battle, owner) or {}
            dmg = max(1, int(float(st.get("atk", 0) or 0)
                               * float(params.get("atk_pct") or 1.0)))
            deal_damage(battle, owner, attacker, dmg, logs)
            logs.append(f"🛡️ 守护反击！对【{attacker.get('name', '敌人')}】造成 {dmg} 点伤害！")
        except Exception:
            pass

    @register_action("passive_shadow_buff")
    def passive_shadow_buff(battle, caster, target, params, logs):
        """act_cast 影舞态强化 buff：态内 → 面板 spd ×(1+spd_add)（暗影步·极）。

        语义（v153）：暗影步·极「影舞态中速度 +25%、暴伤 +20%」——spd 走 buff 快照
        （stat spd op mul）；暴伤无面板通道（crit_dmg 非面板字段）→ 标缺口待引擎通道。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        actor = ctx.get("actor") or caster
        if actor is None:
            return
        ef = actor.setdefault("effects", {})
        buff_key = params.get("buff_key") or "_shadow_spd"
        if not isinstance(ef.get("shadow_dance"), dict):
            ef.pop(buff_key, None)  # 非影舞态 → 清残留
            return
        spd_add = float(params.get("spd_add") or 0)
        if spd_add <= 0:
            return
        ef[buff_key] = {"stacks": 1, "stat": "spd", "mult": 1.0 + spd_add,
                        "op": "mul", "expire": None}

    @register_action("passive_res_gain_turn")
    def passive_res_gain_turn(battle, caster, target, params, logs):
        """turn_start 资源自动回复：effects[res] += gain（奥术直觉每行动回充能）。

        语义（v153 法师奥术线）：奥术直觉「每刻自动回复 1 点奥术充能」——回合制近似
        turn_start 每次行动回 gain（冥想中 +2 需冥想态标缺口）。cap clamp 同 apply。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        actor = ctx.get("actor") or caster
        if actor is None:
            return
        res = params.get("res") or ""
        gain = float(params.get(params.get("gain_field") or "gain") or 0)
        if not res or gain <= 0:
            return  # 缺字段 = 无此行为
        ef = actor.setdefault("effects", {})
        entry = ef.get(res)
        if not isinstance(entry, dict):
            entry = ef[res] = {}
        from ..battle2.effects import _cap_of as _cap_fn
        cap = _cap_fn(actor, res)
        if cap <= 0:
            return
        cur = float(entry.get("stacks", 0) or 0)
        n = min(float(cap), cur + gain)
        if n > cur:
            entry["stacks"] = n
            logs.append(f"🔮 {params.get('label') or '被动'}：奥术充能自动回复 {int(gain)}（{n:g}/{cap}）")

    @register_action("passive_revive_guard")
    def passive_revive_guard(battle, caster, target, params, logs):
        """on_death 守护姿态致命免疫（铁誓·不动）：姿态下首次致命伤 → 回满 + 清空战意。

        语义（v153 desc）：守护姿态下首次致命伤害免疫，清空全部战意——hp_pct 1.0
        （满血复活=致命免疫）；一次性 used_key；姿态保留（守护姿态是 buff 不随战意）。
        """
        ctx = getattr(battle, "_fire_ctx", None) or {}
        owner = ctx.get("actor") or caster
        if owner is None:
            return
        form = params.get("form") or "stance_guard"
        used_key = params.get("used_key") or "_stance_immortal_used"
        ef = owner.setdefault("effects", {})
        if (ef.get(used_key) or {}).get("stacks"):
            return  # 已用（一次性）
        if not isinstance(ef.get(form), dict):
            return  # 非守护姿态
        hp_pct = float(params.get("hp_pct") or 0)
        if hp_pct <= 0:
            return
        mhp = int(owner.get("max_hp", 1) or 1)
        owner["hp"] = max(1, int(mhp * hp_pct))
        zy = ef.get("zhan_yi")
        if isinstance(zy, dict):
            zy["stacks"] = 0
        ef[used_key] = {"stacks": 1, "expire": None}
        try:
            ka = getattr(battle, "killed_actors", None)
            if isinstance(ka, list) and owner in ka:
                ka.remove(owner)
        except Exception:
            pass
        logs.append(f"🛡️ {params.get('label') or '铁誓·不动'}：铁誓加身，致命伤被免疫！")

    @register_action("passive_revive_berserk")
    def passive_revive_berserk(battle, caster, target, params, logs):
        """on_death 狂暴中复活（血怒·不灭）：狂暴中首次死亡 → 清空战意复活回 hp_pct。

        语义（v153 desc 权威 + 旧挂点12 revive_cond 逐字）：狂暴中生命首次归零 →
        清空战意复活回 30%（hp_pct）。一次性（used_key 标记）；复活从 battle.killed_actors
        移除（_on_actor_dead 只记录，胜负/掉落判定后置——复活后照常行动）。
        """
        ctx = getattr(battle, "_fire_ctx", None) or {}
        owner = ctx.get("actor") or caster
        if owner is None:
            return
        form = params.get("form") or "fury"
        used_key = params.get("used_key") or "_berserk_revive_used"
        ef = owner.setdefault("effects", {})
        if (ef.get(used_key) or {}).get("stacks"):
            return  # 已用（一次性）
        if not isinstance(ef.get(form), dict):
            return  # 非狂暴中（条件不满足 = 不复活）
        hp_pct = float(params.get("hp_pct") or 0)
        if hp_pct <= 0:
            return  # 缺字段 = 无此行为
        mhp = int(owner.get("max_hp", 1) or 1)
        owner["hp"] = max(1, int(mhp * hp_pct))
        # 清空战意 + 移除狂暴 + 标记已用（v153：复活清空战意）
        zy = ef.get("zhan_yi")
        if isinstance(zy, dict):
            zy["stacks"] = 0
        ef.pop(form, None)
        ef[used_key] = {"stacks": 1, "expire": None}
        # 从死亡记录移除（胜负/击杀判定后置——复活后不被算作已死）
        try:
            ka = getattr(battle, "killed_actors", None)
            if isinstance(ka, list) and owner in ka:
                ka.remove(owner)
        except Exception:
            pass
        logs.append(f"🔥 {params.get('label') or '血怒·不灭'}：怒意未熄，战士复活！回复 {int(mhp * hp_pct)} 生命")

    @register_action("passive_mark_enhance")
    def passive_mark_enhance(battle, caster, target, params, logs):
        """act_cast 元素印记增强：亲和（引爆后下次挂印+1）/ 同调（连续同系二次挂印+1）。

        语义（desc 权威）：
        - affinity：施放引爆技（mech 前缀 element_burst）→ 置待增强标记；下次挂印技
          （mech=fire/ice/thunder_mark）→ target 对应印记 +1（效果段基础 apply 再 +1 = 总 2）
        - sync：挂印技记录施法系，连续两次同系 → 第二次挂印 +1；非元素施法断连清记录
        多印记技（element_multi_mark 双系）语义复杂不增强（保底基础行为）。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        actor = ctx.get("actor") or caster
        if actor is None:
            return
        info = ctx.get("info") or {}
        mech = info.get("mech") or ""
        mode = params.get("mode") or ""
        _MARKS = {"fire_mark": "fire", "ice_mark": "ice", "thunder_mark": "thunder"}
        is_mark = mech in _MARKS
        is_burst = str(mech).startswith("element_burst")
        if mode == "affinity":
            if is_burst:
                actor.setdefault("effects", {})["_elem_affinity_ready"] = {"stacks": 1}
                return
            if not is_mark:
                return
            ef = actor.get("effects") or {}
            if "_elem_affinity_ready" not in ef:
                return  # 无引爆后待增强标记
            ef.pop("_elem_affinity_ready", None)
            tgt = _act_target(battle, ctx, actor, target)
            if tgt is None:
                return
            _add_mark(tgt, mech, 1)
            logs.append(f"✨ {params.get('label') or '被动'}：元素亲和，挂印 +1 层！")
            return
        if mode == "sync":
            if is_mark:
                ef = actor.setdefault("effects", {})
                last = (ef.get("_elem_last_mark") or {}).get("kind")
                ef["_elem_last_mark"] = {"kind": mech}
                tgt = _act_target(battle, ctx, actor, target)
                if last == mech and tgt is not None:
                    _add_mark(tgt, mech, 1)
                    logs.append(f"✨ {params.get('label') or '被动'}：元素同调，挂印 +1 层！")
            elif not is_burst:
                # 非元素施法（普攻/其他系）打断连续记录
                (actor.get("effects") or {}).pop("_elem_last_mark", None)

    @register_action("passive_element_core_crit")
    def passive_element_core_crit(battle, caster, target, params, logs):
        """act_cast 元素之核：结算技时目标单系印记 ≥3 → 本次结算暴击 +20%。

        语义（desc 权威）：单系印记满 3 时该系结算暴击 +20%——引擎暴击整次技能单 roll，
        无法分系 → 目标有任意单系 ≥3 即整次结算暴击 +20%（近似 desc，buff 快照条
        crit 加算，覆盖整个结算技行动）。
        """
        ctx = getattr(battle, "_fire_ctx", None)
        if ctx is None:
            return
        actor = ctx.get("actor") or caster
        if actor is None:
            return
        info = ctx.get("info") or {}
        mech = info.get("mech") or ""
        if not str(mech).startswith("element_burst"):
            return  # 仅结算技（元素迸发/裁决/万象风暴）
        tgt = _act_target(battle, ctx, actor, target)
        if tgt is None:
            return
        add = float(params.get("add") or 0)
        if add <= 0:
            return  # 缺字段 = 无此行为
        _ef = tgt.get("effects") or {}
        hit = False
        for _mk in ("fire_mark", "ice_mark", "thunder_mark"):
            _en = _ef.get(_mk)
            if int(_en.get("stacks", 0) or 0) >= 3 if isinstance(_en, dict) else False:
                hit = True
                break
        if not hit:
            return
        buff_key = "passive_crit_element_core"
        actor.setdefault("effects", {})[buff_key] = {"stacks": 1, "stat": "crit",
                                                     "mult": add, "op": "add",
                                                     "expire": None}
        logs.append(f"✨ {params.get('label') or '被动'}：元素核心，结算暴击 +{int(add * 100)}%！")

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


# ============================================================
# v181.M-R2d：职业资源攒取渠道（事件型）——装配与动作
# ============================================================
# 渠道时机名 → (battle2 事件, 附加过滤参数)。语义源 = EFFECT_RULES 资源条目 channels
# 声明 + docs/REFACTOR_v181_CLASS_MECH_ASSEMBLY.md『M-R2d 渠道装配设计』§2.2：
#   heal_cast 治疗「施放」与「命中」同刻 → act_cast + kind=治疗（同 R4 holy_echo 折中；
#   每技能施放 fire 1 次，无多目标重复）；普攻（basic 经 do_skill）也 fire act_cast 但
#   kind=物理 → kind 过滤天然排除，不会误攒。
_CHANNEL_EVENTS = {
    "attack_hit": ("attack_hit", {}),            # 普攻命中
    "skill_hit": ("skill_hit", {}),              # 技能命中
    "heal_cast": ("act_cast", {"kind": "治疗"}),  # 治疗施放
    "taken": ("on_taken", {}),                   # 受击（真实承伤后，subject=受击者）
    "cast": ("act_cast", {"not_basic": True}),   # （预留）技能施放（未装配用）
}


def apply_class_channels(actor: dict, rules: dict) -> None:
    """EFFECT_RULES 资源条目 channels 声明 → actor.triggers 事件钩子（并入 apply_class_mech）。

    对每个声明了 channels 的资源条目（归属职业 start_classes 命中才装——防白拿）：
    时机名 → battle2 事件 → 挂 class_res_channel_gain 生产动作（gain 值由声明给，
    cap clamp 动作侧查 EFFECT_RULES）。未映射时机名静默跳过（版本漂移保护，同
    affix 翻译器缺口词条行为）。装配器零资源 key 硬编码——渠道全由声明驱动。
    """
    if not actor:
        return
    cn = actor.get("class_name") or ""
    trig = actor.setdefault("triggers", {})
    for rk, rc in (rules or {}).items():
        if not isinstance(rc, dict):
            continue
        ch = rc.get("channels")
        if not isinstance(ch, dict) or not ch:
            continue  # 无渠道声明 = 无此行为（零默认值铁律）
        sc = rc.get("start_classes") or []
        if sc and cn not in sc:
            continue
        name = rc.get("name") or rk
        for chan, gain in ch.items():
            if not chan or not isinstance(gain, (int, float)) or int(gain) <= 0:
                continue
            ev, extra = _CHANNEL_EVENTS.get(chan, (None, None))
            if ev is None:
                continue
            d = {"type": "class_res_channel_gain", "res": rk, "gain": int(gain),
                 "label": name, "icon": "✦"}
            d.update(extra)
            trig.setdefault(ev, []).append(d)


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


def _learned_proc(actor: dict, proc: str) -> bool:
    """actor 已学技能中是否带指定 passive.proc（链舞 finisher_up 等挂在主动技上）。

    装配器 apply_class_passives 只扫 kind=被动——主动技上的 proc 不装配 triggers，
    但可作为 MECH_CASH.upgrade 的"学到即升级"判据（扫 learned_skills 全表）。
    """
    if not actor or not proc:
        return False
    cn = actor.get("class_name") or ""
    names = actor.get("learned_skills") or []
    if not cn or not names:
        return False
    from .. import engine as E
    for s in names:
        try:
            info = E.skill_info(cn, s)
        except Exception:
            info = None
        if info and isinstance(info.get("passive"), dict) \
                and (info.get("passive") or {}).get("proc") == proc:
            return True
    return False


def _passive_proc_rules() -> dict:
    """PASSIVE_PROC 声明表（缺省空——装配器不崩）。"""
    try:
        from ..data.battle2_rules import PASSIVE_PROC
        return PASSIVE_PROC or {}
    except Exception:
        return {}


def apply_class_passives(actor: dict) -> None:
    """被动 proc 装配（v181.M-passive P1 插件样板）：扫已学 kind=被动 + passive.proc
    → 查 PASSIVE_PROC 声明表 → 参数化挂 actor.triggers[event]。学什么挂什么防白拿；
    表未声明 proc → 跳过（记缺口，不硬做）。
    domain 域（不进 triggers 的静态修正）：cap → 写 actor.bonus.cap[key] += add
    （资源上限被动：毒/猎印/魂标 cap——引擎 _cap_of 动态收敛已支持 bonus.cap）；
    cost → 写 actor.bonus.cost（消耗折扣：mp_pct/mp_flat/res——引擎 _skill_pay_of 折算）。
    """
    if not actor:
        return
    cn = actor.get("class_name") or ""
    names = actor.get("learned_skills") or []
    if not cn or not names:
        return
    install()
    rules = _passive_proc_rules()
    if not rules:
        return
    from .. import engine as E
    trig = actor.setdefault("triggers", {})
    _pending: dict = {}  # (event, agg) -> [(proc, entry)] 聚合族暂存（循环后归并单条）
    for s in names:
        try:
            info = E.skill_info(cn, s)
        except Exception:
            info = None
        if not info or info.get("kind") != "被动":
            continue
        p = info.get("passive") or {}
        proc = p.get("proc") or ""
        cfg = rules.get(proc)
        if not isinstance(cfg, dict):
            continue  # 表未声明 → 记缺口跳过（不硬做）
        domain = cfg.get("domain") or ""
        if domain == "cap":
            # 资源上限被动：bonus.cap[key] += add（cap 修正容器，_cap_of 动态读）
            key = cfg.get("cap_key") or proc
            try:
                add = int(p.get("add", cfg.get("add", 0)) or 0)
            except Exception:
                add = 0
            if add > 0:
                bonus = actor.setdefault("bonus", {})
                bonus.setdefault("cap", {})[key] = \
                    int((bonus.get("cap") or {}).get(key, 0) or 0) + add
            # 双通道声明（cap + event，如 soul_mark_cap/poison_cap_up 乘区段）→ 不 continue，fall through
        if domain == "cost":
            # 消耗折扣被动：bonus.cost（引擎 _skill_pay_of 折算）。mp_mult（如
            # 奥术恒常 mp_mult 0.5 = 奥术技能耗蓝-50%）→ 有 cfg.when 判据则放 when
            # 子条目（限定技能），无 when 才放顶层（无条件全技能）。
            pct = float(p.get("mp_mult", 0) or 0)
            when = cfg.get("when")
            bonus = actor.setdefault("bonus", {})
            _c = bonus.setdefault("cost", {})
            if when:
                _w = dict(when[0]) if isinstance(when, list) and when else {}
                _w["mp_pct"] = float(_w.get("mp_pct", 0) or 0) + pct
                _c.setdefault("when", []).append(_w)
            elif pct > 0:
                _c["mp_pct"] = float(_c.get("mp_pct", 0) or 0) + pct
            # cost 域声明无 event → 下方 d.type 空自然 continue
        d = {"type": cfg.get("action") or "", "judge": cfg.get("judge") or {}}
        # cfg 声明表非结构字段并入（buff_key 等动作参数——domain 消费过的键除外）
        for k, v in cfg.items():
            if k in ("event", "action", "judge", "agg", "domain",
                     "cap_key", "when", "add"):
                continue
            d[k] = v
        # 被动参数并入（mult 归一 mult/dmg_add/per_layer；label 用技能名）
        for k, v in p.items():
            if k in ("proc",):
                continue
            d[k] = v
        d.setdefault("label", info.get("name") or proc)
        if not d.get("type"):
            continue
        ev = cfg.get("event") or ""
        if not ev:
            continue
        # 聚合族（agg：counter 等——多条目合成一条，旧挂点聚合语义）暂存，循环后归并
        if cfg.get("agg"):
            _pending.setdefault((ev, cfg.get("agg")), []).append((proc, d))
        else:
            trig.setdefault(ev, []).append(d)
        # also 段：同被动第二条事件钩子（如坚城之姿 taken_calc 减伤 + turn_start 免晕）——
        # 复用 d 的参数，覆盖 action/judge/额外字段
        for _also in (cfg.get("also") or []):
            if not isinstance(_also, dict):
                continue
            _d2 = dict(d)
            _d2["type"] = _also.get("action") or d.get("type")
            if _also.get("judge"):
                _d2["judge"] = _also["judge"]
            for _k in ("ctrl", "ctrl_any", "res", "left_key", "left_init",
                       "cost_field", "buff_key"):
                if _also.get(_k) is not None:
                    _d2[_k] = _also[_k]
            _ev2 = _also.get("event") or ev
            if cfg.get("agg"):
                _pending.setdefault((_ev2, cfg.get("agg")), []).append((proc, _d2))
            else:
                trig.setdefault(_ev2, []).append(_d2)
        # 计数初始化（tenacity 每场 3 次：effects[left_key] = left_init——装配=开战时机）
        _le = cfg.get("left_key")
        if _le and cfg.get("left_init") is not None:
            actor.setdefault("effects", {})[_le] = {"stacks": int(cfg.get("left_init")),
                                                    "expire": None}
    # ---- 族级聚合（旧 passive_procs 聚合族语义逐字：多条目 → 单条终值）----
    for (ev, agg), entries in _pending.items():
        merged = _merge_agg_entry(agg, entries)
        if merged is not None:
            trig.setdefault(ev, []).append(merged)


def _res_ge_ok(actor: dict, judge: dict, params: dict) -> bool:
    """资源层数门槛判定（res_ge judge 通用）：effects[res].stacks ≥ 阈值。

    judge: {kind: res_ge, res, ge_field}; 阈值读 params[ge_field]（passive dict 并入）。
    """
    if not actor:
        return False
    res = (judge or {}).get("res") or ""
    ge_field = (judge or {}).get("ge_field") or ""
    need = float((params or {}).get(ge_field) or 0)
    if not res or need <= 0:
        return False
    _entry = ((actor.get("effects") or {})).get(res)
    cur = float(_entry.get("stacks", 0) or 0) if isinstance(_entry, dict) else 0.0
    return cur >= need


def _merge_agg_entry(agg: str, entries: list) -> dict:
    """聚合族归并：多条装配条目 → 单条终值 dict（返回 None = 无有效终值）。

    语义源 = 旧 passive_procs._h_* 聚合族 handler 逐字（挂点13 counter）：
    - counter_chance：chance 取 max、mult 取 min（以守为攻 35% ×80% 普攻档）
    - counter_up：chance += chance_add、mult ×= (1+dmg_add)（反击之王只首条加成）
    终值 atk_pct = mult（反击伤害 = 普攻 × mult，对齐 we_affix_counter 的 atk×atk_pct 直伤）。
    """
    if not entries:
        return None
    if agg == "counter":
        chance = 0.0
        mult = 1.0
        labels = []
        for proc, d in entries:
            labels.append(d.get("label") or proc)
            if proc == "counter_chance":
                _ch = float(d.get("chance", 0.0) or 0.0)
                _mu = float(d.get("mult", 0.0) or 0.0)
                if _ch <= 0 or _mu <= 0:
                    continue  # 缺字段 = 无此行为（零默认值铁律）
                chance = max(chance, _ch)
                mult = min(mult, _mu)
            elif proc == "counter_up":
                _ca = float(d.get("chance_add", 0.0) or 0.0)
                _da = float(d.get("dmg_add", 0.0) or 0.0)
                if _ca <= 0 or _da <= 0:
                    continue  # 缺字段 = 无此行为
                chance += _ca
                mult *= (1.0 + _da)
        if chance <= 0 or mult <= 0:
            return None
        return {"type": "passive_counter", "chance": min(chance, 0.9),
                "atk_pct": mult, "label": "+".join(dict.fromkeys(labels))}
    return None


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
        # v181.M-R2d：职业资源攒取渠道（事件型）——EFFECT_RULES 条目 channels 声明 → 事件钩子。
        # 核实结论（docs『M-R2d 渠道装配设计』§1）：现网仅牧师 faith 活 key 缺攒端（卸负消费 +
        # 治疗/受击渠道），rage/cp/chi/element 技能域死 key 不接（EFFECT_RULES 条目注释标注）。
        try:
            apply_class_channels(actor, _effect_rules())
        except Exception:
            pass  # 渠道装配异常不阻断开战（容错铁律）
        # v181.M-R2e B2：牧师信仰负载制装配——faith 条目声明 load_tiers（有档位表才挂，
        # 零默认值铁律）+ start_classes 归属过滤（非牧师不挂，防白拿 heal_calc 乘区）：
        #   heal_calc  → 施法时按自身 faith 层查档位 heal_mult 乘入（档位乘区）
        #   threshold  → 叠层到满 cap 的当次触发过载（清零 + 全队回复）
        try:
            _fc = (_effect_rules() or {}).get("faith") or {}
            if isinstance(_fc.get("load_tiers"), list) and _fc.get("load_tiers"):
                _fsc = _fc.get("start_classes") or []
                _cn2 = actor.get("class_name") or ""
                if not _fsc or _cn2 in _fsc:
                    trig.setdefault("heal_calc", []).append(
                        {"type": "class_faith_load_tier", "res": "faith"})
                    trig.setdefault("threshold", []).append(
                        {"type": "class_faith_overload", "res": "faith"})
        except Exception:
            pass  # 负载制装配异常不阻断开战（容错铁律）
        # v181.M-melody：诗人旋律装配——class=cls_shi_ren 且学了 melody/melody_chant
        # 系技能才挂 act_cast 触发器（学什么挂什么，零噪音；非诗人不挂）。
        try:
            _has_melody = any(
                (info.get("mech") in ("melody", "melody_chant"))
                for _s, info in _learned_mech_skills(actor))
            if _has_melody:
                trig.setdefault("act_cast", []).append(
                    {"type": "class_melody_act"})
        except Exception:
            pass  # melody 装配异常不阻断开战（容错铁律）
        # v181.M-passive P1：被动 proc 装配（扫已学 kind=被动 → PASSIVE_PROC 表挂 triggers）
        try:
            apply_class_passives(actor)
        except Exception:
            pass  # 被动装配异常不阻断开战（容错铁律）
        # v181 破绽接线：挂敌身条注入装配（BAR_INJECT_FIELDS 声明表 → skill_hit 触发器）
        try:
            from .battle2_bar_procs import apply_bar_procs
            apply_bar_procs(actor)
        except Exception:
            pass  # 挂条装配异常不阻断开战（容错铁律）
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
            if mode == "fury_enter":
                # 血祭：施放时花 res 层战意 → 进入狂暴（mech_val = 消耗层，技能数据）
                dm = {"action": "mech_cash_fury_enter", "mech": mech,
                      "res": cash.get("res") or "zhan_yi",
                      "mech_val_field": "mech_val",
                      "label": cash.get("label") or cash.get("name") or mech}
                if cash.get("icon"):
                    dm["icon"] = cash["icon"]
                trig.setdefault("act_cast", []).append(dm)
                continue
            if mode not in ("dmg_mult_clear", "dmg_mult_clear_target"):
                continue
            key = cash.get("key") or mech
            _per = float(cash.get("per_layer") or 0.0)
            # mech 升级（MECH_CASH.upgrade：学某 proc 被动 → 数值增强——链舞 finisher_up
            # 使终结技每段 10%→16%。proc 挂在 kind=物理 主动技上，装配器不装配，这里查学到）
            _up = cash.get("upgrade") or {}
            if isinstance(_up, dict) and _up.get("proc") and _learned_proc(actor, _up["proc"]):
                _per += float(_up.get("per_layer_add") or 0.0)
            dm = {"action": "mech_cash_dmg_mult", "mech": mech, "key": key,
                  "per_layer": _per,
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
