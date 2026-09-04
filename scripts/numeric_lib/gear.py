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
              upgrade: int = 0, gem_tier: int = 0, set_bonus: bool = False,
              affix_type: str = "atk") -> dict:
    """全部部位基础装备：equip_stats × 强化 × 升级 + 幸运宝石 + 套装 + 词条乘区。

    返回 {slot: {"stats": {...}, "enhance": n, "upgrade": n, "gem_tier": n,
                 "set_bonus": bool, "sockets": {...}?, "set": str?}}
    - upgrade:  真等级化养成差（v172）：装备 lv = level + upgrade，属性经
                equip_stats(slot, lv+upgrade, quality) 重算（engine 同款无 upg_mult 乘区）
    - gem_tier: GEM_TIERS[gem_tier]["mult"]（单孔；属性随机取 atk/matk/def 之一，
                固定种子可复现；写入 sockets 由 engine 原石段消费）
    - set_bonus: 套装 2 件同套激活 → 主属性 +SET_BONUS_PCT（简化 8%）。
                橙装双槽（weapon+ring 攻击向 / helm+armor 防御向）套烈焰套/铁皮套，
                引擎 set_bonus_2 按 class 折扣消费（本职业 100%）。
    - affix_type: v175e 词条乘区流派（暴击法师/急速游侠等玩法建模）：
        atk       攻击词条（默认，×AFFIX_MULT 攻击 1.20）
        crit      暴击流：暴击率 +CRIT_AFFIX_CRIT，暴伤 +CRIT_AFFIX_CDMG
        spd       急速流：速度 +SPD_AFFIX_SPD
        pene      穿透流：物/魔穿透 +PENE_AFFIX
        lifesteal 吸血续航流：吸血 +LS_AFFIX
        elem      元素增伤流：对应元素增伤 +ELEM_AFFIX_DMG
      各流派总等价收益 ≈ AFFIX_MULT(1.20) 量级（同强度不同分配，公平比较）。
      词条乘区以面板键写入 stats（crit/crit_dmg/spd/pene_phys/pene_magi/lifesteal/
      elem_dmg_*），由引擎/期望引擎消费。
    """
    # v175e 词条乘区基准（蓝装 2 词条总收益 ≈ ×1.20 等价）
    AFFIX_BY_TYPE = {
        # 面板键 → 加成值（加法键直接加面板；比例键按面板比例）
        "crit": {"crit": 0.10, "crit_dmg": 0.30},      # +10% 暴击率 +30% 爆伤
        "spd": {"spd": 60},                              # +60 速度（≈2倍速 → 频率×1.41）
        "pene": {"pene_phys": 0.20, "pene_magi": 0.20}, # 20% 穿透
        "lifesteal": {"lifesteal": 0.15},                # 15% 吸血（输出等价 ~0.3）
        "elem": {"dmg_mult": 0.20},                      # +20% 全伤（元素增伤近似）
    }
    gear = {}
    mult = C.ENHANCE_TABLE.get(enhance, {}).get("mult", 1.0)
    # v172 真等级化：升级 = 装备 lv +upgrade（属性随 equip_stats 重算，无倍率乘区）
    equip_lv = level + int(upgrade or 0)
    gem_mult = C.GEM_TIERS.get(gem_tier, {}).get("mult", 0.0)
    gem_stat = None
    if gem_tier > 0:
        # 固定种子：与 numeric_sim 同源可复现（seed = level % 7 + slot hash）
        gem_stat = GEM_STAT_POOL[(level + 1) % len(GEM_STAT_POOL)]
    # v175e：词条乘区总量拆分到 4 个槽位（武器/戒指 攻击向 + 头盔/胸甲 半攻击向），
    # 每槽 1/4，累加后 ≈ 基准总值；防御槽（腿/靴）不叠输出词条（真实配装逻辑）
    affix_vals = AFFIX_BY_TYPE.get(affix_type, {})
    affix_slots = ("weapon", "ring", "helm", "armor")
    for slot in C.EQUIP_SLOT_BASE:
        s = ST.equip_stats(slot, equip_lv, quality)
        s = _apply_mult(s, mult)
        entry = {"stats": s, "enhance": enhance, "upgrade": upgrade,
                 "gem_tier": gem_tier, "set_bonus": set_bonus}
        # v175e 词条乘区：只往攻击向槽位叠（每槽 1/4 总值）
        if affix_type != "atk" and affix_vals and slot in affix_slots:
            for k, v in affix_vals.items():
                # 比例键转面板小数；速度等整数键直接加
                if k == "spd":
                    entry["stats"][k] = int(entry["stats"].get(k, 0) or 0) + int(v / len(affix_slots))
                else:
                    entry["stats"][k] = round((entry["stats"].get(k, 0.0) or 0.0) + v / len(affix_slots), 4)
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
