# -*- coding: utf-8 -*-
"""P2 动态验证：s24 交付 → reward_item(裂鬃獠牙) 实际入包（隔离 DB，不碰共享 test_game_data.db）"""
import os, sys, shutil, asyncio

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
PRIVATE_DB = os.path.join(PLUGIN_DIR, "tmp_h4_verify_private.db")
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

async def cmd(m, name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    out = await run(getattr(m, name), ev)
    return out[-1] if out else ""

async def main():
    m = Main(None)
    await cmd(m, "register", "g1", "i1", "注册 战士 格温 男")
    db.update_player("g1", "i1", stamina=999999)
    # 注入 s24 完成态（kill 型：status=ready 即可交付）
    db.save_quests("g1", "i1", {
        "main_quest": "", "main_status": "none", "main_progress": 0,
        "daily": {}, "completed_main": [],
        "side": {"s24": {"status": "ready", "progress": {"野猪王·裂鬃": 1}}},
    })
    gmap = C.NPCS["npc_hunter_gray"]["map"]
    db.update_player("g1", "i1", cur_map=gmap)
    out = await cmd(m, "turn_in", "g1", "i1", "交付任务")
    have = db.count_item("g1", "i1", "mat_lie_zong_liao_ya")
    print("交付输出:", out.replace("\n", " | ")[:300])
    print("背包 裂鬃獠牙 数量:", have)
    ok = "获得特殊道具：裂鬃獠牙" in out and have == 1
    print("== 动态验证:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)

asyncio.run(main())
