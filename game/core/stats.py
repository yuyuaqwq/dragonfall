# -*- coding: utf-8 -*-

from ..data import (
    EQUIP_SLOT_BASE, EQUIP_SLOT_SCALING, MONSTER_EXP_BASE, MONSTER_GOLD_BASE,
    MONSTER_ROLE_BASE, MONSTER_ROLE_GROWTH, QUALITY,
    NORMAL_HP_STAGE_MULT, BOSS_ATK_STAGE_MULT,   # v156 阶段 6 怪物数值修复
)  # v102.5 模板表下沉 data/stat_templates.py


"""奥兰迪亚·余烬纪年数据层 - stats.py"""
# v56.2 怪物等级段曲线（鱼鱼拍板调数值，根治"后期大招乱秒"）
# hp：16 级起渐入放大（30 级 ×2.2 / 60 级 ×3.4 / 90 级 ×4.3），≤15 级完全不变
# atk：31 级起放缓（60 级 ×0.85 / 90 级 ×0.73），避免后期怪攻击成长超过玩家防御
def hp_stage_mult(lv: int) -> float:
    # v131 收缓（2026-08-27）：16-30 段 8%→5%（30 级 1.75）、31-60 段 4%→3%（60 级 2.65）、61+ 3%→2%（100 级 3.45）
    # 原：≤15=1.0；16-30: 1+(lv-15)*0.08；31-60: 2.2+(lv-30)*0.04；61+: 3.4+(lv-60)*0.03
    if lv <= 15:
        return 1.0
    if lv <= 30:
        return 1.0 + (lv - 15) * 0.05
    if lv <= 60:
        return 1.75 + (lv - 30) * 0.03
    return 2.65 + (lv - 60) * 0.02


def atk_stage_mult(lv: int) -> float:
    if lv <= 30:
        return 1.0
    if lv <= 60:
        return 1.0 - (lv - 30) * 0.005
    # 防御性下限，防未来提高等级上限时出现负 atk（当前 ≤100 级不生效）
    return max(0.2, 0.85 - (lv - 60) * 0.004)


def _stage_mult(segments: tuple, lv: int) -> float:
    """等级段乘区表 → 分段线性（每段从上一段末值按斜率增长，与 hp_stage_mult 同风格）。

    segments: [(max_lv, slope_per_lv), ...]——每段 = (该段上限等级, 每级斜率)。
    从 lv=0 起：≤首段 max_lv 时 mult = 首段末值；之后每段按斜率线性增长。
    例：NORMAL_HP_STAGE_MULT = ((15, 0.0), (30, 0.09), (60, 0.005), (999, -0.02))
        Lv10 → 1.0；Lv24 → 1.0+(24-15)×0.09=1.81；Lv45 → 2.35+(45-30)×0.005=2.43；
        Lv95 → 2.50+(95-60)×(-0.02)=1.80 ✓（61+ 段按斜率下降）
    """
    if not segments:
        return 1.0
    # 首段：≤ max_lv 用首段末值（首段斜率 0 = 恒定）
    first_max, first_v = segments[0][0], 1.0
    if lv <= first_max:
        return 1.0
    mult = 1.0
    prev_max = 0
    for max_lv, slope in segments:
        if lv <= max_lv:
            return mult + (lv - prev_max) * slope
        mult += (max_lv - prev_max) * slope
        prev_max = max_lv
    # 超出最后一段：继续按最后一段斜率
    return mult + (lv - prev_max) * segments[-1][1]


