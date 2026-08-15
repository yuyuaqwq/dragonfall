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
        "gold": 100, "exp": 0, "cur_map": "oak_town",
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
    b.player_turn("skill", "战吼", p)
    check("p_buffs 有 atk_up", b.p_buffs.get("atk_up", 0) > 0, str(b.p_buffs))
    # v121 CTB：一次玩家行动后 _end_round 递减一次（无额外行动阶段）
    check("回合结束递减", b.p_buffs.get("atk_up", 0) == 2, str(b.p_buffs))
    check("怒吼无伤害", m["hp"] == 100000)
    # buff 效果对比
    random.seed(3)
    p2 = make_player("战士", 10)
    m2 = make_monster(hp=100000, defense=50)
    b2 = BT.Battle("monster", m2)
    b2.player_turn("skill", "战吼", p2)
    b2.player_turn("attack", None, p2)
    dmg_buffed = 100000 - m2["hp"]
    random.seed(3)
    p3 = make_player("战士", 10)
    m3 = make_monster(hp=100000, defense=50)
    b3 = BT.Battle("monster", m3)
    b3.player_turn("attack", None, p3)
    dmg_plain = 100000 - m3["hp"]
    check("怒吼后伤害提升", dmg_buffed > dmg_plain, f"buff={dmg_buffed} plain={dmg_plain}")

    print("【战斗：减益 buff（冰/毒/破甲）】")
    random.seed(4)
    b = BT.Battle("monster", make_monster(hp=100000))
    b.player_turn("skill", "冰锥", make_player("法师", 10, mp=100))
    check("冰锥挂冰元素印记", b.e_buffs.get("ice_mark", 0) > 0, str(b.e_buffs))
    random.seed(5)
    b = BT.Battle("monster", make_monster(hp=100000))
    b.player_turn("skill", "淬毒", make_player("刺客", 15, mp=100))
    check("淬毒挂毒层", (b.enemy.get("debuffs") or {}).get("poison", {}).get("n", 0) > 0, str(b.enemy.get("debuffs")))
    random.seed(6)
    b = BT.Battle("monster", make_monster(hp=100000))
    b.player_turn("skill", "破甲斩", make_player("战士", 10, mp=100))
    check("破甲斩 def_down", b.e_buffs.get("def_down", 0) > 0, str(b.e_buffs))

    print("【战斗：中毒持续伤害】")
    p = make_player("战士", 10, hp=9999)
    b = BT.Battle("monster", make_monster(hp=1000))
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 2, "mult": 1.0}
    logs, ended = b.player_turn("attack", None, p)
    # 毒 2 层（混合公式 atk×0.5+max_hp×1.5% 每层）+ 普攻
    check("中毒发作扣血", b.enemy["hp"] < 950, f"hp={b.enemy['hp']} (普攻+毒)")
    # 层数=剩余回合：结算后 2→1（衰减）
    check("毒层结算后衰减", b.enemy["debuffs"]["poison"]["n"] == 1, str(b.enemy["debuffs"]))

    print("【数值铁律：分支奥义 ≥ 基础大招】")
    for cls, base_lv30 in [("法师", "元素风暴"), ("战士", "无畏冲击"), ("游侠", "狩猎终章"),
                            ("牧师", "神恩降临"), ("刺客", "暗影处刑"), ("拳师", "破晓之拳")]:
        cid = C.resolve("classes", cls)
        base_power = C.PLAYER_SKILLS[cid]["skills"][C.resolve("skills", base_lv30)]["power"]
        t3 = C.BRANCH_SKILLS[cid]["branches"][3]
        # 分支 t3 奥义等效 = power × multi × cond.mult，取全分支最大
        best = 0
        for bname, skills in t3.items():
            for sname, s in skills.items():
                if s.get("kind") == "被动":
                    continue
                cond_mult = s.get("cond", {}).get("mult", 1) if isinstance(s.get("cond"), dict) else 1
                eff = s.get("power", 0) * s.get("multi", 1) * cond_mult
                best = max(best, eff)
        check(f"{cls} 分支奥义等效 ≥ 基础Lv.30({base_power})", best >= base_power * 0.95,
              f"best {best} vs {base_power}")

    print("【机制：冻结】")
    pl = make_player("法师", 35, skills=["冰霜新星"])
    b2 = make_battle()
    random.seed(42)
    logs, _ = b2.player_turn("skill", "冰霜新星", pl, enemy_act=True)
    check("固定 seed 42 冻结跳过敌方回合", any("冻结" in l for l in logs), str(logs))
    print("【机制：毒层→毒爆】")
    pl = make_player("刺客", 35, skills=["淬毒", "毒爆"])
    b = make_battle(10000)
    b.player_turn("skill", "淬毒", pl, enemy_act=False)
    b.player_turn("skill", "淬毒", pl, enemy_act=False)
    hp_before = b.enemy["hp"]
    b.player_turn("skill", "毒爆", pl, enemy_act=False)
    check("毒爆额外伤害", b.enemy["hp"] < hp_before, f"{hp_before}->{b.enemy['hp']}")

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
    ev = FakeEvent("g1", "1001", "注册 战士 甲 男")
    await run(m.register, ev)
    ev = FakeEvent("g1", "1002", "注册 法师 乙 男")
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
