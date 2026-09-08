# -*- coding: utf-8 -*-
"""battle2 装备特效族扩展动作（game/services/battle2_we_procs.py，N9 形态 2）。

装配层把含"执行条件/复杂逻辑"的武器特效 key 翻译成族扩展动作注册进引擎
ACTION_HANDLERS（battle2 包外注册——引擎只当它是扩展动词执行，零知识）。

签名与引擎动词一致：fn(battle, caster, target, params, logs)
- caster/target：fire 事件上下文（hit：caster=攻击者 target=被打者；taken：caster=
  攻击者 target=受击者；battle_start：caster 缺省=声明者）
- params：装配层从 weapon_effect_data 生成的参数（key/dot_key/chance/pct 等）
- 事件数值（dmg/heal/amount/is_crit/overflow...）读 battle._fire_ctx（N9 fire 暂存）
- CD/次数/标记等持久状态写 actor["ext"]（引擎绝不读，扩展动作自管）

数值权威：全部读 params（装配层从数据表+we_data 翻译）；缺字段 = 无此行为。
"""
from __future__ import annotations

import random

from game.battle2.effects import register_action
from game.battle2.actors import state_add, actor_alive


def _roll(chance) -> bool:
    """概率判定：chance None（无字段）= 恒触发；0 不触发。"""
    if chance is None:
        return True
    try:
        if float(chance) <= 0:
            return False
        return random.random() < float(chance)
    except Exception:
        return True


def _hit_target(battle, target):
    """受击目标：params 无显式 target 时用 fire ctx 的 target（扩展动作兜底）。"""
    if target is not None and actor_alive(target):
        return target
    try:
        t = (battle._fire_ctx or {}).get("target")
        if t is not None and actor_alive(t):
            return t
    except Exception:
        pass
    return None


def _is_boss(actor) -> bool:
    return bool(actor and (actor.get("is_boss") or actor.get("role") == "boss"))


# ============================================================
# proc_dot（4 key：命中挂限时 DOT）
# ============================================================

_DOT_LOG = {
    "smith_blaze_wound": "🔥 裂伤：目标每刻损失生命（{turns} 刻）！",
    "rong_lu_yu_wen": "🔥 熔炉余温：目标每刻灼烧（{turns} 刻）！",
    "ember_burn": "🔥 烬燃：目标每刻燃烧（{turns} 刻）！",
    "blood_trace": "🩸 败血：目标 {turns} 刻内每刻损失当前生命！",
}


@register_action("we_dot")
def we_dot(battle, caster, target, params, logs):
    """命中挂 DOT（proc_dot）：chance → target 挂 state dot 层（数值/限时由
    STATE_EFFECTS dot 声明表；层 cap 声明）。同 key 重复命中叠层（cap 内）。"""
    tgt = _hit_target(battle, target)
    if not tgt:
        return
    if not _roll(params.get("chance")):
        return
    dot_key = params.get("dot_key")
    if not dot_key:
        return  # 缺字段 = 无此行为
    from game.battle2.state_effects import state_def
    cap = int((state_def(dot_key) or {}).get("cap") or 1)
    state_add(tgt, dot_key, int(params.get("amount", 1) or 1), cap=cap)
    turns = int(params.get("turns") or 0) or 3
    logs.append(_DOT_LOG.get(params.get("key"), f"🔥 {dot_key}：目标持续掉血（{turns} 刻）！"))


# ============================================================
# proc_reflect（5 key：受击反弹；纯反伤 2 + 附赠 3）
# ============================================================

_REFLECT_LOG = {
    "thorn_armor": "🌵 荆棘缠绕：反弹 {rd} 点伤害！",
    "retribution_ring": "⚔️ 复仇之环：反弹 {rd} 点伤害！",
    "iron_echo": "🪨 铁壁回响：反弹 {rd} 点伤害，并回复少量生命！",
    "dragon_spine_mail": "🐉 龙脊反噬：反弹 {rd} 点伤害，并施加重伤！",
    "ember_bulwark": "🔥 烬火燎原：反伤 {rd} 点并叠加灼烧！",
}


