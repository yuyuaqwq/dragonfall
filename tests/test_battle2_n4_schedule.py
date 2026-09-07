# -*- coding: utf-8 -*-
"""N4 验收：CTB 调度 + 自动行动 + 完整战斗闭环。

覆盖：
- 完整战斗 auto_run 能打到 victory/defeat（玩家 vs 怪）
- 行动序：速度快者先动（ct 推进正确）
- human_act 推进：玩家出手 → 自动 actor 行动 → 下一个决策点
- DOT：带 burn 状态的目标随时间跳伤害
- 逃跑 fled

跑法：python tests/test_battle2_n4_schedule.py
"""
import os
import sys
import random

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
TEST_DB = os.path.join(PLUGIN_DIR, "test_battle2_n4.db")
os.environ.setdefault("GWEN_GAME_DB", TEST_DB)
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from game import content as C            # noqa: E402
from game import engine as E             # noqa: E402
from game.battle2 import Battle as BT_NEW, make_actor  # noqa: E402
from game.battle2 import config as _b2config  # noqa: E402
_b2config.load_game_defaults()  # noqa: E402

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


def mk_player(cls="战士", level=10, hp=None):
    st = E.player_final_stats(cls, level, {}, 0, {}, 1)
    p = make_actor(uid="p_q1", name="测试勇者", side="player", kind="player",
                   human_controlled=True, class_name=cls, level=level,
                   hp=hp if hp is not None else int(st["max_hp"]),
                   max_hp=int(st["max_hp"]),
                   mp=int(st["max_mp"]), max_mp=int(st["max_mp"]),
                   equipment={}, skills=[], learned_skills=[],
                   race=None, evolve_path=1, class_tier=0, attributes={},
                   **{k: st[k] for k in ("atk", "matk", "def", "mdef", "spd", "crit") if k in st})
    return p


def mk_monster(hp=200, atk=20, spd=5, name="野狼"):
    return make_actor(uid="e_0", name=name, side="enemy", kind="monster",
                      hp=hp, max_hp=hp, atk=atk, **{"def": 5},
                      matk=5, mdef=5, spd=spd, crit=0.05, level=5)


def test_full_battle_victory():
    print("【N4.1 完整战斗：玩家打赢（victory）】")
    p = mk_player("战士", 12)
    m = mk_monster(hp=150, atk=5)  # 怪很弱
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    logs = []
    b.auto_run(logs)
    check("战斗结束", b.result in ("victory", "defeat"))
    check("玩家胜利", b.result == "victory", f"result={b.result}")
    check("怪物死亡", m["hp"] <= 0)
    check("有行动日志", len(logs) > 3)


def test_full_battle_defeat():
    print("【N4.2 完整战斗：玩家被打死（defeat）】")
    p = mk_player("战士", 3)
    m = mk_monster(hp=2000, atk=60, spd=30, name="强敌")
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    logs = []
    b.auto_run(logs)
    check("玩家战败", b.result == "defeat", f"result={b.result}")
    check("玩家死亡", p["hp"] <= 0)


def test_speed_order():
    print("【N4.3 速度决定行动序：快怪先动】")
    # 怪 spd=30 vs 玩家 spd=5 → 怪第一动
    p = mk_player("战士", 10)
    m = mk_monster(hp=100000, atk=1, spd=30, name="快怪")
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    from game.battle2 import schedule as SC
    ct_p = SC.initial_ct(p["spd"])
    ct_m = SC.initial_ct(m["spd"])
    check("快怪初始 ct < 玩家", ct_m < ct_p, f"m={ct_m:.2f} p={ct_p:.2f}")


def test_human_act_advance():
    print("【N4.4 human_act 推进：玩家出手后自动怪会行动】")
    p = mk_player("战士", 10)
    m = mk_monster(hp=100000, atk=5, spd=3, name="慢怪")
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    hp0 = m["hp"]
    # 玩家出手普攻 → 应推进到怪物行动若干次
    logs, ended, who = b.human_act("attack", None, p)
    dmg = hp0 - m["hp"]
    check("玩家普攻打到怪", dmg > 0, f"dmg={dmg}")
    check("推进后未结束（怪血厚）", not ended, f"ended={ended}")
    # 玩家 ct 已推进
    check("玩家 ct > 0", float(p.get("ct", 0)) > 0, f"ct={p.get('ct')}")
    check("now 推进 > 0", b._now > 0, f"now={b._now}")


def test_dot_tick():
    print("【N4.5 DOT：目标带 burn 状态随时间跳伤害】")
    p = mk_player("战士", 20)
    m = mk_monster(hp=10000, atk=1, spd=100, name="靶怪")
    # 挂 burn 3 层（state_add on=target）
    from game.battle2 import effects as FX
    FX.apply_effects(b := BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]}),
                     p, m, [{"type": "state_add", "key": "burn", "amount": 3, "on": "target"}], [])
    check("burn 3 层挂上", m["state"].get("burn") == 3)
    hp0 = m["hp"]
    logs = []
    b.auto_run(logs)
    check("时间推进后怪掉血", m["hp"] < hp0, f"hp {hp0} → {m['hp']}")


def test_flee():
    print("【N4.6 逃跑：fled 结束】")
    p = mk_player("战士", 10)
    m = mk_monster(hp=100000, atk=1)
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    logs, ended, who = b.human_act("flee", None, p)
    check("逃跑结束", b.result == "fled", f"result={b.result}")


def main():
    print("=== N4 battle2 CTB 调度测试 ===")
    test_full_battle_victory()
    test_full_battle_defeat()
    test_speed_order()
    test_human_act_advance()
    test_dot_tick()
    test_flee()
    print(f"\n=== 结果 PASS={PASS} FAIL={FAIL} ===")
    if FAILURES:
        for f in FAILURES:
            print(f"  - {f}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
