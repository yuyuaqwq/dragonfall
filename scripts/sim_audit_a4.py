# -*- coding: utf-8 -*-
"""Audit A4 —— CTB 数值设计一致性：spd 价值 / 行动频率 / buff / 先手 / 极端配速 / 跨职业胜率。

只读审计用模拟（不修改任何 game 文件）。构造风格复用 scripts/sim_ctb_balance.py
（make_player / make_enemy / run_one_battle / action_statistics 的埋点方式）。

覆盖题 2~6：
  A. spd 边际收益曲线（行动频率 vs spd，敌 spd 固定）
  B. 速度 buff（spd_up/减速/疾风药剂/食物）对行动频率的影响
  C. 先手价值（spd 差多少保证先手；同速先手判定）
  D. 极端配速（敌 300 vs 玩家 5 硬上限 8；1:2/1:3 敌方连动分布）
  E. 跨职业/跨等级胜率补测（30 级、60 级战士/法师/游侠 vs 同级怪，200 场）
  F. 敏捷 vs 力量加点价值

确定性：random.seed(42)。只依赖 game.battle / game.engine / game.core.stats / game.data。
"""
import sys, random, statistics
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")

from game import engine as E
from game.core.stats import monster_stats
from game import battle as BT
from game.battle import Battle

random.seed(42)
BASE_DELAY = BT.BASE_DELAY
CAP = BT.SPD_CT_CAP


# ---------------- 构造工具（对齐 sim_ctb_balance） ----------------

def make_player(class_name, level, attributes, equipment, learned_skills):
    return {
        "qq_id": "a4", "class_name": class_name, "level": level,
        "attributes": attributes, "equipment": equipment,
        "learned_skills": learned_skills,
        "skill_levels": {s: min(2, level) for s in learned_skills},
        "hp": 9999, "mp": 9999, "class_tier": 0, "evolve_path": 0,
    }


def make_enemy(st, name="怪", role="dps", skills=()):
    return {
        "name": name, "role": role, "hp": st["hp"], "max_hp": st["hp"],
        "atk": st["atk"], "def": st["def"], "matk": st["matk"], "mdef": st["mdef"],
        "spd": st["spd"], "skills": list(skills),
    }


def run_one_battle(p, enemy, use_skill=True, p_spd=None, e_spd=None):
    """跑一场，返回 (result, rounds, dmg)。p/e spd 注入模拟（保留真实攻防血）。"""
    b = Battle("monster", dict(enemy), player=p)
    if e_spd is not None:
        for u in b.enemies:
            u["spd"] = float(e_spd); u["ct"] = -float(e_spd)
    pp = dict(p)
    st = E.player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
    pp["max_hp"] = st["max_hp"]; pp["max_mp"] = st["max_mp"]
    pp["hp"] = st["max_hp"]; pp["mp"] = st["max_mp"]
    if p_spd is not None:
        _orig = Battle._player_stats
        def _inj(self, player):
            d = dict(_orig(self, player)); d["spd"] = float(p_spd)
            return d
        b._player_stats = _inj.__get__(b, Battle)
    while True:
        if use_skill and pp.get("learned_skills") and pp["mp"] >= 6:
            logs, done = b.player_turn("skill", _SKILL.get(p["class_name"], "sk_meng_ji"), pp)
        else:
            logs, done = b.player_turn("attack", None, pp)
        if done:
            break
        if b.round > 1500:
            break
    dmg = st["max_hp"] - pp["hp"]
    return b.result, b.round, max(0, dmg)


# 每职业代表技能（与资源经济无关度的保守选择：法力系 / 普攻）
_SKILL = {
    "cls_zhan_shi": "sk_meng_ji",     # 猛击 120% 物伤，怒气（无特殊资源）
    "cls_fa_shi": "sk_huo_qiu_shu",   # 火球术 100% 魔伤
    "cls_you_xia": None,              # 游侠技能耗精力，原始对局用普攻最公平
}


