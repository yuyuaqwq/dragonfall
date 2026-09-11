# -*- coding: utf-8 -*-
"""v178 E5 验证：元素免疫/弱点表（怪物 element_immune/element_weak）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import conftest  # noqa: F401
except Exception:
    pass

from game import battle as BT
from game import engine as E

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

def mk_mon(extra=None):
    m = {"name": "元素Boss", "hp": 8000, "max_hp": 8000, "def": 60, "mdef": 60,
         "atk": 100, "matk": 80, "spd": 10, "lv": 40, "id": "m_test",
         "buffs": {}, "resources": {}, "stacks": {}, "charging": None,
         "skills": ["ms_ai_hao"], "elem_res": 0.0}
    if extra:
        m.update(extra)
    return m

print("== E5 元素免疫/弱点验证 ==")

# 1. 免疫火 → 火伤归 0
player = mk_player()
mon = mk_mon({"element_immune": ["fire"]})
b = BT.Battle("monster", mon)
b._focus = player
logs = []
dmg, magi = b._hostile_mitigate(500, 0, "fire", logs, kind="魔法")
check("免疫 fire → 伤害 0", dmg == 0, f"dmg={dmg}")
check("免疫有日志", any("免疫" in l for l in logs), str(logs))

# 2. 不免疫冰 → 正常
logs2 = []
dmg2, magi2 = b._hostile_mitigate(500, 0, "ice", logs2, kind="魔法")
check("不免疫 ice → 正常伤害", dmg2 > 0, f"dmg={dmg2}")

# 3. 弱点冰 ×1.5 → 增伤
mon3 = mk_mon({"element_weak": {"ice": 1.5}})
b3 = BT.Battle("monster", mon3)
b3._focus = player
logs3 = []
dmg3, _ = b3._hostile_mitigate(500, 0, "ice", logs3, kind="魔法")
check("弱点 ice ×1.5 → 伤害 ≥ 750", dmg3 >= 750, f"dmg={dmg3}")
check("弱点有日志", any("弱点" in l for l in logs3), str(logs3))

# 4. 无弱点的元素 → 正常
logs4 = []
dmg4, _ = b3._hostile_mitigate(500, 0, "fire", logs4, kind="魔法")
check("无弱点 fire → 正常 500", dmg4 == 500, f"dmg={dmg4}")

# 5. 普通怪无免疫/弱点字段 → 零行为变化
mon5 = mk_mon()
b5 = BT.Battle("monster", mon5)
b5._focus = player
logs5 = []
dmg5, _ = b5._hostile_mitigate(500, 0, "fire", logs5, kind="魔法")
check("普通怪无字段 → 伤害不变", dmg5 == 500, f"dmg={dmg5}")

# 6. 免疫 + 弱元素并存不冲突（免疫优先）
mon6 = mk_mon({"element_immune": ["ice"], "element_weak": {"ice": 1.5}})
b6 = BT.Battle("monster", mon6)
b6._focus = player
logs6 = []
dmg6, _ = b6._hostile_mitigate(500, 0, "ice", logs6, kind="魔法")
check("免疫优先于弱点", dmg6 == 0, f"dmg={dmg6}")

# 7. 真伤跳过免疫（K_TRUE 语义保留）
logs7 = []
dmg7, _ = b._hostile_mitigate(500, 0, "fire", logs7, kind="真伤")
check("真伤绕过免疫", dmg7 == 500, f"dmg={dmg7}")

# 8. build_monster 透传 element_immune/weak/dmg_taken_mult
from game.core.drops import build_monster
from game.data.monster_mods import MONSTER_MODS
_orig = MONSTER_MODS.get("m_test_imm")
MONSTER_MODS["m_test_imm"] = {
    "element_immune": ["fire"], "element_weak": {"ice": 1.5}, "dmg_taken_mult": 1.2,
    "desc": "测试透传",
}
try:
    mob = build_monster(("m_test_imm", "透传怪", "dps", 20, ["ms_ai_hao"], []),
                        {"id": "x", "name": "x", "area": "wild"})
    check("build_monster 透传 element_immune", mob.get("element_immune") == ["fire"], str(mob.get("element_immune")))
    check("build_monster 透传 element_weak", mob.get("element_weak") == {"ice": 1.5}, str(mob.get("element_weak")))
    check("build_monster 透传 dmg_taken_mult", mob.get("dmg_taken_mult") == 1.2, str(mob.get("dmg_taken_mult")))
finally:
    if _orig is not None:
        MONSTER_MODS["m_test_imm"] = _orig
    else:
        MONSTER_MODS.pop("m_test_imm", None)

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)