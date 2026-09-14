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
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
WORKSPACE = os.path.dirname(os.path.dirname(PLUGIN_DIR))

sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
sys.path.insert(0, os.path.join(PLUGIN_DIR, "framework"))
_shim = os.path.join(HERE, "shim_astrbot")
if os.path.isdir(_shim):
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
    # 宿主存档层工厂（`game.store.store_factory`）把 stdlib `time.time` 作为 clock 句柄注入
    # 包内存档层（`content.persistence.handles._H["clock"]`）→ 落库时间戳会走真墙钟；
    # 该句柄是**函数对象**，只能改注入值本身（同一个注入口，不新增第三套）。
    try:
        import game.store.store_factory as _sf
        if getattr(_sf, "time", None) is _time_mod:
            _sf.time = _ClockProxy()
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
        from game.commands import _host_bridge as BRIDGE
        from game.commands import (PlayerCmds, WorldCmds, CombatCmds, EconomyCmds, SocialCmds,
                                   MiscCmds, InstanceCmds, GmCmds, ExplorationCmds, JobGuideCmds,
                                   CollectionCmds, WeeklyCmds, TowerCmds, EventMenuCmds)
        from content import persistence
        import time as _time
    except Exception:
        emit({"ok": False, "stage": "load", "traceback": traceback.format_exc()})
        return 0

    bases = (PlayerCmds, WorldCmds, CombatCmds, EconomyCmds, SocialCmds, MiscCmds, InstanceCmds,
             GmCmds, ExplorationCmds, JobGuideCmds, CollectionCmds, WeeklyCmds, TowerCmds,
             EventMenuCmds)
    shell_cls = type("B20QqShell", (_PlatformRecorder,) + bases, {})
    shell = shell_cls()

    # 墙钟钉死（与试玩侧同口径；`B20_CLOCK` 或 payload["clock"]）
    clock_ts = payload.get("clock") or os.environ.get("B20_CLOCK") or ""
    if clock_ts not in (None, ""):
        try:
            _freeze_clock(float(clock_ts))
        except Exception:                 # noqa: BLE001
            pass

    from _cmd_registry import declared_usage

    _BY_KEY = {}
    for _mname, _k in declared_usage().items():
        _BY_KEY.setdefault(_k, _mname)

    import asyncio

    def _run_one(key, text):
        fn = getattr(shell, key, None)
        if fn is None:
            # 声明表 key 与宿主方法名不同名（如 register → register_）：按 `_cmd_registry` 反查
            mname = _BY_KEY.get(key)
            fn = getattr(shell, mname, None) if mname else None
        if fn is None:
            return {"error": "宿主侧无 %r 的 handler" % key}
        event = FakeEvent(group_id, uid, text)
        shell._b20_events = []
        segs = []

        async def _collect():
            async for item in BRIDGE.run_async(shell, key, event):
                if item not in (None, ""):
                    segs.append(str(item))
        asyncio.run(_collect())
        return {"segments": segs, "actions": list(shell._b20_events)}

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
