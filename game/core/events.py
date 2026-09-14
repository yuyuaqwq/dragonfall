# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - events.py（★ B13-L3 起 = 薄壳）

实现真源已进内容包：`content/events.py`（`roll_explore_event` / `roll_explore_egg` 逐字端口；
搬的边界 / 正文改动面 / **为什么不用包内 events 域读口（顺序不可逆）** 全写在那边的头注里）。

本文件只剩三件事：

  1. **加载包**：`bootstrap.package_apply()`（本进程唯一包加载口，幂等；失败大声抛）
  2. **同名再导出五个宿主数据符号 + `current_season`**：包内实现按「真源函数体查本模块全局名」
     的同义语义，走 `core.events.<name>` 取件（`_host_attr`）——
     ⇒ `tests/test_v116_explore_season.py:31` 的 `EV.current_season = lambda …` 打桩**照旧生效**，
     快照里的 `EV.EXPLORE_EGG_CHANCE = 1.0` 打桩同理（见 `overnight/w1213_b13l3_snap.py` C6/C7）。
  3. **同名单 re-export**：`game/core/__init__.py:104`（`roll_explore_event, roll_explore_egg`）与
     `tests/test_v116_explore_season.py:13`（含 `current_season`）、`tests/test_v97_06_eggs_hidden.py:27`
     的 import 点零改动 + `__getattr__` 兜底

★ `from ..data import …`（B14 收口已改）→ 现在读**包内源**：两个探索池取
  `content/catalog_quests.py`（`events` 域），三个派生/常量（`EXPLORE_EGG_CHANCE` /
  `EXPLORE_EGG_SUM` / `EVENT_WEIGHT_SUM`）取 `content/catalog_rules.py`；
  `__getattr__` 转发面与符号名一字未变，`game/data` 删掉后本模块仍可 import。

★ 宿主替身注入：**不需要**（包内按 `sys.modules` 惰性解析；core 模块级 import content 会撞 §8-R1）。

改造前 77 行 → 现在 47 行。等价证据：`overnight/w1213_b13l3_snap.py`（C1–C9 共 10 例）
· `overnight/W-B13-L3-events-dialogue.md`。
"""
from .. import bootstrap as _bootstrap                          # noqa: F401

_bootstrap.package_apply()                                      # 本进程唯一包加载口（幂等）

# B14 收口：原 `from ..data import (EVENT_WEIGHT_SUM, EXPLORE_EVENTS, EXPLORE_EGG_CHANCE,
# EXPLORE_EGG_EVENTS, EXPLORE_EGG_SUM)`。五个符号名与位置一字不变（`EV.<名> = …` 打桩照旧）。
from content.catalog_quests import EXPLORE_EVENTS, EXPLORE_EGG_EVENTS   # noqa: E402,F401
from content.catalog_rules import (EVENT_WEIGHT_SUM, EXPLORE_EGG_CHANCE,  # noqa: E402,F401
                                   EXPLORE_EGG_SUM)
# v116 季节渗透：探索事件随季节变化（借鉴垂钓，见 core/fishing.py）
# - 事件 season 硬限定：非当季不触发；season_boost 偏好：当季权重 ×1.5
# - 季节码与 time_weather.current_season 对齐（spring/summer/autumn/winter）
from .time_weather import current_season                        # noqa: E402,F401  真源同名再导出
from content import events as _IMPL                             # noqa: E402  包内唯一实现
import random                                                   # noqa: E402,F401  真源模块级 import random

# ---- 同名单 re-export（真源符号名一字不变）----
roll_explore_event = _IMPL.roll_explore_event
roll_explore_egg = _IMPL.roll_explore_egg


def __getattr__(name):
    """未列名兜底：转发包内实现（宿主替身名不外露；五个数据符号已在上面显式再导出）。"""
    if name in ("bind_host", "_INJECTED", "_HOST_PKG", "_HOST_PKG_FALLBACK",
                "_host_module", "_host_attr", "_src") or name.startswith("__"):
        raise AttributeError("module %r has no attribute %r" % (__name__, name))
    return getattr(_IMPL, name)


def __dir__():
    return sorted(set(globals()) | set(dir(_IMPL)))
