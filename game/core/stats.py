# -*- coding: utf-8 -*-

from ..data import (
    EQUIP_SLOT_BASE, EQUIP_SLOT_SCALING, MONSTER_EXP_BASE, MONSTER_GOLD_BASE,
    MONSTER_ROLE_BASE, MONSTER_ROLE_GROWTH, QUALITY,
)  # v102.5 模板表下沉 data/stat_templates.py


"""《剑与魔法》数据层 - stats.py"""
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
    return 0.85 - (lv - 60) * 0.004


def monster_stats(lv: int, role: str) -> dict:
    """怪物属性公式：按等级 + 角色模板生成。
    role: tank(血牛) / dps(攻高) / caster(魔攻) / speedster(敏捷) / boss(首领) / elite(精英)
    v56.2：hp 吃等级段放大、atk 后期放缓（见 hp_stage_mult/atk_stage_mult）
    """
    base = MONSTER_ROLE_BASE[role]
    growth = MONSTER_ROLE_GROWTH[role]
    stats = {}
    for k in base:
        stats[k] = int(base[k] + growth[k] * (lv - 1))
    # 首领/精英血量系数按等级段放大，保证后期 Boss 有压迫感
    if role == "boss":
        stats["hp"] = int(stats["hp"] * (1 + lv * 0.06))
    if role == "elite":
        stats["hp"] = int(stats["hp"] * (1 + lv * 0.04))
    # v56.2：全角色模板吃等级段曲线
    stats["hp"] = int(stats["hp"] * hp_stage_mult(lv))
    stats["atk"] = int(stats["atk"] * atk_stage_mult(lv))
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

