# -*- coding: utf-8 -*-
"""v181.P2C-C2 武器特效族执行器注册表（试点 3 族）——由 weapon_effects.py proc() 分发消费。

**读表参数、代码零默认值铁律**：所有数值来自 effect_data() 返回的 wd（weapon_effect_data
表权威 + 装备行 we_data 覆盖层）。缺字段 = 无此行为——**绝不补默认值**（C1 已核表值 =
handler 原硬编码值，diff=0，读表安全）。唯一例外：行为控制位（bool/事件存在性）由
wd 中字段存在性决定，handler 里"无条件执行"的族（如 heal_amp 不需要额外开关）直接执行。

签名约定：fn(battle, player, ctx, logs, wd, key) —— 与旧 _we_* handler 同 battle/player/
ctx/logs 对象，wd = effect_data(battle, player, key)，key = 触发装备特效 key（日志兜底用）。
"""

# ---------------------------------------------------------------- 依赖
import random

# ---------------------------------------------------------------- proc_dot（4 key）
# 命中后给敌方挂 DOT（maxhp% / curhp%）。事件 hit/skill_hit 由数据表 family 默认事件表
# 分发（见 weapon_effects.py proc()），执行器本身不关心事件。

def _we_exec_dot(battle, player, ctx, logs, wd, key):
    """DOT 执行器：chance 判定 → 目标 pct 判定（boss/精英 vs 普通）→ 写敌方 debuffs。

    覆盖 smith_blaze_wound/rong_lu_yu_wen/ember_burn（走 _apply_dot 共享动作）与
    blood_trace（当前生命%，直接写 debuffs + 原文案日志）。
    """
    # chance：缺字段（无 chance）= 不触发（无此行为铁律）
    if float(wd.get("chance") or 0) <= 0 or "chance" not in wd:
        return
    if random.random() >= float(wd["chance"]):
        return
    # 目标：battle.enemy（与旧 handler 一致；ctx 不携带目标）
    if not battle.enemy:
        return
    # 延迟取共享动作（weapon_effects 模块已完全加载后才可能调执行器——proc 延迟 import）
    from .weapon_effects import _apply_dot, _boss_enemy
    if key == "blood_trace":
        # 败血：当前生命%（pct_boss 对 Boss/精英），非 _apply_dot maxhp 语义（原 handler 直写）
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.get("blood_trace") or {"n": 0, "mult": 1.0}
        cur["n"] = min(int(cur.get("n", 0) or 0) + 1, 1)
        cur["pct"] = float(wd["pct_boss"]) if _boss_enemy(battle.enemy) else float(wd["pct"])
        cur["turns"] = int(wd["turns"])
        deb["blood_trace"] = cur
        logs.append("🩸 败血：目标 4 刻内每刻损失当前生命！（对败血目标 +10% 伤害）")
        return
    # smith_blaze_wound/rong_lu_yu_wen/ember_burn：_apply_dot（maxhp%）
    pct = float(wd["dot_pct_boss"]) if _boss_enemy(battle.enemy) else float(wd["dot_pct"])
    _apply_dot(battle, wd["dot_key"], 1, pct, int(wd["turns"]), logs, source=_DOT_SOURCE[key])


# ---------------------------------------------------------------- proc_reflect（2 key）
# 纯反伤段（thorn_armor 无条件 / retribution_ring chance）——C2 只收这 2 key，
# iron_echo/dragon_spine_mail/ember_bulwark 带附赠（heal/heal_down/burn）留 C4 收。

def _we_exec_reflect(battle, player, ctx, logs, wd, key):
    """反伤执行器：chance（缺省=恒触发，thorn_armor 无 chance 字段）→ ctx.dmg×reflect_pct 反弹。

    覆盖 thorn_armor（无条件反 15%）/ retribution_ring（20% 反 30%）。
    """
    # 无条件（无 chance 字段）直接过；有 chance 字段则判定（缺 chance 视为无此行为？——
    # thorn_armor 表无 chance，= 无条件反伤；retribution_ring 有 chance=0.20）
    _ch = wd.get("chance")
    if _ch is not None:
        if float(_ch) <= 0 or random.random() >= float(_ch):
            return
    dmg = int(ctx.get("dmg", 0) or 0)
    rd = max(1, int(dmg * float(wd["reflect_pct"])))
    if battle.enemy and battle.enemy.get("hp", 0) > 0 and rd > 0:
        battle._deal_damage(rd, logs)
        logs.append(_REFLECT_LOG[key].format(rd=rd))


