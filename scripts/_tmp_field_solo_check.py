# -*- coding: utf-8 -*-
"""野外 Boss 单人可过性评估：当前落地分档（15/9/6.2）下单刷 vs 4人组队轮数。"""
import os, sys
_PD = os.getcwd()
sys.path.insert(0, os.path.join(_PD, "tests")); sys.path.insert(0, os.path.join(_PD, "scripts"))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PD, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env
from numeric_lib.player import PlayerOptions, build_player, per_action_dmg
from numeric_lib.gear import gear_loadout
from numeric_lib.constants import CLASSES, TEAM_BUFF
from data.plugins.dragonfall.game import content as C

FIELD_TIER_MULT = C.FIELD_TIER_MULT["boss"]

def field_mult(lv):
    for cap, m in FIELD_TIER_MULT:
        if lv <= cap:
            return m
    return FIELD_TIER_MULT[-1][1]

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

def boss_hp(b):
    mid, name, role, lv = b[0], b[1], b[2], b[3]
    m = C.monster_stats(lv, "boss")
    mod = C.MONSTER_MODS.get(mid, {})
    if mod and mod.get("hp_mult"):
        m["hp"] = int(m["hp"] * mod["hp_mult"])
    return int(m["hp"] * field_mult(lv))

def rounds_and_survive(lv, hp, atk, n_players):
    """返回 (轮数, 承伤回合)。承伤按战士面板 HP/单发期望（与 team_matrix 同口径）。"""
    gear = gear_loadout(lv, "team_mid")
    p = build_player("cls_zhan_shi", lv, gear, PlayerOptions())
    d = per_action_dmg("cls_zhan_shi", lv, gear, atk, 0, PlayerOptions(), potion_on=True)
    edef = C.monster_stats(lv, "boss")["def"]
    dmg = per_action_dmg("cls_zhan_shi", lv, gear, edef, 0, PlayerOptions(), potion_on=True)
    rounds = hp / max(dmg * n_players * TEAM_BUFF, 1.0)
    # 承伤：Boss 单发期望（enraged×1.35 保守）
    boss_atk_dmg = atk * 1.35 / (1 + p["def"] / 50.0)  # 近似单发期望
    survive = p["hp"] / max(boss_atk_dmg, 1.0)
    return rounds, survive, dmg, p["hp"]

print(f"{'Boss':<14}{'Lv':>4}{'hp':>8}{'mult':>6}{'单刷轮':>7}{'4人轮':>7}{'承伤':>6}  判定")
for b in sorted(scan_field_bosses(), key=lambda x: x[3]):
    hp = boss_hp(b)
    atk = int(C.monster_stats(b[3], "boss")["atk"])
    r1, surv, dmg, php = rounds_and_survive(b[3], hp, atk, 1)
    r4 = hp / max(dmg * 4 * TEAM_BUFF, 1.0)
    flag = "✅单刷可过" if (r1 <= 80 and surv > r1) else ("💀单刷送死" if surv < r1 else "⏱超80轮")
    print(f"{b[1]:<14}{b[3]:>4}{hp:>8}{field_mult(b[3]):>6}{r1:>7.0f}{r4:>7.0f}{surv:>6.0f}  {flag}")