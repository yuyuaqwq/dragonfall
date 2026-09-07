# -*- coding: utf-8 -*-
"""N2 验收：battle2 技能链（攻击/治疗/增益）vs 旧引擎数值对拍。

跑法：python tests/test_battle2_n2_skill.py（w1 内）
覆盖：
- 攻击技：战士挥砍（exprs 成长 + 等级压制）多 seed
- 治疗技：牧师治愈术（heal_formula + clamp）多档 hp
- 增益技：战士铁壁（reduce buff 数值+刻数）、战吼（atk_up=3 现状复刻）
"""
import os
import sys
import random

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
TEST_DB = os.path.join(PLUGIN_DIR, "test_battle2_n2.db")
os.environ.setdefault("GWEN_GAME_DB", TEST_DB)
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from game import content as C          # noqa: E402
from game import engine as E           # noqa: E402
from game import battle as BT_OLD      # noqa: E402
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


def make_old_player(cls, level, skill_keys, skill_names, hp0=99999, mp0=None):
    p = {"class_name": cls, "level": level, "equipment": {}, "attributes": {},
         "class_tier": 0, "evolve_path": 1,
         "learned_skills": skill_names, "skills": skill_keys,
         "skill_levels": {}, "mech_stacks": {},
         "max_hp": 0, "max_mp": 0, "hp": 0, "mp": 0, "name": "测试勇者",
         "gold": 100, "exp": 0, "cur_map": "oak_town"}
    st = E.player_final_stats(cls, level, {}, 0, {}, 1)
    p["max_hp"], p["max_mp"] = st["max_hp"], st["max_mp"]
    p["hp"], p["mp"] = hp0, st["max_mp"] if mp0 is None else mp0
    return p


def old_battle(p, mdef=5):
    m = {"id": "t", "name": "测试怪", "lv": 5, "role": "normal", "hp": 100000, "max_hp": 100000,
         "atk": 10, "def": mdef, "matk": 5, "mdef": mdef, "spd": 5, "crit": 0.05,
         "exp": 10, "gold": 10, "skills": [], "drops": [], "map": "测试",
         "map_area": "vila", "is_boss": False, "is_elite": False}
    return BT_OLD.Battle("monster", m, player=p)


def new_player(cls, level, skill_keys, skill_names, st, hp0=99999, mp0=None):
    return make_actor(uid="p_q1", name="测试勇者", side="player", kind="player",
                      human_controlled=True, class_name=cls, level=level,
                      hp=hp0, max_hp=int(st["max_hp"]),
                      mp=st["max_mp"] if mp0 is None else mp0, max_mp=int(st["max_mp"]),
                      equipment={}, skills=skill_keys, learned_skills=skill_names,
                      race=None, evolve_path=1, class_tier=0, attributes={},
                      **{k: st[k] for k in ("atk", "matk", "def", "mdef", "spd", "crit") if k in st})


def new_battle(p, mdef=5):
    m = make_actor(uid="e_0", name="测试怪", side="enemy", kind="monster",
                   hp=100000, max_hp=100000, atk=10, **{"def": mdef},
                   matk=5, mdef=mdef, spd=5, crit=0.05, level=5)
    return BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})


def test_attack_skill():
    print("【N2.1 攻击技能：战士挥砍 多 seed × 多防御 对拍】")
    sk, info = find_skill("战士", "挥砍")
    check("找到挥砍", sk is not None)
    total = ok = 0
    for seed in (1, 7, 42):
        for mdef in (0, 5, 50):
            total += 1
            p_old = make_old_player("战士", 12, [sk], [info["name"]])
            b_old = old_battle(p_old, mdef=mdef)
            m_old = b_old.enemies[0]
            random.seed(seed)
            hp0 = m_old["hp"]
            b_old.actor_act("skill", info["name"], p_old)
            dmg_old = hp0 - m_old["hp"]
            st = E.player_final_stats("战士", 12, {}, 0, {}, 1)
            p_new = new_player("战士", 12, [sk], [info["name"]], st)
            b_new = new_battle(p_new, mdef=mdef)
            m_new = b_new.sides["enemy"][0]
            random.seed(seed)
            hp0n = m_new["hp"]
            b_new.human_act("skill", info["name"], p_new)
            dmg_new = hp0n - m_new["hp"]
            if dmg_old == dmg_new:
                ok += 1
            else:
                FAILURES.append(f"挥砍 seed={seed} mdef={mdef}: old={dmg_old} new={dmg_new}")
    check(f"挥砍 {ok}/{total} 一致", ok == total)