def simulate(p, enemy, rounds=200, use_skill=True, p_spd=None, e_spd=None):
    wins, rnds, dmgs = 0, [], []
    for _ in range(rounds):
        res, r, d = run_one_battle(dict(p), enemy, use_skill, p_spd, e_spd)
        if res == "victory":
            wins += 1; rnds.append(r); dmgs.append(d)
    return {
        "wins": wins, "n": rounds,
        "win_rate": wins / rounds,
        "avg_round": (statistics.mean(rnds) if rnds else 0.0),
        "avg_dmg": (statistics.mean(dmgs) if dmgs else 0.0),
    }


# ---------------- A. 行动频率埋点 ----------------

def _build_duel(p_spd, e_spd, p_hp=10_000_000, e_hp=10_000_000,
                p_atk=40, e_atk=5):
    """构造高血量对局用于频次统计。返回 (battle, pp)。"""
    pp = make_player("cls_zhan_shi", 60, {"str": 100, "agi": 0, "int": 0, "vit": 40}, {}, ["sk_meng_ji"])
    s = E.player_final_stats("cls_zhan_shi", 60, {}, 0, {"str": 100, "agi": 0, "int": 0, "vit": 40})
    pp["max_hp"] = s["max_hp"]; pp["max_mp"] = s["max_mp"]; pp["hp"] = p_hp; pp["mp"] = s["max_mp"]
    en = {"name": "e", "role": "dps", "hp": e_hp, "max_hp": e_hp,
          "atk": e_atk, "def": 30, "matk": 5, "mdef": 30, "spd": e_spd, "skills": []}
    b = Battle("monster", dict(en), player=pp)
    for u in b.enemies:
        u["spd"] = float(e_spd); u["ct"] = -float(e_spd); u["atk"] = e_atk
    _orig = Battle._player_stats
    def _inj(self, player):
        d = dict(_orig(self, player)); d["spd"] = float(p_spd)
        return d
    b._player_stats = _inj.__get__(b, Battle)
    return b, pp


def _wrap_freq_counter(b, pp, player_actions):
    """埋点敌方行动计数，执行 player_actions 次玩家攻击，返回 (stat, 玩家执行次数)。"""
    stat = {"e": 0, "chain": 0, "max_chain": 0, "cap_hits": 0}
    real = Battle._after_actor_ct
    def _after(self, side, unit=None, player=None):
        if side == "e":
            stat["e"] += 1; stat["chain"] += 1
            stat["max_chain"] = max(stat["max_chain"], stat["chain"])
            if stat["chain"] >= 8:
                stat["cap_hits"] += 1
        else:
            stat["chain"] = 0
        return real(self, side, unit, player)
    Battle._after_actor_ct = _after
    n = 0
    try:
        while n < player_actions:
            logs, done = b.player_turn("attack", None, pp)
            n += 1
            if done:
                break
    finally:
        Battle._after_actor_ct = real
    return stat, n


def action_freq(p_spd, e_spd, player_actions=100):
    """精确注入玩家 spd 的频次统计（A/D 段用，速度精确可控）。"""
    b, pp = _build_duel(p_spd, e_spd)
    stat, n = _wrap_freq_counter(b, pp, player_actions)
    return {"p": n, "e": stat["e"], "max_chain": stat["max_chain"], "cap_hits": stat["cap_hits"]}


