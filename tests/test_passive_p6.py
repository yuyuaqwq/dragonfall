# -*- coding: utf-8 -*-
"""v181.M-passive P6 测试——DOT 乘区（万毒归宗 dot_calc 引擎 N9.14 钩子）。

跑法：python tests/test_passive_p6.py（exit=0 全绿）
覆盖（旧语义源 = 旧 DOT 结算毒伤乘区；引擎改动 = schedule.py dot_calc + EVENTS）：
  1. 万毒归宗装配：dot_calc passive_dot_mult（judge dot_key poison）
  2. DOT 结算：毒跳伤害 ×1.35（enemy 中毒 → _settle_time_effects 推进）
  3. 对照组：无被动 → 毒跳无加成
"""
import sys, os
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "test_passive_p6.db"))
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from game.battle2 import config as _b2c
_b2c.load_game_defaults()
from game.battle2 import Battle as B2, make_actor
from game.services.class_mech_proc import apply_class_mech

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {detail}")


def mk_poisoner(skills):
    a = make_actor(uid="p_1", name="毒刃", side="player", kind="player",
                   human_controlled=True, class_name="cls_ci_ke", level=95,
                   learned_skills=list(skills), skills=list(skills),
                   atk=150, matk=30, spd=80, hp=3000, max_hp=3000, mp=200, max_mp=200)
    a['effects'] = {}
    a['bonus'] = {'panel': {}, 'cap': {}, 'cost': {}}
    return a


def mk_enemy(hp=10000):
    e = make_actor(uid="e_1", name="毒桩", side="enemy", kind="monster",
                   atk=1, matk=1, spd=1, hp=hp, max_hp=hp)
    e['effects'] = {}
    return e


def run_dot_tick(b, e):
    """推进 DOT 一跳：毒 interval 1.0——首调登记下一跳，二调触发。"""
    from game.battle2.schedule import _settle_time_effects
    b._now = 0.5
    _settle_time_effects(b, [])
    b._now = 1.6
    logs = []
    _settle_time_effects(b, logs)
    return logs


def test_1_assemble():
    print("【1. 万毒归宗装配：dot_calc passive_dot_mult】")
    p = mk_poisoner(["万毒归宗"])
    apply_class_mech(p)
    dc = [t for t in (p.get("triggers") or {}).get("dot_calc", [])
          if t.get("type") == "passive_dot_mult"]
    check("万毒归宗挂 dot_calc（judge dot_key poison）",
          len(dc) == 1 and (dc[0].get("judge") or {}).get("dot_key") == "poison",
          repr(dc))


def test_2_poison_boost():
    print("【2. DOT 结算：毒跳伤害 ×1.35】")
    p = mk_poisoner(["万毒归宗"])
    apply_class_mech(p)
    e = mk_enemy(hp=10000)
    e['effects']['poison'] = {'stacks': 5, 'expire': None}  # 5 层毒：2%×5=10% max_hp=1000
    b = B2("monster", sides={"player": [p], "enemy": [e]}, title_bonus={})
    logs = run_dot_tick(b, e)
    # DOT 落地：1000×1.35=1350 → hp 10000→8650
    check("毒跳 ×1.35 落地（hp 8650）", int(e.get("hp", 0)) == 8650,
          f"hp={e.get('hp')} logs={[l for l in logs if '毒' in l or 'DOT' in l][-2:]}")
    check("dot_calc 乘区日志", any("DOT" in l or "☠️" in l for l in logs),
          str(logs[-3:]))


def test_3_control():
    print("【3. 对照组：无被动 → 毒跳无加成】")
    p = mk_poisoner([])  # 没学万毒归宗
    apply_class_mech(p)
    e = mk_enemy(hp=10000)
    e['effects']['poison'] = {'stacks': 5, 'expire': None}
    b = B2("monster", sides={"player": [p], "enemy": [e]}, title_bonus={})
    logs = run_dot_tick(b, e)
    check("毒跳无加成（hp 9000）", int(e.get("hp", 0)) == 9000,
          f"hp={e.get('hp')}")


def main():
    test_1_assemble()
    test_2_poison_boost()
    test_3_control()
    print(f"\n结果：{PASS} 通过 / {FAIL} 失败")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
