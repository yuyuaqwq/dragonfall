# -*- coding: utf-8 -*-
"""模拟4：普通怪验证——新手期（1-3级）打普通怪不应劝退"""
import sys, random, statistics
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
random.seed(42)

from game import content as C
from game import engine as E
from game.core.stats import monster_stats
from game.battle import Battle

def make_player(lv, attributes):
    return {
        "qq_id": "test", "class_name": "cls_zhan_shi", "level": lv,
        "attributes": attributes, "equipment": {},
        "learned_skills": ["sk_meng_ji"] if lv >= 2 else [],
        "skill_levels": {"sk_meng_ji": min(2, lv)} if lv >= 2 else {},
        "hp": 9999, "mp": 9999, "class_tier": 0, "evolve_path": 0,
    }

def make_enemy(lv, role):
    st = monster_stats(lv, role)
    return {"name": role, "role": role,
            "hp": st["hp"], "max_hp": st["hp"], "atk": st["atk"], "def": st["def"],
            "matk": st["matk"], "mdef": st["mdef"], "spd": st["spd"],
            "skills": [], }

def run_battle(player, enemy, rounds=500):
    wins = 0; dmg_taken = []
    for _ in range(rounds):
        b = Battle("monster", dict(enemy))
        p = dict(player)
        st = E.player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
        p["max_hp"] = st["max_hp"]; p["max_mp"] = st["max_mp"]; p["hp"] = st["max_hp"]; p["mp"] = st["max_mp"]
        while True:
            if p["mp"] >= 6 and p.get("learned_skills"):
                logs, done = b.player_turn("skill", "猛击", p)
            else:
                logs, done = b.player_turn("attack", None, p)
            if done: break
        if b.result == "victory":
            wins += 1; dmg_taken.append(st["max_hp"] - p["hp"])
    return wins / rounds, (statistics.mean(dmg_taken) if dmg_taken else 0)

# 新手场景：1-3 级全力量 vs 同级/高1级 普通怪
scenarios = [
    ("1级战士(初始9点str9)", 1, {"str": 9, "agi": 0, "int": 0, "vit": 0}, 1, "dps"),
    ("1级战士 vs 2级怪",     1, {"str": 9, "agi": 0, "int": 0, "vit": 0}, 2, "dps"),
    ("2级战士 vs 2级怪",     2, {"str": 12, "agi": 0, "int": 0, "vit": 0}, 2, "dps"),
    ("2级战士 vs 3级怪",     2, {"str": 12, "agi": 0, "int": 0, "vit": 0}, 3, "dps"),
    ("3级战士 vs 3级怪",     3, {"str": 15, "agi": 0, "int": 0, "vit": 0}, 3, "dps"),
    ("2级战士 vs 3级坦克",   2, {"str": 12, "agi": 0, "int": 0, "vit": 0}, 3, "tank"),
]

print("新手期普通怪验证（速度机制+精英上调后，普通怪未动）")
print("="*80)
for name, plv, attrs, mlv, role in scenarios:
    p = make_player(plv, attrs)
    en = make_enemy(mlv, role)
    wr, dt = run_battle(p, en)
    st = E.player_final_stats(p["class_name"], plv, {}, 0, attrs)
    flag = "😴轻松" if wr == 1 and dt < st["max_hp"] * 0.4 else ("⚠️有压力" if wr == 1 else "❌打不过")
    print(f"  {name}: 胜率{wr*100:.0f}% 掉血{round(dt,0)}/{st['max_hp']} ({dt/st['max_hp']*100:.0f}%) {flag}")
