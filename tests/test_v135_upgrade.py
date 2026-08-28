# -*- coding: utf-8 -*-
"""v135 装备升级机制验收测试（GWEN_GAME_DB 隔离，不碰生产库）"""
import os
import sys
import asyncio

os.environ.setdefault("GWEN_GAME_DB", os.path.abspath("test_v135_upgrade.db"))
sys.path.insert(0, "tests")

from conftest import clean_db, make_player, Main, FakeEvent, run  # noqa: E402
from data.plugins.dragonfall.game import content as C, db, engine as E  # noqa: E402

g = "g_test_upg"
q = "q_test_upg"

passed = 0
failed = 0


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {extra}")


def goto_smith(m, g, q):
    """把玩家放到橡木镇老铁铁匠铺（oak_town_3, craft funcs）。"""
    db.update_player(g, q, cur_map="oak_town", cur_subarea="oak_town_3")


def prof_to_lv(g, q, lv):
    """把强化副业升到指定等级。"""
    db.activate_prof(g, q, "enhance")
    for _ in range(500):
        nv, _ = db.add_prof_exp(g, q, "enhance", 10)
        if nv >= lv:
            return nv
    return db.get_prof_level(g, q, "enhance")


def main():
    print("== v135 装备升级机制验收 ==")

    # 1. UPGRADE_TABLE import
    print("[1] 数据表")
    check("UPGRADE_TABLE 存在且 11 级", len(C.UPGRADE_TABLE) == 11)
    check("MAX_UPGRADE=10", C.MAX_UPGRADE == 10)
    check("0 级倍率 1.00", C.UPGRADE_TABLE[0]["mult"] == 1.0)
    check("10 级倍率 1.35", C.UPGRADE_TABLE[10]["mult"] == 1.35)
    check("成本递增", C.UPGRADE_TABLE[1]["cost"] > C.UPGRADE_TABLE[0]["cost"])

    # 2. 升级命令流程（成功路径）
    print("[2] 升级命令流程")
    clean_db()
    m = Main(None)
    make_player(g, q, name="测试升级", cls="战士", level=30)
    db.update_player(g, q, gold=999999)
    eq = C.generate_roster_equip("eq_tie_jian")
    db.add_item(g, q, "eq_test1", eq)
    db.add_item(g, q, "i_stone_refine", {"name": "精炼强化石", "type": "材料", "stackable": True, "price": 30})
    prof_to_lv(g, q, 5)
    goto_smith(m, g, q)

    gold_before = db.get_player(g, q)["gold"]
    ev = FakeEvent(g, q, "升级 铁剑")
    out = asyncio.run(run(m.equip_upgrade, ev))
    txt = out[0] if out else ""
    check("升级成功提示", "装备升级成功" in txt, txt[:150])
    inv = db.get_inventory(g, q)
    d = inv[0]["data"] if inv else {}
    check("upgrade_lv=1", d.get("upgrade_lv", 0) == 1, f"got {d.get('upgrade_lv')}")
    gold_after = db.get_player(g, q)["gold"]
    # 200 成本 - 50 每日副业任务奖励 = 150（若每日任务未触发则 200，容差）
    check("金币扣减 200（含副业奖励容差）", gold_before - gold_after in (150, 200), f"diff={gold_before-gold_after}")
    check("精炼强化石扣 1", db.count_item(g, q, "i_stone_refine") == 0)

    # 3. engine 属性结算含升级乘区
    print("[3] engine 属性结算")
    st0, _ = E.player_stats_detail("cls_zhan_shi", 1, {}, 0, None, 0, None, "human")
    eq2 = C.generate_roster_equip("eq_tie_jian")
    eq2["upgrade_lv"] = 5  # 倍率 1.175（v136 升级 1.25→1.175）
    eq2["stats"] = {"atk": 10}
    st1, _ = E.player_stats_detail(
        "cls_zhan_shi", 1,
        {"weapon": eq2}, 0, None, 0, None, "human",
    )
    atk_diff = st1.get("atk", 0) - st0.get("atk", 0)
    check("升级5级 atk×1.175 生效", atk_diff == 11, f"diff={atk_diff}")
    # 升级+强化叠加：atk10 强化2(1.22) + 升级5(1.175) → 10*1.22*1.175=14.34→14
    eq3 = C.generate_roster_equip("eq_tie_jian")
    eq3["upgrade_lv"] = 5
    eq3["enhance"] = 2
    eq3["stats"] = {"atk": 10}
    st2, _ = E.player_stats_detail(
        "cls_zhan_shi", 1,
        {"weapon": eq3}, 0, None, 0, None, "human",
    )
    atk_diff2 = st2.get("atk", 0) - st0.get("atk", 0)
    check("升级×强化叠加 10*1.22*1.175=13（engine 逐级取整）", atk_diff2 == 13, f"diff={atk_diff2}")

    # 4. 拦截分支（每个独立重建玩家）
    print("[4] 拦截分支")
    # 4a. 上限拦截
    clean_db()
    m = Main(None)
    make_player(g, q, name="上限", cls="战士", level=30)
    db.update_player(g, q, gold=999999)
    eq4 = C.generate_roster_equip("eq_tie_jian")
    eq4["upgrade_lv"] = 10
    db.add_item(g, q, "eq_test4", eq4)
    db.add_item(g, q, "i_stone_refine", {"name": "精炼强化石", "type": "材料", "stackable": True, "price": 30})
    prof_to_lv(g, q, 10)
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "升级 铁剑")
    out = asyncio.run(run(m.equip_upgrade, ev))
    txt = out[0] if out else ""
    check("已满级拦截", "已经升级到极限" in txt, txt[:150])
    # 4b. 非铁匠铺拦截
    db.update_player(g, q, cur_map="oak_town", cur_subarea="oak_town_4")  # 旅店
    ev = FakeEvent(g, q, "升级 铁剑")
    out = asyncio.run(run(m.equip_upgrade, ev))
    txt = out[0] if out else ""
    check("非铁匠铺拦截", "需要到铁匠铺" in txt, txt[:150])
    # 4c. 无材料拦截（独立玩家：有石头再清空）
    clean_db()
    m = Main(None)
    make_player(g, q, name="无材料", cls="战士", level=30)
    db.update_player(g, q, gold=999999)
    eq4c = C.generate_roster_equip("eq_tie_jian")
    db.add_item(g, q, "eq_test4c", eq4c)
    db.add_item(g, q, "i_stone_refine", {"name": "精炼强化石", "type": "材料", "stackable": True, "price": 30})
    prof_to_lv(g, q, 5)
    goto_smith(m, g, q)
    db.remove_item(g, q, "i_stone_refine", 99)
    ev = FakeEvent(g, q, "升级 铁剑")
    out = asyncio.run(run(m.equip_upgrade, ev))
    txt = out[0] if out else ""
    check("无材料拦截", "精炼强化石" in txt, txt[:150])
    # 4d. 金币不足拦截（独立玩家）
    clean_db()
    m = Main(None)
    make_player(g, q, name="缺钱", cls="战士", level=30)
    db.update_player(g, q, gold=1)
    eq4d = C.generate_roster_equip("eq_tie_jian")
    db.add_item(g, q, "eq_test4d", eq4d)
    db.add_item(g, q, "i_stone_refine", {"name": "精炼强化石", "type": "材料", "stackable": True, "price": 30})
    prof_to_lv(g, q, 5)
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "升级 铁剑")
    out = asyncio.run(run(m.equip_upgrade, ev))
    txt = out[0] if out else ""
    check("金币不足拦截", "金币" in txt, txt[:150])
    # 4e. 副业等级不足拦截：装备预设 upgrade_lv=4，升 Lv.5 需要副业 Lv.5（Lv.1 不够）
    clean_db()
    m = Main(None)
    make_player(g, q, name="副业", cls="战士", level=30)
    db.update_player(g, q, gold=999999)
    eq5 = C.generate_roster_equip("eq_tie_jian")
    eq5["upgrade_lv"] = 4
    db.add_item(g, q, "eq_test5", eq5)
    db.add_item(g, q, "i_stone_refine", {"name": "精炼强化石", "type": "材料", "stackable": True, "price": 30})
    db.activate_prof(g, q, "enhance")  # 学徒 Lv.1
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "升级 铁剑")
    out = asyncio.run(run(m.equip_upgrade, ev))
    txt = out[0] if out else ""
    check("副业等级不足拦截(升Lv.5需Lv.5)", "需要强化副业" in txt, txt[:150])

    # 5. 旧档兼容：无 upgrade_lv 字段不报错
    print("[5] 旧档兼容")
    eq6 = C.generate_roster_equip("eq_tie_jian")
    eq6.pop("upgrade_lv", None)
    st3, _ = E.player_stats_detail(
        "cls_zhan_shi", 1,
        {"weapon": eq6}, 0, None, 0, None, "human",
    )
    check("旧档无 upgrade_lv 不报错", st3 is not None)

    # 6. 详情显示
    print("[6] 详情显示")
    eq7 = C.generate_roster_equip("eq_tie_jian")
    eq7["upgrade_lv"] = 3
    from data.plugins.dragonfall.game.commands.economy import _render_equip
    _lines = []
    _render_equip(eq7, _lines, equipped=False)
    _rc = "\n".join(_lines)
    check("详情含升级行", "升级：Lv.3" in _rc, _rc[:200])

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
