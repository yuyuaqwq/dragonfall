# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - battle_conds.py（v98.4：战斗伤害条件注册表）

消灭 game/battle.py Battle._cond_mult() 里的 if-elif 硬编码（23 分支）：
技能数据只声明 cond={"type": "...", ...}，战场判定统一走本模块注册表。

扩展方式：
- 加条件类型：register 一个函数（~5 行），之后所有技能数据直接可用
- 函数签名：fn(battle, player, cond) -> bool，返回该条件是否满足
  battle 为 Battle 实例（enemy/e_buffs/mech_stacks/p_buffs/shield/resources/_player_stats...）
  player 为玩家 dict（hp/max_hp 等），cond 为技能条件 dict

约定：
- 条件不满足返回 False，_cond_mult 会返回 1.0（无加成）
- 倍率成长（每级 +0.05）由调用方 E.skill_cond_mult 处理，本模块只管判断
"""
COND_CHECKS = {}
COND_LABELS = {}  # v101.2: 条件类型 -> label(cond)->str（技能详情面板文案）


def register(key, label=None):
    """条件注册装饰器。label(cond)->str 为技能详情面板的条件显示文案（v101.2）。
    加新条件类型 = 一处注册（判断函数 + label），player.py 详情面板零改动。"""
    def deco(fn):
        COND_CHECKS[key] = fn
        if label is not None:
            COND_LABELS[key] = label
        return fn
    return deco


# ================= 血量类条件 =================

@register("enemy_hp_low", label=lambda c: f"敌方血量<{int(c.get('hp_pct', 0.4) * 100)}%")
def _c_enemy_hp_low(battle, player, cond):
    """敌方血量低于 hp_pct（默认 40%）"""
    return battle.enemy.get("hp", 0) < battle.enemy.get("max_hp", 1) * cond.get("hp_pct", 0.4)


@register("player_hp_low", label=lambda c: f"自身血量<{int(c.get('hp_pct', 0.3) * 100)}%")
def _c_player_hp_low(battle, player, cond):
    """自身血量低于 hp_pct（默认 30%）"""
    return player.get("hp", 0) < player.get("max_hp", 1) * cond.get("hp_pct", 0.3)


@register("enemy_hp_high", label=lambda c: f"敌方血量>{int(c.get('hp_pct', 0.7) * 100)}%")
def _c_enemy_hp_high(battle, player, cond):
    """敌方血量高于 hp_pct（默认 70%）"""
    return battle.enemy.get("hp", 0) > battle.enemy.get("max_hp", 1) * cond.get("hp_pct", 0.7)


@register("player_hp_high", label=lambda c: f"自身血量>{int(c.get('hp_pct', 0.8) * 100)}%")
def _c_player_hp_high(battle, player, cond):
    """自身血量高于 hp_pct（默认 80%）"""
    return player.get("hp", 0) > player.get("max_hp", 1) * cond.get("hp_pct", 0.8)


@register("enemy_full_hp", label=lambda c: "敌方满血")
def _c_enemy_full_hp(battle, player, cond):
    """敌方满血"""
    return battle.enemy.get("hp", 0) >= battle.enemy.get("max_hp", 1)


# ================= 控制/异常状态类条件 =================

@register("enemy_frozen", label=lambda c: "敌方被冻结")
def _c_enemy_frozen(battle, player, cond):
    """敌方被冻结"""
    return "freeze" in battle.e_buffs


@register("enemy_stunned", label=lambda c: "敌方被眩晕")
def _c_enemy_stunned(battle, player, cond):
    """敌方被眩晕（v63 联动：晕杀）"""
    return "stun" in battle.e_buffs


@register("enemy_silenced", label=lambda c: "敌方被沉默")
def _c_enemy_silenced(battle, player, cond):
    """敌方被沉默（v63 联动：静默处决）"""
    return "silence" in battle.e_buffs


@register("enemy_poison_stacks", label=lambda c: f"敌方中毒≥{c.get('stacks', 0)}层")
def _c_enemy_poison_stacks(battle, player, cond):
    """敌方中毒层数 ≥ stacks（默认 3）"""
    return battle.mech_stacks.get("poison", 0) >= cond.get("stacks", 3)


@register("enemy_marked", label=lambda c: "敌方被标记")
def _c_enemy_marked(battle, player, cond):
    """敌方被标记（e_buffs 或机制层数任一）"""
    return "mark" in battle.e_buffs or battle.mech_stacks.get("mark", 0) > 0


@register("enemy_debuff", label=lambda c: "敌方有减益")
def _c_enemy_debuff(battle, player, cond):
    """敌方有减益（负面 buff 或毒/灼烧/标记层）"""
    debuff_keys = ("def_down", "spd_down", "mon_atk_down", "atk_down",
                   "stun", "freeze", "silence", "poison", "burn", "mark")
    if any(k in battle.e_buffs for k in debuff_keys):
        return True
    return any(k in battle.mech_stacks for k in ("poison", "burn", "mark"))


@register("enemy_slowed", label=lambda c: "敌方减速中")
def _c_enemy_slowed(battle, player, cond):
    """敌方减速中"""
    return "spd_down" in battle.e_buffs or "mon_spd_down" in battle.e_buffs


@register("element_marks", label=lambda c: f"敌方{c.get('element','')}印记≥{c.get('stacks',0)}层")
def _c_element_marks(battle, player, cond):
    """敌方元素印记层数 ≥ stacks（火印/冰印/雷印；element=any 任意系）"""
    from ..engine import ELEMENT_MARKS  # 延迟引用，避免 core→engine→content→core 循环
    elem = cond.get("element", "")
    if elem == "any":
        marks_total = sum(battle.e_buffs.get(mk, 0) for mk in ELEMENT_MARKS.values())
        return marks_total >= cond.get("stacks", 1)
    mk = ELEMENT_MARKS.get(elem, "")
    return bool(mk) and battle.e_buffs.get(mk, 0) >= cond.get("stacks", 1)


# ================= 自身状态类条件 =================

@register("player_shield", label=lambda c: "自身有护盾")
def _c_player_shield(battle, player, cond):
    """自身有护盾（v104 修复：v101.28d 护盾 buff 化后 battle.shield 已移除，
    改判 p_shields（来源 → {"value": 盾值, "turns": 剩余回合}）任一项盾值 > 0）"""
    shields = getattr(battle, "p_shields", None) or {}
    return sum(s.get("value", 0) for s in shields.values()) > 0


@register("player_spd_up", label=lambda c: "自身加速中")
def _c_player_spd_up(battle, player, cond):
    """自身有加速增益"""
    return "spd_up" in battle.p_buffs


@register("player_chi_stacks", label=lambda c: f"自身气力≥{c.get('stacks',0)}点")
def _c_player_chi_stacks(battle, player, cond):
    """自身气力 ≥ stacks（默认 3）"""
    return battle.mech_stacks.get("chi", 0) >= cond.get("stacks", 3)


@register("player_res_stacks", label=lambda c: f"自身{c.get('res_key','')}≥{c.get('stacks',0)}")
def _c_player_res_stacks(battle, player, cond):
    """核心资源 ≥ stacks（v2.0：怒气≥5 / 连击点≥3 / 信仰≥5 / 气≥3）

    v104 修复：res_key='element' 是 switch 字符串资源（battle.resources["element"]="fire"），
    不能与 int stacks 做 >= 比较（TypeError）→ 字符串资源存在非空值即视为满足
    （元素风暴「元素过载」stacks=1）；rage/cp/faith/chi/energy 等 int 叠层保持原逻辑。
    """
    rk = cond.get("res_key", "rage")
    val = battle.resources.get(rk, 0)
    if isinstance(val, str):
        return bool(val)
    if not isinstance(val, (int, float)):
        return False  # 未知类型防御（None 等）
    return val >= cond.get("stacks", 3)


@register("player_mech_stacks", label=lambda c: f"自身{c.get('mech','')}层≥{c.get('stacks',0)}")
def _c_player_mech_stacks(battle, player, cond):
    """自身机制层数 ≥ stacks（v2.1：奥术充能 / 狂暴等）"""
    return battle.mech_stacks.get(cond.get("mech", "arcane"), 0) >= cond.get("stacks", 3)


@register("player_buffed", label=lambda c: "自身有增益")
def _c_player_buffed(battle, player, cond):
    """自身有任意增益（v2.1：神圣狂热 / 风速）"""
    return bool(battle.p_buffs)


@register("player_untouched", label=lambda c: "本场未受击")
def _c_player_untouched(battle, player, cond):
    """本场未受击（v2.1：无伤精准 / 轻灵）"""
    return not getattr(battle, "_player_hit", False)


# ================= 速度类条件 =================

@register("player_first", label=lambda c: "先手行动")
def _c_player_first(battle, player, cond):
    """先手条件：速度高于目标（v2.0）"""
    pst = battle._player_stats(player)
    est = battle._enemy_stats()
    return pst.get("spd", 0) > est.get("spd", 0)


@register("speed_ratio", label=lambda c: f"速度比≥{c.get('ratio',1.5)}x")
def _c_speed_ratio(battle, player, cond):
    """速度比 ≥ ratio（v2.1：疾风连击 / 极速压制）"""
    pst = battle._player_stats(player)
    est = battle._enemy_stats()
    espd = est.get("spd", 0)
    return espd > 0 and pst.get("spd", 0) / espd >= cond.get("ratio", 1.5)
