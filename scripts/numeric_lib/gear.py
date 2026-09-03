# -*- coding: utf-8 -*-
"""装备工厂：基础面板装备（品质×强化×升级×幸运宝石×套装）+ 档位预设。

口径：
  equip_stats(slot, lv, quality) = (slot_base + slot_scaling×lv) × QUALITY.mult  （32 章二）
  强化：ENHANCE_TABLE[enhance].mult 直接乘装备面板（32 章 2.2，+9 = 2.10）
  升级：真等级化（v172）——make_gear 无 upgrade 乘区，upgrade 参数语义 = "装备 lv = level + upgrade"
  （养成拉高装备 lv，属性经 equip_stats 重算，engine 同款无 upg_mult）。
  幸运宝石：GEM_TIERS[gem_tier].mult（单孔，属性随机取 atk/matk/def 之一，走面板 sockets）
  套装：set_bonus 简化 +8% 主属性（防御向 def；引擎 set_bonus_2 消费需 2 件同套，这里
        用橙装双槽位同套激活，见 make_gear 实现）
  词条/附魔不走面板，走 player.per_action_dmg 的乘区开关（归因清晰）。

向后兼容：不传新参数（upgrade/gem_tier/set_bonus）时行为与旧版完全一致。
"""
from .env import setup_env  # noqa: F401
from data.plugins.dragonfall.game import content as C  # noqa: E402
from data.plugins.dragonfall.game.core import stats as ST  # noqa: E402

# 幸运宝石随机属性池（v136 原石系统面板属性子集；百分比走 PCT_STATS 面板）
GEM_STAT_POOL = ("atk", "matk", "def")

# 套装简化口径：+8% 主属性（任务卡定；防具 def 也属主属性面板）
SET_MAIN_STAT = "atk"     # 输出向主属性（武器/戒指槽）
SET_MAIN_DEF = "def"      # 防具向主属性（头盔/胸甲/护腿/靴子槽）
SET_BONUS_PCT = 0.08      # 2 件套 +8% 主属性（v136 职业套 bonus_2 常见值 0.08）


def _apply_mult(s: dict, mult: float) -> dict:
    """面板乘区：int 截断（engine 同款）。"""
    if mult <= 1.0:
        return dict(s)
    return {k: int(v * mult) for k, v in s.items()}


def make_gear(level: int, quality: str = "blue", enhance: int = 0,
              upgrade: int = 0, gem_tier: int = 0, set_bonus: bool = False) -> dict:
    """全部部位基础装备：equip_stats × 强化 × 升级 + 幸运宝石 + 套装。

    返回 {slot: {"stats": {...}, "enhance": n, "upgrade": n, "gem_tier": n,
                 "set_bonus": bool, "sockets": {...}?, "set": str?}}
    - upgrade:  真等级化养成差（v172）：装备 lv = level + upgrade，属性经
                equip_stats(slot, lv+upgrade, quality) 重算（engine 同款无 upg_mult 乘区）
    - gem_tier: GEM_TIERS[gem_tier]["mult"]（单孔；属性随机取 atk/matk/def 之一，
                固定种子可复现；写入 sockets 由 engine 原石段消费）
    - set_bonus: 套装 2 件同套激活 → 主属性 +SET_BONUS_PCT（简化 8%）。
                橙装双槽（weapon+ring 攻击向 / helm+armor 防御向）套烈焰套/铁皮套，
                引擎 set_bonus_2 按 class 折扣消费（本职业 100%）。
    """
    gear = {}
    mult = C.ENHANCE_TABLE.get(enhance, {}).get("mult", 1.0)
    # v172 真等级化：升级 = 装备 lv +upgrade（属性随 equip_stats 重算，无倍率乘区）
    equip_lv = level + int(upgrade or 0)
    gem_mult = C.GEM_TIERS.get(gem_tier, {}).get("mult", 0.0)
    gem_stat = None
    if gem_tier > 0:
        # 固定种子：与 numeric_sim 同源可复现（seed = level % 7 + slot hash）
        gem_stat = GEM_STAT_POOL[(level + 1) % len(GEM_STAT_POOL)]
    for slot in C.EQUIP_SLOT_BASE:
        s = ST.equip_stats(slot, equip_lv, quality)
        s = _apply_mult(s, mult)
        entry = {"stats": s, "enhance": enhance, "upgrade": upgrade,
                 "gem_tier": gem_tier, "set_bonus": set_bonus}
        if gem_stat:
            entry["sockets"] = {"S1": {"stats": {gem_stat: round(gem_mult, 6)}}}
        if set_bonus:
            # 2 件同套激活（攻击向武器+戒指 / 防御向头盔+胸甲）；蓝装套烈焰/铁皮
            set_name = None
            if slot in ("weapon", "ring"):
                set_name = "烈焰"      # bonus_2 atk 0.12  → 但按简化口径只算 8%
            elif slot in ("helm", "armor"):
                set_name = "铁皮套"    # 职业套 cls_zhan_shi（引擎 class 折扣）
            if set_name:
                entry["set"] = set_name
        gear[slot] = entry
    return gear


def gear_loadout(level: int, loadout: str) -> dict:
    """按档位名取装备：LOADOUTS 表（constants.py）→ make_gear。
    loadout ∈ naked / solo_low / solo_mid / team_mid / team_purple9 / team_orange9
             / solo_mid_upgrade / team_max_full / legacy
    naked = 裸装 {}（对照组）；legacy = 旧残疾模型档（蓝+0 无乘区）。"""
    from .constants import LOADOUTS
    cfg = LOADOUTS[loadout]
    if loadout == "naked":
        return {}
    return make_gear(level,
                     cfg.get("quality", "blue"),
                     cfg.get("enhance", 0),
                     cfg.get("upgrade", 0),
                     cfg.get("gem_tier", 0),
                     cfg.get("set_bonus", False))
