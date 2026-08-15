# -*- coding: utf-8 -*-
"""DOT 数值平衡审计——副本团队回合模型 v2（忠实还原批次结算/叠层累积）
核心：副本每完整团队回合结算一次 dot（dot_pending 闸门）。玩家动作在回合内非同步。
叠层 = 每回合叠层技能施放（淬毒+1/藤蔓+2/毒爆2件套+3/poison_all 团队+2）。
策略：
  maintain 无脑：每个团队回合叠满到 5 层，adapt 爬满 20%
  tempo 节奏：叠满后停 1~2 团队回合（让 adapt 回落到 8-12%），再叠满
"""
import sys, os, random
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import engine as E
from game.core import stats as S

def player_stats(lv, cls, boost=1.0):
    eq = {s: {"stats": S.equip_stats(s, lv, "blue")} for s in
          ("weapon", "armor", "ring", "helm", "legs", "necklace", "boots")}
    attrs = {"str": 2*(lv-1), "vit": 1*(lv-1), "int": 0, "agi": 0}
    st = E.player_final_stats(cls, lv, eq, tier=1, attributes=attrs,
                              evolve_path=0, title_bonus={}, race="human")
    st["atk"] = int(st["atk"]*boost); st["matk"] = int(st["matk"]*boost)
    return st

def mon(lv, role):
    return S.monster_stats(lv, role)

LV = [30, 60, 90]
CLASS = {"poison": "cls_wild_hunter", "burn": "cls_fa_shi", "bleed": "cls_wild_hunter"}

def math_dot(atk, matk, max_hp, n, base_res, adapt, k, bleed_flat=1.0,
             elem_res=0, phys_reduce=0, magic_reduce=0, hp_ratio=1.0):
    res = min(0.95, (base_res or 0)+adapt)
    hp_p = {"poison":0.015,"burn":0.010,"bleed":0.015}[k]
    atk_p = {"poison":0.5,"burn":0.0,"bleed":0.6}[k]
    matk_p = {"poison":0.0,"burn":0.4,"bleed":0.0}[k]
    p = (atk*atk_p + matk*matk_p + max_hp*hp_p) * n * (1-res)
    # 放血：bleed 目标 hp<30% → ×2
    if k == "bleed" and hp_ratio < 0.30:
        p *= 2.0
    if k == "burn":
        p *= (1 - min(elem_res,0.5)); p *= (1 - min(magic_reduce,0.4))
    elif k == "poison":
        p *= (1 - min(magic_reduce,0.4))
    else:
        p *= (1 - min(phys_reduce,0.4))
    return max(0, int(p))

STACK_VAL = {"poison": 2, "burn": 2}  # 默认每回合叠层技能 +2（藤蔓+2/火系+2）
STACK_VAL_HI = {"poison": 3, "burn": 3}  # 高叠（双毒刃+3）

def sim_instance(lv, cls, k, strat, stack_val=None, turns=30):
    """副本团队回合模型：
    每回合: (1) 若策略叠层 → n=min(5,n+sv), adapt+0.04;  (2) 结算 dot(所有层一次性),n-1; (3) adapt回落.
    返回 (dot伤害序列, adapt序列, 层数序列)"""
    sv = (stack_val or STACK_VAL[k])
    st = player_stats(lv, cls)
    m = mon(lv, "boss")
    max_hp = m["hp"]; base_res = m.get("dot_res", 0.9)
    n = 0; adapt = 0.0; last_round = -99
    dot_log = []; adapt_log = []; n_log = []
    hp_left = max_hp
    for r in range(1, turns+1):
        # 1) 叠层决定（先叠后结算，近似团队回合组织）
        if strat == 'maintain':
            if n < 5:
                n = min(5, n + sv); adapt = min(0.20, adapt + 0.04); last_round = r
        elif strat == 'tempo':
            # 节奏：叠2回合停1回合
            pass
        # 2) 结算
        dmg = math_dot(st["atk"], st["matk"], max_hp, n, base_res, adapt, k,
                       hp_ratio=hp_left/max_hp)
        dot_log.append(dmg); adapt_log.append(adapt); n_log.append(n)
        hp_left -= dmg
        # 结算后 n-1，adapt 回落
        if n > 0:
            if (r - last_round) >= 2 and adapt > 0:
                adapt = max(0.0, adapt - 0.04)
            n -= 1
        if hp_left <= 0:
            break
    return dot_log, adapt_log, n_log

