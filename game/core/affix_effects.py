# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - affix_effects.py（v98.5：词条/套装效果注册表）

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
        battle.e_buffs["bleed"] = max(battle.e_buffs.get("bleed", 0), 3)
        logs.append("🩸 流血！敌人伤口裂开，将持续失血！")


@register(HIT_EFFECTS, "armor_break")
def _h_armor_break(battle, player, dmg, logs):
    """破甲：25% 降低目标防御 15%（2 回合）"""
    if "armor_break" in battle._equip_affix_ids(player) and random.random() < _affix_chance("armor_break", 0.25):
        battle.e_buffs["def_down"] = max(battle.e_buffs.get("def_down", 0), 2)
        battle.e_buffs["_armor_break_pct"] = 0.15
        logs.append("🛡️ 破甲！敌人防御下降 15%！")


@register(HIT_EFFECTS, "combo")
def _h_combo(battle, player, dmg, logs):
    """连击：15% 追加一次 50% 伤害"""
    if "combo" in battle._equip_affix_ids(player) and random.random() < _affix_chance("combo", 0.15):
        cd = int(dmg * 0.50)
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - cd)
        logs.append(f"⚡ 连击！追加 {cd} 点伤害！")


@register(HIT_EFFECTS, "lifesteal")
def _h_lifesteal(battle, player, dmg, logs):
    """吸血：伤害的 8% 转化为生命"""
    if "lifesteal" in battle._equip_affix_ids(player) and dmg > 0:
        heal = int(dmg * 0.08)
        player["hp"] = min(player.get("max_hp", player["hp"]), player.get("hp", 0) + heal)
        logs.append(f"🩸 吸血：回复 {heal} 点生命！")


@register(HIT_EFFECTS, "element_fire")
def _h_element_fire(battle, player, dmg, logs):
    """元素附加·火：5% 属性伤害"""
    if "element_fire" in battle._equip_affix_ids(player):
        ed = max(1, int(dmg * 0.05))
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - ed)
        logs.append(f"🔥 fire属性附加 {ed} 点伤害！")


@register(HIT_EFFECTS, "element_ice")
def _h_element_ice(battle, player, dmg, logs):
    """元素附加·冰：5% 属性伤害 + 减速"""
    if "element_ice" in battle._equip_affix_ids(player):
        ed = max(1, int(dmg * 0.05))
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - ed)
        logs.append(f"❄️ ice属性附加 {ed} 点伤害！")
        battle.e_buffs["spd_down"] = max(battle.e_buffs.get("spd_down", 0), 2)
        logs.append("❄️ 减速！")


@register(HIT_EFFECTS, "element_thunder")
def _h_element_thunder(battle, player, dmg, logs):
    """元素附加·雷：5% 属性伤害"""
    if "element_thunder" in battle._equip_affix_ids(player):
        ed = max(1, int(dmg * 0.05))
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - ed)
        logs.append(f"⚡ thunder属性附加 {ed} 点伤害！")


@register(HIT_EFFECTS, "pierce")
def _h_pierce(battle, player, dmg, logs):
    """贯穿：20% 无视防御追加伤害"""
    from ..engine import calc_damage
    if "pierce" in battle._equip_affix_ids(player) and random.random() < _affix_chance("pierce", 0.20):
        pst = battle._player_stats(player)
        pd = calc_damage(int(pst.get("atk", 0) * 0.6), 0)
        if pd > 0:
            battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - pd)
            logs.append(f"🏹 贯穿！无视防御 {pd} 点伤害！")


@register(HIT_EFFECTS, "charge")
def _h_charge(battle, player, dmg, logs):
    """蓄力：10% 造成 150% 伤害（追加 50%）"""
    if "charge" in battle._equip_affix_ids(player) and random.random() < _affix_chance("charge", 0.10):
        cd = int(dmg * 0.50)
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - cd)
        logs.append(f"💪 蓄力爆发！追加 {cd} 点伤害！")


