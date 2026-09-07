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

def _mk_battle(enemy=None):
    """v180-B ①：状态权威在 player actor dict——构造带完整玩家快照（面板字段完整才能跑引擎方法）。"""
    b = BT.Battle("monster", enemy or {"name": "靶", "hp": 100, "max_hp": 100})
    b._focus = {
        "class_name": "cls_zhan_shi", "qq_id": "p_test",
        "hp": 1000, "max_hp": 1000, "mp": 500, "max_mp": 500,
        "atk": 100, "def": 50, "matk": 80, "mdef": 50, "spd": 10, "crit": 0.05,
        "equipment": {}, "skills": [], "skill_levels": {}, "learned_skills": [],
    }
    return b

def _player():
    return {"class_name": "cls_zhan_shi", "qq_id": "p_test",
            "hp": 1000, "max_hp": 1000, "mp": 500, "max_mp": 500,
            "atk": 100, "def": 50, "matk": 80, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": {}, "skills": [], "skill_levels": {}, "learned_skills": []}

def test_serialize_roundtrip():
    print("【序列化 round trip 保留叠层/护盾】")
    b = _mk_battle()
    b._p_stacks()["rage"] = 3
    b._p_shields_bag()["test_shield"] = {"value": 50, "turns": 999}
    st = b.to_state()
    b2 = BT.Battle.from_state(st)
    b2._focus = _player()          # v180-B：from_state 后绑定玩家 actor dict
    b2._apply_restore_pstate()     # 恢复状态灌入绑定玩家
    check("叠层保留", b2._p_stacks().get("rage") == 3, str(b2._p_stacks()))
    check("护盾保留", b2._p_shields_bag().get("test_shield", {}).get("value") == 50, str(b2._p_shields_bag()))
    # 老存档无字段兼容
    b3 = BT.Battle.from_state({"type": "monster", "enemy": {}, "p_buffs": {}, "e_buffs": {}})
    b3._focus = _player()
    b3._apply_restore_pstate()
    check("老存档兼容", b3._p_stacks() == {} and b3._p_shields_bag() == {},
          str((b3._p_stacks(), b3._p_shields_bag())))

def test_two_rounds_stack_persist():
    print("【跨回合叠层持久化（核心 bug 修复）】")
    enemy = {"name": "靶子", "lv": 10, "hp": 99999, "max_hp": 99999,
             "atk": 1, "def": 1, "matk": 1, "mdef": 1, "spd": 1}
    player = _player()
    b = _mk_battle(enemy)
    b._focus = player
    b._apply_mech_effect("rage", 1, b._p_stacks(), 100, [], "狂暴打击")
    st = b.to_state()  # 模拟 db 存储
    b2 = BT.Battle.from_state(st)  # 模拟下一回合 db 重读
    b2._focus = player  # v180-B：恢复战斗需绑玩家（状态经 _apply_restore_pstate 灌入）
    b2._apply_restore_pstate()
    b2._apply_mech_effect("rage", 1, b2._p_stacks(), 100, [], "狂暴打击")
    check("第2回合狂暴=2层", b2._p_stacks().get("rage") == 2, str(b2._p_stacks().get("rage")))
    # 叠到封顶
    for _ in range(5):
        b2._apply_mech_effect("rage", 1, b2._p_stacks(), 100, [], "狂暴打击")
    check("封顶 5", b2._p_stacks().get("rage") == 5, str(b2._p_stacks().get("rage")))

def test_shield_persist_and_absorb():
    print("【护盾跨回合 + 吸收】")
    enemy = {"name": "靶子", "lv": 10, "hp": 99999, "max_hp": 99999,
             "atk": 50, "def": 1, "matk": 1, "mdef": 1, "spd": 1}
    player = _player()
    b = _mk_battle(enemy)
    b._focus = player
    b._p_shields_bag()["test_shield"] = {"value": 100, "turns": 999}
    b2 = BT.Battle.from_state(b.to_state())
    b2._focus = player
    b2._apply_restore_pstate()
    check("护盾跨回合保留", b2._p_shields_bag().get("test_shield", {}).get("value") == 100, str(b2._p_shields_bag()))
    # 屏蔽随机闪避，保证受击断言确定性（护盾吸收需命中才触发）
    _orig_ps = b2._player_stats
    def _ps_nododge(p_):
        s = _orig_ps(p_)
        s["dodge"] = 0.0
        return s
    b2._player_stats = _ps_nododge
    logs = []
    b2._damage_actor(player, 30, logs)
    check("吸收后剩 70", b2._p_shields_bag().get("test_shield", {}).get("value") == 70, str(b2._p_shields_bag()))
    check("玩家未掉血", player["hp"] == 1000, str(player["hp"]))

def test_reduce_all_left_persist():
    print("【团队减伤剩余回合跨存档持久化（A0-A2）】")
    b = _mk_battle()
    b._p_set_reduce_all_left(3)
    st = b.to_state()
    b2 = BT.Battle.from_state(st)
    b2._focus = _player()
    b2._apply_restore_pstate()
    check("reduce_all_left 保留", b2._p_reduce_all_left() == 3, str(b2._p_reduce_all_left()))
    # 老存档无字段兼容（默认 0）
    b3 = BT.Battle.from_state({"type": "monster", "enemy": {}, "p_buffs": {}, "e_buffs": {}})
    b3._focus = _player()
    b3._apply_restore_pstate()
    check("老存档兼容", b3._p_reduce_all_left() == 0, str(b3._p_reduce_all_left()))

if __name__ == "__main__":
    test_serialize_roundtrip()
    test_two_rounds_stack_persist()
    test_shield_persist_and_absorb()
    test_reduce_all_left_persist()
    print(f"\n结果: {passed} 通过, 0 失败")