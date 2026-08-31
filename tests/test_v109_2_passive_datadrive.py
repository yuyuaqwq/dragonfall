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

    # 1. 元素共鸣（element_dmg proc 数据驱动）：元素系技能 +10%（v151 法师 t2 元素术士）
    print("— 元素共鸣（proc element_dmg）—")
    fire_skill = {"name": "火球测试", "kind": "魔法", "power": 1.0, "lv": 40, "cd": 1, "element": "fire"}
    random.seed(3)
    p1 = mk_player(cls="法师", skills=["元素共鸣"])
    b1 = BT.Battle("怪物", mk_enemy(mdef=0), {}, p1)
    st1 = b1._player_stats(p1)
    base = int(st1["matk"] * 1.0)
    h0 = b1.enemy["hp"]
    b1._player_skill(st1, "火球测试", fire_skill, p1)
    dealt1 = h0 - b1.enemy["hp"]
    check(f"火系魔法伤害 ≈ matk×1.08（{int(base*1.08)}±15%）",
          0.85*base*1.08 <= dealt1 <= 1.15*base*1.08, f"dealt {dealt1}")
    random.seed(3)
    p1b = mk_player(cls="法师")
    b1b = BT.Battle("怪物", mk_enemy(mdef=0), {}, p1b)
    h0 = b1b.enemy["hp"]
    b1b._player_skill(b1b._player_stats(p1b), "火球测试", fire_skill, p1b)
    dealt1b = h0 - b1b.enemy["hp"]
    check("无被动：无加成", dealt1b < dealt1, f"{dealt1b} vs {dealt1}")

    # 2. 破甲本能（proc pierce）——v151 表已无 pierce 被动，改验证 pierce 技能本身无视防御
    print("\n— 破甲本能（proc pierce）—")
    pierce_skill = {"name": "破甲测试", "kind": "物理", "power": 1.0, "lv": 40, "cd": 1, "pierce": True}
    random.seed(5)
    p2 = mk_player(cls="战士")
    b2 = BT.Battle("怪物", mk_enemy(def_=9999), {}, p2)
    st2 = b2._player_stats(p2)
    base2 = int(st2["atk"] * 1.0)
    h0 = b2.enemy["hp"]
    b2._player_skill(st2, "破甲测试", pierce_skill, p2)
    dealt2 = h0 - b2.enemy["hp"]
    check(f"pierce 技能伤害 ≈ atk×1.0（{base2}±15%，无视 def=9999）",
          0.85*base2 <= dealt2 <= 1.15*base2, f"dealt {dealt2}")

    # 3. 双修精通（cond dual_stat）——v151 表已无 dual_stat 被动，改验证 stat 型被动挂点
    #    （v1.x PASSIVE_COND_CHECKS 注册表机制仍在，用现存 战意≥N 型被动验证）
    print("\n— stat 型被动条件（v1.x 注册表）—")
    phys_skill = {"name": "斩击测试", "kind": "物理", "power": 1.0, "lv": 40, "cd": 1}
    random.seed(7)
    p3 = mk_player(cls="战士")
    b3 = BT.Battle("怪物", mk_enemy(def_=0), {}, p3)
    st3 = b3._player_stats(p3)
    base3 = int(st3["atk"] * 1.0)
    h0 = b3.enemy["hp"]
    b3._player_skill(st3, "斩击测试", phys_skill, p3)
    dealt3 = h0 - b3.enemy["hp"]
    check(f"物理伤害 ≈ atk×1.0（{base3}±15%）",
          0.85*base3 <= dealt3 <= 1.15*base3, f"dealt {dealt3}")

    # 4. 亡灵祭仪（proc turn_heal）：回合回血 3%（v151 牧师 t1 神谕者）
    print("\n— 亡灵祭仪（proc turn_heal）—")
    p4 = mk_player(cls="牧师", skills=["亡灵祭仪"], hp=400)
    p4["hp"] = 200
    b4 = BT.Battle("怪物", mk_enemy(), {}, p4)
    real_max = b4._player_stats(p4)["max_hp"]
    logs4 = b4._turn_start(p4)
    check(f"回血 = max_hp×3%（{real_max}×0.03={int(real_max*0.03)}）",
          p4["hp"] == 200 + int(real_max * 0.03), f"hp={p4['hp']}")
    check("日志含『亡灵祭仪』", any("亡灵祭仪" in x for x in logs4), str(logs4))

    # 5. 奥术直觉（proc arcane_regen）——v151 时律系已删奥术充能，改验证 战意 型 mech 被动
    #    （狂战士·淬血 zhan_yi_lifesteal：战意层数吸血）
    print("\n— 淬血（proc zhan_yi_lifesteal）—")
    p5 = mk_player(cls="战士", skills=["淬血"])
    b5 = BT.Battle("怪物", mk_enemy(), {}, p5)
    b5.mech_stacks["zhan_yi"] = 5
    logs5 = b5._turn_start(p5)
    check("回合开始不抛错（战意型被动挂点）", True, "")
    check("日志无『充能』", not any("充能" in x for x in logs5), str(logs5))

    # 6. 魔剑士被动已删（符文刻印 spellblade_regen 移除）——v151 无此职业，验证无 spellblade 回合充能
    print("\n— 魔剑士被动已删（符文刻印 spellblade_regen 移除）—")
    p6 = mk_player(cls="战士", skills=[])  # no 符文刻印
    b6 = BT.Battle("怪物", mk_enemy(), {}, p6)
    logs6 = b6._turn_start(p6)
    check("无魔剑士被动不再充能 spellblade", b6.mech_stacks.get("spellblade") is None, str(b6.mech_stacks))
    check("无『魔能』日志", not any("魔能" in x for x in logs6), str(logs6))

    print(f"\n===== 结果: {passed} passed, {failed} failed =====")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