# ---------------------------------------------------------------- proc_control（9 key）
# 敌方控制族：mode(slow_or_freeze/slow_heal_down/freeze_cd/freeze/freeze_taken_limited/
# freeze_heal/spd_down_stack/threshold_stun)。事件 hit/skill_hit/taken/heal/threshold/
# enemy_act 由分发器按 key 注册事件集匹配。全部走 weapon_effects 共享动作
# （_slow_enemy/_freeze_enemy——Boss 免疫退化内建）与 e_buffs 直写（heal_down/stun/叠层）。
# ⚠️ 状态键（eff 计数/CD/used、e_buffs 叠层）一律读表字段，不硬编码。

def _we_exec_control(battle, player, ctx, logs, wd, key):
    """控制执行器：chance/次数/CD 前置判定 → mode 分派 → 共享动作/e_buffs 写控。

    覆盖控制族 9 key：frost_ring/holy_judgment_field/everfrost_domain/everfrost_scepter/
    frost_crown/holy_word_bind/randuin_weary/ice_vein/time_freeze（C5 全量迁移）。
    """
    from .weapon_effects import _slow_enemy, _freeze_enemy
    mode = wd.get("mode") or "freeze"
    eff = player.setdefault("eff", {})
    # ---- heal 事件溢出段跳过（holy_word_bind：旧 handler 在 chance 判定前先跳，
    #      不消耗 RNG——顺序必须保持，防战斗随机流漂移）----
    if mode == "freeze_heal" and ctx.get("overflow"):
        return
    # ---- 前置判定：CD（everfrost_domain）——缺 cd_key=无 CD 段 ----
    cd_key = wd.get("cd_key")
    if cd_key:
        if float(eff.get(cd_key, 0) or 0) > battle._now:
            return
    # ---- 前置判定：限次（frost_crown：每场最多 max_per_battle 次）----
    used_key = wd.get("used_key")
    limit = int(wd.get("max_per_battle") or 0) if wd.get("max_per_battle") is not None else 0
    if limit > 0:
        if int(eff.get(used_key, 0) or 0) >= limit:
            return
    # ---- chance 判定（randuin_weary/ice_vein/time_freeze 表无 chance = 无条件）----
    if wd.get("chance") is not None and random.random() >= float(wd["chance"]):
        return
    # ---- mode 分派（缺字段 = 无此行为铁律；各段参数表权威）----
    src = wd.get("source") or _CONTROL_SOURCE.get(key) or "❄️"
    if mode == "slow_or_freeze":      # frost_ring：已减速→冻结（Boss 退化减速），否则减速
        if battle.e_buffs.get("spd_down"):
            _freeze_enemy(battle, logs, turns=int(wd["freeze_turns"]),
                          boss_slow=int(wd["boss_slow"]), source=src)
        else:
            _slow_enemy(battle, int(wd["slow_turns"]), float(wd["slow_pct"]), logs)
    elif mode == "slow_heal_down":    # holy_judgment_field：减速 + e_buffs.heal_down 禁疗
        _slow_enemy(battle, int(wd["slow_turns"]), float(wd["slow_pct"]), logs)
        battle.e_buffs["heal_down"] = max(battle.e_buffs.get("heal_down", 0), int(wd["heal_down"]))
        logs.append(wd.get("log") or "⚖️ 圣裁领域：目标受治疗 -30%（2 刻）！")
    elif mode == "freeze_cd":         # everfrost_domain：冻结后写 CD（ready_at = now + cd×ACT_TICK）
        _freeze_enemy(battle, logs, turns=int(wd["freeze_turns"]),
                      boss_slow=int(wd["boss_slow"]), source=src)
        from .constants import ACT_TICK
        eff[cd_key] = battle._now + int(wd["cd"]) * ACT_TICK
    elif mode == "freeze":            # everfrost_scepter：纯冻结
        _freeze_enemy(battle, logs, turns=int(wd["freeze_turns"]),
                      boss_slow=int(wd["boss_slow"]), source=src)
    elif mode == "freeze_taken_limited":  # frost_crown：受击冻结限次（先计数后冻结，同旧 handler）
        eff[used_key] = int(eff.get(used_key, 0) or 0) + 1
        _freeze_enemy(battle, logs, turns=int(wd["freeze_turns"]),
                      boss_slow=int(wd["boss_slow"]), source=src)
    elif mode == "freeze_heal":       # holy_word_bind：heal 事件冻结（overflow 段已在上方前置跳过）
        _freeze_enemy(battle, logs, turns=int(wd["freeze_turns"]),
                      boss_slow=int(wd["boss_slow"]), source=src)
    elif mode == "spd_down_stack":    # randuin_weary/ice_vein：enemy_act 叠层（e_buffs 乘算减速）
        ms = int(wd["max_stack"])
        sp = float(wd["spd_down_pct"])
        sk = wd.get("stack_key") or "_randuin_stack"
        n = min(ms, int(battle.e_buffs.get(sk, 0) or 0) + 1)
        battle.e_buffs[sk] = n
        battle.e_buffs["_spd_down_pct"] = max(
            float(battle.e_buffs.get("_spd_down_pct", 0) or 0), sp * n)
        # 日志 = 旧 handler 原文案（表 log 含 f-string 表达式文本，不可机器 .format，代码侧重建）
        logs.append(_CONTROL_STACK_LOG[key].format(sp_pct=int(sp * 100 * n), n=n, ms=ms))
    elif mode == "threshold_stun":    # time_freeze：阈值（每场 1 次）→ 敌 stun
        if eff.get(used_key):
            return
        ratio = float(player.get("hp", 0)) / max(1, player.get("max_hp", 1) or 1)
        if ratio >= float(wd["threshold"]):
            return
        eff[used_key] = True
        battle.e_buffs["stun"] = max(battle.e_buffs.get("stun", 0), 1)
        logs.append(wd.get("log") or "⏳ 时光凝滞！敌人被定身，跳过一次行动！")
        return
    # 未知 mode：静默（旧 proc 语义——无注册事件不触发；防御未知表标注）


