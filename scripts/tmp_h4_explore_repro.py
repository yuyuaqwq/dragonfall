# -*- coding: utf-8 -*-
"""隔离复现：_handle_explore_event 是否导致玩家行消失（验证与 quests.py reward_item 无关）"""
import os, sys, shutil, asyncio

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
PRIVATE_DB = os.path.join(PLUGIN_DIR, "tmp_h4_explore_private.db")
shutil.copyfile(os.path.join(PLUGIN_DIR, "test_game_data.db"), PRIVATE_DB)
os.environ["GWEN_GAME_DB"] = PRIVATE_DB
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from data.plugins.dragonfall.game import content as C, db
from data.plugins.dragonfall.main import Main

class FakeEvent:
    def __init__(self, group_id, qq_id, msg=""):
        self._g, self._q, self.message_str = group_id, qq_id, msg
        self._stopped = False
    def get_group_id(self): return self._g
    def get_sender_id(self): return self._q
    def get_message_str(self): return self.message_str
    def plain_result(self, text): return text
    def stop_event(self): self._stopped = True

async def run(handler, ev):
    gen = handler(ev)
    results = []
    try:
        while True:
            results.append(await gen.__anext__())
    except StopAsyncIteration:
        pass
    return results

async def main():
    m = Main(None)
    ev = FakeEvent("g1", "w1", "注册 战士 测试 男")
    await run(m.register, ev)
    db.update_player("g1", "w1", stamina=999999, gold=50, exp=0, cur_map="oak_plain", cur_subarea="")
    print("explore 前玩家存在:", db.get_player("g1", "w1") is not None)
    try:
        handled, ev_text = m._handle_explore_event("g1", "w1", db.get_player("g1", "w1"), C.MAP_BY_ID["oak_plain"])
        print("explore 返回:", handled, str(ev_text)[:120].replace("\n", " | "))
    except Exception as e:
        print("explore 抛异常:", type(e).__name__, str(e)[:200])
    p = db.get_player("g1", "w1")
    print("explore 后玩家存在:", p is not None)
    ok = p is not None
    print("== 隔离复现:", "玩家存活(与 quests.py 无关，问题在 explore 路径)" if ok else "玩家消失(explore 路径回归)")
    sys.exit(0 if ok else 1)

asyncio.run(main())