@register_action("we_reflect")
def we_reflect(battle, caster, target, params, logs):
    """受击反弹（proc_reflect，on_taken 事件）。事件主体过滤已保证只处理受击者自身
    声明 → 反射者 = _owner/受击者（target）；反弹对象 = _fire_ctx["source"]（攻击者）；
    反弹值基于 _fire_ctx["dmg"]。无攻击者（DOT/环境伤）不反射。

    key 语义：
    - thorn_armor 无条件 ×15%；retribution_ring chance ×30%
    - iron_echo chance ×40% + 反射者回 maxhp×heal_pct
    - dragon_spine_mail chance ×25% + 攻击者 heal_down（state 层，N9 收编）
    - ember_bulwark 整场首触发：max_hp_pct 反伤 + 攻击者 burn 叠层
    反射伤害 source = 反射者（受击者），target = 攻击者（等级压制/击杀归属正确）。
    """
    if target is None:
        return  # 无反射者（受击者）
    key = params.get("key") or ""
    deflector = params.get("_owner") or target   # 装备持有者 = 反射者
    if not actor_alive(deflector):
        return
    if not _roll(params.get("chance")):
        return
    ctx = getattr(battle, "_fire_ctx", None) or {}
    attacker = ctx.get("source")
    if attacker is None or not actor_alive(attacker):
        return  # 无攻击来源（DOT/环境伤）不反射
    rd = 0
    if key == "ember_bulwark":
        # 整场一次（ext 自管标记）
        eff = deflector.setdefault("ext", {}).setdefault("we_proc", {})
        if eff.get("ember_bulwark_used"):
            return
        eff["ember_bulwark_used"] = True
        rd = max(1, int(deflector.get("max_hp", 100) * float(params.get("max_hp_pct", 0.05))))
        if rd > 0:
            from game.battle2.landing import deal_damage
            deal_damage(battle, deflector, attacker, rd, logs)
            from game.battle2.state_effects import state_def
            cap = int((state_def("burn") or {}).get("cap") or 5)
            state_add(attacker, "burn", int(params.get("burn_stack", 1) or 1), cap=cap)
        logs.append(_REFLECT_LOG.get(key, "").format(rd=rd))
        return
    if params.get("reflect_pct") is not None:
        dmg = int(ctx.get("dmg", 0) or 0)
        rd = max(1, int(dmg * float(params.get("reflect_pct", 0))))
    if rd > 0:
        from game.battle2.landing import deal_damage
        deal_damage(battle, deflector, attacker, rd, logs)
        if key == "iron_echo":
            hpv = float(params.get("heal_pct", 0.02) or 0)
            from game.battle2.landing import heal_actor
            heal_actor(battle, deflector, int(deflector.get("max_hp", 100) * hpv), logs)
        elif key == "dragon_spine_mail":
            from game.battle2.state_effects import state_def
            cap = int((state_def("heal_down") or {}).get("cap") or 5)
            state_add(attacker, "heal_down", int(params.get("heal_down", 2) or 2), cap=cap)
    logs.append(_REFLECT_LOG.get(key, "").format(rd=rd))


# ============================================================
# proc_shield taken 概率盾（sentinel/deeprock：chance + cd 冷却）
# ============================================================

_SHIELD_TAKEN_LOG = {
    "sentinel_aegis": "🛡️ 哨兵壁垒：获得 {shield} 点护盾！（3 刻）",
    "deeprock_aegis": "🪨 深岩壁垒：获得护盾！（吸收 8% 最大生命）",
}


