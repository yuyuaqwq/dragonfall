# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心引擎 —— 属性/战斗/掉落/升级/任务"""
import random

from . import content as C
from .data.battle_config import ELEMENT_REACTIONS  # v125.2 B1：元素反应表下沉数据层（对外接口不变）


# ============================================================
# 角色属性
# ============================================================
# 转职成长加成（tier 0-3 → 0/15%/30%/50%）
TIER_GROWTH = {0: 1.0, 1: 1.15, 2: 1.30, 3: 1.50}
# v25 转职分支属性倾向（左=攻击/速度，右=防御/生命）
# v156 职业×分支差异化（计划 §3）：每职业攻线/守线独立加成；
# 旧结构 {1:..., 2:...} 作为默认回退（未配置职业用通用档，向后兼容）
BRANCH_BONUS = {
    1: {"atk": 1.06, "spd": 1.04},   # 左：进攻路线（默认回退）
    2: {"def": 1.08, "hp": 1.06},    # 右：防御路线（默认回退）
}
# v156 职业×分支差异化表（计划 §3 权威）：class_name → {evolve_path: {属性: 倍率}}
# key 用职业 ID（cls_zhan_shi 等，与 C.CLASSES 一致）；中文名会在查询处 resolve 成 ID
BRANCH_BONUS_BY_CLASS = {
    "cls_zhan_shi": {
        1: {"atk": 1.10, "spd": 1.04, "hp": 0.95},   # 狂战士：攻高但血少
        2: {"def": 1.14, "hp": 1.10, "atk": 0.95},   # 盾卫士：防高但攻低
    },
    "cls_fa_shi": {
        1: {"matk": 1.12, "hp": 0.92},   # 元素使：魔攻高但脆
        2: {"matk": 1.08, "mp": 1.10},   # 奥术学者：魔攻+蓝量
    },
    "cls_you_xia": {
        1: {"atk": 1.10, "spd": 1.06},   # 森语者
        2: {"spd": 1.12, "atk": 1.06},   # 风行者
    },
    "cls_mu_shi": {
        1: {"matk": 1.12, "hp": 0.95},   # 死灵祭司
        2: {"matk": 1.06, "mdef": 1.10}, # 神谕者
    },
    "cls_ci_ke": {
        1: {"atk": 1.12, "crit": 0.04},  # 影舞者
        2: {"atk": 1.08, "hp": 1.04},    # 毒刃者
    },
    "cls_wu_seng": {
        1: {"atk": 1.10, "spd": 1.04},   # 格斗士
        2: {"def": 1.12, "hp": 1.10, "atk": 0.95},  # 磐石行者
    },
    "cls_shi_ren": {
        1: {"matk": 1.08, "mp": 1.10},   # 咏叹者
        2: {"matk": 1.08, "hp": 1.06},   # 挽歌者
    },
}


# 元素亲和可切换的系（法师）
ELEMENT_OPTIONS = ["fire", "ice", "thunder"]
ELEMENT_CN = {"fire": "火", "ice": "冰", "thunder": "雷"}
# 元素印记 key（存敌方 e_buffs，层数）
ELEMENT_MARKS = {"fire": "fire_mark", "ice": "ice_mark", "thunder": "thunder_mark"}

# ============================================================
# v2.0 元素反应（12 章 3.1，严格按策划案表）——定义见 data/battle_config.py
# 当前系 × 目标印记 → 反应：蒸发 / 超载 / 冻结（预留，法师暂无水系技能）/ 感电
# ============================================================
# （ELEMENT_REACTIONS 表本体 v125.2 B1 已下沉 data/battle_config.py，顶部 import 保持对外接口）


def element_reaction(cur_element: str, target_marks: dict) -> dict | None:
    """判定元素反应。
    cur_element: 当前系 fire/ice/thunder
    target_marks: 敌方印记 dict（key 见 ELEMENT_MARKS，值为层数）
    返回反应 dict 或 None：{"name", "mult", "clear", "extra"}
    """
    for mark_key, layers in target_marks.items():
        if layers and layers > 0:
            r = ELEMENT_REACTIONS.get((cur_element, mark_key))
            if r:
                return r
    return None


def element_mark_apply(target_marks: dict, element: str, layers: int = 1, max_layers: int = 5) -> dict:
    """给目标挂元素印记(带上限)。返回更新后的印记 dict。"""
    mark_key = ELEMENT_MARKS.get(element, "")
    if not mark_key:
        return target_marks
    target_marks[mark_key] = min(max_layers, target_marks.get(mark_key, 0) + layers)
    return target_marks


def core_resource_def(class_name: str) -> dict:
    """职业核心资源定义(v48：中文或 ID → ID)。无定义返回 {}。"""
    cls_id = C.resolve("classes", class_name) if class_name else ""
    return C.CORE_RESOURCES.get(cls_id, {})


def core_resource_def_by_key(res_key: str) -> dict:
    """按资源 key 直接查核心资源定义（v130.2 副资源：共鸣/回声等按 key 注册，
    非 class id，core_resource_def 按 class 查不到——歌者双资源/分支级 resource_override 用）。"""
    if not res_key:
        return {}
    return C.CORE_RESOURCES.get(res_key, {})


def core_resource_gain_key(res_key: str, resources: dict, amount: int) -> int:
    """按资源 key 直接增加副资源（v130.2：res_gain 副资源 key 支持，歌者共鸣/回声等）。
    返回新值。未配置上限/未定义的资源不限制（同 core_resource_gain 语义）。"""
    rd = core_resource_def_by_key(res_key)
    if not rd:
        return resources.get(res_key, 0)
    cap = rd.get("max", 99)
    return min(cap, resources.get(res_key, 0) + amount)


def core_resource_gain(class_name: str, resources: dict, amount: int, key: str = "") -> int:
    """核心资源增加（带上限）。resources 是战斗内资源 dict（Battle 实例持有）。
    返回新值。未配置上限/未定义的资源不限制。
    """
    rd = core_resource_def(class_name)
    if not rd:
        return resources.get(key, 0)
    k = key or rd["key"]
    cap = rd.get("max", 99)
    return min(cap, resources.get(k, 0) + amount)


def core_resource_spend(class_name: str, resources: dict, amount: int, key: str = "") -> bool:
    """核心资源消耗。返回是否足够并扣除。不足则不扣返回 False。"""
    rd = core_resource_def(class_name)
    if not rd:
        return True
    k = key or rd["key"]
    cur = resources.get(k, 0)
    if cur < amount:
        return False
    resources[k] = cur - amount
    return True


def core_resource_regen(class_name: str, resources: dict) -> int:
    """刻开始核心资源回复(如游侠精力＋25)。返回新值。"""
    rd = core_resource_def(class_name)
    if not rd:
        return resources.get(rd.get("key", ""), 0)
    k = rd["key"]
    regen = rd.get("regen", 0)
    if regen <= 0:
        return resources.get(k, 0)
    return min(rd["max"], resources.get(k, 0) + regen)

# ============================================================
# v59 叠层上限（防数值爆炸：一场战斗叠 25 层金身=无敌、灼烧 10 层=烧死 Boss）
# 层数封顶后依然能用爆发技能一次性清空，只是限制无限滚雪球。
# ============================================================
MECH_STACK_MAX = {
    "burn": 5,     # 灼烧：5 层 = 每刻 15% 生命（结算后逐层衰减消散）
    "poison": 5,   # 毒层：5 层 = 每刻 25% 生命（结算后逐层衰减消散）
    "rage": 5,     # 狂暴：5 层 = +60% 伤害
    "shadow": 5,   # 影袭：5 层 = +60% 伤害
    "chi": 5,      # 气力：5 点 = +60% 伤害
    "judge": 5,    # 审判：5 层 = +75% 伤害
    "mark": 5,     # 标记：5 层 = +100% 伤害
    "wind": 3,     # 风印：3 层 = 4 连击（再多连击刷屏）
    "iron": 5,     # 金身：5 层 = 减伤 20%
    "shield": 5,   # 圣盾：5 层减伤
    "bless": 10,   # 神恩：10 层护盾
    "arcane": 5,   # 奥术充能：5 层（共鸣爆发前置，叠满 5 层=每层 +15% 爆发）
    "spellblade": 5,  # v87 魔剑士·魔能：5 层（叠层→爆发节奏）
    "zhan_yi": 10,    # v151 战士战意：0-10 叠层（持有即生效，从不消耗）
    "lian_duan": 10,  # v151 刺客连段：0-10 命中计数（miss/闪避归零）
}


