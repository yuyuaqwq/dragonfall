# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - battle_mech.py（v98.4：战斗机制效果注册表）

消灭 game/battle.py 里的 if-elif 硬编码：
1. Battle._apply_mech_effect() 的 32 个 mech 分支（攻击技能机制结算）
2. Battle._boss_mech() 的 10 个 boss 专属机制（enrage/summon/heal/shield/phase/stacks/
   reflect + v116.1 条件反制 phase_open/player_low/pv_broken）
3. Battle._enemy_turn() 的怪物增益效果（5 个）+ 控制机制（4 个）

扩展方式：
- 加机制：register 一个函数（~5 行），之后技能/怪物数据直接可用
- MECH_EFFECTS 签名：fn(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None) -> None
  （info=技能 dict，v113.1 增加：handler 可读技能自带 mech_chance 固定概率）
- BOSS_MECHS 签名：fn(battle, logs, e, r) -> None（e=enemy dict, r=round）
- MON_BUFF_EFFECTS 签名：fn(battle, logs, sname) -> None（怪物增益技效果）
- MON_CTRL_EFFECTS 签名：fn(battle, player, logs, mval) -> None（怪物控制技）

约定：
- 原 elif 链中带 `and mval` 守卫的分支 → handler 内 `if not mval: return`
- 未知 mech / m 安全降级为无操作（与旧链兜底一致）
"""
import random


def register(registry, key):
    """注册装饰器。"""
    def deco(fn):
        registry[key] = fn
        return fn
    return deco


def _mech_chance(info, default_chance):
    """v113.1：技能自带 mech_chance（固定触发概率 0~1）消费。
    返回 (使用了 mech_chance?, 最终触发概率)。
    - mech_chance 存在 → 用技能自带的固定概率（不依赖 skill_mech_val 成长，Lv.1 也可触发）
    - mech_chance 不存在 → 保持 handler 内部原有概率逻辑（default_chance）"""
    if info is not None and info.get("mech_chance") is not None:
        return True, float(info["mech_chance"])
    return False, default_chance


# ================= 1. 玩家攻击技能机制（_apply_mech_effect） =================

MECH_EFFECTS = {}


@register(MECH_EFFECTS, "rage")
def _m_rage(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """狂暴：叠层（每层＋12% 伤害）"""
    if not mval:
        return
    p_mech["rage"] = _stack(battle, "rage", p_mech, mval)
    logs.append(f"🔥 狂暴层数 {p_mech['rage']}(每层＋12% 伤害)")


@register(MECH_EFFECTS, "shield")
def _m_shield(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """圣盾：叠层（每层减伤）"""
    if not mval:
        return
    p_mech["shield"] = _stack(battle, "shield", p_mech, mval)
    logs.append(f"🛡️ 圣盾层数 {p_mech['shield']}(每层减伤)")


@register(MECH_EFFECTS, "shield_burst")
def _m_shield_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """圣盾爆发：消耗层数转伤害"""
    n = p_mech.get("shield", 0)
    bonus = int(total * n * 0.12)
    _burst_damage(battle, bonus, logs)
    logs.append(f"🛡️ 圣盾爆发！{n} 层额外 {bonus} 伤害")
    p_mech["shield"] = 0


@register(MECH_EFFECTS, "rage_burst")
def _m_rage_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """狂暴爆发：消耗层数加攻击 buff"""
    from ..engine import skill_buff_turns
    n = p_mech.get("rage", 0)
    if n:
        battle.p_buffs["atk_up_strong"] = skill_buff_turns(1)
        logs.append(f"🔥 狂战之魂！{n} 层狂暴 → 攻击大幅提升")
    p_mech["rage"] = 0


@register(MECH_EFFECTS, "burn")
def _m_burn(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """灼烧：叠层（每层每回合掉 3% 生命）"""
    if not mval:
        return
    p_mech["burn"] = _stack(battle, "burn", p_mech, mval)
    logs.append(f"🔥 灼烧层数 {p_mech['burn']}(每回合 {p_mech['burn'] * 3}% 生命)")


@register(MECH_EFFECTS, "burn_burst")
def _m_burn_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """灼烧引爆：每层立即 30% 魔攻"""
    n = p_mech.get("burn", 0)
    st2 = battle._player_stats(battle._last_player) if hasattr(battle, "_last_player") else None
    if st2 and n:
        d = int(st2["matk"] * 0.30 * n)
        _burst_damage(battle, d, logs)
        logs.append(f"🔥 灼烧引爆！{n} 层造成 {d} 点伤害")
    p_mech["burn"] = 0
    battle.e_buffs.pop("burn", None)


@register(MECH_EFFECTS, "freeze")
def _m_freeze(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """冻结：概率冻结 1 回合"""
    use_mc, chance = _mech_chance(info, min(0.75, 0.25 + mval * 0.15))
    if not mval and not use_mc:
        return
    if random.random() < chance:
        battle.e_buffs["freeze"] = 1
        logs.append("❄️ 敌人被冻结，跳过下回合！")


@register(MECH_EFFECTS, "spd_down")
def _m_spd_down(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """减速：敌方速度下降（battle._enemy_stats 按 SPD_DOWN_MULT 结算）"""
    use_mc, chance = _mech_chance(info, 1.0)  # 原逻辑：命中即减速（无概率）
    if not mval and not use_mc:
        return
    if use_mc and random.random() >= chance:
        return
    dur = max(int(mval or 0), 1)  # v113.1：mech_chance 技能不依赖 mval 成长，保证至少 1 回合
    battle.e_buffs["spd_down"] = max(battle.e_buffs.get("spd_down", 0), dur)
    logs.append(f"🧊 敌人被减速 {dur} 回合，速度下降！")


@register(MECH_EFFECTS, "stun")
def _m_stun(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """眩晕：概率眩晕 1 回合（v63 物理系控制）
    v113.1：技能自带 mech_chance（如时停领域 1.0）时用它覆写内部概率，Lv.1 也可触发。"""
    use_mc, chance = _mech_chance(info, min(0.60, 0.20 + mval * 0.15))
    if not mval and not use_mc:
        return
    if random.random() < chance:
        battle.e_buffs["stun"] = 1
        logs.append("🌀 敌人被眩晕，跳过下回合！")


@register(MECH_EFFECTS, "silence")
def _m_silence(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """沉默：稳定沉默 2 回合（v63 禁技能）"""
    if not mval:
        return
    battle.e_buffs["silence"] = 2
    logs.append("🤐 敌人被沉默，2 回合内无法使用技能！")


@register(MECH_EFFECTS, "cleanse")
def _m_cleanse(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """净化：清除敌方增益（v63 mon_atk_up/mon_def_up/狂暴/召唤）"""
    if not mval:
        return
    removed = []
    for k in ("mon_atk_up", "mon_atk_up_strong", "mon_def_up", "summon", "enraged"):
        if k in battle.e_buffs or (k == "enraged" and battle.enemy.get("enraged")):
            battle.e_buffs.pop(k, None)
            battle.enemy["enraged"] = False
            removed.append(k)
    if removed:
        logs.append("✨ 圣光净化！敌人的增益被驱散！")
    else:
        logs.append("✨ 圣光净化，敌人没有增益可驱散。")


@register(MECH_EFFECTS, "mark")
def _m_mark(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """标记：叠层（层数供 mark_burst 消费，同时挂 e_buffs 供 _apply_mark 增伤）"""
    from ..battle import DEBUFF_TURNS  # 延迟引用，避免模块循环
    if not mval:
        return
    p_mech["mark"] = _stack(battle, "mark", p_mech, mval)
    battle.e_buffs["mark"] = DEBUFF_TURNS
    logs.append(f"🎯 目标被标记！标记层数 {p_mech['mark']}")


@register(MECH_EFFECTS, "mark_burst")
def _m_mark_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """标记爆发：每层 +20%"""
    n = p_mech.get("mark", 0)
    bonus = int(total * n * 0.20)
    _burst_damage(battle, bonus, logs)
    logs.append(f"🎯 猎杀标记！{n} 层额外 {bonus} 伤害")
    p_mech["mark"] = 0


@register(MECH_EFFECTS, "wind")
def _m_wind(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """风印：叠层（连击次数 +1/层，已在伤害循环处理）"""
    if not mval:
        return
    p_mech["wind"] = _stack(battle, "wind", p_mech, mval)
    logs.append(f"💨 风印层数 {p_mech['wind']}(连击次数 +{p_mech['wind']})")


@register(MECH_EFFECTS, "wind_burst")
def _m_wind_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """风印爆发：层数转连击"""
    n = p_mech.get("wind", 0)
    logs.append(f"💨 风印爆发！{n} 层转化为连击")
    p_mech["wind"] = 0


@register(MECH_EFFECTS, "arcane")
def _m_arcane(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """奥术充能：叠层（供 player_mech_stacks 条件 + arcane_burst 消费）"""
    if not mval:
        return
    p_mech["arcane"] = _stack(battle, "arcane", p_mech, mval)
    logs.append(f"📖 奥术充能 {p_mech['arcane']} 层(共鸣爆发前置)")


@register(MECH_EFFECTS, "arcane_burst")
def _m_arcane_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """奥术充能爆发：消耗全部充能，每层 +15% 伤害（奥术洪流）"""
    n = p_mech.get("arcane", 0)
    if n:
        bonus = int(total * n * 0.15)
        _burst_damage(battle, bonus, logs)
        logs.append(f"📖 奥术共鸣！{n} 层充能额外 {bonus} 点伤害")
    p_mech["arcane"] = 0


@register(MECH_EFFECTS, "spellblade")
def _m_spellblade(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """魔剑士·魔能：叠层（每层 +8% 伤害，上限 5）"""
    if not mval:
        return
    p_mech["spellblade"] = _stack(battle, "spellblade", p_mech, mval)
    logs.append(f"⚔️ 魔能充能 {p_mech['spellblade']} 层(每层＋8% 伤害)")


@register(MECH_EFFECTS, "spellblade_surge")
def _m_spellblade_surge(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """魔力涌动：消耗 2 层魔能，下次攻击额外 80% 魔法伤害"""
    n = p_mech.get("spellblade", 0)
    if n >= 2:
        p_mech["spellblade"] = max(0, n - 2)
        battle.p_buffs["spellblade_surge"] = 1
        logs.append(f"✨ 魔力涌动！消耗 2 层魔能，下次攻击额外＋80% 魔法伤害")
    else:
        logs.append(f"⚔️ 魔能不足({n}/2)，魔力涌动无法施展！")


@register(MECH_EFFECTS, "spellblade_storm")
def _m_spellblade_storm(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """剑刃风暴：消耗 3 层魔能，全体 120% 物理 + 40% 魔法（对单体等效）"""
    n = p_mech.get("spellblade", 0)
    if n >= 3:
        p_mech["spellblade"] = max(0, n - 3)
        st2 = battle._player_stats(battle._last_player) if hasattr(battle, "_last_player") else None
        if st2:
            bonus = int(st2["matk"] * 0.40)
            _burst_damage(battle, bonus, logs)
            logs.append(f"🌪️ 剑刃风暴！消耗 3 层魔能，剑气横扫追加 {bonus} 点魔法伤害！")
    else:
        logs.append(f"⚔️ 魔能不足({n}/3)，剑刃风暴无法施展！")


@register(MECH_EFFECTS, "spellblade_burst")
def _m_spellblade_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """魔能爆发：消耗全部魔能（≥4），每层 +25% 伤害，最高 200%"""
    n = p_mech.get("spellblade", 0)
    if n >= 4:
        bonus = int(total * n * 0.25)
        _burst_damage(battle, bonus, logs)
        logs.append(f"💥 魔能爆发！{n} 层魔能倾泻，额外 {bonus} 点伤害！")
        p_mech["spellblade"] = 0
    else:
        logs.append(f"⚔️ 魔能不足({n}/4)，魔能爆发无法施展！")


@register(MECH_EFFECTS, "spellblade_meteor")
def _m_spellblade_meteor(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """星陨斩：消耗 5 层魔能，400% 混合伤害 + 20% 概率眩晕"""
    n = p_mech.get("spellblade", 0)
    if n >= 5:
        p_mech["spellblade"] = 0
        from .. import content as _C  # v101.5 概率常量延迟导入防环
        if random.random() < _C.STARFALL_STUN_CHANCE:
            battle.e_buffs["stun"] = 1
            logs.append("🌠 星陨斩的余威将敌人眩晕！")
    else:
        logs.append(f"⚔️ 魔能不足({n}/5)，星陨斩无法施展！")


@register(MECH_EFFECTS, "judge")
def _m_judge(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """审判：暴击时叠层（每层＋15%）"""
    if not mval or not is_crit:
        return
    p_mech["judge"] = _stack(battle, "judge", p_mech, mval)
    logs.append(f"⚖️ 审判层数 {p_mech['judge']}(每层＋15%)")


@register(MECH_EFFECTS, "judge_burst")
def _m_judge_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """审判爆发"""
    n = p_mech.get("judge", 0)
    bonus = int(total * n * 0.15)
    _burst_damage(battle, bonus, logs)
    logs.append(f"⚖️ 审判裁决！{n} 层额外 {bonus} 伤害")
    p_mech["judge"] = 0


@register(MECH_EFFECTS, "shadow")
def _m_shadow(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """影袭：叠层（每层＋12%）"""
    if not mval:
        return
    p_mech["shadow"] = _stack(battle, "shadow", p_mech, mval)
    logs.append(f"🌑 影袭层数 {p_mech['shadow']}(每层＋12%)")


@register(MECH_EFFECTS, "shadow_burst")
def _m_shadow_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """影袭爆发"""
    n = p_mech.get("shadow", 0)
    bonus = int(total * n * 0.18)
    _burst_damage(battle, bonus, logs)
    logs.append(f"🌑 致命突袭！{n} 层额外 {bonus} 伤害")
    p_mech["shadow"] = 0


@register(MECH_EFFECTS, "poison")
def _m_poison(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """毒层：叠层（每层每回合 5% 生命，v110 与 POISON_PCT 对齐）
    v113.1：技能自带 mech_chance（如轻快拨弦 0.1 / 淬毒之刃 0.5）时作为施毒概率。"""
    use_mc, chance = _mech_chance(info, 1.0)  # 原逻辑：命中即叠毒
    if not mval and not use_mc:
        return
    if use_mc and random.random() >= chance:
        return
    p_mech["poison"] = _stack(battle, "poison", p_mech, mval)
    logs.append(f"☠️ 毒层 {p_mech['poison']}(每回合 {p_mech['poison'] * 5}% 生命)")


@register(MECH_EFFECTS, "poison_burst")
def _m_poison_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v107 毒爆（丛林猎手）：poison 层数≥3 可引爆——每层 15% 魔攻魔法伤害（毒=魔法段，
    吃 mdef/魔免/元素抗？毒非元素不吃元素抗；v107 伤害类型 dmg_type="magi"），清层。"""
    n = p_mech.get("poison", 0)
    if n < 3:
        logs.append(f"☠️ 毒层 {n}（≥3 层可引爆）")
        return
    st2 = battle._player_stats(battle._last_player) if hasattr(battle, "_last_player") else None
    if st2 and n:
        from ..engine import calc_damage as _calc  # v107 局部导入防循环依赖
        est = battle._enemy_stats()
        d = _calc(int(st2["matk"] * 0.15 * n), est.get("mdef", 0), dmg_type="magi")
        _burst_damage(battle, d, logs)
        logs.append(f"☠️ 毒爆！{n} 层引爆造成 {d} 点魔法伤害")
    p_mech["poison"] = 0
    battle.e_buffs.pop("poison", None)


