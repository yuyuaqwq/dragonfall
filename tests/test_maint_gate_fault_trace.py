# -*- coding: utf-8 -*-
"""门禁：宿主 `host/shell.py::_maint_gate` 的**三个兄弟 try** 必须同形留痕（晚到批同族残留）。

缺陷本体（复刻实测，非推断）
----------------------------
`_maint_gate` 是**每条玩家消息**路由前都跑的 gate（`host/adapter_qq.py::gate` → `run_sync(...)`），
它里三个兄弟 try 各自兜住一个包内半边的惰性刷新。修前**第一个**兜底
（`timed_events.refresh_timed`）写的是 `LOG.warning(..., exc_info=True)`，
**第二、三个**（`wild_king.wild_king_tick` / `worlds.cleanup_stale_instances`）却是
裸 `except Exception: pass`。

危害：两个兄弟抛异常时**零日志零痕迹**。玩家看到的是「野王整时段不刷新」
「超龄大陆实例永远不清」，而宿主日志里**查不到任何一行** ⇒ 排障成本 = 无穷尽盲猜。
尤其 `wild_king_tick` 的失败后果直接可见（时段重置 / 刷怪全不发生）。

判定
----
[1] 行为向（黑盒，不读被测源码）：造三个半边，其中两个**必抛** ⇒ 必须各留一条 warning
[2] 三兄弟同形：三条兜底的**异常类型一致**（宽到能接住真故障，不许收窄成只接某类）
[3] 三条兜底都**必须带 exc_info**（留栈，不留消息）
[4] 兜底**不得改成 raise**：真故障不许中断 gate（停服拦截要照跑）
[5] 静态兜底：`except` 后**不得出现裸 `pass`**（AST 判，剔 docstring）——
    留痕只能经 LOG，不许用别的方式再吞一次
[6] ★ 两向反证：把第二/三条改回裸 `pass` ⇒ 本门禁必须转红；还原后复绿

跑法
----
    python tests/test_maint_gate_fault_trace.py
"""
from __future__ import annotations

import ast
import io
import logging
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)          # 供 `from host.shell import ...`（黑盒真调被测实现）

from _check import bind_check                                    # noqa: E402

FAILS: list = []
PASS = 0
check = bind_check(globals(), "PASS", "FAIL", "FAILS")

SHELL_PY = os.path.join(_REPO, "host", "shell.py")


# ---------------------------------------------------------------- 黑盒执行
def _run_gate(raising=("wild_king", "worlds")):
    """造三个假半边真调 `_maint_gate` 的那三个 try，返回捕获到的日志记录。

    捕获走**真 logging handler**（不 monkeypatch）：`host/shell.py` 里的 `LOG` 是
    模块级 `logging.getLogger("astrbot")`，任何实例属性都拦不住它。
    """
    import asyncio
    import logging
    from host.shell import HostShell

    records = []

    class _Capture(logging.Handler):
        def emit(self, record):
            records.append((record.getMessage(), bool(record.exc_info)))

    handler = _Capture()
    log = logging.getLogger("astrbot")
    prev_level, prev_prop = log.level, log.propagate
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    log.propagate = False
    try:
        class _Half:
            def __init__(self, name):
                self._n = name
            def __getattr__(self, item):
                def _fn(*a, **k):
                    if self._n in raising:
                        raise RuntimeError("%s.%s 炸了" % (self._n, item))
                    return {}
                return _fn

        class _Shell(HostShell):
            def _sub(self, name):
                return _Half(name)
            def _uid(self, event):
                return "g1", "u1"
            def _is_gm(self, qq_id):
                return True
            def _server_down(self):
                return False

        asyncio.run(_Shell.__new__(_Shell)._maint_gate({}))
    finally:
        log.removeHandler(handler)
        log.setLevel(prev_level)
        log.propagate = prev_prop
    return records


def _static_handlers():
    """读 `_maint_gate` 源码，返回该协程里 `except Exception` 的三条兜底体。"""
    src = io.open(SHELL_PY, encoding="utf-8").read()
    tree = ast.parse(src)
    fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_maint_gate":
            fn = node
    bodies = []
    for node in ast.walk(fn):
        if isinstance(node, ast.ExceptHandler) and node.type is not None:
            if ast.unparse(node.type) == "Exception":
                bodies.append(node)
    return bodies


# ---------------------------------------------------------------- 判定
def main():
    NL = chr(10)
    # [1] 行为向：两个兄弟抛异常各留一条 warning
    rec = _run_gate()
    warn_msgs = [m for m, _ in rec]
    check("行为：两个抛异常的兄弟各留一条 ⇒ 恰好 2 条（实测 %d）" % len(rec),
          len(rec) == 2)
    check("行为：wild_king_tick 失败有 warning（实测 %r）" % warn_msgs,
          any("wild_king" in m for m in warn_msgs))
    check("行为：cleanup_stale_instances 失败有 warning（实测 %r）" % warn_msgs,
          any("worlds" in m for m in warn_msgs))

    # [2][3] 三条兜底同形 + 都带 exc_info
    check("三条留痕都带 exc_info（实测 %r）" % rec,
          all(flag for _, flag in rec) and rec)
    check("两条留痕各点名自己的兄弟、互不合并（实测 %r）" % sorted(warn_msgs),
          len({m.strip("[").split("]")[0] for m in warn_msgs}) == 2
          and {m.strip("[").split("]")[0] for m in warn_msgs} == {"wild_king", "worlds"})

    # [4] 兜底不 raise：三个全抛 gate 仍走完（不中断停服拦截）
    rec2 = _run_gate(raising=("timed_events", "wild_king", "worlds"))
    check("兜底不中断 gate：三个全抛也各留一条（实测 %d）" % len(rec2),
          len(rec2) == 3)

    # [5] 静态：except 后不得是裸 pass，且都经 LOG 带 exc_info
    bodies = _static_handlers()
    check("静态：_maint_gate 里恰有 3 条宽异常兜底（实测 %d）" % len(bodies),
          len(bodies) == 3)
    bare = []
    for h in bodies:
        body = [s for s in h.body
                if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        if not body or all(isinstance(s, ast.Pass) for s in body):
            bare.append(h.lineno)
    check("静态：三条兜底都不许裸 pass（裸 pass 在 %r）" % bare, not bare)
    for h in bodies:
        calls = [n for n in ast.walk(h) if isinstance(n, ast.Call)]
        kw = {k.arg for c in calls for k in c.keywords if k.arg}
        fn_names = {getattr(c.func, "attr", "") for c in calls}
        check("静态：第 %d 行兜底经 LOG 留痕（实测 %r）" % (h.lineno, sorted(fn_names)),
              bool(fn_names & {"warning", "exception", "error"}))
        check("静态：第 %d 行兜底带 exc_info（实测 kwargs=%r）" % (h.lineno, sorted(kw)),
              "exc_info" in kw or "exception" in fn_names)

    print(NL + "通过 %d / 失败 %d" % (PASS, len(FAILS)))
    if FAILS:
        for f in FAILS:
            print("  FAIL: " + f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
