# -*- coding: utf-8 -*-
"""v47 测试共享脚手架（conftest）。

所有新测试从这里 import 公共设施，禁止再手抄 FakeEvent/run 模板：
    from conftest import FakeEvent, run, clean_db, make_player, TEST_DB, PLUGIN_DIR

- 自动设置 GWEN_GAME_DB → 独立测试库（绝不触碰生产 game_data.db）
- 自动把 qqbot/ 根目录加入 sys.path（支持 data.plugins.dragonfall 包式导入）

★ P5C：本文件是**最后一个**改口的枢纽 —— 各测试族分块改口到 `_engine_harness`
（包 + 引擎通道）期间，本文件保持旧口径，保证「每块复绿」；等 `tests/**` 里再无
`game.*` 引用（grep 判据 ② == 0）后，才把下面这两行 import 切到包侧。
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
# R3 P3-4：setdefault 尊重测试脚本预置的独立私有库（test_v95_76/77 等用
# 各自 test_<名>.db），不再强制覆盖——消除共享 test_game_data.db 顺序执行
# 残留导致的偶发红（v95_77 曾在 line 48 因残留 battle 为 None 崩）
os.environ.setdefault("GWEN_GAME_DB", TEST_DB)
# v110.5 X3：显式测试模式标记——dialogue.check_need 据 GWEN_TEST_MODE=1 在测试环境
# 对未知条件键直接 raise（与库名含 "test" 的旧约定双保险，消除私有库名不含 "test"
# 时测试行为漂移导致的假失败）。
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
# 引擎框架包（S8 物理分离）：引擎在独立仓库，本仓以 submodule 接入 `framework/`，
# 包名 `saintess_engine`。接线在这里做一次，全部 `from conftest import …` 的测试即可解析。
sys.path.insert(0, os.path.join(PLUGIN_DIR, "framework"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # tests/（`_engine_harness`）

# v117.5 测试提速：shim astrbot（平台适配层替身，行为等价，省 ~3s/进程 import）。
# 游戏命令层用到的 astrbot 符号都是注册副作用装饰器+类型标注+简单数据类，
# 见 tests/shim_astrbot/README.md。设 GWEN_NO_SHIMMED_ASTRBOT=1 退回真实 astrbot（对照验证用）。
if os.environ.get("GWEN_NO_SHIMMED_ASTRBOT") != "1":
    _SHIM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
    if os.path.isdir(_SHIM_DIR) and _SHIM_DIR not in sys.path:
        sys.path.insert(0, _SHIM_DIR)

from data.plugins.dragonfall.game import content as C, db  # noqa: E402
from data.plugins.dragonfall.main import Main  # noqa: E402


# v94 体力：测试环境走 register 命令建号（不走 make_player）时，注册后体力拉满，
# 防动作类命令（探索/战斗/锻造/开本等）被体力拦截导致测试误挂。
_orig_register = Main.register
async def _register_with_stamina(self, event):
    gid = event.get_group_id() or "private"
    qid = event.get_sender_id() or "unknown"
    async for r in _orig_register(self, event):
        yield r
    try:
        db.update_player(gid, qid, stamina=999999)
    except Exception:
        pass
Main.register = _register_with_stamina


class FakeEvent:
    """模拟 AstrBot 消息事件。"""

    def __init__(self, group_id, qq_id, msg=""):
        self._g = group_id
        self._q = qq_id
        self.message_str = msg
        self._stopped = False

    def get_group_id(self):
        return self._g

    def get_sender_id(self):
        return self._q

    def get_message_str(self):
        return self.message_str

    def plain_result(self, text):
        return text

    def stop_event(self):
        """v101.16：npc_quick_dialog 测试需要（拦截后续 handler 的标记）。"""
        self._stopped = True


async def run(handler, ev):
    """调用 async handler，收集全部 yield 结果。

    v139 兼容：普通 async def（无 yield，如 _maint_gate v134.7 后静默 stop）直接 await，
    返回 []；async generator（有 yield，有 asend 方法）逐个收集。"""
    gen = handler(ev)
    results = []
    try:
        # async generator 有 asend 方法；普通 coroutine 没有
        if hasattr(gen, "asend"):
            while True:
                results.append(await gen.__anext__())
        else:
            await gen
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
            "visited", "world_event", "event_state", "professions", "props_use",
            "visited_subareas", "possessed",
        )
        for t in targets:
            conn.execute(f"DELETE FROM {t}")
        conn.commit()
    finally:
        conn.close()


def make_player(gid="g1", qid="q1", name="测试", cls="战士", level=1):
    """落库一个玩家，返回 player dict。"""
    # v87.17 与真实注册一致：中文职业名 → 内部 cls_id（如 战士 → cls_zhan_shi）
    cls_id = C.resolve("classes", cls) if hasattr(C, "resolve") else cls
    db.create_player(gid, qid, name, cls_id, {}, 100, 100)
    p = db.get_player(gid, qid)
    if level > 1:
        db.update_player(gid, qid, level=level)
    # v94 体力：测试环境体力拉满（999999），防动作类命令被体力拦截
    db.update_player(gid, qid, stamina=999999)
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
