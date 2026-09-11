# -*- coding: utf-8 -*-
"""DOT 数值平衡审计模拟（纯数学 + 真实 _tick_dots 校验）
场景：
  A: 毒系玩家多等级节点 dot 总伤占比 + 纯 dot 击杀回合数（维持满层 vs 不维持）
  B: 适应机制抑制曲线（连续叠毒 vs 节奏叠毒 2叠1停）
  C: 毒爆 3/5 层伤害占比 + 虚弱压制
  D: 重伤对吸血流影响 + Boss 战可持续性
  E: 灼烧/流血对比（防"毒一家独大"）
只读！不改 game/ 与 tests/。"""
import sys, os, math, random
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from saintess_engine.battle.formulas import calc_damage
from game.content_rules.panel import player_final_stats
from game import battle as BT
from game.core import stats as S

# ------------- 基线参数 -------------
def player_stats(lv, cls, gear="gear", boost=1.0):
    if gear == "gear":
        eq = {s: {"stats": S.equip_stats(s, lv, "blue")} for s in
              ("weapon", "armor", "ring", "helm", "legs", "necklace", "boots")}
    else:
        eq = {}
    attrs = {"str": 2 * (lv - 1), "vit": 1 * (lv - 1), "int": 0, "agi": 0}
    st = player_final_stats(cls, lv, eq, tier=1, attributes=attrs,
                              evolve_path=0, title_bonus={}, race="human")
    st["atk"] = int(st["atk"] * boost)
    st["matk"] = int(st["matk"] * boost)
    return st

def mon(lv, role):
    return S.monster_stats(lv, role)

# 三个等级节点 + 强度档（gear=普通配装, gear2=强配装 atk×2 作为上界）
LV = [30, 60, 90]
CLASS = {
    "poison": "cls_wild_hunter",  # 游侠（藤蔓/毒爆术）毒系
    "burn":   "cls_fa_shi",       # 法师热量系
    "bleed":  "cls_wild_hunter",  # 流血挂物攻
}
# 对 Boss 战一个玩家的"直伤回合数"假设（无 dot 阶段把 boss 打残再 dot 补刀）
BOSS_TURNS_TARGET = {"30": 20, "60": 25, "90": 30}  # 设计期望回合数

# ------------- 校验：纯数学 == 真实 _tick_dots -------------
def real_tick_dmg(atk, matk, max_hp, n, dot_res, adapt, k, mdef=0, def_=0,
                  phys_reduce=0, magic_reduce=0, elem_res=0):
    """用真实 Battle._tick_dots 结算单个初值，返回 dot 伤害。"""
    player = {"class_name": "cls_wild_hunter", "level": 30, "hp": 1, "max_hp": 1,
              "mp": 1, "max_mp": 1, "equipment": {}, "attributes": {}, "spd": 1,
              "crit": 0, "learned_skills": [], "race": "human"} if k != "burn" else \
             {"class_name": "cls_fa_shi", "level": 30, "hp": 1, "max_hp": 1,
              "mp": 1, "max_mp": 1, "equipment": {}, "attributes": {}, "spd": 1,
              "crit": 0, "learned_skills": [], "race": "human"}
    e = {"name": "靶", "hp": max_hp, "max_hp": max_hp, "atk": 1, "def": def_,
         "matk": 1, "mdef": mdef, "spd": 1, "buffs": {}, "dot_res": dot_res,
         "adapt": {"poison": adapt, "burn": adapt},
         "phys_reduce": phys_reduce, "magic_reduce": magic_reduce, "elem_res": elem_res}
    e["debuffs"] = {k: {"n": n, "mult": 1.0}}
    b = BT.Battle("monster", e)
    b._dot_pending = True
    # 固定施法者属性快照
    b._player_stats = lambda pl: {"atk": atk, "matk": matk, "def": 0, "mdef": 0,
                                  "spd": 10, "crit": 0, "max_hp": 1, "max_mp": 1}
    before = b.enemy["hp"]
    logs = []
    b._tick_dots(player, logs)
    return before - b.enemy["hp"]

def math_dot_dmg(atk, matk, max_hp, n, dot_res, adapt, k, mdef=0, def_=0,
                 phys_reduce=0, magic_reduce=0, elem_res=0):
    """纯公式：与 _tick_dots 完全一致（混合公式 + 层数 + 总抗 + 敌防削减）。"""
    res = min(0.95, (dot_res or 0) + adapt)
    hp_p = {"poison": 0.015, "burn": 0.010, "bleed": 0.015}[k]
    atk_p = {"poison": 0.5, "burn": 0.0, "bleed": 0.6}[k]
    matk_p = {"poison": 0.0, "burn": 0.4, "bleed": 0.0}[k]
    base = (atk * atk_p + matk * matk_p + max_hp * hp_p) * n * (1 - res)
    # 敌防削减段（无格挡 roll）
    if k == "burn":
        p = base
        if elem_res > 0:
            er = min(elem_res, 0.5)
            p = p * (1 - er)
        if magic_reduce > 0:
            p = p * (1 - min(magic_reduce, 0.4))
    elif k == "poison":
        p = base
        if magic_reduce > 0:
            p = p * (1 - min(magic_reduce, 0.4))
    else:
        p = base
        if phys_reduce > 0:
            p = p * (1 - min(phys_reduce, 0.4))
    return max(0, int(p))

