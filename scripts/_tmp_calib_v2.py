# -*- coding: utf-8 -*-
"""真实玩家输出模型 v2 —— 补全 numeric_calibration.py 漏掉的全部乘区（只分析，不改源码）

基准脚本口径：rounds = boss_hp / (mn × 单人每轮伤害)，每轮 = 每人一次行动。
原模型：单人每轮 = (战士普攻+游侠普攻)/2 × 1.5（技能轮换估计），无属性点/无tier/无技能轴/无词条/无附魔/无药水。

v2 补全乘区（基准 = 战士+蓝装0强化，Lv 参照 60）：
  a. 满自由属性点   9+3×(lv-1) 点，物理系全 str(+1.2atk/点)，法系全 int(+1.2matk/点)
  b. tier 转职倍率  TIER_GROWTH {0:1.0,1:1.15,2:1.30,3:1.50}（30/60/90 门槛）+ 攻线分支 atk×1.06
  c. 真实技能轴     calc_damage 按技能 power/multi/pierce/穿透 直接算（替代 ×1.5）
  d. 2条攻击词条    蓝装 2 词条 ≈ ×1.20（贯穿20%无视防御+暴击强化，10章七口径）
  e. 附魔 crit4%    ENCHANT_MAX_VALUE.crit=0.04 → 暴击期望乘区
  f. 药水攻击buff   物理:攻击药水 攻+30%；法系:鲛人之泪 魔攻+30%（alchemy.py 实读）
宠物：副本战斗不携带宠物（instance.py:435）→ 不计入。
速度：轮数口径按"每人一次行动"与原表同单位；CTB 行动频率(spd/100)单独备注，不混入轮数。
"""
import sys, os

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
os.environ["GWEN_GAME_DB"] = os.path.join(PLUGIN_DIR, "test_game_data.db")

from data.plugins.dragonfall.game import content as C  # noqa: E402
from saintess_engine.formulas import calc_damage, skill_power_mult
from game.content_rules.panel import player_final_stats
from game.content_rules.skills import skill_info
from game.data.battle_config import TIER_GROWTH
from data.plugins.dragonfall.game.core import stats as ST  # noqa: E402

# ---------------- 玩家真实模型 ----------------
CLASSES = [  # (中文名, id, 物/法, 属性点主属性)
    ("战士", "cls_zhan_shi", "phys", "str"),
    ("游侠", "cls_you_xia", "phys", "str"),
    ("法师", "cls_fa_shi", "magi", "int"),
    ("牧师", "cls_mu_shi", "magi", "int"),
    ("刺客", "cls_ci_ke", "phys", "str"),
]

POTION_ATK = 0.30          # 攻击药水 攻+30%（3回合）alchemy.py:176
POTION_MATK = 0.30         # 鲛人之泪 魔攻+30%（3回合）alchemy.py:254
AFFIX_MULT = 1.20          # 蓝装 2 条攻击词条 ≈ ×1.20（任务给定口径 atk_pct+暴击合算）
ENCHANT_CRIT = 0.04        # 附魔暴击上限 4%（enchant.py ENCHANT_MAX_VALUE.crit）

# 技能轴（技能倍率全部从 data 技能表实读，Lv.1 技能等级，保守）
ROTATIONS = {
    "cls_zhan_shi": [("破甲斩", 1.0), ("猛击", 1.0)],          # 破甲斩130%破防(无视防御) + 猛击120%
    "cls_you_xia": [("瞄准射击", 1.0)],                        # 140% 单体（精力10/发，每回合回30可永续）
    "cls_fa_shi": [("元素弹幕", 1.0)],                         # 100%×2 = 200% 魔法
    "cls_mu_shi": [("惩戒", 1.0)],                             # 120% 圣光魔法
    "cls_ci_ke": [("双刃乱舞", 1.0)],                          # 90%×2，目标HP>70%时+30%（按战斗全程加权）
}
# 双刃乱舞 HP>70% 条件：boss 前 30% 血量期间生效 → 加权 (1 + 0.3×0.3) = 1.09
ASSASSIN_COND_WEIGHT = 1.09
# 破甲斩的防御减半 debuff（DEF_DOWN_MULT=0.5，持续 3 回合）在循环内 100% 覆盖 → 猛击常驻打半防
DEF_DOWN_SKILLS = {"cls_zhan_shi": {"猛击": 0.5}}


