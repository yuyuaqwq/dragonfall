# -*- coding: utf-8 -*-
"""v59 叠层/护盾持久化：修复"多次放技能狂暴只有一层"——
   层数原挂 player（每回合 db 重读丢失），改存 Battle 状态随战斗序列化。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import battle as BT

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

def test_serialize_roundtrip():
    print("【序列化 round trip 保留叠层/护盾】")
    b = BT.Battle("monster", {"name": "靶", "hp": 100, "max_hp": 100})
    b.mech_stacks["rage"] = 3
    b.shield = 50
    b2 = BT.Battle.from_state(b.to_state())
    check("叠层保留", b2.mech_stacks.get("rage") == 3, str(b2.mech_stacks))
    check("护盾保留", b2.shield == 50, str(b2.shield))
    # 老存档无字段兼容
    b3 = BT.Battle.from_state({"type": "monster", "enemy": {}, "p_buffs": {}, "e_buffs": {}})
    check("老存档兼容", b3.mech_stacks == {} and b3.shield == 0, str((b3.mech_stacks, b3.shield)))

def test_two_rounds_stack_persist():
    print("【跨回合叠层持久化（核心 bug 修复）】")
    player = {"hp": 1000, "max_hp": 1000, "mp": 500, "max_mp": 500,
              "atk": 100, "def": 50, "matk": 80, "mdef": 50, "spd": 10, "crit": 0.05,
              "equipment": {}, "skills": [], "skill_levels": {}, "learned_skills": []}
    enemy = {"name": "靶子", "lv": 10, "hp": 99999, "max_hp": 99999,
             "atk": 1, "def": 1, "matk": 1, "mdef": 1, "spd": 1}
    b = BT.Battle("monster", enemy)
    b._apply_mech_effect("rage", 1, b.mech_stacks, 100, [], "狂暴打击")
    st = b.to_state()  # 模拟 db 存储
    b2 = BT.Battle.from_state(st)  # 模拟下一回合 db 重读
    b2._apply_mech_effect("rage", 1, b2.mech_stacks, 100, [], "狂暴打击")
    check("第2回合狂暴=2层", b2.mech_stacks.get("rage") == 2, str(b2.mech_stacks.get("rage")))
    # 叠到封顶
    for _ in range(5):
        b2._apply_mech_effect("rage", 1, b2.mech_stacks, 100, [], "狂暴打击")
    check("封顶 5", b2.mech_stacks.get("rage") == 5, str(b2.mech_stacks.get("rage")))

def test_shield_persist_and_absorb():
    print("【护盾跨回合 + 吸收】")
    player = {"hp": 1000, "max_hp": 1000, "mp": 500, "max_mp": 500,
              "atk": 100, "def": 50, "matk": 80, "mdef": 50, "spd": 10, "crit": 0.05,
              "equipment": {}, "skills": [], "skill_levels": {}, "learned_skills": []}
    enemy = {"name": "靶子", "lv": 10, "hp": 99999, "max_hp": 99999,
             "atk": 50, "def": 1, "matk": 1, "mdef": 1, "spd": 1}
    b = BT.Battle("monster", enemy)
    b.shield = b.shield + 100
    b2 = BT.Battle.from_state(b.to_state())
    check("护盾跨回合保留", b2.shield == 100, str(b2.shield))
    logs = []
    b2._damage_player(player, 30, logs)
    check("吸收后剩 70", b2.shield == 70, str(b2.shield))
    check("玩家未掉血", player["hp"] == 1000, str(player["hp"]))

if __name__ == "__main__":
    test_serialize_roundtrip()
    test_two_rounds_stack_persist()
    test_shield_persist_and_absorb()
    print(f"\n✅ v59 叠层/护盾持久化：{passed} 项全部通过")
