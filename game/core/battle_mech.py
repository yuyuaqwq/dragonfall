# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - battle_mech.py（v98.4：战斗机制效果注册表）

消灭 game/battle.py 里的 if-elif 硬编码：
1. Battle._apply_mech_effect() 的 32 个 mech 分支（攻击技能机制结算）
2. Battle._boss_mech() 的 7 个 boss 专属机制
3. Battle._enemy_turn() 的怪物增益效果（5 个）+ 控制机制（4 个）

扩展方式：
- 加机制：register 一个函数（~5 行），之后技能/怪物数据直接可用
- MECH_EFFECTS 签名：fn(battle, mval, p_mech, total, logs, skill_name, is_crit) -> None
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


# ================= 1. 玩家攻击技能机制（_apply_mech_effect） =================

MECH_EFFECTS = {}


@register(MECH_EFFECTS, "rage")
def _m_rage(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """狂暴：叠层（每层＋12% 伤害）"""
    if not mval:
        return
    p_mech["rage"] = _stack(battle, "rage", p_mech, mval)
    logs.append(f"🔥 狂暴层数 {p_mech['rage']}(每层＋12% 伤害)")


@register(MECH_EFFECTS, "shield")
def _m_shield(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """圣盾：叠层（每层减伤）"""
    if not mval:
        return
    p_mech["shield"] = _stack(battle, "shield", p_mech, mval)
    logs.append(f"🛡️ 圣盾层数 {p_mech['shield']}(每层减伤)")


@register(MECH_EFFECTS, "shield_burst")
def _m_shield_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """圣盾爆发：消耗层数转伤害"""
    n = p_mech.get("shield", 0)
    bonus = int(total * n * 0.12)
    battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - bonus)
    logs.append(f"🛡️ 圣盾爆发！{n} 层额外 {bonus} 伤害")
    p_mech["shield"] = 0


@register(MECH_EFFECTS, "rage_burst")
def _m_rage_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """狂暴爆发：消耗层数加攻击 buff"""
    from ..engine import skill_buff_turns
    n = p_mech.get("rage", 0)
    if n:
        battle.p_buffs["atk_up_strong"] = skill_buff_turns(1)
        logs.append(f"🔥 狂战之魂！{n} 层狂暴 → 攻击大幅提升")
    p_mech["rage"] = 0


@register(MECH_EFFECTS, "burn")
def _m_burn(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """灼烧：叠层（每层每回合掉 3% 生命）"""
    if not mval:
        return
    p_mech["burn"] = _stack(battle, "burn", p_mech, mval)
    logs.append(f"🔥 灼烧层数 {p_mech['burn']}(每回合 {p_mech['burn'] * 3}% 生命)")


@register(MECH_EFFECTS, "burn_burst")
def _m_burn_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """灼烧引爆：每层立即 30% 魔攻"""
    n = p_mech.get("burn", 0)
    st2 = battle._player_stats(battle._last_player) if hasattr(battle, "_last_player") else None
    if st2 and n:
        d = int(st2["matk"] * 0.30 * n)
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - d)
        logs.append(f"🔥 灼烧引爆！{n} 层造成 {d} 点伤害")
    p_mech["burn"] = 0
    battle.e_buffs.pop("burn", None)


@register(MECH_EFFECTS, "freeze")
def _m_freeze(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """冻结：概率冻结 1 回合"""
    if not mval:
        return
    chance = min(0.75, 0.25 + mval * 0.15)
    if random.random() < chance:
        battle.e_buffs["freeze"] = 1
        logs.append("❄️ 敌人被冻结，跳过下回合！")


@register(MECH_EFFECTS, "stun")
def _m_stun(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """眩晕：概率眩晕 1 回合（v63 物理系控制）"""
    if not mval:
        return
    chance = min(0.60, 0.20 + mval * 0.15)
    if random.random() < chance:
        battle.e_buffs["stun"] = 1
        logs.append("🌀 敌人被眩晕，跳过下回合！")


@register(MECH_EFFECTS, "silence")
def _m_silence(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """沉默：稳定沉默 2 回合（v63 禁技能）"""
    if not mval:
        return
    battle.e_buffs["silence"] = 2
    logs.append("🤐 敌人被沉默，2 回合内无法使用技能！")


@register(MECH_EFFECTS, "cleanse")
def _m_cleanse(battle, mval, p_mech, total, logs, skill_name, is_crit):
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
def _m_mark(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """标记：叠层（层数供 mark_burst 消费，同时挂 e_buffs 供 _apply_mark 增伤）"""
    from ..battle import DEBUFF_TURNS  # 延迟引用，避免模块循环
    if not mval:
        return
    p_mech["mark"] = _stack(battle, "mark", p_mech, mval)
    battle.e_buffs["mark"] = DEBUFF_TURNS
    logs.append(f"🎯 目标被标记！标记层数 {p_mech['mark']}")


@register(MECH_EFFECTS, "mark_burst")
def _m_mark_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """标记爆发：每层 +20%"""
    n = p_mech.get("mark", 0)
    bonus = int(total * n * 0.20)
    battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - bonus)
    logs.append(f"🎯 猎杀标记！{n} 层额外 {bonus} 伤害")
    p_mech["mark"] = 0


@register(MECH_EFFECTS, "wind")
def _m_wind(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """风印：叠层（连击次数 +1/层，已在伤害循环处理）"""
    if not mval:
        return
    p_mech["wind"] = _stack(battle, "wind", p_mech, mval)
    logs.append(f"💨 风印层数 {p_mech['wind']}(连击次数 +{p_mech['wind']})")


@register(MECH_EFFECTS, "wind_burst")
def _m_wind_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """风印爆发：层数转连击"""
    n = p_mech.get("wind", 0)
    logs.append(f"💨 风印爆发！{n} 层转化为连击")
    p_mech["wind"] = 0


@register(MECH_EFFECTS, "arcane")
def _m_arcane(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """奥术充能：叠层（供 player_mech_stacks 条件 + arcane_burst 消费）"""
    if not mval:
        return
    p_mech["arcane"] = _stack(battle, "arcane", p_mech, mval)
    logs.append(f"📖 奥术充能 {p_mech['arcane']} 层(共鸣爆发前置)")


@register(MECH_EFFECTS, "arcane_burst")
def _m_arcane_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """奥术充能爆发：消耗全部充能，每层 +15% 伤害（奥术洪流）"""
    n = p_mech.get("arcane", 0)
    if n:
        bonus = int(total * n * 0.15)
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - bonus)
        logs.append(f"📖 奥术共鸣！{n} 层充能额外 {bonus} 点伤害")
    p_mech["arcane"] = 0


@register(MECH_EFFECTS, "spellblade")
def _m_spellblade(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """魔剑士·魔能：叠层（每层 +8% 伤害，上限 5）"""
    if not mval:
        return
    p_mech["spellblade"] = _stack(battle, "spellblade", p_mech, mval)
    logs.append(f"⚔️ 魔能充能 {p_mech['spellblade']} 层(每层＋8% 伤害)")


@register(MECH_EFFECTS, "spellblade_surge")
def _m_spellblade_surge(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """魔力涌动：消耗 2 层魔能，下次攻击额外 80% 魔法伤害"""
    n = p_mech.get("spellblade", 0)
    if n >= 2:
        p_mech["spellblade"] = max(0, n - 2)
        battle.p_buffs["spellblade_surge"] = 1
        logs.append(f"✨ 魔力涌动！消耗 2 层魔能，下次攻击额外＋80% 魔法伤害")
    else:
        logs.append(f"⚔️ 魔能不足({n}/2)，魔力涌动无法施展！")


@register(MECH_EFFECTS, "spellblade_storm")
def _m_spellblade_storm(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """剑刃风暴：消耗 3 层魔能，全体 120% 物理 + 40% 魔法（对单体等效）"""
    n = p_mech.get("spellblade", 0)
    if n >= 3:
        p_mech["spellblade"] = max(0, n - 3)
        st2 = battle._player_stats(battle._last_player) if hasattr(battle, "_last_player") else None
        if st2:
            bonus = int(st2["matk"] * 0.40)
            battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - bonus)
            logs.append(f"🌪️ 剑刃风暴！消耗 3 层魔能，剑气横扫追加 {bonus} 点魔法伤害！")
    else:
        logs.append(f"⚔️ 魔能不足({n}/3)，剑刃风暴无法施展！")


@register(MECH_EFFECTS, "spellblade_burst")
def _m_spellblade_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """魔能爆发：消耗全部魔能（≥4），每层 +25% 伤害，最高 200%"""
    n = p_mech.get("spellblade", 0)
    if n >= 4:
        bonus = int(total * n * 0.25)
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - bonus)
        logs.append(f"💥 魔能爆发！{n} 层魔能倾泻，额外 {bonus} 点伤害！")
        p_mech["spellblade"] = 0
    else:
        logs.append(f"⚔️ 魔能不足({n}/4)，魔能爆发无法施展！")


@register(MECH_EFFECTS, "spellblade_meteor")
def _m_spellblade_meteor(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """星陨斩：消耗 5 层魔能，400% 混合伤害 + 20% 概率眩晕"""
    n = p_mech.get("spellblade", 0)
    if n >= 5:
        p_mech["spellblade"] = 0
        if random.random() < 0.20:
            battle.e_buffs["stun"] = 1
            logs.append("🌠 星陨斩的余威将敌人眩晕！")
    else:
        logs.append(f"⚔️ 魔能不足({n}/5)，星陨斩无法施展！")


@register(MECH_EFFECTS, "judge")
def _m_judge(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """审判：暴击时叠层（每层＋15%）"""
    if not mval or not is_crit:
        return
    p_mech["judge"] = _stack(battle, "judge", p_mech, mval)
    logs.append(f"⚖️ 审判层数 {p_mech['judge']}(每层＋15%)")


@register(MECH_EFFECTS, "judge_burst")
def _m_judge_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """审判爆发"""
    n = p_mech.get("judge", 0)
    bonus = int(total * n * 0.15)
    battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - bonus)
    logs.append(f"⚖️ 审判裁决！{n} 层额外 {bonus} 伤害")
    p_mech["judge"] = 0


@register(MECH_EFFECTS, "shadow")
def _m_shadow(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """影袭：叠层（每层＋12%）"""
    if not mval:
        return
    p_mech["shadow"] = _stack(battle, "shadow", p_mech, mval)
    logs.append(f"🌑 影袭层数 {p_mech['shadow']}(每层＋12%)")


@register(MECH_EFFECTS, "shadow_burst")
def _m_shadow_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """影袭爆发"""
    n = p_mech.get("shadow", 0)
    bonus = int(total * n * 0.18)
    battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - bonus)
    logs.append(f"🌑 致命突袭！{n} 层额外 {bonus} 伤害")
    p_mech["shadow"] = 0


@register(MECH_EFFECTS, "poison")
def _m_poison(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """毒层：叠层（每层每回合 3% 生命）"""
    if not mval:
        return
    p_mech["poison"] = _stack(battle, "poison", p_mech, mval)
    logs.append(f"☠️ 毒层 {p_mech['poison']}(每回合 {p_mech['poison'] * 3}% 生命)")


@register(MECH_EFFECTS, "poison_burst")
def _m_poison_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """毒爆：每层立即 15% 攻击"""
    n = p_mech.get("poison", 0)
    bonus = int(total * n * 0.15)
    battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - bonus)
    logs.append(f"☠️ 毒爆！{n} 层额外 {bonus} 伤害")
    p_mech["poison"] = 0


@register(MECH_EFFECTS, "chi")
def _m_chi(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """气力：攒层（每点＋12%）"""
    if not mval:
        return
    p_mech["chi"] = _stack(battle, "chi", p_mech, mval)
    logs.append(f"🌀 气力 {p_mech['chi']}(每点＋12%)")


@register(MECH_EFFECTS, "chi_burst")
def _m_chi_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """气力爆发"""
    n = p_mech.get("chi", 0)
    bonus = int(total * n * 0.15)
    battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - bonus)
    logs.append(f"🌀 拳法奥义！{n} 点气力额外 {bonus} 伤害")
    p_mech["chi"] = 0


@register(MECH_EFFECTS, "iron")
def _m_iron(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """金身：叠层（减伤，在 _damage_player 生效）"""
    if not mval:
        return
    p_mech["iron"] = _stack(battle, "iron", p_mech, mval)
    logs.append(f"🪷 金身层数 {p_mech['iron']}(每层减伤 4%)")


@register(MECH_EFFECTS, "iron_burst")
def _m_iron_burst(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """金身爆发：层数转伤害"""
    n = p_mech.get("iron", 0)
    bonus = int(total * n * 0.12)
    battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - bonus)
    logs.append(f"🪷 不坏金身！{n} 层额外 {bonus} 伤害")
    p_mech["iron"] = 0


@register(MECH_EFFECTS, "bless_shield")
def _m_bless_shield(battle, mval, p_mech, total, logs, skill_name, is_crit):
    """神恩护盾：层数转护盾"""
    n = p_mech.get("bless", 0)
    st2 = battle._player_stats(battle._last_player) if hasattr(battle, "_last_player") else None
    player = battle._last_player
    if st2 and n and player is not None:
        shield = int(st2["matk"] * 0.08 * n)
        battle.shield = battle.shield + shield
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
    """召唤：每 3 回合召唤援军（攻击提升）"""
    if r > 1 and r % 3 == 0 and e.get("summoned_round") != r:
        e["summoned_round"] = r
        battle.e_buffs["mon_atk_up"] = max(battle.e_buffs.get("mon_atk_up", 0), 2)
        logs.append(f"👥【{e['name']}】召唤了援军！攻击提升！")


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


@register(BOSS_MECHS, "phase")
def _b_phase(battle, logs, e, r):
    """阶段：每掉一半血进入下一阶段（最多 3 次）"""
    pc = e.get("phase_count", 0)
    target = 0.5 ** (pc + 1)
    ratio = e.get("hp", 1) / max(1, e.get("max_hp", 1))
    if ratio < target and pc < 3:
        e["phase_count"] = pc + 1
        logs.append(f"🔥【{e['name']}】进入第 {pc + 2} 阶段！力量再度攀升！")


@register(BOSS_MECHS, "stacks")
def _b_stacks(battle, logs, e, r):
    """叠层：每 2 回合攻击叠层 +1（上限 5）"""
    if r > 0 and r % 2 == 0:
        cur = e.get("mech_stacks_n", 0)
        if cur < 5:
            e["mech_stacks_n"] = cur + 1
            logs.append(f"⚔️【{e['name']}】气势攀升，攻击叠层＋1({cur + 1}/5)")


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
    """召唤援军"""
    from ..battle import BUFF_TURNS  # 延迟引用，避免模块循环
    battle.e_buffs["summon"] = BUFF_TURNS
    logs.append(f"【{battle.enemy['name']}】使用了【{sname}】，召唤了援军！")


# ================= 4. 怪物控制机制（_enemy_turn 技能 mech） =================

MON_CTRL_EFFECTS = {}


@register(MON_CTRL_EFFECTS, "freeze")
def _mc_freeze(battle, player, logs, mval):
    """冻结玩家（概率，1 回合）"""
    chance = min(0.75, 0.25 + mval * 0.15)
    if random.random() < chance:
        battle.p_buffs["freeze"] = 1
        logs.append("❄️ 你被冻结，下回合无法行动！")


@register(MON_CTRL_EFFECTS, "stun")
def _mc_stun(battle, player, logs, mval):
    """眩晕玩家（概率，1 回合）"""
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
    """减速玩家（霜狼套 5 件免疫）"""
    if "霜狼" in "|".join(battle._set_bonus_5(player)):
        logs.append("🧊 抗寒生效！霜狼套免疫了减速！")
    else:
        battle.p_buffs["spd_down"] = max(battle.p_buffs.get("spd_down", 0), 2)
        logs.append("🧊 你被减速，2 回合内速度下降！")


# ================= 内部工具（延迟绑定 Battle 常量） =================

def _stack(battle, mech, p_mech, mval):
    """叠层（封顶逻辑 v59 在 engine.mech_stack_gain）"""
    from ..engine import mech_stack_gain
    return mech_stack_gain(mech, p_mech, mval)
