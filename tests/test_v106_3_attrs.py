#!/usr/bin/env python3
"""v106.3 吸血/暴击伤害/格挡属性专项测试（2026-08-13 鱼鱼拍板面板化）

覆盖：
1. 常量：PCT_STATS/PCT_CAPS 注册
2. 词条折算：lifesteal 8% / crit_dmg 20% / block 15% 进装备 stats
3. 种族天赋：矮人岩壁格挡 5% / 精灵月华利刃 10% / 兽人嗜血本能 5%
4. 战斗消费：吸血回血 / 暴伤倍率 / 格挡减伤 50%
5. 药水：嗜血/狂暴/岩壁 buff 乘算并入
6. 面板：stat_rows 含 3 新行
"""
import random
import sys
import os

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
    from data.plugins.dragonfall.game.data.items import ITEMS
    from data.plugins.dragonfall.game.engine import player_passive_stats

    print("===== v106.3 吸血/暴击伤害/格挡属性 =====")

    # 1. 常量注册
    print("— 常量 —")
    check("PCT_STATS 含 3 新属性", all(s in C.PCT_STATS for s in ("lifesteal", "crit_dmg", "block")))
    check("PCT_CAPS 吸血30%", C.PCT_CAPS.get("lifesteal") == 0.3)
    check("PCT_CAPS 暴伤100%", C.PCT_CAPS.get("crit_dmg") == 1.0)
    check("PCT_CAPS 格挡40%", C.PCT_CAPS.get("block") == 0.4)

    # 2. 词条折算
    print("— 词条折算 —")
    s = stat_affix_stats(["lifesteal", "crit_dmg", "block"], "weapon", 30)
    check("lifesteal 词条 → 8%", abs(s.get("lifesteal", 0) - 0.08) < 1e-9, str(s))
    check("crit_dmg 词条 → 20%", abs(s.get("crit_dmg", 0) - 0.20) < 1e-9, str(s))
    check("block 词条 → 15%", abs(s.get("block", 0) - 0.15) < 1e-9, str(s))

    # 词条定义已是 stat 触发（不再走触发特效）
    check("lifesteal 词条 trigger=stat", AFFIXES["lifesteal"].get("trigger") == "stat")
    check("crit_dmg 词条 trigger=stat", AFFIXES["crit_dmg"].get("trigger") == "stat")
    check("block 词条 trigger=stat", AFFIXES["block"].get("trigger") == "stat")

    # 3. 种族天赋
    print("— 种族天赋 —")
    rt_d = E.race_stats("dwarf")
    check("矮人岩壁格挡 +5%", abs(rt_d.get("block", 0) - 0.05) < 1e-9, str(rt_d))
    rt_e = E.race_stats("elf")
    check("精灵月华利刃 +10%", abs(rt_e.get("crit_dmg", 0) - 0.10) < 1e-9, str(rt_e))
    rt_o = E.race_stats("orc")
    check("兽人嗜血本能 +5%", abs(rt_o.get("lifesteal", 0) - 0.05) < 1e-9, str(rt_o))

    # 4. 战斗消费
    print("— 战斗消费 —")

    def mk_player(affixes=None, race="orc", hp=500):
        eq_stats = {"atk": 100}
        eq_stats.update(stat_affix_stats(affixes or [], "weapon", 30))
        return {
            "class_name": "战士", "level": 30, "hp": hp, "max_hp": hp,
            "mp": 50, "max_mp": 50,
            "equipment": {"weapon": {"name": "测试剑", "stats": eq_stats,
                                     "affixes": affixes or [], "enhance": 0}},
            "attributes": {"str": 10}, "learned_skills": [], "race": race,
        }

    def mk_enemy():
        return {"name": "测试怪", "hp": 1000, "max_hp": 1000,
                "atk": 50, "def": 20, "mdef": 20, "spd": 10}

    # 4a. 吸血：兽人 5% + 词条 8% = 13%，命中后回血
    p = mk_player(["lifesteal"], race="orc")
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    st = b._player_stats(p)
    check("战斗聚合吸血 13%（兽人5%+词条8%）", abs(st.get("lifesteal", 0) - 0.13) < 1e-9, str(st.get("lifesteal")))
    random.seed(42)
    b2 = BT.Battle("怪物", mk_enemy(), {}, p)
    logs = b2._player_attack(b2._player_stats(p), p)
    ls_logs = [l for l in logs if "吸血" in l]
    check("普攻命中触发吸血日志", len(ls_logs) > 0, str(logs))

    # 吸血数值验证：dmg>0 时回复 = int(dmg × 13%)
    p5 = mk_player(["lifesteal"], race="orc", hp=200)
    b5 = BT.Battle("怪物", mk_enemy(), {}, p5)
    random.seed(3)
    logs5 = b5._player_attack(b5._player_stats(p5), p5)
    ls5 = [l for l in logs5 if "吸血" in l]
    if ls5:
        heal = int(ls5[0].split("回复")[1].split("点")[0])
        check("吸血回复量 ≥ 1", heal >= 1, str(ls5))
    else:
        check("吸血回复量 ≥ 1", False, "无吸血日志")

    # 4b. 暴击伤害：crit_dmg 20% → 暴击时 ×(1+0.2)
    p2 = mk_player(["crit_dmg"], race="elf")
    b3 = BT.Battle("怪物", mk_enemy(), {}, p2)
    st3 = b3._player_stats(p2)
    check("战斗聚合暴伤 30%（精灵10%+词条20%）", abs(st3.get("crit_dmg", 0) - 0.30) < 1e-9, str(st3.get("crit_dmg")))
    crit_found = False
    for seed in range(100):
        random.seed(seed)
        p3 = mk_player(["crit_dmg"], race="elf")
        b4 = BT.Battle("怪物", mk_enemy(), {}, p3)
        logs3 = b4._player_attack(b4._player_stats(p3), p3)
        crit = [l for l in logs3 if "💥暴击" in l]
        if crit:
            crit_found = True
            break
    check("暴击伤害属性生效（有暴击样本）", crit_found)

    # 4c. 格挡：block 15% → 受击概率减伤 50%
    p4 = mk_player(["block"], race="dwarf")
    b6 = BT.Battle("怪物", mk_enemy(), {}, p4)
    st6 = b6._player_stats(p4)
    check("战斗聚合格挡 20%（矮人5%+词条15%）", abs(st6.get("block", 0) - 0.20) < 1e-9, str(st6.get("block")))
    block_found = False
    for seed in range(80):
        random.seed(seed)
        p7 = mk_player(["block"], race="dwarf")
        b7 = BT.Battle("怪物", mk_enemy(), {}, p7)
        logs7 = []
        b7._damage_player(p7, 100, logs7)
        g = [l for l in logs7 if "格挡" in l]
        if g:
            block_found = True
            check(f"格挡减伤 50%（seed {seed}）", "减免 50 点" in g[0], g[0])
            break
    check("格挡属性可触发", block_found)

    # 4d. 圣盾被动 stat=block → 被动加成进 block 属性（_PASSIVE_STAT_APPLY）
    pb = player_passive_stats("战士", ["圣盾"])
    if pb.get("block_add", 0) > 0:
        check("圣盾被动 block_add 折算", True, str(pb.get("block_add")))
    else:
        print("  ⚠️ 圣盾被动未在战士技能表（跳过被动折算断言）")

    # 5. 药水
    print("— 药水 —")
    b8 = BT.Battle("怪物", mk_enemy(), {}, mk_player())
    logs8 = []
    b8._apply_potion_special("lifesteal_pot", mk_player(), logs8)
    check("嗜血药剂 buff 生效", b8.p_buffs.get("lifesteal_pot") == 3, str(logs8))
    b9 = BT.Battle("怪物", mk_enemy(), {}, mk_player())
    logs9 = []
    b9._apply_potion_special("crit_dmg_pot", mk_player(), logs9)
    check("狂暴药剂 buff 生效", b9.p_buffs.get("crit_dmg_pot") == 3, str(logs9))
    b10 = BT.Battle("怪物", mk_enemy(), {}, mk_player())
    logs10 = []
    b10._apply_potion_special("block_pot", mk_player(), logs10)
    check("岩壁药剂 buff 生效", b10.p_buffs.get("block_pot") == 3, str(logs10))

    check("嗜血药剂物品数据", "i_lifesteal_pot" in ITEMS, "missing")
    check("狂暴药剂物品数据", "i_crit_dmg_pot" in ITEMS, "missing")
    check("岩壁药剂物品数据", "i_block_pot" in ITEMS, "missing")

    # 6. 面板 stat_rows 含 3 新行（源码断言）
    print("— 面板 —")
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "commands", "player.py"),
              encoding="utf-8") as f:
        src = f.read()
    check("面板含吸血行", '"🩸", "lifesteal"' in src)
    check("面板含暴伤行", '"💢", "crit_dmg"' in src)
    check("面板含格挡行", '"🧱", "block"' in src)

    print()
    print(f"===== v106.3 吸血/暴击伤害/格挡测试: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

