# -*- coding: utf-8 -*-
"""敏感性：玩家 atk 强度档 (boost 1.0/1.5/2.0) 对 key 结论的影响"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from saintess_engine.formulas import calc_damage
from game.content_rules.panel import player_final_stats
from game.core import stats as S

def player_stats(lv, cls, boost):
    eq = {s: {"stats": S.equip_stats(s, lv, "blue")} for s in
          ("weapon","armor","ring","helm","legs","necklace","boots")}
    attrs = {"str": 2*(lv-1), "vit": 1*(lv-1), "int": 0, "agi": 0}
    st = player_final_stats(cls, lv, eq, tier=1, attributes=attrs,
                              evolve_path=0, title_bonus={}, race="human")
    st["atk"]=int(st["atk"]*boost); st["matk"]=int(st["matk"]*boost)
    return st
def mon(lv, role): return S.monster_stats(lv, role)

def math_dot(atk, matk, max_hp, n, base_res, adapt, k, hp_ratio=1.0):
    res = min(0.95, (base_res or 0)+adapt)
    hp_p={"poison":0.015,"burn":0.010,"bleed":0.015}[k]
    atk_p={"poison":0.5,"burn":0.0,"bleed":0.6}[k]
    matk_p={"poison":0.0,"burn":0.4,"bleed":0.0}[k]
    p=(atk*atk_p+matk*matk_p+max_hp*hp_p)*n*(1-res)
    if k=="bleed" and hp_ratio<0.30: p*=2.0
    return max(0,int(p))

print(f"{'Lv':<4}{'boost':<7}{'玩家atk':<8}{'Boss血':<8}{'直伤/回合':<9}{'满层dot/回合':<11}{'dot/直伤%':<9}{'dot占比':<8}")
for lv in (30,60,90):
    m = mon(lv,"boss")
    for b in (1.0, 1.5, 2.0):
        st = player_stats(lv, "cls_wild_hunter", b)
        stra = calc_damage(st["atk"], m["def"], False, 0.0)
        dy = math_dot(st["atk"], st["matk"], m["hp"], 5, 0.9, 0.20, "poison")
        print(f"{lv:<4}{b:<7}{st['atk']:<8}{m['hp']:<8}{stra:<9}{dy:<11}{dy/max(1,stra)*100:<9.0f}{dy/(dy+stra)*100:<8.0f}%")

print()
print("Boss 战期望回合数：玩家需造成 100%Boss 血（直伤+dot+爆发）")
for lv in (30,60,90):
    m=mon(lv,"boss"); st=player_stats(lv,"cls_wild_hunter",1.0)
    hp=m["hp"]; stra=calc_damage(st["atk"],m["def"],False,0.0)
    # 满配直伤（技能倍率~2x普攻，+毒蚀降防）：估 直伤力 ≈ 2.2×基础普攻
    skilled = int(stra*2.2)
    turns = hp/skilled
    print(f"  Lv{lv}: 纯技能直伤(≈{skilled}/回合) 击杀需 ≈{turns:.0f} 回合（若玩家能扛住）")