def tier_of(lv):
    return 3 if lv >= 90 else 2 if lv >= 60 else 1 if lv >= 30 else 0


def attr_pts_of(lv):
    return 9 + 3 * (lv - 1)  # DEFAULT_ATTR_PTS=9 + 每级3点


def make_gear(level, quality, enhance):
    gear = {}
    for slot in C.EQUIP_SLOT_BASE:
        s = ST.equip_stats(slot, level, quality)
        if enhance > 0:
            mult = C.ENHANCE_TABLE.get(enhance, {}).get("mult", 1.0)
            s = {k: int(v * mult) for k, v in s.items()}
        gear[slot] = {"stats": s, "enhance": enhance}
    return gear


def player_stats(cls_id, lv, gear, with_attr=True, potion=0.0):
    """真实玩家面板：自由属性点 + tier 转职成长 + 攻线分支；potion 按战斗内 buff 方式乘入攻击端。"""
    tier = tier_of(lv)
    attrs = None
    if with_attr:
        pts = attr_pts_of(lv)
        main = dict(CLASSES)[cls_id][3] if False else [c[3] for c in CLASSES if c[1] == cls_id][0]
        attrs = {main: pts}
    st = player_final_stats(cls_id, lv, gear, tier, attrs, evolve_path=1 if tier else 0, title_bonus=None, race=None)
    if potion:
        base = st["atk"] if st["atk"] >= st["matk"] else st["matk"]
        if st["atk"] >= st["matk"]:
            st["atk"] = int(st["atk"] * (1 + potion))
        else:
            st["matk"] = int(st["matk"] * (1 + potion))
    return st


def skill_names(cls_id):
    return ROTATIONS[cls_id]


def cast_dmg(st, info, edef, mdef, phys, def_mult=1.0):
    stat = st["atk"] if phys else st["matk"]
    d = (edef if phys else mdef) * def_mult
    power = float(info.get("power", 0)) * skill_power_mult(1, info)
    multi = int(info.get("multi", 1))
    pene = st.get("pene_phys" if phys else "pene_magi", 0)
    pflat = st.get("pene_flat" if phys else "pene_mflat", 0)
    dt = "phys" if phys else "magi"
    if info.get("pierce"):
        base = calc_damage(int(stat * power), 0, pierce=True, dmg_type=dt, variance=0.0)
    else:
        base = calc_damage(int(stat * power), d, pene_pct=pene, pene_flat=pflat, dmg_type=dt, variance=0.0)
    return base * multi


def rotation_dmg(st, edef, mdef, cls_id):
    phys = [c for c in CLASSES if c[1] == cls_id][0][2] == "phys"
    tot, wsum = 0.0, 0.0
    for name, w in ROTATIONS[cls_id]:
        info = skill_info(cls_id, name)
        if not info:
            continue
        def_mult = DEF_DOWN_SKILLS.get(cls_id, {}).get(name, 1.0)
        d = cast_dmg(st, info, edef, mdef, phys, def_mult=def_mult)
        if cls_id == "cls_ci_ke" and name == "双刃乱舞":
            d *= ASSASSIN_COND_WEIGHT
        tot += d * w
        wsum += w
    return tot / max(wsum, 1)


def crit_mult(st, extra_crit=0.0):
    """暴击期望 + 幸运一击（暴击后30%概率追加50%伤害，battle.py:3142/3405）"""
    crit = min(st.get("crit", 0) + extra_crit, 0.5)
    return 1.0 + crit * (0.5 + st.get("crit_dmg", 0)) + crit * 0.3 * 0.5