# ---------------------------------------------------------------- proc_heal amp（4 key）
# 治疗增强段：ctx.heal ×(1+heal_pct)。溢出段（ctx.overflow 真值）跳过——由 battle.py
# 两次 proc（无 overflow 的治疗加成阶段 → 有 overflow 的溢出转盾阶段）驱动。

def _we_exec_heal_amp(battle, player, ctx, logs, wd, key):
    """治疗增幅执行器：ctx.heal ×(1+heal_pct)。"""
    if ctx.get("overflow"):
        return
    heal = int(ctx.get("heal", 0) or 0)
    ctx["heal"] = int(heal * (1 + float(wd["heal_pct"])))



# ---------------------------------------------------------------- proc_shield（10 key）
# 护盾族：battle_start/taken/threshold/skill_hit(暴击)/heal(溢出) 五事件 → 加盾。
# 覆盖 starlight_bulwark/eclipse_crown/sentinel_aegis/deeprock_aegis/bedrock_crown/
# firmament_crown/gargoyle_heart/echo_bless/atonement_shield/endless_radiance。
# 数值全读 wd（表权威 + we_data 覆盖）；行为逐 key 与旧 handler 逐语句等价（C3 目标：行为零变化）：
#   - battle_start：starlight（盾 3 刻 + we_starlight_next 周期刷新标记——battle 2546-2552
#     到期 re-proc battle_start 回路保留原语义）/ eclipse（99 刻 + we_eclipse_active）
#   - taken：sentinel（base+per_lv×lv）/ deeprock（shield_pct×maxhp）——cd 先判 → chance → 加盾 → 写 cd
#   - threshold：bedrock/gargoyle/firmament —— 限次/计数先判 → hp 比门槛 → 触发写标记
#   - heal 溢出：echo_bless（overflow×30% cap 10%maxhp）/ atonement（全额 cap 15%maxhp + active）
#   - skill_hit 暴击：endless_radiance —— is_crit + cd → 盾（shield_turns 刻）
# 日志模板：数据表 log 字段含 Python 表达式（firmament 等），此处保留族内 key 模板字典
# （C10 收尾可下沉 data.log 纯模板后删——与 C2 _DOT_SOURCE 同策略）。

