# -*- coding: utf-8 -*-
"""复现 Bug A：装备后属性变化显示（无变化）"""
import sys
sys.path.insert(0, r"C:/Users/yuyu/qqbot/data/plugins/dragonfall")
from game import engine as E
from game import content as C

# 模拟小蓝：游侠 Lv.4，无武器（weapon=None），装备猎弓
player = {
    "class_name": "cls_you_xia",
    "level": 4,
    "equipment": {},  # 无武器
    "class_tier": 0,
    "attributes": {"str": 0, "agi": 5, "int": 0, "vit": 0},
    "evolve_path": 0,
    "race": "human",
}

# 猎弓（白装 lv2）
bow = C.generate_roster_equip("eq_lie_gong")
print("猎弓 stats:", bow.get("stats"), "req:", bow.get("req"))

old = E.player_final_stats(player["class_name"], player["level"], player["equipment"],
                           player["class_tier"], player["attributes"], player["evolve_path"], None, player["race"])
eq2 = dict(player["equipment"])
eq2["weapon"] = bow
new = E.player_final_stats(player["class_name"], player["level"], eq2,
                           player["class_tier"], player["attributes"], player["evolve_path"], None, player["race"])

print(f"old atk={old['atk']}  new atk={new['atk']}  diff={new['atk']-old['atk']}")
for k, label in [("atk","攻击"),("def","防御"),("matk","魔攻"),("mdef","魔防"),("spd","速度"),("max_hp","生命"),("max_mp","魔力"),("crit","暴击"),("dodge","闪避")]:
    d = new[k] - old[k]
    if abs(d) >= 1e-9:
        print(f"  diff {label}: {d}")
