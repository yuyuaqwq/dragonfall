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
    SPD_REF, SPD_CT_CAP, MECH_MULT,
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
    # v161 表达式变量：等级注入（exprs 公式 player_lv 用；skill_lv 由调用方按需覆盖）
    st["_player_lv"] = int(lv or 1)
    st["level"] = int(lv or 1)
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


def _skill_dmg(st: dict, cls: str, edef: int, mdef: int, extra_crit: float = 0.0) -> float:
    """技能轴一次行动期望伤害（E.calc_damage 实算，variance=0；技能倍率 E.skill_info 实读）。
    v133：暴击/幸运期望按每技能 multi 折算（多段仅首段吃暴击）。
    v161：expr/exprs 表达式技能走 skill_expr_preview（Lv.1 保守档，与 ROTATIONS 口径一致），
          power 字段保留作 fallback（单轨迁移过渡期双兼容）。"""
    phys = _is_phys(cls)
    # v161 ROTATIONS 按阶段选技能：[(max_lv, 技能名, 权重)]，max_lv 是该技能适用的等级上限，
    # 选第一个 max_lv >= 当前等级的档（Lv45 → (60, T1) 而非 (30, 基础)）；超过全档用最后一档
    lvl = int(st.get("level", 1) or 1)
    rot = ROTATIONS.get(cls_id(cls), [])
    cand = [t for t in rot if t[0] >= lvl]
    if not cand:
        cand = [rot[-1]] if rot else []   # lv 超过所有档（如 95>90）→ 用最高阶（999 毕业档）
    else:
        top_lv = min(t[0] for t in cand)  # 最近的上界
        cand = [t for t in cand if t[0] == top_lv]
    tot, wsum = 0.0, 0.0
    # v161 表达式预览变量注入（player_lv 供 exprs 公式使用；skill_lv=Lv.1 保守档）
    _st_expr = dict(st)
    _st_expr["_player_lv"] = int(st.get("level", 1) or 1)
    _st_expr["_skill_lv"] = 1
    for max_lv, name, w in cand:
        info = E.skill_info(cls_id(cls), name)
        if not info:
            continue
        stat = st["atk"] if phys else st["matk"]
        def_mult = DEF_DOWN_SKILLS.get(cls_id(cls), {}).get(name, 1.0)
        d = (mdef if not phys else edef) * def_mult
        multi = int(info.get("hits", info.get("multi", 1)))   # v153：多段用 hits 字段（旧 multi 字段已删）
        pene = st.get("pene_phys" if phys else "pene_magi", 0)
        pflat = st.get("pene_flat" if phys else "pene_mflat", 0)
        dt = "phys" if phys else "magi"
        # v161 表达式技能：代入面板算 Lv.1 期望基础值（variance=0，与引擎同口径）
        _expr_val = E.skill_expr_preview(info, 1, _st_expr)
        if _expr_val > 0:
            base_raw = _expr_val
        else:
            power = float(info.get("power", 0)) * E.skill_power_mult(1, info)
            # v156 技能基础值（保底伤害）：与引擎同口径（flat = BASE + 玩家等级×PER + 技能等级×PER_SKILL）
            # ⚠️ player_lv 传 1（v161 前旧口径：_skill_dmg 无 level 键，st.get("level",1)=1；
            #     build_player 注入 level 后若传实际等级会改变数值，破坏门禁基线）
            skill_flat = E.skill_flat_value(1, 1, info)
            base_raw = int(stat * power) + skill_flat
        if info.get("pierce"):
            base = E.calc_damage(int(base_raw), 0, pierce=True, dmg_type=dt, variance=0.0)
        else:
            base = E.calc_damage(int(base_raw), int(d), pene_pct=pene, pene_flat=pflat,
                                 dmg_type=dt, variance=0.0)
        dmg = base * multi
        if cls_id(cls) == "cls_ci_ke" and name == "双刃乱舞":
            dmg *= ASSASSIN_COND_WEIGHT
        if cls_id(cls) == "cls_wu_seng" and name == "碎骨拳":
            dmg *= 1 / 3.0   # 3 气 → 每 3 行动 1 发
        dmg *= _crit_mult(st, extra_crit=extra_crit, multi=multi)
        tot += dmg * w
        wsum += w
    return tot / max(wsum, 1.0)


