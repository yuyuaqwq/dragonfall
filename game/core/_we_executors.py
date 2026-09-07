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

def _we_exec_dot(battle, player, ctx, logs, wd, key, event):
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

def _we_exec_reflect(battle, player, ctx, logs, wd, key, event):
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

def _we_exec_control(battle, player, ctx, logs, wd, key, event):
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

def _we_exec_heal_amp(battle, player, ctx, logs, wd, key, event):
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

def _we_exec_shield(battle, player, ctx, logs, wd, key, event):
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


# ---------------------------------------------------------------- proc_passive_mult（4 key）
# 被动乘区族：伤害结算挂点（battle _skill_finalize_damage passive 分发，ctx 统一含 mult/tags/
# is_crit/kind/skill）读敌/自身状态条件 → 乘进 ctx.mult 或 ctx.crit_dmg。双事件 key 生产-消费
# 成对整体迁移（§2.4/§6：combo_end 的 hit 置标 + arcane_firmament 的 battle_start 置标也一并进
# 执行器，事件由 ctx 区分——被动消费段 ctx 必带 mult 键，生产段无）。条件谓词/数值作用面见
# docs/REFACTOR_P2C_weapon_executors.md §3.10/§4.1 族 #11。

def _we_exec_passive_mult(battle, player, ctx, logs, wd, key, event):
    """被动乘区执行器：cond 谓词（hp 阈值/kind/连段）命中 → mode mult（ctx.mult ×值）/crit_dmg。

    覆盖 twilight_execute/star_slayer_edge（hp 阈值 mult）/ arcane_firmament（kind=魔法 mult，
    battle_start 置 mark_key 标记——消费段只判 kind 不读标记，置标仅原样保留）/ combo_end
    （hit 置 mark_key 标记 → passive is_crit 消费 ctx.crit_dmg 加法并清标）。行为与旧 handler
    逐语句等价（C8 目标：行为零变化）。
    """
    eff = player.setdefault("eff", {})
    # 事件路由：生产段（battle_start/hit 置标）vs passive 消费段。
    # ⚠️ passive 挂点共 3 处（battle dmg 结算 _wectx / heal / taken）——旧 handler 对全部三 ctx
    # 都执行消费（handler 不查 ctx 内容；twi/star 读敌 hp、arcane 读 ctx.kind、combo 读
    # ctx.is_crit+标——heal/taken ctx 下各自空转或写 mult 都已被 OLD 语义，迁移逐句复刻）。
    if event != "passive":
        # ---- 生产段：置标 / 叠层 ----
        if key == "arcane_firmament":
            # battle_start：挂 eff.we_arcane_firmament 标记 + 日志（旧 handler 原文案）
            eff[wd["mark_key"]] = True
            logs.append(wd.get("log") or "✨ 奥术苍穹：魔攻 +15%，技能伤害 +10%！")
            return
        if key == "combo_end":
            # hit：连段活跃（battle._combo_active——旧 handler 只判布尔不查层数）→ 置暴伤标记
            if battle._combo_active(player):
                eff[wd["mark_key"]] = float(wd["crit_dmg"])
            return
        return  # 其余 key 无其它生产事件（proc_stack 各生产段在其执行器内）
    is_passive = "mult" in ctx
    if key == "twilight_execute":
        # 暮光处决：对生命 <40% 的目标 +25% 伤害（唯一事件 passive）
        from .weapon_effects import _hp_ratio
        if _hp_ratio(battle) < float(wd["threshold"]):
            ctx["mult"] = ctx.get("mult", 1.0) * float(wd["dmg_mult"])
            ctx["tags"] = ctx.get("tags", []) + ["🌆暮光处决"]
        return
    if key == "star_slayer_edge":
        # 弑星：对生命 >70% 的目标 +15% 伤害（暴伤 +30% 在 _player_stats 面板消费点，非本段）
        from .weapon_effects import _hp_ratio
        if _hp_ratio(battle) > float(wd["threshold"]):
            ctx["mult"] = ctx.get("mult", 1.0) * float(wd["dmg_mult"])
            ctx["tags"] = ctx.get("tags", []) + ["⭐弑星"]
        return
    if key == "arcane_firmament":
        # passive：魔法技 ×(1+skill_dmg_pct)（魔攻 +15% 面板在 _player_stats 消费）
        if ctx.get("kind") == "魔法":
            ctx["mult"] = ctx.get("mult", 1.0) * (1 + float(wd["skill_dmg_pct"]))
            ctx["tags"] = ctx.get("tags", []) + ["✨奥术苍穹"]
        return
    if key == "combo_end":
        # 连击终点（夜枭双匕）：hit 置暴伤标记（连段活跃即置——保持旧 handler 判定：只查
        # battle._combo_active，不查 stacks.combo≥3）→ passive 暴击消费 ctx.crit_dmg 加法并清标
        if ctx.get("is_crit") and eff.get(wd["mark_key"]):
            ctx["crit_dmg"] = ctx.get("crit_dmg", 0) + float(wd["crit_dmg"])
            eff.pop(wd["mark_key"], None)
        return


