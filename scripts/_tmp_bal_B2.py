# -*- coding: utf-8 -*-
"""场景 B 决定性测试：玩家总输出 = dot + 直伤（tempo 停手回合用直伤补）
比较：
  A) 纯无脑叠毒（每回合叠，无直伤）
  B) 节奏叠2停2，停手回合打直伤
  C) 纯直伤（不叠毒）
判断：适应机制是否让"无脑叠毒"明显劣于"节奏叠毒 + 直伤穿插"？"""
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

def math_dot(atk, matk, max_hp, n, base_res, adapt, k, hp_ratio=1.0):
    res = min(0.95, (base_res or 0)+adapt)
    hp_p = {"poison":0.015,"burn":0.010,"bleed":0.015}[k]
    atk_p = {"poison":0.5,"burn":0.0,"bleed":0.6}[k]
    matk_p = {"poison":0.0,"burn":0.4,"bleed":0.0}[k]
    p = (atk*atk_p + matk*matk_p + max_hp*hp_p) * n * (1-res)
    if k == "bleed" and hp_ratio < 0.30: p *= 2.0
    return max(0, int(p))

def run(lv, mode, sv=2, cont=2, pause=2):
    st = player_stats(lv, "cls_wild_hunter")
    m = mon(lv, "boss"); max_hp = m["hp"]; base_res = m.get("dot_res",0.9)
    straight = calc_damage(st["atk"], m["def"], False, 0.0)
    n = adapt = 0.0; last_round = -99
    dot_tot = straight_tot = 0; hp = max_hp
    s_cnt = p_cnt = 0
    for r in range(1, 31):
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
        # 行动输出：叠层回合无直伤；停手回合打直伤
        dmg = math_dot(st["atk"], st["matk"], max_hp, n, base_res, adapt, "poison",
                       hp_ratio=(hp/max_hp) if hp > 0 else 1.0)
        dot_tot += dmg
        if mode == "tempo" and not stacked:
            straight_tot += straight
        elif mode == "straight":
            straight_tot += straight
        hp -= dmg + (straight if ((mode=="tempo" and not stacked) or mode=="straight") else 0)
        if n > 0:
            if (r - last_round) >= 2 and adapt > 0: adapt = max(0.0, adapt-0.04)
            n -= 1
        if hp <= 0: break
    return dot_tot, straight_tot

print(f"{'Lv':<4}{'策略':<16}{'dot累计':<10}{'直伤累计':<10}{'总输出':<10}{'总占Boss%':<10}")
for lv in LV:
    max_hp = mon(lv,"boss")["hp"]
    d1, s1 = run(lv, "maintain")
    d2, s2 = run(lv, "tempo")
    d3, s3   = run(lv, "straight")
    print(f"{lv:<4}{'无脑叠毒':<16}{d1:<10}{s1:<10}{d1+s1:<10}{(d1+s1)/max_hp*100:<10.1f}")
    print(f"{lv:<4}{'节奏叠2停2+直伤':<16}{d2:<10}{s2:<10}{d2+s2:<10}{(d2+s2)/max_hp*100:<10.1f}")
    print(f"{lv:<4}{'纯直伤':<16}{0:<10}{s3:<10}{s3:<10}{s3/max_hp*100:<10.1f}")
    # 判定
    mnt = d1+s1; tpo = d2+s2
    print(f"      → 无脑({mnt}) vs 节奏+直伤({tpo}): 节奏{'更优' if tpo>mnt else '更差'}(+{(tpo/mnt-1)*100 if mnt else 0:.0f}%)")
    print(f"      → 纯直伤({s3}) vs 无脑叠毒({mnt}): {'纯直伤更优' if s3>mnt else '叠毒更优'}(+{(abs(s3-mnt)/max(1,min(s3,mnt)))*100:.0f}%)")