def _basic_dmg(st: dict, cls: str, edef: int, mdef: int) -> float:
    """普攻伤害（v156 修正：普攻一律吃 atk——引擎 battle.py 普攻段 calc_damage(st['atk'], ...)，
    法系职业 atk 低故普攻天然弱（魔杖/法杖敲击），符合法系定位；此前误用 matk 导致工具集虚高）"""
    return E.calc_damage(int(st.get("atk", 0)), int(edef), variance=0.0, dmg_type="phys")


def _crit_mult(st: dict, extra_crit: float = 0.0, multi: int = 1) -> float:
    """暴击期望 + 幸运一击（v133 对齐引擎：幸运幅度 1.5→1.3；多段仅首段吃暴击——
    multi≥2 时暴击/幸运加成按 1/multi 折算，与 battle.py seg=0 判定一致）。"""
    crit = min(float(st.get("crit", 0) or 0) + extra_crit, 0.5)
    first = 1.0 / max(1, int(multi or 1))
    return 1.0 + crit * (0.5 + float(st.get("crit_dmg", 0) or 0)) * first + crit * 0.3 * 0.3 * first


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
    _ec = ENCHANT_CRIT if opts.enchant else 0.0
    if opts.skills:
        d = _skill_dmg(st, cls, edef, mdef, extra_crit=_ec)
    else:
        d = _basic_dmg(st, cls, edef, mdef)
    if crit and not opts.skills:
        # v161 修复：普攻只乘一次暴击期望（此前误乘两次导致普攻虚高 ~8%，
        # 让"技能 vs 普攻"门禁失真——技能明明更强却判弱）
        d *= _crit_mult(st, extra_crit=_ec, multi=1)
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


# ---------------- 技能经济（v156 阶段 3）：空蓝轮数 ----------------
MP_REGEN_PCT = 0.05   # 基础回蓝速率：每轮回复 max_mp×5%（27 章基础规则简化口径；不查回蓝技能，保守）


def rotation_mp_per_round(cls: str, rotation: list | None = None, lv: int | None = None) -> float:
    """技能轴平均每轮 MP 消耗（E.skill_info 实读 mp 字段）。

    - rotation: [(技能名, 权重)] 或 v161 [(max_lv, 技能名, 权重)]；None = 职业默认 ROTATIONS
    - lv: 玩家等级；None = 用 ROTATIONS 全部（旧口径）。lv 给定则按档位选当前等级可达技能（与 _skill_dmg 一致）
    - 资源技（res_cost：怒气/连击点/精力等）不耗 MP → 计 0（与 _tmp_calib_v2 同口径）
    """
    cid = cls_id(cls)
    rot = rotation if rotation is not None else ROTATIONS.get(cid, [])
    # v161 按等级选档（与 _skill_dmg 同口径）：max_lv 是技能适用等级上限，选第一个 >= lv 的档；
    # lv 超过全档用最后一档；未传 lv 用全部（旧口径）
    if rotation is None and lv is not None and rot and len(rot[0]) == 3:
        cand = [t for t in rot if t[0] >= lv]
        if cand:
            top_lv = min(t[0] for t in cand)
            rot = [t for t in cand if t[0] == top_lv]
        else:
            rot = [rot[-1]]
    tot, wsum = 0.0, 0.0
    for item in rot:
        # v161 新格式 (max_lv, 技能名, 权重)；兼容旧格式 (技能名, 权重)
        if len(item) == 3:
            _, name, w = item
        else:
            name, w = item
        info = E.skill_info(cid, name)
        if not info:
            continue
        mp = float(info.get("mp", 0) or 0)
        if info.get("res_cost"):   # 资源技（怒气/连击点/精力）不耗 MP
            mp = 0.0
        tot += mp * w
        wsum += w
    return tot / max(wsum, 1.0)


