# -*- coding: utf-8 -*-
"""游戏侧流水接入口 —— 全仓**只此一处**拿流水实例与开关。

与 `game/log_setup.py` 对称：那里管「此刻出什么事了」（文本日志），这里管
「发生过什么、能不能复现」（结构化流水，框架 `saintess_engine.tlog`）。

**默认关**（可拔插）：不设 `DRAGONFALL_TLOG=1`、也没人显式 `enable()` 时，
`tlog()` 返回 None —— 所有埋点第一行就 `return`，**与不接流水时逐字一致**（零 IO、
零 monkey-patch、零字段）。

开启方式::

    # 运维/调试：环境变量（进程启动前设）
    DRAGONFALL_TLOG=1 python main.py

    # 代码里显式开（测试/演练）
    from game import tlog_setup
    tlog_setup.enable()                       # 默认落 data/tlog.jsonl
    tlog_setup.enable(sinks=[MySink()])       # 自定出口

出口默认 = `JSONLSink("data/tlog.jsonl")`（可 grep、可脱敏、零 DB 风险）；
要落库改用 `game.services.tlog_db_sink.SQLiteSink`。
"""
from __future__ import annotations

import os
from typing import Iterable, Optional

from saintess_engine.tlog import JSONLSink, KindTable, TLog

ENV_FLAG = "DRAGONFALL_TLOG"
DEFAULT_PATH = "data/tlog.jsonl"

_state: dict = {"tlog": None, "explicit": False}
_KINDS: Optional[KindTable] = None


def _default_sink():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(os.path.dirname(here), DEFAULT_PATH)
    return JSONLSink(path)


def kinds() -> Optional[KindTable]:
    """`content/data/tlogs.json` 的声明表（缺失 = None = 不校验）。"""
    global _KINDS
    if _KINDS is None:
        try:
            import json
            here = os.path.dirname(os.path.abspath(__file__))
            p = os.path.join(here, "data", "tlogs.json")
            with open(p, encoding="utf-8") as f:
                _KINDS = KindTable(json.load(f))
        except Exception:                                        # noqa: BLE001
            _KINDS = KindTable({})                               # 缺失 → 空表（不拦）
    return _KINDS


def enable(sinks: Optional[Iterable] = None, *, strict: bool = False,
           name: str = "dragonfall") -> TLog:
    """显式开（幂等：已开则复用）。"""
    if _state["tlog"] is not None:
        return _state["tlog"]
    tl = TLog(list(sinks) if sinks else [_default_sink()],
              kinds=kinds(), strict=strict, name=name)
    _state["tlog"] = tl
    _state["explicit"] = True
    return tl


def disable() -> None:
    """关（回到"零行为"）：关闭出口并清空实例。"""
    tl = _state["tlog"]
    if tl is not None:
        try:
            tl.close()
        except Exception:                                        # noqa: BLE001
            pass
    _state["tlog"] = None
    _state["explicit"] = False


def enabled() -> bool:
    """是否启用（显式 enable 或环境变量）。"""
    if _state["explicit"]:
        return True
    return str(os.environ.get(ENV_FLAG, "")).strip() in ("1", "true", "yes", "on")


def tlog() -> Optional[TLog]:
    """取流水实例（**未启用 → None**；埋点见到 None 直接 return）。"""
    if _state["tlog"] is not None:
        return _state["tlog"]
    if enabled():
        return enable()
    return None