def mech_stack_gain(mech: str, p_mech: dict, mval: int) -> int:
    """叠层(带上限)。返回新层数。未配上限的机制不限制。"""
    cap = MECH_STACK_MAX.get(mech, 99)
    return min(cap, p_mech.get(mech, 0) + mval)

def player_base_stats(class_name: str, level: int, tier: int = 0, evolve_path: int = 0, race: str = None) -> dict:
    """职业基础 + 等级成长（含转职成长加成 + v25 分支属性倾向）
    阶段九：race 种族天赋（凡人之躯 growth_mult 只影响基础成长）"""
    class_name = C.resolve("classes", class_name)  # v48：中文或 ID → ID
    cls = C.CLASSES.get(class_name)
    if cls is None:
        # v105 P1(M01#6)：未知/脏 class_name 兜底——脏档/职业迁移改名后全属性链路不崩
        # （原先直接 KeyError，player_base_stats 是面板/战斗/升级的公共入口）
        cls = C.CLASSES.get(C.CLASS_NOVICE)
        if cls is None:
            raise ValueError(f"未知职业 class_name={class_name!r}，且见习兜底职业缺失")
    base = dict(cls["base"])
    growth = cls["growth"]
    mult = TIER_GROWTH.get(tier, 1.0)
    # 阶段九：种族成长倍率（08 章人类凡人之躯 -2%）
    rmult = race_stats(race).get("growth_mult", 1.0) if race else 1.0
    for k in ("hp", "mp", "atk", "def", "matk", "mdef", "spd"):
        base[k] = int(base[k] + growth[k] * (level - 1) * mult * rmult)
    # v25 分支属性倾向（选择转职分支后生效）
    # v156 职业×分支差异化：优先用职业表（BRANCH_BONUS_BY_CLASS），未配置职业回退通用档
    if evolve_path:
        bb = BRANCH_BONUS_BY_CLASS.get(class_name, BRANCH_BONUS).get(evolve_path, BRANCH_BONUS.get(evolve_path, {}))
        for k, v in bb.items():
            if k == "hp":
                base["hp"] = int(base["hp"] * v)
            elif k == "mp":
                base["mp"] = int(base["mp"] * v)
            elif k == "crit":
                base["crit"] = round(base.get("crit", 0) + v, 3)  # crit 是加法（百分比）
            else:
                base[k] = int(base[k] * v)
    base["max_hp"] = base["hp"]
    base["max_mp"] = base["mp"]
    return base


def race_stats(race: str | None) -> dict:
    """种族天赋表(08 章)。未知/空种族返回空 dict(无天赋，向后兼容)。"""
    if not race:
        return {}
    info = C.RACES.get(race) or {}
    return info.get("talents") or {}


def race_name(race: str | None) -> str:
    """种族显示名(未知返回空串，兼容旧档无 race 字段)"""
    if not race:
        return ""
    return (C.RACES.get(race) or {}).get("name", "")


def player_final_stats(class_name: str, level: int, equipment: dict, tier: int = 0, attributes: dict = None, evolve_path: int = 0, title_bonus: dict = None, race: str = None, learned_skills: list | None = None) -> dict:
    """基础属性 + 装备加成(含强化增幅)+ 自由属性点加成 + 称号加成 + 种族天赋 + 已学属性被动(v110.4 X2)
    传 learned_skills 时并入属性被动(面板)；battle.py _player_stats 不传 → 不含 passive，由战斗侧自理
    """
    st, _ = player_stats_detail(class_name, level, equipment, tier, attributes, evolve_path, title_bonus, race, learned_skills)
    return st


# ---------------- 被动技能（v64） ----------------
# 属性型被动：stat -> 修正属性；返回 dict 与 player_final_stats 相同键（max_hp/max_mp/atk/...）
# 被动 stat → (bonus_key, 操作, 需 cond is None)
# 不在表内的 stat：条件型(rage>=5/battle_start/dual_stat) 与战斗内机制(chi_gain/proc 型) 由 battle.py 结算，面板不处理
# （v109.2：dual_stat 双修精通在 battle.py:1582 按 cond 查，fire 已改 proc fire_bonus）
_PASSIVE_STAT_APPLY = {
    "mp":   ("mp_mult", "mul", True),   # 原代码特判：mp 仅在无 cond 时结算
    "spd":  ("spd_mult", "mul", False),
    "crit": ("crit_add", "add", False),
    # v106.1：冷却缩减被动支持（面板结算 + 战斗内 _set_skill_cd 消费）
    "cdr":  ("cdr_add", "add", False),
    # v106.2：穿透被动支持（战斗内乘算合成，职业特色渠道）
    "pene_phys": ("pene_phys_add", "add", False),
    "pene_magi": ("pene_magi_add", "add", False),
    # v106.3：吸血/暴击伤害/格挡被动支持（面板结算 + 战斗内消费）
    "lifesteal": ("lifesteal_add", "add", False),
    "crit_dmg": ("crit_dmg_add", "add", False),
    "block": ("block_add", "add", False),
    # v106.4：反伤/物魔免/物法吸被动支持
    "thorns": ("thorns_add", "add", False),
    "phys_reduce": ("phys_reduce_add", "add", False),
    "magic_reduce": ("magic_reduce_add", "add", False),
    "lifesteal_phys": ("lifesteal_phys_add", "add", False),
    "lifesteal_magi": ("lifesteal_magi_add", "add", False),
    # v107 隐藏职业专属属性被动支持（面板结算 + 战斗内消费）
    # v109.2 清理：shield_power/abyss_res 无对应被动技能（skills.py 零使用），
    # 保留 elem_res/luck/summon_power（龙魂/星辰之力/万兽之力，P0-2 已实装）
    "elem_res": ("elem_res_add", "add", False),
    "luck": ("luck_add", "add", False),
    "summon_power": ("summon_power_add", "add", False),
    # v113.1 修复：时咒线依赖的 heal_power（牧师一转觉醒被动「圣光祝福」）与
    # dodge（游侠一转觉醒被动「风之加护」）此前无映射 → 觉醒被动完全无效。
    "heal_power": ("heal_power_add", "add", False),
    "dodge": ("dodge_add", "add", False),
    # v134.1 意见#45：速度→暴击转化被动（游侠/刺客"疾风之眼"）——spd_crit 系数含义：
    #   每点速度 +0.001×mult 暴击（mult=0.1 → 每10点速度+1%），受 PCT_CAPS.crit 0.5 约束
    "spd_crit": ("spd_crit_add", "add", False),
}


