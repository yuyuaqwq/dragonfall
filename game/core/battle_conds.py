# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - battle_conds.py（v98.4：战斗伤害条件注册表）

消灭 game/battle.py Battle._cond_mult() 里的 if-elif 硬编码（22 分支）：
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
    """敌方中毒层数 ≥ stacks（默认 3）；毒层已迁到目标级 enemy["debuffs"]["poison"]"""
    return (int(((battle.enemy.get("debuffs") or {}).get("poison", {}) or {}).get("n", 0) or 0)
            >= cond.get("stacks", 3))


@register("enemy_shaken_gt", label=lambda c: "敌方破绽/震慑中")
def _c_enemy_shaken_gt(battle, player, cond):
    """敌方破绽（shaken 挂敌身条）处于触发态（val=0 且 trigger_count>0 且免疫期内 = 被震慑中）。

    v139 拳师/淬势者：破绽条触发 = 敌方跳过回合（被晕），trigger_count>0 表示触发过、
    immune_turns>0 表示仍在免疫窗口（即刚被震慑）。stacks 参数保留兼容（默认 0）。
    """
    bs = (battle.enemy.get("buffs") or {}).get("shaken")
    if not isinstance(bs, dict):
        return False
    return int(bs.get("trigger_count", 0) or 0) > 0 and int(bs.get("immune_turns", 0) or 0) > 0


@register("player_rage_form", label=lambda c: "狂暴形态中")
def _c_player_rage_form(battle, player, cond):
    """v139 狂战士：是否处于狂暴形态（dual_form alt 态，怒斩等狂暴门槛技联动）。"""
    from .battle_modes import dual_form_active
    return dual_form_active(player)


@register("player_stance", label=lambda c: "守护姿态生效")
def _c_player_stance(battle, player, cond):
    """v139 盾卫士：是否处于守护姿态（p_buffs 姿态标记或已学守护姿态）。"""
    return bool(battle.p_buffs.get("stance") or battle.p_buffs.get("guard_stance"))


@register("player_combo_stacks", label=lambda c: f"链值≥{c.get('stacks', 3)}")
def _c_player_combo_stacks(battle, player, cond):
    """v139 刺客攻线：链值（combo mech_stacks）≥ stacks（默认 3）。"""
    return int(battle.mech_stacks.get("combo", 0) or 0) >= cond.get("stacks", 3)


@register("enemy_marked", label=lambda c: "敌方被标记")
def _c_enemy_marked(battle, player, cond):
    """敌方被标记（e_buffs 或目标级 debuffs 机制层任一）"""
    return "mark" in battle.e_buffs or int(((battle.enemy.get("debuffs") or {}).get("mark", {}) or {}).get("n", 0) or 0) > 0


@register("enemy_debuff", label=lambda c: "敌方有减益")
def _c_enemy_debuff(battle, player, cond):
    """敌方有减益（e_buffs 控制/属性降或目标级毒/灼烧/印记层）"""
    debuff_keys = ("def_down", "spd_down", "mon_atk_down", "atk_down",
                   "stun", "freeze", "silence")
    if any(k in battle.e_buffs for k in debuff_keys):
        return True
    debuffs = battle.enemy.get("debuffs") or {}
    return any(int((debuffs.get(k) or {}).get("n", 0) or 0) > 0
               for k in ("poison", "burn", "mark", "bleed"))


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
    # v130.2f 修复：条件基于施放前快照评估（HC-12 快照语义）——消耗型技能（res_cost/consume_all）扣费后
    # 资源回落导致「满资源档」cond 永不触发（时停领域-3 满5、流星陨落-5 满5、龙焰吐息-5 满10 同病，
    # 既有先例裂地斩 rage≥8/圣光惩击 faith≥8/疾风拳 chi≥5 一并修复）。施放前快照 _pre_cost_res 由
    # _cast_player_skill 在扣费前写入（battle.py:1849）；非施放语境（外部直接调 cond）回落当前值。
    pres = getattr(battle, "_pre_cost_res", None)
    val = pres.get(rk) if pres is not None else battle.resources.get(rk, 0)
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


