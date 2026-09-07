# -*- coding: utf-8 -*-
"""N3 验收：battle2 效果系统（effects.py）核心行为测试。

覆盖：
- debuff 叠层：burn/bleed/poison 写 target.debuffs（cap）
- 控制：stun/freeze/silence 写 target.buffs
- 资源叠层：zhan_yi/lian_duan/rage/chi 写 caster
- 攻击命中附加 mech 效果（挥砍 zhan_yi、带 burn 技能）
- 增益 effect 走单表（reduce/atk_up/shield_self/cleanse）

跑法：python tests/test_battle2_n3_effects.py
"""
import os
import sys
import random

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
TEST_DB = os.path.join(PLUGIN_DIR, "test_battle2_n3.db")
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
from game.battle2 import effects as FX    # noqa: E402
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


def make_actors(cls="战士", level=10, skill_keys=(), skill_names=()):
    st = E.player_final_stats(cls, level, {}, 0, {}, 1)
    p = make_actor(uid="p_q1", name="测试勇者", side="player", kind="player",
                   human_controlled=True, class_name=cls, level=level,
                   hp=99999, max_hp=int(st["max_hp"]), mp=int(st["max_mp"]), max_mp=int(st["max_mp"]),
                   equipment={}, skills=list(skill_keys), learned_skills=list(skill_names),
                   race=None, evolve_path=1, class_tier=0, attributes={},
                   **{k: st[k] for k in ("atk", "matk", "def", "mdef", "spd", "crit") if k in st})
    m = make_actor(uid="e_0", name="测试怪", side="enemy", kind="monster",
                   hp=100000, max_hp=100000, atk=10, **{"def": 5},
                   matk=5, mdef=5, spd=5, crit=0.05, lv=5)
    return p, m, st


def test_debuff_stack():
    print("【N3.1 状态叠层：burn/bleed/poison（on=target）cap 与写入 state】")
    b = BT_NEW(btype="monster", sides={"player": [], "enemy": []})
    caster = {"uid": "p", "name": "勇者", "state": {}, "buffs": {}}
    target = {"uid": "e", "name": "怪", "state": {}, "buffs": {}, "hp": 100, "max_hp": 100}
    logs = []
    # burn 叠 2 层（on=target → 写 target.state.burn）
    FX.apply_effects(b, caster, target,
                     [{"type": "state_add", "key": "burn", "amount": 2, "on": "target"}], logs)
    check("burn 写入 target.state", target["state"].get("burn") == 2,
          f"target.state={target['state']}")
    check("caster.state 无 burn", "burn" not in caster["state"])
    # burn 再叠 4 层 → cap 5（查声明表）
    FX.apply_effects(b, caster, target,
                     [{"type": "state_add", "key": "burn", "amount": 4, "on": "target"}], logs)
    check("burn cap 5", target["state"].get("burn") == 5, f"n={target['state'].get('burn')}")
    # bleed 叠 3
    FX.apply_effects(b, caster, target,
                     [{"type": "state_add", "key": "bleed", "amount": 3, "on": "target"}], logs)
    check("bleed 写入 state", target["state"].get("bleed") == 3)
    # 元素印记 on=target
    FX.apply_effects(b, caster, target,
                     [{"type": "state_add", "key": "fire_mark", "amount": 2, "on": "target"}], logs)
    check("fire_mark 写入 state", target["state"].get("fire_mark") == 2)


def test_control():
    print("【N3.2 控制：stun/freeze/silence 写入 target.buffs】")
    b = BT_NEW(btype="monster", sides={"player": [], "enemy": []})
    caster = {"uid": "p", "name": "勇者"}
    target = {"uid": "e", "name": "怪", "buffs": {}, "state": {}}
    logs = []
    FX.apply_effects(b, caster, target, [{"type": "stun", "turns": 3}], logs)
    check("stun 3 刻", target["buffs"].get("stun") == 3, f"stun={target['buffs'].get('stun')}")
    FX.apply_effects(b, caster, target, [{"type": "freeze", "turns": 1}], logs)
    check("freeze 1 刻", target["buffs"].get("freeze") == 1)
    FX.apply_effects(b, caster, target, [{"type": "silence", "turns": 2}], logs)
    check("silence 2 刻", target["buffs"].get("silence") == 2)
    # Boss 控制减半
    boss = {"uid": "boss", "name": "Boss", "is_boss": True, "buffs": {}, "state": {}}
    FX.apply_effects(b, caster, boss, [{"type": "stun", "turns": 4}], logs)
    check("Boss stun 减半 2 刻", boss["buffs"].get("stun") == 2, f"stun={boss['buffs'].get('stun')}")


