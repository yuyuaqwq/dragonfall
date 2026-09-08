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
# proc_buff abyss_barrier（battle_start 永久最大生命加成）
# ============================================================


@register_action("we_abyss")
def we_abyss(battle, caster, target, params, logs):
    """深渊屏障（proc_buff abyss_barrier，battle_start 整场一次）：
    最大生命 +max_hp_pct×当前 maxhp，hp 同步等量增加。ext 标记防重复。"""
    owner = params.get("_owner") or caster
    if owner is None:
        return
    st = owner.setdefault("ext", {}).setdefault("we_proc", {})
    if st.get("abyss_used"):
        return
    st["abyss_used"] = True
    bonus = int(owner.get("max_hp", 100) * float(params.get("max_hp_pct") or 0.08))
    if bonus > 0:
        owner["max_hp"] = owner.get("max_hp", 100) + bonus
        owner["hp"] = min(owner["max_hp"], owner.get("hp", 0) + bonus)
        logs.append(params.get("log") or f"🌑 深渊屏障：最大生命 +{bonus}！（持续整场）")


# ============================================================
# proc_extra_dmg（11 key：命中追击直伤/真伤/吸血）
# ============================================================

_EXTRA_LOG = {
    "afterglow_splash": "🌅 余波 溅射 {dmg} 点奥术伤害！",
    "spellblade_echo": "🔮 咒刃 溅射 {dmg} 点奥术伤害！",
    "annihilation_echo": "💥 湮灭回响 溅射 {dmg} 点奥术伤害！",
    "wind_split": "🌪️ 裂风矢 追加 {dmg} 点伤害！",
    "endless_blade": "⚔️ 无尽锋芒 追加 {dmg} 点伤害！",
    "hunter_open": "🗡️ 破绽 造成 {dmg} 点真实伤害！",
    "siren_fang": "🧜 海妖猎杀 造成 {dmg} 点真实伤害！",
    "star_pierce": "☄️ 穿星 造成 {dmg} 点真实伤害！",
}


def _owner_stats(battle, owner):
    from game.battle2 import stats as S
    try:
        return S.actor_stats(battle, owner)
    except Exception:
        return dict(owner)


def _target_def_stats(battle, target):
    from game.battle2 import stats as S
    try:
        return S.actor_stats(battle, target)
    except Exception:
        return dict(target)


def _calc(battle, atk_val, def_val, dmg_type="phys", pene_pct=0.0):
    from game import engine as E
    try:
        if dmg_type == "true":
            return max(1, E.calc_damage(int(atk_val), 0, False, dmg_type="true"))
        return max(1, E.calc_damage(int(atk_val), int(def_val), False,
                                    pene_pct=pene_pct, dmg_type=dmg_type))
    except Exception:
        return max(1, int(atk_val))