@register(HIT_EFFECTS, "purify")
def _h_purify(battle, player, dmg, logs):
    """净化：15% 驱散敌人 1 层增益（审判之链专属 25% 驱散 2 层；if-elif 互斥保持原语义）"""
    ids = battle._equip_affix_ids(player)
    purge_n = 0
    if "judgment_chain" in ids and random.random() < _affix_chance("judgment_chain", 0.25):
        purge_n = 2
    elif "purify" in ids and random.random() < _affix_chance("purify", 0.15):
        purge_n = 1
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


@register(HIT_EFFECTS, "dragon_tongue")
def _h_dragon_tongue(battle, player, dmg, logs):
    """龙语印记：攻击叠印记（每层 +2% 伤害，上限 5）"""
    if "dragon_tongue" in battle._equip_affix_ids(player):
        battle.mech_stacks["dragon_mark"] = min(5, int(battle.mech_stacks.get("dragon_mark", 0) or 0) + 1)
        logs.append(f"🐉 龙语印记叠加！({battle.mech_stacks['dragon_mark']} 层，每层＋2% 伤害)")


# ================= 2. 受击词条（_affix_on_taken） =================
# 顺序结算：ctx["out"] 从原始 dmg 开始，逐个 handler 修改；thorns/ember_ward 读原始 dmg

TAKEN_EFFECTS = {}


@register(TAKEN_EFFECTS, "reduce")
def _t_reduce(battle, player, ctx, logs):
    """减伤（常驻：减伤词条 +3%、大地之心专属 +5%，叠加后统一应用）"""
    ids = battle._equip_affix_ids(player)
    reduce_pct = 0.0
    if "dmg_reduce" in ids:
        reduce_pct += 0.03
    if "earth_heart" in ids:
        reduce_pct += 0.05
    if reduce_pct:
        dmg_before = ctx["out"]
        ctx["out"] = max(1, int(ctx["out"] * (1 - reduce_pct)))
        logs.append(f"🛡️ 减伤 {dmg_before - ctx['out']} 点")


@register(TAKEN_EFFECTS, "block")
def _t_block(battle, player, ctx, logs):
    """格挡：15% 减伤 50%（基于结算中伤害）"""
    if "block" in battle._equip_affix_ids(player) and random.random() < _affix_chance("block", 0.15):
        blocked = int(ctx["out"] * 0.50)
        ctx["out"] = max(1, ctx["out"] - blocked)
        logs.append(f"🛡️ 格挡！减伤 {blocked} 点")


@register(TAKEN_EFFECTS, "tenacity")
def _t_tenacity(battle, player, ctx, logs):
    """坚韧：20% 免疫/清除自身负面（减速/降攻）"""
    if "tenacity" in battle._equip_affix_ids(player) and random.random() < _affix_chance("tenacity", 0.20):
        neg = [k for k in battle.p_buffs if k in ("spd_down", "atk_down", "def_down")]
        if neg:
            del battle.p_buffs[random.choice(neg)]
            logs.append("💪 坚韧！免疫了负面效果")


@register(TAKEN_EFFECTS, "counter")
def _t_counter(battle, player, ctx, logs):
    """反击：20% 反击 60% 伤害"""
    from ..engine import calc_damage
    if "counter" in battle._equip_affix_ids(player) and random.random() < _affix_chance("counter", 0.20) and battle.enemy.get("hp", 0) > 0:
        pst2 = battle._player_stats(player)
        est2 = battle._enemy_stats()
        cd = calc_damage(int(pst2.get("atk", 0) * 0.6), est2.get("def", 0))
        if cd > 0:
            battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - cd)
            logs.append(f"⚔️ 反击！对【{battle.enemy.get('name', '敌人')}】造成 {cd} 点伤害！")


@register(TAKEN_EFFECTS, "thorns")
def _t_thorns(battle, player, ctx, logs):
    """反伤：10% 反弹 30% 伤害（基于原始 dmg）"""
    if "thorns" in battle._equip_affix_ids(player) and random.random() < _affix_chance("thorns", 0.10) and battle.enemy.get("hp", 0) > 0:
        rd = int(ctx["dmg"] * 0.30)
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - rd)
        logs.append(f"🌵 反伤！反弹 {rd} 点伤害！")


