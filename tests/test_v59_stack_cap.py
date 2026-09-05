# -*- coding: utf-8 -*-
"""v59 叠层上限：分支机制层数封顶，防一场战斗无限滚雪球"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import engine as E
from game import battle as BT

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

def _mk_battle(enemy=None):
    """v180-B ①：状态权威在玩家 actor dict——构造后绑玩家快照。"""
    b = BT.Battle("monster", enemy or {"name": "靶子", "lv": 10, "hp": 99999, "max_hp": 99999,
                                       "atk": 1, "def": 1, "matk": 1, "mdef": 1, "spd": 1})
    b.player = {
        "class_name": "zhan_shi", "level": 30, "max_hp": 1000, "hp": 1000,
        "max_mp": 500, "mp": 500, "atk": 100, "def": 50, "matk": 80, "mdef": 50,
        "spd": 10, "crit": 0.05, "equipment": {},
        "skills": [], "skill_levels": {}, "learned_skills": [],
    }
    return b

def test_stack_cap():
    print("【机制：叠层上限】")
    m = {}
    m["burn"] = E.mech_stack_gain("burn", m, 3)
    check("灼烧 3 层", m["burn"] == 3, str(m["burn"]))
    m["burn"] = E.mech_stack_gain("burn", m, 3)
    check("灼烧 3+3 封顶 5", m["burn"] == 5, str(m["burn"]))
    m["wind"] = E.mech_stack_gain("wind", m, 3)
    check("风印 3 层封顶", m["wind"] == 3, str(m["wind"]))
    m["bless"] = E.mech_stack_gain("bless", m, 10)
    check("神恩 10 层封顶", m["bless"] == 10, str(m["bless"]))
    m["rage"] = E.mech_stack_gain("rage", m, 5)
    m["rage"] = E.mech_stack_gain("rage", m, 5)
    check("狂暴 5+5 封顶 5", m["rage"] == 5, str(m["rage"]))
    m["poison"] = E.mech_stack_gain("poison", m, 2)
    m["poison"] = E.mech_stack_gain("poison", m, 2)
    m["poison"] = E.mech_stack_gain("poison", m, 2)
    check("毒层 2+2+2 封顶 5", m["poison"] == 5, str(m["poison"]))
    # 无上限机制不受限
    m2 = {}
    m2["freeze"] = E.mech_stack_gain("freeze", m2, 5)
    check("freeze 不在表内不限制", m2["freeze"] == 5, str(m2["freeze"]))

def test_battle_cap():
    print("【机制：战斗内叠层封顶】")
    b = _mk_battle()
    p_mech = b._p_stacks()  # v180-B：玩家侧叠层权威 = player actor dict["stacks"]
    for _ in range(7):
        b._apply_mech_effect("rage", 1, p_mech, 100, [], "狂暴打击")
    check("狂暴叠 7 次封顶 5", p_mech.get("rage") == 5, str(p_mech.get("rage")))
    for _ in range(6):
        b._apply_mech_effect("burn", 1, p_mech, 100, [], "灼烧")
    # 重构图：敌方灼烧层迁至 enemy.debuffs（目标级共享），cap 5 语义不变
    check("灼烧叠 6 次封顶 5", (b.enemy.get("debuffs") or {}).get("burn", {}).get("n") == 5,
          str(b.enemy.get("debuffs")))
    for _ in range(4):
        b._apply_mech_effect("wind", 1, p_mech, 100, [], "风印")
    check("风印叠 4 次封顶 3", p_mech.get("wind") == 3, str(p_mech.get("wind")))
    # 增益类走 _apply_mech_gain 同样封顶
    for _ in range(4):
        b._apply_mech_gain("shield", 2, p_mech, [], "圣盾术")
    check("圣盾叠 4 次(2/次)封顶 5", p_mech.get("shield") == 5, str(p_mech.get("shield")))

def test_poison_all_cap():
    print("【机制：副本全队淬毒封顶】")
    from game.commands import instance as inst
    # 直接测 helper 语义（淬毒 +2，叠 3 次到 5 封顶）
    ms = {}
    for _ in range(3):
        ms["poison"] = E.mech_stack_gain("poison", ms, 2)
    check("淬毒 2×3 封顶 5", ms["poison"] == 5, str(ms["poison"]))

if __name__ == "__main__":
    test_stack_cap()
    test_battle_cap()
    test_poison_all_cap()
    print(f"\n结果: {passed} 通过, 0 失败")
