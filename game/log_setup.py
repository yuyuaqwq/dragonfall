# -*- coding: utf-8 -*-
"""游戏侧日志接入口 —— 全仓**只此一处**取名与配置。

背景：此前 14 个文件在 19 个点位各自 `logging.getLogger("astrbot")`，名字还分三种
（`astrbot` / `dragonfall` / `dragonfall.battle`）。想统一格式、想落地到文件、想临时开 DEBUG，
都得逐个文件改 —— 有日志行为，没有日志模块。

现在：全仓 import 同一个 `LOG`（= 宿主 AstrBot 的 `astrbot` logger），出口与级别由本模块
的 `setup()` 单点配置。

**默认零行为**（可拔插，与框架 `saintess_engine.log` 同口径）：本模块不自动 configure ——
不调 `setup()` 时，`LOG` 就是 `logging.getLogger("astrbot")` **本体**，
宿主管线照旧，行为与收敛前逐字一致。
"""
from __future__ import annotations

from saintess_engine.log import bind, configure, get_logger  # noqa: F401

# 宿主 logger 名：AstrBot 的日志管线认这个名字（消息会出现在宿主日志里）
HOST_LOGGER = "astrbot"

# 全仓共用的 logger —— 与 `logging.getLogger("astrbot")` 是**同一个对象**
LOG = get_logger("", prefix=HOST_LOGGER)


def setup(*, level=None, fmt=None, sinks=(), propagate=None):
    """单点配置（★ 显式调用才生效；没人调 = 与现状逐字一致）。

    在插件启动处落一份文件日志（同时保留宿主输出）::

        from game.log_setup import setup
        from saintess_engine.log import FileSink
        setup(level="INFO", fmt="%(asctime)s %(levelname)s %(message)s",
              sinks=[FileSink("data/dragonfall.log", rotate="size")])

    注意：本函数会把日志前缀设为 `HOST_LOGGER` —— 之后 `get_logger("x")` 得到 `astrbot.x`
    （宿主命名空间）；引擎内部**已建好**的 `saintess_engine.*` logger 不受影响。
    """
    return configure(prefix=HOST_LOGGER, level=level, fmt=fmt, sinks=sinks,
                     propagate=propagate)


def event(name: str):
    """取一个游戏自己的细分 logger（`astrbot.<name>`）—— 需要按模块过滤时用。"""
    return get_logger(name, prefix=HOST_LOGGER)
