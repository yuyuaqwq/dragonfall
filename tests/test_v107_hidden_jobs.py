#!/usr/bin/env python3
"""v107 隐藏职业数据层测试（2026-08-13 鱼鱼拍板）

覆盖：
1. 13 隐藏职业全注册（吟游/魔剑 + 11 新增）
2. 每职业 base/growth/weapon_type/hidden 字段完整
3. 专属属性进属性聚合（法穿/物穿/元素抗/深渊抗/幸运/护盾/格挡/法吸/召唤强化）
4. 等级成长曲线（40 级 vs 90 级属性增长）
5. 面板显示名解析
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
    print("===== v107 隐藏职业数据层 =====\n")

    HIDDEN = [
        ("cls_bard", "吟游诗人"), ("cls_spellblade", "魔剑士"),
        ("cls_arcanist", "奥术师"), ("cls_shadow_blade", "影武者"),
        ("cls_dragon_warrior", "龙血战士"), ("cls_void_walker", "虚空行者"),
        ("cls_astrologer", "占星者"), ("cls_jungle_hunter", "丛林猎手"),
        ("cls_templar", "圣殿骑士"), ("cls_wu_sheng", "武圣"),
        ("cls_blood_mage", "血法师"), ("cls_necromancer", "亡灵术士"),
        ("cls_beast_king", "兽王"),
    ]
    print("— 注册与字段 —")
    check("隐藏职业共 13 个", len([1 for c in C.CLASSES.values() if c.get("hidden")]) == 13)
    for cid, cname in HIDDEN:
        c = C.CLASSES.get(cid)
        check(f"{cname} 注册", c is not None)
        if c is None:
            continue
        check(f"{cname} hidden 标记", c.get("hidden") is True)
        check(f"{cname} base/growth/weapon", all(k in c for k in ("base", "growth", "weapon_type")))
        check(f"{cname} 三阶 evolve", len(c.get("evolve", [])) == 3, str(c.get("evolve")))

    # 2. 属性计算
    print("\n— 属性计算 —")
    for cid, cname in HIDDEN:
        st = E.player_base_stats(cid, 40, 0, 0)
        check(f"{cname} Lv.40 属性计算", st.get("max_hp", 0) > 0 and st.get("atk", 0) > 0, str(st))

    # 3. 专属属性进聚合
    print("\n— 专属属性 —")
    expect = {
        "cls_arcanist": ("pene_magi", 0.15),
        "cls_shadow_blade": ("pene_phys", 0.15),
        "cls_dragon_warrior": ("elem_res", 0.15),
        "cls_void_walker": ("abyss_res", 0.15),
        "cls_astrologer": ("luck", 0.15),
        "cls_templar": ("shield_power", 0.15),
        "cls_blood_mage": ("lifesteal_magi", 0.15),
        "cls_necromancer": ("summon_power", 0.20),
        "cls_beast_king": ("summon_power", 0.30),
    }
    for cid, (stat, val) in expect.items():
        st = E.player_final_stats(cid, 50, {}, 0, {}, 0, None, "human")
        got = st.get(stat, 0)
        check(f"{C.display('classes', cid)} {stat} = {val}", abs(got - val) < 1e-9,
              f"got {got}")
    st_t = E.player_final_stats("cls_templar", 50, {}, 0, {}, 0, None, "human")
    check("圣殿 block = 10%", abs(st_t.get("block", 0) - 0.10) < 1e-9, str(st_t.get("block")))
    st_s = E.player_final_stats("cls_shadow_blade", 50, {}, 0, {}, 0, None, "human")
    check("影武者 crit_dmg = 20%", abs(st_s.get("crit_dmg", 0) - 0.20) < 1e-9,
          str(st_s.get("crit_dmg")))

    # 4. 成长曲线：40 级 → 90 级属性增长
    print("\n— 成长曲线 —")
    for cid, cname in HIDDEN[2:]:
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
    print(f"===== v107 隐藏职业数据层测试: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