def player_passive_stats(class_name: str, learned_skills: list | None = None) -> dict:
    """计算已学被动技能的属性加成（v64 被动系统）。

    被动技能 kind="被动"，passive 字段结构：
      {"stat": "atk", "mult": 0.15}             属性百分比加成（atk/def/matk/mdef/spd/mp/crit）
      {"stat": "atk", "cond": "rage>=5", ...}   条件型属性（暂不结算数值，战斗内按条件处理）
      {"stat": "chi_gain", "mult": 1}           气获取 +1（战斗内处理）
      {"stat": "fire", "mult": 0.10}            火系增伤（战斗内处理）
      其他 proc 型被动不在属性结算里，由 battle.py 处理
    返回属性加成 dict（百分比已转成系数 1+mult 形式，由调用方决定如何乘）。
    """
    bonus = {"hp_mult": 1.0, "mp_mult": 1.0, "atk_mult": 1.0, "def_mult": 1.0,
             "matk_mult": 1.0, "mdef_mult": 1.0, "spd_mult": 1.0, "crit_add": 0.0,
             "cdr_add": 0.0,  # v106.1 cdr 被动
             "pene_phys_add": 0.0, "pene_magi_add": 0.0,  # v106.2 穿透被动
             "lifesteal_add": 0.0, "crit_dmg_add": 0.0, "block_add": 0.0,  # v106.3 吸血/暴伤/格挡被动
             "thorns_add": 0.0, "phys_reduce_add": 0.0, "magic_reduce_add": 0.0,
             "lifesteal_phys_add": 0.0, "lifesteal_magi_add": 0.0,
             # v110.4 X2 P1-2：shield_power/abyss_res 无对应被动技能(skills.py 零使用)，
             # 恒 0 死键删除——battle.py:916-918 的读 pb.get(...,0.0) 恒 0 死循环由 X1 处理。
             # v113.1：恢复 heal_power_add/dodge_add（圣光祝福/风之加护 觉醒被动消费）
             "elem_res_add": 0.0, "luck_add": 0.0, "summon_power_add": 0.0,
             "heal_power_add": 0.0, "dodge_add": 0.0,
             "spd_crit_add": 0.0}  # v134.1 意见#45：速度→暴击被动（游侠/刺客"疾风之眼"）
    learned = [C.display("skills", s) for s in (learned_skills or []) if s]
    for name in learned:
        info = skill_info(class_name, name)
        if not info or info.get("kind") != "被动":
            continue
        ps = info.get("passive") or {}
        rule = _PASSIVE_STAT_APPLY.get(ps.get("stat"))
        if rule is None:
            continue  # 条件型/战斗内机制 stat 由 battle.py 结算（原 if-elif 无分支，行为一致）
        key, op, need_cond_none = rule
        if need_cond_none and ps.get("cond") is not None:
            continue
        mult = float(ps.get("add", ps.get("mult", 0)))
        if op == "mul":
            bonus[key] *= (1 + mult)
        else:  # add（crit/cdr）
            bonus[key] += mult
    return bonus


def apply_passive_to_stats(st: dict, class_name: str, learned_skills: list | None) -> dict:
    """v110.4 X2 P1-2：把已学属性被动结算进属性 dict。

    与 battle.py:886-920 完全同键同 cap（mp/spd 乘算、crit 加算 cap0.6、
    cdr 加算 cap0.4、穿透乘算 cap0.6、其余加法并入 cap= C.PCT_CAPS），
    保证面板(player_stats_detail) == 战斗(_player_stats) 单一来源。
    条件型被动（cond rage>=5/hp_low_50 等）战斗内动态结算，此处不处理。
    """
    pb = player_passive_stats(class_name, learned_skills)
    if pb.get("mp_mult", 1.0) != 1.0:
        st["max_mp"] = int(st.get("max_mp", 0) * pb["mp_mult"])
        st["mp"] = int(st.get("mp", 0) * pb["mp_mult"])
    if pb.get("spd_mult", 1.0) != 1.0:
        st["spd"] = int(st.get("spd", 0) * pb["spd_mult"])
    if pb.get("crit_add", 0.0):
        # v110 §三：暴击率上限统一 0.5（PCT_CAPS 权威；原 0.6 与 buff 1.0 不一致）
        st["crit"] = min(st.get("crit", 0) + pb["crit_add"], C.PCT_CAPS.get("crit", 0.5))
    # v134.1 意见#45：速度→暴击转化（游侠/刺客"疾风之眼"）——每点速度 +0.001×mult 暴击
    #   mult=0.1 → 每 10 点速度 +1%；须在 spd_mult 应用后折算，受 PCT_CAPS.crit 0.5 约束
    if pb.get("spd_crit_add", 0.0):
        spd_crit = st.get("spd", 0) * 0.001 * pb["spd_crit_add"]
        st["crit"] = min(st.get("crit", 0) + spd_crit, C.PCT_CAPS.get("crit", 0.5))
    if pb.get("cdr_add", 0.0):
        st["cdr"] = min(st.get("cdr", 0) + pb["cdr_add"], 0.4)
    if pb.get("pene_phys_add", 0.0):
        st["pene_phys"] = min(1 - (1 - st.get("pene_phys", 0)) * (1 - pb["pene_phys_add"]), 0.6)
    if pb.get("pene_magi_add", 0.0):
        st["pene_magi"] = min(1 - (1 - st.get("pene_magi", 0)) * (1 - pb["pene_magi_add"]), 0.6)
    for _pk, _pv in (("lifesteal_add", "lifesteal"), ("crit_dmg_add", "crit_dmg"),
                     ("block_add", "block")):
        if pb.get(_pk, 0.0):
            st[_pv] = min(st.get(_pv, 0) + pb[_pk], C.PCT_CAPS.get(_pv, 0.6))
    for _pk, _pv in (("thorns_add", "thorns"), ("phys_reduce_add", "phys_reduce"),
                     ("magic_reduce_add", "magic_reduce"),
                     ("lifesteal_phys_add", "lifesteal_phys"),
                     ("lifesteal_magi_add", "lifesteal_magi")):
        if pb.get(_pk, 0.0):
            st[_pv] = min(st.get(_pv, 0) + pb[_pk], C.PCT_CAPS.get(_pv, 0.6))
    # v107 隐藏职业专属属性被动（龙魂/星辰之力/万兽之力；shield_power/abyss_res 无技能，已删）
    for _pk, _pv in (("elem_res_add", "elem_res"), ("luck_add", "luck"),
                     ("summon_power_add", "summon_power")):
        if pb.get(_pk, 0.0):
            st[_pv] = min(st.get(_pv, 0) + pb[_pk], C.PCT_CAPS.get(_pv, 0.6))
    # v113.1 觉醒被动：heal_power（圣光祝福 /+）与 dodge（风之加护 /+）加法并入，
    # 同 cap 权威（heal_power 0.5，dodge 0.4 见 core/constants.py PCT_CAPS）
    for _pk, _pv in (("heal_power_add", "heal_power"), ("dodge_add", "dodge")):
        if pb.get(_pk, 0.0):
            st[_pv] = min(st.get(_pv, 0) + pb[_pk], C.PCT_CAPS.get(_pv, 0.6))
    return st


def passive_skills_learned(class_name: str, learned_skills: list | None = None) -> list:
    """返回已学被动技能的中文名列表(v64)。battle.py 用它查触发型被动。"""
    learned = [C.display("skills", s) for s in (learned_skills or []) if s]
    out = []
    for name in learned:
        info = skill_info(class_name, name)
        if info and info.get("kind") == "被动":
            out.append(name)
    return out


def is_passive_learned(class_name: str, passive_name: str, learned_skills: list | None = None) -> bool:
    """指定被动是否已学(v64)。passive_name 为被动技能中文名。"""
    return passive_name in passive_skills_learned(class_name, learned_skills)

