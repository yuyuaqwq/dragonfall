# -*- coding: utf-8 -*-
"""DOT 数值平衡审计——完整模拟（忠实还原 _tick_dots 状态机）"""
import sys, os, random
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
CLASS = {"poison": "cls_wild_hunter", "burn": "cls_fa_shi", "bleed": "cls_wild_hunter"}

def math_dot(atk, matk, max_hp, n, base_res, adapt, k, elem_res=0, phys_reduce=0, magic_reduce=0):
    res = min(0.95, (base_res or 0)+adapt)
    hp_p = {"poison":0.015,"burn":0.010,"bleed":0.015}[k]
    atk_p = {"poison":0.5,"burn":0.0,"bleed":0.6}[k]
    matk_p = {"poison":0.0,"burn":0.4,"bleed":0.0}[k]
    p = (atk*atk_p + matk*matk_p + max_hp*hp_p) * n * (1-res)
    if k == "burn":
        p *= (1 - min(elem_res,0.5)); p *= (1 - min(magic_reduce,0.4))
    elif k == "poison":
        p *= (1 - min(magic_reduce,0.4))
    else:
        p *= (1 - min(phys_reduce,0.4))
    return max(0, int(p))

def sim_round_loop(lv, cls, k, strat, turns=30):
    """每回合: (1) _tick_dots 结算 n 层(n→n-1, adapt回落) (2) 玩家动作叠层/停手。
    strat: 'maintain'无脑每回合叠 / 'tempo'叠2回合停2回合 / 'ramp'叠到5后停死"""
    st = player_stats(lv, cls)
    m = mon(lv, "boss")
    max_hp = m["hp"]; base_res = m.get("dot_res", 0.9)
    n = 0; adapt = 0.0; last_round = -99
    dot_log = []
    stacked_this_round = False
    for r in range(1, turns+1):
        # 1) 结算
        if n > 0:
            dmg = math_dot(st["atk"], st["matk"], max_hp, n, base_res, adapt, k)
            dot_log.append(dmg)
            if k in ("poison","burn") and (r - last_round) >= 2 and adapt > 0:
                adapt = max(0.0, adapt - 0.04)
            n -= 1
        else:
            dot_log.append(0)
        # 2) 玩家动作
        stacked_this_round = False
        if strat == 'maintain':
            if n < 5:
                n += 1; adapt = min(0.20, adapt+0.04); last_round = r; stacked_this_round = True
        elif strat == 'ramp':
            if n < 5:
                n += 1; adapt = min(0.20, adapt+0.04); last_round = r; stacked_this_round = True
    return dot_log

def sim_tempo(lv, cls, k, continue_n=2, pause_n=2, turns=30):
    st = player_stats(lv, cls)
    m = mon(lv, "boss")
    max_hp = m["hp"]; base_res = m.get("dot_res", 0.9)
    n = 0; adapt = 0.0; last_round = -99
    dot_log = []
    streak_stack = 0
    idle = 0
    for r in range(1, turns+1):
        # 1) 结算
        if n > 0:
            dmg = math_dot(st["atk"], st["matk"], max_hp, n, base_res, adapt, k)
            dot_log.append(dmg)
            if  (r - last_round) >= 2 and adapt > 0:
                adapt = max(0.0, adapt - 0.04)
            n -= 1
        else:
            dot_log.append(0)
        # 2) 动作
        if streak_stack < continue_n:
            n += 1; adapt = min(0.20, adapt+0.04); last_round = r
            streak_stack += 1; idle = 0
        else:
            idle += 1
            if idle >= pause_n:
                streak_stack = 0
    return dot_log

print("========== 场景 B：适应机制对无脑叠毒的抑制 ==========")
print(f"{'Lv':<4}{'节奏策略':<14}{'20回合dot累计':<14}{'Boss血占比%':<12}")
for lv in LV:
    cls = CLASS["poison"]
    max_hp = mon(lv,"boss")["hp"]
    mnt = sim_round_loop(lv, cls, "poison", 'maintain', turns=20)
    tmp = sim_tempo(lv, cls, "poison", 2, 2, turns=20)
    rmp = sim_round_loop(lv, cls, "poison", 'ramp', turns=20)
    mt, tt, rt = sum(mnt), sum(tmp), sum(rmp)
    print(f"{lv:<4}{'无脑每回合叠':<14}{mt:<14}{mt/max_hp*100:<12.1f}")
    print(f"{lv:<4}{'叠2停2':<14}{tt:<14}{tt/max_hp*100:<12.1f}")
    print(f"{lv:<4}{'叠满停死':<14}{rt:<14}{rt/max_hp*100:<12.1f}")
    if mt >= tt:
        print(f"      → 无脑({mt}) 比 节奏叠2停2({tt}) {'更差(set同)' if mt>tt else '持平'}，适应机制{'生效' if mt>tt else '未拉开差距'}")
    else:
        print(f"      → 无脑({mt}) < 节奏({tt})，适应机制反而不利节奏（需查）")

