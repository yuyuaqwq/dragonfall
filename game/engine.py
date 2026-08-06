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

# ============================================================
# v2.0 核心资源系统（12 章 1.2 战斗资源总览）
# 每职业一个独立战斗资源 dict，随战斗序列化（同 mech_stacks 机制）。
# 阶段五先建引擎，技能数据落地（阶段六）后按技能表挂载获取/消耗。
# ============================================================
CORE_RESOURCES = {
    "cls_zhan_shi": {
        "key": "rage", "name": "怒气", "max": 10, "regen": 0,
        "desc": "攻击/受击 +1-2，终结技消耗，越战越勇",
        "on_attack": 1, "on_hit": 1, "on_skill": 2,
    },
    "cls_fa_shi": {
        "key": "element", "name": "元素亲和", "max": 1, "regen": 0,
        "desc": "火/冰/雷三系切换，施法触发元素反应",
        "on_attack": 0, "on_hit": 0, "on_skill": 0, "type": "switch",
    },
    "cls_you_xia": {
        "key": "energy", "name": "精力", "max": 100, "regen": 25,
        "desc": "每回合回 25 点，技能消耗 15-40，不耗魔力",
        "on_attack": 0, "on_hit": 0, "on_skill": 0,
    },
    "cls_mu_shi": {
        "key": "faith", "name": "信仰值", "max": 10, "regen": 0,
        "desc": "治疗/圣光技/受击 +1，神迹技消耗",
        "on_attack": 0, "on_hit": 1, "on_skill": 1, "on_heal": 2,
    },
    "cls_ci_ke": {
        "key": "cp", "name": "连击点", "max": 5, "regen": 0,
        "desc": "攒点技积累，终结技消耗，潜行爆发",
        "on_attack": 1, "on_hit": 0, "on_skill": 1,
    },
    "cls_quan_shi": {
        "key": "chi", "name": "气", "max": 10, "regen": 0,
        "desc": "连招/受击 +1，终结技/斗气消耗",
        "on_attack": 1, "on_hit": 1, "on_skill": 1,
    },
}

# 元素亲和可切换的系（法师）
ELEMENT_OPTIONS = ["fire", "ice", "thunder"]
ELEMENT_CN = {"fire": "火", "ice": "冰", "thunder": "雷"}


def core_resource_def(class_name: str) -> dict:
    """职业核心资源定义（v48：中文或 ID → ID）。无定义返回 {}。"""
    cls_id = C.resolve("classes", class_name) if class_name else ""
    return CORE_RESOURCES.get(cls_id, {})


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
    """回合开始核心资源回复（如游侠精力 +25）。返回新值。"""
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
}


def mech_stack_gain(mech: str, p_mech: dict, mval: int) -> int:
    """叠层（带上限）。返回新层数。未配上限的机制不限制。"""
    cap = MECH_STACK_MAX.get(mech, 99)
    return min(cap, p_mech.get(mech, 0) + mval)

def player_base_stats(class_name: str, level: int, tier: int = 0, evolve_path: int = 0) -> dict:
    """职业基础 + 等级成长（含转职成长加成 + v25 分支属性倾向）"""
    class_name = C.resolve("classes", class_name)  # v48：中文或 ID → ID
    cls = C.CLASSES[class_name]
    base = dict(cls["base"])
    growth = cls["growth"]
    mult = TIER_GROWTH.get(tier, 1.0)
    for k in ("hp", "mp", "atk", "def", "matk", "mdef", "spd"):
        base[k] = int(base[k] + growth[k] * (level - 1) * mult)
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


def player_final_stats(class_name: str, level: int, equipment: dict, tier: int = 0, attributes: dict = None, evolve_path: int = 0, title_bonus: dict = None) -> dict:
    """基础属性 + 装备加成（含强化增幅）+ 自由属性点加成 + 称号加成"""
    st, _ = player_stats_detail(class_name, level, equipment, tier, attributes, evolve_path, title_bonus)
    return st


