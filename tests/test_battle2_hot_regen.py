# -*- coding: utf-8 -*-
"""N5b4-5a I1 验收：hot 正向持续恢复（battle2 schedule）。

覆盖（对齐旧引擎 v179 P3 语义——每秒墙钟跳，与出手快慢无关；对称 DOT 绝对时刻补跳）：
- 挂 hot 后首跳延迟 1s（首跳登记 now+interval，不立即跳）
- 到点回血/回蓝（按 max_hp/max_mp 百分比，clamp 上限）
- 跨多刻补跳多次（now 一次性推远 → 循环补跳）
- turns 递减，归零清容器（hot 键保留空 dict=actor 同构）
- 同刻重复 settle 不重复跳

跑法：python tests/test_battle2_hot_regen.py
"""
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
TEST_DB = os.path.join(PLUGIN_DIR, "test_battle2_hot_regen.db")
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


def mk_player(cls="战士", level=10, hp_ratio=0.5, mp_ratio=1.0):
    st = E.player_final_stats(cls, level, {}, 0, {}, 1)
    p = make_actor(uid="p_q1", name="测试勇者", side="player", kind="player",
                   human_controlled=True, class_name=cls, level=level,
                   hp=int(st["max_hp"] * hp_ratio),
                   max_hp=int(st["max_hp"]),
                   mp=int(st["max_mp"] * mp_ratio), max_mp=int(st["max_mp"]),
                   equipment={}, skills=[], learned_skills=[],
                   race=None, evolve_path=1, class_tier=0, attributes={},
                   **{k: st[k] for k in ("atk", "matk", "def", "mdef", "spd", "crit") if k in st})
    return p


def mk_monster(hp=100000, atk=1, spd=1):
    return make_actor(uid="e_0", name="木桩", side="enemy", kind="monster",
                      hp=hp, max_hp=hp, atk=atk, **{"def": 0},
                      matk=0, mdef=0, spd=spd, crit=0.0, level=1)


def _mk_battle(p, m=None):
    return BT_NEW(btype="monster", sides={"player": [p], "enemy": [m or mk_monster()]})


def test_hot_first_jump_delay():
    """首跳延迟：挂 hot 后同刻不跳，hot_next 登记 now+1。"""
    print("【I1.1 首跳延迟：挂 hot 同刻不跳，登记 now+interval】")
    from game.battle2.schedule import _settle_time_effects as _ste, HOT_INTERVAL
    p = mk_player(hp_ratio=0.5)
    b = _mk_battle(p)
    p["hot"] = {"heal": 0.1, "mana": 0.0, "turns": 3}
    hp0 = p["hp"]
    b._now = 0.0
    _ste(b, [])
    check("同刻不跳（首跳延迟）", p["hp"] == hp0, f"hp {hp0} → {p['hp']}")
    check("hot_next 登记 now+1", abs(float(p["hot_next"]) - 1.0) < 1e-9,
          f"hot_next={p.get('hot_next')}")
    check("turns 未减", p["hot"].get("turns") == 3)


def test_hot_heal_and_mana():
    """到点回血回蓝（百分比×max，clamp 上限）。"""
    print("【I1.2 到点跳：回血 + 回蓝 + clamp】")
    from game.battle2.schedule import _settle_time_effects as _ste
    p = mk_player(hp_ratio=0.5, mp_ratio=0.5)
    mx_hp = p["max_hp"]
    mx_mp = p["max_mp"]
    b = _mk_battle(p)
    p["hot"] = {"heal": 0.1, "mana": 0.1, "turns": 2}
    hp0, mp0 = p["hp"], p["mp"]
    logs = []
    b._now = 0.0
    _ste(b, [])  # 惰性登记 hot_next=1.0（对称 DOT）
    b._now = 1.0
    _ste(b, logs)
    gain_hp = int(mx_hp * 0.1)
    gain_mp = int(mx_mp * 0.1)
    check("回血 10%max", p["hp"] == hp0 + gain_hp, f"{hp0} → {p['hp']} (期望+{gain_hp})")
    check("回蓝 10%max", p["mp"] == mp0 + gain_mp, f"{mp0} → {p['mp']} (期望+{gain_mp})")
    check("有恢复日志", any("持续恢复" in x for x in logs), f"logs={logs}")
    check("turns 递减到 1", p["hot"].get("turns") == 1, f"turns={p['hot'].get('turns')}")


