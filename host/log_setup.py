# -*- coding: utf-8 -*-
"""宿主日志接入口（P5A：`game/log_setup.py` 迁移进 `host/`）—— 全仓**只此一处**取名与配置。

与源件（`game/log_setup.py`）的差异**只有取件口**：本文件在宿主 `host/` 下，不 import 任何
`game.*`；`LOG` 仍是宿主 AstrBot 的 `astrbot` logger **本体**（`logging.getLogger("astrbot")`
—— 与旧路径拿到的是**同一个对象**，故两条通道的日志出口逐字相同）。

**默认零行为**（可拔插，与框架 `saintess_engine.log` 同口径）：本模块不自动 configure ——
不调 `setup()` 时，`LOG` 就是 `logging.getLogger("astrbot")` 本体，宿主管线照旧。

经 `inject` 交给包：`inject["log"] = host.log_setup.LOG`（包内唯一取用口 = `content/obs.py::bind`）。
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

        from host.log_setup import setup
        from saintess_engine.log import FileSink
        setup(level="INFO", fmt="%(asctime)s %(levelname)s %(message)s",
              sinks=[FileSink("data/dragonfall.log", rotate="size")])

    注意：本函数会把日志前缀设为 `HOST_LOGGER` —— 之后 `get_logger("x")` 得到 `astrbot.x`
    （宿主命名空间）；引擎内部**已建好**的 `saintess_engine.*` logger 不受影响。
    """
    return configure(prefix=HOST_LOGGER, level=level, fmt=fmt, sinks=sinks,
                     propagate=propagate)


def event(name: str):
    """取一个宿主自己的细分 logger（`astrbot.<name>`）—— 需要按模块过滤时用。"""
    return get_logger(name, prefix=HOST_LOGGER)