# ---------------- 被动技能（v64） ----------------
# 属性型被动：stat -> 修正属性；返回 dict 与 player_final_stats 相同键（max_hp/max_mp/atk/...）
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
             "matk_mult": 1.0, "mdef_mult": 1.0, "spd_mult": 1.0, "crit_add": 0.0}
    learned = [C.display("skills", s) for s in (learned_skills or []) if s]
    for name in learned:
        info = skill_info(class_name, name)
        if not info or info.get("kind") != "被动":
            continue
        ps = info.get("passive") or {}
        if ps.get("stat") == "mp" and ps.get("cond") is None:
            bonus["mp_mult"] *= (1 + float(ps.get("mult", 0)))
        elif ps.get("stat") == "spd":
            bonus["spd_mult"] *= (1 + float(ps.get("mult", 0)))
        elif ps.get("stat") == "crit":
            bonus["crit_add"] += float(ps.get("mult", 0))
        elif ps.get("stat") == "fire" or ps.get("stat") == "chi_gain":
            pass  # 战斗内机制，不参与面板
        # 条件型属性（rage>=5 / battle_start）由 battle.py 按条件结算
    return bonus


def passive_skills_learned(class_name: str, learned_skills: list | None = None) -> list:
    """返回已学被动技能的中文名列表（v64）。battle.py 用它查触发型被动。"""
    learned = [C.display("skills", s) for s in (learned_skills or []) if s]
    out = []
    for name in learned:
        info = skill_info(class_name, name)
        if info and info.get("kind") == "被动":
            out.append(name)
    return out


def is_passive_learned(class_name: str, passive_name: str, learned_skills: list | None = None) -> bool:
    """指定被动是否已学（v64）。passive_name 为被动技能中文名。"""
    return passive_name in passive_skills_learned(class_name, learned_skills)

# 属性中文名（面板/来源展示用）
STAT_NAMES = {"hp": "生命", "mp": "魔力", "atk": "攻击", "def": "防御", "matk": "魔攻",
              "mdef": "魔防", "spd": "速度", "crit": "暴击", "dodge": "闪避"}


def player_stats_detail(class_name: str, level: int, equipment: dict, tier: int = 0, attributes: dict = None, evolve_path: int = 0, title_bonus: dict = None) -> tuple:
    """拆解属性来源。返回 (最终属性 dict, 来源明细 list)。

    来源明细每项: {"name": 来源名, "stats": {属性: 加值}}。
    与 player_final_stats 共用同一套计算（最终属性完全一致），保证面板显示和实际战斗一致。
    """
    sources = []
    # 1. 基础（职业 + 等级成长 + 转职加成 + v25 分支倾向）
    st = player_base_stats(class_name, level, tier, evolve_path)
    base_src = {"hp": st["max_hp"], "mp": st["max_mp"]}
    for k in ("atk", "def", "matk", "mdef", "spd"):
        base_src[k] = st[k]
    # v55.1：暴击/闪避基础值也进来源（属性面板显示完整构成）
    base_src["crit"] = st.get("crit", 0)
    base_src["dodge"] = st.get("dodge", 0)
    sources.append({"name": "基础", "stats": base_src})
    # 2. 自由属性点：力量→攻击 敏捷→速度/暴击 智力→魔攻/魔力 耐力→生命
    attr = attributes or {}
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
                item_src[k] = item_src.get(k, 0) + (int(v * mult) if k != "crit" else v)
        for af in item.get("affixes", []):
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
            if k in ("crit", "dodge"):
                st[k] = min(st[k] + v, 0.5 if k == "crit" else 0.4)
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
            if k in ("crit", "dodge"):
                src2[k] = v
                st[k] = min(st[k] + v, 0.5 if k == "crit" else 0.4)
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
                if k in ("crit", "dodge"):
                    st[k] = min(st[k] + v, 0.5 if k == "crit" else 0.4)
                elif k == "hp":
                    st["max_hp"] += int(v)
                elif k == "mp":
                    st["max_mp"] += int(v)
                else:
                    st[k] += int(v)
            sources.append({"name": "副业称号", "stats": tb})
    return st, sources