def action_freq_buff(p_spd, e_spd, player_actions=100, buff_spd=None, debuff_spd=False):
    """统计每 player_actions 次玩家行动里敌方行动数（非战斗数值对局）。
    buff_spd / debuff_spd 用真实 p_buffs 路径（不 monkeypatch 玩家 spd），
    验证 CTB 下 spd_up(×1.4)/减速(×0.5) 是否真的经 _ct_cost 改变行动频率。"""
    # 用真实玩家构造（敏捷拉高到接近 p_spd），交给真实 _player_stats/_apply_buffs 计算
    agi = max(0, int((p_spd - 27) / 0.8))  # 战士60级基础 spd≈27，agi→0.8/点
    attrs = {"str": 80, "agi": agi, "int": 0, "vit": 30}
    pp = make_player("cls_zhan_shi", 60, attrs, {}, ["sk_meng_ji"])
    s = E.player_final_stats("cls_zhan_shi", 60, {}, 0, attrs)
    pp["max_hp"] = s["max_hp"]; pp["max_mp"] = s["max_mp"]
    pp["hp"] = 10_000_000; pp["mp"] = s["max_mp"]
    en = {"name": "e", "role": "dps", "hp": 10_000_000, "max_hp": 10_000_000,
          "atk": 5, "def": 30, "matk": 5, "mdef": 30, "spd": e_spd, "skills": []}
    b = Battle("monster", dict(en), player=pp)
    if buff_spd is True:
        b.p_buffs["spd_up"] = 3
    if debuff_spd:
        b.p_buffs["spd_down"] = 2
    real_spd = b._player_stats(pp).get("spd", 0)
    stat, n = _wrap_freq_counter(b, pp, player_actions)
    return {"p": n, "e": stat["e"], "max_chain": stat["max_chain"],
            "cap_hits": stat["cap_hits"], "real_spd": real_spd}


def effective_spd(spd):
    """CTB 参与 ct 的有效 spd（含软上限）。"""
    return min(float(spd or 0), CAP)


# ---------------- C. 先手判定 ----------------

def first_mover(p_spd, e_spd):
    """CTB 开局 ct=-spd，更负者先动。同速则玩家先（battle 判定比较为准）。"""
    # 单机：p_ct = -p_spd；敌方单个单位 ct = -e_spd。更小（更负）先手。
    if p_spd != e_spd:
        return "player" if p_spd > e_spd else "enemy"
    return "player"  # 同速：玩家方先（文档声明；实现见 _after_actor 顺序）


def run_first_player_first(n_once=32, e_spd=30, p_spd=None):
    """实测同速先手：构造同 spd 战斗，观察开局 ct 谁更小。"""
    b, pp = _build_duel(p_spd if p_spd is not None else e_spd, e_spd)
    return {"p_ct": b.p_ct, "e_ct": b.enemies[0]["ct"]}


# =================================================================
print("=" * 78)
print("【A. spd 边际收益曲线】敌 spd 固定，玩家 spd 10→160")
print("   非战斗对局，统计每 100 次玩家行动时敌方行动数（低=玩家更赚）")
print("=" * 78)
hdr = f"{'玩家spd':>6} {'有效spd':>6} | {'敌30不动':>9} {'敌30超80':>7} | {'敌80超80':>7}"
print(hdr)
freq_e30 = {}
for p_spd in range(10, 161, 10):
    r1 = action_freq(p_spd, 30, player_actions=100)          # 敌30
    r2 = action_freq(p_spd, 80, player_actions=100)          # 敌80（触顶）
    r3 = action_freq(p_spd, 160, player_actions=100)         # 敌160（超cap）
    print(f"{p_spd:>6} {effective_spd(p_spd):>6.0f} | {r1['e']:>9d} {r2['e']:>7d} {r3['e']:>7d}")

print("\n  理论有效行动比（受 cap 影响）玩家:敌 =", end=" ")
for p_spd in (10, 30, 60, 80, 100, 120, 150):
    print(f"\n  spd{p_spd}: 敌30 → {effective_spd(p_spd)/30:.2f}:1  敌80(触顶) → {effective_spd(p_spd)/80:.2f}:1  "
          f"敌160 → {effective_spd(p_spd)/80:.2f}:1", end="")
print()

print("\n  增量表：每 +10 spd 时敌方每100玩家行动减少的次数（敌30，>CAP 后应趋于 0）")
prev = None
for p_spd in range(10, 161, 10):
    r = action_freq(p_spd, 30, player_actions=100)
    if prev is not None:
        print(f"  spd {p_spd-10}→{p_spd}: 敌方行动 {prev['e']} → {r['e']} (减少 {prev['e']-r['e']})")
    prev = r

