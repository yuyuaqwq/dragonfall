# -*- coding: utf-8 -*-
"""v128 赶路模式测试：『位置』精简面板 + 回复 0 进入/结束赶路模式（替代 v101.17 『前往开始/结束』）。

覆盖：
1. 『位置』响应精简面板（当前位置/可前往/赶路提示）
2. 回复 0 开启赶路模式（event_state 落库）
3. 赶路模式中裸数字 → 执行移动（位置变化）
4. 赶路模式中回复 0 → 关闭（状态清除）
5. 关闭后裸数字 → 放行（不再赶路）
6. 移动落点带『回复 0 结束』提示
7. 正则矩阵：『位置』≠『地图』，旧『前往开始』不让 move 吞
"""
import sys, os, asyncio, random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import FakeEvent, run, clean_db, Main, db

random.seed(20260811)  # 固定撞怪随机

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
    from conftest import make_player
    make_player("g1", "1001", "甲", "战士")
    db.update_player("g1", "1001", cur_map="oak_town", cur_subarea="oak_town_1")
    check("造玩家", True)

    # ---- 1. 『位置』精简面板 ----
    ev = FakeEvent("g1", "1001", "位置")
    r = "".join(str(x) for x in await run(m.location_view, ev))
    print("  [位置]", r[:140].replace("\n", " | "))
    check("『位置』响应标题", "冒险者广场" in r, r[:60])
    check("『位置』有当前位置", "当前位置" in r, r[:60])
    check("『位置』有可前往", "可前往" in r, r[:60])
    check("『位置』提示回复0进赶路", "回复 0 进入赶路模式" in r, r[:140])
    check("『位置』非完整地图(无设施区)", "此地设施" not in r, "位置面板未精简")

    # ---- 2. 回复 0 开启赶路模式 ----
    ev2 = FakeEvent("g1", "1001", "0")
    r2 = "".join(str(x) for x in await run(m.npc_quick_dialog, ev2))
    print("  [0 开启]", r2[:80].replace("\n", " | "))
    check("0 开启赶路模式", "赶路模式已开启" in r2, r2[:80])
    check("状态落库", db.get_event_state("move_mode:1001") == "1", str(db.get_event_state("move_mode:1001")))
    check("0 开启后 stop_event", ev2._stopped)

    # ---- 3. 赶路模式中裸数字 → 移动（广场 → 东大街 5） ----
    ev3 = FakeEvent("g1", "1001", "5")
    r3 = "".join(str(x) for x in await run(m.npc_quick_dialog, ev3))
    p3 = db.get_player("g1", "1001")
    print("  [赶路模式裸数字5]", r3[:100].replace("\n", " | "))
    check("裸数字触发移动", "东大街" in r3 or p3["cur_subarea"] == "oak_town_street", f"{p3.get('cur_subarea')}")
    check("移动后 stop_event", ev3._stopped)

    # ---- 4. 赶路模式中回复 0 → 关闭 ----
    ev4 = FakeEvent("g1", "1001", "0")
    r4 = "".join(str(x) for x in await run(m.npc_quick_dialog, ev4))
    print("  [0 关闭]", r4[:80].replace("\n", " | "))
    check("0 关闭响应", "已结束" in r4, r4[:80])
    check("状态清除", db.get_event_state("move_mode:1001") != "1", str(db.get_event_state("move_mode:1001")))

    # ---- 5. 关闭后裸数字 → 放行（不再赶路） ----
    ev5 = FakeEvent("g1", "1001", "1")
    r5 = "".join(str(x) for x in await run(m.npc_quick_dialog, ev5))
    print("  [关闭后裸数字1]", (r5 or "（空=放行）")[:100])
    check("关闭后裸数字放行", r5 == "" and not ev5._stopped, r5[:100])

    # ---- 6. 赶路模式中移动落点带『回复 0 结束』提示 ----
    db.update_player("g1", "1001", cur_map="oak_town", cur_subarea="oak_town_1")  # 回广场
    ev6 = FakeEvent("g1", "1001", "0")
    await run(m.npc_quick_dialog, ev6)
    ev7 = FakeEvent("g1", "1001", "5")
    r7 = "".join(str(x) for x in await run(m.npc_quick_dialog, ev7))
    p7 = db.get_player("g1", "1001")
    check("移动落点带赶路提示", "回复 0 结束" in r7, r7[-140:])
    check("第6步确实移动到东大街", p7["cur_subarea"] == "oak_town_street", str(p7.get("cur_subarea")))
    ev8 = FakeEvent("g1", "1001", "0")
    await run(m.npc_quick_dialog, ev8)

    # ---- 7. 正则矩阵：『位置』≠『地图』，旧『前往开始』不让 move 吞 ----
    import re as _re
    loc_re = _re.compile(r"^(?:\[At:\d+\]\s*)?位置(?:\s*|$)")
    mv_re = _re.compile(r"^(?:\[At:\d+\]\s*)?(?:地图|周围)(?:\s*|$)")
    mm_re = _re.compile(r"^(?:\[At:\d+\]\s*)?(?:前往|移动)(?!开始|结束)(?:\s*|$)")
    check("『位置』匹配 location_view", bool(loc_re.match("位置")), "")
    check("『位置』不匹配 map_view", not mv_re.match("位置"), "map_view 误含位置")
    check("『地图』匹配 map_view", bool(mv_re.match("地图")), "")
    check("『前往开始』不匹配 move", not mm_re.match("前往开始"), "move 误吞旧指令")
    check("『前往 5』匹配 move", bool(mm_re.match("前往 5")), "")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
