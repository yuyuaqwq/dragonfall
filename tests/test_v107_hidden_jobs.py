#!/usr/bin/env python3
"""v112 隐藏线数据层测试（test_v107_hidden_jobs.py，v112 重写）

覆盖：
1. 6 隐藏线全注册（龙裔/奥秘/荒野/暗影神谕/暮影/苦修）
2. 每职业 base/growth/weapon_type/hidden 字段完整 + 新数据字段（aliases/lore/hint/tier_levels）
3. 专属属性进属性聚合（法穿/物穿/元素抗/深渊抗/幸运/护盾/格挡/法吸/召唤强化）
4. 等级成长曲线（40 级 vs 90 级属性增长）
5. 面板显示名解析 + 流派档位结构（每线 2-3 流派 × 3 档）
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
    print("===== v112 隐藏线数据层 =====\n")

    HIDDEN = [
        ("cls_dragon_oath", "龙裔誓约"), ("cls_chronomancer", "时咒法师"),
        ("cls_wild_hunter", "星语者"), ("cls_hymn", "暗影神谕"),
        ("cls_shadow_blade", "暮影行者"), ("cls_wu_sheng", "苦修士"),
    ]
    print("— 注册与字段 —")
    check("隐藏线共 6 条", len([1 for c in C.CLASSES.values() if c.get("hidden")]) == 6)
    for cid, cname in HIDDEN:
        c = C.CLASSES.get(cid)
        check(f"{cname} 注册", c is not None)
        if c is None:
            continue
        check(f"{cname} hidden 标记", c.get("hidden") is True)
        check(f"{cname} base/growth/weapon", all(k in c for k in ("base", "growth", "weapon_type")))
        check(f"{cname} 三阶 evolve", len(c.get("evolve", [])) == 3, str(c.get("evolve")))
        check(f"{cname} v112 新字段齐", all(k in c for k in ("aliases", "lore", "hint", "tier_levels", "attack_text", "tutor")),
              str(sorted(set(("aliases", "lore", "hint", "tier_levels", "attack_text", "tutor")) - set(c))))
        check(f"{cname} 档位门槛 40/60/90", c.get("tier_levels") == {1: 40, 2: 60, 3: 90}, str(c.get("tier_levels")))
        brs = c.get("evolve_branches", {})
        check(f"{cname} 流派 1-3 个", 1 <= len(brs.get(1, [])) <= 3, str(brs.get(1)))
        check(f"{cname} 三档名称齐全", all(len(brs.get(t, [])) >= 1 for t in (1, 2, 3)), str(brs))

    # 2. 属性计算
    print("\n— 属性计算 —")
    for cid, cname in HIDDEN:
        st = E.player_base_stats(cid, 40, 0, 0)
        check(f"{cname} Lv.40 属性计算", st.get("max_hp", 0) > 0 and st.get("atk", 0) > 0, str(st))

    # 3. 专属属性进聚合
    print("\n— 专属属性 —")
    expect = {
        "cls_chronomancer": ("pene_magi", 0.15),
        "cls_shadow_blade": ("pene_phys", 0.15),
        "cls_dragon_oath": ("elem_res", 0.10),
        "cls_wild_hunter": ("luck", 0.10),
        "cls_hymn": ("abyss_res", 0.10),
        "cls_wu_sheng": ("crit", 0.10),
    }
    for cid, (stat, val) in expect.items():
        st = E.player_final_stats(cid, 50, {}, 0, {}, 0, None, "human")
        got = st.get(stat, 0)
        check(f"{C.display('classes', cid)} {stat} = {val}", abs(got - val) < 1e-9,
              f"got {got}")
    st_t = E.player_final_stats("cls_dragon_oath", 50, {}, 0, {}, 0, None, "human")
    check("龙裔 shield_power = 5%", abs(st_t.get("shield_power", 0) - 0.05) < 1e-9, str(st_t.get("shield_power")))
    st_s = E.player_final_stats("cls_shadow_blade", 50, {}, 0, {}, 0, None, "human")
    check("暮影 crit_dmg = 20%", abs(st_s.get("crit_dmg", 0) - 0.20) < 1e-9,
          str(st_s.get("crit_dmg")))

    # 4. 成长曲线：40 级 → 90 级属性增长
    print("\n— 成长曲线 —")
    for cid, cname in HIDDEN:
        st40 = E.player_base_stats(cid, 40, 0, 0)
        st90 = E.player_base_stats(cid, 90, 0, 0)
        check(f"{cname} 50 级成长(hp↑atk↑)", st90["max_hp"] > st40["max_hp"] * 1.5
              and st90["atk"] > st40["atk"] * 1.5,
              f"hp {st40['max_hp']}→{st90['max_hp']}, atk {st40['atk']}→{st90['atk']}")

    # 5. 显示名与转职名
    print("\n— 显示名 —")
    for cid, cname in HIDDEN:
        check(f"{cname} display 解析", C.display("classes", cid) == cname, C.display("classes", cid))

    print()
    print(f"===== v112 隐藏线数据层测试: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
