# -*- coding: utf-8 -*-
"""N1 验收：battle2 新引擎普攻闭环 vs 旧 battle.py 同场景数值对拍。

跑法：python tests/test_battle2_n1_attack.py（w1 内）
覆盖：
- 三职业（战士/游侠/法师）× 多 seed × 三档目标防御（0/5/50）→ 45 场景
- 含暴击路径 + 幸运一击（lucky ×1.3）路径
- 新旧引擎同 seed 最终扣血一致（数值差 = 0）
"""
import os
import sys
import random

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
TEST_DB = os.path.join(PLUGIN_DIR, "test_battle2_n1.db")
os.environ.setdefault("GWEN_GAME_DB", TEST_DB)
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from game import engine as E          # noqa: E402
from game import battle as BT_OLD     # noqa: E402
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
        FAILURES.append(name)
        print(f"  ❌ {name} {detail}")


def make_monster(hp=100000, atk=10, name="测试怪", **kw):
    m = {
        "id": "t", "name": name, "lv": 5, "role": "normal",
        "hp": hp, "max_hp": hp, "atk": atk, "def": 5,
        "matk": 5, "mdef": 5, "spd": 5, "crit": 0.05,
        "exp": 10, "gold": 10, "skills": [], "drops": [],
        "map": "测试", "map_area": "vila", "is_boss": False, "is_elite": False,
    }
    m.update(kw)
    return m


def make_player(cls="战士", level=10, equip=None, skills=None):
    p = {
        "class_name": cls, "level": level, "equipment": equip or {}, "attributes": {},
        "class_tier": 0, "evolve_path": 1,
        "learned_skills": skills or [], "skills": skills or [],
        "skill_levels": {}, "mech_stacks": {},
        "max_hp": 0, "max_mp": 0, "hp": 0, "mp": 0, "name": "测试勇者",
        "gold": 100, "exp": 0, "cur_map": "oak_town",
    }
    st = E.player_final_stats(cls, level, equip or {}, 0, {}, 1)
    p["max_hp"], p["max_mp"] = st["max_hp"], st["max_mp"]
    p["hp"], p["mp"] = 99999, st["max_mp"]
    return p


def run_pair(seed, cls, level, mdef, label):
    """同 seed 同场景：旧引擎 vs 新引擎玩家普攻一次。返回 (旧扣血, 新扣血)。"""
    # ---- 旧引擎 ----
    random.seed(seed)
    p_old = make_player(cls, level)
    m_old = make_monster(**{"def": mdef}, hp=100000)
    b_old = BT_OLD.Battle("monster", m_old, player=p_old)
    hp0_old = m_old["hp"]
    logs_old, _, _ = b_old.actor_act("attack", None, p_old)
    dmg_old = hp0_old - m_old["hp"]
    # ---- 新引擎 ----
    random.seed(seed)
    st_new = E.player_final_stats(cls, level, {}, 0, {}, 1)
    m_new = make_actor(uid="e_0", name="测试怪", side="enemy", kind="monster",
                       hp=100000, max_hp=100000, atk=10, **{"def": mdef},
                       matk=5, mdef=5, spd=5, crit=0.05, level=5)
    p_actor = make_actor(uid="p_q1", name="测试勇者", side="player", kind="player",
                         human_controlled=True, class_name=cls, level=level,
                         hp=99999, max_hp=int(st_new["max_hp"]),
                         mp=int(st_new["max_mp"]), max_mp=int(st_new["max_mp"]),
                         equipment={}, skills=[], learned_skills=[], race=None,
                         evolve_path=1, class_tier=0, attributes={},
                         **{k: st_new[k] for k in ("atk", "matk", "def", "mdef", "spd", "crit") if k in st_new})
    b_new = BT_NEW(btype="monster", sides={"player": [p_actor], "enemy": [m_new]})
    hp0_new = m_new["hp"]
    logs_new, ended_new, who_new = b_new.human_act("attack", None, p_actor)
    dmg_new = hp0_new - m_new["hp"]
    return dmg_old, dmg_new, bool(logs_old), bool(logs_new), ended_new