def monster_stats(lv: int, role: str, area: str | None = None) -> dict:
    """怪物属性公式：按等级 + 角色模板生成。
    role: tank(血牛) / dps(攻高) / caster(魔攻) / speedster(敏捷) / healer(治疗) / boss(首领) / elite(精英)
    area: 地图 area（'instance'=副本）；None=非副本（野外/模拟）。v156 阶段 6：
          BOSS_ATK_STAGE_MULT 只对非副本 Boss 生效（副本 Boss 走 instances atk_mult + 狂暴机制控难，
          不再叠加——叠加会让 4 人标准队后期承伤轮暴跌扛不住）。
    v56.2：hp 吃等级段放大、atk 后期放缓（见 hp_stage_mult/atk_stage_mult）
    """
    base = MONSTER_ROLE_BASE[role]
    growth = MONSTER_ROLE_GROWTH[role]
    stats = {}
    for k in base:
        # v105：dodge 为百分比属性，round 保留小数（int 会截断成 0）
        # v106：pene_phys/pene_magi 同为百分比属性，同样保留小数
        if k in ("dodge", "pene_phys", "pene_magi"):
            stats[k] = round(base[k] + growth.get(k, 0) * (lv - 1), 3)
        else:
            stats[k] = int(base[k] + growth[k] * (lv - 1))
    # 首领/精英血量系数按等级段放大，保证后期 Boss 有压迫感
    # v118+ 审计（用户拍板）：双层叠加设上限 min(·, 3.0)，抑制高等级 boss 血量 runaway
    # boss 系数达 3.0 于 Lv≥33，elite 系数达 3.0 于 Lv≥50，此后不再随等级增长
    if role == "boss":
        stats["hp"] = int(stats["hp"] * min(1 + lv * 0.06, 3.0))
    if role == "elite":
        stats["hp"] = int(stats["hp"] * min(1 + lv * 0.04, 3.0))
    # v106 穿透体系：Boss 重甲/精英精锐——防御 ×1.25/×1.15（穿透属性的需求端）
    if role == "boss":
        stats["def"] = int(stats["def"] * 1.25)
        stats["mdef"] = int(stats["mdef"] * 1.25)
    if role == "elite":
        stats["def"] = int(stats["def"] * 1.15)
        stats["mdef"] = int(stats["mdef"] * 1.15)
    # v56.2：全角色模板吃等级段曲线
    stats["hp"] = int(stats["hp"] * hp_stage_mult(lv))
    stats["atk"] = int(stats["atk"] * atk_stage_mult(lv))
    # v156 阶段 6 怪物数值修复（2026-09-01 鱼鱼拍板：裸装 4~6 轮只约束前期新手）：
    #   普通怪 HP × NORMAL_HP_STAGE_MULT（tank/dps/caster/speedster/healer）——
    #   中后期怪 HP 上调（满装击杀 1.5~2.6 轮 → 4~6 轮），前期 ≤15 恒 1.0（新手裸装 5.8 轮达标）。
    #   Boss atk × BOSS_ATK_STAGE_MULT——**仅非副本 Boss**（野外 Boss 后期攻击追上玩家防御，
    #   单发占 HP 0.9% → 8~12%）；副本 Boss 不吃（走 instances atk_mult + 狂暴机制控难，叠加会打崩 4 人队）。
    #   精英不吃本表（已有 FIELD_TIER_MULT 分档 + 独立 growth）。
    if role in ("tank", "dps", "caster", "speedster", "healer"):
        stats["hp"] = int(stats["hp"] * _stage_mult(NORMAL_HP_STAGE_MULT, lv))
    elif role == "boss" and area != "instance":
        stats["atk"] = int(stats["atk"] * _stage_mult(BOSS_ATK_STAGE_MULT, lv))
    # 重构图契约 §4.1：dot_res 异常抗性（结算时乘 (1-dot_res)）——
    # boss/elite 设置抗性，普通怪不设键（缺失=0）。cap 0.95 由结算端约束。
    if role == "boss":
        stats["dot_res"] = 0.9
    elif role == "elite":
        stats["dot_res"] = 0.8
    return stats

# v156 装备分系表：武器按 weapon_type 分系（atk/matk 分配），防具按需求属性族分系
# 物理武器（剑/匕/拳/弓/枪）atk 为主；法系武器（法杖/锤）matk 为主；盾 防御向
# 防具：str/vit（重甲）HP高、agi（皮甲）spd中、int（布甲）mdef高
WEAPON_DIST = {
    "sword":  {"atk": 1.0, "matk": 0.1},
    "dagger": {"atk": 1.0, "matk": 0.1},
    "fist":   {"atk": 1.0, "matk": 0.1},
    "bow":    {"atk": 1.0, "matk": 0.1},
    "spear":  {"atk": 0.9, "matk": 0.2},
    "staff":  {"atk": 0.1, "matk": 1.0},
    "mace":   {"atk": 0.6, "matk": 0.6},
    "shield": {"atk": 0.3, "matk": 0.3},
}
ARMOR_FAMILY = {
    "heavy": {"hp_mult": 1.6, "def_mult": 1.4, "mdef_mult": 0.7, "spd_mult": 0.6},   # str/vit 重甲
    "leather": {"hp_mult": 1.0, "def_mult": 1.0, "mdef_mult": 1.0, "spd_mult": 1.3}, # agi 皮甲
    "cloth": {"hp_mult": 0.6, "def_mult": 0.7, "mdef_mult": 1.5, "spd_mult": 0.9},   # int 布甲
}
ARMOR_FAMILY_ALIAS = {"str": "heavy", "vit": "heavy", "agi": "leather", "int": "cloth"}

