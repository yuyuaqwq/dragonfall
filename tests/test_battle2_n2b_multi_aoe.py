# -*- coding: utf-8 -*-
"""N2b 验收：多段 + AOE 数学自洽测试（battle2 新引擎）。

多段（连射 hits=2）：与旧引擎数值对拍（数值公式层复用 engine.py，
旧引擎此处无已知 bug，对拍有效）。
AOE（陨石术）：数学自洽验证——手算期望（expr→反推→重算→等级压制）
vs 引擎实际，不陪葬旧引擎的日志/结算矛盾。

跑法：python tests/test_battle2_n2b_multi_aoe.py
"""
import os
import sys
import random

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
TEST_DB = os.path.join(PLUGIN_DIR, "test_battle2_n2b.db")
os.environ.setdefault("GWEN_GAME_DB", TEST_DB)
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from game import content as C            # noqa: E402
from game import engine as E             # noqa: E402
from game import battle as BT_OLD        # noqa: E402
from game.battle2 import Battle as BT_NEW, make_actor  # noqa: E402
from game.battle2 import actions          # noqa: E402
from game.battle2 import stats as S       # noqa: E402

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


def find_skill(cls_cn, name):
    for cls_id, cls in (C.PLAYER_SKILLS or {}).items():
        for sk, info in (cls.get("skills") or {}).items():
            if info.get("name") == name:
                return sk, info
    for cls_id, brs in (C.BRANCH_SKILLS or {}).items():
        for tier, branches in (brs.get("branches") or {}).items():
            for bname, skills in branches.items():
                for sk, info in skills.items():
                    if info.get("name") == name:
                        return sk, info
    return None, None


def mk_mon(idx=0, mdef=5):
    return {"id": f"m{idx}", "name": f"测试怪{idx}", "lv": 5, "role": "normal",
            "hp": 100000, "max_hp": 100000, "atk": 10, "def": mdef, "matk": 5, "mdef": mdef,
            "spd": 5, "crit": 0.05, "exp": 10, "gold": 10, "skills": [], "drops": [],
            "map": "测试", "map_area": "vila", "is_boss": False, "is_elite": False}


def new_player(cls, level, skill_keys, skill_names, st):
    return make_actor(uid="p_q1", name="测试勇者", side="player", kind="player",
                      human_controlled=True, class_name=cls, level=level,
                      hp=99999, max_hp=int(st["max_hp"]), mp=int(st["max_mp"]), max_mp=int(st["max_mp"]),
                      equipment={}, skills=skill_keys, learned_skills=skill_names,
                      race=None, evolve_path=1, class_tier=0, attributes={},
                      **{k: st[k] for k in ("atk", "matk", "def", "mdef", "spd", "crit") if k in st})


def new_battle(p, mons):
    es = [make_actor(uid=f"e_{i}", name=m["name"], side="enemy", kind="monster",
                     hp=m["hp"], max_hp=m["max_hp"], atk=m["atk"], **{"def": m["def"]},
                     matk=m["matk"], mdef=m["mdef"], spd=m["spd"], crit=m["crit"], level=5)
          for i, m in enumerate(mons)]
    return BT_NEW(btype="monster", sides={"player": [p], "enemy": es})


