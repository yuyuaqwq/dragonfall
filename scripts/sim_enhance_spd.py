# -*- coding: utf-8 -*-
"""模拟2：2级战士 vs 4级精英——带装备强化 + 速度机制分析"""
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

def make_enemy(lv=4, elite_mult=1.0):
    st = monster_stats(lv, "elite")
    hp = int(st["hp"] * elite_mult)
    return {"name": "山贼头目", "role": "elite",
            "hp": hp, "max_hp": hp, "atk": int(st["atk"] * (1 + (elite_mult-1)*0.5)), "def": st["def"],
            "matk": st["matk"], "mdef": st["mdef"], "spd": st["spd"],
            "skills": ["ms_pi_kan", "ms_nu_hou"]}

def equip_set(lv, quality, enhance=0):
    eq = {}
    names = {"weapon": "铁剑", "helm": "皮帽", "armor": "皮甲", "legs": "皮裤", "boots": "皮靴", "ring": "铜戒", "necklace": "骨链"}
    for slot in ("weapon", "helm", "armor", "legs", "boots", "ring", "necklace"):
        eq[slot] = {"name": names[slot], "stats": equip_stats(slot, lv, quality), "enhance": enhance}
    return eq

def run_battle(player, rounds=400, elite_mult=1.0):
    wins = 0; rnds = []; dmg_taken = []
    for _ in range(rounds):
        b = Battle("monster", make_enemy(4, elite_mult))
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

print("="*90)
print("【一】装备强化对玩家属性的影响（str12 全力量）")
print("="*90)
for enh in (0, 3, 5, 7, 9):
    p = make_player({"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "white", enh))
    st = player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
    print(f"  白装强化+{enh}: {fmt(st)}")
print()

print("="*90)
print("【二】不同强化 vs 4级精英（现 221血/30攻）")
print("="*90)
for enh in (0, 3, 5):
    p = make_player({"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "white", enh))
    st = player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
    wr, rnd, dt = run_battle(p)
    print(f"  强化+{enh}: {fmt(st)} → 胜率{wr*100:.0f}% 平均{round(rnd,1)}回合 掉血{round(dt,0)}/{st['max_hp']} ({dt/st['max_hp']*100:.0f}%)")
print()

print("="*90)
print("【三】如果怪物也强化（血量×倍数）——多强才让裸奔玩家有压力")
print("="*90)
for mult in (1.0, 1.3, 1.6, 2.0):
    # 裸奔 str12
    p = make_player({"str": 12, "agi": 0, "int": 0, "vit": 0}, {})
    st = player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
    wr, rnd, dt = run_battle(p, elite_mult=mult)
    en = make_enemy(4, mult)
    print(f"  精英血量×{mult} ({en['hp']}血/{en['atk']}攻): 裸奔 → 胜率{wr*100:.0f}% 掉血{round(dt,0)}/{st['max_hp']} ({dt/st['max_hp']*100:.0f}%)")

print()
print("="*90)
print("【四】速度机制现状")
print("="*90)
print("  battle.py 里 spd 的用途：仅 buff 计算（spd_up/spd_down），从不参与行动顺序")
print("  战斗流程：actor_turn 永远是玩家先打 → _enemy_turn 敌人后打")
print("  结论：速度对先手/多动 0 影响 —— 裸奔玩家也永远先手，精英 spd15 也无优势")