# ---------------------------------------------------------------- proc_stack（7 key）
# 叠层增幅族：生产事件（skill_cast/hit/turn_start 叠层写 stacks/eff 槽）→ passive 乘区段
# （读层数/charge 乘进 ctx.mult，rune_amp 消费后清 0 / sage_amp/thunder_weave 消费 charge 后清）。
# 覆盖 7 key = wind_mark/thunder_weave/novice_hunt_combo（hit 叠层；面板/连击消费在 battle
# 直读点，本执行器只写槽）/ rune_amp/sage_amp/eternal_codex（skill_cast 叠层）/ time_staff
# （turn_start 叠层+回血）。面板消费点（_player_stats 直读 gale/wind_mark/thunder_weave 层数）
# 属 C6 批次，不改。事件区分：被动消费段 ctx 必带 mult 键；生产段无。

def _we_exec_stack(battle, player, ctx, logs, wd, key, event):
    """叠层增幅执行器：生产段叠层（写 stacks/eff 槽 + 原文案日志）→ 被动段读层/charge 乘区消费。

    与旧 handler 逐语句等价（C8 目标：行为零变化）。双事件 key（rune_amp/sage_amp/eternal_codex/
    thunder_weave/time_staff）生产-消费配对整体迁移——生产段保留原逻辑，被动消费段读同槽。
    wind_mark/novice_hunt_combo 仅 hit 叠层（无 passive 段），照旧 handler 全量搬迁。
    """
    eff = player.setdefault("eff", {})
    stacks = player.setdefault("stacks", {})
    # 事件路由：生产段（skill_cast/hit/turn_start）叠层写槽 vs passive 消费段。
    # ⚠️ passive 挂点共 3 处（battle dmg 结算 / heal / taken）——旧 handler 全部触发被动消费
    # （不查 ctx 内容；time_staff 等只读 stacks，heal/taken ctx 下也写 ctx.mult/tags，调用方
    # 只读自己键 → 无害）。复刻 = event==passive 即消费（含无 mult 的 heal/taken ctx）。
    is_passive = (event == "passive")
    # 生产段（非被动事件）：wind_mark/novice_hunt_combo/thunder_weave 仅 hit；rune_amp/sage_amp/
    # eternal_codex 仅 skill_cast；time_staff 仅 turn_start。
    if not is_passive:
        if event not in ("hit", "skill_cast", "turn_start"):
            return  # 其它事件（battle_start 等非生产 key）→ 空转
        if key == "wind_mark":
            # 风痕（风行短弓）：每次命中 +1 层（上限 max_stack=4），每层速度 +2%（_player_stats 直读消费）
            n = min(int(wd["max_stack"]), int(stacks.get("wind_mark", 0) or 0) + 1)
            stacks["wind_mark"] = n
            logs.append(f"🌬️ 风痕叠加！({n}/4 层，每层速度 +2%)")
            return
        if key == "novice_hunt_combo":
            # 猎影（猎影之牙）：暴击后叠层（上限 max_stack=5），每层连击率 +per_stack%（消费在 battle）
            if not ctx.get("is_crit"):
                return
            n = min(int(wd["max_stack"]), int(stacks.get("novice_combo", 0) or 0) + 1)
            stacks["novice_combo"] = n
            logs.append(f"🎯 猎影：暴击叠层！（{n}/5 层，每层连击率 +{int(float(wd['per_stack']) * 100)}%）")
            return
        if key == "thunder_weave":
            # hit 生产：+1 层（上限 5），满层清零并置 we_thunder_charge（下一次技能 +20%）
            n = min(int(wd["max_stack"]), int(stacks.get("thunder_weave", 0) or 0) + 1)
            stacks["thunder_weave"] = n
            logs.append(f"⚡ 雷纹连打！({n}/5 层，每层速度+2% 攻击+1%)")
            if n >= int(wd["max_stack"]):
                stacks["thunder_weave"] = 0
                eff[wd["charge_key"]] = float(wd["charge_pct"])
            return
        if key == "rune_amp":
            # skill_cast 生产：叠层（上限 5）
            n = min(int(wd["max_stack"]), int(stacks.get("rune_amp", 0) or 0) + 1)
            stacks["rune_amp"] = n
            logs.append(f"📜 铭文增幅！({n}/5 层，下一技能 +{int(n * float(wd['dmg_pct_per']) * 100)}%)")
            return
        if key == "sage_amp":
            # skill_cast 生产：计数（need 次满 → 置 we_sage_charge = ×charge_pct）
            n = int(stacks.get("sage_amp", 0) or 0) + 1
            stacks["sage_amp"] = n
            if n >= int(wd["need"]):
                stacks["sage_amp"] = 0
                eff[wd["charge_key"]] = float(wd["charge_pct"])
            return
        if key == "eternal_codex":
            # skill_cast 生产：叠层（上限 max_stack=8）
            cap = int(wd["max_stack"])
            n = min(cap, int(stacks.get("eternal_codex", 0) or 0) + 1)
            stacks["eternal_codex"] = n
            logs.append(f"📖 永恒契约！({n}/{cap} 层，每层技能伤害 +{float(wd['dmg_pct_per']) * 100:.1f}%)")
            return
        if key == "time_staff":
            # turn_start 生产：叠层（上限 max_stack=10）+ 掉血时回 1.5% 最大生命
            from .weapon_effects import _heal_player
            n = min(int(wd["max_stack"]), int(stacks.get("time_staff", 0) or 0) + 1)
            stacks["time_staff"] = n
            if player.get("hp", 0) < player.get("max_hp", 1):
                heal = max(1, int(player.get("max_hp", 1) * float(wd["per_pct"])))
                _heal_player(battle, player, heal, logs, source="⏳ 岁月流转")
            logs.append(f"⏳ 岁月流转叠层！({n}/10 层，攻击 +{int(n * float(wd['per_pct']) * 100)}%)")
            return
        return  # 该 key 当前事件无对应生产段 → 空转
    # ===== 以下 = event==passive 且 ctx 带 mult（伤害结算）→ 被动乘区消费 =====
    if key == "wind_mark":
        return  # 风痕无被动消费段（面板直读，C6 收）
    if key == "novice_hunt_combo":
        return  # 猎影无 passive 消费段（连击率由 battle 直读，C6/后收）
    if key == "thunder_weave":
        # passive：满层 charge 消费（下一次技能 ×charge_pct）
        if eff.get(wd["charge_key"]):
            ctx["mult"] = ctx.get("mult", 1.0) * float(eff.get(wd["charge_key"], float(wd["charge_pct"])))
            ctx["tags"] = ctx.get("tags", []) + ["⚡雷纹x1.20"]
            eff.pop(wd["charge_key"], None)
        return
    if key == "rune_amp":
        # passive：下一技能 ×(1+per_pct×层)，消费后清 0
        n = int(stacks.get("rune_amp", 0) or 0)
        if n > 0:
            ctx["mult"] = ctx.get("mult", 1.0) * (1 + float(wd["per_pct"]) * n)
            ctx["tags"] = ctx.get("tags", []) + [f"📜铭文x{1 + float(wd['per_pct']) * n:.2f}"]
            stacks["rune_amp"] = 0
        return
    if key == "sage_amp":
        # passive：charge 消费（下一次技能 ×charge_pct）
        if eff.get(wd["charge_key"]):
            ctx["mult"] = ctx.get("mult", 1.0) * float(eff.get(wd["charge_key"], float(wd["charge_pct"])))
            ctx["tags"] = ctx.get("tags", []) + ["📚秘典x1.25"]
            eff.pop(wd["charge_key"], None)
        return
    if key == "eternal_codex":
        # passive：每层 ×(1+per_pct×层)（不清层）
        n = int(stacks.get("eternal_codex", 0) or 0)
        if n > 0:
            ctx["mult"] = ctx.get("mult", 1.0) * (1 + float(wd["per_pct"]) * n)
            ctx["tags"] = ctx.get("tags", []) + [f"📖永恒x{1 + float(wd['per_pct']) * n:.2f}"]
        return
    if key == "time_staff":
        # passive：每层 ×(1+per_pct×层)（不清层）
        n = int(stacks.get("time_staff", 0) or 0)
        if n > 0:
            ctx["mult"] = ctx.get("mult", 1.0) * (1 + float(wd["per_pct"]) * n)
            ctx["tags"] = ctx.get("tags", []) + [f"⏳岁月x{1 + float(wd['per_pct']) * n:.2f}"]
        return
    return