def mp_budget(cls: str, lv: int, gear: dict | None = None,
              opts: PlayerOptions | None = None,
              rotation: list | None = None) -> dict:
    """按技能轴算空蓝轮数（v156 技能经济：长盘副本法系续航闸门）。

    返回 {"max_mp": x, "per_round_mp": y, "mp_regen": z, "empty_rounds": 空蓝轮数}
    - max_mp: build_player 面板 mp
    - per_round_mp: ROTATIONS 循环每轮技能 mp 消耗（E.skill_info 实读 mp 字段）
    - mp_regen: 基础回蓝速率（简化：每轮回复 max_mp×5%，27 章基础规则口径）
    - empty_rounds: max_mp / (per_round_mp - mp_regen)；per_round_mp <= mp_regen → inf
    """
    st = build_player(cls, lv, gear, opts)
    max_mp = float(st.get("max_mp", 0) or 0)
    per_round_mp = rotation_mp_per_round(cls, rotation, lv=lv)
    mp_regen = max_mp * MP_REGEN_PCT
    net = per_round_mp - mp_regen
    empty_rounds = float("inf") if net <= 0 else max_mp / net
    return {
        "max_mp": max_mp,
        "per_round_mp": per_round_mp,
        "mp_regen": mp_regen,
        "empty_rounds": empty_rounds,
    }


# ---------------- v161 可持续 DPS：出手频率 × 资源折算 × 机制期望 ----------------

def _interval(cast: float, spd: float) -> float:
    """一次行动实际耗时（秒）＝基准耗时 × (SPD_REF / spd)^0.5，引擎 v161 同款折算。

    v161 新曲线（鱼鱼拍板：取消 cap 线性，改边际递减永续公式）：
      折算系数 = sqrt(SPD_REF / spd)，速度 50 → 1.0；25 → 1.41；100 → 0.71；200 → 0.50。
      永不封顶、永不归零、每点速度边际递减 → 堆速度永远有意义、不爆炸。
    """
    import math as _m
    eff = max(float(spd or 0), 1.0)
    return float(cast or 0) * _m.sqrt(SPD_REF / eff)


def basic_interval(st: dict, cls: str) -> float:
    """普攻行动间隔：职业 cast_atk（classes.py 顶层字段）× 速度折算。"""
    cast_atk = None
    for _n, _id, *_ in CLASSES:
        if _id == cls_id(cls):
            _cls_info = _class_info(_id)
            cast_atk = _cls_info.get("cast_atk") if _cls_info else None
            break
    cast = float(cast_atk or 0) if cast_atk else 1.0
    return _interval(cast, st.get("spd", 50))


def skill_interval(st: dict, cls: str, skill_name: str) -> float:
    """技能行动间隔：技能 cast × 速度折算（engine 同款）。"""
    info = E.skill_info(cls_id(cls), skill_name)
    cast = float(info.get("cast", 0) or 0) if info else 1.0
    return _interval(cast, st.get("spd", 50))


def _class_info(cid: str) -> dict:
    """职业配置（classes.py CLASSES 顶层字段：cast_atk 等）。"""
    from data.plugins.dragonfall.game import content as _C
    return (_C.CLASSES or {}).get(cid, {})


def skill_mech_mult(cls: str, skill_name: str) -> float:
    """技能机制稳态倍率（MECH_MULT 表；无机制 = 1.0）。"""
    return float(MECH_MULT.get(skill_name, 1.0))


