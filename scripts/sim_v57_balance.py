# -*- coding: utf-8 -*-
"""模拟3：v57 后数值验证——2级战士 vs 上调后4级精英（带速度机制）"""
import sys, random, statistics
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
random.seed(42)

from game import content as C
from game.content_rules.panel import player_final_stats
from game.core.stats import monster_stats, equip_stats
from game.battle import Battle

def make_player(attributes, equipment, skill_levels=None):
    return {
        "qq_id": "test", "class_name": "cls_zhan_shi", "level": 2,
        "attributes": attributes, "equipment": equipment,
        "learned_skills": ["sk_meng_ji"],
        "skill_levels": skill_levels or {"sk_meng_ji": 2},
        "hp": 9999, "mp": 9999, "class_tier": 0, "evolve_path": 0,
    }

def make_enemy(lv=4):
    st = monster_stats(lv, "elite")
    return {"name": "山贼头目", "role": "elite",
            "hp": st["hp"], "max_hp": st["hp"], "atk": st["atk"], "def": st["def"],
            "matk": st["matk"], "mdef": st["mdef"], "spd": st["spd"],
            "skills": ["ms_pi_kan", "ms_nu_hou"]}

def equip_set(lv, quality, enhance=0):
    eq = {}
    names = {"weapon": "铁剑", "helm": "皮帽", "armor": "皮甲", "legs": "皮裤", "boots": "皮靴", "ring": "铜戒", "necklace": "骨链"}
    for slot in ("weapon", "helm", "armor", "legs", "boots", "ring", "necklace"):
        eq[slot] = {"name": names[slot], "stats": equip_stats(slot, lv, quality), "enhance": enhance}
    return eq

def run_battle(player, rounds=500):
    wins = 0; rnds = []; dmg_taken = []; first_hits = []
    for _ in range(rounds):
        b = Battle("monster", make_enemy())
        p = dict(player)
        st = player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
        p["max_hp"] = st["max_hp"]; p["max_mp"] = st["max_mp"]; p["hp"] = st["max_hp"]; p["mp"] = st["max_mp"]
        while True:
            if p["mp"] >= 6:
                logs, done = b.actor_turn("skill", "猛击", p)
            else:
                logs, done = b.actor_turn("attack", None, p)
            if done: break
        if b.result == "victory":
            wins += 1; rnds.append(b.round); dmg_taken.append(st["max_hp"] - p["hp"])
    return wins / rounds, (statistics.mean(rnds) if rnds else 0), (statistics.mean(dmg_taken) if dmg_taken else 0)

def fmt(s):
    return f"{s['max_hp']}血/{s['atk']}攻/{s['def']}防/{s['spd']}速"

en = make_enemy()
print(f"敌方 山贼头目 Lv4精英（v57上调后）: {en['hp']}血 {en['atk']}攻 {en['def']}防 spd{en['spd']}")
print("="*86)

cases = [
    ("现状(全力量str12 裸奔)",       {"str": 12, "agi": 0, "int": 0, "vit": 0}, {}, "A"),
    ("全力量str12 白装+0",           {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "white", 0), "B"),
    ("全力量str12 白装+5",           {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "white", 5), "C"),
    ("全力量str12 绿装+3",           {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "green", 3), "D"),
    ("均衡str6vit6 白装+0",          {"str": 6,  "agi": 0, "int": 0, "vit": 6}, equip_set(2, "white", 0), "E"),
    ("均衡str3vit3agi6 白装+0",      {"str": 3,  "agi": 6, "int": 0, "vit": 3}, equip_set(2, "white", 0), "F"),
]

for name, attrs, eq, tag in cases:
    p = make_player(attrs, eq)
    st = player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
    wr, rnd, dt = run_battle(p)
    pct = dt / st["max_hp"] * 100
    if wr == 0:
        flag = "❌打不过"
    elif wr == 1 and pct < 35:
        flag = "😴轻松"
    elif wr == 1 and pct < 65:
        flag = "⚠️有压力"
    else:
        flag = "🔥险胜"
    print(f"[{tag}] {name}")
    print(f"   玩家 {fmt(st)} → 胜率{wr*100:.0f}% 平均{round(rnd,1)}回合 掉血{round(dt,0)}/{st['max_hp']} ({pct:.0f}%) {flag}")