@register_action("we_extra_dmg")
def we_extra_dmg(battle, caster, target, params, logs):
    """命中追击（proc_extra_dmg，hit/skill_hit 事件，主体=攻击者即 owner）。
    mode 分派（表字段权威；RNG 在 chance/计数保底处各消耗一次，同旧语义）：
    - splash_magi（afterglow/spellblade_echo/annihilation）：matk×pct vs mdef 溅射
    - extra_phys（wind_split）：atk×pct vs def
    - extra_phys_pene（phantom_barrage）：计数 + chance/保底 → atk×pct vs def×(1-pene)
    - extra_phys_oncrit（endless_blade）：crit 事件 + cd 1 刻 → atk×pct 追加
    - true_dmg_nth（hunter/siren/star）：计数到 count → atk×pct 真伤（star 加已损 bonus cap）
    - curhp_dmg_heal（soul_eater）：敌当前 hp×pct（cap atk）伤 + 回等量
    - lifesteal（novice_lifesteal）：hit dmg×heal_pct 回血
    计数/CD 存 owner.ext.we_proc。
    """
    owner = params.get("_owner") or caster
    if owner is None or not actor_alive(owner):
        return
    ctx = getattr(battle, "_fire_ctx", None) or {}
    tgt = ctx.get("target") or target
    if tgt is None or not actor_alive(tgt):
        return
    key = params.get("key") or ""
    mode = params.get("mode") or ""
    st = owner.setdefault("ext", {}).setdefault("we_proc", {})
    # ---- lifesteal：本击伤害回血 ----
    if key == "novice_lifesteal":
        dmg = int(ctx.get("dmg", 0) or 0)
        if dmg <= 0:
            os_ = _owner_stats(battle, owner)
            dmg = int(os_.get("atk", 0) or 0)
        heal = int(dmg * float(params.get("heal_pct") or 0.05))
        if heal > 0:
            from game.battle2.landing import heal_actor
            heal_actor(battle, owner, heal, logs)
        return
    # ---- 概率前置（溅射/裂风）----
    if mode in ("splash_magi", "extra_phys", "extra_phys_pene"):
        if not _roll(params.get("chance")):
            return
    os_ = _owner_stats(battle, owner)
    es_ = _target_def_stats(battle, tgt)
    # ---- extra_phys_pene（phantom：计数保底）----
    if key == "phantom_barrage":
        sk = params.get("stack_key") or "phantom_cnt"
        n = int(st.get(sk, 0) or 0) + 1
        st[sk] = n
        if n < int(params.get("guarantee") or 5) and random.random() >= float(params.get("chance") or 0.2):
            return
        st[sk] = 0
        dmg = _calc(battle, int(os_.get("atk", 0)) * float(params.get("atk_pct") or 0.3),
                    es_.get("def", 0), pene_pct=float(params.get("pene_pct") or 0.5))
        from game.battle2.landing import deal_damage
        deal_damage(battle, owner, tgt, dmg, logs)
        logs.append(params.get("log") or f"🌪️ 幻影连射！无视 50% 防御造成 {dmg} 点伤害！")
        return
    # ---- splash_magi（matk 溅射）----
    if mode == "splash_magi":
        dmg = _calc(battle, int(os_.get("matk", 0)) * float(params.get("atk_pct") or 0.15),
                    es_.get("mdef", 0), dmg_type="magi")
        from game.battle2.landing import deal_damage
        deal_damage(battle, owner, tgt, dmg, logs)
        logs.append(_EXTRA_LOG.get(key, "🔮 溅射 {dmg} 点奥术伤害！").format(dmg=dmg))
        return
    # ---- extra_phys_oncrit（endless_blade：crit + cd 1 刻限 1）----
    if key == "endless_blade":
        now = float(getattr(battle, "_now", 0) or 0)
        cd_key = params.get("used_key") or "we_blade_cd"
        if float(st.get(cd_key, 0) or 0) > now:
            return
        from game.core.constants import ACT_TICK
        st[cd_key] = now + ACT_TICK  # 1 刻冷却（"每刻限 1"）
        dmg = _calc(battle, int(os_.get("atk", 0)) * float(params.get("atk_pct") or 0.2),
                    es_.get("def", 0))
        from game.battle2.landing import deal_damage
        deal_damage(battle, owner, tgt, dmg, logs)
        logs.append(_EXTRA_LOG.get(key, "⚔️ 追加 {dmg} 点伤害！").format(dmg=dmg))
        return
    # ---- extra_phys（wind_split）----
    if mode == "extra_phys":
        dmg = _calc(battle, int(os_.get("atk", 0)) * float(params.get("atk_pct") or 0.5),
                    es_.get("def", 0))
        from game.battle2.landing import deal_damage
        deal_damage(battle, owner, tgt, dmg, logs)
        logs.append(_EXTRA_LOG.get(key, "💥 追加 {dmg} 点伤害！").format(dmg=dmg))
        return
    # ---- true_dmg_nth（hunter/siren/star 计数真伤）----
    if mode == "true_dmg_nth":
        sk = params.get("stack_key") or key + "_cnt"
        n = int(st.get(sk, 0) or 0) + 1
        st[sk] = n
        if n < int(params.get("count") or 3):
            return
        st[sk] = 0
        base = int(os_.get("atk", 0)) * float(params.get("atk_pct") or 0.2)
        if key == "star_pierce":
            lost = int((tgt.get("max_hp", 0) - tgt.get("hp", 0)) * float(params.get("lost_hp_pct") or 0.03))
            cap = int(tgt.get("max_hp", 1) * float(params.get("cap_pct") or 0.05))
            base = base + min(lost, cap)
        dmg = _calc(battle, base, 0, dmg_type="true")
        from game.battle2.landing import deal_damage
        deal_damage(battle, owner, tgt, dmg, logs)
        logs.append(_EXTRA_LOG.get(key, "✨ 造成 {dmg} 点真实伤害！").format(dmg=dmg))
        return
    # ---- curhp_dmg_heal（soul_eater）----
    if key == "soul_eater":
        cap = max(1, int(os_.get("atk", 0) or 0))
        bonus = min(cap, max(1, int(tgt.get("hp", 0) * float(params.get("cur_hp_pct") or 0.02))))
        if bonus > 0:
            from game.battle2.landing import deal_damage, heal_actor
            deal_damage(battle, owner, tgt, bonus, logs)
            healed = heal_actor(battle, owner, bonus, logs)
            logs.append("💜 破败之吻：额外 {bonus} 点伤害，回复 {healed} 点生命！".format(bonus=bonus, healed=healed))
        return


