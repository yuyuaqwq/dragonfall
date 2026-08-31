# -*- coding: utf-8 -*-
"""v134.x 冒烟：镇长办公处（oak_town_2，有 PROPS 无 POI）地图面板『✨ 可交互场景』换行检查。

用法：GWEN_GAME_DB=<私有测试库> python tests/_smoke_map_newline.py
（独立私有库，不碰共享 test_game_data.db / 生产 game_data.db）
"""
import sys, os, asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import FakeEvent, run, clean_db, Main, db

passed = failed = 0

def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

# 面板区块标题（v132 公共区块，标题行前必须恰有一个空行）
BLOCK_TITLES = ["🏪 此地设施：", "🔎 可探索触发：", "✨ 可交互场景：",
                "👥 这里的 NPC：", "🧭 游历的旅人：", "👤 此地的玩家：",
                "🐾 此地的怪物 ("]

async def main():
    clean_db()
    db.init_db()
    m = Main(None)
    ev = FakeEvent("g1", "1001", "注册 战士 甲 男")
    await run(m.register, ev)

    # 前往 1 = 镇长办公处（oak_town_2）
    ev = FakeEvent("g1", "1001", "前往 1")
    await run(m.move, ev)
    p = db.get_player("g1", "1001")
    check("位于镇长办公处 oak_town_2", p.get("cur_subarea") == "oak_town_2",
          str(p.get("cur_subarea")))

    ev = FakeEvent("g1", "1001", "地图")
    r = "".join(str(x) for x in await run(m.map_view, ev))
    lines = r.split("\n")

    print("======== 地图面板（镇长办公处）========")
    for i, ln in enumerate(lines):
        print(f"{i:>2}| {ln}")
    print("=======================================")

    # 1) 存在性
    check("面板含『✨ 可交互场景』", any("✨ 可交互场景" in x for x in lines))
    check("面板无『🔎 可探索触发』（本子区域无 POI）",
          not any("🔎 可探索触发" in x for x in lines))

    # 2) 核心断言：每个区块标题前恰有一个空行（上一行为空、上上行为内容行）
    seen = 0
    for i, ln in enumerate(lines):
        if any(ln.startswith(t) for t in BLOCK_TITLES):
            seen += 1
            prev_ok = i >= 1 and lines[i - 1] == ""
            prevprev_ok = i >= 2 and bool(lines[i - 2].strip())
            check(f"标题[{ln[:12]}…] 前恰有一个空行",
                  prev_ok and prevprev_ok,
                  f"上一行={lines[i-1]!r} 上上行={lines[i-2]!r}")
    check("至少 1 个区块标题被检查", seen >= 1, f"seen={seen}")

    # 3) 无双空行（区块间分隔统一：空行至多连续一个）
    bad = [i for i in range(1, len(lines)) if lines[i] == "" and lines[i - 1] == ""]
    check("无连续双空行", not bad, f"双空行位置 {bad}")

    # 4) 到达视图（移动返回）同样有换行（_map_blocks 同源）
    ev = FakeEvent("g1", "1001", "前往 1")
    r2 = "".join(str(x) for x in await run(m.move, ev))
    lines2 = r2.split("\n")
    for i, ln in enumerate(lines2):
        if ln.startswith("✨ 可交互场景"):
            check("到达视图『✨ 可交互场景』前有空行",
                  i >= 1 and lines2[i - 1] == "", repr(lines2[i - 1]))
            break

    print(f"\n通过 {passed} / 失败 {failed}")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    asyncio.run(main())
