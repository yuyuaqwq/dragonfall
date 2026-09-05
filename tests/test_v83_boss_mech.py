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

    # ---- 1. 护盾 shield（v177 actor 化：盾存 enemy["shields"]["boss"]={value,halve}）----
    b = mk_boss("shield")
    b.setdefault("shields", {})["boss"] = {"value": int(b["max_hp"] * 0.20), "halve": True}
    bt = BT.Battle("monster", b, {}, player=mk_player())
    dmg = bt._boss_dmg_filter(100, mk_player(), [])
    check("护盾期受伤减半", dmg == 50, str(dmg))
    _sb = bt.enemy.get("shields", {}).get("boss") or {}
    check("护盾被吸收", _sb.get("value") == 200 - 50, str(bt.enemy.get("shields")))
    # 破盾
    bt2 = BT.Battle("monster", mk_boss("shield"), {}, player=mk_player())
    bt2.enemy.setdefault("shields", {})["boss"] = {"value": 30, "halve": True}
    logs = []
    dmg2 = bt2._boss_dmg_filter(100, mk_player(), logs)
    check("破盾后移除", not bt2.enemy.get("shields") and dmg2 == 50,
          f"dmg={dmg2} shields={bt2.enemy.get('shields')}")
    check("破盾提示", any("护盾破碎" in x for x in logs), str(logs))
    # 护盾没了恢复全额伤害
    dmg3 = bt2._boss_dmg_filter(100, mk_player(), [])
    check("护盾消失后全额", dmg3 == 100, str(dmg3))

    # ---- 2. 多阶段 phase ----
    b = mk_boss("phase")
    bt = BT.Battle("monster", b, {}, player=mk_player())
    logs = []
    bt._now = 0.0  # v152：round 1 → 首回合
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
        bt._now = r * 1.0  # v152：round r → 绝对时刻 r×1.0（1刻=1秒）
        bt._boss_mech(logs)
    check("每2回合+1层（6回合=3层）", bt.enemy.get("mech_stacks_n") == 3, str(bt.enemy.get("mech_stacks_n")))
    est = bt._enemy_stats()
    check("3层攻击+24%", est["atk"] == int(50 * 1.24), f"{est['atk']}")
    # 上限 5
    b = mk_boss("stacks")
    bt = BT.Battle("monster", b, {}, player=mk_player())
    for r in range(1, 13):
        bt._now = r * 1.0  # v152：round r → 绝对时刻 r×1.0（1刻=1秒）
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
    # v152：r 从绝对时刻换算（r = now/ACT_TICK + 1，测试 ACT_TICK=1）；v163：summon CD=5 → r=5（now=4）触发，r=6（now=5）不重复
    bt._now = 3 * 1.0
    bt._boss_mech(logs)
    check("组合触发狂暴", bt.enemy.get("enraged"), "")
    check("r=4 未到召唤 CD（summoned_round 空）", not bt.enemy.get("summoned_round"),
          str(bt.enemy.get("summoned_round")))
    bt._now = 4 * 1.0
    bt._boss_mech(logs)
    check("组合触发召唤（summoned_round=5）", bt.enemy.get("summoned_round") == 5,
          str(bt.enemy.get("summoned_round")))
    logs3 = []
    bt._now = 5 * 1.0
    bt._boss_mech(logs3)
    check("召唤幂等（r=6 不重复）", bt.enemy.get("summoned_round") == 5,
          f"{logs3} summoned_round={bt.enemy.get('summoned_round')}")

    # ---- 6. instances 数据完整性：22 副本 mech 全合法 ----
    # v180：reflect 是被动（不在 BOSS_MECHS 注册表）；v116+ 新增 phase_open/player_low/pv_broken
    legal = {"enrage", "summon", "heal", "shield", "phase", "stacks", "reflect",
             "phase_open", "player_low", "pv_broken"}
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
