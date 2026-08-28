# -*- coding: utf-8 -*-
"""v136 装备进化 + 怪异炼成验收（GWEN_GAME_DB 隔离，不碰生产库）

覆盖：
进化：无参列配方 / 素材不足拦截 / 金币不足拦截 / 成功继承强化升级(half折半) / 已装备进化
炼成：素材不足拦截 / 限3次拦截(第4次) / 成功加成生效(calamity_bonus) / engine结算含炼成 / 已装备炼成

独立运行：python tests/test_v136_evolve_calamity.py
"""
import os
import sys
import asyncio
import random

os.environ.setdefault("GWEN_GAME_DB", os.path.abspath("test_v136_evolve_calamity.db"))
sys.path.insert(0, "tests")

from conftest import clean_db, make_player, Main, FakeEvent, run  # noqa: E402
from data.plugins.dragonfall.game import content as C, db, engine as E  # noqa: E402

g = "g_evo"
q = "q_evo"

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
    db.update_player(g, q, cur_map="oak_town", cur_subarea="oak_town_3")


def make_player_lv(name, lv=60, cls="战士"):
    return make_player(g, q, name=name, cls=cls, level=lv)


def give_equip(equip_dict, key="eq_ev1"):
    """给玩家背包塞一件指定装备（带可选增强）。"""
    db.add_item(g, q, key, equip_dict)
    return key


def give_mats(mats):
    for mk, mn in mats.items():
        db.add_item(g, q, mk, {"name": C.display("materials", mk)}, mn)


