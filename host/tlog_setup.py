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

★ R5 缺口③（P5D-2 §6.4）：`attach_tlog` 平台件落点
----------------------------------------------------
旧落点 = `game/services/battle_bridge.py::attach_tlog`（`game/**` 待删树，节点：
「读 `game/tlog_setup` 流水开关 + `game/services/battle_tlog` 采集 sink」）。
终态树里 `game/**` 不在了，而这个功能的**属主是宿主平台**（它读宿主流水开关、挂宿主流水出口）
⇒ 落点 = **本模块**（宿主流水唯一取用口，`host/**` 属主）：

    host/tlog_setup.py::attach_tlog(b, …)   ← 唯一的平台装配实现
    host/store_factory.py::inject_handles() ← 摆进宿主注入面（键名 = 接口表第 11 行 `attach_tlog`）

采集半边（`BattleTLog`）是**包内**件（`content/tlog_collect.py`），按**半边名**
`tlog_collect` 经引擎包契约取 —— 宿主里不出现任何包名 / `content.*` 字面量
（与 `host/shell.py` 的 `_sub("…")` 同口径）。
"""
from __future__ import annotations

import os
from typing import Iterable, Optional

from saintess_engine.tlog import JSONLSink, KindTable, TLog

ENV_FLAG = "DRAGONFALL_TLOG"
ENV_KINDS = "GWEN_TLOGS_JSON"
DEFAULT_PATH = "data/tlog.jsonl"

#: 战斗采集半边名（引擎包契约的**半边名**，不是模块路径字面量）
BATTLE_HALF = "tlog_collect"

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


def attach_tlog(b, *, btype: str = "monster", player=None, enemies=None, seed=None):
    """给一场战斗挂**流水采集**（宿主平台件；未启用流水时**零行为**，直接返回 `b`）。

    逐字下游语义 = 旧宿主 `game/services/battle_bridge.py::attach_tlog`：
    开战处一行调用；未启用流水（`DRAGONFALL_TLOG` 未设且没人 `enable()`）→ 直接返回 `b`。

    终态的两处口径（**不静默**）：

    * 采集半边（包内 `tlog_collect.BattleTLog`）**取不到** = 装配缺陷 → 抛 `RuntimeError`
      （调用方以为挂了流水而其实没挂，是最难查的一类静默失效）；
    * **采集体本身**抛异常 → 记 WARNING 后照旧返回 `b`（旧契约「流水不该影响开战」，
      与 `emit()` 同口径；区别是**留痕**，不再无声吞掉）。
    """
    tl = tlog()
    if tl is None:
        return b
    from .store_factory import store
    pkg = store().package
    half = pkg.optional_submodule(BATTLE_HALF) if pkg is not None else None
    if half is None:
        raise RuntimeError(
            "host.tlog_setup.attach_tlog：包内采集半边 %r 取不到（引擎包契约缺件）"
            "——拒绝静默不记流水" % (BATTLE_HALF,))
    try:
        half.BattleTLog(tl).attach(b, btype=btype, seed=seed, player=player, enemies=enemies)
    except Exception as exc:                                     # noqa: BLE001
        from . import log_setup as _log_setup
        _log_setup.LOG.warning("[dragonfall] 流水采集半边挂载异常（不影响主流程）: %s", exc,
                               exc_info=True)
    return b
