# -*- coding: utf-8 -*-
"""调试 test_commands_apprentice.py 位置满拦截失败：逐步打印 talk state"""
import sys, os, asyncio, json
_PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PLUGIN, "tests"))
sys.path.insert(0, _PLUGIN)
from conftest import C, E, db, clean_db, Main, FakeEvent, run

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "w1", "注册 战士 旅人 男")
    db.update_player("g1", "w1", level=5, gold=1000, cur_map="oak_town", cur_subarea="oak_town_5")

    # 拜艾琳（采集）成功 → 与测试一致
    await cmd(m, "find_npc", "g1", "w1", "找 艾琳")
    await cmd(m, "talk_choice", "g1", "w1", "2")   # 答错
    await cmd(m, "talk_choice", "g1", "w1", "1")   # 答对
    await cmd(m, "talk_choice", "g1", "w1", "1")
    await cmd(m, "talk_choice", "g1", "w1", "1")
    db.add_item("g1", "w1", "草药", {}, 3)
    await cmd(m, "talk_choice", "g1", "w1", "1")
    await cmd(m, "talk_choice", "g1", "w1", "1")
    await cmd(m, "talk_choice", "g1", "w1", "1")
    out = await cmd(m, "talk_choice", "g1", "w1", "1")
    print("=== 艾琳拜师结果:", out[:80])

    # 激活 mining + cooking 占满
    db.activate_prof("g1", "w1", "mining")
    db.activate_prof("g1", "w1", "cooking")
    print("激活列表:", db.get_activated_profs("g1", "w1"))

    db.update_player("g1", "w1", cur_map="ironharbor")
    out = await cmd(m, "find_npc", "g1", "w1", "找 奥格")
    print("=== find 奥格:", out[:120].replace("\n", " | "))
    for i in range(1, 7):
        st = db.get_talk_state("g1", "w1")
        print(f"[step {i} 前] state={st}")
        out = await cmd(m, "talk_choice", "g1", "w1", "1")
        print(f"[step {i}] out={out[:150].replace(chr(10), ' | ')}")
        if i == 4:
            db.add_item("g1", "w1", "铁矿石", {}, 5)
            print("  -> 已补 5 铁矿石")

    st = db.get_talk_state("g1", "w1")
    print("最终 state:", st)

if __name__ == "__main__":
    asyncio.run(main())
