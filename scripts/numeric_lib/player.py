# -*- coding: utf-8 -*-
"""玩家真实模型（核心）：面板 + 一次行动期望伤害 + 乘区归因。

全乘区默认开启（真实玩家）；PlayerOptions 可关任意乘区做归因。
模式开关：
  attr_points  自由属性点（DEFAULT_ATTR_PTS + 每级 3 点，按职业主属性）
  tier         转职倍率 TIER_GROWTH（30/60/90 门槛）
  evolve       攻线分支 atk×1.06（evolve_path=1）
  skills       技能轴（ROTATIONS 循环，替代 普攻×1.5 粗估）
  affixes      攻击词条 ×AFFIX_MULT
  enchant      附魔暴击 +ENCHANT_CRIT
  potion       攻击/魔攻药水 +30%

验证：scripts/_tmp_calib_v2_verify.py 真实 Battle 引擎逐职误差 ≤3.2%。
"""
from dataclasses import dataclass, field

from .env import setup_env  # noqa: F401
from .constants import (
    CLASSES, TIER_GROWTH, EVOLVE_ATK_MULT, DEFAULT_ATTR_PTS, ATTR_PER_LV,
    POTION_ATK, POTION_MATK, AFFIX_MULT, ENCHANT_CRIT,
    ROTATIONS, ASSASSIN_COND_WEIGHT, DEF_DOWN_SKILLS, cls_id,
)
from data.plugins.dragonfall.game import engine as E  # noqa: E402


@dataclass
class PlayerOptions:
    """真实玩家 = 全部 True；归因分析 = 关掉对应项对比。"""
    attr_points: bool = True
    tier: bool = True
    evolve: bool = True
    skills: bool = True
    affixes: bool = True
    enchant: bool = True
    potion: bool = True

    def as_dict(self) -> dict:
        return field.asdict(self)


def tier_of(lv: int) -> int:
    return 3 if lv >= 90 else 2 if lv >= 60 else 1 if lv >= 30 else 0


def attr_pts_of(lv: int) -> int:
    return DEFAULT_ATTR_PTS + ATTR_PER_LV * (lv - 1)


def build_player(cls: str, lv: int, gear: dict | None = None,
                 opts: PlayerOptions | None = None,
                 attr: dict | None = None, potion: float = 0.0) -> dict:
    """真实玩家最终面板（E.player_final_stats）。

    - gear: make_gear 输出；None = 裸装
    - opts: PlayerOptions；None = 全开（真实玩家）
    - attr: 显式加点 dict（如 {"str": 39}）；None = 按职业主属性自动满点（opts.attr_points 时）
    - potion: 显式药水倍率（0.30）；opts.potion 为 True 时自动按职业取默认
    """
    opts = opts or PlayerOptions()
    tid = tier_of(lv) if opts.tier else 0
    attrs = None
    if opts.attr_points or attr is not None:
        if attr is not None:
            attrs = attr
        else:
            main_attr = [c[3] for c in CLASSES if c[1] == cls_id(cls)][0]
            attrs = {main_attr: attr_pts_of(lv)}
    st = E.player_final_stats(
        cls_id(cls), lv, gear or {}, tid,
        attrs,
        evolve_path=1 if (opts.evolve and tid > 0) else 0,
        title_bonus=None, race=None,
    )
    if potion:
        # 药水走战斗内 buff：只乘主攻端（与 _tmp_calib_v2 一致；potion 由调用方显式传）
        if st["atk"] >= st["matk"]:
            st["atk"] = int(st["atk"] * (1 + potion))
        else:
            st["matk"] = int(st["matk"] * (1 + potion))
    return st


def panel(cls: str, lv: int, gear: dict | None = None,
          opts: PlayerOptions | None = None, attr: dict | None = None) -> dict:
    """面板别名（不带药水），CLI/表格友好。"""
    return build_player(cls, lv, gear, opts, attr, potion=0.0)


def _is_phys(cls: str) -> bool:
    return [c[2] for c in CLASSES if c[1] == cls_id(cls)][0] == "phys"