def test_hot_catchup_multijump():
    """跨多刻补跳：now 一次性推远 → while 循环补跳多次。"""
    print("【I1.3 跨多刻补跳：now 推远 5s → 跳满 turns 次】")
    from game.battle2.schedule import _settle_time_effects as _ste
    p = mk_player(hp_ratio=0.1)
    mx_hp = p["max_hp"]
    b = _mk_battle(p)
    p["hot"] = {"heal": 0.1, "mana": 0.0, "turns": 3}
    hp0 = p["hp"]
    b._now = 0.0
    _ste(b, [])  # 登记
    b._now = 1.0
    _ste(b, [])
    # 已跳 1 次（now=1.0），turns=2，hot_next=2.0
    check("首跳后 turns=2", p["hot"].get("turns") == 2, f"turns={p['hot'].get('turns')}")
    b._now = 5.0  # 一次推远 4s → 应补跳 2 次（t=2,3），turns 归零清容器
    _ste(b, [])
    check("hot 容器清空", p["hot"] == {}, f"hot={p['hot']}")
    check("hot_next 清除", "hot_next" not in p, f"hot_next={p.get('hot_next')}")
    expect = hp0 + int(mx_hp * 0.1) * 3
    check("血量 = 首跳+补跳 3 次总量", p["hp"] == expect,
          f"{p['hp']} vs {expect}")


def test_hot_clamp_max():
    """clamp：恢复不超过 max_hp/max_mp。"""
    print("【I1.4 clamp：恢复封顶 max】")
    from game.battle2.schedule import _settle_time_effects as _ste
    p = mk_player(hp_ratio=0.95)
    b = _mk_battle(p)
    p["hot"] = {"heal": 0.1, "mana": 0.0, "turns": 3}
    b._now = 0.0
    _ste(b, [])  # 登记
    b._now = 1.0
    _ste(b, [])
    b._now = 2.0
    _ste(b, [])
    check("hp 封顶 max_hp", p["hp"] == p["max_hp"], f"{p['hp']}/{p['max_hp']}")


def test_hot_no_repeat_same_now():
    """同刻重复 settle 不重复跳（绝对时刻推进语义）。"""
    print("【I1.5 同刻重复 settle 不重复跳】")
    from game.battle2.schedule import _settle_time_effects as _ste
    p = mk_player(hp_ratio=0.5)
    b = _mk_battle(p)
    p["hot"] = {"heal": 0.1, "mana": 0.0, "turns": 3}
    b._now = 0.0
    _ste(b, [])  # 登记 hot_next=1
    hp0 = p["hp"]
    b._now = 1.0
    _ste(b, [])
    hp1 = p["hp"]
    check("now=1 跳 1 次", hp1 > hp0)
    _ste(b, [])  # 同刻再 settle
    check("同刻不重复跳", p["hp"] == hp1, f"{hp1} → {p['hp']}")


def test_hot_auto_run_integration():
    """集成：战斗中挂 hot 后随墙钟结算（木桩不打人，纯验 hot 时间轴）。"""
    print("【I1.6 集成：auto_run 中 hot 随墙钟结算】")
    p = mk_player(hp_ratio=0.4)
    m = mk_monster(hp=100000, atk=0, spd=1)  # 木桩：atk=0 不掉玩家血
    b = _mk_battle(p, m)
    p["hp"] = int(p["max_hp"] * 0.4)
    p["hot"] = {"heal": 0.05, "mana": 0.0, "turns": 3}
    logs = []
    b.auto_run(logs)
    # auto_run 推进中 hot 至少跳过 1 次（墙钟制，与玩家出手无关）
    hot_logs = [x for x in logs if "持续恢复" in x]
    check("auto_run 中有 hot 结算日志", len(hot_logs) >= 1, f"hot_logs={hot_logs}")
    # 战斗没结束（玩家打不死木桩，木桩打不死玩家），但 hot 容器应已耗尽清空或 turn 递减
    check("hot 已结算推进", p["hot"] == {} or int(p["hot"].get("turns", 0)) < 3,
          f"hot={p['hot']}")


def main():
    print("=== I1 battle2 hot 持续恢复测试 ===")
    test_hot_first_jump_delay()
    test_hot_heal_and_mana()
    test_hot_catchup_multijump()
    test_hot_clamp_max()
    test_hot_no_repeat_same_now()
    test_hot_auto_run_integration()
    print(f"\n=== 结果 PASS={PASS} FAIL={FAIL} ===")
    if FAILURES:
        for f in FAILURES:
            print(f"  - {f}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