# ---------------- v10 套装计算 ----------------
def active_sets(equipment: dict) -> dict:
    """返回 {套装名: 已穿件数}，只含 >=2 件的套装（2 件才有效果）"""
    counts = {}
    for slot, item in (equipment or {}).items():
        if not item:
            continue
        s = item.get("set")
        if s:
            counts[s] = counts.get(s, 0) + 1
    return {s: c for s, c in counts.items() if c >= 2}


def set_bonus_2(equipment: dict) -> dict:
    """汇总所有激活套装的 2 件百分比加成 {stat: 总和}"""
    bonus = {}
    for sname, cnt in active_sets(equipment).items():
        info = C.SETS.get(sname)
        if not info:
            continue
        for k, v in info.get("bonus_2", {}).items():
            bonus[k] = bonus.get(k, 0) + v
    return bonus


def set_bonus_4(equipment: dict) -> list:
    """返回已激活套装（>=4 件）的 4 件特效效果名列表"""
    effs = []
    for sname, cnt in active_sets(equipment).items():
        info = C.SETS.get(sname)
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
    """技能是否已学会（v12：必须『技能学习』花技能点学会才能使用，不再按等级自动解锁）"""
    info = skill_info(class_name, skill_name)
    if not info:
        return False
    # v48：learned_skills 是中文名（store 读回），skill_name 可能是 ID——统一 resolve 比较
    sid = C.resolve("skills", skill_name)
    return sid in [C.resolve("skills", s) for s in (learned_skills or []) if s]



def skill_learn_cost(level: int, need_lv: int) -> int:
    """学习技能消耗的技能点（v12：按技能等级定价，等级越高越贵）"""
    return need_lv // 6 + 2


# ---------------- 技能升级（v27） ----------------
SKILL_MAX_LEVEL = 5          # 技能等级上限
SKILL_POWER_PER_LV = 0.10    # 攻击/治疗每级 power +10%（未单独配置时的默认值）


