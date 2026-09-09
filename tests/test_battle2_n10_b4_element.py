# -*- coding: utf-8 -*-
"""N10-B4：element 元素伤害免疫/弱点消费（v178 E5 数据驱动）+ 玩家技能 element 标签。

跑法：python tests/test_battle2_n10_b4_element.py（w1 内）
"""
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "test_b2_n10b4.db"))
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from game.battle2 import config as _b2c
_b2c.load_game_defaults()
from game.battle2 import Battle as B2, make_actor  # noqa: E402
from game.battle2 import landing as L  # noqa: E402
from game.battle2 import actions as A  # noqa: E402
from game.battle2.actors import ActCtx  # noqa: E402

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


def mk_mage():
    p = make_actor(uid="p1", name="元素法师", side="player", kind="player",
                   human_controlled=True, class_name="cls_fa_shi", level=20,
                   hp=3000, max_hp=3000, mp=500, max_mp=500,
                   atk=30, matk=200, spd=15, crit=0.0,
                   equipment={}, skills=[], learned_skills=["火球术"],
                   race=None, evolve_path=0, class_tier=0, attributes={},
                   **{"def": 30, "mdef": 30})
    return p


def mk_enemy(hp=99999, name="测试怪", **kw):
    e = make_actor(uid="e1", name=name, side="enemy", kind="monster",
                   hp=hp, max_hp=hp, atk=1, matk=1, spd=5, crit=0.0,
                   level=20, exp=0, gold=0, **{"def": 5, "mdef": 5}, **kw)
    return e


def fireball_info():
    # 火球术真实技能数据（kind=魔法·火 element=fire，N10-B4 补键）
    from game.data.skills import PLAYER_SKILLS
    for cid, cdata in (PLAYER_SKILLS or {}).items():
        for sid, sk in (cdata.get("skills") or {}).items():
            if str((sk or {}).get("name")) == "火球术":
                return dict(sk)
    return {"kind": "魔法·火", "element": "fire", "exprs": ["matk*1.6"]}


def test_fireball_carries_element():
    print("【1. 火球术数据带 element=fire】")
    info = fireball_info()
    check("火球术 element=fire", info.get("element") == "fire", f"element={info.get('element')}")


def test_weak_multiplier():
    print("【2. 弱点 fire×1.5 → 伤害 ≈1.5×】")
    # 对照怪（无 weak）
    p1 = mk_mage()
    e_no = mk_enemy(hp=99999)
    b1 = B2(btype="monster", sides={"player": [p1], "enemy": [e_no]})
    A.do_skill(b1, ActCtx(caster=p1, action="skill", skill_name="火球术",
                          info=fireball_info(), target=e_no))
    dmg_no = 99999 - e_no["hp"]
    # 冰霜领主（weak fire×1.5）
    p2 = mk_mage()
    e_wk = mk_enemy(hp=99999, element_weak={"fire": 1.5})
    b2 = B2(btype="monster", sides={"player": [p2], "enemy": [e_wk]})
    A.do_skill(b2, ActCtx(caster=p2, action="skill", skill_name="火球术",
                          info=fireball_info(), target=e_wk))
    dmg_wk = 99999 - e_wk["hp"]
    check("弱点怪受伤更多", dmg_wk > dmg_no, f"no={dmg_no} wk={dmg_wk}")
    check("弱点 ≈1.5×", 1.3 * dmg_no <= dmg_wk <= 1.7 * dmg_no, f"no={dmg_no} wk={dmg_wk} ratio={dmg_wk/dmg_no:.2f}")


def test_immune_zero():
    print("【3. 免疫 fire → 伤害 0】")
    p = mk_mage()
    e = mk_enemy(hp=99999, element_immune=["fire"])
    b = B2(btype="monster", sides={"player": [p], "enemy": [e]})
    logs = []
    A.do_skill(b, ActCtx(caster=p, action="skill", skill_name="火球术",
                         info=fireball_info(), target=e))
    check("免疫怪 0 伤害", e["hp"] == 99999, f"hp={e['hp']}")


def test_no_element_noop():
    print("【4. 无元素普攻打 immune/weak 怪 → 零行为】")
    p = mk_mage()
    e = mk_enemy(hp=99999, element_weak={"fire": 1.5}, element_immune=["fire"])
    b = B2(btype="monster", sides={"player": [p], "enemy": [e]})
    # 普攻（basic_skill 无 element）
    A.do_attack(b, ActCtx(caster=p, action="attack", target=e))
    lost = 99999 - e["hp"]
    check("普攻正常扣血且不乘 weak", 50 < lost < 500, f"lost={lost}")


def test_aoe_per_target():
    print("【5. AOE 逐目标独立免疫/弱点】")
    p = mk_mage()
    e_imm = mk_enemy(hp=99999, element_immune=["fire"], name="免疫怪")
    e_wk = mk_enemy(hp=99999, element_weak={"fire": 1.5}, name="弱火怪")
    b = B2(btype="monster", sides={"player": [p], "enemy": [e_imm, e_wk]})
    info = dict(fireball_info())
    info["aoe"] = "all"
    A.do_skill(b, ActCtx(caster=p, action="skill", skill_name="火球术", info=info, target=e_imm))
    check("AOE 免疫目标 0 伤", e_imm["hp"] == 99999, f"hp={e_imm['hp']}")
    check("AOE 弱火目标受伤", e_wk["hp"] < 99999, f"hp={e_wk['hp']}")


def test_holy_weak():
    print("【6. 非 ELEMENT_MARKS 系（holy）同样消费——蚀夜真相形态】")
    p = mk_mage()
    # 造一个 holy 技能（数据无 holy 玩家技能，直接 landing 层验证）
    e = mk_enemy(hp=99999, element_weak={"holy": 1.15})
    b = B2(btype="monster", sides={"player": [p], "enemy": [e]})
    dmg0 = L.deal_damage(b, p, e, 100, [], dmg_kind="magi", element="holy")
    check("holy 弱点 ×1.15", 110 <= 100000 - e["hp"] <= 120, f"hp={e['hp']} dmg0={dmg0}")


if __name__ == "__main__":
    test_fireball_carries_element()
    test_weak_multiplier()
    test_immune_zero()
    test_no_element_noop()
    test_aoe_per_target()
    test_holy_weak()
    print(f"\n== 结果：通过 {PASS} / 共 {PASS + FAIL} ==")
    if FAILURES:
        for f in FAILURES:
            print("  FAIL:", f)
        sys.exit(1)
    print("全绿 ✅")
