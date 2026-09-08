# -*- coding: utf-8 -*-
"""N5b4-2 验证：命令层战斗闭环数据流（battle2 引擎路径）。

模拟真实命令（explore → attack → victory）在 CombatCmds 改造后的
数据搬运语义——构造走 _open_battle2（仪式/sides/装配）、行动走
human_act + sync_player_from_actor 回写、存盘/恢复走 battle2 state。

跑法：python tests/test_battle2_n5b4_flow.py
"""
import os
import sys
import tempfile

os.environ["GWEN_GAME_DB"] = os.path.join(tempfile.mkdtemp(), "game.db")
os.environ["GWEN_TEST_MODE"] = "1"
_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN_DIR)))
sys.path.insert(0, _QQBOT_DIR)
sys.path.insert(0, _PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from game.battle2 import config as _b2c  # noqa: E402
_b2c.load_game_defaults()  # noqa: E402
from game.store.connection import init_db  # noqa: E402
init_db()

from game.core import drops as D  # noqa: E402
from game import db  # noqa: E402
from game.commands.combat import CombatCmds  # noqa: E402

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILURES.append(f"{name}: {detail}")
        print(f"  ❌ {name} {detail}")


def make_player(cls="战士", level=10, qid=10001):
    return {"qq_id": qid, "group_id": "g1", "name": "流程勇者", "class_name": cls,
            "level": level, "hp": 300, "mp": 50, "max_hp": 300, "max_mp": 50,
            "equipment": {}, "class_tier": 0, "attributes": None,
            "evolve_path": 0, "race": None, "learned_skills": [],
            "cur_map": "test_plain", "cur_subarea": "", "stamina": 100}


def build_wolf():
    map_obj = {"id": "test_plain", "name": "测试平原", "area": "field",
               "type": "field", "lv": 5}
    mon = D.build_monster(("test_wolf", "野狼", "dps", 3, [], []), map_obj)
    return D.build_monster_group(mon, map_obj, make_player())


def test_open_and_attack_loop():
    print("【N5b4-2 explore→attack→存盘→恢复→打完】")
    cmds = CombatCmds.__new__(CombatCmds)
    gid, qid = "g_flow", 10001
    player = make_player(qid=qid)
    group = build_wolf()

    # ① explore 构造（_open_battle2：仪式 → sides → 装配 → Battle）
    b = cmds._open_battle2(player, group, "monster", group_id=gid, qq_id=qid)
    check("构造成功 sides", b is not None and len(b.sides_of("enemy")) == len(group))
    st = b.to_state()
    check("state 含 sides", "sides" in st and "type" in st and st["type"] == "monster")
    db.save_battle(gid, qid, st)
    cmds._lock_battle(gid, qid)

    # ② attack 恢复 + human_act + sync 回写
    row = db.get_battle(gid, qid)
    b2 = cmds._restore_battle2(row["state"])
    check("恢复成功", b2 is not None)
    hp0 = b2.sides_of("enemy")[0].get("hp", 0)
    logs, ended, who = b2.human_act("attack", None, b2.focus())
    cmds._sync_battle_player(player, b2)
    dmg = hp0 - b2.sides_of("enemy")[0].get("hp", 0)
    check("普攻造成伤害", dmg > 0, f"dmg={dmg}")
    check("回写 hp 到 player", player.get("hp", 0) <= 300, f"hp={player.get('hp')}")
    # 行动后 db.update_player（命令层真实调用）
    db.update_player(gid, qid, hp=player["hp"], mp=player["mp"],
                     max_hp=player["max_hp"], max_mp=player["max_mp"])
    db.save_battle(gid, qid, b2.to_state())

    # ③ 续战恢复 → 打到结束（auto 模拟多回合玩家输入）
    b3 = None
    guard = 0
    while guard < 60:
        guard += 1
        row = db.get_battle(gid, qid)
        b3 = cmds._restore_battle2(row["state"])
        if b3 is None:
            break
        if b3.result:
            break
        logs, ended, who = b3.human_act("attack", None, b3.focus())
        cmds._sync_battle_player(player, b3)
        db.update_player(gid, qid, hp=player["hp"], mp=player["mp"],
                         max_hp=player["max_hp"], max_mp=player["max_mp"])
        if ended:
            db.save_battle(gid, qid, b3.to_state())
            break
        db.save_battle(gid, qid, b3.to_state())
    check("战斗有结果", b3 is not None and b3.result in ("victory", "defeat"),
          f"result={getattr(b3, 'result', None)} guard={guard}")

    # ④ 展示函数在恢复后的 battle2 上不崩
    row = db.get_battle(gid, qid)
    b4 = cmds._restore_battle2(row["state"]) if row else None
    if b4 is not None:
        f = cmds._battle_footer(player, b4, cmds._b_enemy(b4) or {})
        check("战后页脚不崩", isinstance(f, str))
    db.clear_battle(gid, qid)
    cmds._unlock_battle(gid, qid)
    check("清战斗", db.get_battle(gid, qid) is None)


def test_legacy_state_cleared():
    print("【N5b4-2 旧格式存档 → 清档重开】")
    cmds = CombatCmds.__new__(CombatCmds)
    gid, qid = "g_old", 10002
    legacy = {"type": "monster", "now": 2.0, "round": 1, "result": None,
              "enemy": {"name": "旧怪", "hp": 100, "max_hp": 100}}
    db.save_battle(gid, qid, legacy)
    b = cmds._restore_battle2(legacy)
    check("旧格式恢复返回 None", b is None)
    db.clear_battle(gid, qid)
    check("旧格式清档", db.get_battle(gid, qid) is None)


def main():
    print("=== N5b4-2 命令层 battle2 战斗闭环 ===")
    test_open_and_attack_loop()
    test_legacy_state_cleared()
    print(f"\n=== 结果 PASS={PASS} FAIL={FAIL} ===")
    if FAILURES:
        for f in FAILURES:
            print(f"  - {f}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