# ---------------------------------------------------------------- proc_extra_dmg（11 key）
# 直伤追击族：命中后追加直伤/真伤/吸血。事件 hit（7 key）与 skill_hit（4 key）由分发器
# 按 key 注册事件集匹配。mode 分派（读表字段，零代码默认值）：
#   - splash_magi（afterglow_splash/spellblade_echo/annihilation_echo）：chance（无字段=恒触发）
#     → _extra_magi 奥术溅射（技能命中）
#   - extra_phys（wind_split）：chance → _extra_phys 物理追加
#   - extra_phys_pene（phantom_barrage）：计数 + chance/保底 → calc_damage 无视 pene_pct% 防御直伤
#   - extra_phys_oncrit（endless_blade）：is_crit + 每刻限 1（used_key）→ _extra_phys
#   - true_dmg_nth（hunter_open/siren_fang/star_pierce）：每 count 次真伤（star 含已损加成+cap）
#   - curhp_dmg_heal（soul_eater）：敌当前生命%伤（cap atk）+ 回等量
#   - lifesteal（novice_lifesteal）：dmg×heal_pct 吸血
# 堆栈计数键（hunter_cnt/siren_cnt/star_cnt/phantom_cnt）与 used 键一律读 wd 表字段
# （stack_key/used_key），不硬编码。日志 = 旧 handler 原文案，走共享动作源参/表 log 模板。
#
# ⚠️ 行为零变化要点（与旧 handler 逐语句等价）：
#   - chance 判定在 has_effect 自查后（旧 proc 已保证装备持有，执行器免查）；
#     phantom_barrage 的 RNG 只在 chance 判定消耗一次（保底靠计数无条件触发，同旧语义）
#   - _true_dmg/_extra_phys/_extra_magi/_heal_player/_pstats/_estats 全部从 weapon_effects
#     模块 import（共享动作唯一实现，执行器不复制公式）
#   - soul_eater 的 _deal_damage(wake_sleep=False) 与 heal 顺序（先伤后回）必须保持