def main():
    print("== v136 装备进化 + 怪异炼成验收 ==")
    # ---------- 0. 数据表 ----------
    print("[0] 数据表")
    check("EVOLVE_RECIPES 有 3 条进化链", len(C.EVOLVE_RECIPES) >= 3, str(len(C.EVOLVE_RECIPES)))
    check("弯刀→血誓战剑", C.EVOLVE_RECIPES.get("弯刀", {}).get("target") == "rec_xue_shi_zhan_jian")
    check("CALAMITY_MAX=3", C.CALAMITY_MAX == 3)
    check("CALAMITY_STATS 有 6 属性", len(C.CALAMITY_STATS) == 6)
    check("新素材已登记", C.display("materials", "mat_yu_jin_he_xin") == "余烬核心")

    # ---------- 1. 装备进化 ----------
    print("[1] 装备进化")
    # 1a. 无参列配方
    clean_db()
    m = Main(None)
    make_player_lv("进化列表", 60)
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "装备进化")
    out = asyncio.run(run(m.evolve_equip, ev))
    txt = out[0] if out else ""
    check("无参列出进化配方", "弯刀" in txt and "血誓战剑" in txt, txt[:150])
    # 1b. 素材不足拦截
    clean_db()
    m = Main(None)
    make_player_lv("进化缺材", 60)
    db.update_player(g, q, gold=999999)
    eq_w = C.generate_roster_equip("eq_wan_dao")
    eq_w["enhance"] = 4
    eq_w["upgrade_lv"] = 2
    give_equip(eq_w)
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "装备进化 弯刀")
    out = asyncio.run(run(m.evolve_equip, ev))
    txt = out[0] if out else ""
    check("素材不足拦截", "材料不足" in txt, txt[:150])
    # 1c. 金币不足拦截
    clean_db()
    m = Main(None)
    make_player_lv("进化缺金", 60)
    db.update_player(g, q, gold=100)
    eq_w = C.generate_roster_equip("eq_wan_dao")
    eq_w["enhance"] = 4
    eq_w["upgrade_lv"] = 2
    give_equip(eq_w)
    give_mats(C.EVOLVE_RECIPES["弯刀"]["mats"])
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "装备进化 弯刀")
    out = asyncio.run(run(m.evolve_equip, ev))
    txt = out[0] if out else ""
    check("金币不足拦截", "金币不足" in txt, txt[:150])
    # 1d. 成功进化：继承强化/升级(half)
    clean_db()
    m = Main(None)
    make_player_lv("进化成功", 60)
    db.update_player(g, q, gold=999999)
    eq_w = C.generate_roster_equip("eq_wan_dao")
    eq_w["enhance"] = 4
    eq_w["upgrade_lv"] = 3
    give_equip(eq_w)
    give_mats(C.EVOLVE_RECIPES["弯刀"]["mats"])
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "装备进化 弯刀")
    out = asyncio.run(run(m.evolve_equip, ev))
    txt = out[0] if out else ""
    check("进化成功提示", "进化成功" in txt, txt[:150])
    inv = db.get_inventory(g, q)
    new_eq = [it for it in inv if it["key"].startswith("eq_")][0]
    check("旧弯刀被消耗", all("弯刀" not in it["data"].get("name", "") for it in inv if it["key"] != new_eq["key"]))
    check("新装备是血誓战剑", "血誓战剑" in new_eq["data"].get("name", ""), new_eq["data"].get("name", ""))
    check("继承强化 half(4→2)", new_eq["data"].get("enhance", 0) == 2, str(new_eq["data"].get("enhance")))
    check("继承升级 half(3→1)", new_eq["data"].get("upgrade_lv", 0) == 1, str(new_eq["data"].get("upgrade_lv")))
    # 1e. 已装备进化
    clean_db()
    m = Main(None)
    make_player_lv("进化已装", 60)
    db.update_player(g, q, gold=999999)
    eq_w = C.generate_roster_equip("eq_wan_dao")
    db.update_player(g, q, equipment={"weapon": eq_w})
    give_mats(C.EVOLVE_RECIPES["弯刀"]["mats"])
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "装备进化 弯刀")
    out = asyncio.run(run(m.evolve_equip, ev))
    txt = out[0] if out else ""
    check("已装备进化成功", "进化成功" in txt, txt[:150])

    # ---------- 2. 怪异炼成 ----------
    print("[2] 怪异炼成")
    # 2a. 素材不足拦截
    clean_db()
    m = Main(None)
    make_player_lv("炼成缺材", 60)
    db.update_player(g, q, gold=999999)
    eq_b = C.generate_roster_equip("eq_tie_jian")
    give_equip(eq_b)
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "炼成 铁剑")
    out = asyncio.run(run(m.calamity_forge, ev))
    txt = out[0] if out else ""
    check("炼成素材不足拦截", "材料不足" in txt, txt[:150])
    # 2b. 成功炼成：calamity_bonus 生效 + count+1
    clean_db()
    m = Main(None)
    make_player_lv("炼成成功", 60)
    db.update_player(g, q, gold=999999)
    eq_b = C.generate_roster_equip("eq_tie_jian")
    give_equip(eq_b)
    give_mats(C.CALAMITY_COST["mats"])
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "炼成 铁剑")
    out = asyncio.run(run(m.calamity_forge, ev))
    txt = out[0] if out else ""
    check("炼成成功提示", "炼成成功" in txt or "炼成波动" in txt, txt[:150])
    inv = db.get_inventory(g, q)
    eq_d = [it for it in inv if it["key"].startswith("eq_")][0]["data"]
    check("calamity_count=1", eq_d.get("calamity_count", 0) == 1, str(eq_d.get("calamity_count")))
    check("calamity_bonus 有加成", bool(eq_d.get("calamity_bonus")), str(eq_d.get("calamity_bonus")))
    # 2c. 限 3 次：手动置 count=3 再炼成拦截
    clean_db()
    m = Main(None)
    make_player_lv("炼成限次", 60)
    db.update_player(g, q, gold=999999)
    eq_b = C.generate_roster_equip("eq_tie_jian")
    eq_b["calamity_count"] = 3
    give_equip(eq_b)
    give_mats(C.CALAMITY_COST["mats"])
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "炼成 铁剑")
    out = asyncio.run(run(m.calamity_forge, ev))
    txt = out[0] if out else ""
    check("限3次拦截(第4次)", "到极限" in txt, txt[:150])
    # 2d. engine 结算含炼成加成
    clean_db()
    eq_c = C.generate_roster_equip("eq_tie_jian")
    eq_c["calamity_bonus"] = {"atk": 0.03}
    st_a, _ = E.player_stats_detail("cls_zhan_shi", 30, {"weapon": eq_c}, 0, None, 0, None, "human")
    eq_d2 = C.generate_roster_equip("eq_tie_jian")
    st_b, _ = E.player_stats_detail("cls_zhan_shi", 30, {"weapon": eq_d2}, 0, None, 0, None, "human")
    check("炼成 atk+3% 生效", st_a["atk"] > st_b["atk"], f"{st_a['atk']} vs {st_b['atk']}")
    # 2e. 已装备炼成
    clean_db()
    m = Main(None)
    make_player_lv("炼成已装", 60)
    db.update_player(g, q, gold=999999)
    eq_b = C.generate_roster_equip("eq_tie_jian")
    db.update_player(g, q, equipment={"weapon": eq_b})
    give_mats(C.CALAMITY_COST["mats"])
    goto_smith(m, g, q)
    ev = FakeEvent(g, q, "炼成 铁剑")
    out = asyncio.run(run(m.calamity_forge, ev))
    txt = out[0] if out else ""
    check("已装备炼成成功", "炼成成功" in txt or "炼成波动" in txt, txt[:150])
    eq_now = db.get_player(g, q)["equipment"]["weapon"]
    check("已装备炼成写回 equipment", eq_now.get("calamity_count", 0) == 1, str(eq_now.get("calamity_count")))

    print()
    print(f"===== 结果：通过 {passed} / 断言 {passed + failed} =====")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
