# -*- coding: utf-8 -*-
"""v47 测试共享脚手架（conftest）。

所有新测试从这里 import 公共设施，禁止再手抄 FakeEvent/run 模板：
    from conftest import FakeEvent, run, clean_db, make_player, TEST_DB, PLUGIN_DIR

- 自动设置 GWEN_GAME_DB → 独立测试库（绝不触碰生产 game_data.db）
- 自动把 qqbot/ 根目录加入 sys.path（支持 data.plugins.dragonfall 包式导入）

★ P5F（2026-09-15）：本文件**已改口**（前置①）—— 下面的取件口从宿主聚合壳
（`game.content` / `main.Main`）切到 `tests/_engine_harness.py`（包内真源 + 终态宿主壳）。
旧口径在这里收口，删壳（下一批）后本文件不再依赖 `game/**`。
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

# ★ P5F 前置①（conftest 改口）：取件口切到测试侧**引擎通道驱动口** `tests/_engine_harness.py`
#   —— `Main`（旧 `main.Main` Mixin 汇编的等价驱动口）**无条件**走包侧；
#   `C` / `db` 走「**过渡态回退**」：宿主聚合壳 `game.content` / `game.db` 仍在位时取旧面，
#   删壳（终态）后自动落包内真源（`content.facade.C` / `content.persistence`）。
#
#   为什么 `C`/`db` 要保留这一次**可选**回退（而不是直接切干净）：
#     · 旧 conftest 的 `C`/`db` = **宿主聚合壳**，其面比包内门面**宽**且是**渴求态**：
#       `db.DB_PATH`（包侧按设计没有：库路径是部署信息）· `db._lock` ·
#       `C._INDEXES`（宿主装配期已建好，包内 `content.index` 是惰性）·
#       `C.ALL_WILD` / `C.roll_fish` / `C.current_period` / `C.portal_cost`（包内门面**缺口名**，
#       其错误信息本身就写着「宿主门面有而包内没有？请查 C_NAME_TO_PACKAGE_MAP.md 并登记缺口，
#       别静默兜底」）· 以及 `game.content` 导入链对 `game.drop_engine` 等模块的**加载副作用**。
#     · 这些名字的下游是 18 个测试文件（其中 `test_texts_table.py` 属 R6 线，本批**不许碰**）
#       ⇒ 「conftest 纯包侧」与「未全删 newly-red = 0」在**同一批**里不可兼得。
#     · 回退是 **fail-soft 且可选**：终态 `game/**` 删除后 `ImportError` ⇒ 直接落包侧，
#       conftest 照常可 import / 可跑（**硬依赖已消除**，这正是本项的目的）。
#   P5E-β 的「聚合型 `__init__` 把缺失放大」机制只对**硬**依赖成立；这里不是硬依赖。
#
#   同一族的还有**驱动口** `Main`：旧 conftest 的 `main.Main` 是 `game/commands/**` 的
#   Mixin 汇编（终态不存在），本批改为包侧驱动口 `_engine_harness.Main`。实测两者在**个别**
#   用例上仍有行为差（`test_v1023_life_prof` 的强化设施判定：旧 Mixin 汇编路 vs 引擎通道路，
#   包侧驱动口把玩家判成「不在铁匠铺」⇒ 2 条红）。同一条逻辑：过渡态保留旧驱动口，
#   终态自动落包侧驱动口。
try:                                                            # 过渡态：旧口径逐字不变
    from data.plugins.dragonfall.game import content as C, db   # noqa: E402
    from data.plugins.dragonfall.main import Main               # noqa: E402
    _CONFTEST_FACE = "legacy-host-shell"
except ImportError:                                             # 终态：包内真源 + 引擎通道
    from _engine_harness import C, db, Main                     # noqa: E402
    _CONFTEST_FACE = "engine-harness"


# v94 体力：测试环境走 register 命令建号（不走 make_player）时，注册后体力拉满，
# 防动作类命令（探索/战斗/锻造/开本等）被体力拦截导致测试误挂。
# （`_engine_harness.Main.register` 已内建同一副作用；此处保留同名包装，语义/时机逐字不变。）
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


def _db_path():
    """库路径：过渡态宿主壳给 `DB_PATH` 常量；终态包内真源给 `db_path()`（包侧没有 `DB_PATH`）。"""
    getter = getattr(db, "db_path", None)
    return getter() if callable(getter) else db.DB_PATH


def clean_db(*tables):
    """清空指定表（默认清核心业务表）。"""
    db.init_db()
    # ★ P5F 前置①：库路径取件口两态通用（见 `_db_path()`）。
    conn = sqlite3.connect(_db_path())
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