def basic_hit(st, edef, mdef, phys):
    stat = st["atk"] if phys else st["matk"]
    d = edef if phys else mdef
    return calc_damage(int(stat), d, variance=0.0, dmg_type="phys" if phys else "magi")


def per_round_dmg(cls_id, lv, gear, edef, mdef, full_build=True):
    """单人每轮（一次行动）期望伤害（全配：附魔+药水+词条；不计法力闸门，用于乘区展示）"""
    phys = [c for c in CLASSES if c[1] == cls_id][0][2] == "phys"
    potion = POTION_ATK if phys else POTION_MATK
    st = player_stats(cls_id, lv, gear, with_attr=True, potion=potion if full_build else 0.0)
    d = rotation_dmg(st, edef, mdef, cls_id)
    d *= crit_mult(st, extra_crit=ENCHANT_CRIT if full_build else 0.0)
    if full_build:
        d *= AFFIX_MULT
    return d


def rotation_mp_per_action(cls_id):
    """技能轴平均每行动 MP 消耗（游侠耗精力不计入；战士怒气系无 MP 资源技不计）"""
    tot, wsum = 0.0, 0.0
    for name, w in ROTATIONS[cls_id]:
        info = skill_info(cls_id, name)
        if not info:
            continue
        mp = float(info.get("mp", 0) or 0)
        if info.get("res_cost"):  # 资源技（怒气/连击点/精力）不耗 MP
            mp = 0.0
        tot += mp * w
        wsum += w
    return tot / max(wsum, 1)


def per_round_dmg_gated(cls_id, lv, gear, edef, mdef, rounds_ref):
    """带法力续航闸门：预估战斗轮数 × 每轮MP > 蓝量时，超出的行动降级为普攻。
    战斗内无自然回蓝（仅魔力药水/料理），长局法系会打空蓝。"""
    phys = [c for c in CLASSES if c[1] == cls_id][0][2] == "phys"
    potion = POTION_ATK if phys else POTION_MATK
    st = player_stats(cls_id, lv, gear, with_attr=True, potion=potion)
    rot = rotation_dmg(st, edef, mdef, cls_id)
    basic = basic_hit(st, edef, mdef, phys)
    mp_pa = rotation_mp_per_action(cls_id)
    if mp_pa > 0 and rounds_ref > 0:
        castable = st.get("max_mp", 0) / mp_pa
        n_cast = min(castable, rounds_ref)
        if n_cast < rounds_ref:
            dmg = (n_cast * rot + (rounds_ref - n_cast) * basic) / rounds_ref
        else:
            dmg = rot
    else:
        dmg = rot
    return dmg * crit_mult(st, extra_crit=ENCHANT_CRIT) * AFFIX_MULT


def calib_model_dmg(lv, gear, edef):
    """原校准模型：战士+游侠 普攻均值 ×1.5（与 numeric_calibration.py 一致）"""
    st_w = player_final_stats("cls_zhan_shi", lv, gear, 0, None, 0, None, None)
    st_r = player_final_stats("cls_you_xia", lv, gear, 0, None, 0, None, None)
    avg = (calc_damage(st_w.get("atk", 0), edef, variance=0.0) +
           calc_damage(st_r.get("atk", 0), edef, variance=0.0)) / 2
    return avg * 1.5