# v56.4 每个技能单独策划升级成长 + 独立满级（鱼鱼：不要一刀切）
# 字段：p=每级伤害/治疗倍率 +x%；c=每级条件倍率 +c；m=每 m 级叠层 +1；l=每级吸血比例 +2%；max=满级
# max 规则：增益/嘲讽/团队=3；大招(power≥3.5)=3；治疗大招=4；条件联动/爆发=4；输出/连击/治疗核心=5
SKILL_UP = {
    '猛击': {"p": 12, "m": 2, "max": 5},
    '破甲斩': {"p": 10, "c": 0.05, "max": 4},
    '怒吼': {"max": 3},
    '旋风斩': {"p": 10, "m": 2, "max": 5},
    '铁壁': {"max": 3},
    '处决': {"p": 12, "m": 2, "max": 3},
    '裂空斩': {"p": 8, "c": 0.08, "m": 3, "max": 3},
    '血刃斩': {"p": 12, "l": 2, "max": 5},
    '狂暴连斩': {"p": 9, "m": 3, "max": 5},
    '战争咆哮': {"m": 3, "max": 3},
    '狂暴之心': {"max": 3},
    '挫志怒吼': {"max": 3},
    '挑衅怒吼': {"max": 3},
    '盾牌反击': {"max": 3},
    '援护': {"max": 3},
    '盾墙': {"max": 3},
    '致命重斩': {"p": 10, "m": 3, "max": 3},
    '火球术': {"p": 12, "m": 2, "max": 5},
    '寒冰箭': {"p": 10, "m": 2, "max": 5},
    '雷电术': {"p": 10, "c": 0.08, "max": 4},
    '魔力涌动': {"max": 3},
    '陨石术': {"p": 8, "c": 0.08, "m": 3, "max": 4},
    '奥术强化': {"max": 3},
    '龙息术': {"p": 10, "m": 2, "max": 3},
    '冰棱': {"p": 9, "m": 3, "max": 5},
    '火球连射': {"p": 9, "m": 3, "max": 5},
    '寒冰风暴': {"p": 8, "m": 3, "max": 5},
    '碎冰术': {"p": 9, "c": 0.1, "max": 4},
    '灼烧引爆': {"max": 3},
    '元素护盾': {"max": 3},
    '奥术共鸣': {"max": 3},
    '精准射击': {"p": 12, "m": 2, "max": 5},
    '连射': {"p": 9, "m": 3, "max": 5},
    '毒箭': {"p": 10, "m": 2, "max": 5},
    '疾风步': {"max": 3},
    '贯穿箭': {"p": 10, "c": 0.05, "max": 4},
    '鹰眼': {"max": 3},
    '龙息箭': {"p": 10, "c": 0.05, "m": 2, "max": 3},
    '追踪箭': {"p": 10, "m": 2, "max": 5},
    '风矢': {"p": 9, "m": 3, "max": 5},
    '双连射': {"p": 9, "m": 3, "max": 5},
    '致命狙击': {"p": 10, "max": 4},
    '狩猎号令': {"max": 3},
    '箭雨掩护': {"max": 3},
    '百发百中': {"p": 10, "max": 3},
    '圣光弹': {"p": 12, "m": 2, "max": 5},
    '治愈术': {"p": 15, "max": 5},
    '圣盾': {"max": 3},
    '惩戒': {"p": 9, "c": 0.05, "max": 4},
    '群体治愈': {"p": 12, "max": 5},
    '神圣祷言': {"max": 3},
    '圣焰': {"p": 8, "c": 0.08, "m": 3, "max": 3},
    '圣光连打': {"p": 9, "m": 3, "max": 5},
    '神恩术': {"p": 12, "m": 3, "max": 5},
    '大恢复': {"p": 10, "m": 3, "max": 4},
    '圣光庇护': {"m": 3, "max": 3},
    '圣裁': {"p": 10, "max": 4},
    '治愈祷言': {"p": 10, "max": 3},
    '神恩守护': {"max": 3},
    '背刺': {"p": 12, "c": 0.05, "m": 2, "max": 4},
    '双刃乱舞': {"p": 9, "m": 3, "max": 5},
    '淬毒': {"p": 10, "m": 2, "max": 5},
    '影袭': {"p": 10, "m": 2, "max": 5},
    '致命标记': {"p": 10, "m": 2, "max": 5},
    '疾影': {"max": 3},
    '暗杀': {"p": 12, "max": 3},
    '影刃刺': {"p": 9, "m": 3, "max": 5},
    '淬毒刃': {"p": 8, "m": 3, "max": 5},
    '影连刺': {"p": 8, "m": 3, "max": 5},
    '毒爆': {"p": 10, "max": 4},
    '影袭爆发': {"p": 10, "max": 3},
    '淬毒仪式': {"max": 3},
    '暗影帷幕': {"max": 3},
    '铁拳': {"p": 12, "m": 2, "max": 5},
    '连打': {"p": 9, "m": 3, "max": 5},
    '金刚腿': {"p": 10, "m": 2, "max": 5},
    '内息调理': {"p": 15, "max": 5},
    '震地击': {"p": 9, "c": 0.05, "m": 3, "max": 4},
    '百裂拳': {"p": 7, "m": 3, "max": 5},
    '气功波': {"p": 8, "c": 0.08, "max": 3},
    '寸拳': {"p": 9, "m": 3, "max": 5},
    '罗汉冲拳': {"p": 9, "m": 3, "max": 5},
    '铁布衫': {"m": 3, "max": 3},
    '重炮拳': {"p": 10, "max": 4},
    '金刚打': {"p": 8, "m": 3, "max": 5},
    '金刚伏魔': {"max": 3},
    '气盾': {"max": 3},
}



def _skill_up(info: dict | None) -> dict:
    """按技能 info 查升级配置（key 用中文名）"""
    if not info:
        return {}
    return SKILL_UP.get(info.get("name", "")) or {}