def test_attack_matrix():
    print("【N1.1 普攻闭环数值对拍：三职业×5 seed×3 防御 = 45 场景】")
    total = 0
    ok = 0
    for seed in (1, 7, 42, 99, 123):
        for cls, lv in (("战士", 10), ("游侠", 15), ("法师", 20)):
            for mdef in (0, 5, 50):
                total += 1
                o, n, lo, ln, ended = run_pair(seed, cls, lv, mdef, f"场景{total}")
                if o == n:
                    ok += 1
                else:
                    FAILURES.append(f"攻击矩阵 seed={seed} {cls}{lv} def={mdef}: old={o} new={n}")
                    print(f"  ❌ seed={seed} {cls}{lv} def={mdef}: old={o} new={n}")
    global PASS, FAIL
    if ok == total:
        PASS += 1
        print(f"  ✅ 全部 {total} 场景数值一致")
    else:
        FAIL += 1
        print(f"  ❌ {ok}/{total} 一致")
    return ok == total


def test_battle_ends_on_kill():
    print("【N1.2 普攻打死怪 → 战斗结束（victory）】")
    st_new = E.player_final_stats("战士", 10, {}, 0, {}, 1)
    m_new = make_actor(uid="e_0", name="小怪", side="enemy", kind="monster",
                       hp=30, max_hp=30, atk=10, **{"def": 0},
                       matk=5, mdef=5, spd=5, crit=0.05, level=1)
    p_actor = make_actor(uid="p_q1", name="测试勇者", side="player", kind="player",
                         human_controlled=True, class_name="战士", level=10,
                         hp=99999, max_hp=330, mp=67, max_mp=67,
                         equipment={}, skills=[], learned_skills=[], race=None,
                         evolve_path=1, class_tier=0, attributes={},
                         **{k: st_new[k] for k in ("atk", "matk", "def", "mdef", "spd", "crit") if k in st_new})
    b_new = BT_NEW(btype="monster", sides={"player": [p_actor], "enemy": [m_new]})
    random.seed(1)
    logs, ended, who = b_new.human_act("attack", None, p_actor)
    check("战斗结束标记", ended)
    check("result = victory", b_new.result == "victory")
    check("击杀记录非空", len(b_new.killed_actors) == 1)
    check("怪 hp=0", m_new["hp"] == 0)


def test_battle_defeat_when_player_dies():
    print("【N1.3 玩家被打死 → 战斗结束（defeat）】")
    # 玩家 hp 很低，怪先手打玩家
    st_new = E.player_final_stats("法师", 5, {}, 0, {}, 1)
    m_new = make_actor(uid="e_0", name="强怪", side="enemy", kind="monster",
                       hp=100000, max_hp=100000, atk=500, **{"def": 5},
                       matk=500, mdef=5, spd=5, crit=0.05, level=10)
    p_actor = make_actor(uid="p_q1", name="测试勇者", side="player", kind="player",
                         human_controlled=True, class_name="法师", level=5,
                         hp=10, max_hp=10, mp=67, max_mp=67,
                         equipment={}, skills=[], learned_skills=[], race=None,
                         evolve_path=1, class_tier=0, attributes={},
                         **{k: st_new[k] for k in ("atk", "matk", "def", "mdef", "spd", "crit") if k in st_new})
    b_new = BT_NEW(btype="monster", sides={"player": [p_actor], "enemy": [m_new]})
    # 怪自动攻击玩家（actor_auto 走普攻）
    random.seed(1)
    logs, ended = b_new.actor_auto(m_new, ctx_target=p_actor)
    check("战斗结束标记", ended)
    check("result = defeat", b_new.result == "defeat")
    check("玩家 hp=0", p_actor["hp"] == 0)


def main():
    print("=== N1 battle2 普攻闭环测试 ===")
    test_attack_matrix()
    test_battle_ends_on_kill()
    test_battle_defeat_when_player_dies()
    print(f"\n=== 结果 PASS={PASS} FAIL={FAIL} ===")
    if FAILURES:
        print("失败明细:")
        for f in FAILURES:
            print(f"  - {f}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
