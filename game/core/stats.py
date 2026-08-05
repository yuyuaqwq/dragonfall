# -*- coding: utf-8 -*-

from ..data import QUALITY


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
    base = {
        "tank":       {"hp": 60,  "atk": 8,  "def": 7,  "matk": 3,  "mdef": 6,  "spd": 6},
        "dps":        {"hp": 45,  "atk": 12, "def": 4,  "matk": 4,  "mdef": 4,  "spd": 10},
        "caster":     {"hp": 40,  "atk": 5,  "def": 3,  "matk": 14, "mdef": 8,  "spd": 9},
        "speedster":  {"hp": 35,  "atk": 9,  "def": 3,  "matk": 5,  "mdef": 4,  "spd": 16},
        "elite":      {"hp": 95,  "atk": 14, "def": 8,  "matk": 10, "mdef": 8,  "spd": 11},
        "boss":       {"hp": 160, "atk": 16, "def": 10, "matk": 12, "mdef": 10, "spd": 10},
    }[role]
    growth = {
        "tank":       {"hp": 20,  "atk": 2.5, "def": 1.6, "matk": 0.8, "mdef": 1.4, "spd": 0.3},
        "dps":        {"hp": 15,  "atk": 3.5, "def": 2.0, "matk": 1.0, "mdef": 1.2, "spd": 1.0},
        "caster":     {"hp": 11,  "atk": 1.2, "def": 1.0, "matk": 3.5, "mdef": 2.2, "spd": 0.9},
        "speedster":  {"hp": 10,  "atk": 2.6, "def": 1.0, "matk": 1.0, "mdef": 1.0, "spd": 1.8},
        # v57 精英上调：hp 32→40、atk 5.5→6.5（鱼鱼反馈前期精英太弱，2级全力量战士无脑碾压4级精英）
        "elite":      {"hp": 40,  "atk": 6.5, "def": 2.8, "matk": 5.0, "mdef": 2.8, "spd": 1.5},
        "boss":       {"hp": 58,  "atk": 7.5, "def": 3.8, "matk": 6.0, "mdef": 3.4, "spd": 1.8},
    }[role]
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
    base = {
        "weapon":   {"atk": 3,  "matk": 3},
        "helm":     {"def": 2,  "hp": 8},
        "armor":    {"def": 4,  "hp": 15},
        "legs":     {"def": 3,  "hp": 10},
        "boots":    {"def": 1,  "spd": 2},
        "ring":     {"atk": 1,  "matk": 1},
        "necklace": {"mdef": 2, "hp": 6},
    }[slot]
    scaling = {
        "weapon":   {"atk": 1.0, "matk": 1.0},
        "helm":     {"def": 0.5, "hp": 3},
        "armor":    {"def": 0.9, "hp": 6},
        "legs":     {"def": 0.65, "hp": 4},
        "boots":    {"def": 0.4, "spd": 0.5},
        "ring":     {"atk": 0.35, "matk": 0.35},
        "necklace": {"mdef": 0.6, "hp": 2.5},
    }[slot]
    stats = {}
    for k in base:
        stats[k] = int((base[k] + scaling[k] * lv) * mult)
    if slot in ("weapon", "ring") and quality in ("blue", "purple", "orange"):
        stats["crit"] = round((0.02 + 0.01 * lv / 10) * (QUALITY[quality]["mult"] - 1), 3)
    if slot == "necklace" and quality in ("blue", "purple", "orange"):
        stats["mdef"] += int(3 * mult)
    return stats

def exp_to_next(level: int) -> int:
    """升到下一级所需经验（v28 校准：系数 35→60，升级节奏放缓）"""
    return int(60 * level ** 1.45 + 50)

def monster_exp(lv: int, role: str) -> int:
    """怪物经验公式（v28 校准：base 下调，配合等级差惩罚）
    v56.2：怪 hp 变肉后经验同步补偿（×hp_mult^0.7，30 级约 ×1.8）"""
    base = {"tank": 8, "dps": 9, "caster": 10, "speedster": 9, "elite": 24, "boss": 60}[role]
    exp = int(base * (1 + lv * 0.9))
    return int(exp * (hp_stage_mult(lv) ** 0.7))


def monster_gold(lv: int, role: str) -> int:
    """怪物金币公式（v56.2：同步补偿 ×hp_mult^0.5）"""
    base = {"tank": 5, "dps": 6, "caster": 6, "speedster": 6, "elite": 20, "boss": 60}[role]
    gold = int(base * (1 + lv * 0.6))
    return int(gold * (hp_stage_mult(lv) ** 0.5))