# 属性中文名（面板/来源展示用）
STAT_NAMES = {"hp": "生命", "mp": "魔力", "atk": "攻击", "def": "防御", "matk": "魔攻",
              "mdef": "魔防", "spd": "速度", "crit": "暴击", "dodge": "闪避", "precise": "精准",
              "pene_phys": "物穿", "pene_magi": "法穿", "pene_flat": "固定物穿", "pene_mflat": "固定法穿",
              "tenacity": "韧性", "luck": "幸运",  # v106 穿透/韧性/幸运
              "cdr": "冷却缩减", "elem_res": "元素抗性", "abyss_res": "深渊抗性",
              "exp_bonus": "经验加成", "gold_bonus": "金币加成",  # v106.1 冷却/抗性/成长
              "heal_power": "治疗强度", "shield_power": "护盾强度",
              "lifesteal": "吸血", "crit_dmg": "暴击伤害", "block": "格挡",
              "thorns": "反伤", "phys_reduce": "物免", "magic_reduce": "魔免",
              "lifesteal_phys": "物吸", "lifesteal_magi": "法吸",
              "summon_power": "召唤强化"}  # v106.3/v106.4 + v107 召唤


def player_stats_detail(class_name: str, level: int, equipment: dict, tier: int = 0, attributes: dict = None, evolve_path: int = 0, title_bonus: dict = None, race: str = None, learned_skills: list | None = None) -> tuple:
    """拆解属性来源。返回 (最终属性 dict, 来源明细 list)。

    来源明细每项: {"name": 来源名, "stats": {属性: 加值}}。
    与 player_final_stats 共用同一套计算（最终属性完全一致），保证面板显示和实际战斗一致。
    """
    sources = []
    # 1. 基础（职业 + 等级成长 + 转职加成 + v25 分支倾向 + 种族成长倍率）
    st = player_base_stats(class_name, level, tier, evolve_path, race)
    base_src = {"hp": st["max_hp"], "mp": st["max_mp"]}
    for k in ("atk", "def", "matk", "mdef", "spd"):
        base_src[k] = st[k]
    # v55.1：暴击/闪避基础值也进来源（属性面板显示完整构成）
    base_src["crit"] = st.get("crit", 0)
    base_src["dodge"] = st.get("dodge", 0)
    # v106：穿透/韧性/幸运基础值也进来源（职业天生特色如刺客 10% 物穿）
    base_src["pene_phys"] = st.get("pene_phys", 0)
    base_src["pene_magi"] = st.get("pene_magi", 0)
    base_src["pene_flat"] = st.get("pene_flat", 0)
    base_src["pene_mflat"] = st.get("pene_mflat", 0)
    base_src["tenacity"] = st.get("tenacity", 0)
    base_src["luck"] = st.get("luck", 0)
    # v106.1：冷却缩减/元素抗性/深渊抗性/经验金币加成基础值也进来源（职业天生特色）
    base_src["cdr"] = st.get("cdr", 0)
    base_src["elem_res"] = st.get("elem_res", 0)
    base_src["abyss_res"] = st.get("abyss_res", 0)
    base_src["exp_bonus"] = st.get("exp_bonus", 0)
    base_src["gold_bonus"] = st.get("gold_bonus", 0)
    # v106.2：治疗强度/护盾强度基础值也进来源（职业天生特色）
    base_src["heal_power"] = st.get("heal_power", 0)
    base_src["shield_power"] = st.get("shield_power", 0)
    sources.append({"name": "基础", "stats": base_src})
    # 2. 自由属性点：力量→攻击 敏捷→速度/暴击 智力→魔攻/魔力 耐力→生命
    # v105 P1(M01#7)：attributes 可能是字符串/'null'（脏档）→ 非 dict 一律按空处理
    attr = attributes if isinstance(attributes, dict) else {}
    attr_src = {}
    # v136 数值重构（鱼鱼拍板 C）：属性点转化率回归合理值，降基础属性虚高
    # str→atk 1.2→1.0（1点力量=1攻击）、int→matk 1.2→1.0、vit→hp 8→6
    # 原 1.2 导致裸装主属性堆叠收益高于装备，玩家无脑全投主属性，装备系统失去意义
    attr_src["atk"] = int(attr.get("str", 0) * 1.0)
    attr_src["matk"] = int(attr.get("int", 0) * 1.0)
    attr_src["spd"] = int(attr.get("agi", 0) * 0.8)
    attr_src["crit"] = attr.get("agi", 0) * 0.004
    attr_src["hp"] = int(attr.get("vit", 0) * 6)
    attr_src["mp"] = int(attr.get("int", 0) * 1.5)
    st["atk"] += attr_src["atk"]
    st["matk"] += attr_src["matk"]
    st["spd"] += attr_src["spd"]
    st["crit"] = min(st["crit"] + attr_src["crit"], 0.5)
    st["max_hp"] += attr_src["hp"]
    st["max_mp"] += attr_src["mp"]
    if any(attr_src.values()):
        sources.append({"name": "自由属性点", "stats": {k: v for k, v in attr_src.items() if v}})
    # 3. 装备（含强化增幅 + 词条 + 附魔，按装备逐件列出）
    for slot, item in equipment.items():
        if not item:
            continue
        enh = item.get("enhance", 0)
        mult = 1.0
        if enh > 0:
            info = C.ENHANCE_TABLE.get(enh)
            if info:
                mult = info["mult"]
        # v135 装备升级乘区（养装备）：与强化乘区相乘，稳定保底、不随换装沉没
        upg = item.get("upgrade_lv", 0)
        upg_mult = 1.0
        if upg > 0:
            uinfo = C.UPGRADE_TABLE.get(upg)
            if uinfo:
                upg_mult = uinfo["mult"]
        item_src = {}
        for k, v in item.get("stats", {}).items():
            if k in STAT_NAMES:
                # v101.21e 修复：PCT_STATS（crit/dodge）保留小数——原代码只特判 crit，
                # dodge 0.05 被 int() 截断成 0，装备闪避加成全部丢失
                item_src[k] = item_src.get(k, 0) + (int(v * mult * upg_mult) if k not in C.PCT_STATS else v * upg_mult)
        for af in item.get("affixes", []):
            # 阶段八：词条 v2 是 ID 列表（str），常驻属性已在生成时折算进 stats；
            # 旧结构 [{"stat","value"}] 兼容处理
            if isinstance(af, dict):
                k, v = af.get("stat"), af.get("value", 0)
                if k in STAT_NAMES:
                    item_src[k] = item_src.get(k, 0) + v
        for en in item.get("enchant", []):
            k, v = en.get("stat"), en.get("value", 0)
            if k in STAT_NAMES:
                item_src[k] = item_src.get(k, 0) + v
        # v136 原石系统：孔位里镶嵌的原石属性加成（stats 值=百分比/数值，直接加）
        # sockets: {孔位1: gem_dict, 孔位2: gem_dict, ...}，gem_dict 形如 {"stats": {"atk": 0.01}, ...}
        # 原石 stats 键全在 STAT_NAMES 面板属性内；百分比/数值统一直接加，
        # 后续 PENE_PCT_STATS/PCT_STATS 分支统一处理 cap（见下方汇总循环）
        for _gk, _gv in (item.get("sockets") or {}).items():
            if not isinstance(_gv, dict):
                continue
            for _sk, _sv in (_gv.get("stats") or {}).items():
                if _sk in STAT_NAMES:
                    item_src[_sk] = item_src.get(_sk, 0) + _sv
        # v136 怪异炼成：随机强化属性（calamity_bonus: {属性: 百分比}，每件限 3 次）
        # 与强化/升级乘区独立叠加，走 PCT_STATS cap（≤5% 小数值，机制向取舍）
        for _ck, _cv in (item.get("calamity_bonus") or {}).items():
            if _ck in STAT_NAMES and _cv:
                item_src[_ck] = item_src.get(_ck, 0) + _cv
        if item_src:
            enh_s = f"+{enh}" if enh > 0 else ""
            sources.append({"name": f"{item.get('name', slot)}{enh_s}", "stats": item_src})
    # 汇总装备加成到 st（与 player_final_stats 原逻辑一致；装备键 hp/mp → max_hp/max_mp）
    for src in sources:
        if src["name"] in ("基础", "自由属性点"):
            continue
        for k, v in src["stats"].items():
            if k in C.PENE_PCT_STATS:
                # v106：百分比穿透乘算合成 1-(1-a)(1-b)，不加法（职业/词条/被动多来源）
                st[k] = min(1 - (1 - st.get(k, 0)) * (1 - v), C.PCT_CAPS.get(k, 0.6))
            elif k in C.PCT_STATS:
                st[k] = min(st.get(k, 0) + v, C.PCT_CAPS.get(k, 0.6))
            elif k == "hp":
                st["max_hp"] += v
            elif k == "mp":
                st["max_mp"] += v
            else:
                st[k] += v
    # 4. 套装 2 件百分比加成（基于基础+属性点+装备的最终值）
    # v136 Phase6：传 class_name 实现职业套装折扣（本职业 100%/非本职业 60%）
    sb2 = set_bonus_2(equipment, class_name)
    if sb2:
        src2 = {}
        for k, v in sb2.items():
            if k in C.PENE_PCT_STATS:
                src2[k] = v
                st[k] = min(1 - (1 - st.get(k, 0)) * (1 - v), C.PCT_CAPS.get(k, 0.6))
            elif k in C.PCT_STATS:
                src2[k] = v
                st[k] = min(st.get(k, 0) + v, C.PCT_CAPS.get(k, 0.6))
            elif k == "hp":
                src2["hp"] = v
                st["max_hp"] = int(st["max_hp"] * (1 + v))
            elif k == "mp":
                src2["mp"] = v
                st["max_mp"] = int(st["max_mp"] * (1 + v))
            else:
                src2[k] = v
                # v110 审计修复：非 STAT 键（如旧圣光套 bonus_2.heal）不参与属性倍率，
                # 静默跳过防 KeyError 崩溃（特殊键由各自消费段读取）
                if k in st:
                    st[k] = int(st[k] * (1 + v))
        names2 = [s for s, c in active_sets(equipment).items() if c >= 2]
        sources.append({"name": f"套装2件({'/'.join(names2)})", "stats": src2, "pct": True})
    # 5. 套装 4 件属性型特效（常驻属性；数值读 sets.py bonus_4.stats，v126 数值下沉）
    # 按已激活(>=4 件)套装逐套应用各自 bonus_4.stats（同 eff 多套叠加语义与旧代码一致；
    # 无 stats 字段的特效型由战斗侧消费）
    eff_src = {}
    for sname, cnt in active_sets(equipment).items():
        if cnt < 4:
            continue
        _b4 = (_set_info(sname) or {}).get("bonus_4") or {}
        for k, v in (_b4.get("stats") or {}).items():
            if k == "mdef":
                eff_src["mdef"] = eff_src.get("mdef", 0) + v
                st["mdef"] = int(st["mdef"] * (1 + v))
            elif k == "crit":
                eff_src["crit"] = eff_src.get("crit", 0) + v
                st["crit"] = min(st["crit"] + v, 0.5)
            elif k == "dodge":
                eff_src["dodge"] = eff_src.get("dodge", 0) + v
                st["dodge"] = min(st["dodge"] + v, 0.4)
            else:
                eff_src[k] = eff_src.get(k, 0) + v
                st[k] = min(st.get(k, 0) + v, C.PCT_CAPS.get(k, 0.6))
    if eff_src:
        names4 = [s for s, c in active_sets(equipment).items() if c >= 4]
        sources.append({"name": f"套装4件({'/'.join(names4)})", "stats": eff_src, "pct": True})
    # 6. 副业大师称号加成（固定数值）
    if title_bonus:
        tb = {k: v for k, v in title_bonus.items() if k in STAT_NAMES and v}
        if tb:
            for k, v in tb.items():
                if k in C.PENE_PCT_STATS:
                    st[k] = min(1 - (1 - st.get(k, 0)) * (1 - v), C.PCT_CAPS.get(k, 0.6))
                elif k in C.PCT_STATS:
                    st[k] = min(st.get(k, 0) + v, C.PCT_CAPS.get(k, 0.6))
                elif k == "hp":
                    st["max_hp"] += int(v)
                elif k == "mp":
                    st["max_mp"] += int(v)
                else:
                    st[k] += int(v)
            sources.append({"name": "副业称号", "stats": tb})
    # 7. 种族天赋 stat 型（08 章：月缺 HP-5% / 磐石步履先手-5% / 月之优雅暴击+8% / 坚韧体魄 HP+8%）
    rt = race_stats(race)
    if rt:
        race_src = {}
        if rt.get("hp_mult", 1.0) != 1.0:
            race_src["hp"] = rt["hp_mult"]
            st["max_hp"] = int(st["max_hp"] * rt["hp_mult"])
        if rt.get("spd_mult", 1.0) != 1.0:
            race_src["spd"] = rt["spd_mult"]
            st["spd"] = int(st["spd"] * rt["spd_mult"])
        if rt.get("crit_add"):
            race_src["crit"] = rt["crit_add"]
            st["crit"] = min(st["crit"] + rt["crit_add"], 0.5)
        # v106.2：新属性种族天赋（exp_bonus/luck/elem_res/abyss_res/cdr 加法属性）
        for _rk in ("exp_bonus", "luck", "elem_res", "abyss_res", "cdr"):
            if rt.get(_rk):
                race_src[_rk] = rt[_rk]
                st[_rk] = min(st.get(_rk, 0) + rt[_rk], C.PCT_CAPS.get(_rk, 0.6))
        # v106.3：吸血/暴击伤害/格挡种族天赋（矮人岩壁格挡/精灵月华暴伤/兽人嗜血）
        for _rk in ("lifesteal", "crit_dmg", "block"):
            if rt.get(_rk):
                race_src[_rk] = rt[_rk]
                st[_rk] = min(st.get(_rk, 0) + rt[_rk], C.PCT_CAPS.get(_rk, 0.6))
        # v106.4：反伤/物魔免种族天赋（石肤物免/龙鳞魔免/兽人鲁莽魔免负值已存在，统一聚合）
        for _rk in ("thorns", "phys_reduce", "magic_reduce", "lifesteal_phys", "lifesteal_magi"):
            if rt.get(_rk):
                race_src[_rk] = rt[_rk]
                st[_rk] = min(st.get(_rk, 0) + rt[_rk], C.PCT_CAPS.get(_rk, 0.6))
        if race_src:
            sources.append({"name": "种族天赋", "stats": race_src, "pct": True})
    # 8. 已学属性被动（v110.4 X2 P1-2：面板接入永久被动，与 battle.py:886-920 同键同 cap）
    # 条件型被动（cond rage>=5/hp_low_50/battle_start 等）战斗内动态结算，面板不处理
    if learned_skills:
        _before = dict(st)
        apply_passive_to_stats(st, class_name, learned_skills)
        ps = player_passive_stats(class_name, learned_skills)
        p_src = {}
        # mul 型（mp/spd）：以乘数形式进入来源；add 型：记录最终并入值
        if ps.get("mp_mult", 1.0) != 1.0:
            p_src["mp"] = ps["mp_mult"]
        if ps.get("spd_mult", 1.0) != 1.0:
            p_src["spd"] = ps["spd_mult"]
        for st_key in ("crit", "cdr", "pene_phys", "pene_magi", "lifesteal", "crit_dmg",
                       "block", "thorns", "phys_reduce", "magic_reduce", "lifesteal_phys",
                       "lifesteal_magi", "elem_res", "luck", "summon_power"):
            if st.get(st_key, 0) != _before.get(st_key, 0):  # 被动并入或 cap 收敛导致变化 → 记为来源
                p_src[st_key] = st.get(st_key, 0) - _before.get(st_key, 0)
        if p_src:
            sources.append({"name": "被动技能", "stats": p_src, "pct": True})
    return st, sources


