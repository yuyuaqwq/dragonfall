# -*- coding: utf-8 -*-
"""DOT 平衡审计 -- 汇总输出（干净表格格式，供报告引用）
场景 A/B/C/D/E"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from battle2.formulas import calc_damage
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
CLASS = {"poison": "cls_wild_hunter", "burn": "cls_fa_shi", "bleed": "cls_wild_hunter"}

def math_dot(atk, matk, max_hp, n, base_res, adapt, k, hp_ratio=1.0,
             elem_res=0, phys_reduce=0, magic_reduce=0):
    res = min(0.95, (base_res or 0)+adapt)
    hp_p = {"poison":0.015,"burn":0.010,"bleed":0.015}[k]
    atk_p = {"poison":0.5,"burn":0.0,"bleed":0.6}[k]
    matk_p = {"poison":0.0,"burn":0.4,"bleed":0.0}[k]
    p = (atk*atk_p + matk*matk_p + max_hp*hp_p) * n * (1-res)
    if k == "bleed" and hp_ratio < 0.30: p *= 2.0
    if k == "burn":
        p *= (1-min(elem_res,0.5)); p *= (1-min(magic_reduce,0.4))
    elif k == "poison":
        p *= (1-min(magic_reduce,0.4))
    else:
        p *= (1-min(phys_reduce,0.4))
    return max(0, int(p))

def run_total(lv, mode, cls, k, sv=2, cont=2, pause=2, turns=30):
    st = player_stats(lv, cls)
    m = mon(lv, "boss"); max_hp = m["hp"]; base_res = m.get("dot_res",0.9)
    straight = calc_damage(st["atk"], m["def"], False, 0.0)
    n = adapt = 0.0; last_round = -99
    dot_tot = straight_tot = 0; hp = max_hp; s_cnt = p_cnt = 0
    for r in range(1, turns+1):
        stacked = False
        if mode == "maintain":
            if n < 5:
                n = min(5, n+sv); adapt = min(0.20, adapt+0.04); last_round = r; stacked = True
        elif mode == "tempo":
            if s_cnt < cont:
                n = min(5, n+sv); adapt = min(0.20, adapt+0.04); last_round = r; stacked = True
                s_cnt += 1; p_cnt = 0
            else:
                p_cnt += 1
                if p_cnt >= pause: s_cnt = 0; p_cnt = 0
        elif mode == "straight":
            pass
        dmg = math_dot(st["atk"], st["matk"], max_hp, n, base_res, adapt, k,
                       hp_ratio=hp/max_hp if hp>0 else 1.0)
        dot_tot += dmg
        if ((mode=="tempo" and not stacked) or mode=="straight"):
            straight_tot += straight
        hp -= dmg + (straight if ((mode=="tempo" and not stacked) or mode=="straight") else 0)
        if n > 0:
            if (r-last_round) >= 2 and adapt > 0: adapt = max(0.0, adapt-0.04)
            n -= 1
        if hp <= 0: break
    return dot_tot, straight_tot

print("="*70)
print("场景 A: 纯 dot 击杀 Boss 可行性（维持满层 dot 累计占 Boss 血 %）")
print(f"{'Lv':<4}{'Boss血':<9}{'30回合纯dot累计%':<16}{'纯dot击杀?'}")
for lv in LV:
    max_hp = mon(lv,"boss")["hp"]
    d, _ = run_total(lv, "maintain", CLASS["poison"], "poison", turns=30)
    pct = d/max_hp*100
    print(f"{lv:<4}{max_hp:<9}{pct:<16.1f}{'否(需直伤/爆发补刀)'}")

print()
print("="*70)
print("场景 A2: dot 总输出占比（节奏叠2停2 + 直伤穿插，30回合 Boss 战）")
print(f"{'Lv':<4}{'dot累计':<9}{'直伤累计':<9}{'总输出':<9}{'总占Boss%':<10}{'dot占比':<9}")
for lv in LV:
    max_hp = mon(lv,"boss")["hp"]
    d, s = run_total(lv, "tempo", CLASS["poison"], "poison")
    print(f"{lv:<4}{d:<9}{s:<9}{d+s:<9}{(d+s)/max_hp*100:<10.1f}{d/(d+s)*100 if d+s else 0:<9.1f}%")

print()
print("="*70)
print("场景 B: 适应机制 (30回合 Boss 战, 叠毒+2/回合)")
print(f"{'Lv':<4}{'无脑叠毒':<11}{'节奏叠2停2+直伤':<15}{'纯直伤':<9}{'无脑vs节奏':<12}")
for lv in LV:
    max_hp = mon(lv,"boss")["hp"]
    d1,s1 = run_total(lv, "maintain", CLASS["poison"], "poison")
    d2,s2 = run_total(lv, "tempo", CLASS["poison"], "poison")
    d3,ss = run_total(lv, "straight", CLASS["poison"], "poison")
    m1 = d1+s1; m2 = d2+s2; m3 = ss
    print(f"{lv:<4}{m1:<11}{m2:<15}{m3:<9}{f'+{(m2/m1-1)*100:.0f}%' if m2>m1 else '差'}  (纯直伤{m3/m1:.2f}x 无脑)")

print()
print("="*70)
print("场景 C: 毒爆/灼爆伤害 + 虚弱 (Boss, 毒蚀生效)")
for lv in LV:
    st = player_stats(lv, CLASS["poison"]); m = mon(lv,"boss")
    atk, max_hp, bdef = st["atk"], m["hp"], m["def"]
    for n in (3,5):
        eff = bdef*(1-min(0.20, n*0.04))
        dmg = atk*atk/(atk+max(1,eff))*(0.15*n)
        print(f"Lv{lv} 毒爆{n}:≈{dmg:.0f}({dmg/max_hp*100:.2f}%Boss) 虚弱-{5*n}% | ", end="")
    print()
    stb = player_stats(lv, CLASS["burn"]); mbt, mbmax, bmd = stb["matk"], m["hp"], m["mdef"]
    for n in (3,5):
        mult = 1.0+(0.10*(n-2) if n>=3 else 0.0)
        dmg = mbt*mbt/(mbt+max(1,bmd))*(0.30*n*mult)
        print(f"Lv{lv} 灼爆{n}:≈{dmg:.0f}({dmg/mbmax*100:.2f}%Boss) 易燃×{mult} | ", end="")
    print()
    # 虚弱承伤
    stp = player_stats(lv, CLASS["poison"]); b_atk = m["atk"]
    d0 = b_atk*b_atk/(b_atk+max(1,stp["def"]))
    for n in (3,5):
        ea = int(b_atk*0.70*(1-0.05*n))
        d1 = ea*ea/(ea+max(1,stp["def"]))
        print(f"  虚弱{n}: Boss atk{b_atk}→{ea} 承伤{d0:.0f}→{d1:.0f}(↓{(1-d1/d0)*100:.0f}%)")
    print()

print("="*70)
print("场景 D: 重伤 vs 吸血站撸 (Boss 承伤 vs 玩家普攻吸血)")
for lv in LV:
    st = player_stats(lv, CLASS["poison"]); m = mon(lv,"boss")
    b_hit = m["atk"]*m["atk"]/(m["atk"]+max(1,st["def"]))
    sta = calc_damage(st["atk"], m["def"], False, 0.0)
    ls30, ls15 = sta*0.30, sta*0.15
    net30, net15 = b_hit-ls30, b_hit-ls15
    s30 = st["max_hp"]/max(1,net30); s15 = st["max_hp"]/max(1,net15)
    print(f"Lv{lv}: Boss打{b_hit:.0f} 吸血30%={ls30:.0f}/重伤15%={ls15:.0f}; 净损{net30:.0f}→{net15:.0f}; "
          f"可持续{s30:.0f}→{s15:.0f}回合")

print()
print("="*70)
print("场景 E: 三种 dot 同节点满层对比 (普通怪/精英/Boss)")
for lv in LV:
    for role, rl in (("普通怪","tank"),("精英","elite"),("Boss","boss")):
        m = mon(lv, rl); base = m.get("dot_res",0) or 0
        row = []
        for k in ("poison","burn","bleed"):
            st = player_stats(lv, CLASS[k])
            d = math_dot(st["atk"], st["matk"], m["hp"], 5, base, 0.0, k)
            row.append(f"{k}={d}({d/m['hp']*100:.1f}%)")
        print(f"  Lv{lv} {role}(血{m['hp']},防{m['def']}/{m['mdef']}): {', '.join(row)}")
    print()
