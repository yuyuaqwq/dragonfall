# -*- coding: utf-8 -*-
"""B20 对拍基准：**QQ 侧**（平台插件 + shim_astrbot + `_host_bridge`）跑同一条命令序列。

用法（在宿主插件的**工作副本**里跑，不碰真仓）：

    python tests/b20_qq_ref.py <<'JSON'
    {"commands": ["角色", "背包"], "uid": "8001", "group_id": "g2",
     "db": ".../qq.db", "seed": 3, "handlers": [["角色","profile"], ["背包","inventory"]]}
    JSON

输出（stdout 每行 `__B20_QQREF__` + JSON）：逐条 `{"i","text","key","segments",
"actions","state_sha","digest","ok"}`，末行 `{"stage":"done","digests_sha":...}`。

为什么这样是「QQ 侧口径」
------------------------
`handlers` 由调用方给出 `(消息原文 → 声明 key)` 的映射 —— 与 QQ 侧**同一个**派发口径
（AstrBot `@declared(key)` 注册 + `_cmd_registry` 的声明表正则），调用方用
`tests/_cmd_registry.patterns_with_meta()` 复算出来（见 `b20_qq_ref_keys()`）。
随后**逐字复用**平台路径：

    game.commands.<Mixin>.<handler>(shell, event)
        └─ _host_bridge.run_async(shell, key, event)
             ├─ package()/load_package → COMMANDS[key]（包内处理器）
             ├─ Env(uid/group_id/text/raw/player/clock/rng/texts/state={"shell": shell})
             ├─ run_guards（声明守卫）
             └─ fn(env) → await → 逐段 yield

`shell` = 插件的命令 Mixin 实例（`Main` 的 MRO），`event` = `FakeEvent`（conftest 同款）。
"""
from __future__ import annotations

import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(HERE)
#: ★ P5E-DELETE：交付面 `EngineChannel(package_dir)` 的必填参数 —— 包目录
#: （`content` 的父目录）。**不写死包名**：取 `framework/games/*` 里声明表最大的那个
#: （与全量 runner / 注册门禁同规则）。
def _find_pkg_dir():
    import json as _json
    games = os.path.join(PLUGIN_DIR, "framework", "games")
    best, best_n = "", -1
    if os.path.isdir(games):
        for name in sorted(os.listdir(games)):
            decl = os.path.join(games, name, "content", "data", "commands.json")
            if not os.path.isfile(decl):
                continue
            with open(decl, encoding="utf-8") as fh:
                n = len(_json.load(fh) or {})
            if n > best_n:
                best, best_n = os.path.join(games, name), n
    return best


_PKG_DIR = _find_pkg_dir()
if _PKG_DIR and _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)


