# -*- coding: utf-8 -*-
"""测试侧「引擎通道」驱动口（P5C：宿主壳删除后 tests/** 的唯一入口）。

改造前：`tests/**` 靠**宿主壳**驱动命令 —— `Main`（`game/commands/*` 的 Mixin 汇编）
`getattr(m, "<handler>")(event)` → `game.commands._host_bridge.run/run_async`
→ 引擎包对象 → 声明守卫 → `Env` → 包内 handler → 文本段。

改造后：宿主壳那一层换成**终态宿主壳** `host/shell.py::HostShell`（引擎通用那一半 +
内容规则转引包内真源 + 平台面），本文件只补**测试专有的三件事**：

    ① 平台适配器（三函数 `recv` / `load_player`+`save_player` / `say`）—— 存档走包内存档半边；
    ② 引擎通道装配（`load_package(inject=…)` → `install_engine()` → 声明注册表 → 处理器表）；
    ③ `Main`：保留旧测试的调用面（`getattr(m, "<handler>")(event)` / `await Main.register(...)`），
       把 handler 名按**包内声明表**派到引擎通道，并按旧宿主壳的**消息框定口径**返回。

「handler 名 → 声明 key」从包内命令表派生（`content/data/commands.json` +
`content/commands.py::COMMANDS`），测试侧**不抄任何映射表**：包内既有约定是
「声明 key ≡ 旧宿主壳方法名」（`@declared(key) async def key(...)`）。

`say` 框定口径为什么是「同步族 join / 异步族逐段」：旧宿主壳有两条桥（`_host_bridge.run`
= `"\\n".join` 成一条 / `run_async` = 逐段），包内 handler 的「同步 / 协程」与之 **0 处不一致**
（P5B 当次实测，191 条桥接）。故按 handler 是否 awaitable 判定即可，无需测试侧携带宿主信息。

非命令名（`self._xxx` 私有助手）：`Main.__getattr__` 依次找
① 包内声明表里的处理器 → 引擎通道；② 包内实现类（`combat_cmds.CombatCmds` /
`economy_cmds.EconomyImpl` / `instance_cmds.InstanceImpl` / `cmds_instance_router.InstanceRouterImpl`）的方法；
③ 包内模块级函数。都找不到 → `AttributeError`（不静默）。
"""
from __future__ import annotations

import functools
import importlib
import inspect
import json
import logging
import os
import pkgutil
import re
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(_HERE)                      # dragonfall/
PKG_ROOT = os.path.join(PLUGIN_DIR, "framework", "games", "orlandia")
_ENGINE_ROOT = os.path.join(PLUGIN_DIR, "framework")

