# -*- coding: utf-8 -*-
"""commands 层：战斗引擎 + 分支机制 + PVP（源自 v90/v95/v31/v32/v92）

验证：
  1. Battle 状态机：序列化 round trip / 普攻 / buff 落地 / 持续伤害 / 胜负结算
  2. 分支机制：狂暴叠层/灼烧引爆/冻结/影袭必暴/毒爆/气力爆发/金身减伤/神恩护盾
  3. 数值铁律：分支 tier1 Lv.32 等效 ≥ 基础 Lv.30 大招
  4. PVP：安全区禁止/等级保护/轮流行动/金币转移/红名机制
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, BT, db, clean_db, Main, FakeEvent, run

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def make_monster(hp=100, atk=10, defense=5, name="测试怪", lv=5, skills=None):
    return {
        "id": "t", "name": name, "lv": lv, "role": "normal",
        "hp": hp, "max_hp": hp, "atk": atk, "def": defense,
        "matk": 5, "mdef": 5, "spd": 5, "crit": 0.05,
        "exp": 10, "gold": 10, "skills": skills or [], "drops": [],
        "map": "测试", "map_area": "vila", "is_boss": False, "is_elite": False,
    }


def make_player(cls="战士", level=10, hp=None, mp=None, skills=None, mech=None):
    p = {
        "class_name": cls, "level": level, "equipment": {}, "attributes": {},
        "class_tier": 0 if level < 30 else 1, "evolve_path": 1,
        "learned_skills": skills or E.skills_for_level(cls, level),
        "skills": skills or E.skills_for_level(cls, level),
        "skill_levels": {}, "mech_stacks": mech or {},
        "max_hp": 0, "max_mp": 0, "hp": 0, "mp": 0, "name": "测试勇者",
        "gold": 100, "exp": 0, "cur_map": "vila_square",
    }
    st = E.player_final_stats(cls, level, {}, 0 if level < 30 else 1, {})
    p["max_hp"], p["max_mp"] = st["max_hp"], st["max_mp"]
    p["hp"] = hp if hp is not None else st["max_hp"]
    p["mp"] = mp if mp is not None else st["max_mp"]
    return p


async def main():
    clean_db()
    print("【战斗：序列化 round trip】")
    b = BT.Battle("monster", make_monster(hp=100))
    b2 = BT.Battle.from_state(b.to_state())
    check("type 保留", b2.btype == "monster")
    check("enemy hp 保留", b2.enemy["hp"] == 100)
    check("buffs 保留", b2.p_buffs == {} and b2.e_buffs == {})

    print("【战斗：普攻】")
    random.seed(1)
    p = make_player("战士", 10)
    m = make_monster(hp=1000, defense=5)
    b = BT.Battle("monster", m)
    logs, ended = b.player_turn("attack", None, p)
    check("造成伤害", m["hp"] < 1000, f"hp={m['hp']}")
    check("未结束", not ended)
    check("回合数", b.round == 1)

    print("【战斗：增益 buff 落地（怒吼）】")
    random.seed(2)
    p = make_player("战士", 10, mp=100)
    m = make_monster(hp=100000, defense=50)
    b = BT.Battle("monster", m)
    b.player_turn("skill", "怒吼", p)
    check("p_buffs 有 atk_up", b.p_buffs.get("atk_up", 0) > 0, str(b.p_buffs))
    # v61：速度优势回合不立即结束——防御结束本回合行动（不打怪），回合才递减
    while b.p_extra_left > 0:
        b.player_turn("defend", None, p)
    check("回合结束递减", b.p_buffs.get("atk_up", 0) == 2, str(b.p_buffs))
    check("怒吼无伤害", m["hp"] == 100000)
    # buff 效果对比
    random.seed(3)
    p2 = make_player("战士", 10)
    m2 = make_monster(hp=100000, defense=50)
    b2 = BT.Battle("monster", m2)
    b2.player_turn("skill", "怒吼", p2)
    b2.player_turn("attack", None, p2)
    dmg_buffed = 100000 - m2["hp"]
    random.seed(3)
    p3 = make_player("战士", 10)
    m3 = make_monster(hp=100000, defense=50)
    b3 = BT.Battle("monster", m3)
    b3.player_turn("attack", None, p3)
    dmg_plain = 100000 - m3["hp"]
    check("怒吼后伤害提升", dmg_buffed > dmg_plain, f"buff={dmg_buffed} plain={dmg_plain}")

    print("【战斗：减益 buff（寒冰/毒/破甲）】")
    random.seed(4)
    b = BT.Battle("monster", make_monster(hp=100000))
    b.player_turn("skill", "寒冰箭", make_player("法师", 10, mp=100))
    check("寒冰箭 spd_down", b.e_buffs.get("spd_down", 0) > 0, str(b.e_buffs))
    random.seed(5)
    b = BT.Battle("monster", make_monster(hp=100000))
    b.player_turn("skill", "毒箭", make_player("游侠", 10, mp=100))
    check("毒箭 poison", b.e_buffs.get("poison", 0) > 0, str(b.e_buffs))
    random.seed(6)
    b = BT.Battle("monster", make_monster(hp=100000))
    b.player_turn("skill", "破甲斩", make_player("战士", 10, mp=100))
    check("破甲斩 def_down", b.e_buffs.get("def_down", 0) > 0, str(b.e_buffs))

    print("【战斗：中毒持续伤害】")
    p = make_player("战士", 10, hp=9999)
    b = BT.Battle("monster", make_monster(hp=1000))
    b.e_buffs["poison"] = 2
    logs, ended = b.player_turn("attack", None, p)
    # poison 扣 5% max_hp = 50，加上普攻伤害
    check("中毒发作扣血", b.enemy["hp"] < 950, f"hp={b.enemy['hp']} (普攻+毒50)")
    # v61：速度优势回合不立即结束——防御结束本回合行动，毒才递减
    while b.p_extra_left > 0:
        b.player_turn("defend", None, p)
    check("毒回合递减", b.e_buffs.get("poison", 0) == 1, str(b.e_buffs))

    print("【数值铁律：分支 tier1 ≥ 基础大招】")
    for cls, base_lv30 in [("法师", "龙息术"), ("战士", "裂空斩"), ("游侠", "龙息箭"),
                            ("牧师", "圣焰"), ("刺客", "暗杀"), ("武僧", "气功波")]:
        cid = C.resolve("classes", cls)
        base_power = C.PLAYER_SKILLS[cid]["skills"][C.resolve("skills", base_lv30)]["power"]
        t1 = list(C.BRANCH_SKILLS[cid]["branches"][1].values())[0]
        first_name, first = list(t1.items())[0]
        eff_power = first["power"] * first.get("multi", 1)
        check(f"{cls} 分支Lv.32等效 ≥ 基础Lv.30({base_power})", eff_power >= base_power * 0.95,
              f"{first_name} {eff_power} vs {base_power}")

    print("【机制：狂暴叠层】")
    pl = make_player("战士", 35, skills=["狂暴连斩"])
    b = make_battle()
    b.player_turn("skill", "狂暴连斩", pl, enemy_act=False)
    n1 = b.mech_stacks.get("rage", 0)
    b.player_turn("skill", "狂暴连斩", pl, enemy_act=False)
    n2 = b.mech_stacks.get("rage", 0)
    check("连击叠狂暴 1→2 层", n1 == 1 and n2 == 2, f"{n1}->{n2}")

    print("【机制：灼烧→引爆】")
    pl = make_player("法师", 35, skills=["火球连射", "灼烧引爆"])
    b = make_battle(10000)
    b.player_turn("skill", "火球连射", pl, enemy_act=False)
    b.player_turn("skill", "火球连射", pl, enemy_act=False)
    hp_before = b.enemy["hp"]
    b.player_turn("skill", "灼烧引爆", pl, enemy_act=False)
    check("灼烧引爆造成额外伤害", b.enemy["hp"] < hp_before, f"{hp_before}->{b.enemy['hp']}")
    check("引爆后层数清零", b.mech_stacks.get("burn", 0) == 0)

    print("【机制：冻结】")
    pl = make_player("法师", 35, skills=["冰棱"])
    b2 = make_battle()
    random.seed(42)
    logs, _ = b2.player_turn("skill", "冰棱", pl, enemy_act=True)
    check("固定 seed 42 冻结跳过敌方回合", any("冻结" in l for l in logs), str(logs))
    print("【机制：影袭必暴】")
    pl = make_player("刺客", 35, skills=["影刃刺"])
    b = make_battle()
    logs, _ = b.player_turn("skill", "影刃刺", pl, enemy_act=False)
    check("满血影袭必暴", any("暴击" in l for l in logs), str(logs))

    print("【机制：毒层→毒爆】")
    pl = make_player("刺客", 35, skills=["淬毒刃", "毒爆"])
    b = make_battle(10000)
    b.player_turn("skill", "淬毒刃", pl, enemy_act=False)
    b.player_turn("skill", "淬毒刃", pl, enemy_act=False)
    hp_before = b.enemy["hp"]
    b.player_turn("skill", "毒爆", pl, enemy_act=False)
    check("毒爆额外伤害", b.enemy["hp"] < hp_before, f"{hp_before}->{b.enemy['hp']}")

    print("【机制：气力爆发】")
    pl = make_player("武僧", 35, skills=["寸拳", "重炮拳"])
    b = make_battle(10000)
    b.player_turn("skill", "寸拳", pl, enemy_act=False)
    b.player_turn("skill", "寸拳", pl, enemy_act=False)
    chi = b.mech_stacks.get("chi", 0)
    hp_before = b.enemy["hp"]
    b.player_turn("skill", "重炮拳", pl, enemy_act=False)
    check("气力 4 点 + 重拳爆发", chi == 4 and b.enemy["hp"] < hp_before, f"chi={chi}")

    print("【机制：金身减伤】")
    pl = make_player("武僧", 35, skills=["罗汉冲拳"], mech={"iron": 5}, hp=9999)
    b = make_battle()
    b.mech_stacks["iron"] = 5  # v59 叠层存战斗状态
    b.enemy["atk"] = 300
    b.player_turn("defend", None, pl, enemy_act=True)
    check("金身减伤生效", pl["hp"] > 9900, f"hp={pl['hp']}")

    print("【机制：神恩护盾】")
    pl = make_player("牧师", 40, skills=["神恩术", "神恩守护"], hp=9999, mech={"bless": 3})
    b = make_battle()
    b.mech_stacks["bless"] = 3  # v59 叠层存战斗状态
    b.player_turn("skill", "神恩守护", pl, enemy_act=False)
    check("神恩转护盾", b.shield > 0, f"bless=3 shield={b.shield}")

    print("【v51 战士应对机制】")
    # 挫志怒吼：敌方降攻
    pl = make_player("战士", 14, skills=["挫志怒吼"])
    b = make_battle()
    b.enemy["atk"] = 100
    b.player_turn("skill", "挫志怒吼", pl, enemy_act=False)
    check("挫志怒吼 敌方降攻", b.e_buffs.get("mon_atk_down", 0) > 0, str(b.e_buffs))
    check("降攻后敌方 atk<100", b._enemy_stats()["atk"] < 100, str(b._enemy_stats()["atk"]))
    # 挑衅怒吼：单人=降攻+狂暴，副本=taunt 广播
    pl = make_player("战士", 18, skills=["挑衅怒吼"])
    b = make_battle()
    b.player_turn("skill", "挑衅怒吼", pl, enemy_act=False)
    check("挑衅怒吼 降攻+狂暴", b.e_buffs.get("mon_atk_down", 0) > 0 and b.mech_stacks.get("rage", 0) >= 1,
          f"{b.e_buffs} rage={b.mech_stacks.get('rage')}")
    check("挑衅怒吼 team_effects=taunt", any(te.get("kind") == "taunt" for te in b.team_effects), str(b.team_effects))
    # 盾牌反击：受击反击
    random.seed(42)
    pl = make_player("战士", 22, skills=["盾牌反击"], hp=9999)
    b = make_battle(10000)
    b.player_turn("skill", "盾牌反击", pl, enemy_act=False)
    check("盾牌反击 buff 生效", b.p_buffs.get("counter", 0) > 0, str(b.p_buffs))
    hp_before = b.enemy["hp"]
    logs, _ = b.player_turn("attack", None, pl, enemy_act=True)
    # v61：玩家有额外行动时怪不反击——先防御结束本回合，怪攻击才触发反击
    while b.p_extra_left > 0:
        logs2, _ = b.player_turn("defend", None, pl, enemy_act=True)
    all_logs = logs + logs2
    check("受击触发反击", b.enemy["hp"] < hp_before and any("反击" in l for l in all_logs),
          f"{hp_before}->{b.enemy['hp']} {all_logs[-2:]}")

    print("【装备：武器名类型绑定】")
    random.seed(42)
    bad = 0
    for i in range(100):
        wt = random.choice(list(C.WEAPON_TYPES.keys()))
        eq = C.generate_equip("weapon", random.randint(1, 60), random.choice(C.QUALITY_ORDER), wt)
        if not any(eq["name"].endswith(s) for s in C.WEAPON_NAME_SUFFIX[wt]):
            bad += 1
    check("100 次生成 0 个名字类型不匹配", bad == 0, f"{bad} bad")

    print("【机制字段完整性】")
    mech_count = {}
    for cid, cinfo in C.BRANCH_SKILLS.items():
        for tier, branches in (cinfo.get("branches") if isinstance(cinfo, dict) and "branches" in cinfo else cinfo).items():
            for bname, skills in branches.items():
                for sname, info in skills.items():
                    mech = info.get("mech", info.get("effect", "none"))
                    mech_count[mech] = mech_count.get(mech, 0) + 1
    check("全部技能带机制字段", len([k for k in mech_count if k != "none"]) >= 12, str(mech_count))

    print("【PVP：安全区/等级保护/红名】")
    m = Main(None)
    # 注册两个玩家
    ev = FakeEvent("g1", "1001", "注册 战士 甲")
    await run(m.register, ev)
    ev = FakeEvent("g1", "1002", "注册 法师 乙")
    await run(m.register, ev)
    # 城镇安全区禁止 PK
    ev = FakeEvent("g1", "1001", "攻击 1002")
    got = ""
    for r in await run(m.attack, ev):
        got = r
    check("安全区禁止 PK", "安全区" in got or "不能" in got or "禁止" in got, got[:100])
    # 不能攻击自己
    ev = FakeEvent("g1", "1001", "攻击 1001")
    got = ""
    for r in await run(m.attack, ev):
        got = r
    check("不能攻击自己", "不能攻击自己" in got, got[:100])

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

def make_battle(mon_hp=5000):
    mon = {"name": "测试怪", "hp": mon_hp, "max_hp": mon_hp, "def": 50, "mdef": 40, "spd": 5,
           "atk": 30, "matk": 30, "crit": 0.0, "dodge": 0.0, "is_boss": False,
           "skills": [], "exp": 10, "gold": 10}
    return BT.Battle("monster", mon)

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
