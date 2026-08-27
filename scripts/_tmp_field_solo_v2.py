# -*- coding: utf-8 -*-
"""野外 Boss 单刷化标定 v2（鱼鱼：野外不该不能单人过）：降分档 + 战士/牧师双判定。"""
import os, sys
_PD = os.getcwd()
sys.path.insert(0, os.path.join(_PD, "tests")); sys.path.insert(0, os.path.join(_PD, "scripts"))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PD, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env
from numeric_lib.player import PlayerOptions, build_player, per_action_dmg
from numeric_lib.gear import gear_loadout
from numeric_lib.constants import TEAM_BUFF
from data.plugins.dragonfall.game import content as C

NEW_MULT = ((30, 2.7), (60, 1.5), (999, 1.1))  # 候选：单刷 40~60 轮窗口

def field_mult(lv):
    for cap, m in NEW_MULT:
        if lv <= cap:
            return m
    return NEW_MULT[-1][1]

def scan_field_bosses():
    found = []
    for _, sub in getattr(C, "SUBAREAS", {}).items():
        items = sub.values() if isinstance(sub, dict) else sub
        for it in items:
            if not isinstance(it, dict):
                continue
            b = it.get("boss")
            if isinstance(b, (list, tuple)) and len(b) >= 4 and b[2] == "boss":
                found.append(b)
    return found

def boss_stats(b):
    mid, name, role, lv = b[0], b[1], b[2], b[3]
    m = C.monster_stats(lv, "boss")
    mod = C.MONSTER_MODS.get(mid, {})
    if mod and mod.get("hp_mult"):
        m["hp"] = int(m["hp"] * mod["hp_mult"])
    hp = int(m["hp"] * field_mult(lv))
    return hp, m  # atk 从 m 取

def solo_check(lv, hp, m):
    gear = gear_loadout(lv, "team_mid")
    edef = m["def"]
    # 战士：输出窗口 & 硬抗存活
    d_w = per_action_dmg("cls_zhan_shi", lv, gear, edef, 0, PlayerOptions(), potion_on=True)
    p_w = build_player("cls_zhan_shi", lv, gear, PlayerOptions())
    rounds_w = hp / max(d_w, 1.0)
    boss_dmg = m["atk"] * 1.35 / (1 + p_w["def"] / 50.0)
    surv_w = p_w["hp"] / max(boss_dmg, 1.0)
    # 牧师：输出低但有自奶（治愈 200% × 50% 轮次）
    d_p = per_action_dmg("cls_mu_shi", lv, gear, edef, 0, PlayerOptions(), potion_on=True)
    p_p = build_player("cls_mu_shi", lv, gear, PlayerOptions())
    rounds_p = hp / max(d_p, 1.0)
    heal = p_p.get("matk", 0) * 2.0 * 0.5
    net = max(boss_dmg - heal, boss_dmg * 0.2)
    surv_p = p_p["hp"] / max(net, 1.0)
    r4 = hp / max(d_w * 4 * TEAM_BUFF, 1.0)
    return rounds_w, surv_w, rounds_p, surv_p, r4

ok = fail = 0
print(f"{'Boss':<13}{'Lv':>4}{'hp':>9}{'m':>5}{'战士轮':>6}{'硬抗':>5}{'牧师轮':>6}{'牧存':>5}{'4人':>5}  判定")
for b in sorted(scan_field_bosses(), key=lambda x: x[3]):
    hp, m = boss_stats(b)
    rw, sw, rp, sp, r4 = solo_check(b[3], hp, m)
    tag = "✅战士可单刷" if sw >= rw * 0.9 else ("🟡牧师可单刷" if sp >= rp * 0.9 else "💀仍不可单刷")
    if tag.startswith("💀"):
        fail += 1
    else:
        ok += 1
    print(f"{b[1]:<13}{b[3]:>4}{hp:>9}{field_mult(b[3]):>5}{rw:>6.0f}{sw:>5.0f}{rp:>6.0f}{sp:>5.0f}{r4:>5.0f}  {tag}")
print(f"\n可单刷 {ok}/24，仍不可 {fail}/24")