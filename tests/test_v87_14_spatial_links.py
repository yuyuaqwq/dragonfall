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
    make_player("g1", "1001", "甲", "战士")
    db.update_player("g1", "1001", cur_map="oak_town", cur_subarea="oak_town_1")

    async def move(dest):
        ev = FakeEvent("g1", "1001", f"移动 {dest}")
        return "".join(str(x) for x in await run(m.move, ev))

    def pos():
        p = db.get_player("g1", "1001")
        return f"{p['cur_map']}:{p['cur_subarea']}"

    # ===== 城镇星形 =====
    print("· 城镇星形（广场连所有，场所只连广场）")
    r = await move("2")  # 广场 → 镇长办公处
    check("广场→镇长办公处", pos() == "oak_town:oak_town_2", pos())
    r = await move("3")  # 镇长办公处 → 铁匠铺：应被拦
    check("镇长办公处→铁匠铺被拦", "不能直接去" in r and "广场" in r, r[:120])
    check("位置未变", pos() == "oak_town:oak_town_2", pos())
    r = await move("1")  # 回广场
    check("镇长办公处→广场", pos() == "oak_town:oak_town_1", pos())

    # 广场可直达所有场所
    for d, tgt in [("2", "oak_town_2"), ("3", "oak_town_3"), ("4", "oak_town_4"), ("5", "oak_town_5")]:
        r = await move(d)
        check(f"广场→{tgt}", pos() == f"oak_town:{tgt}", f"{pos()} | {r[:60]}")
        await move("1")

    # 草药铺(5) 只连广场
    r = await move("5")
    check("到草药铺", pos() == "oak_town:oak_town_5", pos())
    r = await move("2")
    check("草药铺→镇长办公处被拦", "不能直接去" in r and "广场" in r, r[:120])

    # ===== 出城走城门 =====
    print("· 出城走城门")
    await move("1")  # 回广场
    r = await move("7")  # 7 = oak_meadow（邻居地图序号 = len(sas)+1 = 7）
    check("广场直接出城被拦", "城门" in r and "不能" in r, r[:120])
    check("仍在广场", pos() == "oak_town:oak_town_1", pos())
    # 到城门（oak_town 6 个子区域：1-5 + 6 城门）
    r = await move("6")
    check("广场→城门", pos() == "oak_town:oak_town_gate", f"{pos()} | {r[:80]}")
    # 从城门出城到橡木草地（邻居序号 7）
    r = await move("7")
    check("城门→橡木草地", pos() == "oak_meadow:oak_meadow_1", f"{pos()} | {r[:120]}")

    # ===== 野外线性 =====
    print("· 野外线性（相邻顺序）")
    r = await move("2")  # 草地边缘 → 草地深处
    check("草地边缘→草地深处", pos() == "oak_meadow:oak_meadow_2", pos())
    r = await move("3")  # 草地深处 → 溪边草地
    check("草地深处→溪边草地", pos() == "oak_meadow:oak_meadow_3", pos())
    r = await move("1")  # 溪边草地 → 草地边缘：被拦（要经过深处）
    check("溪边草地→草地边缘被拦", "路只有一条" in r or "先经过" in r, r[:120])
    check("位置未变", pos() == "oak_meadow:oak_meadow_3", pos())

    # ===== 进城落城门 =====
    print("· 进城落城门")
    r = await move("2")  # 溪边草地 → 草地深处
    r = await move("1")  # 草地深处 → 草地边缘
    check("回到草地边缘", pos() == "oak_meadow:oak_meadow_1", pos())
    r = await move("4")  # 草地边缘 → 橡木镇（邻居序号 = 3+1 = 4）
    check("进城落城门", pos() == "oak_town:oak_town_gate", f"{pos()} | {r[:120]}")
    r = await move("1")  # 城门 → 广场
    check("城门→广场", pos() == "oak_town:oak_town_1", pos())

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
