# -*- coding: utf-8 -*-
"""v83 Boss 机制增强（04 章 2.5）：shield/phase/stacks/reflect + 多机制组合"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, E, BT, Main, FakeEvent, run, clean_db, make_player

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, detail))


def mk_boss(mech, hp=1000, atk=50, lv=45, name="测试Boss"):
    """构造带 mech 的 Boss 字典（build_monster 同形）"""
    return {
        "id": "b_test", "name": name, "lv": lv, "role": "boss",
        "hp": hp, "max_hp": hp, "atk": atk, "def": 10, "matk": atk, "mdef": 10,
        "spd": 5, "exp": 100, "gold": 50, "skills": ["ms_an_ying_dan"],
        "drops": ["狼皮"], "map": "测试地图", "map_area": "test",
        "is_boss": True, "is_elite": False, "mech": mech, "mod": "测试",
    }


def mk_player():
    p = make_player("g1", "w1", "旅人", "战士", level=40)
    p["hp"] = p["max_hp"] = 5000
    p["mp"] = p["max_mp"] = 200
    return p


async def main():
    clean_db()
    m = Main(None)

    # ---- 1. 护盾 shield ----
    b = mk_boss("shield")
    b["boss_shield"] = int(b["max_hp"] * 0.20)
    bt = BT.Battle("monster", b, {}, player=mk_player())
    bt.e_buffs = {}
    dmg = bt._boss_dmg_filter(100, mk_player(), [])
    check("护盾期受伤减半", dmg == 50, str(dmg))
    check("护盾被吸收", bt.enemy["boss_shield"] == 200 - 50, str(bt.enemy.get("boss_shield")))
    # 破盾
    bt2 = BT.Battle("monster", mk_boss("shield"), {}, player=mk_player())
    bt2.enemy["boss_shield"] = 30
    logs = []
    dmg2 = bt2._boss_dmg_filter(100, mk_player(), logs)
    check("破盾后移除", "boss_shield" not in bt2.enemy and dmg2 == 50, f"dmg={dmg2} shield={bt2.enemy.get('boss_shield')}")
    check("破盾提示", any("护盾破碎" in x for x in logs), str(logs))
    # 护盾没了恢复全额伤害
    dmg3 = bt2._boss_dmg_filter(100, mk_player(), [])
    check("护盾消失后全额", dmg3 == 100, str(dmg3))

    # ---- 2. 多阶段 phase ----
    b = mk_boss("phase")
    bt = BT.Battle("monster", b, {}, player=mk_player())
    logs = []
    bt.round = 1
    bt._boss_mech(logs)
    check("满血不触发阶段", "phase_count" not in bt.enemy, str(bt.enemy.get("phase_count")))
    bt.enemy["hp"] = 400  # 40% < 50%
    bt._boss_mech(logs)
    check("半血进二阶段", bt.enemy.get("phase_count") == 1, str(bt.enemy.get("phase_count")))
    check("阶段提示", any("第 2 阶段" in x for x in logs), str(logs))
    est = bt._enemy_stats()
    check("阶段攻击+20%", est["atk"] == int(50 * 1.20), f"{est['atk']}")
    # 二阶段后再触发
    bt.enemy["hp"] = 120  # 12% < 25%
    bt._boss_mech(logs)
    check("再进三阶段", bt.enemy.get("phase_count") == 2, str(bt.enemy.get("phase_count")))
    est = bt._enemy_stats()
    check("三阶段攻击+40%", est["atk"] == int(50 * 1.40), f"{est['atk']}")

    # ---- 3. 叠层强化 stacks ----
    b = mk_boss("stacks")
    bt = BT.Battle("monster", b, {}, player=mk_player())
    logs = []
    for r in range(1, 7):
        bt.round = r
        bt._boss_mech(logs)
    check("每2回合+1层（6回合=3层）", bt.enemy.get("mech_stacks_n") == 3, str(bt.enemy.get("mech_stacks_n")))
    est = bt._enemy_stats()
    check("3层攻击+24%", est["atk"] == int(50 * 1.24), f"{est['atk']}")
    # 上限 5
    b = mk_boss("stacks")
    bt = BT.Battle("monster", b, {}, player=mk_player())
    for r in range(1, 13):
        bt.round = r
        bt._boss_mech([])
    check("叠层上限5", bt.enemy.get("mech_stacks_n") == 5, str(bt.enemy.get("mech_stacks_n")))

    # ---- 4. 龙鳞反伤 reflect ----
    b = mk_boss("reflect")
    b["hp"] = 200  # 20% < 25%
    bt = BT.Battle("monster", b, {}, player=mk_player())
    p = mk_player()
    logs = []
    dmg = bt._boss_dmg_filter(100, p, logs)
    check("反伤不改变伤害", dmg == 100, str(dmg))
    check("反伤15点", p["hp"] == 5000 - 15, str(p["hp"]))
    check("反伤提示", any("龙鳞反伤" in x for x in logs), str(logs))
    # 血量高于25%无反伤
    b2 = mk_boss("reflect")
    bt2 = BT.Battle("monster", b2, {}, player=mk_player())
    p2 = mk_player()
    bt2._boss_dmg_filter(100, p2, [])
    check("高血无反伤", p2["hp"] == 5000, str(p2["hp"]))

    # ---- 5. 组合机制（enrage,summon / phase 多段）----
    b = mk_boss("enrage,summon")
    bt = BT.Battle("monster", b, {}, player=mk_player())
    logs = []
    bt.enemy["hp"] = 200  # 20% 触发狂暴
    bt.round = 3
    bt._boss_mech(logs)
    check("组合触发狂暴", bt.enemy.get("enraged"), "")
    check("组合触发召唤", bt.enemy.get("summoned_round") == 3, str(bt.enemy.get("summoned_round")))

    # ---- 6. instances 数据完整性：22 副本 mech 全合法 ----
    legal = {"enrage", "summon", "heal", "shield", "phase", "stacks", "reflect"}
    bad = []
    for iid, inst in C.INSTANCES.items():
        mc = inst.get("mech", "")
        for x in mc.split(","):
            if x and x not in legal:
                bad.append((iid, x))
    check("22副本mech全合法", not bad, str(bad[:5]))
    multi = sum(1 for i in C.INSTANCES.values() if "," in i.get("mech", ""))
    check("组合机制副本数>=10", multi >= 10, str(multi))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
