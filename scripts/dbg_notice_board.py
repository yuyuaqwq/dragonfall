# -*- coding: utf-8 -*-
"""loopback 复现：告示牌接取流程（交互告示板 → 接取 → 验证入任务栏）"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from tests.conftest import C, E, db, clean_db, Main, FakeEvent, run

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    results = await run(getattr(m, handler_name), ev)
    return results[-1] if results else ""

async def main():
    clean_db()
    m = Main(None)
    gid, qid = "g9", "b1"
    print("== 1. 注册 ==")
    out = await cmd(m, "register", gid, qid, "注册 测试员 男")
    print(out[:150].replace("\n", " | "))

    print("\n== 2. 到橡木镇广场（告示板位置 oak_town_1）==")
    db.update_player(gid, qid, cur_map="oak_town", cur_subarea="oak_town_1")

    print("\n== 3. 交互 告示板 ==")
    out = await cmd(m, "interact_prop", gid, qid, "交互 告示板")
    print(out[:400])

    print("\n== 4. 接取 找猫（s_board_cat 名称看数据）==")
    sq = next((q for q in C.SIDE_QUESTS if q.get("board")), None)
    if not sq:
        print("!! 没有 board 委托")
        return
    print(f"委托名: {sq['name']} giver: {sq['giver']}")
    out = await cmd(m, "quest_accept", gid, qid, f"接取 {sq['name']}")
    print(out[:400])

    print("\n== 5. 验证任务栏 ==")
    quests = db.get_quests(gid, qid)
    side = quests.get("side") or {}
    print("side:", {k: v for k, v in side.items() if v.get("status") == "active"})

    print("\n== 6. 重复接取（应提示已接）==")
    out = await cmd(m, "quest_accept", gid, qid, f"接取 {sq['name']}")
    print(out[:300])

asyncio.new_event_loop().run_until_complete(main())