def _shield_base_value(battle, player, wd):
    """护盾量：sentinel base+per_lv×lv；deeprock shield_pct×maxhp；其余 shield_hp_pct×maxhp。"""
    if wd.get("base") is not None or wd.get("per_lv") is not None:
        lv = int(player.get("level", 1) or 1)
        return int(float(wd.get("base") or 0) + float(wd.get("per_lv") or 0) * lv)
    if wd.get("shield_pct") is not None:
        return int(player.get("max_hp", 100) * float(wd["shield_pct"]))
    return int(player.get("max_hp", 100) * float(wd["shield_hp_pct"]))

def _we_exec_shield(battle, player, ctx, logs, wd, key):
    """护盾族执行器：按 key 语义执行（事件由分发器路由，执行器内逐 key 分支与原 handler 等价）。"""
    from .constants import ACT_TICK
    eff = player.setdefault("eff", {})
    mhp = player.get("max_hp", 100)
    # ---- heal 事件：治疗溢出转盾（echo_bless / atonement_shield）----
    if key in ("echo_bless", "atonement_shield"):
        overflow = int(ctx.get("overflow", 0) or 0)
        if overflow <= 0:
            return
        cap = int(mhp * float(wd["cap_hp_pct"]))
        if key == "echo_bless":
            shield = min(cap, int(overflow * float(wd["overflow_pct"])))
        else:
            shield = min(cap, overflow)
        if shield > 0:
            battle._add_shield(wd["shield_key"], shield, int(wd.get("turns") or 3))
            if wd.get("active_key"):
                eff[wd["active_key"]] = True
            logs.append(_SHIELD_LOG[key].format(shield=shield))
        return
    # ---- threshold 事件：bedrock / firmament / gargoyle_heart ----
    if key in ("bedrock_crown", "firmament_crown", "gargoyle_heart"):
        if key == "firmament_crown":
            n = int(eff.get(wd["used_key"], 0) or 0)
            if n >= int(wd.get("per_battle") or 0):
                return
        else:
            if eff.get(wd["used_key"]):
                return
        ratio = float(player.get("hp", 0)) / max(1, player.get("max_hp", 1) or 1)
        if ratio >= float(wd["threshold"]):
            return
        if key == "firmament_crown":
            n = int(eff.get(wd["used_key"], 0) or 0) + 1
            eff[wd["used_key"]] = n
            shield = _shield_base_value(battle, player, wd)
            battle._add_shield(wd["shield_key"], shield, int(wd.get("turns") or 3))
            logs.append(_SHIELD_LOG[key].format(shield=shield, n=n))
            return
        eff[wd["used_key"]] = True
        shield = _shield_base_value(battle, player, wd)
        battle._add_shield(wd["shield_key"], shield, int(wd.get("turns") or 4))
        if key == "gargoyle_heart":
            heal = int(mhp * float(wd["heal_pct"]))
            from .weapon_effects import _heal_player
            _heal_player(battle, player, heal, logs, source="💎 石像鬼之心")
            logs.append(_SHIELD_LOG[key].format(shield=shield, heal=heal))
        else:
            logs.append(_SHIELD_LOG[key].format(shield=shield))
        return
    # ---- taken 事件：sentinel / deeprock（cd 先判 → chance → 盾 → 写 cd）----
    if key in ("sentinel_aegis", "deeprock_aegis"):
        if float(eff.get(wd["cd_key"], 0) or 0) > battle._now:
            return
        if random.random() >= float(wd["chance"]):
            return
        shield = _shield_base_value(battle, player, wd)
        battle._add_shield(wd["shield_key"], shield, int(wd.get("turns") or 3))
        eff[wd["cd_key"]] = battle._now + int(wd.get("cd") or 1) * ACT_TICK
        logs.append(_SHIELD_LOG[key].format(shield=shield))
        return
    # ---- battle_start / skill_hit 家族 ----
    if key == "starlight_bulwark":
        battle._add_shield(wd["shield_key"], int(mhp * float(wd["shield_hp_pct"])), 3)
        # v152 时刻制：we_starlight_next 存 ready_at（now + refresh_turns×ACT_TICK）
        eff[wd["next_key"]] = battle._now + int(wd.get("refresh_turns") or 5) * ACT_TICK
        logs.append(_SHIELD_LOG[key])
        return
    if key == "eclipse_crown":
        battle._add_shield(wd["shield_key"], int(mhp * float(wd["shield_hp_pct"])), int(wd.get("turns") or 99))
        eff[wd["active_key"]] = True
        logs.append(_SHIELD_LOG[key])
        return
    if key == "endless_radiance":
        if not ctx.get("is_crit"):
            return
        if float(eff.get(wd["cd_key"], 0) or 0) > battle._now:
            return
        battle._add_shield(wd["shield_key"], int(mhp * float(wd["shield_hp_pct"])), int(wd.get("shield_turns") or 2))
        eff[wd["cd_key"]] = battle._now + int(wd.get("cd") or 3) * ACT_TICK
        logs.append(_SHIELD_LOG[key])
        return