@register(TAKEN_EFFECTS, "ember_ward")
def _t_ember_ward(battle, player, ctx, logs):
    """灰烬壁垒（灰烬守卫套专属）：20% 反弹 50% 伤害（基于原始 dmg）"""
    if "ember_ward" in battle._equip_affix_ids(player) and random.random() < _affix_chance("ember_ward", 0.20) and battle.enemy.get("hp", 0) > 0:
        rd = int(ctx["dmg"] * 0.50)
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - rd)
        logs.append(f"🔥 灰烬壁垒！反弹 {rd} 点伤害！")


@register(TAKEN_EFFECTS, "moro_crown")
def _t_moro_crown(battle, player, ctx, logs):
    """深渊腐蚀（摩罗之冠专属）：15% 敌人攻击 -10%（2 回合）"""
    if "moro_crown" in battle._equip_affix_ids(player) and random.random() < _affix_chance("moro_crown", 0.15):
        battle.e_buffs["mon_atk_down"] = max(battle.e_buffs.get("mon_atk_down", 0), 2)
        battle.e_buffs["_weaken_val"] = 0.10
        logs.append("👿 深渊腐蚀！敌人攻击下降 10%！")


# ================= 3. 回合开始词条（_affix_turn_start） =================

TURN_START_EFFECTS = {}


@register(TURN_START_EFFECTS, "regen")
def _ts_regen(battle, player, logs):
    """回春(1% 生命)/晨曦祝福(2% 生命)：叠加后统一回复"""
    ids = battle._equip_affix_ids(player)
    regen_pct = 0.0
    if "regen" in ids:
        regen_pct += 0.01
    if "dawn_crown" in ids:
        regen_pct += 0.02
    if regen_pct and player.get("hp", 0) < player.get("max_hp", 1):
        heal = int(player.get("max_hp", player.get("hp", 1)) * regen_pct)
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🌿 回春生效，回复 {heal} 点生命！")


@register(TURN_START_EFFECTS, "meditate")
def _ts_meditate(battle, player, logs):
    """冥想：1% 魔力回复"""
    if "meditate" in battle._equip_affix_ids(player) and player.get("mp", 0) < player.get("max_mp", 1):
        heal = int(player.get("max_mp", player.get("mp", 1)) * 0.01)
        player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + heal)
        logs.append(f"🧘 冥想生效，回复 {heal} 点魔力！")


# ================= 4. 套装 4 件攻击特效（_set_attack_proc） =================
# elif 分发：eff 互斥匹配（同 eff 只进一个分支）；按 eff key 查表

SET_PROC_EFFECTS = {}


@register(SET_PROC_EFFECTS, "frost")
def _sp_frost(battle, player, dmg, logs):
    """寒霜之力：30% 减速"""
    from ..battle import DEBUFF_TURNS  # 延迟引用，避免模块循环
    if random.random() < _set_chance("frost", 0.30):
        battle.e_buffs["spd_down"] = DEBUFF_TURNS
        logs.append("❄️ 寒霜之力！敌人速度下降！")


@register(SET_PROC_EFFECTS, "burn")
def _sp_burn(battle, player, dmg, logs):
    """烈焰之力：30% 灼烧"""
    from ..battle import DEBUFF_TURNS  # 延迟引用，避免模块循环
    if random.random() < _set_chance("burn", 0.30):
        battle.e_buffs["poison"] = DEBUFF_TURNS
        logs.append("🔥 烈焰之力！敌人被灼烧！")


@register(SET_PROC_EFFECTS, "thunder")
def _sp_thunder(battle, player, dmg, logs):
    """雷霆一击：25% 追加 60% 攻击伤害"""
    from ..engine import calc_damage
    if random.random() < _set_chance("thunder", 0.25):
        pst = battle._player_stats(player)
        est = battle._enemy_stats()
        tdmg = calc_damage(int(pst["atk"] * 0.6), est["def"])
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - tdmg)
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
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - bonus)
        logs.append(f"💀 灭世之力！处决追加 {bonus} 点伤害！")
