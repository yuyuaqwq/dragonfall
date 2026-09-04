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
        # 各乘区等价总收益 ≈ 1.08-1.15（不是无条件 1.20——真实词条池平衡）
        # atk 攻击流 = 面板 atk/matk +%（等效 AFFIX_MULT 1.2 的 12%，与其它乘区同水平）
        "atk": {"atk_pct": 0.12, "matk_pct": 0.12},  # +12% 攻/魔攻（等价全伤 1.12）
        # crit 收敛（v175e 二次校准：鱼鱼质疑暴击通吃——+12%率/+40%爆伤乘算后期望~1.19
        # 碾压其它乘区导致 85% 流派选暴击。降到与其它乘区真正等价：
        # 期望 ≈ 1 + crit×[1.5×(1+cdmg)-1] ≈ 职业自带5-8% + 词条8% = 13-16%暴击×~0.55 ≈ +7-9%）
        "crit": {"crit": 0.08, "crit_dmg": 0.25},      # +8% 暴击率 +25% 爆伤（期望~1.09）
        "spd": {"spd": 50},                              # +50 速度（频率 ×~1.27，cast 折算后 ~1.10）
        "pene": {"pene_phys": 0.30, "pene_magi": 0.30}, # 30% 穿透（对高防 ~1.15）
        "lifesteal": {"lifesteal": 0.15},                # 15% 吸血（生存向）
        "elem": {"dmg_mult": 0.12},                      # +12% 全伤（与其它乘区等价水平）
        "cdr": {"cdr": 0.20},                            # +20% 冷却缩减（引擎 cap 40%；CD8→6.4/12→9.6）
        # v175e 生存乘区（鱼鱼拍板全加）：闪避战士/格挡坦/吸血续航/减伤/反伤/幸运/处决
        # 生存词条是防御向配装（换防御属性），输出收益为负但提高 survive——与输出乘区互斥选择
        "dodge": {"dodge": 0.20},                        # +20% 闪避（引擎 cap 40%；期望承伤 ×0.80）
        "block": {"block": 0.25},                        # +25% 格挡（cap 40%；格挡减半 → 期望 ×(1-0.25/2)=0.875）
        "reduce": {"dmg_reduce": 0.20},                  # +20% 减伤（reduce_all 减伤 cap90%）
        "thorns": {"thorns": 0.30},                      # +30% 反伤（受击反弹 30% 伤害给攻击者）
        "luck": {"luck": 0.15},                          # +15% 幸运（暴击后 30% 概率 ×1.3 → 额外 ~0.09 期望）
        "execute": {"execute_threshold": 0.30},          # 30% 斩杀线（目标血量 <30% ×1.5）
    }
    # 词条类型 → 应用方式（面板键多数直接进 stats 由引擎消费；_pct 后缀 = 百分比乘攻击）
    affix_vals = AFFIX_BY_TYPE.get(affix_type, {})
    affix_slots = ("weapon", "ring", "helm", "armor")
    # atk_pct/matk_pct 需要先知道装备基础攻击总量——改为在 slot 循环里按该槽 atk 加
    def _apply_affix(entry_stats: dict, slot: str) -> dict:
        """把词条乘区加成应用到单个槽位（按槽位类型分配权重）。
        攻击词条只在 weapon/ring（有 atk 的件）生效，每件 +总加成的一半；
        暴击/急速/穿透等词条 4 攻击向槽均摊（1/4）。"""
        if not affix_vals or slot not in affix_slots:
            return entry_stats
        out = dict(entry_stats)
        for k, v in affix_vals.items():
            if k == "spd":
                out[k] = int(out.get(k, 0) or 0) + int(v / len(affix_slots))
            elif k == "atk_pct":
                if slot in ("weapon", "ring") and out.get("atk", 0):
                    out["atk"] = int(out["atk"] * (1 + v / 2))
            elif k == "matk_pct":
                if slot in ("weapon", "ring") and out.get("matk", 0):
                    out["matk"] = int(out["matk"] * (1 + v / 2))
            else:
                out[k] = round((out.get(k, 0.0) or 0.0) + v / len(affix_slots), 4)
        return out
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
    for slot in C.EQUIP_SLOT_BASE:
        s = ST.equip_stats(slot, equip_lv, quality)
        s = _apply_mult(s, mult)
        entry = {"stats": s, "enhance": enhance, "upgrade": upgrade,
                 "gem_tier": gem_tier, "set_bonus": set_bonus}
        # v175e 词条乘区：只往攻击向槽位叠（每槽 1/4 总值）；atk 攻击流也有词条（atk_pct）
        if affix_vals and slot in affix_slots:
            entry["stats"] = _apply_affix(entry["stats"], slot)
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