# ================= 连招类条件（v130.6 变招引擎） =================
@register("player_combo", label=lambda c: f"上一招·{c.get('last', '连招中')}")
def _c_player_combo(battle, player, cond):
    """连招上下文判定（v130.6 变招/派生通用条件）：
    last=<tag>：上一招连招 tag 为指定值（拳/踢/掌；三连触发清空序列后仍记忆）
    无参数：当前连招进行中（combo_seq 非空，如格斗术「连招期间」类判定）
    """
    last = cond.get("last")
    if last:
        return getattr(battle, "last_combo_tag", None) == last
    return bool(getattr(battle, "combo_seq", None))

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


# ================= 被动条件注册表（v1.x：PASSIVE_COND_CHECKS） =================

# 被动技能 passive.cond 判定统一走本注册表（原 battle.py 三处 if/elif 硬编码）：
#   - _player_stats 属性被动（rage>=5 / hp_low_50 / hp_high_70 / battle_start）
#   - _player_skill 伤害倍率被动（dual_stat）
#   - _damage_player 减伤被动（hp_low_30：条件不满足则跳过减伤）
# 签名：fn(battle, player, ps) -> bool（ps=被动 dict，含 cond/stat/mult/reduce 等），
# 返回该条件是否满足。新增被动条件 = 一处注册 + skills.py 数据声明，battle.py 零改动。
PASSIVE_COND_CHECKS = {}


def register_passive_cond(key):
    """被动条件注册装饰器。"""
    def deco(fn):
        PASSIVE_COND_CHECKS[key] = fn
        return fn
    return deco


def passive_cond_ok(battle, player, ps, default=True):
    """被动条件判定（battle.py 消费入口）：
    - ps 无 cond → default
    - cond 已注册 → 按注册表 handler 判定
    - cond 未知 → default（防御：未知条件不改变旧行为）
    """
    cond = ps.get("cond")
    if not cond:
        return default
    fn = PASSIVE_COND_CHECKS.get(cond)
    if fn is None:
        return default
    return fn(battle, player, ps)


@register_passive_cond("rage>=5")
def _pc_rage_ge5(battle, player, ps):
    """怒气 ≥ 5（战意高涨）"""
    return (battle.resources.get("rage", 0) or 0) >= 5


@register_passive_cond("hp_low_50")
def _pc_hp_low_50(battle, player, ps):
    """生命低于 50%（死战）"""
    return player.get("hp", 0) / max(1, player.get("max_hp", 1)) < 0.5


@register_passive_cond("hp_high_70")
def _pc_hp_high_70(battle, player, ps):
    """生命高于 70%（钢铁壁垒/厚土）"""
    return player.get("hp", 0) / max(1, player.get("max_hp", 1)) >= 0.7


@register_passive_cond("battle_start")
def _pc_battle_start(battle, player, ps):
    """战斗开始（首轮，战争咆哮）。v152 时刻制：round 删除，用 _tick_no()（行动轮次）<= 1。"""
    try:
        return battle._tick_no() <= 1
    except Exception:
        return True


@register_passive_cond("hp_low_30")
def _pc_hp_low_30(battle, player, ps):
    """生命低于 30%（磐石之躯减伤）"""
    return player.get("hp", 0) / max(1, player.get("max_hp", 1)) < 0.30


@register_passive_cond("dual_stat")
def _pc_dual_stat(battle, player, ps):
    """力量/智力同时提升（atk 与 matk 均 > 0，双修精通）"""
    st = battle._player_stats(player)
    return bool(st.get("atk")) and bool(st.get("matk"))


# 属性被动（_player_stats stat 加成）可消费的条件键白名单：
# dual_stat（伤害倍率被动，_player_skill 消费）与 hp_low_30（受击减伤被动，
# _damage_player 消费）由各自站点消费，不在 _player_stats 的 stat 循环内判定
# （dual_stat 的 handler 内部会再调 _player_stats，若在此循环内求值将无限递归）。
PASSIVE_COND_STAT_KEYS = frozenset(("rage>=5", "hp_low_50", "hp_high_70", "battle_start"))

