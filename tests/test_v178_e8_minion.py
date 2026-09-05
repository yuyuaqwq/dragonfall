# -*- coding: utf-8 -*-
"""v178 E8 验证：minion 计数 API + 爪牙死亡回调"""
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

def mk_boss(extra=None):
    m = {"name": "机关Boss", "hp": 8000, "max_hp": 8000, "def": 60, "mdef": 60,
         "atk": 100, "matk": 80, "spd": 10, "lv": 40, "id": "b_test",
         "buffs": {}, "resources": {}, "stacks": {}, "charging": None, "is_boss": True,
         "skills": ["ms_ai_hao"], "mech": "phase"}
    if extra:
        m.update(extra)
    return m

def mk_minion(name="爪牙1"):
    return {"name": name, "hp": 500, "max_hp": 500, "def": 10, "mdef": 10,
            "atk": 10, "matk": 10, "spd": 5, "lv": 20, "id": "m_minion",
            "buffs": {}, "resources": {}, "stacks": {}, "charging": None,
            "is_minion": True, "is_boss": False, "rank": 1, "reach": 1,
            "skills": [], "mech": "", "uid": "e_minion1"}

print("== E8 minion 计数 + 死亡回调验证 ==")

# 1. _minion_count 计数
boss = mk_boss()
minion1 = mk_minion("机关A")
minion2 = mk_minion("机关B")
b = BT.Battle("instance", boss, enemies=[boss, minion1, minion2])
b.player = mk_player()
check("存活 2 minion 计数", b._minion_count() == 2, f"n={b._minion_count()}")

# 2. 死亡一个后计数降
minion1["hp"] = 0
check("死亡后计数 1", b._minion_count() == 1, f"n={b._minion_count()}")

# 3. _remove_unit 触发死亡回调记账
minion3 = mk_minion("机关C")
b.enemies.append(minion3)
b._remove_unit("enemy", minion3)
check("Boss 死亡计数 +1", boss.get("_minion_died_count") == 1, str(boss.get("_minion_died_count")))
check("Boss 死亡瞬态标记", boss.get("_minion_died_this_act") is True)

# 4. on_minion_died.stacks_clear（轰鸣碎晶核放能：清层）
boss2 = mk_boss({"on_minion_died": {"effect": "stacks_clear"},
                 "stacks": {"charge": 4}, "mech_stacks_n": 4})
boss2["_minion_died_this_act"] = True
logs = []
ret = b._on_minion_died_tick(boss2, logs)
check("stacks_clear 触发", ret, str(logs))
check("stacks 清空", not (boss2.get("stacks") or {}), str(boss2.get("stacks")))

# 5. on_minion_died.shield（月神守卫机关被击后自保）
boss3 = mk_boss({"on_minion_died": {"effect": "shield"}})
boss3["_minion_died_this_act"] = True
logs5 = []
b._on_minion_died_tick(boss3, logs5)
shd = boss3.get("shields") or {}
check("shield 触发", shd.get("on_minion", {}).get("value", 0) > 0, str(shd))

# 6. on_minion_died.heal_pct（奥姆吸魂）
boss4 = mk_boss({"on_minion_died": {"effect": "heal_pct", "value": 0.1}})
boss4["hp"] = 4000
boss4["_minion_died_this_act"] = True
logs6 = []
b._on_minion_died_tick(boss4, logs6)
check("heal_pct 回血 10%", boss4["hp"] == 4800, f"hp={boss4['hp']}")

# 7. on_minion_died.atk_up（赫尔加吃怪）
boss5 = mk_boss({"on_minion_died": {"effect": "atk_up", "value": 3}})
boss5["_minion_died_this_act"] = True
logs7 = []
b._on_minion_died_tick(boss5, logs7)
check("atk_up buff 写入", (boss5.get("buffs") or {}).get("mon_atk_up") == 3, str(boss5.get("buffs")))

# 8. 无标记不触发（瞬态消费）
boss6 = mk_boss({"on_minion_died": {"effect": "shield"}})
logs8 = []
ret8 = b._on_minion_died_tick(boss6, logs8)
check("无死亡标记不触发", not ret8 and not (boss6.get("shields") or {}))

# 9. 无 on_minion_died 配置的 Boss 死亡爪牙不报错
boss7 = mk_boss()
minion7 = mk_minion("爪牙X")
b7 = BT.Battle("instance", boss7, enemies=[boss7, minion7])
b7.player = mk_player()
b7._remove_unit("enemy", minion7)
check("无配置 Boss 正常", boss7.get("_minion_died_count") == 1)

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