def sim_instance_tempo(lv, cls, k, continue_r, pause_r, stack_val=None, turns=30):
    sv = (stack_val or STACK_VAL[k])
    st = player_stats(lv, cls)
    m = mon(lv, "boss")
    max_hp = m["hp"]; base_res = m.get("dot_res", 0.9)
    n = 0; adapt = 0.0; last_round = -99
    dot_log = []; adapt_log = []; n_log = []
    hp_left = max_hp
    s_cnt = 0; p_cnt = 0
    for r in range(1, turns+1):
        if s_cnt < continue_r:
            n = min(5, n + sv); adapt = min(0.20, adapt + 0.04); last_round = r
            s_cnt += 1; p_cnt = 0
        else:
            p_cnt += 1
            if p_cnt >= pause_r:
                s_cnt = 0
        dmg = math_dot(st["atk"], st["matk"], max_hp, n, base_res, adapt, k,
                       hp_ratio=hp_left/max_hp)
        dot_log.append(dmg); adapt_log.append(adapt); n_log.append(n)
        hp_left -= dmg
        if n > 0:
            if (r - last_round) >= 2 and adapt > 0:
                adapt = max(0.0, adapt - 0.04)
            n -= 1
        if hp_left <= 0:
            break
    return dot_log, adapt_log, n_log

print("========== 场景 B(副本模型)：适应机制对无脑每回合叠毒 vs 节奏的抑制 ==========")
for lv in LV:
    cls = CLASS["poison"]
    max_hp = mon(lv,"boss")["hp"]
    mnt_d, mnt_a, mnt_n = sim_instance(lv, cls, "poison", 'maintain', turns=20)
    tmp_d, tmp_a, tmp_n = sim_instance_tempo(lv, cls, "poison", 2, 1, turns=20)
    mt, tt = sum(mnt_d), sum(tmp_d)
    print(f"Lv{lv}: 无脑叠满 dot累计={mt} ({mt/max_hp*100:.1f}%Boss, 末adapt={mnt_a[-1]:.2f}, 末层={mnt_n[-1]})")
    print(f"       节奏叠2停1 dot累计={tt} ({tt/max_hp*100:.1f}%Boss, 末adapt={tmp_a[-1]:.2f}, 末层={tmp_n[-1]})")
    ratio = mt/tt if tt else 0
    print(f"       → 无脑/节奏={ratio:.2f}  {'(无脑更差，适应生效)' if ratio<1 else '(无脑等同/更优，适应未抑制)'}")

print("\n========== 场景 B2：adapt 爬升曲线（连续叠毒 N 次后 dot 衰减倍数）==========")
for lv in LV:
    cls = CLASS["poison"]
    st = player_stats(lv, cls); max_hp = mon(lv,"boss")["hp"]
    d0 = math_dot(st["atk"], st["matk"], max_hp, 5, 0.9, 0.0, "poison")
    print(f"Lv{lv}: adapt=0 → 满层dot/回合={d0}")
    for ad in (0.04, 0.08, 0.12, 0.16, 0.20):
        d = math_dot(st["atk"], st["matk"], max_hp, 5, 0.9, ad, "poison")
        print(f"      adapt+{int(ad*100)}% → {d} (满层×{d/d0:.2f})")

print("\n========== 场景 B3：单机(每玩家动作结算) vs 副本(每团队回合结算) 差异 ==========")
print("(单机 mode 下 keep-full 很难维持——见说明, 此处只列副本主战场)")
