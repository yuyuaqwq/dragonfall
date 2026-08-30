# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - affix_effects.py（v98.5：词条/套装效果注册表）

消灭 game/battle.py 的四处硬编码效果链：
1. HIT_EFFECTS       _affix_on_hit     攻击命中词条（10 块，并列 if 语义）
2. TAKEN_EFFECTS     _affix_on_taken   受击词条（8 块，顺序结算 out）
3. TURN_START_EFFECTS _affix_turn_start 回合开始词条（回春/冥想/晨曦）
4. SET_PROC_EFFECTS  _set_attack_proc  套装 4 件攻击特效（6 种 eff，elif 分发）

扩展方式：
- 加词条效果：affixes 数据加词条 id + register 一个函数（~5 行），零改动分发骨架

函数签名：
- HIT:           fn(battle, player, dmg, logs) -> None（按注册顺序遍历，全部检查）
- TAKEN:         fn(battle, player, ctx, logs) -> None（ctx={"dmg":原始, "out":结算中}，改 ctx["out"]）
- TURN_START:    fn(battle, player, logs) -> None
- SET_PROC:      fn(battle, player, dmg, logs) -> None（按 eff key 分发，只触发在 effs 中的）

约定（与旧代码行为零差异）：
- 并列 if 语义：多个词条可同时触发 → 遍历全部注册函数，handler 内部自查 aid
- 叠加型效果（dmg_reduce+earth_heart、regen+dawn_crown）合并为一个 handler（先汇总后应用）
- 组合型效果（judgment_chain/purify 的 if-elif 互斥）保持原 if-elif 结构
- TAKEN 的 block 用结算中 out（减伤后），thorns/ember_ward 用原始 dmg——通过 ctx 区分
"""
import random


def _affix_chance(aid: str, default: float) -> float:
    """词条触发概率：读数据（AFFIXES/LEGENDARY_EFFECTS 的 chance），缺失用 default 兜底（v99.2）"""
    from .. import content as C  # 延迟引用，防 core→content→core 循环
    info = C.AFFIXES.get(aid) or C.LEGENDARY_EFFECTS.get(aid)
    if info is None:
        return default
    return info.get("chance", default)


def _affix_effect(aid: str) -> dict:
    """词条效果参数：读数据（AFFIXES/LEGENDARY_EFFECTS 的 effect）。

    缺失返回 {} —— handler 内一律 eff.get(key, 旧默认值) 兜底，
    保证无 effect 字段的旧词条行为不变（数值下沉兼容层）。
    """
    from .. import content as C  # 延迟引用，防 core→content→core 循环
    info = C.AFFIXES.get(aid) or C.LEGENDARY_EFFECTS.get(aid)
    if info is None:
        return {}
    return info.get("effect") or {}


def _set_chance(eff: str, default: float) -> float:
    """套装 4 件特效概率：读 sets.py bonus_4 的 chance，缺失用 default 兜底（v99.2）"""
    from .. import content as C  # 延迟引用，防 core→content→core 循环
    for s in (C.SETS or {}).values():
        b4 = (s or {}).get("bonus_4") or {}
        if b4.get("effect") == eff:
            return b4.get("chance", default)
    return default


def register(registry, key):
    """注册装饰器。"""
    def deco(fn):
        registry[key] = fn
        return fn
    return deco


# ================= 1. 攻击命中词条（_affix_on_hit） =================
# 注册顺序 = 旧代码 if 顺序（dict 保序遍历，行为零变化）

HIT_EFFECTS = {}


@register(HIT_EFFECTS, "bleed")
def _h_bleed(battle, player, dmg, logs):
    """流血：20% 使目标流血（每回合 5% 生命，3 回合）"""
    if "bleed" in battle._equip_affix_ids(player) and random.random() < _affix_chance("bleed", 0.20):
        # 目标级减益：血层挂到 enemy["debuffs"]["bleed"]（攻击命中后 enemy 必在）
        stacks = int(_affix_effect("bleed").get("stacks", 3))  # 每次触发叠层数（兼作上限）
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.get("bleed") or {"n": 0, "mult": 1.0}
        cur["n"] = min(stacks, int(cur.get("n", 0) or 0) + stacks)
        deb["bleed"] = cur
        logs.append("🩸 流血！敌人伤口裂开，将持续失血！")


@register(HIT_EFFECTS, "armor_break")
def _h_armor_break(battle, player, dmg, logs):
    """破甲：25% 降低目标防御 15%（2 回合）"""
    if "armor_break" in battle._equip_affix_ids(player) and random.random() < _affix_chance("armor_break", 0.25):
        eff = _affix_effect("armor_break")
        battle.e_buffs["def_down"] = max(battle.e_buffs.get("def_down", 0), int(eff.get("turns", 2)))
        battle.e_buffs["_armor_break_pct"] = float(eff.get("pct", 0.15))
        logs.append("🛡️ 破甲！敌人防御下降 15%！")


@register(HIT_EFFECTS, "combo")
def _h_combo(battle, player, dmg, logs):
    """连击：15% 追加一次 50% 伤害"""
    if "combo" in battle._equip_affix_ids(player) and random.random() < _affix_chance("combo", 0.15):
        cd = int(dmg * float(_affix_effect("combo").get("extra_atk", 0.50)))
        battle._damage_enemy(cd, logs)
        logs.append(f"⚡ 连击！追加 {cd} 点伤害！")


@register(HIT_EFFECTS, "element_fire")
def _h_element_fire(battle, player, dmg, logs):
    """元素附加·火：5% 属性伤害"""
    if "element_fire" in battle._equip_affix_ids(player):
        ed = max(1, int(dmg * float(_affix_effect("element_fire").get("pct", 0.05))))
        battle._damage_enemy(ed, logs)
        logs.append(f"🔥 fire属性附加 {ed} 点伤害！")


@register(HIT_EFFECTS, "element_ice")
def _h_element_ice(battle, player, dmg, logs):
    """元素附加·冰：5% 属性伤害 + 减速"""
    if "element_ice" in battle._equip_affix_ids(player):
        ed = max(1, int(dmg * float(_affix_effect("element_ice").get("pct", 0.05))))
        battle._damage_enemy(ed, logs)
        logs.append(f"❄️ ice属性附加 {ed} 点伤害！")
        battle.e_buffs["spd_down"] = max(battle.e_buffs.get("spd_down", 0),
                                         int(_affix_effect("element_ice").get("slow_turns", 2)))
        logs.append("❄️ 减速！")


@register(HIT_EFFECTS, "element_thunder")
def _h_element_thunder(battle, player, dmg, logs):
    """元素附加·雷：5% 属性伤害
    v135 哑词条激活·雷系增强：15% 概率追加一次 20% 雷伤小爆（感电连跳，玩家可感知）"""
    if "element_thunder" in battle._equip_affix_ids(player):
        ed = max(1, int(dmg * float(_affix_effect("element_thunder").get("pct", 0.05))))
        battle._damage_enemy(ed, logs)
        logs.append(f"⚡ thunder属性附加 {ed} 点伤害！")
        if random.random() < _affix_chance("element_thunder", 0.15):
            sd = max(1, int(dmg * float(_affix_effect("element_thunder").get("thunder_bonus", 0.20))))
            battle._damage_enemy(sd, logs)
            logs.append(f"⚡⚡ 感电连跳！追加 {sd} 点雷系伤害！")


@register(HIT_EFFECTS, "chu_huo")
def _h_chu_huo(battle, player, dmg, logs):
    """初火余烬（灰烬圣剑·初火 Lv95 终章传说剑）：攻击附加 8% 火属性伤害，
    20% 概率使目标灼烧（每回合损 1.5% 最大生命，3 回合；Boss 1%）"""
    if "chu_huo" not in battle._equip_affix_ids(player):
        return
    eff = _affix_effect("chu_huo")
    pct = float(eff.get("pct", 0.08))
    ed = max(1, int(dmg * pct))
    battle._damage_enemy(ed, logs)
    logs.append(f"🔥 初火余烬：火属性附加 {ed} 点伤害！")
    if random.random() < _affix_chance("chu_huo", 0.20):
        pct_dot = 0.01 if (battle.enemy or {}).get("role") == "boss" else 0.015
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.get("burn") or {"n": 0, "mult": 1.0}
        cur["n"] = min(3, int(cur.get("n", 0) or 0) + 1)
        cur["pct"] = pct_dot
        cur["turns"] = max(int(cur.get("turns", 0) or 0), int(eff.get("burn_turns", 3)))
        deb["burn"] = cur
        logs.append("🔥 初火余烬：目标被灼烧！（每回合损 1.5% 最大生命，3 回合）")


@register(HIT_EFFECTS, "pierce")
def _h_pierce(battle, player, dmg, logs):
    """贯穿：20% 无视防御追加伤害"""
    from ..engine import calc_damage
    if "pierce" in battle._equip_affix_ids(player) and random.random() < _affix_chance("pierce", 0.20):
        pst = battle._player_stats(player)
        pd = calc_damage(int(pst.get("atk", 0) * float(_affix_effect("pierce").get("atk_pct", 0.60))), 0)
        if pd > 0:
            battle._damage_enemy(pd, logs)
            logs.append(f"🏹 贯穿！无视防御 {pd} 点伤害！")


@register(HIT_EFFECTS, "charge")
def _h_charge(battle, player, dmg, logs):
    """蓄力：10% 造成 150% 伤害（追加 50%）"""
    if "charge" in battle._equip_affix_ids(player) and random.random() < _affix_chance("charge", 0.10):
        cd = int(dmg * float(_affix_effect("charge").get("dmg_pct", 0.50)))
        battle._damage_enemy(cd, logs)
        logs.append(f"💪 蓄力爆发！追加 {cd} 点伤害！")


@register(HIT_EFFECTS, "purify")
def _h_purify(battle, player, dmg, logs):
    """净化：15% 驱散敌人 1 层增益（审判之链专属 25% 驱散 2 层；if-elif 互斥保持原语义）"""
    ids = battle._equip_affix_ids(player)
    purge_n = 0
    if "judgment_chain" in ids and random.random() < _affix_chance("judgment_chain", 0.25):
        purge_n = int(_affix_effect("judgment_chain").get("purge", 2))
    elif "purify" in ids and random.random() < _affix_chance("purify", 0.15):
        purge_n = int(_affix_effect("purify").get("purge", 1))
    if purge_n:
        gain_keys = [k for k in battle.e_buffs
                     if k.startswith("mon_") or k in ("summon", "atk_up_strong")]
        removed = 0
        for _ in range(purge_n):
            if not gain_keys:
                break
            k = gain_keys.pop(random.randrange(len(gain_keys)))
            del battle.e_buffs[k]
            removed += 1
        if removed:
            logs.append(f"✨ 净化！驱散了敌人 {removed} 层增益！")
            # v135 哑词条激活·净化增强：驱散成功附加『圣洁』——敌人攻击 -10%(1 回合)
            # （驱散 × 削弱，净化从"防 buff"升级为攻防一体的可感知特色）
            battle.e_buffs["mon_atk_down"] = max(battle.e_buffs.get("mon_atk_down", 0), 1)
            battle.e_buffs["_weaken_val"] = float(_affix_effect("purify").get("holy_weaken", 0.10))
            logs.append("😇 圣洁之力！净化后敌人攻击下降 10%！")


@register(HIT_EFFECTS, "dragon_tongue")
def _h_dragon_tongue(battle, player, dmg, logs):
    """龙语印记：攻击叠印记（每层 +2% 伤害，上限 5）"""
    if "dragon_tongue" in battle._equip_affix_ids(player):
        max_mark = int(_affix_effect("dragon_tongue").get("max_mark", 5))
        battle.mech_stacks["dragon_mark"] = min(max_mark, int(battle.mech_stacks.get("dragon_mark", 0) or 0) + 1)
        logs.append(f"🐉 龙语印记叠加！({battle.mech_stacks['dragon_mark']} 层，每层＋2% 伤害)")


# ================= 2. 受击词条（_affix_on_taken） =================
# 顺序结算：ctx["out"] 从原始 dmg 开始，逐个 handler 修改；thorns/ember_ward 读原始 dmg

TAKEN_EFFECTS = {}


@register(TAKEN_EFFECTS, "reduce")
def _t_reduce(battle, player, ctx, logs):
    """减伤（常驻：减伤词条 +3%、大地之心专属 +5%，叠加后统一应用）。
    v130.2c：沸血浇筑（怒气全满时 全减伤 +8%，rage_full=怒气 ≥ 上限（含怒火熔铸上限加成））"""
    ids = battle._equip_affix_ids(player)
    reduce_pct = 0.0
    if "dmg_reduce" in ids:
        reduce_pct += float(_affix_effect("dmg_reduce").get("dmg_reduce", 0.03))
    if "earth_heart" in ids:
        reduce_pct += float(_affix_effect("earth_heart").get("dmg_reduce", 0.05))
    if "boiling_blood" in ids and battle._rage_full(player):
        reduce_pct += float(_affix_effect("boiling_blood").get("dmg_reduce", 0.08))
    if reduce_pct:
        dmg_before = ctx["out"]
        ctx["out"] = max(1, int(ctx["out"] * (1 - reduce_pct)))
        logs.append(f"🛡️ 减伤 {dmg_before - ctx['out']} 点")


@register(TAKEN_EFFECTS, "tenacity_cc")
def _t_tenacity(battle, player, ctx, logs):
    """坚韧：20% 免疫/清除自身负面（减速/降攻）——v110 审计修复：注册键随数据层拆分
    由 tenacity → tenacity_cc（原键被 v106「韧性」stat 词条占用，双机制隐性叠加）"""
    if "tenacity_cc" in battle._equip_affix_ids(player) and random.random() < _affix_chance("tenacity_cc", 0.20):
        neg = [k for k in battle.p_buffs if k in ("spd_down", "atk_down", "def_down")]
        if neg:
            del battle.p_buffs[random.choice(neg)]
            # v135 哑词条激活·坚韧增强：免疫负面成功后 回复 3% 最大生命（铁壁意志）
            _heal = max(1, int(player.get("max_hp", 1) * float(_affix_effect("tenacity_cc").get("heal_pct", 0.03))))
            player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + _heal)
            logs.append(f"💪 坚韧！免疫了负面效果，回复 {_heal} 点生命")


@register(TAKEN_EFFECTS, "counter")
def _t_counter(battle, player, ctx, logs):
    """反击：20% 反击 60% 伤害"""
    from ..engine import calc_damage
    if "counter" in battle._equip_affix_ids(player) and random.random() < _affix_chance("counter", 0.20) and battle.enemy.get("hp", 0) > 0:
        pst2 = battle._player_stats(player)
        est2 = battle._enemy_stats()
        cd = calc_damage(int(pst2.get("atk", 0) * float(_affix_effect("counter").get("pct", 0.60))), est2.get("def", 0))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"⚔️ 反击！对【{battle.enemy.get('name', '敌人')}】造成 {cd} 点伤害！")


@register(TAKEN_EFFECTS, "ember_ward")
def _t_ember_ward(battle, player, ctx, logs):
    """灰烬壁垒（灰烬守卫套专属）：20% 反弹 50% 伤害（基于原始 dmg）"""
    if "ember_ward" in battle._equip_affix_ids(player) and random.random() < _affix_chance("ember_ward", 0.20) and battle.enemy.get("hp", 0) > 0:
        rd = int(ctx["dmg"] * float(_affix_effect("ember_ward").get("pct", 0.50)))
        battle._damage_enemy(rd, logs)
        logs.append(f"🔥 灰烬壁垒！反弹 {rd} 点伤害！")


@register(TAKEN_EFFECTS, "moro_crown")
def _t_moro_crown(battle, player, ctx, logs):
    """深渊腐蚀（摩罗之冠专属）：15% 敌人攻击 -10%（2 回合）"""
    if "moro_crown" in battle._equip_affix_ids(player) and random.random() < _affix_chance("moro_crown", 0.15):
        eff = _affix_effect("moro_crown")
        battle.e_buffs["mon_atk_down"] = max(battle.e_buffs.get("mon_atk_down", 0), int(eff.get("turns", 2)))
        battle.e_buffs["_weaken_val"] = float(eff.get("pct", 0.10))
        logs.append("👿 深渊腐蚀！敌人攻击下降 10%！")


# ================= 3. 回合开始词条（_affix_turn_start） =================

TURN_START_EFFECTS = {}


@register(TURN_START_EFFECTS, "regen")
def _ts_regen(battle, player, logs):
    """回春(1% 生命)/晨曦祝福(2% 生命)：叠加后统一回复"""
    ids = battle._equip_affix_ids(player)
    regen_pct = 0.0
    if "regen" in ids:
        regen_pct += float(_affix_effect("regen").get("pct", 0.01))
    if "dawn_crown" in ids:
        regen_pct += float(_affix_effect("dawn_crown").get("pct", 0.02))
    if regen_pct and player.get("hp", 0) < player.get("max_hp", 1):
        heal = int(player.get("max_hp", player.get("hp", 1)) * regen_pct)
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🌿 回春生效，回复 {heal} 点生命！")


@register(TURN_START_EFFECTS, "meditate")
def _ts_meditate(battle, player, logs):
    """冥想：1% 魔力回复"""
    if "meditate" in battle._equip_affix_ids(player) and player.get("mp", 0) < player.get("max_mp", 1):
        heal = int(player.get("max_mp", player.get("mp", 1)) * float(_affix_effect("meditate").get("pct", 0.01)))
        player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + heal)
        logs.append(f"🧘 冥想生效，回复 {heal} 点魔力！")


@register(TURN_START_EFFECTS, "energy_tide")
def _ts_energy_tide(battle, player, logs):
    """精力潮汐：每回合 精力回复 +5（史诗）/ +10（传说，tier 取档）。
    v130.2c 接线：数据 effect.regen + effect.tiers[quality] 覆盖，走 battle._res_gain（带上限）。"""
    if "energy_tide" not in battle._equip_affix_ids(player) or "energy" not in battle._branch_keys(player):
        return
    eff, tier = battle._affix_eff_tiered(player, "energy_tide")
    gain = int(tier if tier is not None else (eff or {}).get("regen", 5) or 5)
    if gain <= 0:
        return
    old = battle._res_read("energy")
    battle._res_gain(player, "energy", gain)
    if battle._res_read("energy") > old:
        logs.append(f"🌊 精力潮汐：精力回复 +{gain}！")


# ================= 4. 套装 4 件攻击特效（_set_attack_proc） =================
# elif 分发：eff 互斥匹配（同 eff 只进一个分支）；按 eff key 查表

SET_PROC_EFFECTS = {}
SET_PROC_TYPES = {}  # 数据驱动 type → 通用执行器（v142 重构）


def _proc_register(registry, key):
    """注册表装饰器（SET_PROC_TYPES / SET_PROC_EFFECTS 通用）"""

    def deco(fn):
        registry[key] = fn
        return fn

    return deco


# ============================================================
# v142 数据驱动：通用执行器（type 分发表）
# 数值全部从套装数据 params 读取，禁止硬编码魔法数
# ============================================================

def _sp_params(eff: dict) -> dict:
    """取 effect dict 的 params（缺省空 dict）"""
    return (eff or {}).get("params") or {}


def _sp_chance(eff: dict) -> float:
    """触发概率：优先 params.chance，其次数据表 chance，默认 1.0"""
    p = _sp_params(eff)
    if "chance" in p:
        return float(p["chance"])
    return float((eff or {}).get("chance", 1.0))


def _sp_stat(battle, player, key: str) -> float:
    """读取玩家属性（atk/matk/def/mdef）"""
    st = battle._player_stats(player)
    return float(st.get(key, 0) or 0)


def _sp_enemy_def(battle, key: str = "def") -> float:
    """读取敌方防御（def/mdef）"""
    est = battle._enemy_stats()
    return float(est.get(key, est.get("def", 0)) or 0)


def _sp_flat_dmg(battle, player, dmg, logs, params: dict):
    """proc_flat_dmg：概率附加 pct×atk/matk 伤害（可带条件：标记/低血变比例）
    params: chance, stat(atk/matk), pct, cond_mark(bool), cond_hp_lt, pct_alt, dmg_type"""
    from ..engine import calc_damage
    pct = float(params.get("pct", 0.50))
    if params.get("cond_hp_lt") is not None:
        ratio = battle.enemy.get("hp", 0) / max(1, battle.enemy.get("max_hp", 1))
        if ratio >= float(params["cond_hp_lt"]):
            return
    if params.get("cond_mark"):
        mk = (battle.enemy.get("debuffs") or {}).get("mark") or {}
        if int(mk.get("n", 0) or 0) > 0:
            pct = float(params.get("pct_alt", pct))
    stat = params.get("stat", "atk")
    atk = _sp_stat(battle, player, stat)
    edef = _sp_enemy_def(battle, params.get("edef", "def" if stat == "atk" else "mdef"))
    dmg_type = params.get("dmg_type", "phys" if stat == "atk" else "magic")
    cd = calc_damage(int(atk * pct), int(edef), dmg_type=dmg_type)
    if cd > 0:
        battle._damage_enemy(cd, logs)
        tag = params.get("tag", "⚔️")
        logs.append(f"{tag} {params.get('name', '追加伤害')}！追加 {cd} 点伤害！")


def _sp_mark(battle, player, dmg, logs, params: dict):
    """proc_mark：概率叠标记
    params: chance, max_mark, mark_key(mark/element_marks/thunder/erode/poison), mark_desc"""
    deb = battle.enemy.setdefault("debuffs", {})
    key = params.get("mark_key", "mark")
    if key == "element_marks":
        mk = deb.setdefault("element_marks", {})
        mk["thunder"] = min(int(params.get("max_mark", 3)), int(mk.get("thunder", 0) or 0) + 1)
    elif key in ("erode", "poison", "burn"):
        cur = deb.get(key) or {"n": 0, "mult": 1.0}
        cur["n"] = min(int(params.get("max_mark", 5)), int(cur.get("n", 0) or 0) + 1)
        if params.get("pct"):
            cur["pct"] = float(params["pct"])
        if params.get("turns"):
            cur["turns"] = max(int(cur.get("turns", 0) or 0), int(params["turns"]))
        deb[key] = cur
    else:
        cur = deb.setdefault(key, {"n": 0, "mult": 1.0})
        cur["n"] = min(int(params.get("max_mark", 5)), int(cur.get("n", 0) or 0) + 1)
    tag = params.get("tag", "🎒")
    logs.append(f"{tag} {params.get('name', '标记')}！{params.get('mark_desc', '敌人被标记！')}")


def _sp_slow(battle, player, dmg, logs, params: dict):
    """proc_slow：概率减速
    params: chance, slow_pct, slow_turns"""
    battle.e_buffs["spd_down"] = max(battle.e_buffs.get("spd_down", 0), int(params.get("slow_turns", 2)))
    battle.e_buffs["_spd_down_pct"] = float(params.get("slow_pct", 0.15))
    tag = params.get("tag", "🕸️")
    logs.append(f"{tag} {params.get('name', '减速')}！敌方速度下降 {int(params.get('slow_pct', 0.15)*100)}%！")


def _sp_heal_hp(battle, player, dmg, logs, params: dict):
    """proc_heal_hp：概率回血 %max_hp
    params: chance, heal_pct"""
    heal = int(player.get("max_hp", 1) * float(params.get("heal_pct", 0.05)))
    player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
    tag = params.get("tag", "🌳")
    logs.append(f"{tag} {params.get('name', '回血')}！回复 {heal} 点生命！")


def _sp_heal_mp(battle, player, dmg, logs, params: dict):
    """proc_heal_mp：概率回蓝 %max_mp
    params: chance, heal_pct"""
    heal = int(player.get("max_mp", 1) * float(params.get("heal_pct", 0.05)))
    player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + heal)
    tag = params.get("tag", "🎵")
    logs.append(f"{tag} {params.get('name', '回蓝')}！回复 {heal} 点魔力！")


def _sp_lifesteal(battle, player, dmg, logs, params: dict):
    """proc_lifesteal：概率吸血 %伤害
    params: chance, lifesteal_pct"""
    heal = int(dmg * float(params.get("lifesteal_pct", 0.15)))
    if heal > 0:
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        tag = params.get("tag", "🌑")
        logs.append(f"{tag} {params.get('name', '吸血')}！汲取 {heal} 点生命！")


def _sp_buff(battle, player, dmg, logs, params: dict):
    """proc_buff：概率自身 buff
    params: chance, buff_key, buff_val, buff_turns, buff_mode(set/add/stack)"""
    key = params.get("buff_key")
    val = params.get("buff_val")
    if params.get("buff_mode") == "stack":
        lv = battle.p_eff.get(key, 0)
        if lv < int(params.get("buff_max", 10)):
            battle.p_eff[key] = lv + 1
            tag = params.get("tag", "🔨")
            logs.append(f"{tag} {params.get('name', '叠加')}！（当前 {lv+1} 层）")
    else:
        battle.p_eff[key] = val
        tag = params.get("tag", "✨")
        logs.append(f"{tag} {params.get('name', 'Buff')}！")


def _sp_execute(battle, player, dmg, logs, params: dict):
    """proc_execute：低血处决（追加 pct×atk 伤害）
    params: hp_lt, pct, stat"""
    from ..engine import calc_damage
    ratio = battle.enemy.get("hp", 0) / max(1, battle.enemy.get("max_hp", 1))
    if ratio < float(params.get("hp_lt", 0.30)):
        stat = params.get("stat", "atk")
        atk = _sp_stat(battle, player, stat)
        dmg_type = params.get("dmg_type", "true" if params.get("true_dmg") else ("phys" if stat == "atk" else "magic"))
        edef = 0 if dmg_type == "true" else int(_sp_enemy_def(battle, params.get("edef", "def" if stat == "atk" else "mdef")))
        cd = calc_damage(int(atk * float(params.get("pct", 0.50))), edef, dmg_type=dmg_type)
        if cd > 0:
            battle._damage_enemy(cd, logs)
            tag = params.get("tag", "💀")
            logs.append(f"{tag} {params.get('name', '处决')}！追加 {cd} 点伤害！")


def _sp_shield(battle, player, dmg, logs, params: dict):
    """proc_shield：概率护盾
    params: chance, shield_pct, shield_turns"""
    shield = int(player.get("max_hp", 1) * float(params.get("shield_pct", 0.05)))
    battle._add_shield(params.get("shield_key", "proc_shield"), shield, int(params.get("shield_turns", 1)))
    tag = params.get("tag", "🛡️")
    logs.append(f"{tag} {params.get('name', '护盾')}！获得 {shield} 点护盾！")


def _sp_burn(battle, player, dmg, logs, params: dict):
    """proc_burn：概率灼烧
    params: chance, burn_pct, burn_turns, max_stacks"""
    deb = battle.enemy.setdefault("debuffs", {})
    cur = deb.get("burn") or {"n": 0, "mult": 1.0}
    cur["n"] = min(int(params.get("max_stacks", 3)), int(cur.get("n", 0) or 0) + 1)
    cur["pct"] = float(params.get("burn_pct", 0.01))
    cur["turns"] = max(int(cur.get("turns", 0) or 0), int(params.get("burn_turns", 2)))
    deb["burn"] = cur
    tag = params.get("tag", "🔥")
    logs.append(f"{tag} {params.get('name', '灼烧')}！目标被灼烧！（每回合损 {int(params.get('burn_pct', 0.01)*100)}% 最大生命，{params.get('burn_turns', 2)} 回合）")


def _sp_freeze(battle, player, dmg, logs, params: dict):
    """proc_freeze：概率冰冻
    params: chance, freeze_turns"""
    if hasattr(battle, "_freeze_enemy"):
        battle._freeze_enemy()
    else:
        battle.e_buffs["freeze"] = max(battle.e_buffs.get("freeze", 0), int(params.get("freeze_turns", 1)))
    tag = params.get("tag", "🧊")
    logs.append(f"{tag} {params.get('name', '冰冻')}！敌人被冻结！")


def _sp_purify_heal(battle, player, dmg, logs, params: dict):
    """proc_purify_heal：概率净化减益 + 回血
    params: chance, heal_pct"""
    neg = [k for k in battle.p_buffs if k in ("spd_down", "poison", "mortal_wound", "atk_down", "def_down", "burn", "weak")]
    if neg:
        del battle.p_buffs[neg[0]]
        tag = params.get("tag", "⚖️")
        logs.append(f"{tag} {params.get('name', '净化')}！净化 1 个负面效果！")
    heal = int(player.get("max_hp", 1) * float(params.get("heal_pct", 0.04)))
    player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
    tag = params.get("tag", "⚖️")
    logs.append(f"{tag} {params.get('name', '净化')}！回复 {heal} 点生命！")


def _sp_armor_break(battle, player, dmg, logs, params: dict):
    """proc_armor_break：概率破甲（可带：已破甲追加伤害）
    params: chance, break_pct, break_turns, bonus_atk_pct"""
    if "def_down" in battle.e_buffs and params.get("bonus_atk_pct"):
        from ..engine import calc_damage
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("atk", 0) * float(params["bonus_atk_pct"])), est.get("def", 0))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            tag = params.get("tag", "🐎")
            logs.append(f"{tag} {params.get('name', '破甲追加')}！追加 {cd} 点伤害！")
    else:
        battle.e_buffs["def_down"] = max(battle.e_buffs.get("def_down", 0), int(params.get("break_turns", 2)))
        battle.e_buffs["_armor_break_pct"] = float(params.get("break_pct", 0.15))
        tag = params.get("tag", "🐎")
        logs.append(f"{tag} {params.get('name', '破甲')}！敌人防御下降 {int(params.get('break_pct', 0.15)*100)}%！")


def _sp_anti_heal(battle, player, dmg, logs, params: dict):
    """proc_anti_heal：概率破甲 + 受疗 -%
    params: chance, break_pct, break_turns, anti_heal_pct"""
    battle.e_buffs["def_down"] = max(battle.e_buffs.get("def_down", 0), int(params.get("break_turns", 2)))
    battle.e_buffs["_armor_break_pct"] = float(params.get("break_pct", 0.15))
    battle.e_buffs["_anti_heal_pct"] = float(params.get("anti_heal_pct", 0.30))
    tag = params.get("tag", "🌅")
    logs.append(f"{tag} {params.get('name', '破甲+禁疗')}！敌人破甲且受疗效果 -{int(params.get('anti_heal_pct', 0.30)*100)}%！")


def _sp_mon_atk_down(battle, player, dmg, logs, params: dict):
    """proc_mon_atk_down：概率敌方攻击 -%
    params: chance, atk_down_pct, turns"""
    battle.e_buffs["mon_atk_down"] = max(battle.e_buffs.get("mon_atk_down", 0), int(params.get("turns", 2)))
    battle.e_buffs["_weaken_val"] = float(params.get("atk_down_pct", 0.15))
    tag = params.get("tag", "🐉")
    logs.append(f"{tag} {params.get('name', '敌方攻击下降')}！敌人攻击下降 {int(params.get('atk_down_pct', 0.15)*100)}%！")


def _sp_def_up_stack(battle, player, dmg, logs, params: dict):
    """proc_def_up_stack：受击概率叠防御 buff（层数上限）
    params: chance, def_pct, turns, max_stacks, stack_key"""
    key = params.get("stack_key", "tie_pi_def_lv")
    lv = battle.p_buffs.get(key, 0)
    if lv < int(params.get("max_stacks", 2)):
        battle.p_buffs[key] = lv + 1
        battle.p_buffs[params.get("turns_key", "tie_pi_def_turns")] = int(params.get("turns", 2))
    tag = params.get("tag", "🛡️")
    logs.append(f"{tag} {params.get('name', '防御叠加')}！防御 +{int(params.get('def_pct', 0.15)*100)}%！")


def _sp_dmg_cut(battle, player, dmg, logs, params: dict):
    """proc_dmg_cut：受击概率本次伤害 -%
    params: chance, cut_pct"""
    dmg = max(1, int(dmg * float(params.get("cut_pct", 0.50))))
    battle._last_dmg = dmg
    tag = params.get("tag", "🛡️")
    logs.append(f"{tag} {params.get('name', '减伤')}！本次受击伤害减半！")


def _sp_counter(battle, player, dmg, logs, params: dict):
    """proc_counter：受击概率反击
    params: chance, atk_pct, once_per_round(bool)"""
    if not battle.enemy.get("hp", 0) or battle.enemy.get("hp", 0) <= 0:
        return
    if params.get("once_per_round"):
        _turn = getattr(battle, "round", 0) or 0
        if (battle.p_eff or {}).get("counter_used") == _turn:
            return
        battle.p_eff["counter_used"] = _turn
    from ..engine import calc_damage
    pst = battle._player_stats(player)
    est = battle._enemy_stats()
    cd = calc_damage(int(pst.get("atk", 0) * float(params.get("atk_pct", 0.40))), est.get("def", 0), dmg_type="phys")
    cd = battle._boss_dmg_filter(cd, player, logs)
    battle._damage_enemy(cd, logs)
    tag = params.get("tag", "🌊")
    logs.append(f"{tag} {params.get('name', '反击')}！反击 {cd} 点伤害！")


def _sp_res_gain(battle, player, dmg, logs, params: dict):
    """proc_res_gain：概率获得资源
    params: chance, res_key, amount"""
    battle._res_gain(player, params.get("res_key", "cp"), int(params.get("amount", 1)))
    tag = params.get("tag", "🗡️")
    logs.append(f"{tag} {params.get('name', '资源')}！额外获得 {params.get('amount', 1)} 点资源！")


def _sp_stealth(battle, player, dmg, logs, params: dict):
    """proc_stealth：低血概率隐身（下次攻击必暴击）
    params: hp_lt, chance, buff_key"""
    ratio = battle.enemy.get("hp", 0) / max(1, battle.enemy.get("max_hp", 1))
    if ratio < float(params.get("hp_lt", 0.30)):
        battle.p_buffs[params.get("buff_key", "stealth")] = 1
        tag = params.get("tag", "🌙")
        logs.append(f"{tag} {params.get('name', '隐身')}！下一次攻击必定暴击！")


def _sp_mp_on_dmg(battle, player, dmg, logs, params: dict):
    """proc_mp_on_dmg：概率雷击 + 回伤害% MP
    params: chance, stat, pct, mp_pct"""
    from ..engine import calc_damage
    stat = params.get("stat", "matk")
    atk = _sp_stat(battle, player, stat)
    edef = _sp_enemy_def(battle, params.get("edef", "mdef" if stat == "matk" else "def"))
    dmg_type = params.get("dmg_type", "magic" if stat == "matk" else "phys")
    cd = calc_damage(int(atk * float(params.get("pct", 0.40))), int(edef), dmg_type=dmg_type)
    if cd > 0:
        battle._damage_enemy(cd, logs)
        mp = int(cd * float(params.get("mp_pct", 0.15)))
        player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + mp)
        tag = params.get("tag", "✨")
        logs.append(f"{tag} {params.get('name', '雷击回蓝')}！追加 {cd} 点伤害，回复 {mp} 点魔力！")


def _sp_erode(battle, player, dmg, logs, params: dict):
    """proc_erode：概率暗蚀（敌方每回合损 %max_hp，全额回血）
    params: chance, max_stacks, turns"""
    deb = battle.enemy.setdefault("debuffs", {})
    cur = deb.get("erode") or {"n": 0, "mult": 1.0}
    cur["n"] = min(int(params.get("max_stacks", 2)), int(cur.get("n", 0) or 0) + 1)
    deb["erode"] = cur
    tag = params.get("tag", "🌑")
    logs.append(f"{tag} {params.get('name', '暗蚀')}！敌人被暗蚀侵蚀！（每回合损 {params.get('pct', 1)}% 最大生命，全额回血）")


def _sp_thunder_burst(battle, player, dmg, logs, params: dict):
    """proc_thunder_burst：雷印体系——叠印/满印引爆
    params: chance, max_mark, burst_pct, stat(matk), edef"""
    from ..engine import calc_damage
    deb = battle.enemy.setdefault("debuffs", {})
    mk = deb.setdefault("element_marks", {})
    mk["thunder"] = min(int(params.get("max_mark", 3)), int(mk.get("thunder", 0) or 0) + 1)
    if int(mk.get("thunder", 0)) >= int(params.get("burst_at", 3)):
        stat = params.get("stat", "matk")
        atk = _sp_stat(battle, player, stat)
        edef = _sp_enemy_def(battle, params.get("edef", "mdef"))
        cd = calc_damage(int(atk * float(params.get("burst_pct", 0.90))), int(edef), dmg_type="magic")
        if cd > 0:
            battle._damage_enemy(cd, logs)
        mk["thunder"] = 0
        tag = params.get("tag", "📜")
        logs.append(f"{tag} {params.get('name', '引爆')}！引爆 {cd} 点雷伤！")
    else:
        tag = params.get("tag", "📜")
        logs.append(f"{tag} {params.get('name', '刻印')}！雷印记 +1！")


# 注册表：type → 执行器
SET_PROC_TYPES.update({
    "proc_flat_dmg": _sp_flat_dmg,
    "proc_mark": _sp_mark,
    "proc_slow": _sp_slow,
    "proc_heal_hp": _sp_heal_hp,
    "proc_heal_mp": _sp_heal_mp,
    "proc_lifesteal": _sp_lifesteal,
    "proc_buff": _sp_buff,
    "proc_execute": _sp_execute,
    "proc_shield": _sp_shield,
    "proc_burn": _sp_burn,
    "proc_freeze": _sp_freeze,
    "proc_purify_heal": _sp_purify_heal,
    "proc_armor_break": _sp_armor_break,
    "proc_anti_heal": _sp_anti_heal,
    "proc_mon_atk_down": _sp_mon_atk_down,
    "proc_def_up_stack": _sp_def_up_stack,
    "proc_dmg_cut": _sp_dmg_cut,
    "proc_counter": _sp_counter,
    "proc_res_gain": _sp_res_gain,
    "proc_stealth": _sp_stealth,
    "proc_mp_on_dmg": _sp_mp_on_dmg,
    "proc_erode": _sp_erode,
    "proc_thunder_burst": _sp_thunder_burst,
})


def _execute_set_proc(eff: dict, battle, player, dmg, logs):
    """数据驱动套装特效分发器：读 params.type → 调通用执行器。
    无 params 时按旧 effect 名查注册表（兼容过渡期）。"""
    p = _sp_params(eff)
    t = p.get("type")
    if t and t in SET_PROC_TYPES:
        if random.random() > _sp_chance(eff):
            return
        SET_PROC_TYPES[t](battle, player, dmg, logs, p)
        return
    # 旧路径（无 params）：查 effect 名注册表
    fn = SET_PROC_EFFECTS.get(eff.get("effect"))
    if fn:
        fn(battle, player, dmg, logs)


@register(SET_PROC_EFFECTS, "frost")
def _sp_frost(battle, player, dmg, logs):
    """寒霜之力：30% 减速"""
    from ..battle import DEBUFF_TURNS  # 延迟引用，避免模块循环
    if random.random() < _set_chance("frost", 0.30):
        battle.e_buffs["spd_down"] = DEBUFF_TURNS
        logs.append("❄️ 寒霜之力！敌人速度下降！")


@register(SET_PROC_EFFECTS, "burn")
def _sp_burn(battle, player, dmg, logs):
    """烈焰之力：30% 灼烧
    契约 §4.2 修复：原误写 e_buffs["poison"] 为 bug——改为对 enemy 挂灼烧层
    enemy["debuffs"]["burn"]（目标级减益，副本/世界Boss 全局共享，mult 1.0）。"""
    if random.random() < _set_chance("burn", 0.30):
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.get("burn") or {"n": 0, "mult": 1.0}
        cur["n"] = min(5, int(cur.get("n", 0) or 0) + 1)
        cur["last_round"] = getattr(battle, "round", 0) or 0  # 记录叠层回合
        deb["burn"] = cur
        # 适应机制：目标记忆灼烧，叠层成功 +0.04（cap 0.20），回落由结算侧按回合判定
        adapt = battle.enemy.setdefault("adapt", {})
        adapt["burn"] = min(0.20, float(adapt.get("burn", 0.0) or 0.0) + 0.04)
        logs.append("🔥 烈焰之力！敌人被灼烧！")


@register(SET_PROC_EFFECTS, "thunder")
def _sp_thunder(battle, player, dmg, logs):
    """雷霆一击：25% 追加 60% 攻击伤害"""
    from ..engine import calc_damage
    if random.random() < _set_chance("thunder", 0.25):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        tdmg = calc_damage(int(pst["atk"] * 0.6), est["def"])
        battle._damage_enemy(tdmg, logs)
        logs.append(f"⚡ 雷霆一击！追加 {tdmg} 点伤害！")


@register(SET_PROC_EFFECTS, "pierce")
def _sp_pierce(battle, player, dmg, logs):
    """破甲之力：30% 破甲"""
    from ..battle import DEBUFF_TURNS  # 延迟引用，避免模块循环
    if random.random() < _set_chance("pierce", 0.30):
        battle.e_buffs["def_down"] = DEBUFF_TURNS
        # v105 M07 P3-7：旧世界「诸神」套文案 → 破甲之力（与套装 desc「攻击 30% 概率破甲」一致）
        logs.append("⚔️ 破甲之力！敌人护甲破碎！")


@register(SET_PROC_EFFECTS, "lifesteal_set")
def _sp_lifesteal_set(battle, player, dmg, logs):
    """深渊之力：30% 汲取 15% 伤害为生命"""
    if random.random() < _set_chance("lifesteal_set", 0.30):
        heal = int(dmg * 0.15)
        player["hp"] = min(player.get("max_hp", player["hp"]), player.get("hp", 0) + heal)
        logs.append(f"🌑 深渊之力！汲取 {heal} 点生命！")


@register(SET_PROC_EFFECTS, "execute")
def _sp_execute(battle, player, dmg, logs):
    """灭世之力：处决（敌方 <30% 血时追加 25% 伤害）"""
    ratio = battle.enemy.get("hp", 0) / max(1, battle.enemy.get("max_hp", 1))
    if ratio < 0.30:
        bonus = int(dmg * 0.25)
        battle._damage_enemy(bonus, logs)
        logs.append(f"💀 灭世之力！处决追加 {bonus} 点伤害！")

# ============================================================
# v141.3 S1 套装去模板化 + D3 装备专属 handler（数据驱动追加）
# ============================================================

# ---- D3 装备专属 on_hit（HIT_EFFECTS，经 _equip_affix_ids 消费）----

@register(HIT_EFFECTS, "oath_sword")
def _h_oath_sword(battle, player, dmg, logs):
    """誓约之刃（王都誓约之剑）：暴击时回复 2% 最大生命"""
    if "oath_sword" in battle._equip_affix_ids(player):
        if getattr(battle, "_last_crit", False):
            heal = int(player.get("max_hp", 1) * float(_affix_effect("oath_sword").get("heal_pct", 0.02)))
            player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
            logs.append(f"🗡️ 誓约之刃！暴击回复 {heal} 点生命！")


@register(HIT_EFFECTS, "sanctum_light")
def _h_sanctum_light(battle, player, dmg, logs):
    """圣殿辉光（圣殿战锤）：15% 敌人攻击 -8%（1 回合）"""
    if "sanctum_light" in battle._equip_affix_ids(player) and random.random() < _affix_chance("sanctum_light", 0.15):
        eff = _affix_effect("sanctum_light")
        battle.e_buffs["enemy_atk_down"] = max(battle.e_buffs.get("enemy_atk_down", 0), int(eff.get("turns", 1)))
        battle.e_buffs["_enemy_atk_down_pct"] = float(eff.get("enemy_atk_down", 0.08))
        logs.append("✨ 圣殿辉光！敌人攻击下降 8%！")


@register(HIT_EFFECTS, "ember_furnace")
def _h_ember_furnace(battle, player, dmg, logs):
    """熔炉余烬（熔岩护手）：20% 灼烧 1% 最大生命×2 回合"""
    if "ember_furnace" in battle._equip_affix_ids(player) and random.random() < _affix_chance("ember_furnace", 0.20):
        eff = _affix_effect("ember_furnace")
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.get("burn") or {"n": 0, "mult": 1.0}
        cur["n"] = min(3, int(cur.get("n", 0) or 0) + 1)
        cur["pct"] = float(eff.get("burn_pct", 0.01))
        cur["turns"] = max(int(cur.get("turns", 0) or 0), int(eff.get("burn_turns", 2)))
        deb["burn"] = cur
        logs.append("🔥 熔炉余烬！目标被灼烧！（每回合损 1% 最大生命，2 回合）")


@register(HIT_EFFECTS, "blazing_sun")
def _h_blazing_sun(battle, player, dmg, logs):
    """烈日灼烧（铁砧战锤）：15% 火附加 8% + 灼烧 1.5%×3"""
    if "blazing_sun" in battle._equip_affix_ids(player):
        eff = _affix_effect("blazing_sun")
        ed = max(1, int(dmg * float(eff.get("pct", 0.08))))
        battle._damage_enemy(ed, logs)
        logs.append(f"🔥 烈日灼烧：火属性附加 {ed} 点伤害！")
        if random.random() < _affix_chance("blazing_sun", 0.15):
            deb = battle.enemy.setdefault("debuffs", {})
            cur = deb.get("burn") or {"n": 0, "mult": 1.0}
            cur["n"] = min(3, int(cur.get("n", 0) or 0) + 1)
            cur["pct"] = float(eff.get("burn_pct", 0.015))
            cur["turns"] = max(int(cur.get("turns", 0) or 0), int(eff.get("burn_turns", 3)))
            deb["burn"] = cur
            logs.append("🔥 烈日灼烧：目标被灼烧！（每回合损 1.5% 最大生命，3 回合）")


@register(HIT_EFFECTS, "deep_frost")
def _h_deep_frost(battle, player, dmg, logs):
    """深寒（银叶法杖）：20% 冰附加 8% + 减速 20% 2 回合"""
    if "deep_frost" in battle._equip_affix_ids(player):
        eff = _affix_effect("deep_frost")
        ed = max(1, int(dmg * float(eff.get("pct", 0.08))))
        battle._damage_enemy(ed, logs)
        logs.append(f"❄️ 深寒：冰属性附加 {ed} 点伤害！")
        if random.random() < _affix_chance("deep_frost", 0.20):
            battle.e_buffs["spd_down"] = max(battle.e_buffs.get("spd_down", 0), int(eff.get("slow_turns", 2)))
            battle.e_buffs["_spd_down_pct"] = float(eff.get("slow", 0.20))
            logs.append("❄️ 深寒：目标减速 20%！")


@register(HIT_EFFECTS, "thunder_mark")
def _h_thunder_mark(battle, player, dmg, logs):
    """雷鸣印记（雷鸣龙鳞）：20% 叠雷鸣印记"""
    if "thunder_mark" in battle._equip_affix_ids(player) and random.random() < _affix_chance("thunder_mark", 0.20):
        eff = _affix_effect("thunder_mark")
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.setdefault("mark", {"n": 0, "mult": 1.0})
        cur["n"] = min(int(eff.get("max_mark", 5)), int(cur.get("n", 0) or 0) + 1)
        logs.append("⚡ 雷鸣印记！敌人被标记（每层 +2% 伤害）")


@register(HIT_EFFECTS, "soul_devourer")
def _h_soul_devourer(battle, player, dmg, logs):
    """噬魂者：15% 将 6% 伤害转生命"""
    if "soul_devourer" in battle._equip_affix_ids(player) and random.random() < _affix_chance("soul_devourer", 0.15):
        heal = int(dmg * float(_affix_effect("soul_devourer").get("heal_pct", 0.06)))
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"👻 噬魂者！汲取 {heal} 点生命！")


# ---- D3 装备专属 on_taken（TAKEN_EFFECTS，ctx 结算）----

@register(TAKEN_EFFECTS, "blood_oath_echo")
def _t_blood_oath_echo(battle, player, ctx, logs):
    """血誓回响（血誓战剑）：受击 20% 回复 2% 最大生命 + 下次攻击 +10%"""
    if "blood_oath_echo" in battle._equip_affix_ids(player) and random.random() < _affix_chance("blood_oath_echo", 0.20):
        eff = _affix_effect("blood_oath_echo")
        heal = int(player.get("max_hp", 1) * float(eff.get("heal_pct", 0.02)))
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        battle.p_eff["atk_up"] = float(eff.get("atk_up", 0.10))
        logs.append(f"🩸 血誓回响！回复 {heal} 点生命，下次攻击 +10%！")


@register(TAKEN_EFFECTS, "night_watch")
def _t_night_watch(battle, player, ctx, logs):
    """长夜守望（长夜徽记）：受击 5% 回复 1% 最大生命"""
    if "night_watch" in battle._equip_affix_ids(player) and random.random() < _affix_chance("night_watch", 0.05):
        heal = int(player.get("max_hp", 1) * float(_affix_effect("night_watch").get("heal_pct", 0.01)))
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🌙 长夜守望！回复 {heal} 点生命！")


# ---- D3 装备专属 turn_start（TURN_START_EFFECTS）----

@register(TURN_START_EFFECTS, "morning_dew")
def _ts_morning_dew(battle, player, logs):
    """晨露滋养（晨露戒指）：每回合回复 1% 魔力"""
    if "morning_dew" in battle._equip_affix_ids(player) and player.get("mp", 0) < player.get("max_mp", 1):
        heal = int(player.get("max_mp", player.get("mp", 1)) * float(_affix_effect("morning_dew").get("pct", 0.01)))
        player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + heal)
        logs.append(f"💧 晨露滋养！回复 {heal} 点魔力！")


@register(TURN_START_EFFECTS, "night_prayer")
def _ts_night_prayer(battle, player, logs):
    """夜祷（夜祷兜帽）：每回合回复 3% 最大生命"""
    if "night_prayer" in battle._equip_affix_ids(player) and player.get("hp", 0) < player.get("max_hp", 1):
        heal = int(player.get("max_hp", player.get("hp", 1)) * float(_affix_effect("night_prayer").get("pct", 0.03)))
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🙏 夜祷！回复 {heal} 点生命！")


# ---- S1 套装 on_hit（SET_PROC_EFFECTS，_set_attack_proc 分发）----

@register(SET_PROC_EFFECTS, "travel_mark")
def _sp_travel_mark(battle, player, dmg, logs):
    """旅人标记（旅人公会 4 件）：30% 叠 1 层敌人标记"""
    if random.random() < _set_chance("travel_mark", 0.30):
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.setdefault("mark", {"n": 0, "mult": 1.0})
        cur["n"] = min(5, int(cur.get("n", 0) or 0) + 1)
        logs.append("🎒 旅人标记！敌人被标记（每层 +20% 伤害）")


@register(SET_PROC_EFFECTS, "hunter_mark_bonus")
def _sp_hunter_mark_bonus(battle, player, dmg, logs):
    """猎手印记（猎手 4 件）：40% 标记目标 +15% 伤害否则叠层"""
    if random.random() < _set_chance("hunter_mark_bonus", 0.40):
        mk = (battle.enemy.get("debuffs") or {}).get("mark") or {}
        if int(mk.get("n", 0) or 0) > 0:
            battle._damage_enemy(int(dmg * 0.15), logs)
            logs.append("🏹 猎手印记！标记目标追加 15% 伤害！")
        else:
            deb = battle.enemy.setdefault("debuffs", {})
            cur = deb.setdefault("mark", {"n": 0, "mult": 1.0})
            cur["n"] = min(5, int(cur.get("n", 0) or 0) + 1)
            logs.append("🏹 猎手印记！敌人被标记！")


@register(SET_PROC_EFFECTS, "gale_double")
def _sp_gale_double(battle, player, dmg, logs):
    """风行连射（风行 4 件）：25% 追加 50% atk 连射"""
    from ..engine import calc_damage
    if random.random() < _set_chance("gale_double", 0.25):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("atk", 0) * 0.50), est.get("def", 0))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"🌪️ 风行连射！追加 {cd} 点伤害！")


@register(SET_PROC_EFFECTS, "eagle_vision")
def _sp_eagle_vision(battle, player, dmg, logs):
    """鹰眼锐视（鹰眼 4 件）：35% 下一次攻击暴伤 +30%"""
    if random.random() < _set_chance("eagle_vision", 0.35):
        battle.p_eff["eagle_vision"] = True
        logs.append("🦅 鹰眼锐视！下一次攻击暴击伤害 +30%！")


@register(SET_PROC_EFFECTS, "sky_chain")
def _sp_sky_chain(battle, player, dmg, logs):
    """苍穹连星（苍穹 4 件）：25% 追加 60% atk 箭雨（标记时 75%）"""
    from ..engine import calc_damage
    if random.random() < _set_chance("sky_chain", 0.25):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        mk = (battle.enemy.get("debuffs") or {}).get("mark") or {}
        pct = 0.75 if int(mk.get("n", 0) or 0) > 0 else 0.60
        cd = calc_damage(int(pst.get("atk", 0) * pct), est.get("def", 0))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"☄️ 苍穹连星！追加 {cd} 点伤害！")


@register(SET_PROC_EFFECTS, "hunt_pack")
def _sp_hunt_pack(battle, player, dmg, logs):
    """狩猎本能（猎手套 4 件）：30% 追加 50% atk 追击，低血 <50% +20%"""
    from ..engine import calc_damage
    if random.random() < _set_chance("hunt_pack", 0.30):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        hp_ratio = battle.enemy.get("hp", 0) / max(1, battle.enemy.get("max_hp", 1))
        pct = 0.60 if hp_ratio < 0.50 else 0.50
        cd = calc_damage(int(pst.get("atk", 0) * pct), est.get("def", 0))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"🏹 狩猎本能！追加 {cd} 点伤害！")


@register(SET_PROC_EFFECTS, "shadow_track")
def _sp_shadow_track(battle, player, dmg, logs):
    """暗影追踪（暗夜套 4 件）：30% 叠 1 层暗影标记"""
    if random.random() < _set_chance("shadow_track", 0.30):
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.setdefault("mark", {"n": 0, "mult": 1.0})
        cur["n"] = min(5, int(cur.get("n", 0) or 0) + 1)
        logs.append("🌑 暗影追踪！敌人被暗影标记！")


@register(SET_PROC_EFFECTS, "ranger_net")
def _sp_ranger_net(battle, player, dmg, logs):
    """巡林罗网（巡林套 3 件）：30% 敌方速度 -15% 2 回合"""
    if random.random() < _set_chance("ranger_net", 0.30):
        battle.e_buffs["spd_down"] = max(battle.e_buffs.get("spd_down", 0), 2)
        battle.e_buffs["_spd_down_pct"] = 0.15
        logs.append("🕸️ 巡林罗网！敌方速度下降 15%！")


@register(SET_PROC_EFFECTS, "cloth_regen_battle")
def _sp_cloth_regen_battle(battle, player, dmg, logs):
    """布衣愈合（布衣 4 件）：30% 回 8% max_hp"""
    if random.random() < _set_chance("cloth_regen_battle", 0.30):
        heal = int(player.get("max_hp", 1) * 0.08)
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"☀️ 布衣愈合！回复 {heal} 点生命！")


@register(SET_PROC_EFFECTS, "bless_chant_mp")
def _sp_bless_chant_mp(battle, player, dmg, logs):
    """祝福咏叹（祝福 4 件）：35% 回 5% max_mp"""
    if random.random() < _set_chance("bless_chant_mp", 0.35):
        heal = int(player.get("max_mp", 1) * 0.05)
        player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + heal)
        logs.append(f"🎵 祝福咏叹！回复 {heal} 点魔力！")


@register(SET_PROC_EFFECTS, "judge_purify_heal")
def _sp_judge_purify_heal(battle, player, dmg, logs):
    """审判净化（审判 4 件）：25% 净化 1 减益 + 回 4% max_hp"""
    if random.random() < _set_chance("judge_purify_heal", 0.25):
        neg = [k for k in battle.p_buffs if k in ("spd_down", "poison", "mortal_wound", "atk_down", "def_down", "burn", "weak")]
        if neg:
            del battle.p_buffs[neg[0]]
            logs.append("⚖️ 审判净化！净化 1 个负面效果！")
        heal = int(player.get("max_hp", 1) * 0.04)
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"⚖️ 审判净化！回复 {heal} 点生命！")


@register(SET_PROC_EFFECTS, "ranger_regen_wild")
def _sp_ranger_regen_wild(battle, player, dmg, logs):
    """护林再生（护林套 3 件）：40% 回 5% max_hp"""
    if random.random() < _set_chance("ranger_regen_wild", 0.40):
        heal = int(player.get("max_hp", 1) * 0.05)
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🌳 护林再生！回复 {heal} 点生命！")


@register(SET_PROC_EFFECTS, "iron_execute_rampage")
def _sp_iron_execute_rampage(battle, player, dmg, logs):
    """黑铁斩杀（黑铁佣兵 4 件）：敌 hp<40% 时 30% 追加 50% atk 斩杀"""
    from ..engine import calc_damage
    hp_ratio = battle.enemy.get("hp", 0) / max(1, battle.enemy.get("max_hp", 1))
    if hp_ratio < 0.40 and random.random() < _set_chance("iron_execute_rampage", 0.30):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("atk", 0) * 0.50), est.get("def", 0))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"💀 黑铁斩杀！追加 {cd} 点伤害！")


@register(SET_PROC_EFFECTS, "shadow_combo_double")
def _sp_shadow_combo_double(battle, player, dmg, logs):
    """轻影连刺（轻影 4 件）：25% 追加 40% atk 连刺"""
    from ..engine import calc_damage
    if random.random() < _set_chance("shadow_combo_double", 0.25):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("atk", 0) * 0.40), est.get("def", 0))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"🗡️ 轻影连刺！追加 {cd} 点伤害！")


@register(SET_PROC_EFFECTS, "night_backstab")
def _sp_night_backstab(battle, player, dmg, logs):
    """夜行背刺（夜行 4 件）：满血 +25% 增伤，否则 20% 5% max_hp 真伤"""
    from ..engine import calc_damage
    hp_ratio = battle.enemy.get("hp", 0) / max(1, battle.enemy.get("max_hp", 1))
    if hp_ratio >= 0.999:
        battle._damage_enemy(int(dmg * 0.25), logs)
        logs.append("🌙 夜行背刺！满血目标追加 25% 伤害！")
    elif random.random() < _set_chance("night_backstab", 0.20):
        pst = battle._player_stats(player)
        cd = calc_damage(int(battle.enemy.get("max_hp", 1) * 0.05), 0)
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"🌙 夜行背刺！追加 {cd} 点真伤！")


@register(SET_PROC_EFFECTS, "shadow_etch_vuln")
def _sp_shadow_etch_vuln(battle, player, dmg, logs):
    """阴影蚀刻（阴影 4 件）：30% 叠 1 层蚀刻（每层 +15% 受伤害）"""
    if random.random() < _set_chance("shadow_etch_vuln", 0.30):
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.setdefault("mark", {"n": 0, "mult": 1.0})
        cur["n"] = min(5, int(cur.get("n", 0) or 0) + 1)
        logs.append("🌒 阴影蚀刻！敌人被蚀刻（每层 +15% 受伤害）")


@register(SET_PROC_EFFECTS, "phantom_echo")
def _sp_phantom_echo(battle, player, dmg, logs):
    """幻影分身（幻影 4 件）：20% 追加 60% atk 幻影斩（暴击时 35%）"""
    from ..engine import calc_damage
    is_crit = getattr(battle, "_last_crit", False)
    chance = 0.35 if is_crit else 0.20
    if random.random() < _set_chance("phantom_echo", chance):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("atk", 0) * 0.60), est.get("def", 0))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"👻 幻影分身！追加 {cd} 点伤害！")


@register(SET_PROC_EFFECTS, "midnight_assassinate")
def _sp_midnight_assassinate(battle, player, dmg, logs):
    """午夜暗杀（午夜 4 件）：敌 hp<30% 时 35% 追加 40% atk 真伤"""
    from ..engine import calc_damage
    hp_ratio = battle.enemy.get("hp", 0) / max(1, battle.enemy.get("max_hp", 1))
    if hp_ratio < 0.30 and random.random() < _set_chance("midnight_assassinate", 0.35):
        pst = battle._player_stats(player)
        cd = calc_damage(int(pst.get("atk", 0) * 0.40), 0)
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"🗡️ 午夜暗杀！追加 {cd} 点真伤处决！")


@register(SET_PROC_EFFECTS, "shadow_combo_cp")
def _sp_shadow_combo_cp(battle, player, dmg, logs):
    """轻影连击套（轻影套 4 件）：30% 额外获得 1 连击点"""
    if random.random() < _set_chance("shadow_combo_cp", 0.30):
        battle._res_gain(player, "cp", 1)
        logs.append("🗡️ 轻影连击！额外获得 1 连击点！")


@register(SET_PROC_EFFECTS, "night_stealth_exec")
def _sp_night_stealth_exec(battle, player, dmg, logs):
    """夜行潜行套（夜行套 4 件）：敌 hp<30% 时 30% 下一次攻击必定暴击"""
    hp_ratio = battle.enemy.get("hp", 0) / max(1, battle.enemy.get("max_hp", 1))
    if hp_ratio < 0.30 and random.random() < _set_chance("night_stealth_exec", 0.30):
        battle.p_buffs["stealth"] = 1
        logs.append("🌙 夜行潜行！下一次攻击必定暴击！")


@register(SET_PROC_EFFECTS, "shadow_erode_poison")
def _sp_shadow_erode_poison(battle, player, dmg, logs):
    """阴影侵蚀套（阴影套 4 件）：30% 叠 1 层毒（上限 5）"""
    if random.random() < _set_chance("shadow_erode_poison", 0.30):
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.get("poison") or {"n": 0, "mult": 1.0}
        cur["n"] = min(5, int(cur.get("n", 0) or 0) + 1)
        deb["poison"] = cur
        logs.append("☠️ 阴影侵蚀！敌人中毒！（每层持续伤害）")


@register(SET_PROC_EFFECTS, "frost_hunt_freeze")
def _sp_frost_hunt_freeze(battle, player, dmg, logs):
    """霜猎冰冻（霜猎套 3 件）：20% 冻结敌人 1 回合（Boss 减速 40%）"""
    if random.random() < _set_chance("frost_hunt_freeze", 0.20):
        if hasattr(battle, "_freeze_enemy"):
            battle._freeze_enemy()
            logs.append("🧊 霜猎冰冻！敌人被冻结！")
        else:
            battle.e_buffs["freeze"] = max(battle.e_buffs.get("freeze", 0), 1)
            logs.append("🧊 霜猎冰冻！敌人被冻结！")


@register(SET_PROC_EFFECTS, "silver_knight_lance")
def _sp_silver_knight_lance(battle, player, dmg, logs):
    """白银冲锋（白银骑士 4 件）：30% 破甲 15% 2 回合 + 已破甲追加 30% atk"""
    from ..engine import calc_damage
    if random.random() < _set_chance("silver_knight_lance", 0.30):
        if "def_down" in battle.e_buffs:
            pst = battle._player_stats(player)
            est = battle._enemy_stats()
            cd = calc_damage(int(pst.get("atk", 0) * 0.30), est.get("def", 0))
            if cd > 0:
                battle._damage_enemy(cd, logs)
                logs.append(f"🐎 白银冲锋！破甲追加 {cd} 点伤害！")
        else:
            battle.e_buffs["def_down"] = max(battle.e_buffs.get("def_down", 0), 2)
            battle.e_buffs["_armor_break_pct"] = 0.15
            logs.append("🐎 白银冲锋！敌人防御下降 15%！")


@register(SET_PROC_EFFECTS, "jing_tie_refine")
def _sp_jing_tie_refine(battle, player, dmg, logs):
    """精淬（精铁 4 件）：50% 叠 1 层精淬（-5%/层，上限 3）"""
    if random.random() < _set_chance("jing_tie_refine", 0.50):
        lv = battle.e_buffs.get("jing_tie_lv", 0)
        if lv < 3:
            battle.e_buffs["jing_tie_lv"] = lv + 1
            battle.e_buffs["def_down"] = max(battle.e_buffs.get("def_down", 0), 2)
        logs.append("⚒️ 精淬！敌方防御 -5%/层！")


@register(SET_PROC_EFFECTS, "qi_shi_charge")
def _sp_qi_shi_charge(battle, player, dmg, logs):
    """骑士冲锋（骑士 4 件）：18% 追加 100% atk 冲锋（每回合 1 次）"""
    from ..engine import calc_damage
    if battle.p_eff.get("qi_shi_used"):
        return
    if random.random() < _set_chance("qi_shi_charge", 0.18):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("atk", 0) * 1.00), est.get("def", 0))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            battle.p_eff["qi_shi_used"] = True
            logs.append(f"🐎 骑士冲锋！追加 {cd} 点伤害！")


@register(SET_PROC_EFFECTS, "li_ming_dawnbreak")
def _sp_li_ming_dawnbreak(battle, player, dmg, logs):
    """黎明破晓（黎明 4 件）：30% 破甲 15% 2 回合 + 目标受疗 -30%"""
    if random.random() < _set_chance("li_ming_dawnbreak", 0.30):
        battle.e_buffs["def_down"] = max(battle.e_buffs.get("def_down", 0), 2)
        battle.e_buffs["_armor_break_pct"] = 0.15
        battle.e_buffs["_anti_heal_pct"] = 0.30
        logs.append("🌅 黎明破晓！敌人破甲且受疗效果 -30%！")


@register(SET_PROC_EFFECTS, "jing_tie_edge")
def _sp_jing_tie_edge(battle, player, dmg, logs):
    """精铁锋刃（精铁套 4 件）：40% 本次攻击无视 15% 防御"""
    from ..engine import calc_damage
    if random.random() < _set_chance("jing_tie_edge", 0.40):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("atk", 0) * 0.15), 0)
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"⚔️ 精铁锋刃！追加 {cd} 点无视防御伤害！")


@register(SET_PROC_EFFECTS, "bai_lian_forge")
def _sp_bai_lian_forge(battle, player, dmg, logs):
    """百炼（百炼套 4 件）：叠 1 层百炼（+2% atk，上限 10）"""
    lv = battle.p_eff.get("bai_lian_lv", 0)
    if lv < 10:
        battle.p_eff["bai_lian_lv"] = lv + 1
        logs.append(f"🔨 百炼！攻击 +2%（当前 {lv+1} 层）")


@register(SET_PROC_EFFECTS, "long_yi_dread")
def _sp_long_yi_dread(battle, player, dmg, logs):
    """龙威压制（龙裔套 3 件）：30% 敌人攻击 -15% 2 回合"""
    if random.random() < _set_chance("long_yi_dread", 0.30):
        battle.e_buffs["mon_atk_down"] = max(battle.e_buffs.get("mon_atk_down", 0), 2)
        battle.e_buffs["_weaken_val"] = 0.15
        logs.append("🐉 龙威压制！敌人攻击下降 15%！")


@register(SET_PROC_EFFECTS, "lei_ting_chain")
def _sp_lei_ting_chain(battle, player, dmg, logs):
    """连环雷（雷霆 4 件）：25% 追加 50% matk 雷击（带雷印时 75%）"""
    from ..engine import calc_damage
    if random.random() < _set_chance("lei_ting_chain", 0.25):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        mk = (battle.enemy.get("debuffs") or {}).get("element_marks") or {}
        pct = 0.75 if int(mk.get("thunder", 0) or 0) > 0 else 0.50
        cd = calc_damage(int(pst.get("matk", 0) * pct), est.get("mdef", est.get("def", 0)))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"⚡ 连环雷！追加 {cd} 点雷击伤害！")


@register(SET_PROC_EFFECTS, "xue_tu_spark")
def _sp_xue_tu_spark(battle, player, dmg, logs):
    """蓄雷（学徒 4 件）：40% 叠 1 层雷印记（上限 3）"""
    if random.random() < _set_chance("xue_tu_spark", 0.40):
        deb = battle.enemy.setdefault("debuffs", {})
        mk = deb.setdefault("element_marks", {})
        mk["thunder"] = min(3, int(mk.get("thunder", 0) or 0) + 1)
        logs.append("⚡ 蓄雷！雷印记 +1！")


@register(SET_PROC_EFFECTS, "fu_wen_glyph_bolt")
def _sp_fu_wen_glyph_bolt(battle, player, dmg, logs):
    """符文雷刻（符文 4 件）：30% 追加 45% matk 雷击（雷印 ≥2 消耗 1 层 +30%）"""
    from ..engine import calc_damage
    if random.random() < _set_chance("fu_wen_glyph_bolt", 0.30):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        mk = (battle.enemy.setdefault("debuffs", {}).setdefault("element_marks", {}))
        pct = 0.45
        if int(mk.get("thunder", 0) or 0) >= 2:
            pct = 0.75
            mk["thunder"] = int(mk.get("thunder", 0)) - 1
        cd = calc_damage(int(pst.get("matk", 0) * pct), est.get("mdef", est.get("def", 0)))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"📜 符文雷刻！追加 {cd} 点雷击伤害！")


@register(SET_PROC_EFFECTS, "mi_fa_arcane_bolt")
def _sp_mi_fa_arcane_bolt(battle, player, dmg, logs):
    """秘术重雷（秘法 4 件）：20% 追加 80% matk 秘法雷击"""
    from ..engine import calc_damage
    if random.random() < _set_chance("mi_fa_arcane_bolt", 0.20):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("matk", 0) * 0.80), est.get("mdef", est.get("def", 0)))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"✨ 秘术重雷！追加 {cd} 点雷击伤害！")


@register(SET_PROC_EFFECTS, "xing_jie_starfall")
def _sp_xing_jie_starfall(battle, player, dmg, logs):
    """星坠（星界 4 件）：15% 追加 80% matk 星雷 + 溅射 40% matk"""
    from ..engine import calc_damage
    if random.random() < _set_chance("xing_jie_starfall", 0.15):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("matk", 0) * 0.80), est.get("mdef", est.get("def", 0)))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"☄️ 星坠！追加 {cd} 点星雷伤害！")


@register(SET_PROC_EFFECTS, "xing_chen_starstrike")
def _sp_xing_chen_starstrike(battle, player, dmg, logs):
    """星辰轰击（星辰 4 件）：25% 追加 75% matk 星雷（雷印满 3 必触发）"""
    from ..engine import calc_damage
    mk = (battle.enemy.setdefault("debuffs", {}).setdefault("element_marks", {}))
    full = int(mk.get("thunder", 0) or 0) >= 3
    if full or random.random() < _set_chance("xing_chen_starstrike", 0.25):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("matk", 0) * 0.75), est.get("mdef", est.get("def", 0)))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"🌟 星辰轰击！追加 {cd} 点星雷伤害！")


@register(SET_PROC_EFFECTS, "xue_tu_surge")
def _sp_xue_tu_surge(battle, player, dmg, logs):
    """蓄能（学徒套 4 件）：叠 1 层蓄能（下次雷击 +10%，上限 3）"""
    lv = battle.p_eff.get("xue_tu_surge_lv", 0)
    if lv < 3:
        battle.p_eff["xue_tu_surge_lv"] = lv + 1
        logs.append(f"⚡ 蓄能！下次雷击伤害 +10%（当前 {lv+1} 层）")


@register(SET_PROC_EFFECTS, "fu_wen_annihilate")
def _sp_fu_wen_annihilate(battle, player, dmg, logs):
    """符文爆印（符文套 4 件）：30% 叠雷印；雷印 ≥3 引爆 90% matk 雷伤并清印"""
    from ..engine import calc_damage
    if random.random() < _set_chance("fu_wen_annihilate", 0.30):
        deb = battle.enemy.setdefault("debuffs", {})
        mk = deb.setdefault("element_marks", {})
        mk["thunder"] = min(3, int(mk.get("thunder", 0) or 0) + 1)
        if int(mk.get("thunder", 0)) >= 3:
            pst = battle._player_stats(player)
            est = battle._enemy_stats()
            cd = calc_damage(int(pst.get("matk", 0) * 0.90), est.get("mdef", est.get("def", 0)))
            if cd > 0:
                battle._damage_enemy(cd, logs)
            mk["thunder"] = 0
            logs.append(f"📜 符文爆印！引爆 {cd} 点雷伤！")
        else:
            logs.append("📜 符文刻印！雷印记 +1！")


@register(SET_PROC_EFFECTS, "mi_fa_condense")
def _sp_mi_fa_condense(battle, player, dmg, logs):
    """秘术回响（秘法套 4 件）：25% 追加 40% matk 雷击 + 回 15% 伤害 MP"""
    from ..engine import calc_damage
    if random.random() < _set_chance("mi_fa_condense", 0.25):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("matk", 0) * 0.40), est.get("mdef", est.get("def", 0)))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            mp = int(cd * 0.15)
            player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + mp)
            logs.append(f"✨ 秘术回响！追加 {cd} 点雷击，回复 {mp} 点魔力！")


@register(SET_PROC_EFFECTS, "hei_zhao_erode")
def _sp_hei_zhao_erode(battle, player, dmg, logs):
    """暗蚀（黑沼 4 件）：30% 附加暗蚀 2 回合每回合 1% max_hp 暗伤全额回血"""
    if random.random() < _set_chance("hei_zhao_erode", 0.30):
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.get("erode") or {"n": 0, "mult": 1.0}
        cur["n"] = min(2, int(cur.get("n", 0) or 0) + 1)
        deb["erode"] = cur
        logs.append("🌑 暗蚀！敌人被暗蚀侵蚀！（每回合损 1% 最大生命，全额回血）")


@register(SET_PROC_EFFECTS, "xing_zhe_flow")
def _sp_xing_zhe_flow(battle, player, dmg, logs):
    """行者游血（行者套 4 件）：100% 吸血 6% 伤害"""
    heal = int(dmg * 0.06)
    if heal > 0:
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🩸 行者游血！汲取 {heal} 点生命！")


@register(SET_PROC_EFFECTS, "xing_zhe_hunt")
def _sp_xing_zhe_hunt(battle, player, dmg, logs):
    """猎血（行者 4 件）：40% 吸血 12% 伤害"""
    if random.random() < _set_chance("xing_zhe_hunt", 0.40):
        heal = int(dmg * 0.12)
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🩸 猎血！汲取 {heal} 点生命！")

# ============================================================
# v141.3 D2 独特装备触发型 handler 补充（on_hit/on_taken/turn_start）
# passive 型（giant_slayer/mark_hunt/executioner/top_hunter/last_breath/grim_ward）
# 走 _affix_dmg_mult 被动倍率通道（battle.py），不注册触发 handler
# ============================================================

# ---- D2 受击型（TAKEN_EFFECTS）----

@register(TAKEN_EFFECTS, "obsidian_aegis")
def _t_obsidian_aegis(battle, player, ctx, logs):
    """黑曜壁垒（D2）：受击 10% 获得 8% 最大生命护盾（3 回合）"""
    if "obsidian_aegis" in battle._equip_affix_ids(player) and random.random() < _affix_chance("obsidian_aegis", 0.10):
        eff = _affix_effect("obsidian_aegis")
        shield = int(player.get("max_hp", 1) * float(eff.get("pct", 0.08)))
        battle._add_shield("obsidian_aegis", shield, int(eff.get("turns", 3)))
        logs.append(f"🪨 黑曜壁垒！获得 {shield} 点护盾！")


@register(TAKEN_EFFECTS, "iron_bastion")
def _t_iron_bastion(battle, player, ctx, logs):
    """铁壁意志（D2）：受击 20% 使敌人下一次攻击 -25%"""
    if "iron_bastion" in battle._equip_affix_ids(player) and random.random() < _affix_chance("iron_bastion", 0.20):
        eff = _affix_effect("iron_bastion")
        battle.e_buffs["mon_atk_down"] = max(battle.e_buffs.get("mon_atk_down", 0), 1)
        battle.e_buffs["_weaken_val"] = float(eff.get("pct", 0.25))
        logs.append("🛡️ 铁壁意志！敌人下一次攻击 -25%！")


@register(TAKEN_EFFECTS, "steady_core")
def _t_steady_core(battle, player, ctx, logs):
    """磐石之心（D2）：受击 15% 免疫眩晕/减速且回 3% 生命"""
    if "steady_core" in battle._equip_affix_ids(player) and random.random() < _affix_chance("steady_core", 0.15):
        eff = _affix_effect("steady_core")
        for k in ("stun", "freeze", "spd_down"):
            battle.p_buffs.pop(k, None)
        heal = int(player.get("max_hp", 1) * float(eff.get("heal_pct", 0.03)))
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"⛰️ 磐石之心！免疫控制，回复 {heal} 点生命！")


@register(TAKEN_EFFECTS, "grim_ward")
def _t_grim_ward(battle, player, ctx, logs):
    """亡者守护（D2）：生命 >50% 时受击伤害 -7%"""
    if "grim_ward" in battle._equip_affix_ids(player):
        eff = _affix_effect("grim_ward")
        p_ratio = player.get("hp", 0) / max(1, player.get("max_hp", 1))
        if p_ratio > 0.50:
            dmg_before = ctx["out"]
            ctx["out"] = max(1, int(ctx["out"] * float(eff.get("dmg_taken_mult", 0.93))))
            logs.append(f"🕯️ 亡者守护！减伤 {dmg_before - ctx['out']} 点")


# ---- D2 回合开始型（TURN_START_EFFECTS）----

@register(TURN_START_EFFECTS, "life_spring")
def _ts_life_spring(battle, player, logs):
    """生命泉涌（D2）：每回合回 3% 最大生命"""
    if "life_spring" in battle._equip_affix_ids(player) and player.get("hp", 0) < player.get("max_hp", 1):
        heal = int(player.get("max_hp", player.get("hp", 1)) * float(_affix_effect("life_spring").get("pct", 0.03)))
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🌊 生命泉涌！回复 {heal} 点生命！")


# ---- D2 攻击命中型（HIT_EFFECTS，全部 on_hit trigger）----

@register(HIT_EFFECTS, "sun_blaze")
def _h_sun_blaze(battle, player, dmg, logs):
    """烈日迸发（D2）：攻击 15% 概率造成 80% 额外火伤"""
    if "sun_blaze" in battle._equip_affix_ids(player) and random.random() < _affix_chance("sun_blaze", 0.15):
        ed = max(1, int(dmg * 0.80))
        battle._damage_enemy(ed, logs)
        logs.append(f"☀️ 烈日迸发！追加 {ed} 点火属性伤害！")


@register(HIT_EFFECTS, "chain_overload")
def _h_chain_overload(battle, player, dmg, logs):
    """连锁过载（D2）：攻击 15% 概率追加 60% 魔攻雷击"""
    from ..engine import calc_damage
    if "chain_overload" in battle._equip_affix_ids(player) and random.random() < _affix_chance("chain_overload", 0.15):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("matk", 0) * 0.60), est.get("mdef", est.get("def", 0)))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"⚡ 连锁过载！追加 {cd} 点雷击伤害！")


@register(HIT_EFFECTS, "mortal_wound")
def _h_mortal_wound(battle, player, dmg, logs):
    """致伤重击（D2）：攻击 20% 概率使目标受疗效果 -50%（2 回合）"""
    if "mortal_wound" in battle._equip_affix_ids(player) and random.random() < _affix_chance("mortal_wound", 0.20):
        battle.e_buffs["_anti_heal_pct"] = 0.50
        battle.e_buffs["anti_heal_turns"] = max(battle.e_buffs.get("anti_heal_turns", 0), 2)
        logs.append("💢 致伤重击！目标受疗效果 -50%！")


@register(HIT_EFFECTS, "memory_tear")
def _h_memory_tear(battle, player, dmg, logs):
    """记忆撕裂（D2）：攻击 15% 概率使敌人攻击 -15%（2 回合）"""
    if "memory_tear" in battle._equip_affix_ids(player) and random.random() < _affix_chance("memory_tear", 0.15):
        battle.e_buffs["mon_atk_down"] = max(battle.e_buffs.get("mon_atk_down", 0), 2)
        battle.e_buffs["_weaken_val"] = 0.15
        logs.append("🧠 记忆撕裂！敌人攻击下降 15%！")


@register(HIT_EFFECTS, "arcane_echo")
def _h_arcane_echo(battle, player, dmg, logs):
    """秘法回响（D2）：攻击 15% 概率使下次技能伤害 +15%"""
    if "arcane_echo" in battle._equip_affix_ids(player) and random.random() < _affix_chance("arcane_echo", 0.15):
        battle.p_eff["arcane_echo_next"] = 1.15
        logs.append("🔮 秘法回响！下一次技能伤害 +15%！")


@register(HIT_EFFECTS, "siphon")
def _h_siphon(battle, player, dmg, logs):
    """汲力（D2）：攻击 20% 概率回复 5% 最大生命"""
    if "siphon" in battle._equip_affix_ids(player) and random.random() < _affix_chance("siphon", 0.20):
        heal = int(player.get("max_hp", 1) * 0.05)
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🌀 汲力！回复 {heal} 点生命！")


@register(HIT_EFFECTS, "summon_pact")
def _h_summon_pact(battle, player, dmg, logs):
    """召唤契约（D2）：攻击 20% 概率召唤援军（30% 攻击力）"""
    from ..engine import calc_damage
    if "summon_pact" in battle._equip_affix_ids(player) and random.random() < _affix_chance("summon_pact", 0.20):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        cd = calc_damage(int(pst.get("atk", 0) * 0.30), est.get("def", 0))
        if cd > 0:
            battle._damage_enemy(cd, logs)
            logs.append(f"📜 召唤契约！召唤援军造成 {cd} 点伤害！")


