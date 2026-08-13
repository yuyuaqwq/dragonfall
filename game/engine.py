# -*- coding: utf-8 -*-
"""《剑与魔法》核心引擎 —— 属性/战斗/掉落/升级/任务"""
import random

from . import content as C


# ============================================================
# 角色属性
# ============================================================
# 转职成长加成（tier 0-3 → 0/15%/30%/50%）
TIER_GROWTH = {0: 1.0, 1: 1.15, 2: 1.30, 3: 1.50}
# v25 转职分支属性倾向（左=攻击/速度，右=防御/生命）
BRANCH_BONUS = {
    1: {"atk": 1.06, "spd": 1.04},   # 左：进攻路线
    2: {"def": 1.08, "hp": 1.06},    # 右：防御路线
}


# 元素亲和可切换的系（法师）
ELEMENT_OPTIONS = ["fire", "ice", "thunder"]
ELEMENT_CN = {"fire": "火", "ice": "冰", "thunder": "雷"}
# 元素印记 key（存敌方 e_buffs，层数）
ELEMENT_MARKS = {"fire": "fire_mark", "ice": "ice_mark", "thunder": "thunder_mark"}

# ============================================================
# v2.0 元素反应（12 章 3.1，严格按策划案表）
# 当前系 × 目标印记 → 反应：
#   蒸发 = 火印(目标) + 水/冰(当前系) → 增伤 30%，清除印记
#   超载 = 雷印(目标) + 火(当前系)   → 全体 120% 伤害，清除印记
#   冻结 = 冰印(目标) + 水(当前系)   → 冻结 1 回合（法师暂无水系技能，预留）
#   感电 = 雷印(目标) + 雷(当前系)   → 连击 +1，印记保留
# ============================================================
ELEMENT_REACTIONS = {
    ("ice", "fire_mark"):      {"name": "蒸发", "mult": 1.30, "clear": True, "extra": ""},
    ("fire", "thunder_mark"):  {"name": "超载", "mult": 1.00, "clear": True, "extra": "aoe"},
    ("water", "ice_mark"):     {"name": "冻结", "mult": 1.00, "clear": True, "extra": "freeze"},
    ("thunder", "thunder_mark"): {"name": "感电", "mult": 1.00, "clear": False, "extra": "chain"},
}


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
    """回合开始核心资源回复(如游侠精力＋25)。返回新值。"""
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
    "burn": 5,     # 灼烧：5 层 = 每回合 15% 生命
    "poison": 5,   # 毒层：5 层 = 每回合 15% 生命
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
    if evolve_path:
        bb = BRANCH_BONUS.get(evolve_path, {})
        for k, v in bb.items():
            if k == "hp":
                base["hp"] = int(base["hp"] * v)
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


def player_final_stats(class_name: str, level: int, equipment: dict, tier: int = 0, attributes: dict = None, evolve_path: int = 0, title_bonus: dict = None, race: str = None) -> dict:
    """基础属性 + 装备加成(含强化增幅)+ 自由属性点加成 + 称号加成 + 种族天赋"""
    st, _ = player_stats_detail(class_name, level, equipment, tier, attributes, evolve_path, title_bonus, race)
    return st


# ---------------- 被动技能（v64） ----------------
# 属性型被动：stat -> 修正属性；返回 dict 与 player_final_stats 相同键（max_hp/max_mp/atk/...）
# 被动 stat → (bonus_key, 操作, 需 cond is None)
# 不在表内的 stat：条件型(rage>=5/battle_start/dual_stat) 与战斗内机制(fire/chi_gain/proc 型) 由 battle.py 结算，面板不处理
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
             "lifesteal_phys_add": 0.0, "lifesteal_magi_add": 0.0}  # v106.4 反伤/物魔免/物法吸被动
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
              "lifesteal_phys": "物吸", "lifesteal_magi": "法吸"}  # v106.3/v106.4