@register_action("we_shield_taken")
def we_shield_taken(battle, caster, target, params, logs):
    """受击概率盾（proc_shield taken，on_taken）：cd 冷却 → chance → 上盾。

    owner = _owner/受击者；盾值 sentinel = base+per_lv×lv，deeprock = shield_pct×maxhp；
    cd 存 owner.ext.we_proc（cd_key → ready_at 绝对时刻，ACT_TICK 折算）。
    """
    owner = params.get("_owner") or target
    if owner is None or not actor_alive(owner):
        return
    cd_key = params.get("cd_key")
    now = float(getattr(battle, "_now", 0) or 0)
    st = owner.setdefault("ext", {}).setdefault("we_proc", {})
    if cd_key:
        if float(st.get(cd_key, 0) or 0) > now:
            return  # cd 中
    if not _roll(params.get("chance")):
        return
    # 盾值
    if params.get("base") is not None or params.get("per_lv") is not None:
        lv = int(owner.get("level", 1) or 1)
        value = int(float(params.get("base") or 0) + float(params.get("per_lv") or 0) * lv)
    elif params.get("shield_pct") is not None:
        value = int(owner.get("max_hp", 100) * float(params["shield_pct"]))
    else:
        return
    if value <= 0:
        return
    key = params.get("shield_key") or "we_sentinel"
    turns = int(params.get("turns") or 3)
    from game.battle2.effects import act_shield
    act_shield(battle, owner, owner,
               {"type": "shield", "key": key, "value": value, "turns": turns, "on": "caster"},
               logs)
    if cd_key:
        from game.core.constants import ACT_TICK
        st[cd_key] = now + int(params.get("cd") or 1) * ACT_TICK
    logs.append(_SHIELD_TAKEN_LOG.get(params.get("key") or "", f"🛡️ 获得护盾 {value} 点！").format(shield=value))


# ============================================================
# proc_retort_mark guardian_will（受击给攻击者挂减攻）
# ============================================================


@register_action("we_guardian_will")
def we_guardian_will(battle, caster, target, params, logs):
    """卫士信念：受击 chance → 攻击者下一次攻击伤害 -weaken%（攻方 buff atk mul 0.75）。"""
    owner = params.get("_owner") or target
    if owner is None or not actor_alive(owner):
        return
    if not _roll(params.get("chance")):
        return
    ctx = getattr(battle, "_fire_ctx", None) or {}
    attacker = ctx.get("source")
    if attacker is None or not actor_alive(attacker):
        return
    weaken = float(params.get("weaken", 0.25) or 0.25)
    from game.battle2.effects import act_buff
    act_buff(battle, attacker, attacker,
             {"type": "buff", "key": params.get("debuff_key") or "mon_atk_down",
              "stat": "atk", "op": "mul", "mult": 1.0 - weaken,
              "turns": int(params.get("turns", 1) or 1), "on": "caster"}, logs)
    logs.append("🛡️ 卫士信念：敌人下一次攻击伤害 -25%！")


# ============================================================
# proc_shield 条件盾（threshold 低保 3 + heal 溢出 2 + crit 1）
# ============================================================

_SHIELD_COND_LOG = {
    "bedrock_crown": "🪨 磐石守护：生命垂危，获得 {shield} 点护盾！（4 刻）",
    "firmament_crown": "🌌 苍穹庇护：获得 {shield} 点护盾！",
    "gargoyle_heart": "💎 石像鬼之心：获得 {shield} 点护盾并回复 {heal} 点生命！",
    "echo_bless": "🌿 回响祝福：治疗溢出转化为 {shield} 点护盾！",
    "atonement_shield": "⚖️ 赎罪之盾：治疗溢出转化为 {shield} 点护盾！",
    "endless_radiance": "🌟 无尽辉光：暴击获得 {shield} 点护盾！",
}


def _add_owner_shield(battle, owner, params, value, logs):
    from game.battle2.effects import act_shield
    act_shield(battle, owner, owner,
               {"type": "shield", "key": params.get("shield_key") or "we_shield",
                "value": value, "turns": int(params.get("turns") or 3), "on": "caster"},
               logs)


