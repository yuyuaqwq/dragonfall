# -*- coding: utf-8 -*-
"""v126.7 战斗胜利结算回归测试：打死怪后 _remove_unit 清空 enemies 导致
b.enemy 变 {} → _handle_victory monster["exp"] KeyError（玩家鱼鱼 2026-08-18
实战抓包：每次打死怪物就报 'exp'）。

根因：v116 harness 多对多重构后，死亡单位从 enemies 阵列移除 + compact 压缩，
单怪场景 enemies 清空 → b.enemy property 兜底返回 {}。
修复：Battle 构造时保存 _origin_enemy 副本（原主怪 exp/gold/lv/drops），
3 处胜利结算调用点（attack/skill/use_item）改用 _origin_enemy。

环境铁律：私有库 test_v1267.db（绝不碰生产库）。
"""
import os
import sys

os.environ["GWEN_GAME_DB"] = os.path.abspath("test_v1267.db")
os.environ["GWEN_TEST_MODE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.game.commands.combat import CombatCmds  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def test_origin_enemy_preserved():
    print("【1. _origin_enemy 保存原主怪引用（含 exp/gold）】")
    mon_def = ("m_slime", "史莱姆", "dps", 1, ["撞击"], [])
    m = C.build_monster(mon_def, {"id": "oak_plain", "name": "橡木平原", "area": "新手区"})
    check("build_monster 有 exp", m.get("exp", 0) > 0, str(m.get("exp")))
    group = C.build_monster_group(m, {"id": "oak_plain", "name": "橡木平原"})
    b = BT.Battle("monster", None, {}, player={}, enemies=group)
    check("_origin_enemy 有 exp", b._origin_enemy.get("exp") == m["exp"],
          f"origin={b._origin_enemy.get('exp')} vs {m['exp']}")
    check("_origin_enemy 有 gold", b._origin_enemy.get("gold") == m["gold"], str(b._origin_enemy.get("gold")))
    check("_origin_enemy 有 name", b._origin_enemy.get("name") == "史莱姆", str(b._origin_enemy.get("name")))


def test_victory_after_remove_unit():
    print("【2. 打死怪后 b.enemy 变 {} 但 _origin_enemy 保留】")
    mon_def = ("m_slime", "史莱姆", "dps", 1, ["撞击"], [])
    m = C.build_monster(mon_def, {"id": "oak_plain", "name": "橡木平原", "area": "新手区"})
    b = BT.Battle("monster", None, {}, player={},
                  enemies=C.build_monster_group(m, {"id": "oak_plain", "name": "橡木平原"}))
    b.enemy["hp"] = 0
    b._remove_unit("enemy", b.enemy)
    check("enemies 被清空", len(b.enemies) == 0, str(len(b.enemies)))
    check("b.enemy 变 {}", b.enemy == {}, repr(b.enemy))
    _mon = getattr(b, "_origin_enemy", None) or b.enemy
    check("结算用 _origin_enemy.exp 可读", _mon.get("exp") == m["exp"],
          f"{_mon.get('exp')} vs {m['exp']}")
    check("结算用 _origin_enemy.gold 可读", _mon.get("gold") == m["gold"],
          f"{_mon.get('gold')} vs {m['gold']}")


def test_from_state_restore():
    print("【3. from_state 恢复后 _origin_enemy 正确】")
    mon_def = ("m_slime", "史莱姆", "dps", 1, ["撞击"], [])
    m = C.build_monster(mon_def, {"id": "oak_plain", "name": "橡木平原", "area": "新手区"})
    b = BT.Battle("monster", None, {}, player={},
                  enemies=C.build_monster_group(m, {"id": "oak_plain", "name": "橡木平原"}))
    b.enemy["hp"] = 5  # 打一半保存
    st = b.to_state()
    b2 = BT.Battle.from_state(st)
    check("恢复后 _origin_enemy.exp 正确", b2._origin_enemy.get("exp") == m["exp"],
          f"{b2._origin_enemy.get('exp')} vs {m['exp']}")
    check("恢复后 _origin_enemy 独立副本（不随 enemies 变空丢失）",
          b2._origin_enemy.get("name") == "史莱姆", str(b2._origin_enemy.get("name")))


def test_handle_victory_call_uses_origin():
    print("【4. 命令层胜利结算调用点用 _origin_enemy】")
    import inspect
    import re
    src = inspect.getsource(CombatCmds.attack) + inspect.getsource(CombatCmds.skill)
    # 两处调用点都应带 _origin_enemy 兜底
    check("attack 胜利分支用 _origin_enemy", "_origin_enemy" in src, "")
    check("skill 胜利分支用 _origin_enemy", src.count("_origin_enemy") >= 2, str(src.count("_origin_enemy")))
    # economy.py use_item 调用点
    from data.plugins.dragonfall.game.commands.economy import EconomyCmds
    eco_src = inspect.getsource(EconomyCmds)
    check("economy use_item 胜利分支用 _origin_enemy", "_origin_enemy" in eco_src, "")


if __name__ == "__main__":
    clean_db()
    test_origin_enemy_preserved()
    test_victory_after_remove_unit()
    test_from_state_restore()
    test_handle_victory_call_uses_origin()
    print(f"\n===== 结果 {passed} 通过 / {failed} 失败 =====")
    sys.exit(1 if failed else 0)