def test_caster_stack():
    print("【N3.3 叠层：zhan_yi/rage/chi 写入 caster.state】")
    b = BT_NEW(btype="monster", sides={"player": [], "enemy": []})
    caster = {"uid": "p", "name": "勇者", "buffs": {}, "state": {}}
    logs = []
    FX.apply_effects(b, caster, None,
                     [{"type": "state_add", "key": "zhan_yi", "amount": 3, "on": "caster"}], logs)
    check("zhan_yi 3 层", caster["state"].get("zhan_yi") == 3)
    FX.apply_effects(b, caster, None,
                     [{"type": "state_add", "key": "zhan_yi", "amount": 9, "on": "caster"}], logs)
    check("zhan_yi cap 10", caster["state"].get("zhan_yi") == 10,
          f"n={caster['state'].get('zhan_yi')}")
    FX.apply_effects(b, caster, None,
                     [{"type": "state_add", "key": "rage", "amount": 4, "on": "caster"}], logs)
    check("rage 4", caster["state"].get("rage") == 4)
    FX.apply_effects(b, caster, None,
                     [{"type": "state_add", "key": "chi", "amount": 5, "on": "caster"}], logs)
    check("chi 5", caster["state"].get("chi") == 5)
    # 不足消费拦截（state_spend 需足额）
    FX.apply_effects(b, caster, None,
                     [{"type": "state_spend", "key": "zhan_yi", "amount": 50, "on": "caster"}], logs)
    check("zhan_yi 消费不足保留 10", caster["state"].get("zhan_yi") == 10)
    FX.apply_effects(b, caster, None,
                     [{"type": "state_spend", "key": "zhan_yi", "amount": 4, "on": "caster"}], logs)
    check("zhan_yi 消费 4 → 6", caster["state"].get("zhan_yi") == 6,
          f"n={caster['state'].get('zhan_yi')}")


def test_buff_effect_handler():
    print("【N3.4 增益 effect 单表：reduce/atk_all/shield_self/cleanse】")
    b = BT_NEW(btype="monster", sides={"player": [], "enemy": []})
    caster = {"uid": "p", "name": "勇者", "buffs": {}, "state": {},
              "shields": {}, "reduce_left": 0, "max_hp": 1000, "hp": 500}
    logs = []
    # reduce（mech_val=45 → 45%）
    FX.apply_effects(b, caster, caster,
                     [{"type": "reduce", "turns": 8, "mech_val": 45, "info": {}}], logs)
    check("reduce buffs=0.45", abs(caster["buffs"].get("reduce", 0) - 0.45) < 1e-9)
    check("reduce_left=8", caster.get("reduce_left") == 8)
    # atk_all → atk_up
    caster["buffs"].clear()
    FX.apply_effects(b, caster, caster, [{"type": "atk_all", "turns": 10}], logs)
    check("atk_all → atk_up=10", caster["buffs"].get("atk_up") == 10,
          f"buffs={caster['buffs']}")
    # shield_self
    FX.apply_effects(b, caster, caster,
                     [{"type": "shield_self", "mech_val": 300, "info": {"effect_val": 0}}], logs)
    check("shield_self 300", caster["shields"].get("buff", {}).get("value") == 300)
    # cleanse：先挂状态再净化（cleanse 清 state 减益键 + buffs 控制键）
    caster["state"]["burn"] = 2
    caster["buffs"]["stun"] = 1
    FX.apply_effects(b, caster, caster, [{"type": "cleanse", "turns": 0}], logs)
    check("cleanse 移除 burn", "burn" not in caster["state"])
    check("cleanse 移除 stun", "stun" not in caster["buffs"])