def sustained_dps(cls: str, lv: int, gear: dict | None, edef: int, mdef: int,
                  opts: PlayerOptions | None = None, potion_on: bool = False,
                  fight_len: float = 60.0, target_max_hp: float = 0.0,
                  target_role: str = "dps") -> float:
    """可持续 DPS（v161 核心口径）：出手频率 × 单发 × 资源折算 × 机制期望。

    口径 = 输出节奏DPS × 资源可持续性系数
      - 出手频率：技能 cast（普攻 cast_atk）× (SPD_REF/spd)，快攻职业受益
      - 资源折算：空蓝轮数 N = max_mp / (每轮耗蓝 - 每轮回蓝)；N ≥ 战斗长度 → 纯技能；
                  N < 战斗长度 → 空蓝期转普攻（引擎 _skill_cast_blocked 蓝不足拦截）
      - 机制期望：MECH_MULT 稳态倍率（印记/连击/条件增伤长盘期望）

    fight_len：长盘副本基准（轮），默认 60（v136 长盘副本 60-100 轮区间下界）。
    """
    opts = opts or PlayerOptions()
    # 单发伤害（技能轴 / 普攻）
    d_skill = per_action_dmg(cls, lv, gear, edef, mdef, opts, potion_on=potion_on)
    # 出手频率：技能轴当前档位 cast
    st = build_player(cls, lv, gear, opts, potion=0.0)
    lvl = int(st.get("level", 1) or 1)
    cid = cls_id(cls)
    rot = ROTATIONS.get(cid, [])
    cand = [t for t in rot if t[0] >= lvl]
    if not cand:
        cand = [rot[-1]] if rot else []
    else:
        top_lv = min(t[0] for t in cand)
        cand = [t for t in cand if t[0] == top_lv]
    # 技能轴 cast 加权（多技能取加权；当前单技能）
    cast_sum, wsum = 0.0, 0.0
    for max_lv, name, w in cand:
        cast_sum += skill_interval(st, cls, name) * w
        wsum += w
    cast_avg = cast_sum / max(wsum, 1.0) if wsum else basic_interval(st, cls)
    freq = 1.0 / max(cast_avg, 0.001)
    # 机制期望倍率（技能轴当前技能）
    mech_mult = 1.0
    if cand:
        _, name, _ = cand[0]
        mech_mult = skill_mech_mult(cls, name)
    # 纸面 DPS（无资源压力）
    st["_target_max_hp"] = target_max_hp
    st["_target_role"] = target_role
    # v161 CD 折算：技能有 CD 时不能每行动都用——一个循环 = 技能(cast秒) + CD期普攻(cd秒)。
    # 引擎 _skill_on_cd 拦截：CD 未结束只能普攻。基础技能 cd=0（P1/P2 模型原口径）；
    # P3+ T1-T3 技能 cd=8-24，必须折算（否则模型高估 3-5 倍）。
    d_basic = _basic_dmg(st, cls, edef, mdef)
    freq_basic = 1.0 / max(basic_interval(st, cls), 0.001)
    dps_basic = d_basic * freq_basic
    cd = 0.0
    if cand:
        info = E.skill_info(cls, cand[0][1])
        if info:
            cd = float(info.get("cd", 0) or 0)
    if cd > 0:
        # 循环 = cd 秒一循环：1 发主技能 + CD 剩余时间用填充技能（无 CD 基础技）或普攻。
        # 引擎真实循环：主技能 CD 期间用基础技能填充（挥砍/连射/火球/刺击/直拳 cd=0），
        # 牧师/诗人无 cd=0 基础技 → 普攻填充。
        skill_hit = d_skill * mech_mult  # 单发主技能（含机制）
        dot_hit = dot_dps(st, cls, edef, mdef, cand) / max(freq, 0.001)  # DOT 摊到单循环
        cycle_time = cd
        fill_dps = dps_basic  # 默认普攻填充
        # 找该职业 cd=0 填充技能（ROTATIONS 内第一个无 CD 攻击技），用其单发×频率作填充 DPS
        for maxlv, fname, w in ROTATIONS.get(cid, []):
            finfo = E.skill_info(cid, fname)
            fkind = str(finfo.get("kind", "")) if finfo else ""
            # kind 可能是 '魔法' 或 '魔法·火'（元素后缀）——前缀匹配
            if not (finfo and not finfo.get("cd") and (fkind.startswith("物理") or fkind.startswith("魔法"))):
                continue
            f_interval = skill_interval(st, cls, fname)
            # 内联算填充技能单发（与 _skill_dmg 同口径，但指定技能名）
            f_phys = _is_phys(cls)
            f_stat = st["atk"] if f_phys else st["matk"]
            f_dt = "phys" if f_phys else "magi"
            f_expr = dict(st)
            f_expr["_player_lv"] = int(st.get("level", 1) or 1)
            f_expr["_skill_lv"] = 1
            f_val = E.skill_expr_preview(finfo, 1, f_expr)
            if f_val > 0:
                f_raw = f_val
            else:
                f_raw = int(f_stat * float(finfo.get("power", 0) or 0)) + E.skill_flat_value(1, 1, finfo)
            if finfo.get("pierce"):
                f_base = E.calc_damage(int(f_raw), 0, pierce=True, dmg_type=f_dt, variance=0.0)
            else:
                f_def = mdef if not f_phys else edef
                f_base = E.calc_damage(int(f_raw), int(f_def), dmg_type=f_dt, variance=0.0)
            f_multi = int(finfo.get("hits", finfo.get("multi", 1)))
            f_dmg = f_base * f_multi
            fill_dps = f_dmg / max(f_interval, 0.001)
            break
        skill_dmg_cycle = skill_hit + dot_hit + fill_dps * (cd - cast_avg)
        dps_paper = skill_dmg_cycle / max(cycle_time, 0.001)
    else:
        dps_paper = d_skill * freq * mech_mult + dot_dps(st, cls, edef, mdef, cand)
    # 资源折算：空蓝轮数 → 满蓝期技能 / 空蓝期普攻
    if opts.skills:
        b = mp_budget(cls, lv, gear, opts)
        empty_rounds = b["empty_rounds"]
        if empty_rounds == float("inf"):
            return dps_paper
        # 空蓝期普攻 DPS（同面板，普攻 cast_atk 频率）
        N = float(empty_rounds)
        if N >= fight_len:
            return dps_paper
        return (dps_paper * N + dps_basic * (fight_len - N)) / fight_len
    return dps_paper


