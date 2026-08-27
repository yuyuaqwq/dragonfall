# -*- coding: utf-8 -*-
"""装备工厂：基础面板装备（品质×强化）+ 档位预设。

口径：
  equip_stats(slot, lv, quality) = (slot_base + slot_scaling×lv) × QUALITY.mult  （32 章二）
  强化：ENHANCE_TABLE[enhance].mult 直接乘装备面板（32 章 2.2，+9 = 2.62）
  词条/附魔不走面板，走 player.per_action_dmg 的乘区开关（归因清晰）。
"""
from .env import setup_env  # noqa: F401
from data.plugins.dragonfall.game import content as C  # noqa: E402
from data.plugins.dragonfall.game.core import stats as ST  # noqa: E402


def make_gear(level: int, quality: str = "blue", enhance: int = 0) -> dict:
    """全部部位基础装备：equip_stats(slot, level, quality) × 强化倍率。
    返回 {slot: {"stats": {...}, "enhance": n}}（与 numeric_calibration 旧实现同构）。"""
    gear = {}
    for slot in C.EQUIP_SLOT_BASE:
        s = ST.equip_stats(slot, level, quality)
        if enhance > 0:
            mult = C.ENHANCE_TABLE.get(enhance, {}).get("mult", 1.0)
            s = {k: int(v * mult) for k, v in s.items()}
        gear[slot] = {"stats": s, "enhance": enhance}
    return gear


def gear_loadout(level: int, loadout: str) -> dict:
    """按档位名取装备：LOADOUTS 表（constants.py）→ make_gear。
    loadout ∈ naked / solo_low / solo_mid / team_mid / team_purple9 / team_orange9 / legacy
    naked = 裸装 {}（对照组）；legacy = 旧残疾模型档（蓝+0 无乘区）。"""
    from .constants import LOADOUTS
    cfg = LOADOUTS[loadout]
    if loadout == "naked":
        return {}
    return make_gear(level, cfg.get("quality", "blue"), cfg.get("enhance", 0))