def player_stats_detail(class_name: str, level: int, equipment: dict, tier: int = 0, attributes: dict = None, evolve_path: int = 0, title_bonus: dict = None, race: str = None) -> tuple:
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
    attr_src["atk"] = int(attr.get("str", 0) * 1.2)
    attr_src["matk"] = int(attr.get("int", 0) * 1.2)
    attr_src["spd"] = int(attr.get("agi", 0) * 0.8)
    attr_src["crit"] = attr.get("agi", 0) * 0.004
    attr_src["hp"] = int(attr.get("vit", 0) * 8)
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
        item_src = {}
        for k, v in item.get("stats", {}).items():
            if k in STAT_NAMES:
                # v101.21e 修复：PCT_STATS（crit/dodge）保留小数——原代码只特判 crit，
                # dodge 0.05 被 int() 截断成 0，装备闪避加成全部丢失
                item_src[k] = item_src.get(k, 0) + (int(v * mult) if k not in C.PCT_STATS else v)
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
    sb2 = set_bonus_2(equipment)
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
                st[k] = int(st[k] * (1 + v))
        names2 = [s for s, c in active_sets(equipment).items() if c >= 2]
        sources.append({"name": f"套装2件({'/'.join(names2)})", "stats": src2, "pct": True})
    # 5. 套装 4 件属性型特效（常驻属性）
    eff_src = {}
    for eff in set_bonus_4(equipment):
        if eff == "crit_up_set":
            eff_src["crit"] = eff_src.get("crit", 0) + 0.08
            st["crit"] = min(st["crit"] + 0.08, 0.5)
        elif eff == "dodge_set":
            eff_src["dodge"] = eff_src.get("dodge", 0) + 0.10
            st["dodge"] = min(st["dodge"] + 0.10, 0.4)
        elif eff == "mdef_up_set":
            eff_src["mdef"] = eff_src.get("mdef", 0) + 0.20
            st["mdef"] = int(st["mdef"] * 1.20)
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


def set_bonus_2(equipment: dict) -> dict:
    """汇总所有激活套装的 2 件百分比加成 {stat: 总和}
    阶段八：>=4 件时叠加 4 件属性加成（bonus_4_stats），>=5 件时叠加 5 件 stat 型效果（bonus_5.crit/dodge，10 章五节橡木/铁港）"""
    bonus = {}
    for sname, cnt in active_sets(equipment).items():
        info = _set_info(sname)
        if not info:
            continue
        for k, v in info.get("bonus_2", {}).items():
            bonus[k] = bonus.get(k, 0) + v
        if cnt >= 4:
            for k, v in info.get("bonus_4_stats", {}).items():
                bonus[k] = bonus.get(k, 0) + v
        if cnt >= 5:
            for k, v in info.get("bonus_5", {}).items():
                # 5 件 stat 型效果（crit/dodge 直接是属性）；desc 型（战斗特效）不在这里结算
                if k in C.PCT_STATS:
                    bonus[k] = bonus.get(k, 0) + v
    return bonus


def has_set(equipment: dict, set_name: str) -> bool:
    """装备是否穿戴了指定套装(10 章名册套装按套装名匹配)"""
    for item in (equipment or {}).values():
        if item and item.get("set") == set_name:
            return True
    return False


def set_bonus_4(equipment: dict) -> list:
    """返回已激活套装(>=4 件)的 4 件特效效果名列表"""
    effs = []
    for sname, cnt in active_sets(equipment).items():
        info = _set_info(sname)
        if info and cnt >= 4 and info.get("bonus_4", {}).get("effect"):
            effs.append(info["bonus_4"]["effect"])
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
    """v95.7 #36：最终学习成本（含种族折扣）——技能列表/学习提示/扣点必须同源，避免显示不一致"""
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


def skill_buff_turns(level: int, base: int = 3, info: dict | None = None) -> int:
    """增益技能升级：每级持续回合＋1(Lv.1=3，Lv.5=7)"""
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
    m = _skill_up(info).get("m", 2)
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


def check_player_level_up(group_id, qq_id, player: dict) -> tuple[list, dict]:
    """检查是否升级(处理多次连升)。返回 (log列表, 更新后的player)"""
    logs = []
    # v95.12 #143：消费读档惰性升级暂存的提示（get_player 已静默升级写回，这里补回提示）
    if player.get("_lv_logs"):
        logs = player.pop("_lv_logs")
    while player["exp"] >= C.exp_to_next(player["level"]):
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
    return logs, player