def equip_stats(slot: str, lv: int, quality: str,
                weapon_type: str | None = None,
                armor_family: str | None = None) -> dict:
    """装备属性公式：部位 + 装备等级 + 品质 → 属性字典

    v156 装备分系（可选参数，默认 None = 旧行为，36 调用点零破坏）：
      - weapon_type: 武器分系（sword/dagger/fist/bow/spear 物理 atk 主；
                      staff/mace 法系 matk 主；shield 防御向）
      - armor_family: 防具分系（heavy 重甲 HP高/def高；leather 皮甲 spd高；
                       cloth 布甲 mdef高）
    只有装备生成路径显式传参才生效，其余调用保持原样。
    """
    mult = QUALITY[quality]["mult"]
    base = EQUIP_SLOT_BASE[slot]
    scaling = EQUIP_SLOT_SCALING[slot]
    stats = {}
    for k in base:
        stats[k] = int((base[k] + scaling[k] * lv) * mult)
    # v156 武器分系：按 weapon_type 重分配 atk/matk（保留部位基础总量）
    if slot == "weapon" and weapon_type and weapon_type in WEAPON_DIST:
        dist = WEAPON_DIST[weapon_type]
        total = stats.get("atk", 0) + stats.get("matk", 0)
        stats["atk"] = int(total * dist["atk"])
        stats["matk"] = int(total * dist["matk"])
    # v156 防具分系：按需求属性族调整 HP/def/mdef/spd（保留部位基础）
    if slot in ("helm", "armor", "legs", "boots") and armor_family:
        fam = ARMOR_FAMILY.get(armor_family)
        if fam:
            for k, m in (("hp", fam["hp_mult"]), ("def", fam["def_mult"]),
                         ("mdef", fam["mdef_mult"]), ("spd", fam["spd_mult"])):
                if k in stats:
                    stats[k] = int(stats[k] * m)
    if slot in ("weapon", "ring") and quality in ("blue", "purple", "orange"):
        stats["crit"] = round((0.02 + 0.01 * lv / 10) * (QUALITY[quality]["mult"] - 1), 3)
    if slot == "necklace" and quality in ("blue", "purple", "orange"):
        stats["mdef"] += int(3 * mult)
    return stats


# v101.25h3 装备属性价值权重（定价用）：HP/MP 是"量"不是"质"，1 点 HP 远不值 1 点攻击。
# 曾导致权杖(hp_fix 60) Lv.2 白装卖 560 金币 vs 铁剑 80——HP 被当攻击等价计价。
_EQUIP_VALUE_WEIGHT = {"hp": 0.1, "mp": 0.1}


def equip_value(stats: dict) -> float:
    """装备属性加权总值（定价/推导价用）：atk/matk/def/mdef/spd/crit/dodge 全价，HP/MP 按 0.1 折算"""
    return sum(v * _EQUIP_VALUE_WEIGHT.get(k, 1.0) for k, v in stats.items())

def exp_to_next(level: int) -> int:
    """升到下一级所需经验(v28 校准：系数 35→60，升级节奏放缓)"""
    return int(60 * level ** 1.45 + 50)

def monster_exp(lv: int, role: str) -> int:
    """怪物经验公式（v28 校准：base 下调，配合等级差惩罚）
    v56.2：怪 hp 变肉后经验同步补偿（×hp_mult^0.7，30 级约 ×1.8）
    v131：战斗拉长补偿 ×1.5（2026-08-27 拍板，27 章附章七同步）"""
    base = MONSTER_EXP_BASE[role]
    exp = int(base * (1 + lv * 0.9))
    return int(exp * 1.5 * (hp_stage_mult(lv) ** 0.7))


def monster_gold(lv: int, role: str) -> int:
    """怪物金币公式(v56.2：同步补偿 ×hp_mult^0.5)
    v131：战斗拉长补偿 ×1.3（2026-08-27 拍板，27 章附章七同步）"""
    base = MONSTER_GOLD_BASE[role]
    gold = int(base * (1 + lv * 0.6))
    return int(gold * 1.3 * (hp_stage_mult(lv) ** 0.5))