# ============================================================
# proc_aux novice_dawn_mana（施法首次回蓝）
# ============================================================


@register_action("we_mana_once")
def we_mana_once(battle, caster, target, params, logs):
    """晨星回蓝（novice_dawn_mana，skill_cast 事件）：整场首次施法回蓝。"""
    owner = params.get("_owner") or caster
    if owner is None:
        return
    st = owner.setdefault("ext", {}).setdefault("we_proc", {})
    if st.get("dawn_mana_used"):
        return
    st["dawn_mana_used"] = True
    mp = int(params.get("mp") or 10)
    owner["mp"] = min(int(owner.get("max_mp", 999) or 999), int(owner.get("mp", 0) or 0) + mp)
    logs.append(params.get("log") or f"🌅 晨星：回复 {mp} 点魔力！")


# ============================================================
# proc_control（9 key 敌方控制：7 可迁 + randuin/ice_vein 依赖 enemy_act 事件
# ——battle2 无"敌人行动后"事件点位，留缺口记录（见 docs/N9 施工文档 §1.3））
# ============================================================

_CONTROL_LOG = {
    "frost_ring": "🧊 霜环：目标被冻结 {turns} 刻！",
    "holy_judgment_field": "⚖️ 圣裁领域：目标受治疗 -30%（2 刻）！",
    "everfrost_domain": "🧊 永冻领域：目标被冻结 {turns} 刻！",
    "everfrost_scepter": "🧊 永霜禁锢：目标被冻结 {turns} 刻！",
    "frost_crown": "🧊 寒霜凝视：目标被冻结 {turns} 刻！",
    "holy_word_bind": "✨ 圣言禁锢：目标被冻结 {turns} 刻！",
    "time_freeze": "⏳ 时光凝滞！敌人被定身，跳过一次行动！",
}


def _control_target(battle, target, params) -> dict:
    """控制作用目标（owner = 装备者）：
    - hit/skill_hit 事件：被打者（ctx.target，非 owner）
    - taken 事件：攻击者 ctx.source（受击反冻——不控自己）
    - heal 事件：敌对首选存活（治疗控场）
    目标非 owner 自己时优先 target（hit 被打者）。
    """
    ctx = getattr(battle, "_fire_ctx", None) or {}
    ev = ctx.get("_event") or ""
    owner = params.get("_owner")
    if ev in ("taken",):
        t = ctx.get("source")
        if t is not None and actor_alive(t):
            return t
    if target is not None and target is not owner and actor_alive(target):
        return target
    if ev in ("heal",):
        pass  # fallthrough 敌对首选
    t = ctx.get("source")
    if t is not None and t is not owner and actor_alive(t):
        return t
    # 兜底：敌对首个存活
    for acts in battle.sides.values():
        for a in acts:
            if a is not owner and actor_alive(a) and not a.get("human_controlled"):
                return a
    return None


def _freeze(battle, owner, tgt, turns, params, logs):
    """冻结（Boss 减半沿用引擎 act_control 定稿语义，不迁旧免疫退化特例）。"""
    from game.battle2.effects import act_control
    act_control(battle, owner, tgt,
                {"type": "control", "tag": "freeze", "turns": turns, "mode": "skip"}, logs)