def skill_upgrade_cost(cur_lv: int, info: dict | None = None) -> int:
    """升级消耗（递增）：Lv.1→2 花1点，2→3 花2点，3→4 花3点，4→5 花4点
    v56.4：达到该技能独立满级（max）后返回 0"""
    mx = skill_max_level(info)
    if cur_lv < 1 or cur_lv >= mx:
        return 0
    return cur_lv


def skill_max_level(info: dict | None = None) -> int:
    """技能独立满级（v56.4）：SKILL_UP 配了 max 用配置，否则默认 5"""
    if not info:
        return SKILL_MAX_LEVEL
    return int(_skill_up(info).get("max", SKILL_MAX_LEVEL))


def skill_power_mult(level: int, info: dict | None = None) -> float:
    """技能等级对 power 的倍率。info 给定且配了 p 时按该技能成长，否则默认每级 +10%"""
    lv = max(1, min(level, skill_max_level(info)))
    p = _skill_up(info).get("p", SKILL_POWER_PER_LV * 100)
    return 1.0 + (p / 100) * (lv - 1)


def skill_buff_turns(level: int, base: int = 3, info: dict | None = None) -> int:
    """增益技能升级：每级持续回合 +1（Lv.1=3，Lv.5=7）"""
    lv = max(1, min(level, skill_max_level(info)))
    return base + (lv - 1)


def skill_cond_mult(cond: dict | None, level: int, info: dict | None = None) -> float:
    """条件转化倍率随等级成长。info 配了 c 时按该技能成长，否则默认每级 +0.05"""
    if not cond:
        return 1.0
    lv = max(1, min(level, skill_max_level(info)))
    c = _skill_up(info).get("c", 0.05)
    return cond.get("mult", 1.0) + c * (lv - 1)


def skill_mech_val(info: dict, level: int) -> int:
    """机制叠层随等级成长。info 配了 m 时按该技能间隔，否则默认每 2 级 +1 层"""
    base = int(info.get("mech_val", 0) or 0)
    lv = max(1, min(level, skill_max_level(info)))
    m = _skill_up(info).get("m", 2)
    return base + (lv - 1) // m


def skill_lifesteal_pct(info: dict | None, level: int) -> float:
    """吸血比例随等级成长：基础 20%，配了 l 时每级 +2%"""
    lv = max(1, min(level, skill_max_level(info)))
    return 0.20 + _skill_up(info).get("l", 0) / 100 * (lv - 1)



def skill_info(class_name: str, skill_name: str):
    """技能详情：先查基础职业技能表，再查分支专属技能表（v26）
    v48：skill_name 接受中文名或 ID，统一 resolve 为 ID 再查（表 key 已是 sk_xxx）"""
    skill_name = C.resolve("skills", skill_name)
    info = _sk_table(class_name).get(skill_name)
    if info:
        return info
    for tier, branches in _br_table(class_name).items():
        for bname, skills in branches.items():
            if skill_name in skills:
                return skills[skill_name]
    return None


def branch_skill_owner(class_name: str, skill_name: str):
    """分支专属技能归属：(tier, 分支名)；非分支技能返回 None（v26）"""
    skill_name = C.resolve("skills", skill_name)
    for tier, branches in _br_table(class_name).items():
        for bname, skills in branches.items():
            if skill_name in skills:
                return tier, bname
    return None
# ============================================================
# 战斗
# ============================================================
def calc_damage(atk, def_, is_crit=False, variance=0.15, pierce=False):
    """伤害公式（v22 非线性减伤）：dmg = atk²/(atk+def)，防御收益递减，杜绝物理免疫"""
    if pierce:
        dmg = atk
    else:
        # 非线性减伤：防御越高收益越低，但不会完全免疫
        dmg = atk * atk / (atk + def_)
    dmg = max(1, dmg)
    dmg = int(dmg * (1 + random.uniform(-variance, variance)))
    if is_crit:
        dmg = int(dmg * 1.5)
    return max(1, dmg)