def _find_qqbot_dir(plugin_dir):
    """qqbot 部署根（`<qqbot>/data/plugins/<插件>` 的那一层 `data` 的父目录）。

    旧写法是死算 `dirname³(PLUGIN_DIR)` —— 只在**部署布局**（插件目录正好是
    `<qqbot>/data/plugins/<名>`）成立。本工作副本里插件目录是 `<ws>/host`，
    死算得到 `<ws>/../..`（垃圾路径）⇒ 下面 `import data.plugins.dragonfall.main`
    当场 ModuleNotFoundError（实测：引擎门禁 `tests/test_editor_play.py` 的
    「QQ 侧参考跑通」7 条红全由此而来）。

    口径（与 `tests/_paths.py` 同精神：**发现 + 显式报错，不写死路径**）：
      ① `GWEN_QQBOT_DIR` 环境变量优先；
      ② 从插件目录的**各级祖先**（含其**一级子目录**——本工作副本里 qqbot 根
         `<ws>/_run_home` 是插件目录 `<ws>/host` 的**兄弟**，不是祖先）里，找
         「谁家 `data/plugins/<任一插件>` 与本插件目录**同一实体**」
         （`samefile` 认目录联接/软链/同路径）——部署布局命中 `<qqbot>`，
         本工作副本命中 `<ws>/_run_home`；
      ③ 都不中 → 回落旧口径 `dirname³(PLUGIN_DIR)`（保持原有报错行为，不静默换路径）。

    注 1：判据必须是「`data/plugins/<x>` **确实是本插件**」而不是「存在 `data/plugins/`
    目录」——本机 `<ws>/../data/plugins/` 是个空目录，只判存在会命中它（实测：
    `_find_qqbot_dir` 直接返回 `C:/Users/yuyu/dsh-work`，`import` 照旧失败）。
    注 2：剪枝 = 先要求候选根下 `data/plugins` 目录存在，才列它的子项；且只扫
    祖先自身 + 祖先的一级子目录（本工作副本在第 1 级就命中，开销可忽略）。
    """
    env = (os.environ.get("GWEN_QQBOT_DIR") or "").strip()
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    legacy = os.path.dirname(os.path.dirname(os.path.dirname(plugin_dir)))
    plugin_abs = os.path.abspath(plugin_dir)

    def _hit(root):
        plugins = os.path.join(root, "data", "plugins")
        if not os.path.isdir(plugins):
            return False
        try:
            names = sorted(os.listdir(plugins))
        except OSError:
            return False
        for name in names:
            cand = os.path.join(plugins, name)
            try:
                if os.path.isdir(cand) and os.path.samefile(cand, plugin_abs):
                    return True
            except OSError:
                continue
        return False

    home = os.path.dirname(plugin_abs)
    steps = 0
    while steps < 6:
        steps += 1
        if _hit(home):
            return home
        try:
            children = sorted(os.listdir(home))
        except OSError:
            children = []
        for name in children:
            child = os.path.join(home, name)
            try:
                if os.path.isdir(child) and _hit(child):
                    return child
            except OSError:
                continue
        parent = os.path.dirname(home)
        if parent == home:
            break
        home = parent
    return legacy


QQBOT_DIR = _find_qqbot_dir(PLUGIN_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(PLUGIN_DIR))

sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
sys.path.insert(0, os.path.join(PLUGIN_DIR, "framework"))
# ★ T8（测试单源化）：shim 目录改走**宿主布局适配层** —— 旧写法只认
#   `host/tests/shim_astrbot`，T8 后宿主侧不再自留该副本（回落到包仓那份 tests 里同名目录）。
#   不修的话 QQ 侧会退回**真实 astrbot** ⇒ 与试玩侧逐字节对拍当场失真（实测：
#   `test_editor_play.py` 的 C 段 3/44 条 tip 不一致，30/3 红）。
_shim = ""
try:
    from _host_layout import SHIM_DIR as _shim        # noqa: PLC0415
except Exception:                                     # noqa: BLE001
    _shim = os.path.join(HERE, "shim_astrbot")
if _shim and os.path.isdir(_shim):
    sys.path.insert(0, _shim)

MARKER = "__B20_QQREF__"