# ---------------- v10 套装计算 ----------------
def active_sets(equipment: dict) -> dict:
    """返回 {套装名: 已穿件数}，只含 >=2 件的套装(2 件才有效果)"""
    counts = {}
    for slot, item in (equipment or {}).items():
        if not item:
            continue
        s = item.get("set")
        if s:
            counts[s] = counts.get(s, 0) + 1
    return {s: c for s, c in counts.items() if c >= 2}


def _set_info(set_name: str) -> dict | None:
    """按套装名(装备 set 字段，中文)查 SETS 条目(SETS key 是 set_xxx ID)"""
    if set_name in C.SETS:
        return C.SETS[set_name]
    for info in C.SETS.values():
        if info.get("name") == set_name:
            return info
    return None


def set_bonus_2(equipment: dict, class_name: str | None = None) -> dict:
    """汇总所有激活套装的 2 件百分比加成 {stat: 总和}
    阶段八：>=4 件时叠加 4 件属性加成（bonus_4_stats），>=5 件时叠加 5 件 stat 型效果（bonus_5.crit/dodge，10 章五节橡木/铁港）
    v130.2c 修复 P0：effect 型 bonus_2（资源联动 12 套，键含 effect/res/value/on/desc）不再按 stat 累加
    （旧实现 int+str TypeError 崩点）；整 dict 跳过交由战斗侧 _set_effs 消费，面板 sources 不再混入
    非数值键（P2 污染清理）。仅聚合数值型属性键，兼容 {"spd": 0.15} 旧属性型。
    v136 Phase6：职业套装职业折扣——套装 entry 带 "class" 字段（本职业专用）时，
    非本职业玩家（class_name != entry["class"]）属性加成 ×0.6（鱼鱼拍板：本职业 100%，非本职业 60%）。
    effect 型特效（bonus_4/bonus_5）不打折（机制向非面板向）。"""
    bonus = {}
    for sname, cnt in active_sets(equipment).items():
        info = _set_info(sname)
        if not info:
            continue
        # v136 Phase6 职业折扣：仅影响 stat 型加成（bonus_2/bonus_4_stats/bonus_5 数值键）
        _disc = 1.0
        _cls = info.get("class")
        if _cls and class_name and class_name != _cls:
            _disc = 0.6
        _b2 = info.get("bonus_2") or {}
        if "effect" not in _b2:
            for k, v in _b2.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    bonus[k] = bonus.get(k, 0) + v * _disc
        if cnt >= 3:
            # v136 审计：区域套 3 槽位（armor/legs/boots）只能凑 3 件，bonus_3 让 3 件套生效
            for k, v in info.get("bonus_3_stats", {}).items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    bonus[k] = bonus.get(k, 0) + v * _disc
            for k, v in info.get("bonus_3", {}).items():
                if k not in ("effect", "desc", "chance", "stats") and isinstance(v, (int, float)) and not isinstance(v, bool):
                    bonus[k] = bonus.get(k, 0) + v * _disc
        if cnt >= 4:
            for k, v in info.get("bonus_4_stats", {}).items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    bonus[k] = bonus.get(k, 0) + v * _disc
        if cnt >= 5:
            for k, v in info.get("bonus_5", {}).items():
                # 5 件 stat 型效果（crit/dodge 直接是属性）；desc/effect 型（战斗特效）不在这里结算
                if k in C.PCT_STATS and isinstance(v, (int, float)) and not isinstance(v, bool):
                    bonus[k] = bonus.get(k, 0) + v * _disc
    return bonus