def player_attack(class_name: str, level: int, equipment: dict, monster: dict, skill_name: str | None = None, cur_hp: int = None, cur_mp: int = None, tier: int = 0, attributes: dict = None, evolve_path: int = 0, skill_levels: dict = None) -> tuple:
    """玩家行动。返回 (log列表, 是否结束, 怪物剩余hp, 消耗mp, 附加效果dict)
    skill_name 为 None 表示普攻。v27：skill_levels 支持技能升级倍率。
    """
    st = player_final_stats(class_name, level, equipment, tier, attributes, evolve_path)
    logs = []
    used_mp = 0
    extra = {}

    if skill_name:
        skill_name = C.resolve("skills", skill_name)
        info = _sk_table(class_name)[skill_name]
        used_mp = info["mp"]
        if cur_mp is not None and cur_mp < used_mp:
            return ["魔力不足！"], False, monster["hp"], 0, {}
        lv = int((skill_levels or {}).get(skill_name, 1) or 1)
        kind = info["kind"]
        if kind == "治疗":
            heal = int(st["matk"] * info["power"] * skill_power_mult(lv))
            extra["heal"] = heal
            logs.append(f"你施展【{skill_name}】，圣光治愈了你 {heal} 点生命！")
            return logs, False, monster["hp"], used_mp, extra
        if kind == "增益":
            extra["buff"] = info.get("effect")
            logs.append(f"你施展【{skill_name}】！")
            return logs, False, monster["hp"], used_mp, extra
        # 攻击技能
        is_crit = random.random() < st["crit"]
        multi = info.get("multi", 1)
        total = 0
        hit_logs = []
        pmult = skill_power_mult(lv)
        for _ in range(multi):
            if kind == "物理":
                if info.get("pierce"):
                    dmg_i = calc_damage(int(st["atk"] * info["power"] * pmult), 0, is_crit, pierce=True)
                else:
                    dmg_i = calc_damage(int(st["atk"] * info["power"] * pmult), monster["def"], is_crit)
            else:  # 魔法
                dmg_i = calc_damage(int(st["matk"] * info["power"] * pmult), monster["mdef"], is_crit)
            total += dmg_i
        monster["hp"] -= total
        if multi > 1:
            logs.append(f"你施展【{skill_name}】，连击 {multi} 次，共造成 {total} 点伤害！")
        else:
            logs.append(f"你施展【{skill_name}】，造成 {total} 点伤害！")
        if is_crit:
            logs[-1] += " 💥暴击！"
        # 技能特效（v48：技能名已转 ID，用 resolve 动态比较，避免硬编码 ID 漂移）
        SK = lambda cn: C.resolve("skills", cn)  # noqa: E731
        if skill_name == SK("处决"):
            bonus = int(total * (1 - monster["hp"] / monster["max_hp"]))
            monster["hp"] -= bonus
            logs[-1] = f"你施展【{skill_name}】，造成 {total + bonus} 点伤害（残血加成 {bonus}）！"
        if skill_name == SK("破甲斩"):
            extra["def_down"] = 1
            logs[-1] += " 敌防下降！"
        if skill_name == SK("寒冰箭"):
            extra["spd_down"] = 1
            logs[-1] += " 敌速下降！"
        if skill_name == SK("毒箭"):
            extra["poison"] = 2
            logs[-1] += " 敌人中毒了！"
        if skill_name == SK("标记猎杀"):
            extra["mark"] = 2
            logs[-1] += " 目标被标记！"
        return logs, False, monster["hp"], used_mp, extra
    else:
        # 普攻
        is_crit = random.random() < st["crit"]
        dmg = calc_damage(st["atk"], monster["def"], is_crit)
        monster["hp"] -= dmg
        logs.append(f"你挥剑攻击，造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
        return logs, False, monster["hp"], 0, {}


def monster_turn(monster: dict, player_stats: dict) -> tuple:
    """怪物行动。返回 (log, 对玩家造成的伤害, 附加效果dict)"""
    logs = []
    dmg = 0
    extra = {}
    # 20% 概率使用技能（有技能时）
    skill = None
    if monster.get("skills") and random.random() < 0.3:
        skill = random.choice(monster["skills"])
        sinfo = C.MONSTER_SKILLS.get(skill)
        if sinfo:
            kind = sinfo.get("kind")
            if kind == "增益":
                eff = sinfo.get("effect")
                if eff == "atk_up":
                    extra["mon_atk_up"] = 1
                    logs.append(f"【{monster['name']}】使用了【{skill}】，攻击力提升了！")
                elif eff == "atk_up_strong":
                    extra["mon_atk_up_strong"] = 1
                    logs.append(f"【{monster['name']}】使用了【{skill}】，攻击力大幅提升了！")
                elif eff == "def_up":
                    extra["mon_def_up"] = 1
                    logs.append(f"【{monster['name']}】使用了【{skill}】，防御提升了！")
                elif eff == "heal_self":
                    heal = int(monster["max_hp"] * 0.15)
                    monster["hp"] = min(monster["max_hp"], monster["hp"] + heal)
                    logs.append(f"【{monster['name']}】使用了【{skill}】，恢复了 {heal} 点生命！")
                elif eff == "summon":
                    extra["summon"] = 1
                    logs.append(f"【{monster['name']}】使用了【{skill}】，召唤了援军！")
                return logs, 0, extra
            power = sinfo.get("power", 1.0)
            is_crit = random.random() < 0.1
            if kind == "物理":
                dmg = calc_damage(int(monster["atk"] * power), player_stats["def"], is_crit)
            else:
                dmg = calc_damage(int(monster["matk"] * power), player_stats["mdef"], is_crit)
            logs.append(f"【{monster['name']}】使用了【{skill}】，对你造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
            return logs, dmg, extra
    # 普攻
    dmg = calc_damage(monster["atk"], player_stats["def"])
    logs.append(f"【{monster['name']}】攻击你，造成 {dmg} 点伤害！")
    return logs, dmg, {}


def check_player_level_up(group_id, qq_id, player: dict) -> tuple[list, dict]:
    """检查是否升级（处理多次连升）。返回 (log列表, 更新后的player)"""
    logs = []
    while player["exp"] >= C.exp_to_next(player["level"]):
        player["exp"] -= C.exp_to_next(player["level"])
        player["level"] += 1
        tier = player.get("class_tier", 0)
        prev_base = player_base_stats(player["class_name"], player["level"] - 1, tier)
        st = player_final_stats(player["class_name"], player["level"], player.get("equipment", {}), tier, player.get("attributes"))
        player["attr_pts"] = player.get("attr_pts", 0) + 3  # 每级 +3 自由属性点
        player["skill_points"] = player.get("skill_points", 0) + 1  # 每级 +1 技能点
        player["max_hp"] = st["max_hp"]
        player["max_mp"] = st["max_mp"]
        player["hp"] = st["max_hp"]
        player["mp"] = st["max_mp"]
        # v12：等级只解锁"可学习资格"，不再自动学会（要花技能点学）
        available = [s for s, info in _sk_table(player["class_name"]).items()
                     if info["lv"] <= player["level"]]
        learned_now = set(player.get("learned_skills", []))
        can_learn = [s for s in available if s not in learned_now]
        logs.append(
            f"🎉 恭喜升级！现在 {player['level']} 级！"
            f"(生命上限 +{st['max_hp'] - prev_base['hp']}, 攻击 +{st['atk'] - prev_base['atk']})"
        )
        if can_learn:
            logs.append(f"📖 有 {len(can_learn)} 个新技能可学习！『技能学习 <技能名>』消耗技能点学会（『技能列表』查看）")
        if player["level"] in (30,):
            logs.append(f"🌟 你已达到 {player['level']} 级，可以转职了！(输入『转职』查看)")
    return logs, player
