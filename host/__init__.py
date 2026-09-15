# -*- coding: utf-8 -*-
"""宿主平台面（P5A）：引擎 host 契约的宿主实现。

| 文件 | 职责 |
|---|---|
| `adapter_qq.py` | ★ 契约实现：三函数（`recv` / `load_player`+`save_player` / `say`）+ 可选钩子 + 平台 gate |
| `_platform.py` | 平台 API 面（事件协议 / 消息链 / filter / 注册表）—— `game/commands/_platform.py` 原样迁 |
| `_identity.py` | 平台标识 → uid（openid ⇄ QQ 号映射） |
| `store_factory.py` | 库路径 + 连接/锁取用口 + **存档半边**取用口 + `inject` 五键 |
| `log_setup.py` · `tlog_setup.py` | 日志 / 流水 sink（平台件；经 `inject` 交给包） |

方向铁律（见 `README`/`docs/engine-wiki/reference/host-api.md`）：本包**零游戏知识** ——
不出现包名、`content.*`、任何职业/技能/怪物/地名/文案槽位；包目录路径一律**由配置给**
（`main.py::resolve_package_dir()`）。引擎（`saintess_engine`）经宿主根下的
`framework/` 子模块接入，本文件负责把它接进 `sys.path`（与 `game/__init__.py` 同一手法，
只认目录、不认包名）。
"""
import os as _os
import sys as _sys

_FRAMEWORK_DIR = _os.path.normpath(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "framework"))
if _os.path.isdir(_FRAMEWORK_DIR) and _FRAMEWORK_DIR not in _sys.path:
    _sys.path.insert(0, _FRAMEWORK_DIR)