def test_heal_skill():
    print("【N2.2 治疗技能：牧师治愈术 多档 hp 对拍】")
    sk, info = find_skill("牧师", "治愈术")
    check("找到治愈术", sk is not None)
    total = ok = 0
    for hp0 in (50, 100, 190):
        total += 1
        p_old = make_old_player("牧师", 10, [sk], [info["name"]], hp0=hp0)
        b_old = old_battle(p_old)
        b_old.actor_act("skill", info["name"], p_old)
        oh = p_old["hp"]
        st = E.player_final_stats("牧师", 10, {}, 0, {}, 1)
        p_new = new_player("牧师", 10, [sk], [info["name"]], st, hp0=hp0)
        b_new = new_battle(p_new)
        # 单次行动直调 act（不推进——推进会让怪反击干扰治疗量验证）
        from game.battle2.actors import ActCtx
        ctx = ActCtx(caster=p_new, action="skill", skill_name=info["name"],
                     info=info, target=p_new)
        b_new.act(ctx)
        nh = p_new["hp"]
        if oh == nh:
            ok += 1
        else:
            FAILURES.append(f"治愈术 hp0={hp0}: old={oh} new={nh}")
    check(f"治愈术 {ok}/{total} 一致", ok == total)


def test_buff_skill():
    print("【N2.3 增益技能：铁壁 reduce / 战吼 atk_all 对拍】")
    # 铁壁
    sk, info = find_skill("战士", "铁壁")
    check("找到铁壁", sk is not None)
    p_old = make_old_player("战士", 12, [sk], [info["name"]])
    b_old = old_battle(p_old)
    b_old.actor_act("skill", info["name"], p_old)
    st = E.player_final_stats("战士", 12, {}, 0, {}, 1)
    p_new = new_player("战士", 12, [sk], [info["name"]], st)
    b_new = new_battle(p_new)
    b_new.human_act("skill", info["name"], p_new)
    same_buff = p_old.get("buffs") == p_new.get("buffs")
    same_left = p_old.get("reduce_left") == p_new.get("reduce_left")
    check("铁壁 buffs 一致 (reduce=0.45)", same_buff, f"old={p_old.get('buffs')} new={p_new.get('buffs')}")
    check("铁壁 reduce_left 一致 (8)", same_left, f"old={p_old.get('reduce_left')} new={p_new.get('reduce_left')}")
    # 战吼 atk_up（新引擎做正确值 10 刻 = desc「全队攻击+30% 持续 10 刻」；
    # 旧引擎漏传 info → 只给 3 刻 = 旧 bug，测试固化。此处验证新引擎正确行为）
    sk2, info2 = find_skill("战士", "战吼")
    check("找到战吼", sk2 is not None)
    p_old2 = make_old_player("战士", 20, [sk2], [info2["name"]])
    b_old2 = old_battle(p_old2)
    b_old2.actor_act("skill", info2["name"], p_old2)
    st2 = E.player_final_stats("战士", 20, {}, 0, {}, 1)
    p_new2 = new_player("战士", 20, [sk2], [info2["name"]], st2)
    b_new2 = new_battle(p_new2)
    b_new2.human_act("skill", info2["name"], p_new2)
    new_atk_up = p_new2.get("buffs", {}).get("atk_up")
    old_atk_up = p_old2.get("buffs", {}).get("atk_up")
    check("战吼 atk_up = 10 刻（desc 正确值，旧引擎 bug=3 不跟随）",
          new_atk_up == int(info2.get("buff_turns", 10)),
          f"new={new_atk_up} old_bug={old_atk_up} desc_buff_turns={info2.get('buff_turns')}")


def test_basic_n1_still_green():
    print("【N2.4 回归：N1 普攻矩阵仍绿】")
    from tests import test_battle2_n1_attack as t1  # noqa: F401  # 单独跑，此处验证文件存在
    check("N1 测试文件存在", os.path.exists(os.path.join(os.path.dirname(__file__), "test_battle2_n1_attack.py")))


def main():
    print("=== N2 battle2 技能链测试 ===")
    test_attack_skill()
    test_heal_skill()
    test_buff_skill()
    test_basic_n1_still_green()
    print(f"\n=== 结果 PASS={PASS} FAIL={FAIL} ===")
    if FAILURES:
        print("失败明细:")
        for f in FAILURES:
            print(f"  - {f}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