def emit(obj) -> None:
    sys.stdout.write(MARKER + json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
    sys.stdout.flush()


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _state_sha(blobs=None) -> str:
    """与试玩侧 `editor/play_worker.py::_state_sha` **同口径**：整库快照 + blob。"""
    import sqlite3
    db_path = os.environ.get("GWEN_GAME_DB") or ""
    snap = {"blobs": blobs if blobs is not None else {}}
    if db_path and os.path.isfile(db_path):
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            tables = {}
            for (name,) in conn.execute(
                    "select name from sqlite_master where type='table' order by name"):
                if str(name).startswith("sqlite_"):
                    continue
                rows = [list(r) for r in conn.execute('select * from "%s"' % name)]
                tables[str(name)] = rows
            conn.close()
            snap["tables"] = tables
        except Exception as e:            # noqa: BLE001
            snap["tables_error"] = repr(e)
    return _sha(_dump(snap))


class FakeEvent:
    """conftest 同款最小事件（`shim_astrbot` 口径）。"""

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
        return str(text)

    def stop_event(self):
        self._stopped = True

    async def send(self, message):
        return message


class _PlatformRecorder:
    """平台动作记录基类（放在 MRO 最前 → 覆盖宿主的 `_broadcast`；试玩侧同款记录）。

    试玩侧（`editor/play_worker.py::PlayShell`）与这里都把「广播 / webhook」落成一条记录，
    因此两侧的 `actions` 逐字节可比；QQ 侧的真实投递（`self.context.send_message`）在
    试玩通道里没有平台可发。
    """

    def _record_events(self):
        ev = getattr(self, "_b20_events", None)
        if ev is None:
            ev = []
            self._b20_events = ev
        return ev

    async def _broadcast(self, text, exclude_group=None):
        self._record_events().append({"action": "broadcast", "text": str(text),
                                      "exclude": str(exclude_group or "")})

    async def _notify_hermes(self, group_id, qq_id, content, msg_type):
        self._record_events().append({"action": "hermes", "content": str(content),
                                      "msg_type": str(msg_type)})


def _freeze_clock(ts: float) -> None:
    """与试玩侧 `editor/play_worker.py::_freeze_clock` 同口径：钉死包内墙钟读取点。

    对拍两侧必须同刻（`时间` / 天气 / 冷却 / 「今日」类命令的输出与当前时刻有关）。
    """
    import datetime as _dt
    import time as _time_mod

    class _FrozenDateTime(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.fromtimestamp(ts, tz) if tz else cls.fromtimestamp(ts)

    class _FrozenDate(_dt.date):
        @classmethod
        def today(cls):
            return cls.fromtimestamp(ts)

    class _ClockProxy:
        def __getattr__(self, name):
            return getattr(_time_mod, name)

        @staticmethod
        def time():
            return ts

    for name, mod in list(sys.modules.items()):
        if not (name == "content" or name.startswith("content.")) or mod is None:
            continue
        if getattr(mod, "time", None) is _time_mod:
            mod.time = _ClockProxy()
        if getattr(mod, "datetime", None) is _dt:
            proxy = type("_dt_proxy", (), {})()
            proxy.datetime = _FrozenDateTime
            proxy.date = _FrozenDate
            proxy.timedelta = _dt.timedelta
            proxy.time = _dt.time
            proxy.timezone = _dt.timezone
            mod.datetime = proxy
    # 宿主存档层工厂（旧路径 `game.store.store_factory`；P5A 后真源在 `host/store_factory`）
    # 把 stdlib `time.time` 作为 clock 句柄注入包内存档层
    # （`content.persistence.handles._H["clock"]`）→ 落库时间戳会走真墙钟；
    # 该句柄是**函数对象**，只能改注入值本身（同一个注入口，不新增第三套）。
    try:
        import game.store.store_factory as _sf
        if getattr(_sf, "time", None) is _time_mod:
            _sf.time = _ClockProxy()
    except Exception:                     # noqa: BLE001
        pass
    # 宿主桥给 `Env` 的 clock 句柄（`_host_bridge._prepare()`：`clock=time.time`）——
    # 试玩侧那份 `Env.clock` 由引擎 Host 从适配器取（`Host.clock()` → 适配器 `clock()` =
    # 冻结值），这里对齐：不然 `content/guards.py` 的「当前时刻」读点在两侧不同刻。
    try:
        import game.commands._host_bridge as _bridge
        if getattr(_bridge, "time", None) is _time_mod:
            _bridge.time = _ClockProxy()
    except Exception:                     # noqa: BLE001
        pass
    try:
        import content.persistence.handles as _handles
        _handles.bind(clock=lambda: float(ts))
    except Exception:                     # noqa: BLE001
        pass
    try:
        from saintess_engine import clock as _clock
        _clock.set_provider(lambda: float(ts))
    except Exception:                     # noqa: BLE001
        pass


def main() -> int:
    payload = json.load(sys.stdin)
    db = payload.get("db") or ""
    if db:
        os.environ["GWEN_GAME_DB"] = db
    os.environ.setdefault("GWEN_TEST_MODE", "1")

    uid = str(payload.get("uid") or "u1")
    group_id = str(payload.get("group_id") or "g1")
    pairs = [(str(a), str(b)) for a, b in (payload.get("handlers") or [])]
    seed = payload.get("seed", 1)
    try:
        import random
        random.seed(float(seed) if seed is not None else 1.0)
    except Exception:                     # noqa: BLE001
        pass

    try:
        # ★ P5E-DELETE（2026-09-15，删壳批）：驱动面从**待删宿主壳**
        #   （`game.commands` 的 14 个 Mixin + `game.commands._host_bridge.run_async`）
        #   改成**交付面** `main.EngineChannel`（`main.py:647`；与 `host/adapter_qq.py`
        #   同一条平台路径：平台 gate → 平台例外 → 引擎可见路由）。
        #   本脚本的角色是「QQ 侧对拍基准」——终态下这就是 QQ 侧本身
        #   （`main.EngineChannel` 是生产唯一「跑一条消息」入口），
        #   判据（逐条 key/文本段/动作/状态 sha 与试玩侧逐字节相同）一字未变。
        import importlib
        _main = importlib.import_module("data.plugins.dragonfall.main")
        from content import persistence
        import time as _time
    except Exception:
        emit({"ok": False, "stage": "load", "traceback": traceback.format_exc()})
        return 0

    # ★ 装配顺序铁律（原注释保留）：**先把包物化（宿主注入面落地）再钉墙钟**。
    #   交付面 `EngineChannel.boot()` 内部即 `host.boot()`（load_package + bind_host 的
    #   clock 注入），故顺序天然正确。
    try:
        _channel = _main.EngineChannel(_PKG_DIR)
        _channel.boot()
    except Exception:
        emit({"ok": False, "stage": "load",
              "message": "包物化失败（引擎 load_package + 宿主注入面）",
              "traceback": traceback.format_exc()})
        return 0
    shell = _channel.shell
    BRIDGE = _channel          # 兼容下面的旧名字（`.dispatch_declaration` ≡ 旧 `run_async`）

    # 墙钟钉死（与试玩侧同口径；`B20_CLOCK` 或 payload["clock"]）—— 必须在注入面落地之后
    clock_ts = payload.get("clock") or os.environ.get("B20_CLOCK") or ""
    if clock_ts not in (None, ""):
        try:
            _freeze_clock(float(clock_ts))
        except Exception:                 # noqa: BLE001
            pass

    def _run_one(key, text):
        """按**声明 key** 跑一条 → 回话段（旧壳 `_BRIDGE.run_async` 的同义落点）。"""
        event = FakeEvent(group_id, uid, text)
        try:
            segs = [str(x) for x in (_channel.dispatch_declaration(key, event) or [])
                    if x not in (None, "")]
        except Exception as e:            # noqa: BLE001
            return {"error": "%s: %s" % (type(e).__name__, e)}
        return {"segments": segs,
                "actions": list(getattr(shell, "_events", None) or [])}

    rows = []
    for i, (text, key) in enumerate(pairs):
        rec = {"i": i, "text": text, "key": key, "segments": [], "message": "", "actions": [],
               "state_sha": "", "digest": "", "ok": True}
        try:
            out = _run_one(key, text)
            if out.get("error"):
                rec["ok"] = False
                rec["error"] = out["error"]
            rec["segments"] = out.get("segments") or []
            rec["message"] = "\n".join(str(x) for x in rec["segments"] if x not in (None, ""))
            rec["actions"] = out.get("actions") or []
            rec["state_sha"] = _state_sha(shell._b20_blobs if hasattr(shell, "_b20_blobs") else {})
            rec["digest"] = _sha("\n".join(
                [rec["key"], rec["message"]]
                + [_dump(a) for a in rec["actions"]] + [rec["state_sha"]]))
        except Exception as e:            # noqa: BLE001
            rec["ok"] = False
            rec["error"] = "%s: %s" % (type(e).__name__, e)
            rec["traceback"] = traceback.format_exc()[-2000:]
        rows.append(rec)
        emit(rec)

    emit({"ok": True, "stage": "done", "ran": len(rows),
          "digests_sha": _sha("\n".join(r.get("digest", "") for r in rows))})
    return 0


if __name__ == "__main__":
    sys.exit(main())