# 校验若干组合
VAL_OK = True
for atk in (100, 242, 698):
    for mhp in (10000, 68653):
        for n in (1, 3, 5):
            for dr in (0.0, 0.8, 0.9):
                for ad in (0.0, 0.12, 0.20):
                    for k in ("poison",):
                        r = real_tick_dmg(atk, 0, mhp, n, dr, ad, k)
                        m = math_dot_dmg(atk, 0, mhp, n, dr, ad, k)
                        if r != m:
                            print(f"MISMATCH poison atk={atk} hp={mhp} n={n} res={dr} ad={ad}: real={r} math={m}")
                            VAL_OK = False
for atk, matk in ((0, 216), (0, 603)):
    for mhp in (10000, 68653):
        for n in (1, 3, 5):
            for dr in (0.0, 0.9):
                for ad in (0.0, 0.20):
                    for k in ("burn",):
                        r = real_tick_dmg(atk, matk, mhp, n, dr, ad, k)
                        m = math_dot_dmg(atk, matk, mhp, n, dr, ad, k)
                        if r != m:
                            print(f"MISMATCH burn matk={matk} hp={mhp} n={n} res={dr} ad={ad}: real={r} math={m}")
                            VAL_OK = False
for atk in (100, 698):
    for mhp in (10000, 68653):
        for n in (1, 3):
            for k in ("bleed",):
                r = real_tick_dmg(atk, 0, mhp, n, 0.0, 0.0, k)
                m = math_dot_dmg(atk, 0, mhp, n, 0.0, 0.0, k)
                if r != m:
                    print(f"MISMATCH bleed atk={atk} hp={mhp} n={n}: real={r} math={m}")
                    VAL_OK = False
print(f"[校验] 纯数学 vs 真实 _tick_dots 全一致: {VAL_OK}")

def sim_boss_dot(lv, cls, k, maintain, adapt_cap_hits=5, turns=30):
    """模拟 Boss 战一轮轮叠毒，返回每回合 dot 伤害序列与累计占比。
    maintain=True: 每回合叠至满层持续维持; maintain=False: 叠满5层后停手(让层自然衰减)
    adapt: 每次叠层 +0.04 cap 0.20; 2 回合未叠回落 -0.04。"""
    st = player_stats(lv, cls)
    atk, matk = st["atk"], st["matk"]
    m = mon(lv, "boss")
    max_hp = m["hp"]
    base_res = m.get("dot_res", 0.9)
    n = 0
    adapt = 0.0
    last_round = -99
    seq = []
    hp_left = max_hp
    for r in range(1, turns + 1):
        # 叠层决策
        if maintain:
            if n < 5:
                n = min(5, n + 1)
                adapt = min(0.20, adapt + 0.04)
                last_round = r
        else:
            if n < 5:
                n = min(5, n + 1)
                adapt = min(0.20, adapt + 0.04)
                last_round = r
            else:
                # 满层停手，让层自然衰减
                pass
        # 结算 dot（每回合结算 n 层）
        dmg = math_dot_dmg(atk, matk, max_hp, n, base_res, adapt, k)
        hp_left -= dmg
        seq.append(dmg)
        # 结算后层数 n-1；残余再往下回合由是否继续叠决定
        n_after = max(0, n - 1)
        # 适应回落：结算时若 round - last_round >= 2 → -0.04
        if n_after > 0 and (r - last_round) >= 2:
            adapt = max(0.0, adapt - 0.04)
        n = n_after
        if hp_left <= 0:
            return {"kill_round": r, "seq": seq}
    return {"kill_round": None, "seq": seq}

print("\n========== 场景 A：毒系纯 dot 击杀 Boss 回合数（维持 vs 不维持）==========")
print(f"{'Lv':<4}{'策略':<8}{'前10回合累计dot':<14}{'dot占Boss血%':<12}{'纯dot击杀回合':<10}{'30回合累计%':<10}")
for lv in LV:
    cls = CLASS["poison"]
    m = mon(lv, "boss")
    max_hp = m["hp"]
    st = player_stats(lv, cls)
    a1 = sim_boss_dot(lv, cls, "poison", maintain=True, turns=30)
    a2 = sim_boss_dot(lv, cls, "poison", maintain=False, turns=30)
    def pct(res): return sum(res["seq"]) / max_hp * 100
    for tag, a in (("维持", a1), ("不维持", a2)):
        kr = a["kill_round"] if a["kill_round"] else "-"
        cum30 = sum(a["seq"])
        print(f"{lv:<4}{tag:<8}{sum(a['seq'][:10]):<14}{pct(a):<12.1f}{kr:<10}{cum30/max_hp*100:<10.1f}")

print("\n========== 场景 A2：dot 总伤占比 = 纯 dot 回合伤 / 直伤回合期望输出 ==========")
# 假设玩家每回合直伤 ≈ calc_damage(atk, boss_def)，dot 全伤在窗口内
for lv in LV:
    cls = CLASS["poison"]
    m = mon(lv, "boss")
    st = player_stats(lv, cls)
    atk = st["atk"]
    straight = calc_damage(atk, m["def"], False, 0.0)
    # 满层维持时的 dot 回合伤（稳态，adapt 顶到 0.2）
    adapt = 0.20
    dot_full = math_dot_dmg(atk, st["matk"], m["hp"], 5, 0.9, adapt, "poison")
    # 适应 0 时
    dot_full0 = math_dot_dmg(atk, st["matk"], m["hp"], 5, 0.9, 0.0, "poison")
    print(f"Lv{lv}: 直伤/回合≈{straight}, 满层dot/回合(adapt0)={dot_full0}, "
          f"(adapt20%)={dot_full}, dot/直伤比(adapt0)={dot_full0/max(1,straight)*100:.0f}%")
