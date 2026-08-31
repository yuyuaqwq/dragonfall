# -*- coding: utf-8 -*-
"""审计 T1 独立验证脚本（只读，不碰生产库）：
① 真实回合流：暗影步(施放) → 终局·破影一击(下回合) 潜行 buff 是否存活 → 乘区是否可达
② 同回合注入潜行 → 乘区生效（对照，即 test_v1302f2 覆盖方式）
③ 潜行出手额外+1 影步：潜行技能出手 vs 非潜行出手 的资源增量对比
④ 暗影之舞(潜行暴伤+30%)被动在潜行技能出手时是否生效
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".."))  # noqa
_WD = os.path.dirname(os.path.abspath(__file__))
_DB = os.path.join(_WD, "audit_t1_private.db")
os.environ["GWEN_GAME_DB"] = _DB
os.environ["GWEN_TEST_MODE"] = "1"
# 复用测试脚手架（路径注入由 conftest 完成）
sys.path.insert(0, os.path.join(os.path.dirname(_WD), "tests"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(_WD)), "tests"))
os.environ.setdefault("GWEN_TEST_MODE", "1")

from unittest import mock
from conftest import E, BT, clean_db  # noqa: E402

R = BT.random


def make_enemy(hp=200000, atk=5):
    return {"name": "靶子", "hp": hp, "max_hp": hp, "atk": atk, "matk": 5,
            "def": 20, "mdef": 20, "spd": 1, "crit": 0.05}


def mk_player(cls, tier, path, learned=(), level=95, equipment=None):
    return {"class_name": cls, "class_tier": tier, "evolve_path": path, "level": level,
            "hp": 400, "max_hp": 400, "mp": 200, "max_mp": 200,
            "equipment": equipment or {}, "attributes": {}, "race": None,
            "learned_skills": list(learned), "name": "测试勇者"}


def new_battle(cls, tier, path, **pw):
    p = mk_player(cls, tier, path, **pw)
    b = BT.Battle("monster", make_enemy(), player=p)
    b.resources["shadow_step"] = 5
    return b, p


def deterministic(fn):
    with mock.patch.object(R, "random", return_value=0.99), \
            mock.patch.object(R, "uniform", return_value=0.0):
        return fn()


def main():
    clean_db()
    print("=== ① 真实回合流：暗影步施放后 buff 是否存活到下一回合 ===")
    b1, p1 = new_battle("cls_shadow_blade", 3, 3, learned=["暗影步", "终结·破影一击"])
    logs1 = deterministic(lambda: b1.player_turn("skill", "暗影步", p1)[0])
    stealth_after_cast = b1.p_buffs.get("stealth")
    print(f"  暗影步施放回合结束 logs[-1]={logs1[-1] if isinstance(logs1, list) and logs1 else '?'}")
    print(f"  施放后 p_buffs['stealth'] = {stealth_after_cast!r}  影步={b1.resources.get('shadow_step')}")
    h_before = b1.enemy["hp"]
    logs2 = deterministic(lambda: b1.player_turn("skill", "终结·破影一击", p1)[0])
    dmg_real = h_before - b1.enemy["hp"]
    stealth_used = b1.p_buffs.get("stealth")
    print(f"  下回合 破影一击 伤害={dmg_real}  logs[-1]={logs2[-1] if isinstance(logs2, list) and logs2 else '?'}")
    print(f"  攻击后 p_buffs['stealth'] = {stealth_used!r}")

    print("\n=== ② 同回合注入潜行（对照，test_v1302f2 覆盖方式）===")
    b2, p2 = new_battle("cls_shadow_blade", 3, 3, learned=["终结·破影一击"])
    b2.p_buffs["stealth"] = 1
    h2 = b2.enemy["hp"]
    logs_s = deterministic(lambda: b2._do_player_skill("终结·破影一击", p2))
    dmg_inject = h2 - b2.enemy["hp"]
    print(f"  注入潜行 破影一击 伤害={dmg_inject}  标签={'🌙潜行x1.5' in str(logs_s)}")

    print("\n=== ③ 潜行出手额外+1 影步（SHADOW_STEP_CFG.stealth_extra）===")
    # 幽影袭：满血必暴(mech=shadow) → on_crit +1；res_gain shadow_step +1；潜行出手应再 +1
    def step_gain(stealth):
        b3, p3 = new_battle("cls_shadow_blade", 1, 1, learned=["幽影袭"])
        b3.resources["shadow_step"] = 0
        if stealth:
            b3.p_buffs["stealth"] = 1
        deterministic(lambda: b3._do_player_skill("幽影袭", p3))
        return b3.resources["shadow_step"]
    g_ns = step_gain(False)
    g_s = step_gain(True)
    print(f"  非潜行 幽影袭 后影步={g_ns}  潜行 幽影袭 后影步={g_s}  (期望潜行=非潜行+1 若额外生效)")

    print("\n=== ④ 暗影之舞（潜行暴伤+30%）在潜行技能出手时是否生效 ===")
    def dmg_with_passive(learned):
        b4, p4 = new_battle("cls_shadow_blade", 3, 3, learned=learned)
        b4.p_buffs["stealth"] = 1
        b4.resources["shadow_step"] = 5
        h4 = b4.enemy["hp"]
        deterministic(lambda: b4._do_player_skill("终结·破影一击", p4))
        return h4 - b4.enemy["hp"]
    d_nop = dmg_with_passive(["终结·破影一击"])
    d_wp = dmg_with_passive(["终结·破影一击", "暗影之舞"])
    print(f"  无被动={d_nop}  有被动={d_wp}  (被动生效则应有明显差,期望后者+30%暴伤)")

    print("\n=== ⑤ 非潜行=1.0 无乘区（表外技能幽影袭 潜行出手不加乘）===")
    b5, p5 = new_battle("cls_shadow_blade", 1, 1, learned=["幽影袭"])
    h5 = b5.enemy["hp"]
    logs5 = deterministic(lambda: b5._do_player_skill("幽影袭", p5))
    print(f"  幽影袭(潜行而非表内) 伤害={h5 - b5.enemy['hp']}  无无🌙标签={'🌙潜行x' not in str(logs5)}")

    clean_db()
    sys.exit(0)


if __name__ == "__main__":
    main()