#!/usr/bin/env python3
"""v106.4 反伤/物魔免/物法吸属性体系测试（2026-08-13 鱼鱼拍板）

覆盖：
1. 常量：PCT_STATS/PCT_CAPS/OPTIONAL_STATS 注册
2. 词条折算：thorns 10% / 铁壁物免5% / 魔抗魔免5% / 渴血物吸8% / 吸魂法吸8%
3. 种族聚合：矮人石肤物免 10% 进属性、龙裔龙鳞魔免 10%、兽人鲁莽 -5%
4. 战斗消费：反伤反弹 / 物免减免 / 魔免减免 / 物法吸血分流
5. 面板：OPTIONAL_STATS 0 不显示（源码断言）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run, make_player

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


async def main():
    clean_db()
    from data.plugins.dragonfall.game import battle as BT
    from data.plugins.dragonfall.game.core.affix import stat_affix_stats
    from data.plugins.dragonfall.game.data.affixes import AFFIXES

    print("===== v106.4 反伤/物魔免/物法吸属性体系 =====")

    # 1. 常量注册
    print("— 常量 —")
    check("PCT_STATS 含 5 新属性", all(s in C.PCT_STATS for s in
                                      ("thorns", "phys_reduce", "magic_reduce",
                                       "lifesteal_phys", "lifesteal_magi")))
    check("PCT_CAPS 反伤50%", C.PCT_CAPS.get("thorns") == 0.5)
    check("PCT_CAPS 物免40%", C.PCT_CAPS.get("phys_reduce") == 0.4)
    check("PCT_CAPS 魔免40%", C.PCT_CAPS.get("magic_reduce") == 0.4)
    check("PCT_CAPS 物吸30%", C.PCT_CAPS.get("lifesteal_phys") == 0.3)
    check("PCT_CAPS 法吸30%", C.PCT_CAPS.get("lifesteal_magi") == 0.3)
    check("OPTIONAL_STATS 注册", all(s in C.OPTIONAL_STATS for s in
                                     ("thorns", "phys_reduce", "magic_reduce",
                                      "lifesteal_phys", "lifesteal_magi")))

    # 2. 词条折算
    print("— 词条折算 —")
    s = stat_affix_stats(["thorns", "phys_ward", "magic_ward", "thirst_phys", "thirst_magi"], "weapon", 30)
    check("thorns 词条 → 10%", abs(s.get("thorns", 0) - 0.10) < 1e-9, str(s))
    check("铁壁词条 → 物免5%", abs(s.get("phys_reduce", 0) - 0.05) < 1e-9, str(s))
    check("魔抗词条 → 魔免5%", abs(s.get("magic_reduce", 0) - 0.05) < 1e-9, str(s))
    check("渴血词条 → 物吸8%", abs(s.get("lifesteal_phys", 0) - 0.08) < 1e-9, str(s))
    check("吸魂词条 → 法吸8%", abs(s.get("lifesteal_magi", 0) - 0.08) < 1e-9, str(s))
    check("thorns 词条 trigger=stat", AFFIXES["thorns"].get("trigger") == "stat")

    # 3. 种族聚合
    print("— 种族聚合 —")
    st_d = E.player_final_stats("战士", 50, {}, 2, None, 0, None, "dwarf")
    check("矮人石肤物免 10% 聚合", abs(st_d.get("phys_reduce", 0) - 0.10) < 1e-9,
          str(st_d.get("phys_reduce")))
    st_db = E.player_final_stats("战士", 50, {}, 2, None, 0, None, "dragonborn")
    check("龙裔龙鳞魔免 10% 聚合", abs(st_db.get("magic_reduce", 0) - 0.10) < 1e-9,
          str(st_db.get("magic_reduce")))
    st_o = E.player_final_stats("战士", 50, {}, 2, None, 0, None, "orc")
    check("兽人鲁莽魔免 -5% 聚合", abs(st_o.get("magic_reduce", 0) - (-0.05)) < 1e-9,
          str(st_o.get("magic_reduce")))

    # 4. 战斗消费
    print("— 战斗消费 —")

    def mk_player(affixes=None, race="human", cls="战士", skills=None):
        eq_stats = {"atk": 100, "matk": 100}
        eq_stats.update(stat_affix_stats(affixes or [], "weapon", 30))
        return {
            "class_name": cls, "level": 30, "hp": 500, "max_hp": 500,
            "mp": 100, "max_mp": 100,
            "equipment": {"weapon": {"name": "测试剑", "stats": eq_stats,
                                     "affixes": affixes or [], "enhance": 0}},
            "attributes": {"str": 10, "int": 10},
            "learned_skills": skills or [], "race": race,
        }

    def mk_enemy():
        return {"name": "测试怪", "hp": 1000, "max_hp": 1000,
                "atk": 100, "def": 20, "mdef": 20, "spd": 10}

    # 4a. 反伤：受击反弹 thorns%
    p = mk_player(["thorns"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    st = b._player_stats(p)
    check("战斗聚合反伤 10%", abs(st.get("thorns", 0) - 0.10) < 1e-9, str(st.get("thorns")))
    found = False
    for seed in range(60):
        random.seed(seed)
        p2 = mk_player(["thorns"])
        b2 = BT.Battle("怪物", mk_enemy(), {}, p2)
        logs = []
        b2._damage_player(p2, 100, logs)
        if any("反伤" in l for l in logs):
            found = True
            check(f"反伤反弹（seed {seed}）", any("反弹" in l for l in logs), str(logs))
            break
    check("反伤属性可触发", found)

    # 4b. 物理免伤：矮人石肤 10% + 铁壁 5% = 15%
    p3 = mk_player(["phys_ward"], race="dwarf")
    b3 = BT.Battle("怪物", mk_enemy(), {}, p3)
    st3 = b3._player_stats(p3)
    check("战斗聚合物免 15%（石肤10%+铁壁5%）", abs(st3.get("phys_reduce", 0) - 0.15) < 1e-9,
          str(st3.get("phys_reduce")))
    found3 = False
    for seed in range(30):
        random.seed(seed)
        p3b = mk_player(["phys_ward"], race="dwarf")
        b3b = BT.Battle("怪物", {"name": "怪", "hp": 1000, "max_hp": 1000,
                                 "atk": 100, "def": 20, "mdef": 20, "spd": 10}, {}, p3b)
        logs3, _ = b3b._enemy_turn(p3b)
        if any("物理免伤" in l for l in logs3):
            found3 = True
            break
    check("物理免伤生效", found3)

    # 4c. 魔法免伤：龙裔 10% + 魔抗 5% = 15%
    p4 = mk_player(["magic_ward"], race="dragonborn")
    b4 = BT.Battle("怪物", mk_enemy(), {}, p4)
    st4 = b4._player_stats(p4)
    check("战斗聚合魔免 15%（龙鳞10%+魔抗5%）", abs(st4.get("magic_reduce", 0) - 0.15) < 1e-9,
          str(st4.get("magic_reduce")))

    # 4d. 物理/法术吸血分流（人类无通用吸血）
    p5 = mk_player(["thirst_phys"])
    b5 = BT.Battle("怪物", mk_enemy(), {}, p5)
    random.seed(42)
    logs5 = b5._player_attack(b5._player_stats(p5), p5)
    check("物吸普攻触发", any("吸血" in l for l in logs5), str(logs5))

    p6 = mk_player(["thirst_magi"], cls="法师", skills=["火球术"])
    b6 = BT.Battle("怪物", mk_enemy(), {}, p6)
    st6 = b6._player_stats(p6)
    check("法吸不作用于普攻", st6.get("lifesteal_magi") == 0.08)
    random.seed(42)
    logs6 = b6._player_attack(st6, p6)
    check("法吸普攻不触发", not any("吸血" in l for l in logs6), str([l for l in logs6 if "吸血" in l]))
    found6 = False
    for seed in range(60):
        random.seed(seed)
        p6b = mk_player(["thirst_magi"], cls="法师", skills=["火球术"])
        b6b = BT.Battle("怪物", mk_enemy(), {}, p6b)
        logs6b = b6b._player_skill(b6b._player_stats(p6b), "火球术",
                                   E.skill_info("法师", "火球术"), p6b)
        if any("吸血" in l for l in logs6b):
            found6 = True
            break
    check("法吸魔法技能触发", found6)

    # 5. 面板 OPTIONAL_STATS 0 不显示（源码断言）
    print("— 面板 —")
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "commands", "player.py"),
              encoding="utf-8") as f:
        src = f.read()
    check("面板含反伤行", '"🌵", "thorns"' in src)
    check("面板含物免行", '"🪨", "phys_reduce"' in src)
    check("面板含魔免行", '"🛡️", "magic_reduce"' in src)
    check("面板含物吸行", '"🩸", "lifesteal_phys"' in src)
    check("面板含法吸行", '"🔮", "lifesteal_magi"' in src)
    check("面板 0 不显示逻辑", "C.OPTIONAL_STATS" in src and "continue" in src)

    print()
    print(f"===== v106.4 反伤/物魔免/物法吸测试: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
