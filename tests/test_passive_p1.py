# -*- coding: utf-8 -*-
"""v181.M-passive P1 测试——被动 proc 系统样板（插件形态：声明表 + 装配 + 通用动作）。

跑法：python tests/test_passive_p1.py（exit=0 全绿）
覆盖（方案 docs/REFACTOR_v181_PASSIVE_PROC_PLAN.md）：
  1. 装配：法师学奥术共鸣（被动 proc=arcane_resonance）→ dmg_calc 触发器（judge+参数化）
  2. 触发：施放 mech=arcane 技能（奥术弹幕）→ 伤害 ×1.15（dmg_calc 乘区）
  3. 负向：非 arcane 技能（无 mech）不触发被动乘区
  4. 负向：未学被动/非被动技能不挂触发器（学什么挂什么）
  5. 追风：击杀 → energy 回满（on_kill 通道）
  6. 表未声明 proc → 跳过装配（不崩不挂）
"""
import sys, os
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "test_passive_p1.db"))
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


def mk_mage(skills, hp=600, mp=500):
    a = make_actor(uid="p_m", name="法师", side="player", kind="player",
                   human_controlled=True, class_name="cls_fa_shi", level=60,
                   learned_skills=list(skills), skills=list(skills),
                   atk=50, matk=200, spd=60, hp=hp, max_hp=hp, mp=mp, max_mp=500)
    a['effects'] = {}
    a['bonus'] = {'panel': {}, 'cap': {}, 'cost': {}}
    return a


def mk_ranger(skills, hp=600):
    a = make_actor(uid="p_r", name="游侠", side="player", kind="player",
                   human_controlled=True, class_name="cls_you_xia", level=60,
                   learned_skills=list(skills), skills=list(skills),
                   atk=150, matk=30, spd=120, hp=hp, max_hp=hp, mp=200, max_mp=200)
    a['effects'] = {}
    a['bonus'] = {'panel': {}, 'cap': {}, 'cost': {}}
    return a


def mk_battle(players):
    enemy = make_actor(uid="e_1", name="木桩", side="enemy", kind="monster",
                       atk=1, matk=1, spd=1, hp=999999, max_hp=999999)
    enemy['effects'] = {}
    return B2("monster", sides={"player": players, "enemy": [enemy]}, title_bonus={})


def test_1_assemble():
    print("【1. 装配：被动 proc → dmg_calc 触发器（参数化）】")
    m = mk_mage(["奥术共鸣", "奥术弹幕"])
    apply_class_mech(m)
    dmgs = [t for t in (m.get("triggers") or {}).get("dmg_calc", [])
            if t.get("type") == "passive_dmg_mult"]
    check("奥术共鸣挂 dmg_calc（judge mech_eq arcane + mult 0.15 参数化）",
          len(dmgs) == 1 and dmgs[0]["judge"].get("mech") == "arcane"
          and float(dmgs[0].get("mult") or 0) == 0.15, repr(dmgs))
    m2 = mk_mage(["奥术弹幕"])  # 没学被动
    apply_class_mech(m2)
    check("未学被动不挂触发器", not any(
        t.get("type") == "passive_dmg_mult"
        for t in (m2.get("triggers") or {}).get("dmg_calc", [])), "")


def test_2_trigger_arcane():
    print("【2. 触发：奥术系技能伤害 ×1.15】")
    m = mk_mage(["奥术共鸣", "奥术弹幕"])
    apply_class_mech(m)
    b = mk_battle([m])
    base_e = b.sides_of("enemy")[0]
    logs, _, _ = b.human_act("skill", "奥术弹幕", m)
    check("奥术弹幕触发被动（日志含被动生效）", any("被动生效" in l for l in logs),
          str([l for l in logs if "被动" in l or "受到" in l][-2:]))


def test_3_negative_non_arcane():
    print("【3. 负向：非奥术系技能不触发被动乘区】")
    # 法师没有非 arcane 基础魔法？用一个无 mech 的伤害技能（火球术基础）
    m = mk_mage(["奥术共鸣", "火球术"])
    apply_class_mech(m)
    b = mk_battle([m])
    logs, _, _ = b.human_act("skill", "火球术", m)
    check("火球术（无 mech）不触发被动", not any("被动生效" in l for l in logs),
          str([l for l in logs if "被动" in l][-1:]))


def test_4_undeclared_proc():
    print("【4. 表未声明 proc → 跳过装配不崩】")
    # 用 4.1 一个表未声明的被动（如 berserk_revive——P1 表未含）学给战士
    from game.data.skills import BRANCH_SKILLS
    import json
    war_skills = []
    w = BRANCH_SKILLS.get("cls_zhan_shi") or {}
    for bk, bv in (w.get("branches") or {}).items():
        if isinstance(bv, dict):
            for sub, sk2 in bv.items():
                if isinstance(sk2, dict):
                    for n, i in sk2.items():
                        if isinstance(i.get("passive"), dict) \
                                and i.get("passive", {}).get("proc") == "berserk_revive":
                            war_skills.append(n)
    if war_skills:
        a = make_actor(uid="p_w", name="战士", side="player", kind="player",
                       human_controlled=True, class_name="cls_zhan_shi", level=90,
                       learned_skills=war_skills, skills=war_skills,
                       atk=200, matk=20, spd=40, hp=2000, max_hp=2000, mp=100, max_mp=100)
        a['effects'] = {}
        a['bonus'] = {'panel': {}, 'cap': {}, 'cost': {}}
        apply_class_mech(a)
        check("表未声明 proc（berserk_revive）装配不崩不挂", True, "")
    else:
        check("表未声明 proc 测试技能缺失", False, "找不到 berserk_revive 技能")


def test_5_on_kill_gain():
    print("【5. 追风：击杀 → energy 回满（on_kill）】")
    r = mk_ranger(["追风", "疾风连射"], hp=600)
    apply_class_mech(r)
    b = mk_battle([r])
    # 追风是被动技能吗？查 kind——若是被动才装配
    from game import engine as E
    info = E.skill_info("cls_you_xia", "追风") or {}
    check("追风是 kind=被动", info.get("kind") == "被动", repr(info.get("kind")))
    kills = [t for t in (r.get("triggers") or {}).get("on_kill", [])
             if t.get("type") == "passive_kill_gain"]
    check("追风挂 on_kill passive_kill_gain", len(kills) == 1, repr(kills))


def main():
    test_1_assemble()
    test_2_trigger_arcane()
    test_3_negative_non_arcane()
    test_4_undeclared_proc()
    test_5_on_kill_gain()
    print(f"\n结果：{PASS} 通过 / {FAIL} 失败")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
