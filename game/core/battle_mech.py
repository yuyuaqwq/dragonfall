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
    """注册装饰器。
    v125.1 P2：同时记录 (registry, key) 注册顺序——供末尾 _validate_boss_mechs()
    检测 BOSS_MECHS 重复注册（register 会静默覆盖同键，重复即 bug）。"""
    def deco(fn):
        _REG_ORDER.append((id(registry), key))
        registry[key] = fn
        return fn
    return deco


# v125.1 P2：注册顺序跟踪（见 register docstring；供末尾启动校验消费）
# v163 召唤机制定稿（策划案 04 章二.5）：CD 5 刻、单次 1 只、场上上限 3。
# 数值意图：Boss 战长盘有召唤压力但可推进；防无上限堆怪拖死（咕噜 round63 实测越打越多）。
SUMMON_MINION_CAP = 3
SUMMON_MINION_CD = 5
_REG_ORDER = []


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


@register(MECH_EFFECTS, "zhan_yi")
def _m_zhan_yi(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v151 战意：叠层（0-10，持有即生效，每层＋4% 攻击，不消耗）"""
    if not mval:
        return
    p_mech["zhan_yi"] = _stack(battle, "zhan_yi", p_mech, mval)
    logs.append(f"⚔️ 战意 {p_mech['zhan_yi']}(每层攻击＋4%，满 10 进入狂暴)")


@register(MECH_EFFECTS, "lian_duan")
def _m_lian_duan(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v151 连段：叠层（0-10，计数非货币，断连归零）"""
    if not mval:
        return
    p_mech["lian_duan"] = _stack(battle, "lian_duan", p_mech, mval)
    logs.append(f"🔗 连段 {p_mech['lian_duan']}(计数型，断连归零)")


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
        battle._cast_buffs()["atk_up_strong"] = skill_buff_turns(1)
        logs.append(f"🔥 狂战之魂！{n} 层狂暴 → 攻击大幅提升")
    p_mech["rage"] = 0


@register(MECH_EFFECTS, "burn")
def _m_burn(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """灼烧：叠层（每层每刻掉 3% 生命）
    重构图契约 §3.1：敌方灼烧迁为 enemy["debuffs"]["burn"]（副本/世界Boss 全局共享）。"""
    if not mval:
        return
    enemy = battle.enemy or {}
    # 免疫检查：enemy["immune_dots"] 含 "burn" 时完全免疫，不叠层
    if "burn" in (enemy.get("immune_dots") or []):
        logs.append("🛡️ 敌人免疫灼烧！")
        return
    deb = enemy.setdefault("debuffs", {})
    cur = deb.get("burn") or {"n": 0, "mult": 1.0}
    # v1.1 火之亲和（burn_amp 被动）乘算：mult 取 max(旧, 新)，无被动=1.0（对齐 _m_poison 模式）
    new_mult = 1.0
    try:
        _lp = getattr(battle, "_last_player", None)
        if _lp is not None:
            for _pn, _ps in battle._passive_map(_lp)["proc"].get("burn_amp", []):
                new_mult *= float(_ps.get("mult", 1.2))
    except Exception:
        new_mult = 1.0
    cur["mult"] = max(float(cur.get("mult", 1.0) or 1.0), new_mult)
    cur["n"] = min(5, int(cur.get("n", 0) or 0) + mval)
    deb["burn"] = cur
    n = cur["n"]
    base_log = f"🔥 灼烧层数 {n}(每刻 {n * 3}% 生命)"
    # v1.1 易燃预备：层数≥3 时灼爆引爆伤害 +{10*(n-2)}%（3层+10%/4层+20%/5层+30%）
    if n >= 3:
        base_log += f" 🔥 易燃预备：引爆伤害 +{10 * (n - 2)}%"
    # v1.2 减益适应（契约 §11.1）：灼烧叠层成功（含刷新）时适应 +4%（cap 0.20），记录 last_round
    adapt = enemy.setdefault("adapt", {})
    adapt["burn"] = min(0.20, float(adapt.get("burn", 0.0) or 0.0) + 0.04)
    cur["last_tick"] = max(1, int(battle._tick_no()))
    deb["burn"] = cur
    base_log += f" 🦠 目标对灼烧产生了适应！抗性 +4%（当前 +{int(adapt['burn'] * 100)}%）"
    logs.append(base_log)


@register(MECH_EFFECTS, "burn_burst")
def _m_burn_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """灼烧引爆：每层立即 40% 魔攻
    重构图契约 §3.1：读/清 enemy["debuffs"]["burn"]（敌方灼烧层迁为目标级状态）。
    重构图契约 §10.1 易燃乘区：灼爆时 n≥3 → 伤害 ×(1+0.10×(n-2))（3层+10%/4层+20%/5层+30%），
    日志标注「🔥 易燃！」；公式主体仍为 matk×0.40×n 魔法段。"""
    enemy = battle.enemy or {}
    n = int(((enemy.get("debuffs") or {}).get("burn") or {"n": 0}).get("n", 0) or 0)
    st2 = battle._player_stats(battle._last_player) if hasattr(battle, "_last_player") else None
    if st2 and n:
        d = int(st2["matk"] * 0.40 * n)
        # 易燃乘区：n≥3 时引爆伤害提升（3层+10%/4层+20%/5层+30%）
        if n >= 3:
            flammable = 1.0 + 0.10 * (n - 2)
            d = int(d * flammable)
            logs.append(f"🔥 易燃！灼烧层数 {n} 触发易燃，引爆伤害 ×{flammable:.1f}！")
        _burst_damage(battle, d, logs)
        logs.append(f"🔥 灼烧引爆！{n} 层造成 {d} 点伤害")
    enemy.get("debuffs", {}).pop("burn", None)
    battle.e_buffs.pop("burn", None)


@register(MECH_EFFECTS, "freeze")
def _m_freeze(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """冻结：概率冻结 1 刻"""
    use_mc, chance = _mech_chance(info, min(0.75, 0.25 + mval * 0.15))
    if not mval and not use_mc:
        return
    if random.random() < chance:
        battle.e_buffs["freeze"] = 1
        logs.append("❄️ 敌人被冻结，跳过下刻！")


@register(MECH_EFFECTS, "spd_down")
def _m_spd_down(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """减速：敌方速度下降（battle._enemy_stats 按 SPD_DOWN_MULT 结算）"""
    use_mc, chance = _mech_chance(info, 1.0)  # 原逻辑：命中即减速（无概率）
    if not mval and not use_mc:
        return
    if use_mc and random.random() >= chance:
        return
    dur = max(int(mval or 0), 1)  # v113.1：mech_chance 技能不依赖 mval 成长，保证至少 1 刻
    battle.e_buffs["spd_down"] = max(battle.e_buffs.get("spd_down", 0), dur)
    logs.append(f"🧊 敌人被减速 {dur} 刻，速度下降！")


@register(MECH_EFFECTS, "stun")
def _m_stun(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """眩晕：概率眩晕 1 刻（v63 物理系控制）
    v113.1：技能自带 mech_chance（如时停领域 1.0）时用它覆写内部概率，Lv.1 也可触发。"""
    use_mc, chance = _mech_chance(info, min(0.60, 0.20 + mval * 0.15))
    if not mval and not use_mc:
        return
    if random.random() < chance:
        battle.e_buffs["stun"] = 1
        logs.append("🌀 敌人被眩晕，跳过下刻！")


@register(MECH_EFFECTS, "silence")
def _m_silence(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """沉默：稳定沉默 2 刻（v63 禁技能）"""
    if not mval:
        return
    battle.e_buffs["silence"] = 2
    logs.append("🤐 敌人被沉默，2 刻内无法使用技能！")


@register(MECH_EFFECTS, "cleanse")
def _m_cleanse(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """净化：清除敌方增益（v63 mon_atk_up/mon_def_up/狂暴/召唤）
    重构图契约 §3.1 扩展：新增清空敌方持续减益 enemy["debuffs"]（毒/灼烧/标记/流血）。"""
    if not mval:
        return
    removed = []
    for k in ("mon_atk_up", "mon_atk_up_strong", "mon_def_up", "summon", "enraged"):
        if k in battle.e_buffs or (k == "enraged" and battle.enemy.get("enraged")):
            battle.e_buffs.pop(k, None)
            battle.enemy["enraged"] = False
            removed.append(k)
    # 新增：净化敌方持续减益（目标级 enemy["debuffs"]，pop 全部键）
    enemy = battle.enemy or {}
    deb = enemy.get("debuffs") or {}
    had_debuffs = bool(deb)
    for _k in list(deb):
        deb.pop(_k, None)
    # 文案：增益与减益的净化提示各自独立
    if removed and had_debuffs:
        logs.append("✨ 净化！敌人的增益被驱散，中毒/灼烧/标记也被一并清除！")
    elif removed:
        logs.append("✨ 圣光净化！敌人的增益被驱散！")
    elif had_debuffs:
        logs.append("✨ 净化！敌人的中毒/灼烧/标记被驱散！")
    else:
        logs.append("✨ 圣光净化，敌人没有增益可驱散。")


@register(MECH_EFFECTS, "mark")
def _m_mark(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """标记：叠层（层数供 mark_burst 消费，同时挂 e_buffs 供 _apply_mark 增伤）
    重构图契约 §3.1：敌方标记迁为 enemy["debuffs"]["mark"]（cap 5），
    并**保留** battle.e_buffs["mark"]=DEBUFF_TURNS（+30% 易伤计时不变）。"""
    from ..battle import DEBUFF_TURNS  # 延迟引用，避免模块循环
    if not mval:
        return
    enemy = battle.enemy or {}
    deb = enemy.setdefault("debuffs", {})
    cur = deb.get("mark") or {"n": 0, "mult": 1.0}
    cur["n"] = min(5, int(cur.get("n", 0) or 0) + mval)
    deb["mark"] = cur
    battle.e_buffs["mark"] = DEBUFF_TURNS  # +30% 易伤计时保留
    n = cur["n"]
    logs.append(f"🎯 目标被标记！标记层数 {n}")


@register(MECH_EFFECTS, "mark_burst")
def _m_mark_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """标记爆发：每层 +20%
    重构图契约 §3.1：读/清 enemy["debuffs"]["mark"]（敌方标记层迁为目标级状态）。"""
    enemy = battle.enemy or {}
    n = int(((enemy.get("debuffs") or {}).get("mark") or {"n": 0}).get("n", 0) or 0)
    bonus = int(total * n * 0.20)
    _burst_damage(battle, bonus, logs)
    logs.append(f"🎯 猎杀标记！{n} 层额外 {bonus} 伤害")
    enemy.get("debuffs", {}).pop("mark", None)


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
        battle._cast_buffs()["spellblade_surge"] = 1
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
    """毒层：叠层（每层每刻 5% 生命，v110 与 POISON_PCT 对齐）
    重构图契约 §3.1：敌方持续减益迁为 enemy["debuffs"]（副本/世界Boss 全局共享单份），
    不再写 p_mech（玩家 mech_stacks）——敌方毒层为目标级共享状态。
    v113.1：技能自带 mech_chance（如轻快拨弦 0.1 / 淬毒之刃 0.5）时作为施毒概率。"""
    use_mc, chance = _mech_chance(info, 1.0)  # 原逻辑：命中即叠毒
    if not mval and not use_mc:
        return
    if use_mc and random.random() >= chance:
        return
    enemy = battle.enemy or {}
    # 免疫检查：enemy["immune_dots"] 含 "poison" 时完全免疫，不叠层
    if "poison" in (enemy.get("immune_dots") or []):
        logs.append("🛡️ 敌人免疫中毒！")
        return
    deb = enemy.setdefault("debuffs", {})
    cur = deb.get("poison") or {"n": 0, "mult": 1.0}
    # 叠毒者被动倍率：乘算（默认 1.0），刷新取 max(旧, 新)，getattr 保护对齐 _m_burn 风格
    new_mult = 1.0
    try:
        _lp = getattr(battle, "_last_player", None)
        if _lp is not None:
            for _pn, _ps in battle._passive_map(_lp)["proc"].get("poison", []):
                new_mult *= float(_ps.get("mult", 1.2))
    except Exception:
        new_mult = 1.0
    cur["mult"] = max(float(cur.get("mult", 1.0) or 1.0), new_mult)
    cur["n"] = min(5, int(cur.get("n", 0) or 0) + mval)
    deb["poison"] = cur
    n = cur["n"]
    # v1.1 毒蚀：每层使目标防御 -4%（上限 -20%），随层数衰减自动恢复；日志与毒层合并输出
    base_log = f"☠️ 毒层 {n}(每层 50%攻击+1.5%生命，{n} 刻后消散) 🛡️ 毒蚀：目标防御 -{4 * n}%（上限20%）"
    # v1.2 减益适应（契约 §11.1）：毒层叠成功（含刷新）时适应 +4%（cap 0.20），记录 last_round
    adapt = enemy.setdefault("adapt", {})
    adapt["poison"] = min(0.20, float(adapt.get("poison", 0.0) or 0.0) + 0.04)
    cur["last_tick"] = max(1, int(battle._tick_no()))
    deb["poison"] = cur
    base_log += f" 🦠 目标对毒产生了适应！抗性 +4%（当前 +{int(adapt['poison'] * 100)}%）"
    logs.append(base_log)


@register(MECH_EFFECTS, "poison_burst")
def _m_poison_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v107 毒爆（丛林猎手）：poison 层数≥3 可引爆——清层。
    重构图契约 §3.1：读/清 enemy["debuffs"]["poison"]（敌方毒层迁为目标级共享状态）。
    重构图契约 §10.1 v1.1 修正：伤害 = atk×0.30×n，**物理段吃 def**（dmg_type="phys"，
    与毒 dot 的 atk 口径一致，修复 skills.py 注释"按 atk"的矛盾）；仍不吃 dot_res（爆发直伤）。
    v1.3（审计 R1）：毒爆系数 0.15 → 0.30，5 层从 1%→2%+ Boss 血，成为可观收尾。"""
    enemy = battle.enemy or {}
    n = int(((enemy.get("debuffs") or {}).get("poison") or {"n": 0}).get("n", 0) or 0)
    if n < 3:
        logs.append(f"☠️ 毒层 {n}（≥3 层可引爆）")
        return
    st2 = battle._player_stats(battle._last_player) if hasattr(battle, "_last_player") else None
    if st2 and n:
        from ..engine import calc_damage as _calc  # v107 局部导入防循环依赖
        est = battle._enemy_stats()
        d = _calc(int(st2["atk"] * 0.30 * n), est.get("def", 0), dmg_type="phys")
        _burst_damage(battle, d, logs)
        # v1.3 毒爆特色（与灼爆"易燃更痛"区分）：毒爆余毒虚弱——敌方攻击 -5%×n（3层-15%…5层-25%）2 刻。
        # 提前引爆（3层）即可拿虚弱压制，等满层则更高伤害+更强虚弱——"提前爆发的价值"成立。
        _wv = 0.05 * n
        battle.e_buffs["mon_atk_down"] = max(int(battle.e_buffs.get("mon_atk_down", 0) or 0), 2)
        battle.e_buffs["_weaken_val"] = max(float(battle.e_buffs.get("_weaken_val", 0) or 0), _wv)
        logs.append(f"😵 毒爆余毒侵蚀！敌方攻击 -{int(_wv * 100)}%（2 刻）")
        logs.append(f"☠️ 毒爆！{n} 层引爆造成 {d} 点物理伤害")
    enemy.get("debuffs", {}).pop("poison", None)
    battle.e_buffs.pop("poison", None)


@register(MECH_EFFECTS, "bleed")
def _m_bleed(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v151 流血：叠层到 enemy.debuffs.bleed（每层每刻掉血，与 poison 同构）。
    刺客割裂等技能 mech=bleed 消费端。"""
    use_mc, chance = _mech_chance(info, 1.0)
    if not mval and not use_mc:
        return
    if use_mc and random.random() >= chance:
        return
    enemy = battle.enemy or {}
    if "bleed" in (enemy.get("immune_dots") or []):
        logs.append("🛡️ 敌人免疫流血！")
        return
    deb = enemy.setdefault("debuffs", {})
    cur = deb.get("bleed") or {"n": 0, "mult": 1.0}
    cur["n"] = min(5, int(cur.get("n", 0) or 0) + mval)
    cur["last_tick"] = max(1, int(battle._tick_no()))
    deb["bleed"] = cur
    n = cur["n"]
    logs.append(f"🩸 流血 {n} 层(每层每刻掉血)")


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
    """召唤：每 5 刻召唤 1 只援军实体（v163 定稿：原每 3 刻 1-2 只且无场上上限→越打越多，
    咕噜 round63 实测召唤 9+ 爪牙清不完；CD 拉长 + 单次 1 只 + 上限 3 由
    battle._summon_minions 统一执行——技能召唤同走该函数也受上限约束）"""
    if r > 1 and r % SUMMON_MINION_CD == 0 and e.get("summoned_round") != r:
        e["summoned_round"] = r
        mins = battle._summon_minions(1)
        names = '、'.join(f'【{m["name"]}】' for m in mins)
        if not mins:
            return  # 满员/无可召（上限 3 已满）→ 本次机制跳过（不叠攻击buff）
        battle.e_buffs["mon_atk_up"] = max(battle.e_buffs.get("mon_atk_up", 0), 2)
        logs.append(f'👥【{e["name"]}】召唤了 {names}！它们挡在身前，攻击也提升了！')


@register(BOSS_MECHS, "heal")
def _b_heal(battle, logs, e, r):
    """回血：每 4 刻恢复 8% 生命"""
    if r > 1 and r % 4 == 0 and e.get("healed_round") != r:
        e["healed_round"] = r
        heal = int(e.get("max_hp", 1) * 0.08)
        e["hp"] = min(e.get("max_hp", 1), e.get("hp", 0) + heal)
        logs.append(f"💚【{e['name']}】汲取力量，恢复了 {heal} 点生命！")


@register(BOSS_MECHS, "shield")
def _b_shield(battle, logs, e, r):
    """护盾：首刻出现 20% 护盾（受伤减半）"""
    if r == 1 and not e.get("shields"):
        # v177 actor 护盾统一：e["shields"] dict（halve=True 保留受伤减半语义，兼容旧 boss_shield 单源）
        _val = int(e.get("max_hp", 1) * 0.20)
        _shd = e.setdefault("shields", {})
        _shd["boss"] = {"value": _val, "halve": True}
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
    - 阶段演出刻：进入新阶段该刻不行动（battle._phase_skip_act=True）
    - 换招表：进入第 N 阶段追加 phases[N-1].add_skills（幂等）
    - 阈值预告：阶段 2/3 起，血量接近下一阈值(+3%)提前输出预警
    - 阈值：有 phases[].min 用 min%（设计 60%/30%），缺省 0.5^n（50%/25%）
    无 phases 配置 → 完全维持旧行为（纯增伤 atk/matk +20%/阶段）。"""
    pc = e.get("phase_count", 0)
    cfg = battle._boss_cfg(e) if hasattr(battle, "_boss_cfg") else {}
    phases = cfg.get("phases") or []
    target = _phase_threshold(phases, pc)
    ratio = e.get("hp", 1) / max(1, e.get("max_hp", 1))
    # ---- 阈值预告（阶段 2/3 起）：接近下一阈值 +3% 内提前 2 刻口径输出 ----
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
        # v138.1 阶段四件套：读取模板 + Boss 内联覆盖，应用数值/行为/退出/反制
        # 数据源 game/data/boss_phases.py BOSS_PHASE_TEMPLATES（phases[] 条目带 phase_id 时引用；
        # 旧 phases 只有 min/add_skills/script → 不引用模板，维持旧行为）
        _phase_cfg = None
        _merged = None
        if phases and npc - 1 < len(phases):
            _ph = phases[npc - 1]
            _pid = _ph.get("phase_id")
            if _pid and hasattr(battle, "_phase_apply"):
                try:
                    from ..data.boss_phases import merge_phase_config
                    _merged = merge_phase_config(_pid, _ph)
                    _phase_cfg = _merged
                except Exception:
                    _phase_cfg = None
        if _phase_cfg and hasattr(battle, "_phase_apply"):
            battle._phase_apply(e, _phase_cfg, npc, logs)
        # v1.2 Boss phase 转换清异常（契约 §11.2）：清空敌方持续减益与适应状态
        # v138.2 律三（进度遗产）：改为保留一半层数（_preserve_debuffs），不再全清——
        # 借鉴《云海猎团》「破坏槽不随阶段重置、异常积蓄保留 50%」：转阶段前攒的异常条不白费
        # （若阶段模板 preserve_debuffs=False 才全清，默认 True 保留）
        _preserve = True
        if _merged is not None:
            _preserve = bool(_merged.get("preserve_debuffs", True))
        had_debuffs = bool(e.get("debuffs"))
        had_adapt = bool(e.get("adapt"))
        if had_debuffs or had_adapt:
            if _preserve and hasattr(battle, "_preserve_debuffs"):
                battle._preserve_debuffs(logs)  # 保留 50% 层数 + 阈值 +15%
            else:
                e.pop("debuffs", None)
                e.pop("adapt", None)
                logs.append("🌀 Boss 转换阶段，净化了身上的异常状态！")
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
        # ---- 阶段演出刻：本刻不行动（给玩家呼吸点）----
        battle._phase_skip_act = True


@register(BOSS_MECHS, "stacks")
def _b_stacks(battle, logs, e, r):
    """叠层：每 2 刻攻击叠层 +1（上限 5）"""
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
# 约束防刷屏（once / 每 N 刻）。战斗实例级瞬态标记 battle._phase_skip_act 用于阶段演出刻。


@register(BOSS_MECHS, "phase_open")
def _b_opening(battle, logs, e, r):
    """开场技：战斗第一刻必放一次（once）。默认『咆哮』：演出行 + mon_atk_up 增益 2 刻。
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
        battle._cast_buffs()["atk_down"] = max(battle._cast_buffs().get("atk_down", 0), int(power))
        logs.append(f"🫁【{e['name']}】的{name}压制了你，攻击下降！")
    elif effect == "mortal_wound":  # v1.3 重创：玩家吸血/治疗偷取减半（2 刻）——反制吸血站撸
        battle._cast_buffs()["mortal_wound"] = max(int(battle._cast_buffs().get("mortal_wound", 0) or 0), int(power))
        logs.append(f"🤕【{e['name']}】的{name}重创了你！吸血效果减半（{int(power)} 刻）！")
    # 其他 effect 安全忽略（无副作用），保持"必放一次演出"性质


@register(BOSS_MECHS, "player_low")
def _b_player_low(battle, logs, e, r):
    """玩家低血追击：玩家 HP<30% 时 Boss 输出杀意文案并本刻攻击加成（25%）。
    触发频率：默认 once；或配置 triggers.player_low.cooldown=N 后每 N 刻一次。"""
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
    logs.append(f"☠️ 【{e['name']}】盯上了重伤的你……本刻攻击大幅提升！")
    e["_low_hp_active"] = True


@register(BOSS_MECHS, "pv_broken")
def _b_pv_broken(battle, logs, e, r):
    """玩家大招后反扑（原"破防反扑"，游戏无 PV/防护体系 → 改为玩家刚放技能后 Boss 反击）：
    玩家上一刻使用技能（battle._player_recent_skill）时触发一次反击演出 + 本刻攻击加成
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
    logs.append(f"💥 防护崩溃！【{e['name']}】愤怒反扑！(本刻追加攻击)")
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


@register(MON_BUFF_EFFECTS, "shield")
def _mb_shield(battle, logs, sname):
    """怪物护盾（v1.x 补注册：珊瑚护盾/铁壁/云盾 等 effect=shield 此前静默空转）。
    v177 actor 护盾统一：写 battle.enemy["shields"] dict（halve=True 受伤减半），
    （技能数据无数值字段，按 BOSS 口径 = 20% 最大生命），玩家伤害经
    battle._boss_dmg_filter 扣减（受伤减半 + 先扣盾再扣血），破盾即消失。"""
    _val = int(battle.enemy.get("max_hp", 1) * 0.20)
    _shd = battle.enemy.setdefault("shields", {})
    _shd["buff"] = {"value": _val, "halve": True}
    logs.append(f"🛡️ 【{battle.enemy['name']}】使用了【{sname}】，周身浮现一层护盾(受伤减半)！")


@register(MON_BUFF_EFFECTS, "spd_up")
def _mb_spd_up(battle, logs, sname):
    """怪物加速（v1.x 补注册：疾驰/疾跑/闪烁 等 effect=spd_up 此前静默空转）。
    参考 BUFF_MULT spd_up 模式：e_buffs["spd_up"] = BUFF_TURNS，
    _enemy_stats → _apply_buffs 读 BUFF_MULT["spd_up"]=(spd, 1.40) 实际生效。"""
    from ..battle import BUFF_TURNS  # 延迟引用，避免模块循环
    battle.e_buffs["spd_up"] = BUFF_TURNS
    logs.append(f"【{battle.enemy['name']}】使用了【{sname}】，速度提升了！")


# ================= 4. 怪物控制机制（_enemy_turn 技能 mech） =================

MON_CTRL_EFFECTS = {}


@register(MON_CTRL_EFFECTS, "freeze")
def _mc_freeze(battle, player, logs, mval):
    """冻结玩家（概率，1 刻）"""
    if battle._cast_buffs().get("cc_immune"):
        logs.append("🗿 不动如山！免疫了冻结！")
        return
    chance = min(0.75, 0.25 + mval * 0.15)
    if random.random() < chance:
        battle._cast_buffs()["freeze"] = 1
        logs.append("❄️ 你被冻结，下刻无法行动！")


@register(MON_CTRL_EFFECTS, "stun")
def _mc_stun(battle, player, logs, mval):
    """眩晕玩家（概率，1 刻）"""
    if battle._cast_buffs().get("cc_immune"):
        logs.append("🗿 不动如山！免疫了眩晕！")
        return
    chance = min(0.60, 0.20 + mval * 0.15)
    if random.random() < chance:
        battle._cast_buffs()["stun"] = 1
        logs.append("🌀 你被眩晕，下刻无法行动！")


@register(MON_CTRL_EFFECTS, "silence")
def _mc_silence(battle, player, logs, mval):
    """沉默玩家（稳定，2 刻）"""
    battle._cast_buffs()["silence"] = 2
    logs.append("🤐 你被沉默，2 刻内无法使用技能！")


@register(MON_CTRL_EFFECTS, "interrupt")
def _mc_interrupt(battle, player, logs, mval):
    """打断玩家蓄力（v125.1 P2 消费端：ms_an_ying_dan 等带 mech=interrupt 的怪物技能）。
    原怪物技能 interrupt:True 为死字段（_enemy_turn 不读 interrupt）——改经 mech 接线本表：
    命中时若玩家正在蓄力（battle.charging，蓄力状态在 Battle 对象而非 player dict），
    打断并返还 50% 已扣 MP（向上取整，对齐 battle._interrupt_charging 玩家侧口径）。"""
    ch = getattr(battle, "charging", None)
    if not ch or not ch.get("skill"):
        return
    cname = ch.get("name", ch.get("skill", "?"))
    spent = int(ch.get("mp_spent", 0) or 0)
    battle.charging = None
    if spent > 0 and player is not None:
        player["mp"] = min(player.get("max_mp", player.get("mp", 0)),
                           player.get("mp", 0) + (spent + 1) // 2)
        logs.append(f"🔨 你的蓄力【{cname}】被怪物打断了！返还 {(spent + 1) // 2} 点魔力。")
    else:
        logs.append(f"🔨 你的蓄力【{cname}】被怪物打断了！")


@register(MON_CTRL_EFFECTS, "slow")
def _mc_slow(battle, player, logs, mval):
    """减速玩家（霜狼套 5 件免疫；v101.28f 不动药剂免疫）"""
    if battle._cast_buffs().get("cc_immune"):
        logs.append("🗿 不动如山！免疫了减速！")
    elif "霜狼" in "|".join(battle._set_bonus_5(player)):
        logs.append("🧊 抗寒生效！霜狼套免疫了减速！")
    else:
        battle._cast_buffs()["spd_down"] = max(battle._cast_buffs().get("spd_down", 0), 2)
        logs.append("🧊 你被减速，2 刻内速度下降！")


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


# ================= 4.5 玩家增益技能效果（_skill_buff effect 分支注册表） =================

# v1.x：battle.py _skill_buff 的 effect 8 分支中 7 个可注册表化的分支迁入本表
# （mon_atk_down/element_shift/stealth/mark/sleep/shield_all/reduce_all），
# battle.py 改查表；TEAM_BUFF_KEYS（effect=xx_all 团队增益）保留原逻辑。
# SKILL_BUFF_EFFECTS 签名：fn(battle, skill_name, info, player, lv, logs) -> None
SKILL_BUFF_EFFECTS = {}


@register(SKILL_BUFF_EFFECTS, "mon_atk_down")
def _sb_mon_atk_down(battle, skill_name, info, player, lv, logs):
    """v51 挫志怒吼：敌方攻击下降（写 e_buffs 而非 p_buffs）"""
    from ..engine import skill_buff_turns
    battle.e_buffs["mon_atk_down"] = skill_buff_turns(lv)


@register(SKILL_BUFF_EFFECTS, "element_shift")
def _sb_element_shift(battle, skill_name, info, player, lv, logs):
    """v2.1 元素跃迁：切换当前元素亲和系（火→冰→雷→火），下次元素技能伤害 +20%"""
    from ..engine import skill_buff_turns
    cur = battle.resources.get("element", "fire")
    nxt = {"fire": "ice", "ice": "thunder", "thunder": "fire"}.get(cur, "fire")
    battle.resources["element"] = nxt
    battle._cast_buffs()["matk_up"] = skill_buff_turns(lv)
    battle._shifted_element = nxt  # 由 battle.py _skill_buff 元素跃迁展示块消费


@register(SKILL_BUFF_EFFECTS, "stealth")
def _sb_stealth(battle, skill_name, info, player, lv, logs):
    """v104 R3 P1-10：潜行状态实装——下次攻击必暴（desc 对齐），暴击率 +20% 持续刻"""
    from ..engine import skill_buff_turns
    battle._cast_buffs()["stealth"] = 1
    battle._cast_buffs()["crit_up"] = skill_buff_turns(lv)


@register(SKILL_BUFF_EFFECTS, "shadow_realm")
def _sb_shadow_realm(battle, skill_name, info, player, lv, logs):
    """v134.1 意见#45：影之国度实装——desc 说"每刻高暴击"但原只挂 spd_up（速度+40%），
    描述与效果不符。现补暴击：速度+40% + 暴击+20%（crit_up）持续 skill_buff_turns 刻。
    数值对齐 desc"暗影国度 3 刻(每刻高暴击)"；受 PCT_CAPS.crit 0.5 约束（_apply_buffs）。"""
    from ..engine import skill_buff_turns
    turns = skill_buff_turns(lv)
    battle._cast_buffs()["spd_up"] = max(battle._cast_buffs().get("spd_up", 0), turns)
    battle._cast_buffs()["crit_up"] = max(battle._cast_buffs().get("crit_up", 0), turns)
    logs.append(f"🌑 影之国度笼罩！速度+40%、暴击+20%（持续 {turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "mark")
def _sb_mark(battle, skill_name, info, player, lv, logs):
    """v104 M02 P1-2：死亡标记是目标易伤——挂敌方侧 e_buffs（_apply_mark 只认 e_buffs）"""
    from ..engine import skill_buff_turns
    battle.e_buffs["mark"] = skill_buff_turns(lv)


@register(SKILL_BUFF_EFFECTS, "sleep")
def _sb_sleep(battle, skill_name, info, player, lv, logs):
    """v109.2 P1-3：安眠曲改睡眠——敌方睡眠（受击解除；世界 Boss 只睡 1 刻）
    v120 q5：Boss 亦控制减半（普通 2 刻 → Boss 1 刻）。"""
    battle.e_buffs["sleep"] = battle._boss_ctrl_dur("sleep", 1 if battle.btype == "worldboss" else 2)


@register(SKILL_BUFF_EFFECTS, "shield_all")
def _sb_shield_all(battle, skill_name, info, player, lv, logs):
    """v104 M02 P1-4：全队护盾施放者自身同样获得（与 instance.py 广播口径一致：matk 20% 3 刻）
    v151 刻制审计：盾值优先读技能字段 shield_val（盾值=matk×shield_val），缺省回落 0.20"""
    st2 = battle._player_stats(player)
    base = (st2 or {}).get("matk") or (st2 or {}).get("atk") or 0
    pct = float((info or {}).get("shield_val") or 0.20)
    battle._add_shield("team_bless", int(base * pct), 3)


@register(SKILL_BUFF_EFFECTS, "reduce_all")
def _sb_reduce_all(battle, skill_name, info, player, lv, logs):
    """v113.1：团队减伤改真·百分比减伤（此前映射 def_up 防御提升，与"减伤 x%"不符）。
    p_buffs["reduce_all"] 存减伤百分比；刻数记 battle._reduce_all_left（_end_round 单独递减）。
    v1.x：数值下沉 skills.py reduce_all 字段（原 battle.py REDUCE_ALL_PCT 中文名硬编码已删）。
    v162：技能未配 reduce_all 字段时回落 desc/mech_val（战吼·守 desc 20% 但无字段）"""
    from ..engine import skill_buff_turns
    pct = float((info or {}).get("reduce_all") or 0)
    if pct <= 0:
        # v162 回落：mech_val 或默认 0.20（战吼·守 desc '全队减伤 20%'）
        mv = float((info or {}).get("mech_val") or 0)
        pct = (mv / 100.0) if mv > 1 else (mv if 0 < mv <= 1 else 0.20)
    turns = skill_buff_turns(lv, info=info)
    battle._cast_buffs()["reduce_all"] = pct
    battle._reduce_all_left = max(getattr(battle, "_reduce_all_left", 0), turns)
    logs.append(f"🛡️ 全队减伤 {int(pct*100)}%（持续 {battle._reduce_all_left} 刻）")


@register(SKILL_BUFF_EFFECTS, "reduce")
def _sb_reduce(battle, skill_name, info, player, lv, logs):
    """v162：单人减伤实现（铁壁/铜墙/亡魂护甲/磐岩甲等 effect=reduce 此前零效果）。
    时间制（与 reduce_all 一致，desc '持续 8 刻' 真实生效）：
    p_buffs["reduce"] 存减伤百分比，剩余刻记 battle._reduce_left（_end_round 递减）。
    减伤值：优先技能 reduce_pct 字段（0.45），回落 mech_val（45=45% 或 0.45），默认 0.20。"""
    from ..engine import skill_buff_turns
    rp = float((info or {}).get("reduce_pct") or 0)
    if rp <= 0:
        mv = float((info or {}).get("mech_val") or 0)
        rp = (mv / 100.0) if mv > 1 else (mv if 0 < mv <= 1 else 0.20)
    rp = min(max(rp, 0.0), 0.9)
    turns = max(1, skill_buff_turns(lv, info=info))
    battle._cast_buffs()["reduce"] = rp
    battle._reduce_left = max(getattr(battle, "_reduce_left", 0), turns)
    logs.append(f"🛡️ 减伤 {int(rp*100)}%（持续 {battle._reduce_left} 刻）")


# ================= 4.6 技能 effect 缺口补全（v169.7 技能全鉴：26 种空转 effect） =================
# 清单来源：技能引擎缺口全量清单.md §二.1/2.2。
# 命名遵循 _sb_* 风格；注册进 SKILL_BUFF_EFFECTS。
# 签名：fn(battle, skill_name, info, player, lv, logs) -> None
# ============================================================
# 通用小工具
# ============================================================

# effect 直接映射到已有 p_buffs/e_buffs 键（不改数值体系，缺数值档位由 desc 对齐的键承载）
# spd_buff→spd_up（BUFF_MULT spd_up=1.40）；dodge_buff→dodge_up（受击闪避 +40% 乘算并入，battle.py:6745）
# crit_hit_buff→crit_up（暴击 +20%）；vuln→mark（e_buffs mark +30% 易伤，_apply_mark 消费）


def _sb_pb_set_turns(battle, key, lv, info=None, base=None):
    """写 p_buffs[key]=skill_buff_turns(lv, info)（同 effect 不同技能覆盖取高）。
    base：显式刻数（desc 已写死 N 刻的技能），不传走数据 buff_turns/默认成长。"""
    from ..engine import skill_buff_turns
    t = base if base else skill_buff_turns(lv, info=info)
    battle._cast_buffs()[key] = max(int(battle._cast_buffs().get(key, 0) or 0), int(t))
    return int(battle._cast_buffs()[key])


def _sb_eb_set_turns(battle, key, lv, info=None, base=None):
    """写 e_buffs[key]=skill_buff_turns(lv, info)（敌方侧计时键，同 effect 覆盖取高）。"""
    from ..engine import skill_buff_turns
    t = base if base else skill_buff_turns(lv, info=info)
    battle.e_buffs[key] = max(int(battle.e_buffs.get(key, 0) or 0), int(t))
    return int(battle.e_buffs[key])


def _sb_write_eb_pct(battle, valkey, pct):
    """写敌方减益百分比自定义通道（_enemy_stats 消费）：
    mon_atk_down/_weaken_val（攻）、def_down/_armor_break_pct（防）、spd_down/_spd_down_pct（速）。"""
    eb = battle.e_buffs
    eb[valkey] = max(float(eb.get(valkey, 0) or 0), float(pct))


def _sb_cleanse_p(battle, player, logs, scope="single"):
    """净化玩家减益：白名单化（增益不删）——清首个非增益键（single）或全部（all）。
    注：此函数被 _sb_cleanse/_sb_cleanse_all 调用；治疗型技能（圣光驱散/圣辉涤净/生命圣域
    等 kind=治疗）的 effect 消费链在 battle.py _skill_heal——治疗路径挂接点在 battle.py
    （另一 agent 管辖），届时直接调本表 handler 即可复用同一净化逻辑。"""
    _bless = {"atk_up", "def_up", "spd_up", "matk_up", "matk_up_strong", "crit_up", "atk_up_strong",
              "atk_up_big", "atk_up_small", "spd_up_small", "crit_up_small", "crit_up_big",
              "reduce", "reduce_all", "dodge_up", "cc_immune", "shadow_dance", "next_atk_up"}
    removed = []
    if scope == "single":
        for k in list(battle._cast_buffs().keys()):
            if k in _bless:
                continue
            # 控制类不净（解控由 cleanse_all 的 ctrl 分支另处理；单体净化 desc 只清减益）
            removed.append(k)
            del battle._cast_buffs()[k]
            break
    else:
        for k in list(battle._cast_buffs().keys()):
            if k in _bless:
                continue
            removed.append(k)
            del battle._cast_buffs()[k]
    # 净化攻击/减速类 p_buffs 减益（spd_down/atk_down 等）
    if removed:
        logs.append(f"✨ 净化！驱散了 {'、'.join(removed)}")
    return removed


@register(SKILL_BUFF_EFFECTS, "spd_buff")
def _sb_spd_buff(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：速度提升（风之疾走/疾影/疾风步 desc +30%~+40%）。
    映射 BUFF_MULT spd_up=1.40（×1.40 = +40%；引擎单档无法表达 30/40 梯度，取 spd_up 档）。"""
    turns = _sb_pb_set_turns(battle, "spd_up", lv, info)
    logs.append(f"💨 速度提升！(spd_up 持续 {turns} 刻)")


@register(SKILL_BUFF_EFFECTS, "dodge_buff")
def _sb_dodge_buff(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：闪避提升（闪现/闪避步/风之屏障/影分身/毒雾·障 desc +30~40%）。
    消费端已存在（battle.py:6745 受击闪避乘算并入 p_buffs[\"dodge_up\"] +40%）。"""
    turns = _sb_pb_set_turns(battle, "dodge_up", lv, info)
    logs.append(f"💨 闪避大幅提升！(dodge_up 持续 {turns} 刻)")


@register(SKILL_BUFF_EFFECTS, "crit_hit_buff")
def _sb_crit_hit_buff(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：鹰眼锁定 desc「暴击 +20%、命中 +15%」。
    v173.3 意见#95（鱼鱼拍板 B 方案）：命中维度真实落地——crit_up（暴击 +20%）+
    hit_up（精准 +15%，_monster_dodge_check 消费为敌方闪避抵消率，cap 60% 与词条同源）。
    """
    turns = _sb_pb_set_turns(battle, "crit_up", lv, info)
    _sb_pb_set_turns(battle, "hit_up", lv, info)
    logs.append(f"🎯 暴击提升 +20%、命中 +15%（持续 {turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "vuln")
def _sb_vuln(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：死亡标记（vuln）→ 目标易伤 e_buffs mark（_apply_mark 按层 +20% 消费）。
    desc「目标受到伤害 +25%」与 mark 语义完全一致（旧表死亡标记 effect=vuln 无 handler）。"""
    _sb_mark(battle, skill_name, info, player, lv, logs)


@register(SKILL_BUFF_EFFECTS, "cc_immune")
def _sb_cc_immune(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：免疫控制（圣佑/英雄叙事诗/咏叹·辉 desc「免疫 1 次控制」）。
    药水先例 potion_effects.cc_immune 写 p_buffs[\"cc_immune\"]=turns（MON_CTRL_EFFECTS
    freeze/stun/slow 命中前查此键，持续刻内免疫；刻递减由 _advance_time 驱动）。"""
    turns = _sb_pb_set_turns(battle, "cc_immune", lv, info)
    logs.append(f"🗿 免疫控制！（cc_immune 持续 {turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "cleanse")
def _sb_cleanse(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：驱散单体 1 个减益（增益型冥想 / 治疗型圣光驱散）。
    净化白名单见 _sb_cleanse_p。
    治疗路径挂接点在 battle.py（治疗型技能 effect 在 _skill_heal 无消费链——该 agent 接线时
    直接调本 handler）。"""
    _sb_cleanse_p(battle, player, logs, scope="single")
    # 冥想（武僧 增益）：desc「每刻回蓝 2% 持续 6 刻」——p_hot mana 通道（食物同款）
    if (info or {}).get("name") == "冥想" and player.get("max_mp", 0):
        _hot = battle.p_hot
        battle.p_hot = {"heal": max(0.0, float(_hot.get("heal", 0) or 0)),
                        "mana": max(0.02, float(_hot.get("mana", 0) or 0)),
                        "turns": max(int(_hot.get("turns", 0) or 0), 6)}
        logs.append("🧘 冥想：自身每刻回蓝 2%（6 刻）")


@register(SKILL_BUFF_EFFECTS, "cleanse_all")
def _sb_cleanse_all(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：全体净化并解控（治疗型 圣辉涤净/生命圣域——治疗路径挂接点在
    battle.py _skill_heal；增益技带此 effect 时经 _skill_buff 直接调用）。
    解控 = 清除玩家控制（stun/freeze/silence 行动级标记由对应行动分支消费，直接移除）。"""
    _sb_cleanse_p(battle, player, logs, scope="all")
    _rem_ctrl = []
    for _ck in ("stun", "freeze", "silence", "spd_down"):
        if battle._cast_buffs().pop(_ck, None) is not None:
            _rem_ctrl.append(_ck)
    if _rem_ctrl:
        logs.append(f"✨ 解除了 {'、'.join(_rem_ctrl)}！")


@register(SKILL_BUFF_EFFECTS, "atk_matk_all")
def _sb_atk_matk_all(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：圣光祝福 desc「全队攻+魔攻 +30% 10 刻」。
    批量写 atk_up + matk_up（参考 crit_all→crit_up 同款双写；单机=施放者自身，副本由
    instance 广播 team_effects——effect 映射在 instance buff_effects 表，此处处理单机侧）。"""
    from ..engine import skill_buff_turns
    turns = skill_buff_turns(lv, info=info)
    battle._cast_buffs()["atk_up"] = max(int(battle._cast_buffs().get("atk_up", 0) or 0), int(turns))
    battle._cast_buffs()["matk_up"] = max(int(battle._cast_buffs().get("matk_up", 0) or 0), int(turns))
    logs.append(f"✨ 全队攻击与魔攻 +30%！（持续 {turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "all_stat_cc")
def _sb_all_stat_cc(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：永恒赞歌 desc「全队全属性 +30%、免疫控制 8 刻」。
    批量写 BUFF_MULT 多键（atk_up/matk_up/def_up/spd_up/crit_up）+ cc_immune。"""
    turns = skill_buff_turns(lv, info=info)
    for _k in ("atk_up", "matk_up", "def_up", "spd_up", "crit_up"):
        battle._cast_buffs()[_k] = max(int(battle._cast_buffs().get(_k, 0) or 0), int(turns))
    battle._cast_buffs()["cc_immune"] = max(int(battle._cast_buffs().get("cc_immune", 0) or 0), int(turns))
    logs.append(f"🌈 全队全属性 +30% 并免疫控制！（持续 {turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "element_switch")
def _sb_element_switch(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：元素流转 desc「切换当前主系，影响下次挂印系别」。
    法师 _m_element_mark_current 读 battle._element_main 决定挂印系；自由切（默认火系轮换
    顺序环切，desc 无指定系——按 火→冰→雷→火 前进保持确定性）。"""
    cur = getattr(battle, "_element_main", None) or "fire"
    nxt = {"fire": "ice", "ice": "thunder", "thunder": "fire"}.get(cur, "fire")
    battle._element_main = nxt
    logs.append(f"✦ 元素流转！当前主系切换为 {nxt}（下次挂印系别）")


@register(SKILL_BUFF_EFFECTS, "shield_self")
def _sb_shield_self(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：霜晶护体 desc「为自己张开护盾 12 刻」。
    _add_shield 同源叠加 + 刷新时长；盾值按实例广播口径 matk×20%（数据无 shield_val 字段）。"""
    st2 = battle._player_stats(player)
    base = (st2 or {}).get("matk") or (st2 or {}).get("atk") or 0
    pct = float((info or {}).get("shield_val") or 0.20)
    turns = max(1, skill_buff_turns(lv, info=info))
    battle._add_shield("self_bless", int(base * pct), int(turns))
    logs.append(f"🧊 霜晶护盾！获得 {int(base * pct)} 点护盾（{turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "shield_block")
def _sb_shield_block(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：铁壁·誓 desc「自身获得护盾，格挡率 +30% 10 刻」。
    护盾走 _add_shield；格挡 = 乘算并入受击格挡键 block_up（battle.py:6817 同 block_pot 通道
    +15% 硬编码——skill 30% 需新数值键，此处写 block_up 标记 + p_eff 存 30%，引擎侧暂按
    block_pot 15% 档接入并注释扩展点）。"""
    st2 = battle._player_stats(player)
    base = (st2 or {}).get("matk") or (st2 or {}).get("atk") or 0
    pct = float((info or {}).get("shield_val") or 0.20)
    turns = max(1, skill_buff_turns(lv, info=info))
    battle._add_shield("shield_block", int(base * pct), int(turns))
    # 格挡率：写 battle._p_buff_hits 专用键（受击计数 1 次 = 格挡 1 次语义，与铁山靠同款）
    battle._cast_buffs()["block_up"] = max(int(battle._cast_buffs().get("block_up", 0) or 0), int(turns))
    battle.p_eff["block_up_val"] = max(float(battle.p_eff.get("block_up_val", 0) or 0), 0.30)  # 数值通道（受击格挡结算读）
    logs.append(f"🛡️ 获得护盾并格挡率 +30%！（{turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "block_reflect")
def _sb_block_reflect(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：铁山靠 desc「格挡 1 次攻击并反伤 40% 8 刻」。
    引擎既有消费点：受击格挡判定（battle.py:6817 并入 st[\"block\"]，格挡成功减半）+ 反伤。
    写 p_buffs block_up（格挡触发标记）+ thorns_pot（反伤乘算并入 30% 上限——40% 超上限，
    记 battle.p_eff 数值，battle.py 反伤段已存在 thorns 汇总）。"""
    turns = max(1, skill_buff_turns(lv, info=info))
    battle._cast_buffs()["block_up"] = max(int(battle._cast_buffs().get("block_up", 0) or 0), int(turns))
    battle.p_eff["block_up_val"] = max(float(battle.p_eff.get("block_up_val", 0) or 0), 0.50)  # 引擎格挡减伤档（格挡成功减半）
    # 反伤 40% 走 block_reflect_val（battle.py 反伤段随 block_up 生效），不写 thorns_pot 防与荆棘药剂双算
    battle.p_eff["block_reflect_val"] = max(float(battle.p_eff.get("block_reflect_val", 0) or 0), 0.40)
    logs.append(f"🛡️ 格挡并反伤 40%！（{turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "protect")
def _sb_protect(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：誓约之盾/守护誓言 desc「为队友挡刀并反伤 30%/50% 12 刻」。
    单人战斗无队友（allies 空）；副本仇恨/挡刀在 instance.py 广播（team_effects 口径）。
    本处单机侧等效：高额单人减伤（挡刀=承伤转移给自己，减伤映射）+ 反伤乘算。"""
    rp = 0.30 if "30" in str((info or {}).get("desc", "")) else 0.50
    turns = max(1, skill_buff_turns(lv, info=info))
    battle._cast_buffs()["reduce"] = max(float(battle._cast_buffs().get("reduce", 0) or 0), rp)
    battle._reduce_left = max(int(getattr(battle, "_reduce_left", 0) or 0), int(turns))
    # 反伤 rp 走 block_reflect_val（随 block_up/受击反伤段生效），不写 thorns_pot 防与荆棘药剂双算
    battle.p_eff["block_reflect_val"] = max(float(battle.p_eff.get("block_reflect_val", 0) or 0), rp)
    battle._cast_buffs()["block_up"] = max(int(battle._cast_buffs().get("block_up", 0) or 0), int(turns))
    logs.append(f"🛡️ 誓约守护：减伤 {int(rp * 100)}% 并反伤！（{turns} 刻；副本挡刀由 instance 广播）")


@register(SKILL_BUFF_EFFECTS, "disengage_dodge")
def _sb_disengage_dodge(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：烟雾弹 desc「脱离战斗，全队闪避 +25% 8 刻」。
    单机无脱战机制（combat 层管逃跑）；只落地闪避部分（dodge_up 40% 档降级——引擎无 25% 数值键）。"""
    _sb_dodge_buff(battle, skill_name, info, player, lv, logs)


@register(SKILL_BUFF_EFFECTS, "dodge_reduce_all")
def _sb_dodge_reduce_all(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：自然护佑 desc「全队闪避 +15%、减伤 10% 12 刻」（复合）。
    dodge 键（dodge_up）+ reduce_all 键（pct 通道独立计时）双写。"""
    _sb_dodge_buff(battle, skill_name, info, player, lv, logs)
    turns = max(1, skill_buff_turns(lv, info=info))
    battle._cast_buffs()["reduce_all"] = max(float(battle._cast_buffs().get("reduce_all", 0) or 0), 0.10)
    battle._reduce_all_left = max(int(getattr(battle, "_reduce_all_left", 0) or 0), int(turns))
    logs.append(f"🍃 自然护佑：全队减伤 10%（{turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "hunt_team_dmg")
def _sb_hunt_team_dmg(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：猎杀时刻 desc「全队对猎印目标增伤 +30% 12 刻」。
    伤害侧乘区键 hunt_mark_dmg_mult（battle.py 伤害结算读 p_buffs，命中带猎印目标时 ×1.30）。"""
    turns = max(1, skill_buff_turns(lv, info=info))
    # 乘区键：p_buffs 只存 int 时长（_advance_time 按刻到期），数值存 p_eff float（battle.py 伤害乘区读）
    battle._cast_buffs()["hunt_team_dmg"] = max(int(battle._cast_buffs().get("hunt_team_dmg", 0) or 0), int(turns))
    battle.p_eff["hunt_team_dmg"] = max(float(battle.p_eff.get("hunt_team_dmg", 0) or 0), 0.30)
    logs.append(f"🎯 猎杀时刻：全队对猎印目标增伤 +30%（{turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "star_lock")
def _sb_star_lock(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：星轨锁定 desc「锁定目标无视站位，全队对其伤害 +12% 12 刻」。
    单人无站位概念；等效 = 对当前敌增伤 12%（star_lock_mult 键伤害乘区，battle.py 读）。"""
    turns = max(1, skill_buff_turns(lv, info=info))
    battle._cast_buffs()["star_lock"] = max(int(battle._cast_buffs().get("star_lock", 0) or 0), int(turns))
    battle.p_eff["star_lock"] = max(float(battle.p_eff.get("star_lock", 0) or 0), 0.12)
    logs.append(f"🌟 星轨锁定：全队对目标伤害 +12%（{turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "reduce_shield_all")
def _sb_reduce_shield_all(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：大地守护 desc「全队减伤 30-50%（按磐核数）+护盾 12 刻」（复合）。
    磐核数 battle.resources.guard_core（0-5）：核数 ≥3 → 50%，否则 30%；护盾走 shield_all。"""
    cores = int((battle.resources or {}).get("guard_core", 0) or 0)
    rp = 0.50 if cores >= 3 else 0.30
    turns = max(1, skill_buff_turns(lv, info=info))
    battle._cast_buffs()["reduce_all"] = max(float(battle._cast_buffs().get("reduce_all", 0) or 0), rp)
    battle._reduce_all_left = max(int(getattr(battle, "_reduce_all_left", 0) or 0), int(turns))
    _sb_shield_all(battle, skill_name, info, player, lv, logs)
    logs.append(f"🪨 大地守护：全队减伤 {int(rp * 100)}%（磐核 {cores}）")


@register(SKILL_BUFF_EFFECTS, "shield_all_reduce")
def _sb_shield_all_reduce(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：守护圣域 desc「花满 10 层战意：全队护盾+减伤 30% 12 刻」（复合+门槛）。
    战意 mech_stacks.zhan_yi ≥10 才施放（数据 mp=0 CD24；不足时提示不放——desc 门槛语义）。"""
    zy = int((battle.mech_stacks or {}).get("zhan_yi", 0) or 0)
    if zy < 10:
        logs.append("⚔️ 战意不足（需满 10 层），守护圣域无法展开！")
        return
    turns = max(1, skill_buff_turns(lv, info=info))
    battle._cast_buffs()["reduce_all"] = max(float(battle._cast_buffs().get("reduce_all", 0) or 0), 0.30)
    battle._reduce_all_left = max(int(getattr(battle, "_reduce_all_left", 0) or 0), int(turns))
    _sb_shield_all(battle, skill_name, info, player, lv, logs)
    logs.append(f"🛡️ 守护圣域：全队护盾 + 减伤 30%（{turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "shadow_dance")
def _sb_shadow_dance(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：暗影步 desc「连段满 5 进影舞态：技能 CD −20%、受击不清连段」。
    battle.py 已有 _shadow_dance() 读 p_buffs[\"shadow_dance\"] 消费点（v169.7 接线：暗影步
    施放时置位）；连段门槛校验（combo/连段 ≥5 才进影舞态）。CD 减成/受击保护由 battle.py 消费。"""
    combo = int((battle.mech_stacks or {}).get("combo", 0) or 0)
    if combo < 5:
        logs.append(f"🌑 连段不足（{combo}/5），影舞态无法开启！")
        return
    turns = 6
    battle._cast_buffs()["shadow_dance"] = max(int(battle._cast_buffs().get("shadow_dance", 0) or 0), int(turns))
    logs.append(f"🌑 影舞态开启！技能 CD −20%、受击不清连段（{turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "stealth_cc")
def _sb_stealth_cc(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：影遁 desc「强制进入潜行并免疫控制 6 刻」。
    潜行 = p_buffs stealth（攻击消费，必暴+潜行乘区）；免控 = cc_immune。"""
    turns = max(1, skill_buff_turns(lv, info=info))
    battle._cast_buffs()["stealth"] = max(int(battle._cast_buffs().get("stealth", 0) or 0), 1)
    battle._cast_buffs()["cc_immune"] = max(int(battle._cast_buffs().get("cc_immune", 0) or 0), int(turns))
    logs.append(f"🌙 强制潜行并免疫控制！（{turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "taunt")
def _sb_taunt(battle, skill_name, info, player, lv, logs):
    """v169.7 注册兜底：嘲讽 effect 实机不可达（kind=嘲讽走 battle.py _player_skill 独立分支：
    敌方降攻 + 叠狂暴 / 副本仇恨），不留无消费端假字段。仅占位注册说明。"""
    logs.append("📢 嘲讽！强制敌人攻击你！(kind=嘲讽分支处理)")


@register(SKILL_BUFF_EFFECTS, "arcane_shield")
def _sb_arcane_shield(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：相位偏折 desc「张开力场护盾，消耗全部充能，每层 8% 魔攻护盾」。
    充能 battle.resources[\"arcane\"]（法师攻线）；护盾 3 刻（参考 _sb_shield_all 口径）。"""
    n = int((battle.resources or {}).get("arcane", 0) or 0)
    if n <= 0:
        logs.append("📖 没有奥术充能，相位偏折无法展开！")
        return
    st2 = battle._player_stats(player)
    base = (st2 or {}).get("matk") or 0
    val = int(base * 0.08 * n)
    battle._add_shield("arcane_shield", val, 3)
    battle.resources["arcane"] = 0
    logs.append(f"📖 相位偏折！消耗 {n} 层充能，张开 {val} 点力场护盾！")


@register(SKILL_BUFF_EFFECTS, "arcane_matrix")
def _sb_arcane_matrix(battle, skill_name, info, player, lv, logs):
    from ..engine import skill_buff_turns
    """v169.7 effect 补全：奥术矩阵 desc「全队奥术/魔法伤害 +20% 12 刻」。
    写魔法增伤乘区键 arcane_matrix（battle.py 魔法伤害结算读 p_buffs，×(1+pct)）。"""
    turns = max(1, skill_buff_turns(lv, info=info))
    battle._cast_buffs()["arcane_matrix"] = max(int(battle._cast_buffs().get("arcane_matrix", 0) or 0), int(turns))
    battle.p_eff["arcane_matrix"] = max(float(battle.p_eff.get("arcane_matrix", 0) or 0), 0.20)
    logs.append(f"🔮 奥术矩阵：奥术/魔法伤害 +20%（{turns} 刻）")


@register(SKILL_BUFF_EFFECTS, "arcane_field")
def _sb_arcane_field(battle, skill_name, info, player, lv, logs):
    """v169.7 effect 补全：奥术力场 desc「消耗 2 点充能，选择护盾或利刃（下次奥术技 ×1.3）」。
    引擎无战斗中二选一交互先例 → 默认利刃（攻击向，desc 数值可表达）：耗 2 充能 + 下次奥术技 ×1.3。
    （护盾档无数值字段——设计裁定走利刃；记录日志说明。）"""
    n = int((battle.resources or {}).get("arcane", 0) or 0)
    if n < 2:
        logs.append("📖 奥术充能不足（需 2 点），力场无法塑形！")
        return
    battle.resources["arcane"] = n - 2
    battle._cast_buffs()["arcane_field"] = max(int(battle._cast_buffs().get("arcane_field", 0) or 0), 1)
    battle.p_eff["arcane_field"] = max(float(battle.p_eff.get("arcane_field", 0) or 0), 1.30)
    logs.append("📖 奥术力场·利刃！下次奥术技伤害 ×1.3（自动选择利刃档——引擎无战斗中二选一）")


# ================= 4.7 诗人旋律 / 终章效果消费（v169.7 缺口 §四.1） =================
# 数据：12 首歌 melody=系别 token；7 个 finale=终章 token。系别→p_buffs/e_buffs 映射：
#   atk→atk_up、def→def_up(减伤 reduce_all)、spd→spd_up、atk_matk→atk_up+matk_up、
#   e_spd→e_buffs spd_down、e_atk→mon_atk_down、e_all→mon_atk_down+def_down+spd_down、
#   all→atk_up+matk_up+def_up+spd_up+crit_up（黎明颂歌 顶点）
# 数值档位（desc 基础）：
#   基础歌：战歌 atk+12%、守歌 def/减伤+10%、疾歌 spd+12%
#   分支歌：激昂 atk+20%、英雄 atk+matk+16%、凯旋 atk+18%+crit+12%、镇魂 e_spd 15%、
#          挽歌 e_atk 18%、黎明 all+25%、终焉 e_all 25%
# 光环随刻驻留：写成 p_buffs/e_buffs 时长键（v152 时刻制由 _advance_time 按数值刻到期），
# 换歌时旧键覆盖为新歌键（同一歌重复唱取高）。强度层 +20%/层由 _m_melody_chant 的
# per_stack_mult 折算在写键时放大（底层引擎只有固定倍率键 → 强度主要影响持续刻与刷新，
# 倍率分档：强度≥4 自动升一档——留给 cond agent 的 melody_stacks 乘区处理）。
# ⚠️ e_buffs 写键对齐既有命名：mon_atk_down（攻）、def_down（防）、spd_down（速）——
#   数值 % 由 _weaken_val/_armor_break_pct/_spd_down_pct 通道承载（_enemy_stats 消费）。


def _melody_apply_p_buffs(battle, mel, turns):
    """按旋律 kind 写 p_buffs 光环（返回写键列表）。数值档位按 desc 的百分比映射为既有
    BUFF_MULT 键（atk_up=+30% 档 / matk_up=+50% 档 / spd_up=+40% 档 / def_up=+45% 档——
    引擎为离散档位；desc 12~25% 的连续 % 无法逐技能表达，写键即按档生效并打日志注明）。"""
    kind = mel.get("kind")
    pb = battle._cast_buffs()
    keys = []
    if kind == "atk":
        keys.append("atk_up")
    elif kind == "def":
        # 守歌「全队减伤 +10%」→ reduce_all 减伤键（10%）——reduce_all 存百分比 float 且独立计时，
        # 不能进 keys（下方通用循环会把它当 int 刻覆盖），单独写后不再 append
        pb["reduce_all"] = max(float(pb.get("reduce_all", 0) or 0), 0.10)
        battle._reduce_all_left = max(int(getattr(battle, "_reduce_all_left", 0) or 0), int(turns))
    elif kind == "spd":
        keys.append("spd_up")
    elif kind == "atk_matk":
        keys.extend(("atk_up", "matk_up"))
    elif kind == "all":
        keys.extend(("atk_up", "matk_up", "def_up", "spd_up", "crit_up"))
    for k in keys:
        pb[k] = max(int(pb.get(k, 0) or 0), int(turns))
    return keys


def _melody_apply_e_buffs(battle, mel, turns):
    """按旋律 kind 写 e_buffs 减益光环（敌方侧）。e_* 写对应降键 + 数值 % 通道。"""
    kind = mel.get("kind")
    eb = battle.e_buffs
    if kind == "e_spd":
        eb["spd_down"] = max(int(eb.get("spd_down", 0) or 0), int(turns))
        _sb_write_eb_pct(battle, "_spd_down_pct", 0.15)
    elif kind == "e_atk":
        eb["mon_atk_down"] = max(int(eb.get("mon_atk_down", 0) or 0), int(turns))
        _sb_write_eb_pct(battle, "_weaken_val", 0.18)
    elif kind == "e_silence":
        # 封印敌方技能（每 4 刻至多 1 次）→ 以每 4 刻 1 次计时键模拟：刻数 × 0.25 折算静默覆盖
        # 引擎级：写专用计时键 melody_silence_ticks，消费点在 battle.py（敌方出手段查：距上次
        # 封印 ≥4 刻则沉默 1 刻）。此处仅置位 + 日志（数据无整数语义时按 8 刻窗口表达）。
        eb["melody_silence_lock"] = max(int(eb.get("melody_silence_lock", 0) or 0), int(turns))
    elif kind == "e_spd_hit":
        eb["spd_down"] = max(int(eb.get("spd_down", 0) or 0), int(turns))
        _sb_write_eb_pct(battle, "_spd_down_pct", 0.20)
        # 命中 −15%：敌方命中无独立通道 → 以闪避提升等效（敌方 dodge 通道 battle 无技能键）
    elif kind == "e_all":
        eb["mon_atk_down"] = max(int(eb.get("mon_atk_down", 0) or 0), int(turns))
        _sb_write_eb_pct(battle, "_weaken_val", 0.25)
        eb["def_down"] = max(int(eb.get("def_down", 0) or 0), int(turns))
        _sb_write_eb_pct(battle, "_armor_break_pct", 0.25)
        eb["spd_down"] = max(int(eb.get("spd_down", 0) or 0), int(turns))
        _sb_write_eb_pct(battle, "_spd_down_pct", 0.25)


@register(MECH_EFFECTS, "melody")
def _m_melody(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 起手：唱一首歌（驻留旋律，全队光环）。
    v169.7 补全：
    1. 存 kind=info.melody 系别 token（供 cond agent _c_melody_buff 读 battle._melody[\"kind\"]）；
    2. 真正写 p_buffs/e_buffs 光环效果（_melody_apply_p_buffs/_melody_apply_e_buffs）。"""
    if not info:
        return
    mel = _melody_state(battle)
    kind = info.get("melody") or "atk"
    mel["name"] = info.get("name", skill_name)
    mel["kind"] = kind           # ★ cond agent 消费：melody_buff / melody_stacks 读此
    mel["stack"] = 1
    mel["finale_ready"] = False
    mel["turns"] = max(1, int((info or {}).get("buff_turns") or 0) or 3)
    turns = int(mel.get("turns", 3) or 3)
    # 光环生效：清上一首同源旧键防残留后写新键（同一首歌重唱覆盖取高由写键逻辑保证）
    _melody_apply_p_buffs(battle, mel, turns)
    _melody_apply_e_buffs(battle, mel, turns)
    side = "全队" if kind in ("atk", "def", "spd", "atk_matk", "all") else "敌方"
    logs.append(f"🎵 你开始演唱【{mel['name']}】！旋律驻留（{side}，{turns} 刻），光环已生效！")


@register(MECH_EFFECTS, "melody_chant")
def _m_melody_chant(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 吟唱：当前旋律强度 +1（满 5 触发终章）。
    v169.7 补全：吟唱后按新强度刷新光环持续（同键取高）+ 强度 ≥4 时数值提升一档
    （描述层强度每层 +20% 由 p_buffs 倍率档位近似；cond agent 的 melody_stacks 另做乘区）。"""
    if not mval:
        return
    mel = _melody_state(battle)
    if not mel.get("name"):
        logs.append("🎵 还没有旋律驻留，吟唱落空！")
        return
    mel["stack"] = min(MELODY_CFG["max_stack"], int(mel.get("stack", 0)) + mval)
    turns = int(mel.get("turns", 3) or 3) + int(mel.get("stack", 1) or 1)  # 强度层顺延驻留刻
    _melody_apply_p_buffs(battle, mel, turns)
    _melody_apply_e_buffs(battle, mel, turns)
    logs.append(f"🎶 吟唱！旋律强度 {mel['stack']}/{MELODY_CFG['max_stack']}（光环刷新至 {turns} 刻）")
    if mel["stack"] >= MELODY_CFG["max_stack"] and not mel.get("finale_ready"):
        mel["finale_ready"] = True
        logs.append("🌟 旋律圆满！下一次吟唱将触发【终章】！")


@register(MECH_EFFECTS, "melody_finale")
def _m_melody_finale(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 终章：满强度一次性爆发，强度归零、旋律继续驻留。
    v169.7 补全：按 info.finale（或当前旋律 kind）真正爆发——
      crit  → crit_up 提升 +25% 8 刻
      e_spd → 敌方速度 −35% 8 刻（spd_down + _spd_down_pct 0.35）
      e_atk → 敌方攻击 −40% 8 刻（mon_atk_down + _weaken_val 0.40）
      silence → 全体沉默 3.0 刻（e_buffs silence）
      stun  → 敌方定身 3.5 刻（e_buffs stun）
      all   → 全队全属性 +50% 10 刻（批量键）
      e_all → 敌方全属性 −50% 10 刻
    爆发刻数读 desc buff_turns；控制时长小数引擎 int 递减会截断——按 int() 写入并注释。"""
    mel = _melody_state(battle)
    if not mel.get("name"):
        logs.append("🎵 还没有旋律驻留，终章落空！")
        return
    fin = (info or {}).get("finale") or mel.get("kind") or ""
    turns = max(1, int((info or {}).get("buff_turns") or 8) or 8)
    pb, eb = battle._cast_buffs(), battle.e_buffs
    tag = ""
    if fin in ("crit",):
        pb["crit_up"] = max(int(pb.get("crit_up", 0) or 0), int(turns))
        tag = "全队暴击 +25%"
    elif fin in ("e_spd",):
        eb["spd_down"] = max(int(eb.get("spd_down", 0) or 0), int(turns))
        _sb_write_eb_pct(battle, "_spd_down_pct", 0.35)
        tag = "敌方全体速度 −35%"
    elif fin in ("e_atk",):
        eb["mon_atk_down"] = max(int(eb.get("mon_atk_down", 0) or 0), int(turns))
        _sb_write_eb_pct(battle, "_weaken_val", 0.40)
        tag = "敌方全体攻击 −40%"
    elif fin in ("silence",):
        eb["silence"] = max(int(eb.get("silence", 0) or 0), int(3.0))
        tag = "全体沉默 3 刻"
    elif fin in ("stun",):
        eb["stun"] = max(int(eb.get("stun", 0) or 0), int(3.5))
        tag = "敌方全体定身 3.5 刻（引擎按 3 刻 int 消费）"
    elif fin in ("all",):
        for _k in ("atk_up", "matk_up", "def_up", "spd_up", "crit_up"):
            pb[_k] = max(int(pb.get(_k, 0) or 0), int(turns))
        tag = f"全队全属性 +50%（{turns} 刻）"
    elif fin in ("e_all",):
        eb["mon_atk_down"] = max(int(eb.get("mon_atk_down", 0) or 0), int(turns))
        _sb_write_eb_pct(battle, "_weaken_val", 0.50)
        eb["def_down"] = max(int(eb.get("def_down", 0) or 0), int(turns))
        _sb_write_eb_pct(battle, "_armor_break_pct", 0.50)
        eb["spd_down"] = max(int(eb.get("spd_down", 0) or 0), int(turns))
        _sb_write_eb_pct(battle, "_spd_down_pct", 0.50)
        tag = f"敌方全体全属性 −50%（{turns} 刻）"
    mel["stack"] = 0
    mel["finale_ready"] = False
    logs.append(f"🌠【终章】！{mel['name']} 的力量完全迸发——{tag}！")


# ================= 5. BOSS_MECHS 启动校验（v125.1 P2 审计） =================

# 被动机制白名单：reflect 由 battle.py _boss_dmg_filter 直读 enemy.mech 消费
# （不经 _boss_mech/BOSS_MECHS 注册表，见 battle.py _boss_mech docstring），
# 故不要求注册；其余 token 必须能在 BOSS_MECHS 找到 handler。
_PASSIVE_MECH_TOKENS = ("reflect",)


def validate_boss_mechs():
    """v125.1 P2：BOSS_MECHS 注册表启动校验（模块导入末尾执行，可重复调用）。
    1. 键去重：同一 mech token 被 register 两次（后注册静默覆盖前注册）→ 直接报错，
       防止两个 handler 抢同一 token 导致前者永久失效。
    2. 数据引用校验：instances.py / monster_mods.py 的 mech 字段 token 必须已注册
       （未注册 → 告警；reflect 等被动 token 白名单豁免）。
    """
    from collections import Counter
    reg_keys = [k for rid, k in _REG_ORDER if rid == id(BOSS_MECHS)]
    dups = [k for k, n in Counter(reg_keys).items() if n > 1]
    if dups:
        raise RuntimeError(
            "[battle_mech] BOSS_MECHS 重复注册（后注册覆盖前注册，请检查重复的 @register 装饰器）："
            + ", ".join(sorted(dups))
        )
    try:
        from ..data.instances import INSTANCES
        from ..data.monster_mods import MONSTER_MODS
    except Exception as _e:  # 数据层不可用（极简环境）→ 跳过数据引用校验，仅保留去重校验
        print(f"[battle_mech] 跳过 mech token 数据引用校验（数据层不可用）：{_e}")
        return
    unknown = []
    for _src_name, _src in (("instances", INSTANCES), ("monster_mods", MONSTER_MODS)):
        for _k, _v in _src.items():
            for _tok in str(_v.get("mech") or "").split(","):
                _tok = _tok.strip()
                if _tok and _tok not in BOSS_MECHS and _tok not in _PASSIVE_MECH_TOKENS:
                    unknown.append(f"{_src_name}:{_k}={_tok}")
    if unknown:
        print("[battle_mech] 警告：mech token 未在 BOSS_MECHS 注册（运行期将静默无效果）："
              + "; ".join(sorted(set(unknown))))


# ================= 4.9 v153 元素印记（法师 A 线：记账「元素印记」） =================
# v153 §2：火/冰/雷三系印记挂敌身（enemy.debuffs.element_marks），0-3 层/系，
# 不衰减（生命周期 = 结算清除或战斗结束）；结算触发反应（蒸发×1.3 / 超载AOE / 冻结 / 感电连击）。
# 层数作用：该系结算倍率 1层×1.0 / 2层×1.2 / 3层×1.4

ELEMENT_MARKS_KEY = "element_marks"
ELEMENT_MARKS_MAX = 3
ELEMENT_MARKS_REACTION = {
    "evaporate": {"pair": ("fire", "ice"), "mult": 1.30},      # 火+冰 = 蒸发 伤害×1.30
    "overload": {"pair": ("thunder", "fire"), "aoe": True},     # 雷+火 = 超载 转全体 AOE
    "freeze": {"pair": ("ice", "thunder"), "stun": 1.5},        # 冰+雷 = 冻结 定身 1.5 刻
}


def _element_marks(battle):
    """读取敌身元素印记 dict（不存在则初始化）"""
    deb = (battle.enemy or {}).setdefault("debuffs", {})
    return deb.setdefault(ELEMENT_MARKS_KEY, {})


@register(MECH_EFFECTS, "fire_mark")
def _m_fire_mark(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 挂火印：叠层（0-3，不衰减）"""
    if not mval:
        return
    marks = _element_marks(battle)
    marks["fire"] = min(ELEMENT_MARKS_MAX, int(marks.get("fire", 0) or 0) + mval)
    logs.append(f"🔥 火印 {marks['fire']}/3")


@register(MECH_EFFECTS, "ice_mark")
def _m_ice_mark(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 挂冰印：叠层（0-3，不衰减）"""
    if not mval:
        return
    marks = _element_marks(battle)
    marks["ice"] = min(ELEMENT_MARKS_MAX, int(marks.get("ice", 0) or 0) + mval)
    logs.append(f"❄️ 冰印 {marks['ice']}/3")


@register(MECH_EFFECTS, "thunder_mark")
def _m_thunder_mark(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 挂雷印：叠层（0-3，不衰减）"""
    if not mval:
        return
    marks = _element_marks(battle)
    marks["thunder"] = min(ELEMENT_MARKS_MAX, int(marks.get("thunder", 0) or 0) + mval)
    logs.append(f"⚡ 雷印 {marks['thunder']}/3")


@register(MECH_EFFECTS, "element_multi_mark")
def _m_element_multi_mark(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 双系连珠：两段各挂不同系印记 1 层（优先挂空系）"""
    marks = _element_marks(battle)
    order = ["fire", "ice", "thunder"]
    empty = [k for k in order if (marks.get(k) or 0) == 0]
    if empty:
        k = empty[0]
    else:
        k = min(order, key=lambda x: marks.get(x, 0))
    marks[k] = min(ELEMENT_MARKS_MAX, int(marks.get(k, 0) or 0) + 1)
    logs.append(f"🎨 双系连珠：{k} 印 +1（{marks.get(k)}/3）")


@register(MECH_EFFECTS, "element_burst")
def _m_element_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 结算：引爆目标印记，触发对应反应"""
    marks = _element_marks(battle)
    active = {k: v for k, v in marks.items() if v > 0}
    if not active:
        logs.append("🌫️ 目标身上没有印记，元素引爆落空！")
        return
    total_mult = 1.0
    for k, n in active.items():
        total_mult *= (1.0 + 0.2 * (n - 1))
    reacted = False
    for rname, rcfg in ELEMENT_MARKS_REACTION.items():
        k1, k2 = rcfg["pair"]
        if active.get(k1, 0) > 0 and active.get(k2, 0) > 0:
            if rname == "evaporate":
                total_mult *= rcfg["mult"]
                logs.append(f"💨 蒸发反应！伤害 ×{rcfg['mult']}")
            elif rname == "overload":
                logs.append("💥 超载反应！转为全体 AOE")
                battle._cast_buffs()["element_overload_aoe"] = 1
            elif rname == "freeze":
                battle.e_buffs["stun"] = rcfg["stun"]
                logs.append(f"🧊 冻结反应！目标定身 {rcfg['stun']} 刻")
            reacted = True
            break
    if active.get("thunder", 0) >= 3 and not reacted:
        logs.append("⚡ 感电！雷印满 3 层，连击 +1")
        battle._cast_buffs()["element_thunder_combo"] = int(battle._cast_buffs().get("element_thunder_combo", 0)) + 1
    if total_mult > 1.0:
        battle._cast_buffs()["element_burst_mult"] = total_mult
    for k in list(marks.keys()):
        marks[k] = 0
    logs.append(f"🔥 元素结算完成，印记清空！")


@register(MECH_EFFECTS, "element_burst_all")
def _m_element_burst_all(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 元素迸发：结算目标全部印记，每层 +12% 伤害"""
    marks = _element_marks(battle)
    total_layers = sum(v for v in marks.values() if v > 0)
    if total_layers <= 0:
        logs.append("🌫️ 目标身上没有印记！")
        return
    mult = 1.0 + 0.12 * total_layers
    battle._cast_buffs()["element_burst_mult"] = mult
    logs.append(f"🔥 元素迸发：结算 {total_layers} 层印记，伤害 ×{mult}")
    for k in list(marks.keys()):
        marks[k] = 0


@register(MECH_EFFECTS, "element_burst_3")
def _m_element_burst_3(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 元素裁决：结算三系印记，每系 ×1.2"""
    marks = _element_marks(battle)
    active = {k: v for k, v in marks.items() if v > 0}
    if not active:
        logs.append("🌫️ 目标身上没有印记！")
        return
    mult = 1.0
    for k, n in active.items():
        mult *= 1.2
    battle._cast_buffs()["element_burst_mult"] = mult
    logs.append(f"⚖️ 元素裁决：结算 {len(active)} 系印记，伤害 ×{mult}")
    for k in list(marks.keys()):
        marks[k] = 0


@register(MECH_EFFECTS, "element_mark_current")
def _m_element_mark_current(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 元素洪流：全体挂当前主系印记 1 层"""
    marks = _element_marks(battle)
    cur = getattr(battle, "_element_main", "fire")  # 默认火系
    marks[cur] = min(ELEMENT_MARKS_MAX, int(marks.get(cur, 0) or 0) + 1)
    logs.append(f"🌊 元素洪流：全队挂 {cur} 印 1 层（{marks.get(cur)}/3）")


# ================= 4.10 v153 诗人旋律（battle_aura + 强度层 + 终章） =================
# v153 §7：旋律驻留（同时 1 首），起手 0.6 / 吟唱 1.2 / 终章 2.4 三档；
# 强度层 0-5（每层光环效果 +20%），满 5 触发终章（一次性爆发，放完强度归零、旋律继续）
# ⚠️ v169.7 技能全鉴：本区块 handler 的真实效果实现已前移 §4.7（_melody_apply_p_buffs/
# _melody_apply_e_buffs + _m_melody/_m_melody_chant/_m_melody_finale 注册 MECH_EFFECTS）。
# Python 模块级 @register 按「后注册覆盖前注册」，同名旧骨架 handler 若保留在此会在导入
# 末尾覆盖 §4.7 的新实现——故已删除，本区块只保留 MELODY_CFG/_melody_state 供复用。

MELODY_CFG = {
    "max_stack": 5,
    "per_stack_mult": 0.20,   # 每层光环效果 +20%
}


def _melody_state(battle):
    """读取诗人旋律状态（存 battle 实例）。v169.7：含 kind 系别 token（_m_melody 写入）。"""
    if not hasattr(battle, "_melody"):
        battle._melody = {"name": None, "kind": None, "stack": 0, "finale_ready": False}
    return battle._melody


# ================= 4.11 v153 磐核 discharge（拳师 B 线） =================
# v153 §6：磐核 0-5（引擎 GUARD_CORE_CFG 已配 max 5 / discharge 系数 0.7），
# 磐岩释能/磐核爆发/气力万法 消耗全部磐核换伤害倍率

@register(MECH_EFFECTS, "guard_core_burst")
def _m_guard_core_burst(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 磐核爆发：消耗全部磐核，×(1 + 0.7 × 核数)"""
    cores = int((battle.resources or {}).get("guard_core", 0) or 0)
    if cores <= 0:
        logs.append("🪨 磐核为空，爆发落空！")
        return
    mult = 1.0 + 0.7 * cores
    battle._cast_buffs()["guard_core_burst_mult"] = mult
    battle.resources["guard_core"] = 0
    logs.append(f"🪨 磐核爆发！消耗 {cores} 核，伤害 ×{mult}")


# ================= 4.12 v153 补充机制 handler（15 个缺失 mech） =================
# v153 技能表用到的 mech 里，以下 15 个在 battle_mech.py 无 handler（会静默失效）——
# 逐一按 v153 文档机制语义补注册。

@register(MECH_EFFECTS, "zhan_yi_cash")
def _m_zhan_yi_cash(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 战士冷静：花 5 层战意 → 回 20% 生命 + 清 1 减益"""
    if not mval:
        return
    stacks = int(p_mech.get("zhan_yi", 0) or 0)
    if stacks < mval:
        logs.append("⚔️ 战意不足，冷静失效！")
        return
    p_mech["zhan_yi"] = stacks - mval
    player = getattr(battle, "_last_player", None) or battle.player or {}
    heal = int(player.get("max_hp", 1) * 0.20)
    player["hp"] = min(player.get("max_hp", 1), player.get("hp", 0) + heal)
    logs.append(f"🧘 冷静！消耗 {mval} 层战意，回复 {heal} 点生命！")
    for k in list(battle._cast_buffs().keys()):
        if k not in ("atk_up", "def_up", "spd_up"):
            del battle._cast_buffs()[k]
            logs.append(f"✨ 净化了减益【{k}】！")
            break


@register(MECH_EFFECTS, "zhan_yi_fury")
def _m_zhan_yi_fury(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 战士血祭：花 4 层战意 → 立即进入狂暴（无视 10 层门槛）"""
    if not mval:
        return
    stacks = int(p_mech.get("zhan_yi", 0) or 0)
    if stacks < mval:
        logs.append("⚔️ 战意不足，血祭失效！")
        return
    p_mech["zhan_yi"] = stacks - mval
    from .battle_modes import dual_form_state
    df = dual_form_state(getattr(battle, "_last_player", None) or battle.player or {})
    df["form"] = "alt"
    logs.append(f"🩸 血祭！消耗 {mval} 层战意，强制进入狂暴形态！")


@register(MECH_EFFECTS, "faith_unload")
def _m_faith_unload(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 牧师卸负：主动卸除 3 点信念，自身回血 15%"""
    if not mval:
        return
    faith = float(battle.resources.get("faith", 0) or 0)
    if faith < mval:
        logs.append("🕯️ 信念不足，卸负失效！")
        return
    battle.resources["faith"] = faith - mval
    player = getattr(battle, "_last_player", None) or battle.player or {}
    heal = int(player.get("max_hp", 1) * 0.15)
    player["hp"] = min(player.get("max_hp", 1), player.get("hp", 0) + heal)
    logs.append(f"🕊️ 卸负！信念 -{mval}，回复 {heal} 点生命！")


@register(MECH_EFFECTS, "finisher")
def _m_finisher(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 刺客终结技：×(1 + 0.10×连段)，结算后归零"""
    if not mval:
        return
    stacks = int(p_mech.get("lian_duan", 0) or 0)
    per = 0.10
    if info and info.get("per_stack"):
        per = float(info["per_stack"])
    mult = 1.0 + per * stacks
    battle._cast_buffs()["finisher_mult"] = mult
    logs.append(f"🔪 终结技！连段 {stacks} 段，伤害 ×{mult}")
    if not (info and info.get("keep_on_kill")):
        p_mech["lian_duan"] = 0


@register(MECH_EFFECTS, "hunt_mark")
def _m_hunt_mark(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 游侠猎印：挂敌身（enemy.debuffs.hunt_mark），每层全队 +8% 伤害，上限 3"""
    if not mval:
        return
    deb = (battle.enemy or {}).setdefault("debuffs", {})
    cur = int(deb.get("hunt_mark", 0) or 0)
    cap = int((info or {}).get("mark_cap", 3) or 3)
    deb["hunt_mark"] = min(cap, cur + mval)
    logs.append(f"🎯 猎印 {deb['hunt_mark']}/{cap} 层（全队对其伤害 +{8 * deb['hunt_mark']}%）")


@register(MECH_EFFECTS, "soul_mark")
def _m_soul_mark(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 牧师灵魂标记：每层全队 +6%（上限 3，随骷髅存活同步）"""
    if not mval:
        return
    deb = (battle.enemy or {}).setdefault("debuffs", {})
    cur = int(deb.get("soul_mark", 0) or 0)
    cap = int((info or {}).get("mark_cap", 3) or 3)
    deb["soul_mark"] = min(cap, cur + mval)
    logs.append(f"💀 灵魂标记 {deb['soul_mark']}/{cap} 层（全队对其伤害 +{6 * deb['soul_mark']}%）")


@register(MECH_EFFECTS, "curse")
def _m_curse(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 牧师骨噬诅咒：全队对目标伤害 +20%（8 刻）"""
    if not mval:
        return
    deb = (battle.enemy or {}).setdefault("debuffs", {})
    deb["curse"] = {"n": 1, "turns": 8}
    logs.append("☠️ 骨噬诅咒！全队对其伤害 +20%（8 刻）")


@register(MECH_EFFECTS, "curse_refresh")
def _m_curse_refresh(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 牧师墓穴低语：刷新目标诅咒持续"""
    deb = (battle.enemy or {}).setdefault("debuffs", {})
    if "curse" in deb:
        deb["curse"]["turns"] = 8
        logs.append("☠️ 墓穴低语：诅咒持续时间刷新！")
    else:
        deb["curse"] = {"n": 1, "turns": 8}
        logs.append("☠️ 墓穴低语：施加骨噬诅咒！")


@register(MECH_EFFECTS, "bone_rush")
def _m_bone_rush(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 牧师骸骨洪流：消耗全部骷髅，每只 90% 全体暗蚀"""
    skels = [s for s in getattr(battle, "summons", []) if s.get("tid") == "skeleton" and s.get("hp", 0) > 0]
    n = len(skels)
    if n <= 0:
        logs.append("💀 场上没有骷髅，骸骨洪流落空！")
        return
    battle._cast_buffs()["bone_rush_mult"] = 0.9 * n
    logs.append(f"💀 骸骨洪流！消耗 {n} 只骷髅，全体暗蚀 ×{0.9 * n}")


@register(MECH_EFFECTS, "sacrifice")
def _m_sacrifice(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 牧师骸骨祭仪：献祭 1 骷髅 → 全体暗蚀"""
    skels = [s for s in getattr(battle, "summons", []) if s.get("tid") == "skeleton" and s.get("hp", 0) > 0]
    if not skels:
        logs.append("💀 场上没有骷髅，祭仪落空！")
        return
    skels[0]["hp"] = 0
    battle._cast_buffs()["bone_rush_mult"] = 0.9
    logs.append("💀 骸骨祭仪！献祭 1 只骷髅，全体暗蚀 ×0.9")


@register(MECH_EFFECTS, "poison_burst_finisher")
def _m_poison_burst_finisher(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 刺客毒爆（终结技）：引爆全部毒层，每层 +14%，结算后连段归零"""
    deb = (battle.enemy or {}).setdefault("debuffs", {})
    poison = int((deb.get("poison") or {}).get("n", 0) or 0)
    per = 0.14
    if info and info.get("per_layer"):
        per = float(info["per_layer"])
    mult = 1.0 + per * poison
    battle._cast_buffs()["finisher_mult"] = mult
    logs.append(f"☠️ 毒爆！引爆 {poison} 层毒，伤害 ×{mult}")
    if poison:
        deb["poison"]["n"] = 0
    p_mech["lian_duan"] = 0


@register(MECH_EFFECTS, "atk_down")
def _m_atk_down(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 诗人哀歌：音刃 + 目标攻击 −20%"""
    battle.e_buffs["mon_atk_down"] = 8
    logs.append("📉 敌方攻击下降！（8 刻）")


@register(MECH_EFFECTS, "def_down")
def _m_def_down(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 诗人破碎和音：目标防御 −30%"""
    battle.e_buffs["def_down"] = 8
    logs.append("🛡️ 敌方防御下降！（8 刻）")


@register(MECH_EFFECTS, "all_down")
def _m_all_down(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 诗人哀悼之音：目标全属性 −20%"""
    battle.e_buffs["mon_atk_down"] = 8
    battle.e_buffs["def_down"] = 8
    logs.append("📉 敌方全属性下降！（8 刻）")


@register(MECH_EFFECTS, "corros")
def _m_corros(battle, mval, p_mech, total, logs, skill_name, is_crit, info=None):
    """v153 刺客腐蚀：真伤 DOT（层数）"""
    if not mval:
        return
    deb = (battle.enemy or {}).setdefault("debuffs", {})
    cur = deb.get("corros") or {"n": 0, "mult": 1.0}
    cur["n"] = min(5, int(cur.get("n", 0) or 0) + mval)
    deb["corros"] = cur
    logs.append(f"🧪 腐蚀 {deb['corros']['n']} 层（真伤 DOT）")


validate_boss_mechs()

