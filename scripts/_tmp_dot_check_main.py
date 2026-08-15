# -*- coding: utf-8 -*-
"""主 agent 集成验证：battle.py v1.1（混合公式/毒蚀/放血/标记按层）+ v1.2（总抗/适应回落）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

def make_player(atk=100, matk=80):
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": {}, "skills": [], "skill_levels": {}, "learned_skills": []}

def enemy(**kw):
    e = {"name": "靶子", "lv": 10, "hp": 100000, "max_hp": 100000,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}}
    e.update(kw)
    return e

def tick(b, player):
    # 固定施放者属性快照（避免 _player_stats 对不完整测试玩家的职业兜底）
    b._player_stats = lambda pl: {"atk": 100, "matk": 80, "def": 50, "mdef": 50,
                                  "spd": 10, "crit": 0.05, "max_hp": 9999, "max_mp": 999}
    b._dot_pending = True
    logs = []
    b._tick_dots(player, logs)
    return logs

print("【v1.1 混合公式：毒 1 层首 tick = atk×0.5 + max_hp×1.5%】")
p = make_player(atk=100)
e = enemy(max_hp=1000, hp=1000)
b = BT.Battle("monster", e)
b.mech_stacks = {}
b.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0}
logs = tick(b, p)
dmg = 1000 - b.enemy["hp"]
check("毒 1 层 = int(50+15) = 65", dmg == 65, f"dmg={dmg} logs={logs}")
check("结算后剩 0 层（消散）", "poison" not in b.enemy.get("debuffs", {}), str(b.enemy.get("debuffs")))

print("【v1.2 总抗：dot_res=0.9 + adapt=0.2 → res=0.95】")
e2 = enemy(max_hp=1000, hp=1000, dot_res=0.9, adapt={"poison": 0.2})
b2 = BT.Battle("monster", e2)
b2.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0}
logs = tick(b2, p)
dmg2 = 1000 - b2.enemy["hp"]
check("毒 1 层 ×(1-0.95) = int(65*0.05) = 3", dmg2 == 3, f"dmg={dmg2}")

print("【v1.1 放血：bleed 且 hp<30% → ×2】")
e3 = enemy(max_hp=1000, hp=200)
b3 = BT.Battle("monster", e3)
b3.enemy.setdefault("debuffs", {})["bleed"] = {"n": 1, "mult": 1.0}
logs = tick(b3, p)
dmg3 = 200 - b3.enemy["hp"]
# bleed = atk×0.6 + max_hp×1.5% = 60+15 = 75；hp=200 < 300 → ×2 = 150
check("放血 75×2 = 150", dmg3 == 150, f"dmg={dmg3} logs={logs}")
check("放血日志标注", any("放血" in l for l in logs), str(logs))

print("【v1.2 适应回落：last_round 距今≥2 → adapt -0.04】")
e4 = enemy(max_hp=100000, hp=100000, adapt={"poison": 0.12})
b4 = BT.Battle("monster", e4)
b4.round = 5
b4.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0, "last_round": 2}
tick(b4, p)
check("adapt 0.12 → 0.08", abs(b4.enemy["adapt"]["poison"] - 0.08) < 1e-9, str(b4.enemy["adapt"]))

print("【v1.1 毒蚀：5 层毒 → _enemy_stats def/mdef -20%】")
e5 = enemy(**{"def": 1000, "mdef": 800})
b5 = BT.Battle("monster", e5)
b5.enemy.setdefault("debuffs", {})["poison"] = {"n": 5, "mult": 1.0}
est = b5._enemy_stats()
check("def 1000×0.8 = 800", est["def"] == 800, str(est["def"]))
check("mdef 800×0.8 = 640", est["mdef"] == 640, str(est["mdef"]))
b5.enemy["debuffs"]["poison"]["n"] = 2
est2 = b5._enemy_stats()
check("2 层毒 -8%：def 920", est2["def"] == 920, str(est2["def"]))

print("【v1.1 标记按层：_apply_mark 5 层 = +100%】")
e6 = enemy()
b6 = BT.Battle("monster", e6)
b6.enemy.setdefault("debuffs", {})["mark"] = {"n": 5, "mult": 1.0}
check("_apply_mark(100) = 200", b6._apply_mark(100) == 200, str(b6._apply_mark(100)))
b6.enemy["debuffs"]["mark"]["n"] = 1
check("_apply_mark(100) = 120", b6._apply_mark(100) == 120, str(b6._apply_mark(100)))
b6.enemy["debuffs"].pop("mark", None)
check("无标记 = 原伤害", b6._apply_mark(100) == 100, str(b6._apply_mark(100)))

print("【护盾对 dot 生效：shield boss 毒伤减半】")
e7 = enemy(max_hp=1000, hp=1000, mech="shield", boss_shield=500)
b7 = BT.Battle("monster", e7)
b7.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0}
logs = tick(b7, p)
dmg7 = 1000 - b7.enemy["hp"]
# 65 减半 → int(65*0.5)=32，护盾吸收 32
check("毒 65 → 护盾减半 32", dmg7 == 32, f"dmg={dmg7} logs={logs} boss_shield={b7.enemy.get('boss_shield')}")
check("护盾被吸收", abs(b7.enemy.get("boss_shield", 0) - 468) <= 1, f"shield={b7.enemy.get('boss_shield')}")

print("【衰减：5 层毒 5 回合总伤（无抗性）】")
e8 = enemy(max_hp=1000, hp=1000)
b8 = BT.Battle("monster", e8)
b8.enemy.setdefault("debuffs", {})["poison"] = {"n": 5, "mult": 1.0}
total = 0
for r in range(6):
    total += 1000 - b8.enemy["hp"]
    if b8._enemy_dead():
        break
    b8.enemy["hp"] = 1000  # 重置模拟（伤害累积用），保留 debuffs 衰减
    tick(b8, p)
# 每层 65：5+4+3+2+1 = 15 层回合 → 975；但第 6 回合已无层
check("5 回合总伤 = 65×15 = 975", total == 975, f"total={total}")

print(f"\n结果: {passed} 通过, 0 失败")