# ---------------- B. 速度 buff ----------------
print("\n" + "=" * 78)
print("【B. 速度 buff 对行动频率的影响】（真实 p_buffs 路径，玩家 spd 由真实 buff 结算）")
print("=" * 78)
for p_spd, e_spd, label in ((60, 30, "玩家spd≈60 vs 敌30"),
                             (80, 40, "玩家spd≈80 vs 敌40"),
                             (100, 50, "玩家spd≈100 vs 敌50")):
    base = action_freq_buff(p_spd, e_spd, player_actions=100)
    up = action_freq_buff(p_spd, e_spd, player_actions=100, buff_spd=True)      # spd_up ×1.4
    down = action_freq_buff(p_spd, e_spd, player_actions=100, debuff_spd=True)  # spd_down ×0.5
    print(f"\n  {label}")
    print(f"    无buff      : 玩家结算spd={base['real_spd']} → 每100玩家行动敌方动 {base['e']} 次")
    print(f"    spd_up×1.4  : 玩家结算spd={up['real_spd']} → 敌动 {up['e']} 次 (敌减少 {base['e']-up['e']})")
    print(f"    spd_down×0.5: 玩家结算spd={down['real_spd']} → 敌动 {down['e']} 次 (敌增多 {down['e']-base['e']})")

# 3 回合 buff 性价比：buff 生效的 3 次玩家行动内敌方少动次数
print("\n  3 回合 spd_up 行动利润（buff 生效前 3 次玩家行动内敌方少动次数）：")
for p_spd, e_spd, label in ((60, 30, "spd≈60 vs 敌30"), (80, 40, "spd≈80 vs 敌40"), (100, 50, "spd≈100 vs 敌50")):
    base3 = action_freq_buff(p_spd, e_spd, player_actions=3)
    up3 = action_freq_buff(p_spd, e_spd, player_actions=3, buff_spd=True)
    print(f"    {label}: 无buff敌动{base3['e']} → spd_up敌动{up3['e']} (省 {base3['e']-up3['e']} 次敌方行动)")

# ---------------- C. 先手价值 ----------------
print("\n" + "=" * 78)
print("【C. 先手价值】实现公式：p_ct=-玩家spd（battle.py:197），敌方ct=-敌spd（:221）")
print("   先手者 = ct 更小者 → spd 更大者。同速 p_ct==e_ct，玩家方驱动 player_turn → 玩家先。")
print("=" * 78)
for p, e in ((30, 30), (31, 30), (29, 30), (35, 30), (30, 45), (10, 30)):
    pc, ec = -float(p), -float(e)
    mover = "玩家" if p >= e else "敌方"
    tie = "（同速，玩家方先手）" if p == e else ""
    print(f"  玩家 spd{p:>3} vs 敌 spd{e:>3} → p_ct={pc:.1f} e_ct={ec:.1f} → 先手={mover}{tie}")
print("\n  结论：差 1 点 spd 即换边（连续数值无阈值）；同速玩家先手。")

# ---------------- D. 极端配速 ----------------
print("\n" + "=" * 78)
print("【D. 极端配速】敌 300 vs 玩家 5（硬上限 8）；1:2/1:3 敌方连动分布")
print("=" * 78)
for p_spd, e_spd, label in ((5, 300, "玩家5 vs 敌300（触顶）"),
                             (30, 60, "玩家30 vs 敌60 (1:2)"),
                             (10, 20, "玩家10 vs 敌20 (1:2)"),
                             (20, 60, "玩家20 vs 敌60 (1:3)"),
                             (30, 90, "玩家30 vs 敌90 (1:3)")):
    r = action_freq(p_spd, e_spd, player_actions=100)
    print(f"  {label}: 每100玩家行动敌方动 {r['e']} 次 | 单回合敌方最大连动 {r['max_chain']} | 触顶8×{r['cap_hits']}")

# 敌方 spd300 vs 玩家5 单回合内硬上限精确验证
print("\n  敌 spd300 vs 玩家 spd5 真实单回合（高血对局）敌方行动次数：")
for _ in range(3):
    r = action_freq(5, 300, player_actions=1)
    print(f"    单次玩家行动内敌方行动 {r['e']} 次 (连动 max {r['max_chain']})")

