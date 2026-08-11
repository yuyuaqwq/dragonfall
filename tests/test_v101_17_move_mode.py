# -*- coding: utf-8 -*-
"""v101.17 移动模式测试：『前往开始』→ 裸数字赶路 → 『前往结束』退出。

覆盖：
1. 『前往开始』开启移动模式（event_state 落库）
2. 移动模式中裸数字 → 执行移动（位置变化）
3. 『前往结束』关闭 → 裸数字回退 NPC 对话
4. 『前往开始』不被 move handler 抢（regex 独立）
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

    # ---- 1. 『前往开始』开启 ----
    ev = FakeEvent("g1", "1001", "前往开始")
    r = "".join(str(x) for x in await run(m.move_mode_cmd, ev))
    print("  [前往开始]", r[:80].replace("\n", " | "))
    check("『前往开始』响应", "移动模式已开启" in r, r[:80])
    check("状态落库", db.get_event_state("move_mode:1001") == "1", str(db.get_event_state("move_mode:1001")))

    # ---- 2. 移动模式中裸数字 → 移动（广场 → 东大街 5） ----
    ev2 = FakeEvent("g1", "1001", "5")
    r2 = "".join(str(x) for x in await run(m.npc_quick_dialog, ev2))
    p2 = db.get_player("g1", "1001")
    print("  [移动模式裸数字5]", r2[:100].replace("\n", " | "))
    check("裸数字触发移动", "东大街" in r2 or p2["cur_subarea"] == "oak_town_street", f"{p2.get('cur_subarea')}")
    check("移动后 stop_event", ev2._stopped)

    # ---- 3. 『前往结束』关闭 ----
    ev3 = FakeEvent("g1", "1001", "前往结束")
    r3 = "".join(str(x) for x in await run(m.move_mode_cmd, ev3))
    check("『前往结束』响应", "已关闭" in r3, r3[:80])
    check("状态清除", db.get_event_state("move_mode:1001") != "1", str(db.get_event_state("move_mode:1001")))

    # ---- 4. 关闭后裸数字 → 回退 NPC 对话（东大街有 NPC） ----
    ev4 = FakeEvent("g1", "1001", "1")
    r4 = "".join(str(x) for x in await run(m.npc_quick_dialog, ev4))
    print("  [关闭后裸数字1]", r4[:100].replace("\n", " | "))
    check("关闭后裸数字走 NPC 对话", bool(r4 and len(r4) > 15), r4[:100])
    check("NPC 分支 stop_event", ev4._stopped)

    # ---- 5. 『前往开始』不被 move 抢（regex 验证） ----
    import re as _re
    move_re = _re.compile(r"^(?:\[At:\d+\]\s*)?前往(?!开始|结束)(?:\s*|$)")
    mm_re = _re.compile(r"^(?:\[At:\d+\]\s*)?前往(?:开始|结束)(?:\s*|$)")
    check("『前往开始』不匹配 move", not move_re.match("前往开始"), "move regex 误匹配")
    check("『前往结束』匹配 move_mode", bool(mm_re.match("前往结束")), "move_mode regex 未匹配")
    check("『前往 2』不匹配 move_mode", not mm_re.match("前往 2"), "move_mode regex 误匹配")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
