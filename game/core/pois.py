# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - pois.py（v87 02 章 7.6：探索点 POI 系统）—— B13-L5 **薄壳**（2026-09-14）

POI 触发与效果结算的实现正文（55 行：`subarea_pois` / `subarea_props` / `prop_entry` / `roll_poi`）
已**逐字搬进内容包** `content/pois.py`；`subarea_pois` 改读包内 `pois` 域（457 行房间挂载表，
对拍逐键相等）。本文件只剩两件事：**加载包** · **模块别名**（`sys.modules[__name__] = 包内模块`）。

别名之后 `game.core.pois` 与 `content.pois` **是同一个模块对象**：
`from .pois import subarea_pois, roll_poi, subarea_props, prop_entry`（`game/core/__init__.py:105`）
与聚合层 `C.subarea_pois` / `C.roll_poi` / `C.prop_entry`（`commands/instance.py:539/808/1898`、
包内 `content/world_cmds.py` 经 `C` 宿主面、`tests/test_v87_hidden.py` 等）取到的都是包内实现本体。

⚠️ 两处**故意仍走宿主句柄**（缺口，见包内头注）：`POIS` 类型定义表（83 条，未进包）与
`SUBAREA_PROPS`（`props` 域是反投影、行内序不复原，不满足 I3）。
"""
import sys as _sys

from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                  # 本进程唯一包加载口（幂等）

from content import pois as _impl                            # noqa: E402  包内实现（真源）

_sys.modules[__name__] = _impl                               # 模块别名：壳与实现同体
