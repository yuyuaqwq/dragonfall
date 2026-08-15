# -*- coding: utf-8 -*-

from ..data import (
    EQUIP_SLOT_BASE, EQUIP_SLOT_SCALING, MONSTER_EXP_BASE, MONSTER_GOLD_BASE,
    MONSTER_ROLE_BASE, MONSTER_ROLE_GROWTH, QUALITY,
)  # v102.5 模板表下沉 data/stat_templates.py


"""奥兰迪亚·余烬纪年数据层 - stats.py"""
# v56.2 怪物等级段曲线（鱼鱼拍板调数值，根治"后期大招乱秒"）
# hp：16 级起渐入放大（30 级 ×2.2 / 60 级 ×3.4 / 90 级 ×4.3），≤15 级完全不变
# atk：31 级起放缓（60 级 ×0.85 / 90 级 ×0.73），避免后期怪攻击成长超过玩家防御
def hp_stage_mult(lv: int) -> float:
    if lv <= 15:
        return 1.0
    if lv <= 30:
        return 1.0 + (lv - 15) * 0.08
    if lv <= 60:
        return 2.2 + (lv - 30) * 0.04
    return 3.4 + (lv - 60) * 0.03


def atk_stage_mult(lv: int) -> float:
    if lv <= 30:
        return 1.0
    if lv <= 60:
        return 1.0 - (lv - 30) * 0.005
    # 防御性下限，防未来提高等级上限时出现负 atk（当前 ≤100 级不生效）
    return max(0.2, 0.85 - (lv - 60) * 0.004)


def monster_stats(lv: int, role: str) -> dict:
    """怪物属性公式：按等级 + 角色模板生成。
    role: tank(血牛) / dps(攻高) / caster(魔攻) / speedster(敏捷) / healer(治疗) / boss(首领) / elite(精英)
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
    # 重构图契约 §4.1：dot_res 异常抗性（结算时乘 (1-dot_res)）——
    # boss/elite 设置抗性，普通怪不设键（缺失=0）。cap 0.95 由结算端约束。
    if role == "boss":
        stats["dot_res"] = 0.9
    elif role == "elite":
        stats["dot_res"] = 0.8
    return stats

def equip_stats(slot: str, lv: int, quality: str) -> dict:
    """装备属性公式：部位 + 装备等级 + 品质 → 属性字典"""
    mult = QUALITY[quality]["mult"]
    base = EQUIP_SLOT_BASE[slot]
    scaling = EQUIP_SLOT_SCALING[slot]
    stats = {}
    for k in base:
        stats[k] = int((base[k] + scaling[k] * lv) * mult)
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
    v56.2：怪 hp 变肉后经验同步补偿（×hp_mult^0.7，30 级约 ×1.8）"""
    base = MONSTER_EXP_BASE[role]
    exp = int(base * (1 + lv * 0.9))
    return int(exp * (hp_stage_mult(lv) ** 0.7))


def monster_gold(lv: int, role: str) -> int:
    """怪物金币公式(v56.2：同步补偿 ×hp_mult^0.5)"""
    base = MONSTER_GOLD_BASE[role]
    gold = int(base * (1 + lv * 0.6))
    return int(gold * (hp_stage_mult(lv) ** 0.5))