def has_set(equipment: dict, set_name: str) -> bool:
    """装备是否穿戴了指定套装(10 章名册套装按套装名匹配)"""
    for item in (equipment or {}).values():
        if item and item.get("set") == set_name:
            return True
    return False


def set_bonus_4(equipment: dict) -> list:
    """返回已激活套装的 4 件特效效果名列表（v136 审计：区域套 3 槽位用 bonus_3 特效）"""
    effs = []
    for sname, cnt in active_sets(equipment).items():
        info = _set_info(sname)
        if info and cnt >= 4 and info.get("bonus_4", {}).get("effect"):
            effs.append(info["bonus_4"]["effect"])
        elif info and cnt >= 3 and info.get("bonus_3", {}).get("effect"):
            effs.append(info["bonus_3"]["effect"])
    return effs


# v48：职业/技能均用 ID 访问。表结构已变 {cls_id: {"name":.., "skills": {sk_id: def}}}
# 兼容 v48 前旧结构 {职业: {技能: def}} 的读取辅助。
def _sk_table(class_name: str) -> dict:
    class_name = C.resolve("classes", class_name)  # v48：统一转 ID
    t = C.PLAYER_SKILLS.get(class_name, {})
    if isinstance(t, dict) and "skills" in t:
        return t["skills"]
    return t

def _br_table(class_name: str) -> dict:
    class_name = C.resolve("classes", class_name)
    t = C.BRANCH_SKILLS.get(class_name, {})
    if isinstance(t, dict) and "branches" in t:
        return t["branches"]
    return t


def skills_for_level(class_name: str, level: int) -> list[str]:
    """返回该职业当前等级已解锁的技能 id"""
    skills = _sk_table(class_name)
    return [name for name, info in skills.items() if info["lv"] <= level]


def is_skill_learned(class_name: str, level: int, skill_name: str, learned_skills: list | None = None) -> bool:
    """技能是否已学会(v12：必须『技能学习』花技能点学会才能使用，不再按等级自动解锁)"""
    info = skill_info(class_name, skill_name)
    if not info:
        return False
    # v48：learned_skills 是中文名（store 读回），skill_name 可能是 ID——统一 resolve 比较
    sid = C.resolve("skills", skill_name)
    return sid in [C.resolve("skills", s) for s in (learned_skills or []) if s]


def skill_learn_cost(need_lv: int) -> int:
    """学习技能消耗的技能点(v12：按技能等级定价，等级越高越贵)
    v104 R3 P2-17：删除未使用的 level 死参数（原签名 level, need_lv 但成本只与 need_lv 挂钩）"""
    return need_lv // 6 + 2


def skill_learn_cost_for(player: dict, need_lv: int) -> int:
    """v95.7 #36：最终学习成本（含种族折扣）——技能列表/学习提示/扣点必须同源，避免显示不一致
    v134.1 人类天赋重做：learn_discount 已删除（鱼鱼拍板改 first_upgrade_refund），
    本函数保留比例折扣兼容（未来种族若配比例仍生效）"""
    cost = skill_learn_cost(need_lv)
    disc = race_stats(player.get("race")).get("learn_discount")
    if disc:
        cost = max(1, int(cost * (1 - disc)))
    return cost


# ---------------- 技能升级（v27） ----------------
SKILL_MAX_LEVEL = 5          # 技能等级上限
SKILL_POWER_PER_LV = 0.10    # 攻击/治疗每级 power +10%（未单独配置时的默认值）



def _skill_up(info: dict | None) -> dict:
    """按技能 info 查升级配置(key 用中文名)"""
    if not info:
        return {}
    return C.SKILL_UP.get(info.get("name", "")) or {}


def skill_upgrade_cost(cur_lv: int, info: dict | None = None) -> int:
    """升级消耗（递增）：Lv.1→2 花1点，2→3 花2点，3→4 花3点，4→5 花4点
    v56.4：达到该技能独立满级（max）后返回 0"""
    mx = skill_max_level(info)
    if cur_lv < 1 or cur_lv >= mx:
        return 0
    return cur_lv