def _skill_dmg(st: dict, cls: str, edef: int, mdef: int) -> float:
    """技能轴一次行动期望伤害（E.calc_damage 实算，variance=0；技能倍率 E.skill_info 实读）。"""
    phys = _is_phys(cls)
    tot, wsum = 0.0, 0.0
    for name, w in ROTATIONS.get(cls_id(cls), []):
        info = E.skill_info(cls_id(cls), name)
        if not info:
            continue
        stat = st["atk"] if phys else st["matk"]
        def_mult = DEF_DOWN_SKILLS.get(cls_id(cls), {}).get(name, 1.0)
        d = (mdef if not phys else edef) * def_mult
        power = float(info.get("power", 0)) * E.skill_power_mult(1, info)
        multi = int(info.get("multi", 1))
        pene = st.get("pene_phys" if phys else "pene_magi", 0)
        pflat = st.get("pene_flat" if phys else "pene_mflat", 0)
        dt = "phys" if phys else "magi"
        if info.get("pierce"):
            base = E.calc_damage(int(stat * power), 0, pierce=True, dmg_type=dt, variance=0.0)
        else:
            base = E.calc_damage(int(stat * power), int(d), pene_pct=pene, pene_flat=pflat,
                                 dmg_type=dt, variance=0.0)
        dmg = base * multi
        if cls_id(cls) == "cls_ci_ke" and name == "双刃乱舞":
            dmg *= ASSASSIN_COND_WEIGHT
        if cls_id(cls) == "cls_wu_seng" and name == "碎骨拳":
            dmg *= 1 / 3.0   # 3 气 → 每 3 行动 1 发
        tot += dmg * w
        wsum += w
    return tot / max(wsum, 1.0)


def _basic_dmg(st: dict, cls: str, edef: int, mdef: int) -> float:
    phys = _is_phys(cls)
    stat = st["atk"] if phys else st["matk"]
    d = edef if phys else mdef
    return E.calc_damage(int(stat), int(d), variance=0.0, dmg_type="phys" if phys else "magi")


def _crit_mult(st: dict, extra_crit: float = 0.0) -> float:
    """暴击期望 + 幸运一击（暴击后 30% 概率追加 50% 伤害，battle.py 引擎路径）。"""
    crit = min(float(st.get("crit", 0) or 0) + extra_crit, 0.5)
    return 1.0 + crit * (0.5 + float(st.get("crit_dmg", 0) or 0)) + crit * 0.3 * 0.5


def per_action_dmg(cls: str, lv: int, gear: dict | None, edef: int, mdef: int,
                   opts: PlayerOptions | None = None, potion_on: bool = False,
                   crit: bool = True) -> float:
    """该玩家一次行动（当前技能轴/普攻）对 (edef, mdef) 目标的期望伤害。

    opts.skills=False → 纯普攻口径（胜率矩阵对齐用，与 tests/numeric_sim 纯普攻一致）。
    affixes/enchant/potion 只在 opts 对应开关为 True 时乘入。
    crit=False → 不含暴击期望（legacy 旧模型对照用；旧工具没有任何暴击期望）。
    """
    opts = opts or PlayerOptions()
    potion = 0.0
    if opts.potion and potion_on:
        st_tmp = build_player(cls, lv, gear, PlayerOptions(
            attr_points=opts.attr_points, tier=opts.tier, evolve=opts.evolve,
            skills=False, affixes=False, enchant=False, potion=False))
        potion = POTION_ATK if st_tmp["atk"] >= st_tmp["matk"] else POTION_MATK
    st = build_player(cls, lv, gear, opts, potion=potion)
    if opts.skills:
        d = _skill_dmg(st, cls, edef, mdef)
    else:
        d = _basic_dmg(st, cls, edef, mdef)
    if crit:
        d *= _crit_mult(st, extra_crit=ENCHANT_CRIT if opts.enchant else 0.0)
    if opts.affixes:
        d *= AFFIX_MULT
    return d


def dmg_budget(cls: str, lv: int, gear: dict | None, edef: int, mdef: int,
               opts: PlayerOptions | None = None) -> dict:
    """乘区归因表：逐项开关对比 → 每项单独倍率（基准=全关）。

    返回 {"base": 全关伤害, "total": 全开伤害, "total_mult": 累乘, "items": {乘区名: 倍率}}
    """
    base = PlayerOptions(attr_points=False, tier=False, evolve=False,
                         skills=False, affixes=False, enchant=False, potion=False)
    d_base = per_action_dmg(cls, lv, gear, edef, mdef, base, potion_on=False)
    total = per_action_dmg(cls, lv, gear, edef, mdef, opts or PlayerOptions(), potion_on=True)
    items = {}
    names = {
        "attr_points": "自由属性点", "tier": "tier转职", "evolve": "攻线分支",
        "skills": "技能轴", "affixes": "词条", "enchant": "附魔", "potion": "药水",
    }
    for key, label in names.items():
        o = PlayerOptions(attr_points=False, tier=False, evolve=False,
                          skills=False, affixes=False, enchant=False, potion=False)
        if key == "evolve":    # 攻线分支依赖转职（tier>0 才生效）→ 归因时联动
            o.tier = True
        setattr(o, key, True)
        o.evolve = o.evolve and (o.tier or key == "evolve" and o.tier)
        d_one = per_action_dmg(cls, lv, gear, edef, mdef, o, potion_on=(key == "potion"))
        items[label] = d_one / max(d_base, 1)
    return {
        "base": d_base, "total": total,
        "total_mult": total / max(d_base, 1),
        "items": items,
    }