def _slow(battle, owner, tgt, turns, pct, logs):
    """减速：敌 spd×（1-pct）buff（battle2 buff 快照折算）。"""
    from game.battle2.effects import act_buff
    act_buff(battle, owner, tgt,
             {"type": "buff", "key": "spd_down", "stat": "spd", "op": "mul",
              "mult": 1.0 - float(pct), "turns": turns, "on": "target"}, logs)


@register_action("we_control")
def we_control(battle, caster, target, params, logs):
    """敌方控制（proc_control）：mode 分派。目标 = hit/skill_hit 被打者 /
    taken 攻击者 / heal 敌对首选。状态（次数/cd/used）存 owner.ext.we_proc。"""
    owner = params.get("_owner") or caster
    if owner is None or not actor_alive(owner):
        return
    key = params.get("key") or ""
    mode = params.get("mode") or "freeze"
    tgt = _control_target(battle, target, params)
    if tgt is None or not actor_alive(tgt):
        return
    st = owner.setdefault("ext", {}).setdefault("we_proc", {})
    ctx = getattr(battle, "_fire_ctx", None) or {}
    now = float(getattr(battle, "_now", 0) or 0)
    # ---- 前置：cd（everfrost_domain）----
    cd_key = params.get("cd_key")
    if cd_key and float(st.get(cd_key, 0) or 0) > now:
        return
    # ---- 前置：限次（frost_crown 每场 max_per_battle）----
    used_key = params.get("used_key")
    limit = int(params.get("max_per_battle") or 0) if params.get("max_per_battle") is not None else 0
    if limit > 0 and int(st.get(used_key, 0) or 0) >= limit:
        return
    # ---- chance ----
    if not _roll(params.get("chance")):
        return
    src_turns = int(params.get("freeze_turns") or params.get("turns") or 1)
    if mode == "slow_or_freeze":
        # frost_ring：已减速 → 冻结；否则减速
        if (tgt.get("buffs") or {}).get("spd_down"):
            _freeze(battle, owner, tgt, src_turns, params, logs)
            _bump_control_state(st, cd_key, used_key, params, now)
            logs.append(_CONTROL_LOG.get(key, "🧊 冻结！").format(turns=src_turns))
        else:
            _slow(battle, owner, tgt, int(params.get("slow_turns") or 2),
                  float(params.get("slow_pct") or 0.4), logs)
        return
    if mode == "slow_heal_down":
        _slow(battle, owner, tgt, int(params.get("slow_turns") or 2),
              float(params.get("slow_pct") or 0.3), logs)
        from game.battle2.state_effects import state_def
        cap = int((state_def("heal_down") or {}).get("cap") or 5)
        state_add(tgt, "heal_down", int(params.get("heal_down") or 2), cap=cap)
        logs.append(_CONTROL_LOG.get(key, "⚖️ 圣裁领域！").format(turns=0))
        return
    if mode == "freeze_cd":
        _freeze(battle, owner, tgt, src_turns, params, logs)
        if cd_key:
            from game.core.constants import ACT_TICK
            st[cd_key] = now + int(params.get("cd") or 1) * ACT_TICK
        logs.append(_CONTROL_LOG.get(key, "🧊 永冻！").format(turns=src_turns))
        return
    if mode == "freeze":
        _freeze(battle, owner, tgt, src_turns, params, logs)
        logs.append(_CONTROL_LOG.get(key, "🧊 冻结！").format(turns=src_turns))
        return
    if mode == "freeze_taken_limited":
        # frost_crown：受击冻结限次（先计数后冻结）
        if used_key:
            st[used_key] = int(st.get(used_key, 0) or 0) + 1
        _freeze(battle, owner, tgt, src_turns, params, logs)
        logs.append(_CONTROL_LOG.get(key, "🧊 冻结！").format(turns=src_turns))
        return
    if mode == "freeze_heal":
        if ctx.get("overflow"):
            return
        _freeze(battle, owner, tgt, src_turns, params, logs)
        logs.append(_CONTROL_LOG.get(key, "✨ 禁锢！").format(turns=src_turns))
        return
    if mode == "threshold_stun":
        # time_freeze：玩家 hp 低阈值（挂 on_taken 自查）每场一次
        if st.get(used_key):
            return
        ratio = float(owner.get("hp", 0)) / max(1, owner.get("max_hp", 1) or 1)
        if ratio >= float(params.get("threshold") or 0.30):
            return
        st[used_key] = True
        from game.battle2.effects import act_control
        act_control(battle, owner, tgt,
                    {"type": "control", "tag": "stun", "turns": 1, "mode": "skip"}, logs)
        logs.append(_CONTROL_LOG.get(key, "⏳ 时光凝滞！"))
        return
    return  # 未知 mode 静默


