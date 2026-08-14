#!/usr/bin/env python3
"""v109.2 P2-9 半死字段数据驱动化验证（临时）"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, run
from data.plugins.dragonfall.game import engine as EG
from data.plugins.dragonfall.game import battle as BT
from data.plugins.dragonfall.game.core.affix import stat_affix_stats

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond: passed += 1; print(f"  ✅ {name}")
    else: failed += 1; print(f"  ❌ {name} {detail}")

async def main():
    clean_db()
    def mk_player(cls="战士", skills=None, extra_stats=None, hp=500):
        eq_stats = {"atk": 100, "matk": 100}
        if extra_stats: eq_stats.update(extra_stats)
        return {"class_name": cls, "level": 90, "hp": hp, "max_hp": hp,
                "mp": 200, "max_mp": 200,
                "equipment": {"weapon": {"name": "t", "stats": eq_stats, "affixes": [], "enhance": 0}},
                "attributes": {"str": 10, "int": 10},
                "learned_skills": skills or [], "race": "human"}
    def mk_enemy(def_=20, mdef=20, hp=10**9):
        return {"name": "怪", "hp": hp, "max_hp": hp, "atk": 0, "def": def_, "mdef": mdef, "spd": 10}

    print("===== P2-9 数据驱动化 =====\n")

    # 1. 烈焰亲和：火系魔法 +10%（element=fire 判断）
    print("— 烈焰亲和（proc fire_bonus）—")
    fire_skill = {"name": "火球测试", "kind": "魔法", "power": 1.0, "lv": 40, "cd": 1, "element": "fire"}
    random.seed(3)
    p1 = mk_player(cls="法师", skills=["烈焰亲和"])
    b1 = BT.Battle("怪物", mk_enemy(mdef=0), {}, p1)
    st1 = b1._player_stats(p1)
    base = int(st1["matk"] * 1.0)
    h0 = b1.enemy["hp"]
    b1._player_skill(st1, "火球测试", fire_skill, p1)
    dealt1 = h0 - b1.enemy["hp"]
    check(f"火系魔法伤害 ≈ matk×1.1（{int(base*1.1)}±15%）",
          0.85*base*1.1 <= dealt1 <= 1.15*base*1.1, f"dealt {dealt1}")
    random.seed(3)
    p1b = mk_player(cls="法师")
    b1b = BT.Battle("怪物", mk_enemy(mdef=0), {}, p1b)
    h0 = b1b.enemy["hp"]
    b1b._player_skill(b1b._player_stats(p1b), "火球测试", fire_skill, p1b)
    dealt1b = h0 - b1b.enemy["hp"]
    check("无被动：无加成", dealt1b < dealt1, f"{dealt1b} vs {dealt1}")

    # 2. 破甲本能：pierce 技能 +10%
    print("\n— 破甲本能（proc pierce）—")
    pierce_skill = {"name": "破甲测试", "kind": "物理", "power": 1.0, "lv": 40, "cd": 1, "pierce": True}
    random.seed(5)
    p2 = mk_player(cls="战士", skills=["破甲本能"])
    b2 = BT.Battle("怪物", mk_enemy(def_=9999), {}, p2)
    st2 = b2._player_stats(p2)
    base2 = int(st2["atk"] * 1.0)
    h0 = b2.enemy["hp"]
    b2._player_skill(st2, "破甲测试", pierce_skill, p2)
    dealt2 = h0 - b2.enemy["hp"]
    check(f"pierce 技能伤害 ≈ atk×1.1（{int(base2*1.1)}±15%）",
          0.85*base2*1.1 <= dealt2 <= 1.15*base2*1.1, f"dealt {dealt2}")

    # 3. 双修精通：atk+matk → +5%
    print("\n— 双修精通（cond dual_stat）—")
    phys_skill = {"name": "斩击测试", "kind": "物理", "power": 1.0, "lv": 40, "cd": 1}
    random.seed(7)
    p3 = mk_player(cls="龙裔誓约", skills=["双修精通"])
    b3 = BT.Battle("怪物", mk_enemy(def_=0), {}, p3)
    st3 = b3._player_stats(p3)
    base3 = int(st3["atk"] * 1.0)
    h0 = b3.enemy["hp"]
    b3._player_skill(st3, "斩击测试", phys_skill, p3)
    dealt3 = h0 - b3.enemy["hp"]
    check(f"物理伤害 ≈ atk×1.05（{int(base3*1.05)}±15%）",
          0.85*base3*1.05 <= dealt3 <= 1.15*base3*1.05, f"dealt {dealt3}")

    # 4. 气力调和：回合回血 2%（Battle.__init__ 会按实时属性重算 max_hp）
    print("\n— 气力调和（proc turn_heal）—")
    p4 = mk_player(cls="拳师", skills=["气力调和"], hp=400)
    p4["hp"] = 200
    b4 = BT.Battle("怪物", mk_enemy(), {}, p4)
    real_max = b4._player_stats(p4)["max_hp"]
    logs4 = b4._turn_start(p4)
    check(f"回血 = max_hp×2%（{real_max}×0.02={int(real_max*0.02)}）",
          p4["hp"] == 200 + int(real_max * 0.02), f"hp={p4['hp']}")
    check("日志含『气力调和』", any("气力调和" in x for x in logs4), str(logs4))

    # 5. 奥术直觉：回合开始 arcane+1（v112.4：属法师守线秘法族）
    print("\n— 奥术直觉（proc arcane_regen）—")
    p5 = mk_player(cls="法师", skills=["奥术直觉"])
    b5 = BT.Battle("怪物", mk_enemy(), {}, p5)
    logs5 = b5._turn_start(p5)
    check("arcane 层 = 1", b5.mech_stacks.get("arcane") == 1, str(b5.mech_stacks))
    check("日志含『充能』", any("充能" in x for x in logs5), str(logs5))

    # 6. 符文刻印（stat spellblade_regen）已随 v113 魔剑士流派删除——应无 spellblade 回合充能
    print("\n— 魔剑士被动已删（符文刻印 spellblade_regen 移除）—")
    p6 = mk_player(cls="龙裔誓约", skills=[])  # no 符文刻印
    b6 = BT.Battle("怪物", mk_enemy(), {}, p6)
    logs6 = b6._turn_start(p6)
    check("无魔剑士被动不再充能 spellblade", b6.mech_stacks.get("spellblade") is None, str(b6.mech_stacks))
    check("无『魔能』日志", not any("魔能" in x for x in logs6), str(logs6))

    print(f"\n===== 结果: {passed} passed, {failed} failed =====")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
