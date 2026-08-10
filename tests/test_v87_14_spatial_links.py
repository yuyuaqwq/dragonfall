# -*- coding: utf-8 -*-
"""v87.14 验证：空间连接——城镇星形/野外线性/城门出入"""
import sys, os, asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import FakeEvent, run, clean_db, Main, db, make_player

passed = failed = 0
def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

async def main():
    clean_db()
    db.init_db()
    m = Main(None)
    # v103.4 修复：玩家等级提到威慑线（地图 lv+5 = 6 级）——_travel_ambush 判定
    # diff <= -5 永不撞怪。原 Lv.1 vs 橡木平原 Lv.1 → diff=0 → 每次跨图 move 18% 撞怪，
    # 撞怪后位置不变导致断言随机失败（全量两次深夜跑挂、单跑偶过）。
    make_player("g1", "1001", "甲", "战士", level=10)
    db.update_player("g1", "1001", cur_map="oak_town", cur_subarea="oak_town_1")

    async def move(dest):
        ev = FakeEvent("g1", "1001", f"前往 {dest}")
        return "".join(str(x) for x in await run(m.move, ev))

    def pos():
        p = db.get_player("g1", "1001")
        return f"{p['cur_map']}:{p['cur_subarea']}"

    # ===== 城镇星形 + 街道链 =====
    # v87.16 显示=解析：广场可达 1=镇长办公处 2=铁匠铺 3=旅店 4=草药铺 5=东大街（镇郊需经东大街）
    print("· 城镇星形（广场连场所，街道链通郊外）")
    r = await move("1")  # 广场 → 镇长办公处
    check("广场→镇长办公处", pos() == "oak_town:oak_town_2", pos())
    r = await move("2")  # 镇长办公处 → 邻居（橡木平原）：非出口被拦
    check("镇长办公处直接出图被拦", "镇郊" in r or "东大街" in r, r[:120])
    check("位置未变", pos() == "oak_town:oak_town_2", pos())
    r = await move("1")  # 回广场（场所只连广场）
    check("镇长办公处→广场", pos() == "oak_town:oak_town_1", pos())

    # 广场可直达所有场所
    for d, tgt in [("1", "oak_town_2"), ("2", "oak_town_3"), ("3", "oak_town_4"), ("4", "oak_town_5")]:
        r = await move(d)
        check(f"广场→{tgt}", pos() == f"oak_town:{tgt}", f"{pos()} | {r[:60]}")
        await move("1")

    # 草药铺(4) 只连广场
    r = await move("4")
    check("到草药铺", pos() == "oak_town:oak_town_5", pos())
    r = await move("2")  # 草药铺 → 邻居（橡木平原）：非出口被拦
    check("草药铺直接出图被拦", "镇郊" in r or "东大街" in r, r[:120])
    await move("1")  # 回广场

    # ===== 街道链：出镇走东大街 → 镇郊 =====
    print("· 街道链（东大街 → 镇郊）")
    # 广场直接出城被拦（序号 6 = 邻居橡木平原，但广场不是出口子区域）
    r = await move("6")
    check("广场无直达野外", "镇郊" in r, r[:120])
    check("仍在广场", pos() == "oak_town:oak_town_1", pos())
    r = await move("5")  # 广场 → 东大街（链首）
    check("广场→东大街", pos() == "oak_town:oak_town_street", f"{pos()} | {r[:80]}")
    # 东大街可回广场/去镇郊
    r = await move("1")  # 东大街 → 镇郊（链尾）
    check("东大街→镇郊", pos() == "oak_town:oak_town_outskirts", f"{pos()} | {r[:80]}")
    # 镇郊是出口：可回东大街 + 出图
    r = await move("2")  # 镇郊 → 橡木平原（邻居序号 = 1+1 = 2）
    check("镇郊→橡木平原", pos() == "oak_plain:oak_plain_1", f"{pos()} | {r[:120]}")

    # ===== 野外线性 =====
    print("· 野外线性（相邻顺序）")
    r = await move("1")  # 草地边缘(入口) → 草地深处
    check("草地边缘→草地深处", pos() == "oak_plain:oak_plain_2", pos())
    r = await move("2")  # 草地深处 → 溪边草地
    check("草地深处→溪边草地", pos() == "oak_plain:oak_plain_3", pos())
    r = await move("2")  # 溪边草地 → 邻居（橡木镇）：非入口被拦
    check("溪边草地直接出图被拦", "草地边缘" in r, r[:120])
    check("位置未变", pos() == "oak_plain:oak_plain_3", pos())

    # ===== 进城落出口 =====
    print("· 进城落出口（镇郊）")
    r = await move("1")  # 溪边草地 → 草地深处
    r = await move("1")  # 草地深处 → 草地边缘
    check("回到草地边缘", pos() == "oak_plain:oak_plain_1", pos())
    r = await move("2")  # 草地边缘 → 橡木镇（邻居序号 = 1+1 = 2）
    check("进城落镇郊", pos() == "oak_town:oak_town_outskirts", f"{pos()} | {r[:120]}")
    r = await move("1")  # 镇郊 → 东大街
    check("镇郊→东大街", pos() == "oak_town:oak_town_street", pos())
    r = await move("2")  # 东大街 → 广场
    check("东大街→广场", pos() == "oak_town:oak_town_1", pos())

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
