#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""奥兰迪亚 · 配置编辑器 —— 战斗模拟预览（**父进程侧**：只起子进程，不 import game）。

为什么必须走子进程
------------------
* 循环导入陷阱：`game.data ↔ game.core` 互相 import；在编辑器主进程里 import game
  会在错误时机拿到半初始化模块（真相见 `game/bootstrap.py` 的装载顺序注释）。
* 装配有副作用：`battle2.config.load_game_defaults()` 会把公式/面板/kind 常量 mount 到
  引擎全局 hook 面 —— 进程级污染，跑一次就回不去。
* 隔离/兜底：引擎异常、死循环都能被超时掐死，编辑器主进程永不受影响。
* 纪律一致：编辑器数据层（data_io）只读 py 源码字面量、**绝不 import game**；
  模拟预览同样把「唯一碰 game 的地方」隔离到子进程。

因此本模块只做三件事：拼 payload → `subprocess` 跑 `simulate_worker.py` → 解析 marker 行。

零第三方依赖（stdlib subprocess/json/os）。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

EDITOR_DIR = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.join(EDITOR_DIR, "simulate_worker.py")
MARKER = "__DF_SIM_RESULT__"

DEFAULT_TIMEOUT = float(os.environ.get("DF_SIM_TIMEOUT", "30"))


def available() -> bool:
    return os.path.isfile(WORKER)


def _tail(text: str, n: int = 20) -> str:
    lines = (text or "").replace("\r\n", "\n").strip().splitlines()
    return "\n".join(lines[-n:])


def _python() -> str:
    """优先用「能跑起 astrbot 插件」的 python（含 pypinyin）；回落当前解释器。"""
    env_py = os.environ.get("DF_ENGINE_PYTHON")
    if env_py and os.path.isfile(env_py):
        return env_py
    cand = r"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe"
    if os.path.isfile(cand):
        return cand
    return sys.executable


def simulate(payload: dict, timeout: float | None = None) -> dict:
    """跑一次模拟，返回 worker 的 JSON 结果（永远返回 dict，绝不抛）。

    成功：{"ok": True, "damage": N, "logs": [...], "events": [...], ...}
    失败：{"ok": False, "stage": "...", "message": "...", ["stderr"/"traceback"]}
    """
    if not available():
        return {"ok": False, "stage": "setup", "message": f"找不到模拟 worker：{WORKER}"}
    timeout = float(timeout or DEFAULT_TIMEOUT)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    try:
        proc = subprocess.run(
            [_python(), "-B", WORKER],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout, env=env, cwd=os.path.dirname(EDITOR_DIR),
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "timeout",
                "message": f"模拟超时（>{timeout:g}s）——引擎装配或战斗推进卡住，已中止。"}
    except Exception as exc:                                    # pragma: no cover
        return {"ok": False, "stage": "spawn",
                "message": f"无法启动模拟子进程：{type(exc).__name__}: {exc}"}

    res = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith(MARKER):
            try:
                res = json.loads(line[len(MARKER):])
            except Exception:
                res = None
    if res is None:
        return {"ok": False, "stage": "crash",
                "message": "模拟子进程未返回结果（可能崩溃）。",
                "returncode": proc.returncode,
                "stderr": _tail(proc.stderr),
                "stdout_tail": _tail(proc.stdout)}
    if not res.get("ok") and not res.get("stderr"):
        res["stderr"] = _tail(proc.stderr)
    return res


if __name__ == "__main__":                                       # pragma: no cover
    # 命令行自检：python editor/simulate.py
    demo = {"skill": {"name": "挥砍", "kind": "物理", "lv": 1, "mp": 6, "power": 0.82,
                      "cast": 0.45, "exprs": ["atk*1.0 + 10"], "desc": "自检"},
            "attacker": {"class_name": "战士", "level": 20}}
    print(json.dumps(simulate(demo), ensure_ascii=False, indent=2))
