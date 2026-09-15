# -*- coding: utf-8 -*-
"""宿主流水接入口（P5A：`game/tlog_setup.py` 迁移进 `host/`）—— 全仓**只此一处**拿流水实例与开关。

与 `host/log_setup.py` 对称：那里管「此刻出什么事了」（文本日志），这里管
「发生过什么、能不能复现」（结构化流水，框架 `saintess_engine.tlog`）。

**默认关**（可拔插）：不设 `DRAGONFALL_TLOG=1`、也没人显式 `enable()` 时，`tlog()` 返回 None
—— 所有埋点第一行就 `return`，**与不接流水时逐字一致**（零 IO、零 monkey-patch、零字段）。

开启方式::

    # 运维/调试：环境变量（进程启动前设）
    DRAGONFALL_TLOG=1 python main.py

    # 代码里显式开（测试/演练）
    from host import tlog_setup
    tlog_setup.enable()                       # 默认落 data/tlog.jsonl
    tlog_setup.enable(sinks=[MySink()])       # 自定出口

出口默认 = `JSONLSink("data/tlog.jsonl")`（可 grep、可脱敏、零 DB 风险）。

声明表（`kinds()`）读的是**部署期镜像** `<插件根>/game/data/tlogs.json` —— 与旧路径
（`game/tlog_setup.py`）读**同一个文件**（P4′-C 单源收口的镜像件；包内真源运行时不读，
一致性由 `tests/test_tlogs_single_source.py` 盯着）。可用 `GWEN_TLOGS_JSON` 指向别处。

经 `inject` 交给包：`inject["tlog"] = host.tlog_setup`（包内唯一取用口 = `content/obs.py::bind`）。
"""
from __future__ import annotations

import os
from typing import Iterable, Optional

from saintess_engine.tlog import JSONLSink, KindTable, TLog

ENV_FLAG = "DRAGONFALL_TLOG"
ENV_KINDS = "GWEN_TLOGS_JSON"
DEFAULT_PATH = "data/tlog.jsonl"

#: 插件根（`host/tlog_setup.py` → `host/` → 插件根）
PLUGIN_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

_state: dict = {"tlog": None, "explicit": False}
_KINDS: Optional[KindTable] = None


def _default_sink():
    return JSONLSink(os.path.join(PLUGIN_ROOT, DEFAULT_PATH))


def kinds_path() -> str:
    """声明表镜像件路径（`GWEN_TLOGS_JSON` 优先；否则部署期镜像 `game/data/tlogs.json`）。"""
    return os.environ.get(ENV_KINDS) or os.path.join(PLUGIN_ROOT, "game", "data", "tlogs.json")


def kinds() -> Optional[KindTable]:
    """流水声明表 —— 读**部署期镜像**（运行时唯一读点）。缺失 = None = 不校验（空表不拦）。"""
    global _KINDS
    if _KINDS is None:
        try:
            import json
            with open(kinds_path(), encoding="utf-8") as f:
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


def emit(kind: str, actor: str = "", **fields):
    """埋点便捷口 —— **未启用时直接返回 None**（零构造、零 IO、零字段）。

    用法（各处埋点一行）::

        from host import tlog_setup as _tlog
        _tlog.emit("drop.grant", actor=qq_id, item=item_id, qty=n, source="battle")

    ⚠️ 字段名与保留参数（`kind`/`actor`/`tags`）撞名时用 `fields={...}`：
    `_tlog.emit("battle.hit", fields={"kind": "phys"})`。
    """
    tl = tlog()
    if tl is None:
        return None
    try:
        return tl.emit(kind, actor=str(actor or ""), **fields)
    except Exception:                                            # noqa: BLE001
        return None                                              # 流水异常绝不影响主流程
