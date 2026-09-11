# -*- coding: utf-8 -*-
"""模拟：2级战士 vs 4级精英（山贼头目）——带加点+装备"""
import sys, random, statistics
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
random.seed(42)

from game import content as C
from game.content_rules.panel import player_final_stats
from game.core.stats import monster_stats, equip_stats
from game.battle import Battle

def make_player(attributes, equipment, skill_levels=None):
    return {
        "qq_id": "test",
        "class_name": "cls_zhan_shi",
        "level": 2,
        "attributes": attributes,
        "equipment": equipment,
        "learned_skills": ["sk_meng_ji"],
        "skill_levels": skill_levels or {"sk_meng_ji": 2},
        "hp": 9999, "mp": 9999,  # 会被战斗内修正
        "class_tier": 0,
        "evolve_path": 0,
    }

def make_enemy():
    st = monster_stats(4, "elite")
    return {
        "name": "山贼头目",
        "role": "elite",
        "hp": st["hp"], "max_hp": st["hp"],
        "atk": st["atk"], "def": st["def"],
        "matk": st["matk"], "mdef": st["mdef"],
        "spd": st["spd"],
        "skills": ["ms_pi_kan", "ms_nu_hou"],
    }

def equip_set(lv, quality):
    """一套装备：武器+头+胸+腿+靴+戒+链"""
    eq = {}
    names = {"weapon": "铁剑", "helm": "皮帽", "armor": "皮甲", "legs": "皮裤", "boots": "皮靴", "ring": "铜戒", "necklace": "骨链"}
    for slot in ("weapon", "helm", "armor", "legs", "boots", "ring", "necklace"):
        stats = equip_stats(slot, lv, quality)
        eq[slot] = {"name": names[slot], "stats": stats, "enhance": 0}
    return eq

def run_battle(player, use_skill=True, rounds=300):
    """跑多次完整战斗，返回 (胜率, 平均回合, 平均掉血)"""
    wins = 0; rnds = []; dmg_taken = []
    for _ in range(rounds):
        b = Battle("monster", make_enemy())
        p = dict(player)
        st = player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
        p["max_hp"] = st["max_hp"]; p["max_mp"] = st["max_mp"]
        p["hp"] = st["max_hp"]; p["mp"] = st["max_mp"]
        while True:
            done = False
            if use_skill and p["mp"] >= 6:
                logs, done = b.actor_turn("skill", "猛击", p)
            else:
                logs, done = b.actor_turn("attack", None, p)
            if done: break
        if b.result == "victory":
            wins += 1
            rnds.append(b.round)
            dmg_taken.append(st["max_hp"] - p["hp"])
        elif b.result == "defeat":
            pass
    return wins / rounds, (statistics.mean(rnds) if rnds else 0), (statistics.mean(dmg_taken) if dmg_taken else 0)

def fmt(s):
    return f"{s['max_hp']}血 {s['atk']}攻 {s['def']}防 {s['matk']}魔攻 {s['mdef']}魔防 {s['spd']}速 暴击{s.get('crit',0)*100:.0f}%"

# 敌方属性
en = make_enemy()
print(f"敌方 山贼头目(Lv4精英): {en['hp']}血 {en['atk']}攻 {en['def']}防 {en['matk']}魔攻 {en['mdef']}魔防 {en['spd']}速")
print("="*70)

scenarios = [
    ("A 现状(全力量str12, 裸奔)", {"str": 12, "agi": 0, "int": 0, "vit": 0}, {}, True),
    ("B 现状+白装Lv2",            {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "white"), True),
    ("C 现状+绿装Lv2",            {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "green"), True),
    ("D 现状+蓝装Lv2",            {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "blue"), True),
    ("E 均衡(str6vit6)+白装Lv2",  {"str": 6, "agi": 0, "int": 0, "vit": 6}, equip_set(2, "white"), True),
    ("F 肉装(vit12)+白装Lv2",     {"str": 0, "agi": 0, "int": 0, "vit": 12}, equip_set(2, "white"), True),
    ("G 现状+白装(普攻无技能)",   {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "white"), False),
]

for name, attrs, eq, use_skill in scenarios:
    p = make_player(attrs, eq)
    st = player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
    wr, rnd, dt = run_battle(p, use_skill)
    print(f"{name}")
    print(f"  玩家: {fmt(st)}")
    print(f"  结果: 胜率{wr*100:.0f}% | 平均{round(rnd,1)}回合 | 胜局平均掉血{round(dt,1)}")
    print("-"*70)