# 族内 key 日志模板（数据表 log 字段暂含 Python 表达式，C10 下沉纯模板前先放这）
_SHIELD_LOG = {
    "starlight_bulwark": "✨ 星辉壁垒：战斗开始获得 10% 最大生命护盾！",
    "eclipse_crown": "🌒 蚀月之蚀：获得 15% 最大生命护盾！",
    "sentinel_aegis": "🛡️ 哨兵壁垒：获得 {shield} 点护盾！（3 刻）",
    "deeprock_aegis": "🪨 深岩壁垒：获得护盾！（吸收 8% 最大生命）",
    "bedrock_crown": "🪨 磐石守护：生命垂危，获得 {shield} 点护盾！（4 刻）",
    "firmament_crown": "🌌 苍穹庇护：获得 {shield} 点护盾！（{n}/2 次）",
    "gargoyle_heart": "💎 石像鬼之心：获得 {shield} 点护盾并回复 {heal} 点生命！",
    "echo_bless": "🌿 回响祝福：治疗溢出转化为 {shield} 点护盾！",
    "atonement_shield": "⚖️ 赎罪之盾：治疗溢出转化为 {shield} 点护盾！",
    "endless_radiance": "🌟 无尽辉光：暴击获得 5% 最大生命护盾！",
}

# ---------------------------------------------------------------- 注册表
# 族名 → 执行器。key→族 由数据表 family 字段路由（proc() 分发器读表）。
WE_EXECUTORS = {
    "proc_dot": _we_exec_dot,
    "proc_reflect": _we_exec_reflect,
    "proc_control": _we_exec_control,
    "proc_heal": _we_exec_heal_amp,
    "proc_shield": _we_exec_shield,
}

# 族内 key 专属文案/源（dot 触发源 / reflect 日志模板）——数据表未下沉文案时放这
# （C10 收尾可全量下沉 data.log 后删）。
_DOT_SOURCE = {
    "smith_blaze_wound": "🔥 裂伤",
    "rong_lu_yu_wen": "🔥 熔炉余温",
    "ember_burn": "🔥 烬燃",
}
_REFLECT_LOG = {
    "thorn_armor": "🌵 荆棘缠绕：反弹 {rd} 点伤害！",
    "retribution_ring": "⚔️ 复仇之环：反弹 {rd} 点伤害！",
}
# 叠层减速日志模板（C5：旧 handler f-string 原文案；表 log 字段含 f-string 表达式文本，
# 不可机器 .format——C10 收尾把文案全量下沉为纯模板后删本表）
_CONTROL_STACK_LOG = {
    "randuin_weary": "🛡️ 兰顿倦意：敌人速度 -{sp_pct}%（{n}/{ms} 层）！",
    "ice_vein": "❄️ 冰脉寒流：敌人速度 -{sp_pct}%（{n}/{ms} 层）！",
}
# C5 冻结/减速触发源 emoji（旧 handler source 参数原文案；表 log 已含完整文案的
# slow_heal_down/threshold_stun 例外，其余 7 key 文案由 _freeze_enemy/_slow_enemy 拼接）
_CONTROL_SOURCE = {
    "frost_ring": "🧊 霜环",
    "everfrost_domain": "🧊 永冻领域",
    "everfrost_scepter": "🧊 永霜禁锢",
    "frost_crown": "🧊 寒霜凝视",
    "holy_word_bind": "✨ 圣言禁锢",
}
