# -*- coding: utf-8 -*-
"""v178 E4 重构验证：dot 是 actor 通用能力（玩家/怪同一入口 _apply_dot/_tick_dots_of）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import conftest  # noqa: F401
except Exception:
    pass

from game import battle as BT

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  ✅ {name}")
    else:
        FAIL += 1; print(f"  ❌ {name} {detail}")

def mk_player():
    return {"class_name": "cls_zhan_shi", "level": 40, "name": "测试", "hp": 9999, "max_hp": 9999,
            "mp": 500, "max_mp": 500, "attributes": {}, "equipment": {}, "class_tier": 0,
            "learned_skills": [], "resources": {}, "buffs": {}, "def": 50, "mdef": 50, "spd": 10,
            "level": 40}

def mk_mon(atk=200, matk=180):
    return {"name": "测试Boss", "hp": 8000, "max_hp": 8000, "def": 60, "mdef": 60,
            "atk": atk, "matk": matk, "spd": 10, "lv": 40, "id": "m_test",
            "buffs": {}, "resources": {}, "stacks": {}, "charging": None,
            "skills": ["ms_ai_hao"]}

print("== E4 actor 通用重构验证 ==")

# 1. 同一个 _apply_dot 给玩家挂（怪打玩家）
player = mk_player()
mon = mk_mon(atk=300, matk=0)
b = BT.Battle("monster", mon)
b.player = player
logs = []
b._apply_dot(player, mon, {"type": "poison", "n": 2}, logs)
deb_p = player.get("debuffs") or {}
check("通用 _apply_dot 给玩家挂毒", deb_p.get("poison", {}).get("n") == 2, str(deb_p))
check("强度快照=怪的 atk", deb_p.get("poison", {}).get("atk") == 300, str(deb_p.get("poison")))
check("日志说'你'", any("你中了" in l for l in logs), str(logs))

# 2. 同一个 _apply_dot 给怪挂（玩家毒技打怪——source=玩家）
player2 = mk_player()
mon2 = mk_mon()
b2 = BT.Battle("monster", mon2)
b2.player = player2
logs2 = []
b2._apply_dot(mon2, player2, {"type": "burn", "n": 1}, logs2)
deb_m = mon2.get("debuffs") or {}
check("通用 _apply_dot 给怪挂灼烧", deb_m.get("burn", {}).get("n") == 1, str(deb_m))
check("日志说怪物名", any("测试Boss" in l for l in logs2), str(logs2))

# 3. _tick_dots_of 结算玩家（扣血走 _damage_actor）
player3 = mk_player()
mon3 = mk_mon(atk=100, matk=0)
b3 = BT.Battle("monster", mon3)
b3.player = player3
logs3 = []
b3._apply_dot(player3, mon3, {"type": "poison", "n": 1}, logs3)
hp_before = player3["hp"]
b3._tick_dots_of(player3, logs3)
check("通用结算玩家 dot 扣血", player3["hp"] < hp_before, f"{hp_before}→{player3['hp']}")

# 4. _tick_dots_of 结算怪（同样入口也能结算怪身上的毒——玩家毒怪）
player4 = mk_player()
mon4 = mk_mon()
mon4["hp"] = 8000
b4 = BT.Battle("monster", mon4)
b4.player = player4
logs4 = []
# 先给怪挂上毒（玩家面板 100 atk）
player4["atk"] = 200
b4._apply_dot(mon4, player4, {"type": "poison", "n": 1}, logs4)
hp_before4 = mon4["hp"]
b4._tick_dots_of(mon4, logs4)
check("通用结算怪 dot 扣血", mon4["hp"] < hp_before4, f"{hp_before4}→{mon4['hp']}")

# 5. 无 debuffs 的 actor → 零操作不崩
player5 = mk_player()
b5 = BT.Battle("monster", mk_mon())
b5.player = player5
logs5 = []
b5._tick_dots_of(player5, logs5)
check("空 actor 不崩", player5["hp"] == 9999)

# 6. 反向：_tick_dots（旧，结算 enemy）与 _tick_dots_of 都能结算怪——不冲突
player6 = mk_player()
mon6 = mk_mon()
mon6["hp"] = 8000
b6 = BT.Battle("monster", mon6)
b6.player = player6
player6["atk"] = 200
b6._apply_dot(mon6, player6, {"type": "poison", "n": 1}, [])
# 旧 _tick_dots 走玩家面板结算怪毒（原有行为）
logs6 = []
b6._tick_dots(player6, logs6)
check("旧 _tick_dots 仍结算怪毒", mon6["hp"] < 8000, f"hp={mon6['hp']}")

# 7. 兼容壳还能调（旧代码不崩）
b7 = BT.Battle("monster", mk_mon())
b7.player = mk_player()
logs7 = []
b7._apply_player_dot(b7.player, mk_mon(atk=50), {"type": "burn", "n": 1}, logs7)
check("兼容壳 _apply_player_dot 可用", (b7.player.get("debuffs") or {}).get("burn", {}).get("n") == 1)
logs7b = []
b7._tick_player_dots(b7.player, logs7b)
check("兼容壳 _tick_player_dots 可用", len(logs7b) >= 0)

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