def dot_dps(st: dict, cls: str, edef: int, mdef: int,
            rotation: list | None = None) -> float:
    """DOT 机制稳态 DPS（v161 鱼鱼拍板：职业机制折算成系数计入 DPS）。

    引擎公式（battle.py _tick_dots）：每层每刻 = (atk×a + matk×m + max_hp×h) × 层数 × (1-抗)
    对普通怪（stage_scan 口径）：百分比部分不打折；真伤穿防。
    对 Boss/精英：百分比部分 ×DOT_BOSS_PCT_MULT（0.5），单层 cap max_hp×1%。

    稳态假设（长盘普通怪）：DOT 全程覆盖（每次释放刷新），层数 = mech_val。
    返回当前技能轴技能的 DOT 稳态 DPS 附加（无 DOT = 0）。
    """
    from data.plugins.dragonfall.game.data.battle_config import DOT_DEFS, DOT_BOSS_PCT_MULT, DOT_PCT_CAP
    cid = cls_id(cls)
    if not rotation:
        return 0.0
    # 当前档技能（与 sustained_dps 同选档逻辑）
    lvl = int(st.get("level", 1) or 1)
    rot = rotation or []
    cand = [t for t in rot if t[0] >= lvl]
    if not cand:
        cand = [rot[-1]] if rot else []
    else:
        top_lv = min(t[0] for t in cand)
        cand = [t for t in cand if t[0] == top_lv]
    if not cand:
        return 0.0
    _, name, _ = cand[0]
    info = E.skill_info(cid, name)
    if not info:
        return 0.0
    mech = info.get("mech", "")
    stacks = int(info.get("mech_val", 0) or 0)
    if not mech or mech not in DOT_DEFS or stacks <= 0:
        return 0.0
    dd = DOT_DEFS[mech]
    atk = float(st.get("atk", 0) or 0)
    matk = float(st.get("matk", 0) or 0)
    # 目标类型：Boss/精英百分比打折。stage_scan 用普通怪（edef/mdef 为 dps 怪）
    # 简化：函数不感知目标 role，调用方传 target_role；默认普通怪
    target_role = st.get("_target_role", "dps")
    is_boss = target_role in ("boss", "elite")
    hp_part = 0.0
    if dd.get("hp"):
        hp_part = float(st.get("_target_max_hp", 0) or 0) * dd["hp"]
        if dd.get("type") in ("pct", "hybrid"):
            if is_boss:
                hp_part *= DOT_BOSS_PCT_MULT
            cap = float(st.get("_target_max_hp", 0) or 0) * DOT_PCT_CAP
            hp_part = min(hp_part, cap)
    per_tick = atk * dd.get("atk", 0) + matk * dd.get("matk", 0) + hp_part
    # 真伤穿防（直接加）；非真伤也按引擎 _tick_dots 免防御处理（DOT 不吃防御，只吃 dot_res）
    interval = skill_interval(st, cls, name)
    freq = 1.0 / max(interval, 0.001)
    return per_tick * stacks * freq