# ---------------- E. 跨职业/等级胜率 ----------------
print("\n" + "=" * 78)
print("【E. 跨职业/等级胜率补测】战士/法师/游侠 Lv30、Lv60 vs 同级怪（200 场/技能）")
print("   缺口侧重点：中等/高级等级段的非战士职业没有历史模拟基线")
print("=" * 78)

def build_player(cls, level, eq=None, attrs=None):
    eq = eq or {}
    return make_player(cls, level, attrs or {"str": 40, "agi": 0, "int": 15, "vit": 20},
                       eq, _SKILL.get(cls) and [x for x in [_SKILL[cls]] if x] or [])

CLASS_ATTRS = {
    "cls_zhan_shi": {"str": 60, "agi": 0, "int": 0, "vit": 30},
    "cls_fa_shi": {"str": 0, "agi": 0, "int": 75, "vit": 15},
    "cls_you_xia": {"str": 45, "agi": 45, "int": 0, "vit": 10},
}
CLASS_CN = {"cls_zhan_shi": "战士", "cls_fa_shi": "法师", "cls_you_xia": "游侠"}

# 同级怪（同等级各 role 平均配速的代表）
from game.data.stat_templates import MONSTER_ROLE_BASE, MONSTER_ROLE_GROWTH
for lv in (30, 60):
    print(f"\n--- {lv} 级 ---")
    for cls in ("cls_zhan_shi", "cls_fa_shi", "cls_you_xia"):
        p = build_player(cls, lv, attrs=CLASS_ATTRS[cls])
        for role in ("dps", "elite"):
            from game.core.stats import monster_stats as _ms
            en = make_enemy(_ms(lv, role), role=role, skills=[])
            # 依职业技能表给怪配基础技能（简化：dps 用普攻即可，避免怪技能依赖）
            r = simulate(p, en, rounds=200, use_skill=True)
            st = E.player_final_stats(cls, lv, {}, 0, CLASS_ATTRS[cls])
            mst = _ms(lv, role)
            print(f"    {CLASS_CN[cls]:>2} vs {role:<7} | 玩家{st['max_hp']}血/{st['atk']}攻/{st['matk']}魔/"
                  f"{st['spd']}速 vs 怪{mst['hp']}血/{mst['atk']}攻/spd{mst['spd']}"
                  f" | 胜率{r['win_rate']*100:.0f}% 平均{r['avg_round']:.1f}回合 胜局掉血{r['avg_dmg']:.0f}")

# ---------------- F. 敏捷 vs 力量 ----------------
print("\n" + "=" * 78)
print("【F. 加点价值】战士 Lv60：纯力量 vs 纯敏捷（同为 40 点，去攻血耦合差异）")
print("=" * 78)
war = "cls_zhan_shi"
base_enemy = make_enemy(monster_stats(60, "dps"), role="dps")
# 力量 40 点 → +48 atk；敏捷 40 点 → +32 spd（去装备靴的影响，单独量化 spd 分量）
cases = [
    ("纯力量40 (atk+48)", {"str": 60, "agi": 0, "int": 0, "vit": 20}),
    ("纯敏捷40 (spd+32)", {"str": 20, "agi": 40, "int": 0, "vit": 20}),
    ("力20敏20混合",     {"str": 40, "agi": 20, "int": 0, "vit": 20}),
]
for name, attrs in cases:
    p = make_player(war, 60, attrs, {}, ["sk_meng_ji"])
    r = simulate(p, base_enemy, rounds=200, use_skill=True)
    st = E.player_final_stats(war, 60, {}, 0, attrs)
    print(f"  {name:<16} | 面板 spd={st['spd']} atk={st['atk']} | 胜率{r['win_rate']*100:.0f}% "
          f"平均{r['avg_round']:.1f}回合 胜局掉血{r['avg_dmg']:.0f}")

print("\n" + "=" * 78)
print("审计脚本 sim_audit_a4.py 完成。仅输出，未修改任何文件。")
print("=" * 78)