def skill_max_level(info: dict | None = None) -> int:
    """技能独立满级(v56.4)：SKILL_UP 配了 max 用配置，否则默认 5"""
    if not info:
        return SKILL_MAX_LEVEL
    return int(_skill_up(info).get("max", SKILL_MAX_LEVEL))


def skill_power_mult(level: int, info: dict | None = None) -> float:
    """技能等级对 power 的倍率。info 给定且配了 p 时按该技能成长，否则默认每级＋10%"""
    lv = max(1, min(level, skill_max_level(info)))
    p = _skill_up(info).get("p", SKILL_POWER_PER_LV * 100)
    return 1.0 + (p / 100) * (lv - 1)


def skill_flat_value(player_lv: int, skill_lv: int, info: dict | None = None) -> int:
    """v156 技能基础值（保底伤害）：flat = BASE + player_lv×PER_LV + skill_lv×PER_SKILL_LV。

    - 随玩家等级成长（等级越高基础越高，低攻不刮痧）
    - 随技能等级成长（技能升级基础值也涨）
    - 高等级时百分比主导（基础值占比稀释，不膨胀）
    数值常量在 game/data/skill_up.py（SKILL_FLAT_*），工具集/引擎共用同一口径。
    """
    from .data.skill_up import SKILL_FLAT_BASE, SKILL_FLAT_PER_PLAYER_LV, SKILL_FLAT_PER_SKILL_LV
    lv = max(1, min(skill_lv, skill_max_level(info)))
    return int(SKILL_FLAT_BASE + player_lv * SKILL_FLAT_PER_PLAYER_LV + lv * SKILL_FLAT_PER_SKILL_LV)


def skill_buff_turns(level: int, base: int = 3, info: dict | None = None) -> int:
    """增益技能升级：每级持续刻＋1(Lv.1=3，Lv.5=7)"""
    lv = max(1, min(level, skill_max_level(info)))
    return base + (lv - 1)


def skill_cond_mult(cond: dict | None, level: int, info: dict | None = None) -> float:
    """条件转化倍率随等级成长。info 配了 c 时按该技能成长，否则默认每级＋0.05"""
    if not cond:
        return 1.0
    lv = max(1, min(level, skill_max_level(info)))
    c = _skill_up(info).get("c", 0.05)
    return cond.get("mult", 1.0) + c * (lv - 1)


def skill_mech_val(info: dict, level: int) -> int:
    """机制叠层随等级成长。info 配了 m 时按该技能间隔，否则默认每 2 级＋1 层"""
    base = int(info.get("mech_val", 0) or 0)
    lv = max(1, min(level, skill_max_level(info)))
    m = max(1, int(_skill_up(info).get("m", 2) or 0))  # v109.2 防御：m≤0 时按默认 2（防除零）
    return base + (lv - 1) // m


def skill_lifesteal_pct(info: dict | None, level: int) -> float:
    """吸血比例随等级成长：基础读技能 lifesteal 字段（如嗜血斩 0.25），未配置默认 20%；配了 l 时每级＋2%
    v104 R3 P2-10 修复：原固定 0.20 基础不读 lifesteal 字段 → 嗜血斩 desc 承诺 25% 实机 20%"""
    lv = max(1, min(level, skill_max_level(info)))
    base = float((info or {}).get("lifesteal", 0) or 0) or 0.20
    return base + _skill_up(info).get("l", 0) / 100 * (lv - 1)


def skill_level_of(player: dict, skill_name: str) -> int:
    """技能等级查询（v46+ 兼容）：store 读库后 skill_levels 的 key 是中文名（players.py:113 display 转换），
    入参可能是 ID 或中文名——统一 resolve 后匹配，查不到按未升级 Lv.1。
    修复 #259：技能列表/详情/战斗内此前用 ID 直接查 key 恒 fallback Lv.1（战斗内实际按 Lv.1 计算）。"""
    levels = player.get("skill_levels") or {}
    if not levels:
        return 1
    sid = C.resolve("skills", skill_name)
    for k, v in levels.items():
        if k and C.resolve("skills", k) == sid:
            return int(v or 1)
    return 1


def skill_info(class_name: str, skill_name: str):
    """技能详情：先查基础职业技能表，再查分支专属技能表（v26），最后查导师进阶技能（v95.23）
    v48：skill_name 接受中文名或 ID，统一 resolve 为 ID 再查（表 key 已是 sk_xxx）"""
    skill_name = C.resolve("skills", skill_name)
    info = _sk_table(class_name).get(skill_name)
    if info:
        return info
    for tier, branches in _br_table(class_name).items():
        for bname, skills in branches.items():
            if skill_name in skills:
                return skills[skill_name]
    # v95.23 职业导师进阶技能（TUTOR_SKILLS 并入查询链，battle/面板共用）
    t_info = (C.TUTOR_SKILLS or {}).get(class_name, {}).get(skill_name)
    if t_info:
        return t_info
    return None


def branch_skill_owner(class_name: str, skill_name: str):
    """分支专属技能归属：(tier, 分支名)；非分支技能返回 None(v26)"""
    skill_name = C.resolve("skills", skill_name)
    for tier, branches in _br_table(class_name).items():
        for bname, skills in branches.items():
            if skill_name in skills:
                return tier, bname
    return None
# ============================================================
# 战斗
# ============================================================
def calc_damage(atk, def_, is_crit=False, variance=0.15, pierce=False, pene_pct=0.0, pene_flat=0, dmg_type="phys"):
    """伤害公式(v22 非线性减伤)：dmg = atk²/(atk+def)，防御收益递减，杜绝物理免疫
    v106 穿透：有效防御 = max(0, int(def × (1-pene_pct)) - pene_flat)（先百分比后固定，下限 0）
    v107 伤害类型四层架构（鱼鱼拍板）：dmg_type = phys/magi/true
    - true 真伤：绕过全部减伤（无防御公式，dmg = atk 直伤），与 pierce 语义区分——
      pierce 仅无视防御公式、调用方仍可能叠加免伤段；true 为纯真伤（不吸/不反/全无视）
    - 真伤同样吃波动与暴击（暴击倍率由调用方 crit_dmg 段统一追加）"""
    if dmg_type == "true" or pierce:
        dmg = atk
    else:
        # v106：穿透削减有效防御（百分比上限 0.6 由聚合层 cap，这里兜底防脏值）
        eff_def = def_
        try:
            pct = min(max(float(pene_pct), 0.0), 0.6)
            flat = max(int(pene_flat), 0)
            if pct > 0 or flat > 0:
                eff_def = max(0, int(def_ * (1 - pct)) - flat)
        except Exception:
            eff_def = def_
        # v104 M02 P2：atk+def_ 为 0 时直接返回伤害下限 1，防 ZeroDivisionError
        if atk + eff_def <= 0:
            return 1
        # 非线性减伤：防御越高收益越低，但不会完全免疫
        dmg = atk * atk / (atk + eff_def)
    dmg = max(1, dmg)
    dmg = int(dmg * (1 + random.uniform(-variance, variance)))
    if is_crit:
        dmg = int(dmg * 1.5)
    return max(1, dmg)


