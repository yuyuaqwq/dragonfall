# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - affix.py（阶段八重写，2026-08-06）

20 章特色词条系统核心逻辑：
- roll_affixes：按品质随机词条池（武器/防具按部位过滤）→ 返回词条 ID 列表
- fixed_affixes：名册装备固定词条（20 章 3.x 系列主题）
- stat_affix_stats：常驻属性词条折算进装备 stats（crit_up/dodge/hp_up/swift）
- random_req：随机装备的属性需求估算（按部位/武器类型）
- 触发型词条（on_hit/on_taken/turn_start/battle_start/passive）由 battle.py 消费
"""

import random

from ..data import (AFFIXES, AFFIX_FALLBACK, AFFIX_POOL_BY_QUALITY,
                    LEGENDARY_EFFECTS, SERIES_FIXED_AFFIX)

# 词条触发时机分组（battle 挂点用）
TRIGGER_TYPES = {"stat", "on_hit", "on_taken", "turn_start", "battle_start", "passive"}


def _affix_base_value(slot: str, lv: int, stat: str) -> int:
    """附魔数值兜底：优先部位白板属性，无则用保底模板(旧词条系统遗留，enchant 用)"""
    from .stats import equip_stats
    base = equip_stats(slot, lv, "white")
    if base.get(stat, 0) > 0:
        return base[stat]
    fb = AFFIX_FALLBACK.get(stat, (2, 1.0))
    return int(fb[0] + fb[1] * lv)

# 随机装备属性需求估算：按部位/武器类型 → 主属性
_REQ_STAT_BY_SLOT = {
    "weapon": {"sword": "str", "mace": "str", "fist": "str", "spear": "str", "shield": "str",
               "bow": "agi", "dagger": "agi", "staff": "int"},
    "helm": "vit", "armor": "vit", "legs": "vit",
    "boots": "agi", "ring": "agi", "necklace": "int",
}

# 常驻属性词条 → 折算方式（生成时并入装备 stats）
# crit/dodge 为小数概率直接加；hp/spd 按装备基础值百分比折算
_STAT_AFFIX_FX = {
    "crit_up": {"stat": "crit", "pct": None, "flat": 0.05},
    "dodge": {"stat": "dodge", "pct": None, "flat": 0.05},
    "hp_up": {"stat": "hp", "pct": 0.05},
    "swift": {"stat": "spd", "pct": 0.05},
}


def roll_affixes(slot: str, lv: int, quality: str) -> list:
    """按品质生成随机词条（20 章 4.2 随机池 + 部位过滤）。

    返回词条 ID 列表；白色 0 条、绿色 1 条、蓝色 2 条、紫色 3 条、橙色 3 条。
    （名册固定词条不在随机池，由 fixed_affixes 提供。）
    """
    n = {"green": 1, "blue": 2, "purple": 3, "orange": 3}.get(quality, 0)
    if not n:
        return []
    pool = AFFIX_POOL_BY_QUALITY.get(quality, AFFIX_POOL_BY_QUALITY["orange"])
    # 按部位过滤：武器只出攻击词条，防具只出防御词条（kind 归属）
    want_kind = "attack" if slot == "weapon" else "defense"
    pool = [a for a in pool if AFFIXES[a]["kind"] == want_kind]
    if not pool:
        return []
    return random.sample(pool, min(n, len(pool)))


def fixed_affixes(name: str) -> list:
    """名册装备固定词条(20 章 3.x 系列主题，无随机)"""
    return list(SERIES_FIXED_AFFIX.get(name, []))


def stat_affix_stats(affix_ids: list, slot: str, lv: int) -> dict:
    """常驻属性词条折算成装备 stats 加成（crit/dodge 直接加，hp/spd 按基础值百分比）。

    返回 {属性: 加值}；触发型词条不在这里折算（由 battle 消费）。
    """
    out = {}
    for aid in affix_ids:
        fx = _STAT_AFFIX_FX.get(aid)
        if not fx:
            continue
        stat = fx["stat"]
        if fx.get("flat") is not None:
            out[stat] = round(out.get(stat, 0) + fx["flat"], 4)
        else:
            # 按装备基础值百分比折算（生成时已拿到 equip_stats 基础）
            from .stats import equip_stats
            base = equip_stats(slot, lv, "white").get(stat, 0)
            add = int(base * fx["pct"]) if base else max(1, lv // 10)
            out[stat] = out.get(stat, 0) + max(1, add)
    return out


def random_req(slot: str, lv: int, weapon_type: str | None = None) -> dict:
    """随机装备（非名册）的属性需求估算：主属性 + 5 + lv//5。

    名册装备用策划案表（EQUIP_ROSTER.req），此函数仅服务随机掉落/奖励装备。
    """
    if slot == "weapon":
        stat = _REQ_STAT_BY_SLOT["weapon"].get(weapon_type or "sword", "str")
    else:
        stat = _REQ_STAT_BY_SLOT.get(slot, "vit")
    return {stat: 5 + lv // 5}


def affix_label(aid: str) -> str:
    """词条显示短名(装备详情/词条表)"""
    info = AFFIXES.get(aid) or LEGENDARY_EFFECTS.get(aid)
    return info["name"] if info else aid