def main():
    # ---------------- 参照副本（Lv 最接近 60，用于各乘区表） ----------------
    insts = sorted(C.INSTANCES.items(), key=lambda x: x[1].get("lv", 0))
    ref = min(insts, key=lambda x: abs(x[1].get("lv", 0) - 60))
    ref_id, ref_inst = ref
    ref_lv = ref_inst.get("lv", 60)
    ref_boss = ref_inst.get("boss") or (ref_inst.get("stages") or [])[-1].get("boss")
    ref_m = C.build_monster(ref_boss, {"id": ref_id, "name": ref_id, "area": "instance"})
    ref_def, ref_mdef = ref_m.get("def", 0), ref_m.get("mdef", 0)

    gear0 = make_gear(ref_lv, "blue", 0)
    st_w0 = player_final_stats("cls_zhan_shi", ref_lv, gear0, 0, None, 0, None, None)
    base_per_round = calc_damage(st_w0.get("atk", 0), ref_def, variance=0.0) * 1.5

    print("=" * 78)
    print(f"① 各维度单独提升倍数表（基准 = 战士+蓝装0强化 ×1.5普攻，参照副本 {ref_id} Lv.{ref_lv}）")
    print(f"   Boss 防御 {ref_def} / 魔防 {ref_mdef}")
    print("=" * 78)
    hdr = f"{'乘区':<14}{'说明':<36}{'单独倍数':>8}"
    print(hdr)
    print("-" * 78)

    # a. 满自由属性点
    st_a = player_stats("cls_zhan_shi", ref_lv, gear0, with_attr=True)
    d_a = calc_damage(st_a.get("atk", 0), ref_def, variance=0.0) * 1.5
    m_a = d_a / base_per_round
    print(f"{'a.满自由属性点':<14}{f'9+3×{ref_lv-1}={attr_pts_of(ref_lv)}点全str，攻击+{int(attr_pts_of(ref_lv)*1.2)}'[:36]:<36}{m_a:>8.2f}×")

    # b. tier 转职倍率
    st_b = player_stats("cls_zhan_shi", ref_lv, gear0, with_attr=False)
    d_b = calc_damage(st_b.get("atk", 0), ref_def, variance=0.0) * 1.5
    m_b = d_b / base_per_round
    print(f"{'b.tier转职倍率':<14}{f'tier{tier_of(ref_lv)}成长×{TIER_GROWTH.get(tier_of(ref_lv),1.0):g} + 攻线×1.06'[:36]:<36}{m_b:>8.2f}×")

    # c. 真实技能轴（替代 ×1.5）
    st_c = player_stats("cls_zhan_shi", ref_lv, gear0)
    d_c = rotation_dmg(st_c, ref_def, ref_mdef, "cls_zhan_shi")
    rot_over_basic = d_c / calc_damage(st_c.get("atk", 0), ref_def, variance=0.0)
    m_c = rot_over_basic / 1.5  # 相对校准模型的 ×1.5
    print(f"{'c.真实技能轴':<14}{'破甲斩(130%破防+减半防)+猛击(120%)循环'[:36]:<36}{m_c:>8.2f}× (技能倍率 {rot_over_basic:.2f}×普攻 vs 原×1.5)")

    # d. 2条攻击词条
    print(f"{'d.2条攻击词条':<14}{'蓝装2词条:贯穿+暴击强化(10章七口径)'[:36]:<36}{AFFIX_MULT:>8.2f}×")

    # e. 附魔 crit4%
    cm0 = crit_mult(st_c)
    cm1 = crit_mult(st_c, extra_crit=ENCHANT_CRIT)
    m_e = cm1 / cm0
    print(f"{'e.附魔crit4%':<14}{f'暴击期望 {cm0:.3f}→{cm1:.3f}（crit上限0.5）'[:36]:<36}{m_e:>8.2f}×")

    # f. 药水攻击buff
    st_f = player_stats("cls_zhan_shi", ref_lv, gear0, potion=POTION_ATK)
    d_f = calc_damage(st_f.get("atk", 0), ref_def, variance=0.0)
    m_f = d_f / calc_damage(st_c.get("atk", 0), ref_def, variance=0.0)
    print(f"{'f.药水攻击buff':<14}{f'攻击药水 攻+30%(3回合) 实算'[:36]:<36}{m_f:>8.2f}×")

    m_total = m_a * m_b * m_c * AFFIX_MULT * m_e * m_f
    print("-" * 78)
    print(f"{'累乘总提升':<14}{'a×b×c×d×e×f（相对战士+蓝装0强化基准）':<36}{m_total:>8.2f}×")
    print(f"→ 真实玩家每轮输出 ≈ 校准模型（战士+游侠均值 ×1.5）的 {m_total:.2f} 倍")
    print(f"   （即校准模型对同档位玩家的输出低估 {m_total:.1f} 倍；其中 c 项已扣除原有的 ×1.5）")
    print(f"   注：CTB 行动频率 = min(spd,80)/100 次/时隙，原模型隐式视为 1.0/轮 —— 高灵巧职业实战时长进一步缩短，此处未计入轮数。")
    print()

    # 各职业每轮输出明细（参照副本）
    print("各职业每轮期望伤害（低配/全配 vs 校准模型，参照副本）：")
    for name, cid, kind, _ in CLASSES:
        d_low = per_round_dmg(cid, ref_lv, gear0, ref_def, ref_mdef, full_build=False)
        d_full = per_round_dmg(cid, ref_lv, gear0, ref_def, ref_mdef, full_build=True)
        cb = calib_model_dmg(ref_lv, gear0, ref_def)
        print(f"  {name:<4} 低配 {d_low:>8.0f}   全配 {d_full:>8.0f}   校准模型 {cb:>8.0f}   全配/校准 = {d_full/cb:.2f}×")
    print()

    # ---------------- ③ 全部副本 Boss 轮数 ----------------
    print("=" * 78)
    print("③ 全副本 Boss 战轮数（真实玩家模型；每轮=每人一次行动；组队=4人×1.1团队buff；BossHP=hp_mult+0.65×(n−min_players))")
    print("=" * 78)
    hdr2 = f"{'副本':<22}{'Lv':>3}{'原表蓝装':>8} | {'单刷低配+0':>10} {'单刷+5':>8} {'4人+5':>8} {'4人+9':>8} | {'判定'}"
    print(hdr2)
    print("-" * 108)

    rows = []
    comfort_cnt = {"solo0": 0, "solo5": 0, "team5": 0, "team9": 0}
    bad_cnt = {"solo0": 0, "solo5": 0, "team5": 0, "team9": 0}
    fast_cnt = {"solo0": 0, "solo5": 0, "team5": 0, "team9": 0}
    comfort_list = {k: [] for k in comfort_cnt}
    bad_list = {k: [] for k in bad_cnt}
    fast_list = {k: [] for k in fast_cnt}
    total_mult_all = []
    gap_list = []

    for iid, inst in insts:
        lv = inst.get("lv", 0)
        boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
        if not boss_def:
            continue
        m = C.build_monster(boss_def, {"id": iid, "name": iid, "area": "instance"})
        hpm = inst.get("hp_mult", 1.0)
        mn = inst.get("min_players", 1)
        boss_hp = int(m.get("max_hp", 0) * hpm)
        bdef, bmdef = m.get("def", 0), m.get("mdef", 0)

        # 原校准模型（蓝装+0，mn×1.5）
        gear0 = make_gear(lv, "blue", 0)
        cb = calib_model_dmg(lv, gear0, bdef)
        orig_rounds = boss_hp / max(cb * mn, 1)

        # 四档
        gear5 = make_gear(lv, "blue", 5)
        gear9 = make_gear(lv, "blue", 9)

        def team_hpm(n):
            return max(hpm + 0.65 * (n - mn), 0.2)

        def rounds_of2(n, gear, full_build, team_mult):
            hpm_n = hpm + 0.65 * (n - mn)
            if hpm_n <= 0:
                hpm_n = hpm * 0.3
            hp = int(m.get("max_hp", 0) * hpm_n)
            # 法力闸门迭代（战斗轮数 → 蓝耗 → 有效每轮伤害 → 轮数，2 轮收敛）
            r = hp / max(n * team_mult, 1)
            for _ in range(3):
                per = sum(per_round_dmg_gated(cid, lv, gear, bdef, bmdef, r) for _, cid, _, _ in CLASSES) / len(CLASSES)
                r = hp / max(n * per * team_mult, 1)
            return r

        r_solo0 = rounds_of2(1, gear0, full_build=True, team_mult=1.0)
        r_solo5 = rounds_of2(1, gear5, full_build=True, team_mult=1.0)
        r_team5 = rounds_of2(4, gear5, full_build=True, team_mult=1.1)
        r_team9 = rounds_of2(4, gear9, full_build=True, team_mult=1.1)
        total_mult_all.append(orig_rounds / r_solo0)
        # 纯输出差距（同HP直比，排除人数/HP缩放差异）：真实5职均值 / 校准模型每轮
        per_real = sum(per_round_dmg(cid, lv, gear0, bdef, bmdef, True) for _, cid, _, _ in CLASSES) / len(CLASSES)
        gap_list.append(per_real / cb)

        flag = "🔴" if r_solo0 > 60 else ("✅" if 15 <= r_solo0 <= 30 else ("🟡" if r_solo0 <= 15 else "⚠️"))
        rows.append((iid, lv, orig_rounds, r_solo0, r_solo5, r_team5, r_team9, flag))
        for k, v in (("solo0", r_solo0), ("solo5", r_solo5), ("team5", r_team5), ("team9", r_team9)):
            if 15 <= v <= 30:
                comfort_cnt[k] += 1
                comfort_list[k].append(iid)
            if v > 60:
                bad_cnt[k] += 1
                bad_list[k].append(iid)
            if v < 15:
                fast_cnt[k] += 1
                fast_list[k].append(iid)
        print(f"{iid:<22}{lv:>3}{orig_rounds:>8.0f} | {r_solo0:>10.0f} {r_solo5:>8.0f} {r_team5:>8.0f} {r_team9:>8.0f} | {flag}")

    print("-" * 108)
    gap = sum(total_mult_all) / len(total_mult_all)
    gmin, gmax = min(gap_list), max(gap_list)
    gmed = sorted(gap_list)[len(gap_list) // 2]
    print(f"副本数（含Boss）: {len(rows)}")
    print(f"纯输出差距（真实5职全配均值输出 / 校准模型输出，同HP直比）：最小 {gmin:.1f}× / 中位 {gmed:.1f}× / 最大 {gmax:.1f}×")
    print(f"按轮数直比（原表蓝装轮数 / 单刷蓝装+0全配轮数，含单人HP缩放差异）：均值 {gap:.1f}×")
    print()
    print("=== 舒适区(15~30轮) / 过速(<15轮) / 恶性超标(>60轮) 统计 ===")
    for k, label in (("solo0", "单刷蓝装+0(低配)"), ("solo5", "单刷蓝+5"), ("team5", "4人蓝+5"), ("team9", "4人蓝+9")):
        print(f"  {label:<14} 舒适区 {comfort_cnt[k]:>2} 个: {','.join(comfort_list[k]) or '无'}")
        print(f"  {label:<14} 过速   {fast_cnt[k]:>2} 个: {','.join(fast_list[k]) or '无'}   （<15轮，Boss被秒）")
        print(f"  {label:<14} 超标   {bad_cnt[k]:>2} 个: {','.join(bad_list[k]) or '无'}   （>60轮）")
    print()
    print("口径与假设：技能 Lv.1（未计技能升级+10%/级）；未计元素反应/暴击药水/战吼/称号/种族；")
    print("战士循环未计裂地斩(怒气3终结180%破防，实机可再高~15%)；Boss 全程不回血、无小怪干扰；")
    print("法系长局已按蓝量闸门降级普攻（战斗内无自然回蓝，仅魔力药水/料理）；宠物不参战（instance.py:435）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())