def resolve_formula(formula, stats, target_def, target_mdef, is_crit=False,
                    pene_phys=0.0, pene_magi=0.0, pene_flat_phys=0, pene_flat_magi=0,
                    variance=0.15, mult=1.0, target_max_hp=None, randomize=True):
    """v156 通用公式解释器——所有伤害来源（技能/装备/食物/宠物/敌方）共用。

    formula 每段：
      {"stat": "atk"|"matk"|"max_hp"|"flat",   # 属性来源（flat=纯固定值）
       "mult": 1.2,                            # 百分比系数（乘以 stat）
       "flat": 50,                             # 固定值（基础值；可选，默认 0）
       "type": "phys"|"magi"|"true",           # 伤害类型（吃 def/mdef/无视）
       "chance": 0.5}                          # 触发概率（可选；缺省 100%）

    stats: 攻击方面板（atk/matk/max_hp 等）
    target_def/target_mdef: 目标防御
    mult: 外部乘区（技能 power 成长/条件/叠层等，由调用方算好）
    target_max_hp: 目标 max_hp（stat=max_hp 时用；缺省用 stats.max_hp）

    返回 (总伤害, 魔法段伤害) —— magi 段单独返回供吸血/魔免分账。
    """
    total = 0
    magi_part = 0
    if not formula:
        return 0, 0
    import random as _r
    for seg in formula:
        # 触发概率
        chance = float(seg.get("chance", 1.0))
        if chance != 1.0:
            chance = float(seg.get("chance", 1.0) or 0.0)
        if randomize and chance < 1.0 and _r.random() > chance:
            continue
        fstat = seg.get("stat", "atk")
        fmult = float(seg.get("mult", 1.0) or 1.0) * mult
        fflat = int(seg.get("flat", 0) or 0)
        ftype = seg.get("type", "phys")
        # 属性来源
        if fstat == "matk":
            base = int(stats.get("matk", 0) * fmult) + fflat
        elif fstat == "max_hp":
            _mh = target_max_hp if target_max_hp is not None else stats.get("max_hp", 0)
            base = int(_mh * fmult) + fflat
        elif fstat == "flat":
            base = fflat
        else:  # atk
            base = int(stats.get("atk", 0) * fmult) + fflat
        # 伤害类型 → 防御/穿透
        if ftype == "true":
            dmg = calc_damage(base, 0, is_crit, variance=variance, dmg_type="true")
        elif ftype == "magi":
            dmg = calc_damage(base, target_mdef, is_crit, variance=variance,
                              pene_pct=pene_magi, pene_flat=pene_flat_magi, dmg_type="magi")
            magi_part += dmg
        else:
            # v157 formula 段级 pierce：seg 带 "pierce": true → 绕过防御公式
            # （与非 formula 物理 pierce 技能 calc_damage(pierce=True) 等价）
            if seg.get("pierce"):
                dmg = calc_damage(base, 0, is_crit, variance=variance, pierce=True, dmg_type="phys")
            else:
                dmg = calc_damage(base, target_def, is_crit, variance=variance,
                                  pene_pct=pene_phys, pene_flat=pene_flat_phys, dmg_type="phys")
        total += dmg
    return total, magi_part


def check_player_level_up(group_id, qq_id, player: dict) -> tuple[list, dict]:
    """检查是否升级(处理多次连升)。返回 (log列表, 更新后的player)"""
    logs = []
    # v95.12 #143：消费读档惰性升级暂存的提示（get_player 已静默升级写回，这里补回提示）
    if player.get("_lv_logs"):
        logs = player.pop("_lv_logs")
    # v110 审计修复：100 级硬顶（07 章"以 100 为终极等级"，成就"达到100级"为里程碑）——
    # 原实现可无限升级为空成长；达 100 级后经验不再消费
    while player["level"] < 100 and player["exp"] >= C.exp_to_next(player["level"]):
        player["exp"] -= C.exp_to_next(player["level"])
        player["level"] += 1
        tier = player.get("class_tier", 0)
        prev_base = player_base_stats(player["class_name"], player["level"] - 1, tier)
        # v101.28l #419：升级横幅差值必须同口径裸装对比（此前新级最终属性−旧级裸装，
        # 装备/属性点/称号加成全被算进"升级成长"→ playtest 实锤虚高 50 倍/40 倍）
        new_base = player_base_stats(player["class_name"], player["level"], tier)
        # v94 #41：升级重算必须传全 7 参数（race/evolve_path/title_bonus 漏传 → 写入值与面板/战斗重算不一致）
        st = player_final_stats(player["class_name"], player["level"], player.get("equipment", {}), tier, player.get("attributes"), player.get("evolve_path", 0), player.get("_title_bonus", {}) or {}, player.get("race"))
        player["attr_pts"] = player.get("attr_pts", 0) + 3  # 每级 +3 自由属性点
        player["skill_points"] = player.get("skill_points", 0) + 1  # 每级 +1 技能点
        player["max_hp"] = st["max_hp"]
        player["max_mp"] = st["max_mp"]
        player["hp"] = st["max_hp"]
        player["mp"] = st["max_mp"]
        # v12：等级只解锁"可学习资格"，不再自动学会（要花技能点学）
        # v95 #136：available 是 sk_xxx ID，learned_now 是中文名（v46 内存层转名），
        # 必须取 info["name"] 比较，否则已学技能也计入"可学"（s not in learned_now 恒 True）
        available = [info.get("name", s) for s, info in _sk_table(player["class_name"]).items()
                     if info["lv"] <= player["level"]]
        learned_now = set(player.get("learned_skills", []))
        can_learn = [s for s in available if s not in learned_now]
        logs.append(
            f"🎉 恭喜升级！现在 {player['level']} 级！"
            f"(生命上限 +{new_base['hp'] - prev_base['hp']}, 攻击 +{new_base['atk'] - prev_base['atk']})"
            f"\n📌 属性点 +3、技能点 +1(『属性』加点 / 『技能学习 <名称>』学技能)"
        )
        if can_learn:
            # v101.30d #O54：提示语修正——可学的含 5 技能点被动（风行步/狩猎咆哮等），
            # 不再叫"新技能"误导（playtest 小蓝：提示与"新技能"概念出入）
            logs.append(f"📖 有 {len(can_learn)} 个技能可学习（含被动）！『技能学习 <技能名>』消耗技能点学会(『技能列表』查看)")
        if player["level"] == C.EVOLVE_LEVELS[1]:
            logs.append(f"🌟 你已达到 {player['level']} 级，可以转职了！(输入『转职』查看)")
        # v140 波3.3：章节礼包——每 10 级里程碑发放一次（event_state 防重复）
        if player["level"] % 10 == 0:
            try:
                from . import db as _db
                _ck = f"chapter_pack_{player['level']}_{qq_id}"
                if not _db.get_event_state(_ck):
                    _packs = {p["lv"]: p for p in C.CHAPTER_PACK}
                    _pack = _packs.get(player["level"])
                    if _pack:
                        from .store.inventory import add_item as _add_item
                        _got = []
                        for _iname in _pack.get("items", []):
                            _iid = C.resolve("items", _iname)
                            if _iid in C.ITEMS:
                                _add_item(group_id, qq_id, _iid, C.ITEMS[_iid])
                                _got.append(_iname)
                            else:
                                _imid = C.resolve("materials", _iname)
                                if _imid in C.MATERIALS:
                                    _add_item(group_id, qq_id, _imid, {"name": C.display("materials", _imid), "type": C.MATERIALS[_imid].get("type", "材料"), "stackable": True, "price": C.MATERIALS[_imid]["price"]})
                                    _got.append(_iname)
                        if _got:
                            _db.set_event_state(_ck, "1")
                            logs.append(f"🎁 章节里程碑达成！获得【{_pack.get('name', '礼包')}】：{'、'.join(_got)}！")
            except Exception:
                pass
    return logs, player


def resolve_drop(name: str):
    """v110 审计修复：掉落名解析——材料优先，其次 ITEMS（消耗品/副本钥匙 i_key_* 等）。

    战斗/副本掉落结算原先只认 MATERIALS，钥匙类消耗品（29 章入场钥匙）结构上发不出
    （D11 P0-2：设计 29:505「遗骸搜出龙宫宝珠」在当前架构不可实现）。返回 item ID。
    """
    mid = C.resolve("materials", name)
    if mid in C.MATERIALS:
        return mid
    for _k, _v in C.ITEMS.items():
        if _v.get("name") == name:
            return _k
    return None
