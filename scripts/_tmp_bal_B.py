# -*- coding: utf-8 -*-
"""场景 B 精修 + 输出占比模型（副本团队回合）
tempo = 叠2回合，停2回合（contract: 停 2~3 回合等回落）"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from saintess_engine.battle.formulas import calc_damage
from game.content_rules.panel import player_final_stats
from game.core import stats as S

def player_stats(lv, cls, boost=1.0):
    eq = {s: {"stats": S.equip_stats(s, lv, "blue")} for s in
          ("weapon", "armor", "ring", "helm", "legs", "necklace", "boots")}
    attrs = {"str": 2*(lv-1), "vit": 1*(lv-1), "int": 0, "agi": 0}
    st = player_final_stats(cls, lv, eq, tier=1, attributes=attrs,
                              evolve_path=0, title_bonus={}, race="human")
    st["atk"] = int(st["atk"]*boost); st["matk"] = int(st["matk"]*boost)
    return st

def mon(lv, role):
    return S.monster_stats(lv, role)

LV = [30, 60, 90]

def math_dot(atk, matk, max_hp, n, base_res, adapt, k, hp_ratio=1.0,
             elem_res=0, phys_reduce=0, magic_reduce=0):
    res = min(0.95, (base_res or 0)+adapt)
    hp_p = {"poison":0.015,"burn":0.010,"bleed":0.015}[k]
    atk_p = {"poison":0.5,"burn":0.0,"bleed":0.6}[k]
    matk_p = {"poison":0.0,"burn":0.4,"bleed":0.0}[k]
    p = (atk*atk_p + matk*matk_p + max_hp*hp_p) * n * (1-res)
    if k == "bleed" and hp_ratio < 0.30:
        p *= 2.0
    if k == "burn":
        p *= (1 - min(elem_res,0.5)); p *= (1 - min(magic_reduce,0.4))
    elif k == "poison":
        p *= (1 - min(magic_reduce,0.4))
    else:
        p *= (1 - min(phys_reduce,0.4))
    return max(0, int(p))

def sim(lv, cls, k, mode, cont, pause, sv, turns=30):
    st = player_stats(lv, cls)
    m = mon(lv, "boss")
    max_hp = m["hp"]; base_res = m.get("dot_res", 0.9)
    n = adapt = 0.0 if False else 0
    last_round = -99
    dot=[]; ad=[]; nl=[]
    hp = max_hp
    s_cnt = p_cnt = 0
    for r in range(1, turns+1):
        # 叠层行动
        if mode == 'maintain':
            if n < 5:
                n = min(5, n+sv); adapt = min(0.20, adapt+0.04); last_round = r
        else:  # tempo
            if s_cnt < cont:
                n = min(5, n+sv); adapt = min(0.20, adapt+0.04); last_round = r
                s_cnt += 1; p_cnt = 0
            else:
                p_cnt += 1
                if p_cnt >= pause:
                    s_cnt = 0; p_cnt = 0
        dmg = math_dot(st["atk"], st["matk"], max_hp, n, base_res, adapt, k,
                       hp_ratio=hp/max_hp)
        dot.append(dmg); ad.append(adapt); nl.append(n)
        hp -= dmg
        if n > 0:
            if (r - last_round) >= 2 and adapt > 0:
                adapt = max(0.0, adapt-0.04)
            n -= 1
        if hp <= 0:
            break
    return dot, ad, nl

print("===== 场景 B（精修）=====")
for lv in LV:
    max_hp = mon(lv,"boss")["hp"]
    mtn = sim(lv, "cls_wild_hunter", "poison", 'maintain', 0, 0, 2, 30)
    tmp = sim(lv, "cls_wild_hunter", "poison", 'tempo', 2, 2, 2, 30)
    m = sum(mtn[0]); t = sum(tmp[0])
    print(f"Lv{lv}: 无脑叠满 dot累计={m} ({m/max_hp*100:.1f}%Boss) [末adapt={mtn[1][-1]:.2f} 末层={mtn[2][-1]}]")
    print(f"      节奏叠2停2 dot累计={t} ({t/max_hp*100:.1f}%Boss) [末adapt={tmp[1][-1]:.2f} 末层={tmp[2][-1]}]")
    print(f"      → 无脑/节奏 = {m/t:.2f}")

print("\n===== dot 输出占比（vs 直伤）=====")
for lv in LV:
    m = mon(lv,"boss"); max_hp = m["hp"]
    st = player_stats(lv, "cls_wild_hunter")
    straight = calc_damage(st["atk"], m["def"], False, 0.0)
    # 满层 dot（adapt 0 稳态 vs 稳态适应后）
    d0 = math_dot(st["atk"], st["matk"], max_hp, 5, 0.9, 0.20, "poison")
    print(f"Lv{lv}: 直伤/回合≈{straight}, 满层dot稳态(adapt20%)≈{d0}, "
          f"dot/直伤 = {d0/max(1,straight)*100:.0f}%  → dot占比≈{d0/(d0+straight)*100:.0f}%")

print("\n【结论】dot 满层稳态单回合 ≈ 直伤单回合的 50-80% → dot 总输出占比 ~40%± "
      "(若玩家一半行动在叠毒/一半在直伤，dot占比 ~35-45%，贴近或略超 20-40% 目标)")