@register_action("we_shield_cond")
def we_shield_cond(battle, caster, target, params, logs):
    """条件护盾（proc_shield 条件型）——事件由装配层挂载，执行器按 key 语义：

    - bedrock/gargoyle（on_taken 后自查）：hp 低于 threshold → 整场一次低保盾
      （gargoyle 附回血）
    - firmament（on_taken 后自查）：hp 低于 threshold → 限 per_battle 次低保盾
    - echo_bless/atonement（on_heal）：治疗溢出转盾（_fire_ctx.overflow）
    - endless_radiance（crit）：暴击 + cd → 盾
    状态（used/次数/cd）存 owner.ext.we_proc。
    """
    owner = params.get("_owner") or target
    if owner is None or not actor_alive(owner):
        return
    key = params.get("key") or ""
    st = owner.setdefault("ext", {}).setdefault("we_proc", {})
    ctx = getattr(battle, "_fire_ctx", None) or {}
    now = float(getattr(battle, "_now", 0) or 0)
    # ---- heal 溢出转盾 ----
    if key in ("echo_bless", "atonement_shield"):
        overflow = int(ctx.get("overflow", 0) or 0)
        if overflow <= 0:
            return
        cap = int(owner.get("max_hp", 100) * float(params.get("cap_hp_pct") or 0.10))
        if key == "echo_bless":
            shield = min(cap, int(overflow * float(params.get("overflow_pct") or 0.30)))
        else:
            shield = min(cap, overflow)
        if shield > 0:
            _add_owner_shield(battle, owner, params, shield, logs)
            logs.append(_SHIELD_COND_LOG.get(key, "").format(shield=shield))
        return
    # ---- crit 盾（endless_radiance：装配层挂 crit 事件 → 到达即暴击）----
    if key == "endless_radiance":
        if float(st.get(params.get("cd_key"), 0) or 0) > now:
            return
        shield = int(owner.get("max_hp", 100) * float(params.get("shield_hp_pct") or 0.05))
        from game.core.constants import ACT_TICK
        _add_owner_shield(battle, owner, params, shield, logs)
        st[params.get("cd_key") or "we_radiance_cd"] = now + int(params.get("cd") or 3) * ACT_TICK
        logs.append(_SHIELD_COND_LOG.get(key, "").format(shield=shield))
        return
    # ---- threshold 低保盾（bedrock/gargoyle/firmament）----
    used_key = params.get("used_key")
    if key == "firmament_crown":
        n = int(st.get(used_key, 0) or 0)
        if n >= int(params.get("per_battle") or 2):
            return
    else:
        if st.get(used_key):
            return
    ratio = float(owner.get("hp", 0)) / max(1, owner.get("max_hp", 1) or 1)
    if ratio >= float(params.get("threshold") or 0.30):
        return  # 血量未到阈值
    if key == "firmament_crown":
        st[used_key] = int(st.get(used_key, 0) or 0) + 1
    else:
        st[used_key] = True
    shield = int(owner.get("max_hp", 100) * float(params.get("shield_hp_pct") or 0.2))
    _add_owner_shield(battle, owner, params, shield, logs)
    if key == "gargoyle_heart":
        heal = int(owner.get("max_hp", 100) * float(params.get("heal_pct") or 0.1))
        from game.battle2.landing import heal_actor
        heal_actor(battle, owner, heal, logs)
        logs.append(_SHIELD_COND_LOG.get(key, "").format(shield=shield, heal=heal))
    else:
        logs.append(_SHIELD_COND_LOG.get(key, "").format(shield=shield))


def _crit_flag(ctx: dict) -> bool:
    """crit 事件判定兜底：crit 事件 ctx 无 is_crit 键（事件本身即暴击）——
    由装配层区分：endless_radiance 挂 crit 事件时恒为暴击 → ctx 带 is_crit=True 由
    fire 暂存补充不了，这里约定 crit 事件挂载的 effect 直接视为暴击。
    """
    # fire crit 事件 ctx 不设 is_crit；on_hit 类也不该挂 endless_radiance——
    # 装配层把 endless_radiance 挂 crit 事件 → 到达执行器即暴击。
    return True


# ============================================================
# 注册入口（装配层 install_ext_actions 调，幂等）
# ============================================================

_INSTALLED = False


def ensure_registered() -> None:
    """注册全部族扩展动作（battle2_equip_proc.apply_to_actor 前调一次）。"""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True
    # 装饰器已随模块 import 注册（register_action 模块级执行）——本函数仅做幂等标记