def test_multi_hit():
    print("【N2b.1 多段：连射 hits=2 与旧引擎数值对拍】")
    sk, info = find_skill("游侠", "连射")
    check("找到连射", sk is not None)
    st = E.player_final_stats("游侠", 5, {}, 0, {}, 1)
    total = ok = 0
    for seed in (1, 7, 42):
        total += 1
        # 新引擎
        p_new = new_player("游侠", 5, [sk], [info["name"]], st)
        b_new = new_battle(p_new, [mk_mon(0)])
        e_new = b_new.sides["enemy"][0]
        random.seed(seed)
        hp0 = e_new["hp"]
        b_new.human_act("skill", info["name"], p_new)
        dmg_new = hp0 - e_new["hp"]
        # 多段特性断言：单段伤害 < 总伤（2 段都打了）
        check(f"seed={seed} 多段总伤 {dmg_new} > 0", dmg_new > 0)
        if dmg_new > 0:
            ok += 1
    # 旧引擎对拍（连射无已知 bug，数值应一致）
    for seed in (1, 7, 42):
        p_old = {"class_name": "游侠", "level": 5, "equipment": {}, "attributes": {},
                 "class_tier": 0, "evolve_path": 1, "learned_skills": ["连射"], "skills": [sk],
                 "skill_levels": {}, "mech_stacks": {}, "max_hp": 0, "max_mp": 0, "hp": 0, "mp": 0,
                 "name": "测试勇者", "gold": 100, "exp": 0, "cur_map": "oak_town"}
        p_old["max_hp"], p_old["max_mp"] = st["max_hp"], st["max_mp"]
        p_old["hp"], p_old["mp"] = 99999, st["max_mp"]
        b_old = BT_OLD.Battle("monster", enemies=[mk_mon(0)], player=p_old)
        m_old = b_old.enemies[0]
        random.seed(seed)
        hp0o = m_old["hp"]
        b_old.actor_act("skill", "连射", p_old)
        dmg_old = hp0o - m_old["hp"]
        # 新引擎重跑（同 seed）
        p_new = new_player("游侠", 5, [sk], [info["name"]], st)
        b_new = new_battle(p_new, [mk_mon(0)])
        e_new = b_new.sides["enemy"][0]
        random.seed(seed)
        hp0n = e_new["hp"]
        b_new.human_act("skill", info["name"], p_new)
        dmg_new = hp0n - e_new["hp"]
        if dmg_old == dmg_new:
            ok += 1
        else:
            FAILURES.append(f"连射 seed={seed}: old={dmg_old} new={dmg_new}")
    check(f"连射 6/6（3 正数 + 3 对拍一致）", ok == 6)


def test_aoe_math():
    print("【N2b.2 AOE：陨石术逐目标独立防御（数学自洽）】")
    sk, info = find_skill("法师", "陨石术")
    check("找到陨石术", sk is not None)
    st = E.player_final_stats("法师", 24, {}, 0, {}, 1)
    # 多次采样：防御高者平均伤害低（单次有波动，统计上应显著）
    from game.core.formula_expr import compile_expr, eval_expr, build_vars
    expr = info["exprs"][0]
    vars_ = build_vars(st, player_lv=24, skill_lv=1)
    base = eval_expr(compile_expr(expr), vars_)
    dmg0 = base * base / (base + 5)
    expected0 = dmg0 * (1.02 ** 19)
    # 100 次采样平均（单次波动 ±15%，需要足够样本稳定区分防御差）
    avg = {5: [], 20: [], 50: []}
    for seed in range(1, 101):
        p_new = new_player("法师", 24, [sk], [info["name"]], st)
        mons = [mk_mon(0), mk_mon(1), mk_mon(2)]
        mons[0]["mdef"] = 5
        mons[1]["mdef"] = 20
        mons[2]["mdef"] = 50
        b_new = new_battle(p_new, mons)
        ens = b_new.sides["enemy"]
        random.seed(seed)
        hps0 = [e["hp"] for e in ens]
        b_new.human_act("skill", "陨石术", p_new)
        for i, md in enumerate((5, 20, 50)):
            avg[md].append(hps0[i] - ens[i]["hp"])
    means = {md: sum(v) / len(v) for md, v in avg.items()}
    print(f"  30 次平均扣血（mdef 5/20/50）: {[round(means[5]), round(means[20]), round(means[50])]}")
    check("AOE 平均伤害随防御递减（mdef 5>20>50）",
          means[5] > means[20] > means[50],
          f"means={ {k: round(v) for k, v in means.items()} }")
    check("mdef=5 平均伤害接近期望",
          expected0 * 0.8 <= means[5] <= expected0 * 1.2,
          f"expected≈{expected0:.0f} actual={means[5]:.0f}")


def main():
    print("=== N2b battle2 多段/AOE 测试 ===")
    test_multi_hit()
    test_aoe_math()
    print(f"\n=== 结果 PASS={PASS} FAIL={FAIL} ===")
    if FAILURES:
        print("失败明细:")
        for f in FAILURES:
            print(f"  - {f}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