@register(MECH_EFFECTS, "chi")
def _m_chi(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """气力：攒层（每点＋12%）"""
    if not mval:
        return
    p_mech["chi"] = _stack(battle, "chi", p_mech, mval)
    logs.append(f"🌀 气力 {p_mech['chi']}(每点＋12%)")


@register(MECH_EFFECTS, "chi_burst")
def _m_chi_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """气力爆发"""
    n = p_mech.get("chi", 0)
    bonus = int(total * n * 0.15)
    _burst_damage(battle, bonus, logs)
    logs.append(f"🌀 拳法奥义！{n} 点气力额外 {bonus} 伤害")
    p_mech["chi"] = 0


@register(MECH_EFFECTS, "iron")
def _m_iron(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """金身：叠层（减伤，在 _damage_player 生效）"""
    if not mval:
        return
    p_mech["iron"] = _stack(battle, "iron", p_mech, mval)
    logs.append(f"🪷 金身层数 {p_mech['iron']}(每层减伤 4%)")


@register(MECH_EFFECTS, "iron_burst")
def _m_iron_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """金身爆发：层数转伤害"""
    n = p_mech.get("iron", 0)
    bonus = int(total * n * 0.12)
    _burst_damage(battle, bonus, logs)
    logs.append(f"🪷 不坏金身！{n} 层额外 {bonus} 伤害")
    p_mech["iron"] = 0


@register(MECH_EFFECTS, "bless_shield")
def _m_bless_shield(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """神恩护盾：层数转护盾"""
    n = p_mech.get("bless", 0)
    st2 = battle._player_stats(battle._last_player) if hasattr(battle, "_last_player") else None
    if st2 and n:
        shield = int(st2["matk"] * 0.08 * n)
        # v104 M02 P2-3：护盾已 buff 化（v101.28d p_shields），旧 battle.shield 直写必 AttributeError
        battle._add_shield("bless", shield, 2)
        logs.append(f"✨ 神恩护盾！{n} 层转化为 {shield} 点护盾")
    p_mech["bless"] = 0


# ================= 2. Boss 专属机制（_boss_mech） =================

BOSS_MECHS = {}


@register(BOSS_MECHS, "enrage")
def _b_enrage(battle, logs, e, r):
    """狂暴：血量 <30% 时攻击大幅提升（每场一次）"""
    ratio = e.get("hp", 1) / max(1, e.get("max_hp", 1))
    if ratio < 0.30 and not e.get("enraged"):
        e["enraged"] = True
        logs.append(f"😡【{e['name']}】陷入狂暴！攻击大幅提升！")


@register(BOSS_MECHS, "summon")
def _b_summon(battle, logs, e, r):
    """召唤：每 3 回合召唤援军实体（v101.28l #438：真召唤，援军挡刀+出手）"""
    if r > 1 and r % 3 == 0 and e.get("summoned_round") != r:
        e["summoned_round"] = r
        n = 2 if r % 6 == 0 else 1  # 每 6 回合召唤 2 只
        mins = battle._summon_minions(n)
        names = "、".join(f"【{m['name']}】" for m in mins)
        battle.e_buffs["mon_atk_up"] = max(battle.e_buffs.get("mon_atk_up", 0), 2)
        logs.append(f"👥【{e['name']}】召唤了 {names}！它们挡在身前，攻击也提升了！")


@register(BOSS_MECHS, "heal")
def _b_heal(battle, logs, e, r):
    """回血：每 4 回合恢复 8% 生命"""
    if r > 1 and r % 4 == 0 and e.get("healed_round") != r:
        e["healed_round"] = r
        heal = int(e.get("max_hp", 1) * 0.08)
        e["hp"] = min(e.get("max_hp", 1), e.get("hp", 0) + heal)
        logs.append(f"💚【{e['name']}】汲取力量，恢复了 {heal} 点生命！")


@register(BOSS_MECHS, "shield")
def _b_shield(battle, logs, e, r):
    """护盾：首回合出现 20% 护盾（受伤减半）"""
    if r == 1 and not e.get("boss_shield"):
        e["boss_shield"] = int(e.get("max_hp", 1) * 0.20)
        logs.append(f"🛡️【{e['name']}】周身浮现一层护盾(受伤减半)！")


def _phase_threshold(phases, pc):
    """阶段进下一阶段阈值（ratio 0-1）：有 phases 配置且 phases[pc].min 存在则用 min/100
    （设计 60%/30%），否则回退 0.5**(pc+1)（50%/25%）。
    v118+ 审计：用户拍板，实现读 phases[].min，缺省保留 0.5^n。"""
    if pc < len(phases):
        mn = phases[pc].get("min")
        if mn is not None:
            return mn / 100.0
    return 0.5 ** (pc + 1)


@register(BOSS_MECHS, "phase")
def _b_phase(battle, logs, e, r):
    """阶段：每掉一半血进入下一阶段（最多 3 次）
    v116.1 剧本化（BOSS 战编排 §一）：e 的 phases=[{"min":60,"add_skills":[..],"script":{..}},..]
    - 阶段演出回合：进入新阶段该回合不行动（battle._phase_skip_act=True）
    - 换招表：进入第 N 阶段追加 phases[N-1].add_skills（幂等）
    - 阈值预告：阶段 2/3 起，血量接近下一阈值(+3%)提前输出预警
    - 阈值：有 phases[].min 用 min%（设计 60%/30%），缺省 0.5^n（50%/25%）
    无 phases 配置 → 完全维持旧行为（纯增伤 atk/matk +20%/阶段）。"""
    pc = e.get("phase_count", 0)
    cfg = battle._boss_cfg(e) if hasattr(battle, "_boss_cfg") else {}
    phases = cfg.get("phases") or []
    target = _phase_threshold(phases, pc)
    ratio = e.get("hp", 1) / max(1, e.get("max_hp", 1))
    # ---- 阈值预告（阶段 2/3 起）：接近下一阈值 +3% 内提前 2 回合口径输出 ----
    if pc > 0:
        nxt = _phase_threshold(phases, pc)  # 下一阶段阈值
        within = 0.03
        if nxt <= ratio <= nxt + within:
            warned = e.get("_phase_warned") or []
            if (pc + 1) not in warned:
                warned.append(pc + 1)
                e["_phase_warned"] = warned
                logs.append(f"⚠️ 【{e['name']}】的气息开始紊乱……似乎要进入更凶猛的阶段了！")
    if ratio < target and pc < 3:
        npc = pc + 1
        e["phase_count"] = npc
        if not isinstance(e.get("_phase_warned"), list):
            e["_phase_warned"] = []
        e["_phase_warned"].append(npc)
        # ---- 换招表：第 npc 阶段对应 phases[npc-1]，追加阶段专属技能（幂等）----
        if phases and npc - 1 < len(phases):
            for s in (phases[npc - 1].get("add_skills") or []):
                if s and s not in e["skills"]:
                    e["skills"] = list(e["skills"]) + [s]
        # ---- 旧行为保留（阶段攻击+20%）----
        logs.append(f"🔥【{e['name']}】进入第 {npc + 1} 阶段！力量再度攀升！")
        # ---- 剧本演出文案（phases 配置了 script 时追加）----
        script = {}
        if phases and npc - 1 < len(phases):
            script = (phases[npc - 1].get("script") or {})
        sname = script.get("name")
        if sname:
            icon = script.get("icon", "🔥")
            logs.append(f"{icon}【{e['name']}】{sname}！")
        else:
            logs.append(f"🔥【{e['name']}】的鳞片泛起暗红……【狂暴】！")
        # ---- 阶段演出回合：本回合不行动（给玩家呼吸点）----
        battle._phase_skip_act = True


@register(BOSS_MECHS, "stacks")
def _b_stacks(battle, logs, e, r):
    """叠层：每 2 回合攻击叠层 +1（上限 5）"""
    if r > 0 and r % 2 == 0:
        cur = e.get("mech_stacks_n", 0)
        if cur < 5:
            e["mech_stacks_n"] = cur + 1
            logs.append(f"⚔️【{e['name']}】气势攀升，攻击叠层＋1({cur + 1}/5)")


# ================= 2.1 条件触发反制（v116.1 怪物行动 AI §二 条件行动子集） =================
# 三类触发器：开场技 / 玩家低血追击 / 玩家大招后反扑（破防反扑无 PV 体系 → 改为大招反扑）。
# 数据驱动：配置从 battle._boss_cfg(e) 读取（monster_mods/instances 的 boss 条目加
# "opening"/"triggers"/"phases" 字段，battle.py 按 enemy id 解析）。无配置则用内置兜底默认值。
# 触发频率用附着在 e 上的计数器字段（_open_played/_low_hp_cd/_pv_broken_cd/_phase_warned）
# 约束防刷屏（once / 每 N 回合）。战斗实例级瞬态标记 battle._phase_skip_act 用于阶段演出回合。


@register(BOSS_MECHS, "phase_open")
def _b_opening(battle, logs, e, r):
    """开场技：战斗第一回合必放一次（once）。默认『咆哮』：演出行 + mon_atk_up 增益 2 回合。
    数据：e 的 opening 可配技能名 / {"name","effect","power"}。"""
    if r != 1 or e.get("_open_played"):
        return
    e["_open_played"] = True
    cfg = battle._boss_cfg(e) if hasattr(battle, "_boss_cfg") else {}
    op = cfg.get("opening") or {"name": "咆哮"}
    if isinstance(op, str):
        op = {"name": op}
    name = op.get("name", "咆哮")
    logs.append(f"🌪️【{e['name']}】发出震天【{name}】！气势瞬间拉满！")
    effect = (op.get("effect") or "atk_up").lower()
    power = float(op.get("power", 2.0) or 2.0)
    from ..battle import BUFF_TURNS  # 延迟引用，避免模块循环
    if effect == "atk_up":
        battle.e_buffs["mon_atk_up"] = max(battle.e_buffs.get("mon_atk_up", 0), int(power))
        logs.append(f"⚡【{e['name']}】的{name}让攻击力提升了！")
    elif effect == "atk_up_strong":
        battle.e_buffs["mon_atk_up_strong"] = max(
            battle.e_buffs.get("mon_atk_up_strong", 0), int(power))
        logs.append(f"⚡【{e['name']}】的{name}让攻击力大幅提升了！")
    elif effect == "mon_atk_down":  # 低吼削弱玩家（可选）
        battle.p_buffs["atk_down"] = max(battle.p_buffs.get("atk_down", 0), int(power))
        logs.append(f"🫁【{e['name']}】的{name}压制了你，攻击下降！")
    # 其他 effect 安全忽略（无副作用），保持"必放一次演出"性质


@register(BOSS_MECHS, "player_low")
def _b_player_low(battle, logs, e, r):
    """玩家低血追击：玩家 HP<30% 时 Boss 输出杀意文案并本回合攻击加成（25%）。
    触发频率：默认 once；或配置 triggers.player_low.cooldown=N 后每 N 回合一次。"""
    p = getattr(battle, "player", None) or {}
    mh = p.get("max_hp") or 0
    if mh <= 0:
        return
    cd = e.get("_low_hp_cd", 0)
    if cd > 0:
        e["_low_hp_cd"] = cd - 1
        return
    ratio = p.get("hp", mh) / mh
    cfg = battle._boss_cfg(e) if hasattr(battle, "_boss_cfg") else {}
    thresh = float((cfg.get("triggers") or {}).get("player_low", {}).get("hp", 0.30) or 0.30)
    if ratio >= thresh:
        return
    if e.get("_low_hp_fired"):
        # 若配了 cooldown 才允许重复触发
        cooldown = int((cfg.get("triggers") or {}).get("player_low", {}).get("cooldown", 0) or 0)
        if cooldown <= 0:
            return
        e["_low_hp_cd"] = cooldown
        logs.append(f"☠️ 【{e['name']}】盯上了重伤的你，狞笑着扑来！(追击)")
        e["_low_hp_active"] = True
        return
    e["_low_hp_fired"] = True
    cooldown = int((cfg.get("triggers") or {}).get("player_low", {}).get("cooldown", 0) or 0)
    if cooldown > 0:
        e["_low_hp_cd"] = cooldown
    logs.append(f"☠️ 【{e['name']}】盯上了重伤的你……本回合攻击大幅提升！")
    e["_low_hp_active"] = True


@register(BOSS_MECHS, "pv_broken")
def _b_pv_broken(battle, logs, e, r):
    """玩家大招后反扑（原"破防反扑"，游戏无 PV/防护体系 → 改为玩家刚放技能后 Boss 反击）：
    玩家上一回合使用技能（battle._player_recent_skill）时触发一次反击演出 + 本回合攻击加成
    （30% / 额外一次攻击）。频率：once + cooldown 可选。"""
    if not getattr(battle, "_player_recent_skill", False):
        return
    if e.get("_pv_broken_fired"):
        cd = e.get("_pv_broken_cd", 0)
        if cd <= 0:
            return
        e["_pv_broken_cd"] = cd - 1
        return
    e["_pv_broken_fired"] = True
    cfg = battle._boss_cfg(e) if hasattr(battle, "_boss_cfg") else {}
    cooldown = int((cfg.get("triggers") or {}).get("pv_broken", {}).get("cooldown", 0) or 0)
    if cooldown > 0:
        e["_pv_broken_cd"] = cooldown
    logs.append(f"💥 防护崩溃！【{e['name']}】愤怒反扑！(本回合追加攻击)")
    e["_pv_broken_active"] = True


# ================= 3. 怪物增益效果（_enemy_turn 增益技能） =================

MON_BUFF_EFFECTS = {}


@register(MON_BUFF_EFFECTS, "atk_up")
def _mb_atk_up(battle, logs, sname):
    """攻击提升"""
    from ..battle import BUFF_TURNS  # 延迟引用，避免模块循环
    battle.e_buffs["mon_atk_up"] = BUFF_TURNS
    logs.append(f"【{battle.enemy['name']}】使用了【{sname}】，攻击力提升了！")


@register(MON_BUFF_EFFECTS, "atk_up_strong")
def _mb_atk_up_strong(battle, logs, sname):
    """攻击大幅提升"""
    from ..battle import BUFF_TURNS  # 延迟引用，避免模块循环
    battle.e_buffs["mon_atk_up_strong"] = BUFF_TURNS
    logs.append(f"【{battle.enemy['name']}】使用了【{sname}】，攻击力大幅提升了！")


@register(MON_BUFF_EFFECTS, "def_up")
def _mb_def_up(battle, logs, sname):
    """防御提升"""
    from ..battle import BUFF_TURNS  # 延迟引用，避免模块循环
    battle.e_buffs["mon_def_up"] = BUFF_TURNS
    logs.append(f"【{battle.enemy['name']}】使用了【{sname}】，防御提升了！")


@register(MON_BUFF_EFFECTS, "heal_self")
def _mb_heal_self(battle, logs, sname):
    """自我恢复 15% 生命"""
    heal = int(battle.enemy.get("max_hp", 1) * 0.15)
    battle.enemy["hp"] = min(battle.enemy.get("max_hp", 1), battle.enemy.get("hp", 0) + heal)
    logs.append(f"【{battle.enemy['name']}】使用了【{sname}】，恢复了 {heal} 点生命！")


@register(MON_BUFF_EFFECTS, "summon")
def _mb_summon(battle, logs, sname):
    """召唤援军（v101.28l #438：真召唤，生成援军实体）"""
    mins = battle._summon_minions(1)
    m = mins[0] if mins else {}
    logs.append(f"【{battle.enemy['name']}】使用了【{sname}】，召唤了援军【{m.get('name', '爪牙')}】！")


# ================= 4. 怪物控制机制（_enemy_turn 技能 mech） =================

MON_CTRL_EFFECTS = {}


@register(MON_CTRL_EFFECTS, "freeze")
def _mc_freeze(battle, player, logs, mval):
    """冻结玩家（概率，1 回合）"""
    if battle.p_buffs.get("cc_immune"):
        logs.append("🗿 不动如山！免疫了冻结！")
        return
    chance = min(0.75, 0.25 + mval * 0.15)
    if random.random() < chance:
        battle.p_buffs["freeze"] = 1
        logs.append("❄️ 你被冻结，下回合无法行动！")


@register(MON_CTRL_EFFECTS, "stun")
def _mc_stun(battle, player, logs, mval):
    """眩晕玩家（概率，1 回合）"""
    if battle.p_buffs.get("cc_immune"):
        logs.append("🗿 不动如山！免疫了眩晕！")
        return
    chance = min(0.60, 0.20 + mval * 0.15)
    if random.random() < chance:
        battle.p_buffs["stun"] = 1
        logs.append("🌀 你被眩晕，下回合无法行动！")


@register(MON_CTRL_EFFECTS, "silence")
def _mc_silence(battle, player, logs, mval):
    """沉默玩家（稳定，2 回合）"""
    battle.p_buffs["silence"] = 2
    logs.append("🤐 你被沉默，2 回合内无法使用技能！")


@register(MON_CTRL_EFFECTS, "slow")
def _mc_slow(battle, player, logs, mval):
    """减速玩家（霜狼套 5 件免疫；v101.28f 不动药剂免疫）"""
    if battle.p_buffs.get("cc_immune"):
        logs.append("🗿 不动如山！免疫了减速！")
    elif "霜狼" in "|".join(battle._set_bonus_5(player)):
        logs.append("🧊 抗寒生效！霜狼套免疫了减速！")
    else:
        battle.p_buffs["spd_down"] = max(battle.p_buffs.get("spd_down", 0), 2)
        logs.append("🧊 你被减速，2 回合内速度下降！")


# ================= 内部工具（延迟绑定 Battle 常量） =================

def _stack(battle, mech, p_mech, mval):
    """叠层（封顶逻辑 v59 在 engine.mech_stack_gain）"""
    from ..engine import mech_stack_gain
    return mech_stack_gain(mech, p_mech, mval)


def _burst_damage(battle, bonus, logs):
    """v104 M02 P2：burst 附加伤害统一走结算主路径（Boss 护盾减半 + 援军挡刀）。

    此前 burst 类机制直接 battle.enemy["hp"] -= bonus，绕过 _boss_dmg_filter
    （护盾受伤减半/反伤）与 _damage_enemy（e_minions 援军挡刀）→ 打盾 Boss 不减半、
    有援军不挡刀。修复：参照普通伤害路径（battle.py _skill_use 的
    `_boss_dmg_filter → _damage_enemy`）逐段结算，不双杀（total 主伤害已结算，本函数只结算附加段）。"""
    if bonus <= 0:
        return
    player = getattr(battle, "_last_player", None)
    if player is not None:
        bonus = battle._boss_dmg_filter(bonus, player, logs)
    battle._damage_enemy(bonus, logs)
