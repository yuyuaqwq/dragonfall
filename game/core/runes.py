# -*- coding: utf-8 -*-

from ..data import RUNES, RUNE_CONFLICTS, RUNE_LEVEL_ROMAN


"""《剑与魔法》数据层 - runes.py"""
def rune_value(effect: str, lvl: int):
    """符文效果数值：effect + 等级 → 数值(用于战斗结算)"""
    for name, r in RUNES.items():
        if r["effect"] == effect:
            return r["lvl"].get(lvl, r["lvl"].get(1, 0))
    return 0

def rune_conflict(effect_a: str, effect_b: str) -> bool:
    """两个符文效果是否冲突(同件装备不能共存)"""
    if effect_a == effect_b:
        return False
    for (x, y) in RUNE_CONFLICTS:
        if (effect_a == x and effect_b == y) or (effect_a == y and effect_b == x):
            return True
    return False

def rune_item(effect: str, lvl: int = 1) -> dict:
    """构造符文物品 data(掉落/奖励用)"""
    for name, r in RUNES.items():
        if r["effect"] == effect:
            lv = min(3, max(1, lvl))
            roman = RUNE_LEVEL_ROMAN[lv]
            desc = r["desc"]
            if "{" in desc:
                try:
                    if "v1" in desc:
                        v1, v2 = r["lvl"][lv]
                        desc = desc.format(v1=int(v1 * 100), v2=int(v2 * 100))
                    else:
                        v = r["lvl"][lv]
                        if isinstance(v, float) and v < 1:
                            v = int(v * 100)
                        desc = desc.format(v=v)
                except Exception:
                    pass
            return {
                "name": f"{r['quality']}符文·{r.get('name', name)} {roman}",
                "type": "符文",
                "effect": effect,
                "lvl": lv,
                "quality": r["quality"],
                "price": r["cost"] // 2,
                "desc": desc,
            }
    return None