def _bump_control_state(st, cd_key, used_key, params, now):
    from game.core.constants import ACT_TICK
    if cd_key:
        st[cd_key] = now + int(params.get("cd") or 1) * ACT_TICK


# ============================================================
# 乘区修正动作（N9.13：dmg_calc/taken_calc 事件消费）
# ============================================================

_MULT_TAG = {
    "hp_target_lt": "💀处决",
    "hp_self_lt": "🔥残血",
    "target_marked": "🎯追猎",
    "always": "🛡️",
}


@register_action("we_dmg_mult_cond")
def we_dmg_mult_cond(battle, caster, target, params, logs):
    """条件增伤乘区（dmg_calc 事件，攻击者视角）：cond 命中 → _fire_ctx.mult ×= 值。
    条件谓词全在扩展动作（引擎零知识）：
    - hp_target_lt：目标生命低于阈值（处决 execute：<30% ×1.3）
    - hp_self_lt：自己生命低于阈值（残血增伤）
    - always：无条件（叠层放大器常驻段等）"""
    ctx = getattr(battle, "_fire_ctx", None)
    if ctx is None:
        return
    owner = params.get("_owner") or caster
    tgt = ctx.get("target") or target
    cond = params.get("cond") or "always"
    mult = float(params.get("mult") or 0)
    if mult <= 0:
        return
    hit = False
    try:
        if cond == "hp_target_lt":
            if tgt is not None and actor_alive(tgt) and tgt.get("hp") is not None:
                hit = (float(tgt.get("hp", 0)) / max(1, float(tgt.get("max_hp", 1) or 1))
                       < float(params.get("threshold") or 0.30))
        elif cond == "hp_self_lt":
            if owner is not None and owner.get("hp") is not None:
                hit = (float(owner.get("hp", 0)) / max(1, float(owner.get("max_hp", 1) or 1))
                       < float(params.get("threshold") or 0.30))
        else:
            hit = True
    except Exception:
        hit = False
    if hit:
        ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * mult
        tag = params.get("tag") or _MULT_TAG.get(cond, "")
        if tag:
            ctx["tags"] = list(ctx.get("tags") or []) + [f"{tag}x{mult:.2f}"]


@register_action("we_taken_mult_cond")
def we_taken_mult_cond(battle, caster, target, params, logs):
    """条件减伤乘区（taken_calc 事件，承伤者视角）：cond 命中 → _fire_ctx.mult ×= 值
    （值 <1 = 减伤：death_dance 8% → 0.92；沸血怒气满全减伤 0.92）。
    谓词：always / hp_self_lt / state_full（state 满层：rage_full 怒气满）"""
    ctx = getattr(battle, "_fire_ctx", None)
    if ctx is None:
        return
    owner = params.get("_owner") or target
    cond = params.get("cond") or "always"
    mult = float(params.get("mult") or 0)
    if mult <= 0:
        return
    hit = False
    try:
        if cond == "hp_self_lt":
            if owner is not None and owner.get("hp") is not None:
                hit = (float(owner.get("hp", 0)) / max(1, float(owner.get("max_hp", 1) or 1))
                       < float(params.get("threshold") or 0.30))
        elif cond.startswith("state_full"):
            sk = params.get("state_key") or ""
            if owner is not None and sk:
                st = owner.get("state") or {}
                cap = int((_state_cap(sk) or 0))
                hit = cap > 0 and int(st.get(sk, 0) or 0) >= cap
        else:
            hit = True
    except Exception:
        hit = False
    if hit:
        ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * mult
        tag = params.get("tag") or ""
        if tag:
            ctx["tags"] = list(ctx.get("tags") or []) + [f"{tag}x{mult:.2f}"]


def _state_cap(key: str) -> int:
    try:
        from game.battle2.state_effects import state_def
        return int((state_def(key) or {}).get("cap") or 0)
    except Exception:
        return 0


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