def test_mech_on_hit():
    print("【N3.5 攻击命中附加 mech：挥砍 zhan_yi / 带 mech 技能】")
    # 挥砍（mech=zhan_yi mech_val=1）→ 命中后 caster.state.zhan_yi+1
    sk, info = find_skill("战士", "挥砍")
    check("找到挥砍", sk is not None)
    p, m, st = make_actors("战士", 12, [sk], [info["name"]])
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    random.seed(1)
    b.human_act("skill", info["name"], p)
    zy = p.get("state", {}).get("zhan_yi", 0)
    check("挥砍命中后 zhan_yi ≥1", zy >= 1, f"zhan_yi={zy}")
    # 找带 burn mech 的攻击技能（龙息之怒 burn）
    sk2, info2 = find_skill("战士", "龙息之怒")
    if sk2 and info2.get("mech") == "burn":
        p2, m2, st2 = make_actors("战士", 70, [sk2], [info2["name"]])
        b2 = BT_NEW(btype="monster", sides={"player": [p2], "enemy": [m2]})
        random.seed(3)
        b2.human_act("skill", info2["name"], p2)
        burn = m2.get("state", {}).get("burn", 0)
        check("龙息之怒命中后目标 burn ≥1", burn >= 1, f"burn={burn}")
    else:
        print("  跳过：龙息之怒未找到（数据可能变动）")


def test_state_scale():
    print("【N3.6 声明折算：state_effects 表 stat_scale/dmg_mult 驱动面板与伤害】")
    # stat_scale：战意 5 层 → atk ×1.2
    b = BT_NEW(btype="monster", sides={"player": [], "enemy": []})
    actor = make_actor(uid="e1", name="测试单位", side="enemy", kind="monster",
                       atk=100, **{"def": 5}, matk=10, mdef=5, spd=5, crit=0.05)
    st0 = S.actor_stats(b, actor)
    check("无 state atk=100", st0["atk"] == 100, f"atk={st0['atk']}")
    actor["state"]["zhan_yi"] = 5
    st1 = S.actor_stats(b, actor)
    check("战意 5 层 atk ×1.2 = 120", st1["atk"] == 120, f"atk={st1['atk']}")
    # dmg_mult：rage 3 层 → _state_dmg_mult 1.36
    actor["state"]["rage"] = 3
    st2 = S.actor_stats(b, actor)
    check("rage 3 层 _state_dmg_mult=1.36",
          abs(float(st2.get("_state_dmg_mult", 1.0)) - 1.36) < 1e-9,
          f"mult={st2.get('_state_dmg_mult')}")
    # 伤害消费：无 state 打怪 vs rage 3 层打怪（同 seed 差值比例 ~1.36）
    def hit_dmg(p_atk, state_rage):
        mon = make_actor(uid="e0", name="靶", side="enemy", kind="monster",
                         hp=100000, max_hp=100000, atk=10, **{"def": 0},
                         matk=5, mdef=0, spd=5, crit=0.05, lv=1)
        p = make_actor(uid="p1", name="打手", side="player", kind="player",
                       human_controlled=True, class_name="战士", level=1,
                       hp=999, max_hp=999, mp=100, max_mp=100,
                       equipment={}, skills=[], learned_skills=[],
                       race=None, evolve_path=1, class_tier=0, attributes={},
                       atk=p_atk, matk=10, **{"def": 5}, mdef=5, spd=5, crit=0.0)
        if state_rage:
            p["state"]["rage"] = state_rage
        bb = BT_NEW(btype="monster", sides={"player": [p], "enemy": [mon]})
        random.seed(9)
        hp0 = mon["hp"]
        bb.human_act("attack", None, p)
        return hp0 - mon["hp"]
    d0 = hit_dmg(100, 0)
    d1 = hit_dmg(100, 3)
    check(f"普攻伤害 rage 3 层（{d1}）> 无层（{d0}）", d1 > d0, f"d0={d0} d1={d1}")


def main():
    print("=== N3 battle2 效果系统测试 ===")
    test_debuff_stack()
    test_control()
    test_caster_stack()
    test_buff_effect_handler()
    test_mech_on_hit()
    test_state_scale()
    print(f"\n=== 结果 PASS={PASS} FAIL={FAIL} ===")
    if FAILURES:
        print("失败明细:")
        for f in FAILURES:
            print(f"  - {f}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
