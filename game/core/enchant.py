# -*- coding: utf-8 -*-

from .stats import equip_stats
from .affix import _affix_base_value
from .constants import PCT_STATS  # v102.6 百分比显示属性
from ..data import ENCHANT_MAX_VALUE, ENCHANT_RECIPES


"""《剑与魔法》数据层 - enchant.py"""
def enchant_value(slot: str, lv: int, stat: str, big: bool = False) -> int | float:
    """附魔数值：白板基础 * ratio；大成功 1.5x；crit/dodge 固定小值"""
    rec = ENCHANT_RECIPES.get(stat)
    if not rec:
        return 0
    if stat in PCT_STATS:
        v = rec["ratio"]
    else:
        base = equip_stats(slot, lv, "white").get(stat, 0)
        if base <= 0:
            base = _affix_base_value(slot, lv, stat)
        v = max(1, int(base * rec["ratio"]))
    if big:
        v = v * 1.5
        if stat in PCT_STATS:
            v = round(v, 3)
    if stat in ENCHANT_MAX_VALUE:
        v = min(v, ENCHANT_MAX_VALUE[stat])
    return v

def enchant_match_material(stat: str, items: list) -> str | None:
    """从背包物品里找第一个匹配该附魔系的材料名(无则 None)"""
    rec = ENCHANT_RECIPES.get(stat)
    if not rec:
        return None
    for it in items:
        d = it.get("data", {})
        # F2-3：材料判定放宽——gm/部分发放路径材料入包缺 type 字段（或 type=兽材，
        #   如余烬甲片），原按 type==\"材料\" 过滤导致背包有材料却报\"没有材料\"（report_11 P1-1）。
        #   改按材料 key 规范 mat_ 前缀兜底（全库材料 key 均 mat_ 开头，v48 ID 规范）。
        if d.get("type") != "材料" and not str(it.get("key", "")).startswith("mat_"):
            continue
        name = d.get("name", "")
        if any(kw in name for kw in rec["mats"]):
            return name
    return None

