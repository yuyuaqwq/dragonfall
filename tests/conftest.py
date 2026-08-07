# -*- coding: utf-8 -*-
"""v47 测试共享脚手架（conftest）。

所有新测试从这里 import 公共设施，禁止再手抄 FakeEvent/run 模板：
    from conftest import FakeEvent, run, clean_db, make_player, TEST_DB, PLUGIN_DIR

- 自动设置 GWEN_GAME_DB → 独立测试库（绝不触碰生产 game_data.db）
- 自动把 qqbot/ 根目录加入 sys.path（支持 data.plugins.dragonfall 包式导入）
"""
import os
import sys
import asyncio
import sqlite3

# ---- 路径 ----
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dragonfall/
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))  # dragonfall/ → plugins/ → data/ → qqbot/
TEST_DB = os.path.join(PLUGIN_DIR, "test_game_data.db")

# 必须在 import 插件前设置（db.py 模块级读取 DB_PATH）
os.environ["GWEN_GAME_DB"] = TEST_DB
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from data.plugins.dragonfall.game import content as C, db, engine as E  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.main import Main  # noqa: E402


class FakeEvent:
    """模拟 AstrBot 消息事件。"""

    def __init__(self, group_id, qq_id, msg=""):
        self._g = group_id
        self._q = qq_id
        self.message_str = msg

    def get_group_id(self):
        return self._g

    def get_sender_id(self):
        return self._q

    def get_message_str(self):
        return self.message_str

    def plain_result(self, text):
        return text


async def run(handler, ev):
    """调用 async handler，收集全部 yield 结果。"""
    gen = handler(ev)
    results = []
    try:
        while True:
            results.append(await gen.__anext__())
    except StopAsyncIteration:
        pass
    return results


def clean_db(*tables):
    """清空指定表（默认清核心业务表）。"""
    db.init_db()
    conn = sqlite3.connect(db.DB_PATH)
    try:
        targets = tables or (
            "players", "player_groups", "inventory", "quests", "battle_state",
            "achievements", "stats", "feedback", "market", "bestiary",
            "guilds", "guild_members", "party", "pets", "pet_dex", "reputation", "signin", "fishing",
            "visited", "world_event", "event_state", "professions",
        )
        for t in targets:
            conn.execute(f"DELETE FROM {t}")
        conn.commit()
    finally:
        conn.close()


def make_player(gid="g1", qid="q1", name="测试", cls="战士", level=1):
    """落库一个玩家，返回 player dict。"""
    db.create_player(gid, qid, name, cls, {}, 100, 100)
    return db.get_player(gid, qid)


def new_main():
    """干净实例（带独立清理后的测试库）。"""
    clean_db()
    return Main(None)


# 让测试脚本直接 `python tests/test_xxx.py` 也能跑（无 pytest 环境）
if __name__ == "__main__":
    print(f"conftest OK: TEST_DB={TEST_DB}")
    print(f"  content 表数量: {len([k for k in dir(C) if k.isupper() and isinstance(getattr(C, k), dict)])}")
    print(f"  Main Mixin: {[c.__name__ for c in Main.__mro__ if c.__name__ != 'object']}")