for _p in (_ENGINE_ROOT, PLUGIN_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from saintess_engine.host import Host as _EngineHost                          # noqa: E402
from saintess_engine.host import load_package, run_guards                     # noqa: E402
from host.shell import HostShell                                              # noqa: E402
from host import _platform                                                    # noqa: E402

__all__ = ["Main", "EngineHarness", "harness", "boot", "reset_for_tests", "C",
           "PKG_ROOT", "GameCmdFilter", "tlog_setup",
           # conftest 兼容面
           "FakeEvent", "run", "clean_db", "make_player", "new_main",
           "TEST_DB", "PLUGIN_DIR", "QQBOT_DIR"]

_IDENTITY_KEYS = ("group_id", "qq_id", "uid")
_PLATFORM_EXCEPTIONS = ("_maint_gate", "page_flip", "shortcut_trigger", "gm_play", "gm_spy")


# ============================================================ ① 平台三函数适配器
class _Adapter(object):
    """三函数（`recv` / `load_player` + `save_player` / `say`）—— 存档层 = 包内存档半边。"""

    def __init__(self, harness):
        self.h = harness
        self.gid = "g1"
        self.uid = "q1"
        self.said = []
        self.events = []
        self.blobs = {}
        self.tlogs = []
        self.clock_value = None

    def recv(self):
        return None

    def load_player(self, uid):
        """不存在 → `{}`（假值）。`None` 会让引擎走「新玩家建初始档」，与旧宿主壳口径不同。"""
        return self.h.db.get_player(self.gid, str(uid)) or {}

    def save_player(self, uid, data):
        """≡ 旧宿主桥 `_host_bridge._save_player`：剔平台身份列 → `update_player`（不吞异常）。"""
        if not isinstance(data, dict):
            return
        fields = {k: v for k, v in data.items() if k not in _IDENTITY_KEYS}
        if fields:
            self.h.db.update_player(self.gid, str(uid), **fields)

    def say(self, to, text):
        if text:
            self.said.append(str(text))

    def clock(self):
        return self.clock_value if self.clock_value is not None else time.time()

    def on_tlog(self, record):
        self.tlogs.append(record)

    def load_blob(self, key):
        return self.blobs.get(key)

    def save_blob(self, key, value):
        self.blobs[key] = value


# ============================================================ 引擎 Host（补 async handler）
def _make_host_class():
    """派生引擎 `Host`：`build_env` 注入壳 + `invoke_async` 补 await 分支。

    「补 await」为什么必须：包内大量 handler 是 `async def fn(env) -> list[str]`，
    引擎 `Host.invoke` 是同步的。旧宿主桥 `_host_bridge.run_async` 自己 await；
    此处按同样顺序补齐（**不改引擎**）。
    """

    class _TestHost(_EngineHost):
        shell = None

        def build_env(self, key, spec, ctx, player, *, raw=None):
            env = super().build_env(key, spec, ctx, player, raw=raw)
            if self.shell is not None:
                env.state = dict(env.state or {})
                env.state["shell"] = self.shell
            return env

        async def invoke_async(self, spec, ctx, player, *, raw=None):
            key = str(getattr(spec, "key", "") or "")
            entry = self.handlers.get(key) if self.pkg else None
            if not entry:
                return self.declared_echo(spec)
            fn = self.pkg.resolve_handler(entry.get("handler")) if self.pkg else None
            if fn is None:
                return ["【%s】包内处理器未解析：%r（检查 content/commands.py 的 handler 引用）"
                        % (key, entry.get("handler"))]
            env = self.build_env(key, spec, ctx, player, raw=raw)
            guards = entry.get("guards")
            if guards is None:
                guards = list(getattr(spec, "guards", ()) or ())
            blocked = run_guards(guards, env, builtin=self.builtin_guards(),
                                 hooks=(self.pkg.guard_hooks() if self.pkg else {}))
            if blocked:
                return [blocked]
            out = fn(env)
            if hasattr(out, "__await__"):
                out = await out
            return self._as_replies(out)

    return _TestHost


def _binds_shell(fn):
    """包内函数是否以「宿主壳」为第一参数（`def fn(self, …)` / `def fn(shell, …)`）。"""
    try:
        params = list(inspect.signature(fn).parameters)
    except (TypeError, ValueError):
        return False
    return bool(params) and params[0] in ("self", "shell")


def _unwrap_register_lambda(fn):
    """`content/commands.py::register` 把实现塞进 lambda 默认参数 → 取回真实现。"""
    seen = 0
    while (callable(fn) and getattr(fn, "__name__", "") == "<lambda>"
           and fn.__defaults__ and seen < 3):
        nxt = fn.__defaults__[0]
        if not callable(nxt):
            break
        fn = nxt
        seen += 1
    return fn


# ============================================================ ③ 驱动口
class EngineHarness(object):
    """引擎通道驱动口：`make_handler(key)(event)` → 文本段（按旧宿主壳的消息框定）。"""

    def __init__(self, db_path=None, seed=None, clock=None):
        self.db_path = db_path or os.environ.get("GWEN_GAME_DB")
        self.seed = seed
        self.clock = clock
        self.adapter = None
        self.host = None
        self.shell = None
        self.inject = {}
        self.facade = None
        self.db = None
        self.rules = None
        self._decls = None
        self._handlers = None
        self._mods = None
        self._impl_classes = None
        self._async_cache = {}
        self._decl_pats = None

    # ------------------------------------------------------------ 装配
    def boot(self):
        if self.host is not None:
            return self
        global _HARNESS
        _HARNESS = self            # ★ 先登记：`Main()` 构造期会回调 `harness()`（防递归重建）
        inject = {
            "db_path": self.db_path,
            "clock": time.time,
            "log": logging.getLogger("dragonfall"),
            "flush_log": logging.getLogger("dragonfall").debug,
            "tlog": None,
        }
        self.inject = inject
        self.adapter = _Adapter(self)
        if self.clock is not None:
            self.adapter.clock_value = float(self.clock)
        host_cls = _make_host_class()
        kwargs = {"seed": self.seed, "id_key": "qq_id", "inject": inject}
        self.host = host_cls(self.adapter, PKG_ROOT, **kwargs)
        # ---- 装配四步（与引擎 Host.boot 同序同内容，用公开 API 逐项调）----
        self.host.pkg = load_package(PKG_ROOT, inject=inject)   # ① 先 bind 扇出
        self.facade = importlib.import_module("content.facade")
        self.db = importlib.import_module("content.persistence")
        self.rules = importlib.import_module("content.cmds_base_rules")
        self.host.pkg.install_engine()                          # ② 引擎 hook
        from saintess_engine.command import CommandRegistry      # ③ 声明注册表
        try:
            self.host.commands = CommandRegistry(name=self.host.pkg.id).load(
                self.host.pkg.command_declarations())
        except Exception:                                        # noqa: BLE001
            self.host.commands = CommandRegistry(name=self.host.pkg.id)
        self.host.handlers = dict(self.host.pkg.command_handlers())   # ④ 处理器表
        self.host.texts = self._load_texts()
        # ---- 壳 ----
        self.shell = Main()
        self.shell.bind_package(self.host.pkg)
        self.shell.context = getattr(self.adapter, "context", None)
        self.host.shell = self.shell
        Main._static_source = self.declarations_for_static
        # 包内文案表接线（≡ 宿主薄壳 `content/flow/instance_gate.set_text_table`）
        try:
            self.host.pkg.optional_submodule("flow").instance_gate.set_text_table(
                importlib.import_module("content.texts").table())
        except Exception:                                        # noqa: BLE001
            pass
        self._decls = dict(self.host.pkg.command_declarations() or {})
        self._handlers = dict(self.host.handlers or {})
        # 平台 gate 过滤器的「游戏指令正则」供体（包内声明表；宿主件零包知识）
        _platform._GameCmdFilter.set_pattern_source(self.declaration_patterns)
        return self

    def _load_texts(self):
        try:
            data = self.host.pkg.domain(self.host.texts_domain) if self.host.pkg else {}
            if not isinstance(data, dict) or not data:
                return None
            from saintess_engine.text import TextTable
            return TextTable.from_data(data, name=self.host.pkg.id)
        except Exception:                                        # noqa: BLE001
            return None

    # ------------------------------------------------------------ 表 / 名字落点
    def is_declared(self, name):
        return name in (self._decls or {})

    def has_handler(self, key):
        return key in (self._handlers or {})

    def declarations_for_static(self):
        """`[(compiled_re, key)]` —— 引擎 `_find_handler` 的静态兜底表（包内声明为真源）。"""
        out = []
        for key, spec in (self._decls or {}).items():
            for pat in (spec.get("patterns") or []):
                try:
                    out.append((re.compile(pat), key))
                except re.error:
                    continue
        return out

    def declaration_patterns(self):
        """包内声明表的**合并正则**列表（引擎 `combine_patterns` 口径；懒缓存）。"""
        if self._decl_pats is None:
            from saintess_engine.command import combine_patterns
            pats = []
            for key, spec in (self._decls or {}).items():
                one = [p for p in (spec.get("patterns") or []) if p]
                if not one:
                    continue
                pats.append(one[0] if len(one) == 1 else combine_patterns(one))
            self._decl_pats = pats
        return self._decl_pats

    def _mods_index(self):
        if self._mods is None:
            self._mods = {}
            import content
            for mi in pkgutil.walk_packages(content.__path__, "content."):
                try:
                    mod = importlib.import_module(mi.name)
                except Exception:                                # noqa: BLE001
                    continue
                self._mods[mi.name] = mod
        return self._mods

    def _classes(self):
        if self._impl_classes is None:
            self._impl_classes = []
            for ref in ("content.combat_cmds:CombatCmds",
                        "content.economy_cmds:EconomyImpl",
                        "content.instance_cmds:InstanceImpl",
                        "content.cmds_instance_router:InstanceRouterImpl"):
                mod, _, attr = ref.partition(":")
                try:
                    self._impl_classes.append(getattr(importlib.import_module(mod), attr))
                except Exception:                                # noqa: BLE001
                    continue
        return self._impl_classes

    def impl_method(self, name):
        for cls in self._classes():
            attr = getattr(cls, name, None)
            if attr is not None:
                return attr
        return None

    def impl_classes(self):
        return self._classes()

    def module_function(self, name):
        for mod_name, mod in self._mods_index().items():
            fn = getattr(mod, name, None)
            if callable(fn) and getattr(fn, "__module__", "") == mod_name:
                return fn
        return None

    # ------------------------------------------------------------ 驱动
    def _spec(self, key):
        spec = self.host.commands.get(key)
        if spec is None:
            raise KeyError("包内声明表没有 key=%r（测试侧驱动口不接受未声明的名字）" % key)
        return spec

    async def _invoke_by_key(self, key, event):
        """一条声明 → 引擎链（声明项 / 守卫 / Env / 包内 handler）→ 文本段（不框定）。"""
        spec = self._spec(key)
        gid, qid = self.shell._uid(event)
        ad = self.adapter
        ad.gid, ad.uid = gid, qid
        ad.said = []
        player = self.db.get_player(gid, qid) or {}
        ctx = {"uid": str(qid), "group_id": str(gid),
               "text": event.get_message_str() or "",
               "is_group": bool(event.get_group_id()), "at": [],
               "ts": time.time(), "raw": event}
        return await self.host.invoke_async(spec, ctx, player, raw=event)

    def _is_async_handler(self, key):
        if key not in self._async_cache:
            entry = (self._handlers or {}).get(key) or {}
            fn = _unwrap_register_lambda(self.host.pkg.resolve_handler(entry.get("handler")))
            self._async_cache[key] = bool(fn) and inspect.iscoroutinefunction(fn)
        return self._async_cache[key]

    def _frame(self, key, replies):
        """旧宿主壳的消息框定：同步族 → `"\\n".join` 成一条；异步族 → 逐段。"""
        replies = [r for r in (replies or []) if r not in (None, "")]
        if self._is_async_handler(key):
            return [str(r) for r in replies]
        return ["\n".join(str(r) for r in replies)] if replies else []

    def make_handler(self, key):
        h = self

        async def _handler(event):
            replies = await h._invoke_by_key(key, event)
            for seg in h._frame(key, replies):
                yield seg

        _handler.__name__ = key
        return _handler

    def call(self, name, event):
        return self.make_handler(name)(event)


# ============================================================ 对外：Main（旧名，新实现）
class Main(HostShell):
    """旧测试里的 `Main`：**驱动口**（终态宿主壳 + 引擎通道派发）。

    对外保留同名 handler 方法面（`getattr(m, "<handler>")(event)` /
    `await Main.register(...)`），实现走引擎 host 通道；非命令私有名转发到包内同名实现。
    `Main(None)` 的入参（旧 `context`）保留（平台发送面）。
    """

    def __init__(self, context=None):
        super().__init__(pkg=harness().host.pkg, store=harness().db,
                         context=context, events=harness().adapter.events)
        self.context = context

    async def register(self, event):
        """注册命令（引擎通道）+ 旧 conftest 的「注册后体力拉满」语义（同一副作用同一时机）。"""
        h = harness()
        replies = await h._invoke_by_key("register", event)
        gid, qid = h.shell._uid(event)
        try:
            h.db.update_player(gid, qid, stamina=999999)
        except Exception:                                        # noqa: BLE001
            pass
        for seg in h._frame("register", replies):
            yield seg

    # ---- 非命令名：包内落点 ----
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        h = harness()
        # ① 声明表里有处理器 → 引擎通道（**唯一**命令驱动路径）
        if h.is_declared(name) and h.has_handler(name):
            return h.make_handler(name)
        # ② 包内实现类的方法（CombatCmds / EconomyImpl / InstanceImpl / InstanceRouterImpl）
        attr = h.impl_method(name)
        if attr is not None:
            if not callable(attr):
                return attr
            if _is_staticmethod(h, name):
                return attr
            if _binds_shell(attr):
                return functools.partial(attr, self)
            return attr
        # ③ 包内模块级函数
        fn = h.module_function(name)
        if fn is not None:
            return functools.partial(fn, self) if _binds_shell(fn) else fn
        raise AttributeError("%s has no attribute %r（包内无同名落点）"
                             % (type(self).__name__, name))


def _is_staticmethod(h, name):
    for cls in h.impl_classes():
        try:
            if isinstance(inspect.getattr_static(cls, name), staticmethod):
                return True
        except AttributeError:
            continue
    return False


_HARNESS = None


def harness():
    global _HARNESS
    if _HARNESS is None:
        _HARNESS = EngineHarness().boot()
    return _HARNESS


def boot():
    """确保「包路径 + 引擎通道装配」完成（幂等）。

    = 改造前 `game.content_rules.apply.ensure_engine_configured()` /
    `game.bootstrap.package_apply()` 在测试侧的等价入口（同一个幂等装配语义）。
    """
    return harness()


def reset_for_tests():
    """重建驱动口（私有库切换 / 猴补还原后调用；正常路径不需要）。"""
    global _HARNESS
    _HARNESS = None
    HostShell._STATIC_HANDLERS = None
    HostShell._COMMAND_PATTERNS = None
    return harness()


#: 包内聚合门面（引擎约定接口 `content/facade.py::C`）——**装配完成后**才取件
C = harness().facade.C

#: 包内存档半边（≡ 旧宿主 `game.db` 的调用面；`DB_PATH` → `db_path()`）
db = harness().db


# ============================================================ 平台面（测试侧）
#: 停服 gate 的过滤器 —— **宿主件**（`host/_platform.py::_GameCmdFilter`，P5C 从原
#: `game/commands/base.py` 迁入）。这里只登记「游戏指令正则」供体（包内声明表）。
GameCmdFilter = _platform._GameCmdFilter


class _TlogHolder(object):
    """流水句柄（`content.obs.bind(tlog=…)` 的宿主侧替身）。

    公开面 = 旧宿主 `game/tlog_setup.py`（enable/disable/enabled/kinds/ENV_FLAG），
    实现用引擎 `saintess_engine.tlog` + 包内 `tlogs` 域。
    """

    ENV_FLAG = "DRAGONFALL_TLOG"

    def __init__(self):
        self._t = None

    def kinds(self):
        from saintess_engine.tlog import KindTable
        return KindTable.from_data(harness().host.pkg.domain("tlogs"),
                                   name=harness().host.pkg.id)

    def enable(self, sinks=None, *, strict=False):
        from saintess_engine.tlog import JSONLSink, TLog
        if sinks is None:
            sinks = [JSONLSink(os.path.join(PLUGIN_DIR, "data", "tlog.jsonl"))]
        self._t = TLog(sinks=list(sinks), kinds=self.kinds())
        import content.obs as _obs
        _obs.bind(tlog=self)
        return self._t

    def disable(self):
        self._t = None
        import content.obs as _obs
        _obs.bind(tlog=self)

    def tlog(self):
        return self._t

    def enabled(self) -> bool:
        return self._t is not None

    def emit(self, kind, actor="", **fields):
        if self._t is None:
            return None
        try:
            return self._t.emit(kind, actor=actor, **fields)
        except Exception:                                        # noqa: BLE001
            return None


#: 宿主流水装配面（模块级单例；测试里当模块用：`tlog_setup.ENV_FLAG` / `.enable(…)`）
tlog_setup = _TlogHolder()


# ============================================================
# conftest 兼容面（`from conftest import …` → `from _engine_harness import …` 即可整族改口）
# ------------------------------------------------------------
# 语义与 `tests/conftest.py` **逐字相同**（FakeEvent / run / clean_db / make_player /
# new_main / TEST_DB / PLUGIN_DIR / QQBOT_DIR），只有取件口从宿主聚合层换成包侧。
# 这样一族测试改口 = 把 `from conftest import X` 改成 `from _engine_harness import X`，
# 其余断言一行不动。
# ============================================================
import sqlite3  # noqa: E402

QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
TEST_DB = os.path.join(PLUGIN_DIR, "test_game_data.db")


class FakeEvent:
    """模拟 AstrBot 消息事件（形状与 conftest 版逐字相同）。"""

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
        self._stopped = True


async def run(handler, ev):
    """调用 async handler，收集全部 yield 结果（普通 coroutine → await 后返回 []）。"""
    gen = handler(ev)
    results = []
    try:
        if hasattr(gen, "asend"):
            while True:
                results.append(await gen.__anext__())
        else:
            await gen
    except StopAsyncIteration:
        pass
    return results


_DEFAULT_TABLES = (
    "players", "player_groups", "inventory", "quests", "battle_state",
    "achievements", "stats", "feedback", "market", "bestiary",
    "guilds", "guild_members", "party", "pets", "pet_dex", "reputation", "signin", "fishing",
    "visited", "world_event", "event_state", "professions", "props_use",
    "visited_subareas", "possessed",
)


def clean_db(*tables):
    """清空指定表（默认清单与 conftest 版逐字相同）。"""
    dbmod = harness().db
    dbmod.init_db()
    conn = sqlite3.connect(dbmod.db_path())
    try:
        for t in (tables or _DEFAULT_TABLES):
            conn.execute("DELETE FROM %s" % t)
        conn.commit()
    finally:
        conn.close()


def make_player(gid="g1", qid="q1", name="测试", cls="战士", level=1):
    """落库一个玩家并返回 player dict（注册名 → cls_id 走包内聚合门面）。"""
    dbmod = harness().db
    cls_id = C.resolve("classes", cls) if hasattr(C, "resolve") else cls
    dbmod.create_player(gid, qid, name, cls_id, {}, 100, 100)
    if level > 1:
        dbmod.update_player(gid, qid, level=level)
    dbmod.update_player(gid, qid, stamina=999999)
    return dbmod.get_player(gid, qid)


def new_main():
    """干净实例（带独立清理后的测试库）。"""
    clean_db()
    return Main(None)