def _we_exec_extra_dmg(battle, player, ctx, logs, wd, key, event):
    """直伤追击族执行器：mode 分派 → 计数/chance/crit 前置 → 共享动作追加伤害。"""
    from .weapon_effects import (
        _extra_magi, _extra_phys, _true_dmg, _heal_player,
        _pstats, _estats,
    )
    mode = wd.get("mode") or ""
    stacks = player.setdefault("stacks", {})
    eff = player.setdefault("eff", {})
    # ================= splash_magi：奥术溅射 =================
    if key in ("afterglow_splash", "spellblade_echo", "annihilation_echo"):
        if wd.get("chance") is not None and random.random() >= float(wd["chance"]):
            return
        _extra_magi(battle, float(wd["atk_pct"]), logs,
                    source=_EXTRA_DMG_SOURCE[key])
        return
    # ================= extra_phys：物理追加 =================
    if key == "wind_split":
        if wd.get("chance") is not None and random.random() >= float(wd["chance"]):
            return
        _extra_phys(battle, float(wd["atk_pct"]), logs,
                    source=_EXTRA_DMG_SOURCE[key])
        return
    # ================= extra_phys_pene：破防追加+保底 =================
    if key == "phantom_barrage":
        sk = wd["stack_key"]
        n = int(stacks.get(sk, 0) or 0) + 1
        stacks[sk] = n
        if random.random() < float(wd["chance"]) or n >= int(wd["guarantee"]):
            stacks[sk] = 0
            st = _pstats(battle, player)
            est = _estats(battle)
            from ..engine import calc_damage
            dmg = max(1, calc_damage(
                int(st.get("atk", 0) * float(wd["atk_pct"])),
                int(est.get("def", 0) * (1 - float(wd["pene_pct"])))))
            battle._deal_damage(dmg, logs)
            logs.append(wd.get("log", "🌪️ 幻影连射！无视 50% 防御造成 {dmg} 点伤害！").format(dmg=dmg))
        return
    # ================= extra_phys_oncrit：暴击追击（每刻限 1） =================
    if key == "endless_blade":
        if not ctx.get("is_crit") or eff.get(wd["used_key"]):
            return
        eff[wd["used_key"]] = True
        _extra_phys(battle, float(wd["atk_pct"]), logs,
                    source=_EXTRA_DMG_SOURCE[key])
        return
    # ================= true_dmg_nth：每 N 次真伤 =================
    if key in ("hunter_open", "siren_fang", "star_pierce"):
        sk = wd["stack_key"]
        n = int(stacks.get(sk, 0) or 0) + 1
        stacks[sk] = n
        if n >= int(wd["count"]):
            stacks[sk] = 0
            st = _pstats(battle, player)
            if key == "star_pierce":
                e = battle.enemy or {}
                base = int(st.get("atk", 0) * float(wd["atk_pct"]))
                lost = int((e.get("max_hp", 0) - e.get("hp", 0)) * float(wd["lost_hp_pct"]))
                cap = int(e.get("max_hp", 1) * float(wd["cap_pct"]))
                bonus = base + min(lost, cap)
                _true_dmg(battle, bonus, logs, source=_EXTRA_DMG_SOURCE[key])
            else:
                _true_dmg(battle, st.get("atk", 0) * float(wd["atk_pct"]),
                          logs, source=_EXTRA_DMG_SOURCE[key])
        return
    # ================= curhp_dmg_heal：敌当前生命%伤 + 回等量 =================
    if key == "soul_eater":
        e = battle.enemy or {}
        st = _pstats(battle, player)
        cap = max(1, int(st.get("atk", 0) or 0))
        bonus = min(cap, max(1, int(e.get("hp", 0) * float(wd["cur_hp_pct"]))))
        if bonus > 0:
            battle._deal_damage(bonus, logs, wake_sleep=False)
            healed = _heal_player(battle, player, bonus, logs,
                                  source=_EXTRA_DMG_SOURCE[key])
            logs.append(wd.get("log", "💜 破败之吻：额外 {bonus} 点伤害，回复 {healed} 点生命！")
                        .format(bonus=bonus, healed=healed))
        return
    # ================= lifesteal：吸血 =================
    if key == "novice_lifesteal":
        dmg = int(ctx.get("dmg", 0) or 0)
        if dmg <= 0:
            st = _pstats(battle, player)
            dmg = int(st.get("atk", 0) or 0)
        heal = int(dmg * float(wd["heal_pct"]))
        _heal_player(battle, player, heal, logs, source=_EXTRA_DMG_SOURCE[key])
        return


# 直伤追击族触发源（旧 handler source 参数原文案）
_EXTRA_DMG_SOURCE = {
    "afterglow_splash": "🌅 余波",
    "spellblade_echo": "🔮 咒刃",
    "annihilation_echo": "💥 湮灭回响",
    "wind_split": "🌪️ 裂风矢",
    "endless_blade": "⚔️ 无尽锋芒",
    "hunter_open": "🗡️ 破绽",
    "siren_fang": "🧜 海妖猎杀",
    "star_pierce": "☄️ 穿星",
    "soul_eater": "💜 破败之吻",
    "novice_lifesteal": "🩸 吸血",
}

# ---------------------------------------------------------------- 注册表
# 族名 → 执行器。key→族 由数据表 family 字段路由（proc() 分发器读表）。
WE_EXECUTORS = {
    "proc_dot": _we_exec_dot,
    "proc_reflect": _we_exec_reflect,
    "proc_control": _we_exec_control,
    "proc_heal": _we_exec_heal_amp,
    "proc_shield": _we_exec_shield,
    "proc_passive_mult": _we_exec_passive_mult,
    "proc_stack": _we_exec_stack,
    "proc_extra_dmg": _we_exec_extra_dmg,
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