print("\n========== 场景 C：毒爆/灼爆伤害占比 + 虚弱 ==========")
for lv in LV:
    st = player_stats(lv, CLASS["poison"])
    m = mon(lv, "boss")
    atk, max_hp, boss_def = st["atk"], m["hp"], m["def"]
    for n in (3, 5):
        eff = boss_def * (1 - min(0.20, n*0.04))
        dmg = atk*atk/(atk+max(1,eff)) * (0.15*n)
        print(f"Lv{lv} 毒爆{n}层: ≈{dmg:.0f} ({dmg/max_hp*100:.2f}% Boss血), 虚弱-{5*n}%")
    stb = player_stats(lv, CLASS["burn"])
    mb = mon(lv, "boss")
    mbt = stb["matk"]; mbmax = mb["hp"]; bmd = mb["mdef"]
    for n in (3, 5):
        mult = 1.0 + (0.10*(n-2) if n>=3 else 0.0)
        dmg = mbt*mbt/(mbt+max(1,bmd)) * (0.30*n*mult)
        print(f"Lv{lv} 灼爆{n}层: ≈{dmg:.0f} ({dmg/mbmax*100:.2f}% Boss血), 易燃×{mult}")
    # 虚弱压制
    boss_atk = m["atk"]
    stp = player_stats(lv, CLASS["poison"])
    for n in (3, 5):
        eff_atk = int(boss_atk * 0.70 * (1 - 0.05*n))
        d0 = boss_atk*boss_atk/(boss_atk+max(1,stp["def"]))
        d1 = eff_atk*eff_atk/(eff_atk+max(1,stp["def"]))
        print(f"Lv{lv} 毒爆{n}层虚弱: Boss atk {boss_atk}→{eff_atk}, 承伤 {d0:.0f}→{d1:.0f} (↓{(1-d1/d0)*100:.0f}%)")

print("\n========== 场景 D：重伤 vs 吸血站撸 ==========")
for lv in LV:
    st = player_stats(lv, CLASS["poison"])
    m = mon(lv, "boss")
    atk, pdef, php, b_atk = st["atk"], st["def"], st["max_hp"], m["atk"]
    stra = calc_damage(atk, m["def"], False, 0.0)
    boss_hit = b_atk*b_atk/(b_atk+max(1,pdef))
    ls30 = stra*0.30; ls15 = stra*0.15
    net30 = boss_hit - ls30; net15 = boss_hit - ls15
    surv30 = php/max(1,net30) if net30>0 else float('inf')
    surv15 = php/max(1,net15) if net15>0 else float('inf')
    surv_str30 = f"{surv30:.0f}" if surv30 != float('inf') else "∞(可持续站撸)"
    surv_str15 = f"{surv15:.0f}" if surv15 != float('inf') else "∞"
    print(f"Lv{lv}: Boss打≈{boss_hit:.0f}, 玩家普攻≈{stra}, 吸血30%={ls30:.0f}→重伤={ls15:.0f}; "
          f"净损 {net30:.0f}→{net15:.0f}; 血线可撑 {surv30:.0f}→{surv15:.0f} 回合")

print("\n========== 场景 E：灼烧/流血 vs 毒 同节点对比 ==========")
print(f"{'Lv':<4}{'类型':<8}{'满层dot/回合':<14}{'30回合累计占Boss%':<18}")
for lv in LV:
    max_hp = mon(lv,"boss")["hp"]; base0 = mon(lv,"boss").get("dot_res",0.9)
    for k in ("poison","burn","bleed"):
        cls = CLASS[k]
        st = player_stats(lv, cls)
        # 满层单回合（adapt=0）
        d = math_dot(st["atk"], st["matk"], max_hp, 5, base0, 0.0, k)
        # 30回合全集（近似：满层×5层衰减的三角和 ≈ 满层回×15）
        cum = int(d/max_hp*100)
        print(f"{lv:<4}{k:<8}{d:<14}{cum:<18.1f}")
