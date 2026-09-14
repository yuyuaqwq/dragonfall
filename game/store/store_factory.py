# -*- coding: utf-8 -*-
"""存档层**连接工厂**（B17）—— 宿主对包内 `content.persistence` 的**唯一装配点**。

「宿主零逻辑」边界：本文件只有「连接怎么来」（四个注入点），**零 SQL、零业务分支**；
表结构与 CRUD 全在包内 `content/persistence/`，本文件一行实现都不留。

注入点（BRIEF §0/§2 四句柄）：
  `db_path`   ← 环境变量 `GWEN_GAME_DB` 优先，否则插件目录下 `game_data.db`（原文逻辑逐字搬运）
  `clock`     ← stdlib `time.time`（包内 `time.time()` 调用点已全改 `clock()`）
  `flush_log` ← 日志 sink（默认静默；宿主 logger 已在 `sys.modules` 时转 DEBUG）
  `lock`      ← 不注入：由引擎 `Database.lock`（RLock）提供，与改造前**同一个锁实例**
"""
import os
import sys
import time as _time

from content.persistence import handles as _h

# 库路径（逐字搬运自旧 `game/store/connection.py:15-18`；`__file__` 同在本目录 → 结果同值）
DB_PATH = os.environ.get(
    "GWEN_GAME_DB",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game_data.db"),
)


def _noop(*_a, **_k):
    """空 sink（日志 sink / logger 缺失时的默认落点；零分支）。"""
    return None


def _flush_log(msg):
    """日志 sink 注入点：默认静默（行为与改造前零差异）；宿主 logger 在册时记 DEBUG。"""
    log_setup = sys.modules.get("data.plugins.dragonfall.game.log_setup") or         sys.modules.get("game.log_setup")
    getattr(getattr(log_setup, "LOG", None), "debug", _noop)(msg)   # 不在册 → 静默丢弃


_h.bind(db_path=DB_PATH, clock=_time.time, flush_log=_flush_log)
